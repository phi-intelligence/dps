"""
Customer-safe tracking + ETA derived from operational_tracking_service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.operational_tracking_service import (
    compute_internal_job_eta,
    get_operational_tracking_state,
    resolve_job_destination_lat_lon,
)
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.quoting.models import Quote


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

CustomerTrackingState = Literal[
    "request_received",
    "quote_sent",
    "quote_accepted",
    "scheduled",
    "engineer_assigned",
    "engineer_on_the_way",
    "engineer_on_site",
    "work_in_progress",
    "work_completed",
    "documents_ready",
    "invoice_issued",
    "closed",
]


def derive_customer_tracking_state(db: Session, *, job: Job) -> CustomerTrackingState:
    """Single headline state for the customer UI (most advanced applicable milestone)."""
    inv = db.query(Invoice).filter(Invoice.job_id == job.id).order_by(Invoice.created_at.desc()).first()
    if inv and (inv.paid_at or inv.status == "paid"):
        return "closed"

    if inv and inv.status == "unpaid":
        return "invoice_issued"

    certs = db.query(Certificate).filter(Certificate.job_id == job.id).count()
    if job.status in ("completed", "closed") and certs > 0:
        return "documents_ready"

    if job.status in ("completed", "closed"):
        return "work_completed"

    if job.on_site_at:
        if job.status in ("accepted", "in_progress", "on_site"):
            return "work_in_progress"
        return "engineer_on_site"

    if job.en_route_at or job.on_my_way_sent_at:
        return "engineer_on_the_way"

    if job.assigned_engineer_id or job.dispatched_at:
        return "engineer_assigned"

    if job.scheduled_at:
        return "scheduled"

    if job.quote_id:
        q = db.get(Quote, job.quote_id)
        if q and q.accepted_at:
            return "quote_accepted"
        if q and q.status not in ("draft",):
            return "quote_sent"

    return "request_received"


def get_customer_job_tracking_state(db: Session, *, job_id: str) -> dict[str, Any]:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    op = get_operational_tracking_state(db, job_id=job_id)
    headline = derive_customer_tracking_state(db, job=job)
    lsu = op.get("last_status_update_at")
    return {
        "job_id": job_id,
        "customer_tracking_state": headline,
        "engineer_on_the_way": bool(op.get("engineer_on_the_way")),
        "engineer_on_site": bool(op.get("engineer_on_site")),
        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        "last_status_update_at": _aware(lsu).isoformat() if isinstance(lsu, datetime) else lsu,
        "on_my_way_sent_at": job.on_my_way_sent_at.isoformat() if job.on_my_way_sent_at else None,
        "customer_notified_at": job.customer_notified_at.isoformat() if job.customer_notified_at else None,
    }


def compute_customer_eta(db: Session, *, job_id: str, now: datetime | None = None) -> dict[str, Any]:
    internal = compute_internal_job_eta(db, job_id=job_id, now=now)
    # Strip operational-only nuance; keep portal-safe fields.
    conf = internal.get("eta_confidence")
    if internal.get("telemetry_freshness_status") == "stale" and internal.get("eta_source") == "live_tracking":
        conf = "low"
    lu = internal.get("last_updated_at")
    ws = internal.get("eta_window_start")
    we = internal.get("eta_window_end")
    return {
        "eta_minutes": internal.get("eta_minutes"),
        "eta_window_start": _aware(ws).isoformat() if isinstance(ws, datetime) else ws,
        "eta_window_end": _aware(we).isoformat() if isinstance(we, datetime) else we,
        "eta_confidence": conf,
        "eta_source": internal.get("eta_source"),
        "last_updated_at": _aware(lu).isoformat() if isinstance(lu, datetime) else lu,
    }


def _rounded_coord(lat: float, lon: float, decimals: int = 2) -> tuple[float, float]:
    return round(lat, decimals), round(lon, decimals)


def build_customer_safe_map_payload(db: Session, *, job: Job) -> dict[str, Any] | None:
    """
    Only when engineer is on the way and live telemetry is usable; heavily reduced precision.
    """
    if not (job.en_route_at or job.on_my_way_sent_at):
        return None
    if not job.assigned_engineer_id:
        return None
    op = resolve_operational_position_for_engineer(db, engineer_id=job.assigned_engineer_id)
    if not op or op.freshness_status not in ("fresh", "aging"):
        return None
    lat, lon = _rounded_coord(op.latitude, op.longitude)
    dest = resolve_job_destination_lat_lon(db, job=job)
    band = "unknown"
    if dest:
        from backend.app.modules.tracking.service import haversine_m

        d_km = haversine_m(lat1=op.latitude, lon1=op.longitude, lat2=dest[0], lon2=dest[1]) / 1000.0
        if d_km < 5:
            band = "under_5_km"
        elif d_km < 15:
            band = "under_15_km"
        else:
            band = "over_15_km"
    return {
        "approximate_engineer_position": {"latitude": lat, "longitude": lon},
        "precision": "reduced",
        "distance_band": band,
        "freshness": op.freshness_status,
    }


def build_customer_job_timeline(db: Session, *, job_id: str) -> list[dict[str, Any]]:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    labels: dict[str, str] = {
        "job_created": "We received your service request",
        "quote_accepted": "Quote accepted",
        "scheduled": "Visit scheduled",
        "dispatched": "An engineer has been assigned",
        "en_route": "Engineer is on the way",
        "customer_on_my_way_signal": "On the way — ETA updating",
        "on_site": "Engineer has arrived",
        "status_completed": "Work completed",
        "certificate": "Certificate issued",
        "invoice_issued": "Invoice issued",
        "payment_received": "Payment received",
    }

    from backend.app.modules.dispatch.operational_tracking_service import build_internal_job_timeline

    internal = build_internal_job_timeline(db, job_id=job_id)
    out: list[dict[str, Any]] = []
    for ev in internal:
        et = ev["event_type"]
        if et in ("quote_updated", "resolved"):
            continue
        out.append(
            {
                "at": ev["at"],
                "milestone": et,
                "title": labels.get(et, ev["summary"]),
            }
        )
    return out
