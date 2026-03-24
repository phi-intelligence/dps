"""
Shared operational truth for job ETA, tracking, and timelines.
Used by internal dispatch endpoints and derived customer portal views.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.dispatch.models import Job, JobEtaDelayNotice, JobEtaState
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.portal.models import CustomerCommsEvent
from backend.app.modules.quoting.models import Quote
from backend.app.modules.sites.models import Site
from backend.app.modules.tracking.service import get_job_geofence, haversine_m
from backend.app.services.runtime_settings_service import get_effective_dispatch_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


TelemetryFreshness = Literal["fresh", "aging", "stale", "unknown"]
EtaConfidence = Literal["high", "medium", "low", "unavailable"]
EtaSource = Literal["live_tracking", "schedule_window", "manual_override", "unavailable"]


def resolve_job_destination_lat_lon(db: Session, *, job: Job) -> tuple[float, float] | None:
    gf = get_job_geofence(db, job_id=job.id)
    if gf:
        return float(gf.latitude), float(gf.longitude)
    if job.site_latitude is not None and job.site_longitude is not None:
        return float(job.site_latitude), float(job.site_longitude)
    if job.site_id:
        site = db.get(Site, job.site_id)
        if site and site.latitude is not None and site.longitude is not None:
            return float(site.latitude), float(site.longitude)
    if job.address_geocoded_latitude is not None and job.address_geocoded_longitude is not None:
        return float(job.address_geocoded_latitude), float(job.address_geocoded_longitude)
    return None


def _freshness_to_telemetry_status(fs: str | None) -> TelemetryFreshness:
    if fs in ("fresh", "aging", "stale"):
        return fs  # type: ignore[return-value]
    return "unknown"


def compute_internal_job_eta(
    db: Session,
    *,
    job_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Full internal ETA payload. Does not mask operational detail.
    """
    now = now or utc_now()
    now = _aware(now)
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    ds = get_effective_dispatch_settings(db)
    avg_speed_mps = float(ds["avg_vehicle_speed_mps"])
    schedule_window_before = timedelta(minutes=30)
    schedule_window_after = timedelta(minutes=60)

    base: dict[str, Any] = {
        "job_id": job_id,
        "eta_minutes": None,
        "eta_window_start": None,
        "eta_window_end": None,
        "eta_confidence": "unavailable",
        "eta_source": "unavailable",
        "last_updated_at": now,
        "operational_position_source": None,
        "telemetry_freshness_status": "unknown",
    }

    # 1) Manual override (dispatcher-set), if recent (48h).
    if job.manual_eta_minutes is not None and job.manual_eta_set_at:
        age = now - _aware(job.manual_eta_set_at)
        if age.total_seconds() < 48 * 3600:
            base["eta_minutes"] = float(job.manual_eta_minutes)
            base["eta_confidence"] = "high"
            base["eta_source"] = "manual_override"
            base["last_updated_at"] = _aware(job.manual_eta_set_at)
            base["telemetry_freshness_status"] = "unknown"
            base["operational_position_source"] = None
            return base

    dest = resolve_job_destination_lat_lon(db, job=job)
    op = None
    if job.assigned_engineer_id:
        op = resolve_operational_position_for_engineer(db, engineer_id=job.assigned_engineer_id, now=now)

    if op and dest and op.freshness_status in ("fresh", "aging"):
        distance_m = haversine_m(
            lat1=op.latitude,
            lon1=op.longitude,
            lat2=dest[0],
            lon2=dest[1],
        )
        eta_min = float(distance_m / max(avg_speed_mps, 0.1) / 60.0)
        margin = max(5.0, eta_min * 0.15)
        base["eta_minutes"] = eta_min
        base["eta_window_start"] = now + timedelta(minutes=max(0.0, eta_min - margin))
        base["eta_window_end"] = now + timedelta(minutes=eta_min + margin)
        base["eta_source"] = "live_tracking"
        base["operational_position_source"] = op.source
        base["telemetry_freshness_status"] = _freshness_to_telemetry_status(op.freshness_status)
        base["eta_confidence"] = "high" if op.freshness_status == "fresh" else "medium"
        base["last_updated_at"] = op.occurred_at
        return base

    if op and dest and op.freshness_status == "stale":
        # Stale live: degrade and fall through to schedule if possible
        base["telemetry_freshness_status"] = "stale"
        base["operational_position_source"] = op.source

    # 2) Scheduled window fallback
    if job.scheduled_at:
        s = _aware(job.scheduled_at)
        w0 = s - schedule_window_before
        w1 = s + schedule_window_after
        base["eta_window_start"] = w0
        base["eta_window_end"] = w1
        base["eta_source"] = "schedule_window"
        delta = (s - now).total_seconds() / 60.0
        base["eta_minutes"] = max(0.0, delta) if delta > -schedule_window_after.total_seconds() / 60.0 else None
        base["eta_confidence"] = "medium" if op is None or op.freshness_status == "stale" else "low"
        if base["telemetry_freshness_status"] == "unknown":
            base["telemetry_freshness_status"] = "stale" if op else "unknown"
        return base

    # 3) JobEtaState as weak hint
    st = db.query(JobEtaState).filter(JobEtaState.job_id == job_id).one_or_none()
    if st:
        base["eta_minutes"] = float(st.last_eta_minutes)
        base["eta_confidence"] = "low"
        base["eta_source"] = "live_tracking"
        base["last_updated_at"] = _aware(st.last_eta_updated_at)

    return base


def _engineer_on_the_way(job: Job) -> bool:
    return bool(job.en_route_at or job.on_my_way_sent_at)


def _engineer_on_site(job: Job) -> bool:
    return bool(job.on_site_at)


def get_operational_tracking_state(db: Session, *, job_id: str, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    eta = compute_internal_job_eta(db, job_id=job_id, now=now)
    user = db.get(User, job.assigned_engineer_id) if job.assigned_engineer_id else None
    op = None
    if job.assigned_engineer_id:
        op = resolve_operational_position_for_engineer(db, engineer_id=job.assigned_engineer_id, now=now)

    delay = (
        db.query(JobEtaDelayNotice)
        .filter(JobEtaDelayNotice.job_id == job_id, JobEtaDelayNotice.status == "open")
        .order_by(JobEtaDelayNotice.created_at.desc())
        .first()
    )

    last_comms = (
        db.query(CustomerCommsEvent)
        .filter(CustomerCommsEvent.job_id == job_id)
        .order_by(CustomerCommsEvent.created_at.desc())
        .first()
    )

    milestones = [
        job.created_at,
        job.dispatched_at,
        job.en_route_at,
        job.on_site_at,
        job.resolved_at,
        job.customer_notified_at,
        job.on_my_way_sent_at,
        job.manual_eta_set_at,
    ]
    last_update = max((m for m in milestones if m is not None), default=job.created_at)

    return {
        "job_id": job_id,
        "internal_status": job.status,
        "assigned_engineer_id": job.assigned_engineer_id,
        "assigned_vehicle_id": user.assigned_vehicle_id if user else None,
        "live_position_source": op.source if op else None,
        "telemetry_freshness": op.freshness_status if op else None,
        "engineer_on_the_way": _engineer_on_the_way(job),
        "engineer_on_site": _engineer_on_site(job),
        "eta": eta,
        "on_my_way_sent_at": job.on_my_way_sent_at,
        "customer_notified_at": job.customer_notified_at,
        "last_status_update_at": _aware(last_update),
        "delay_notice": delay.message if delay else None,
        "delay_notice_at": delay.created_at if delay else None,
        "last_comms_event": last_comms.event_type if last_comms else None,
        "last_comms_at": last_comms.created_at if last_comms else None,
    }


def build_internal_job_timeline(db: Session, *, job_id: str) -> list[dict[str, Any]]:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    events: list[dict[str, Any]] = []

    def add(ts: datetime | None, event_type: str, summary: str, detail: dict[str, Any] | None = None) -> None:
        if not ts:
            return
        events.append(
            {
                "at": _aware(ts).isoformat(),
                "event_type": event_type,
                "summary": summary,
                "detail": detail or {},
            }
        )

    add(job.created_at, "job_created", "Job created", {"status": job.status})
    if job.quote_id:
        q = db.get(Quote, job.quote_id)
        if q and q.accepted_at:
            add(q.accepted_at, "quote_accepted", "Quote accepted", {"quote_id": q.id})
        elif q:
            add(q.created_at, "quote_updated", f"Quote status: {q.status}", {"quote_id": q.id})
    add(job.scheduled_at, "scheduled", "Visit scheduled", {})
    add(job.dispatched_at, "dispatched", "Engineer dispatched", {"engineer_id": job.assigned_engineer_id})
    add(job.en_route_at, "en_route", "Engineer en route", {})
    add(job.on_my_way_sent_at, "customer_on_my_way_signal", "On-my-way signal recorded for customer comms", {})
    add(job.on_site_at, "on_site", "Engineer on site", {})
    add(job.resolved_at, "resolved", "Work resolved / completed checkpoint", {})

    if job.status in ("completed", "closed"):
        add(job.resolved_at or job.created_at, "status_completed", f"Job status: {job.status}", {})

    for cert in db.query(Certificate).filter(Certificate.job_id == job_id).order_by(Certificate.created_at.asc()).all():
        add(cert.created_at, "certificate", f"Certificate {cert.certificate_type}", {"certificate_id": cert.id})

    for inv in db.query(Invoice).filter(Invoice.job_id == job_id).order_by(Invoice.created_at.asc()).all():
        add(inv.created_at, "invoice_issued", f"Invoice {inv.status}", {"invoice_id": inv.id})
        if inv.paid_at:
            add(inv.paid_at, "payment_received", "Payment received", {"invoice_id": inv.id})

    events.sort(key=lambda e: e["at"])
    return events
