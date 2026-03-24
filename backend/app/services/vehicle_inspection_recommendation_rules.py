"""Ops recommendations for vehicle pre-use inspection and defects."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.models import Job
from backend.app.modules.vehicles.models import VehicleDefect, VehicleInspection
from backend.app.services.recommendation_engine import _register
from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness, utc_now


def _utc_date(dt: datetime):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


def register_vehicle_inspection_recommendations(db: Session, active_keys: set[str], *, now: datetime | None = None) -> None:
    now = now or utc_now()
    today = _utc_date(now)
    horizon = now + timedelta(days=7)

    # Engineers with assigned vans: no inspection today
    for u in db.query(User).filter(User.assigned_vehicle_id.isnot(None)).all():
        vid = (u.assigned_vehicle_id or "").strip()
        if not vid:
            continue
        r = evaluate_vehicle_readiness(db, vehicle_id=vid, now=now)
        if "no_inspection_today" in r.reasons:
            key = f"vehicle:no-inspection-today:{vid}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="vehicle_no_inspection_today",
                category="vehicle_readiness",
                severity="medium",
                confidence="high",
                title=f"Daily vehicle inspection missing: {vid}",
                summary="No pre-use inspection recorded today (UTC) for an assigned service vehicle.",
                detail={
                    "vehicle_id": vid,
                    "engineer_id": u.id,
                    "suggested_action": "Complete H&S pre-use check before field work.",
                },
                entity_type="vehicle",
                entity_id=vid,
                related_engineer_id=u.id,
            )

    # Failed critical inspection today
    for insp in (
        db.query(VehicleInspection)
        .filter(
            VehicleInspection.inspection_date == today,
            VehicleInspection.overall_status == "failed_critical",
        )
        .all()
    ):
        key = f"vehicle:failed-critical-inspection:{insp.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="vehicle_inspection_failed_critical",
            category="vehicle_readiness",
            severity="critical",
            confidence="high",
            title=f"Critical vehicle inspection failure: {insp.vehicle_id}",
            summary="Today's pre-use inspection recorded a critical failure — vehicle must not be used until cleared.",
            detail={
                "vehicle_id": insp.vehicle_id,
                "inspection_id": insp.id,
                "engineer_id": insp.engineer_id,
                "suggested_action": "Ground vehicle, log defects, and arrange workshop review.",
            },
            entity_type="vehicle",
            entity_id=insp.vehicle_id,
            related_engineer_id=insp.engineer_id,
            related_job_id=None,
        )

    # Unresolved critical defects (one open rec per defect id for stable dedupe)
    for d in (
        db.query(VehicleDefect)
        .filter(VehicleDefect.status == "open", VehicleDefect.severity == "critical")
        .all()
    ):
        key = f"vehicle:unresolved-critical-defect:{d.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="vehicle_critical_defect_open",
            category="vehicle_readiness",
            severity="critical",
            confidence="high",
            title=f"Critical vehicle defect open: {d.title[:80]}",
            summary=f"Vehicle {d.vehicle_id} has an unresolved critical defect.",
            detail={
                "defect_id": d.id,
                "vehicle_id": d.vehicle_id,
                "title": d.title,
                "suggested_action": "Resolve or formally ground vehicle before dispatch.",
            },
            entity_type="vehicle",
            entity_id=d.vehicle_id,
        )

    # Blocked readiness vehicle still has upcoming assigned work
    seen_v: set[str] = set()
    for u in db.query(User).filter(User.assigned_vehicle_id.isnot(None)).all():
        vid = (u.assigned_vehicle_id or "").strip()
        if not vid or vid in seen_v:
            continue
        seen_v.add(vid)
        r = evaluate_vehicle_readiness(db, vehicle_id=vid, now=now)
        if r.readiness_status != "blocked":
            continue
        upcoming = (
            db.query(Job)
            .filter(
                Job.assigned_engineer_id == u.id,
                Job.status.not_in(["completed", "closed", "cancelled"]),
                Job.scheduled_at.isnot(None),
                Job.scheduled_at >= now,
                Job.scheduled_at <= horizon,
            )
            .order_by(Job.scheduled_at.asc())
            .first()
        )
        if not upcoming:
            continue
        key = f"vehicle:blocked-with-upcoming:{vid}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="vehicle_blocked_assigned_upcoming_work",
            category="vehicle_readiness",
            severity="critical",
            confidence="high",
            title=f"Blocked vehicle has upcoming assigned work: {vid}",
            summary="Vehicle readiness is blocked but the assigned engineer has scheduled work soon.",
            detail={
                "vehicle_id": vid,
                "engineer_id": u.id,
                "next_job_id": upcoming.id,
                "readiness": r.to_dict(),
                "suggested_action": "Reassign jobs, substitute vehicle, or clear inspection/defects.",
            },
            entity_type="vehicle",
            entity_id=vid,
            related_engineer_id=u.id,
            related_job_id=upcoming.id,
        )
