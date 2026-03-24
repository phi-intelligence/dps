from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.time_tracking.models import Punch
from backend.app.modules.time_tracking.models import TimesheetApproval
from backend.app.modules.tracking.models import JobGeofence
from backend.app.modules.tracking.service import check_point_in_geofence
from backend.app.core.config import settings


def utc_date_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).date().isoformat()


def compute_job_work_seconds(db: Session, *, job_id: str) -> int:
    """
    Pair punch-in/out for the job and sum durations (per user, FIFO).
    Used for job costing and invoicing labour stub.
    """
    punches = (
        db.query(Punch)
        .filter(Punch.job_id == job_id, Punch.kind.in_(["in", "out"]))
        .order_by(Punch.occurred_at.asc())
        .all()
    )
    open_by_user: dict[str, Punch] = {}
    total_seconds = 0
    for p in punches:
        if p.kind == "in":
            open_by_user[p.user_id] = p
        elif p.kind == "out":
            open_in = open_by_user.get(p.user_id)
            if not open_in:
                continue
            total_seconds += int((p.occurred_at - open_in.occurred_at).total_seconds())
            open_by_user.pop(p.user_id, None)
    return max(total_seconds, 0)


def punch_in(
    db: Session,
    *,
    user_id: str,
    payload: "PunchInOutIn",
) -> Punch:
    job_id = payload.job_id
    geofence = db.query(JobGeofence).filter(JobGeofence.job_id == job_id).one_or_none()
    if not geofence:
        raise ValueError("No geofence configured for this job")

    # Security/consistency: engineer can only punch for jobs they are assigned to.
    from backend.app.modules.dispatch.models import Job

    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != user_id:
        raise ValueError("Job is assigned to another engineer")

    latest = (
        db.query(Punch)
        .filter(Punch.user_id == user_id, Punch.job_id == job_id, Punch.kind.in_(["in", "out"]))
        .order_by(Punch.occurred_at.desc(), Punch.created_at.desc())
        .first()
    )
    if latest and latest.kind == "in":
        raise ValueError("Already punched in for this job; punch-out before punching in again")

    in_geofence, distance_m = check_point_in_geofence(
        latitude=payload.latitude, longitude=payload.longitude, geofence=geofence
    )

    if not in_geofence:
        # Enforce geofence validation per plan.
        raise ValueError("Geofence validation failed for punch-in")

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    punch = Punch(
        user_id=user_id,
        job_id=job_id,
        kind="in",
        occurred_at=occurred_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        valid=True,
        distance_m=distance_m,
        offline_device_id=payload.offline_device_id,
    )
    db.add(punch)
    db.commit()
    db.refresh(punch)

    # Minimal cross-module effect: when a valid engineer clocks in, mark job as "on_site".
    from backend.app.modules.dispatch.models import Job

    job = db.get(Job, job_id)
    if job:
        job.status = "on_site"
        db.commit()

    return punch


def punch_out(
    db: Session,
    *,
    user_id: str,
    payload: "PunchInOutIn",
) -> Punch:
    job_id = payload.job_id

    geofence = db.query(JobGeofence).filter(JobGeofence.job_id == job_id).one_or_none()
    if not geofence:
        raise ValueError("No geofence configured for this job")

    # Security/consistency: engineer can only punch for jobs they are assigned to.
    from backend.app.modules.dispatch.models import Job

    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != user_id:
        raise ValueError("Job is assigned to another engineer")

    in_geofence, distance_m = check_point_in_geofence(
        latitude=payload.latitude, longitude=payload.longitude, geofence=geofence
    )

    # Allow clock-out even if slightly outside, but mark invalid if it fails validation.
    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    latest = (
        db.query(Punch)
        .filter(Punch.user_id == user_id, Punch.job_id == job_id, Punch.kind.in_(["in", "out"]))
        .order_by(Punch.occurred_at.desc(), Punch.created_at.desc())
        .first()
    )

    if not latest or latest.kind != "in":
        raise ValueError("No previous punch-in found for this job")

    punch = Punch(
        user_id=user_id,
        job_id=job_id,
        kind="out",
        occurred_at=occurred_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        valid=bool(in_geofence),
        distance_m=distance_m,
        offline_device_id=payload.offline_device_id,
    )
    db.add(punch)
    db.commit()
    db.refresh(punch)

    # Phase 3.1 completion gate:
    # - clock-out triggers "attempt completion"
    # - final job status becomes `completed` only if required forms are satisfied
    from backend.app.modules.dispatch.models import Job

    job = db.get(Job, job_id)
    if job:
        job.status = "completion_pending_forms"
        db.commit()

        from backend.app.modules.dispatch.service import try_finalize_job_completion_if_possible
        from backend.app.modules.inventory.service import consume_parts_for_quote

        finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)

        # Only consume reserved materials once the job is fully completed.
        if finalized.status == "completed" and finalized.quote_id:
            consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)

        db.commit()

    return punch


def get_timesheet(db: Session, *, user_id: str, date_str: str) -> "TimesheetOut":
    # UTC date boundaries for consistent aggregation.
    start = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    end = start.replace(hour=23, minute=59, second=59)

    punches = (
        db.query(Punch)
        .filter(Punch.user_id == user_id, Punch.kind.in_(["in", "out"]))
        .filter(Punch.occurred_at >= start, Punch.occurred_at <= end)
        .order_by(Punch.occurred_at.asc())
        .all()
    )

    sessions: list[dict[str, object]] = []
    open_in: Punch | None = None

    for p in punches:
        if p.kind == "in":
            open_in = p
        elif p.kind == "out" and open_in:
            duration = int((p.occurred_at - open_in.occurred_at).total_seconds())
            sessions.append(
                {
                    "job_id": open_in.job_id,
                    "clock_in_punch_id": open_in.id,
                    "clock_out_punch_id": p.id,
                    "clock_in_at": open_in.occurred_at,
                    "clock_out_at": p.occurred_at,
                    "duration_seconds": max(duration, 0),
                }
            )
            open_in = None

    total_seconds = sum(int(s["duration_seconds"]) for s in sessions) if sessions else 0
    from backend.app.modules.time_tracking.schemas import TimesheetOut

    return TimesheetOut(user_id=user_id, date=date_str, total_seconds=total_seconds, sessions=sessions)


def split_regular_overtime(total_seconds: int, *, regular_daily_seconds: int = 8 * 3600) -> tuple[int, int]:
    regular_seconds = min(total_seconds, regular_daily_seconds)
    overtime_seconds = max(0, total_seconds - regular_seconds)
    return regular_seconds, overtime_seconds


def approve_timesheet(
    db: Session,
    *,
    user_id: str,
    date_str: str,
    approved_by_user_id: str,
) -> TimesheetApproval:
    # Compute from raw punches.
    ts = get_timesheet(db, user_id=user_id, date_str=date_str)
    regular_seconds, overtime_seconds = split_regular_overtime(ts.total_seconds)

    existing = (
        db.query(TimesheetApproval)
        .filter(TimesheetApproval.user_id == user_id, TimesheetApproval.date_str == date_str)
        .one_or_none()
    )

    if existing:
        existing.total_seconds = int(ts.total_seconds)
        existing.regular_seconds = int(regular_seconds)
        existing.overtime_seconds = int(overtime_seconds)
        existing.status = "approved"
        existing.approved_by_user_id = approved_by_user_id
        existing.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    approval = TimesheetApproval(
        user_id=user_id,
        date_str=date_str,
        total_seconds=int(ts.total_seconds),
        regular_seconds=int(regular_seconds),
        overtime_seconds=int(overtime_seconds),
        status="approved",
        approved_by_user_id=approved_by_user_id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def export_payroll_for_date(db: Session, *, date_str: str) -> "PayrollExportOut":
    regular_rate = float(getattr(settings, "PHI_DPS_LABOUR_HOURLY_RATE", 60.0))
    overtime_multiplier = float(getattr(settings, "PHI_DPS_OVERTIME_MULTIPLIER", 1.5))

    approvals = (
        db.query(TimesheetApproval)
        .filter(TimesheetApproval.date_str == date_str, TimesheetApproval.status == "approved")
        .all()
    )

    lines = []
    # Local import to avoid circular references at module import time.
    from backend.app.modules.time_tracking.schemas import PayrollExportOut, PayrollLineOut

    for a in approvals:
        regular_hours = a.regular_seconds / 3600.0
        overtime_hours = a.overtime_seconds / 3600.0
        amount = round(regular_hours * regular_rate + overtime_hours * regular_rate * overtime_multiplier, 2)
        lines.append(
            PayrollLineOut(
                user_id=a.user_id,
                date_str=a.date_str,
                total_seconds=a.total_seconds,
                regular_seconds=a.regular_seconds,
                overtime_seconds=a.overtime_seconds,
                amount=amount,
            )
        )

    return PayrollExportOut(date_str=date_str, lines=lines)

