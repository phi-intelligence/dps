from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.competence.models import Qualification
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.time_tracking.models import Punch


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


TERMINAL_JOB_STATUSES = frozenset({"completed", "closed", "cancelled"})
ON_JOB_STATUSES = frozenset({"in_progress"})


def _active_assigned_jobs(db: Session, *, engineer_id: str) -> list[Job]:
    return (
        db.query(Job)
        .filter(
            Job.assigned_engineer_id == engineer_id,
            Job.status.not_in(TERMINAL_JOB_STATUSES),
        )
        .all()
    )


def _last_open_punch(db: Session, *, user_id: str) -> Punch | None:
    """
    Most recent punch for user (any job). Used as a weak signal for on-site / travelling.
    """
    return (
        db.query(Punch)
        .filter(Punch.user_id == user_id)
        .order_by(Punch.occurred_at.desc())
        .first()
    )


def engineer_has_valid_competencies(
    db: Session,
    *,
    engineer_id: str,
    required_competencies: list[str],
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    if not required_competencies:
        return True, None
    now = _aware_utc(now or utc_now())
    need = set(required_competencies)
    quals = (
        db.query(Qualification)
        .filter(
            Qualification.engineer_user_id == engineer_id,
            Qualification.competency.in_(list(need)),
            Qualification.status == "active",
        )
        .all()
    )
    active: set[str] = set()
    for q in quals:
        if q.expires_at is None or _aware_utc(q.expires_at) >= now:
            active.add(q.competency)
    missing = need - active
    if missing:
        return False, f"missing_or_expired:{','.join(sorted(missing))}"
    return True, None


def compute_engineer_availability(
    db: Session,
    *,
    engineer_id: str,
    required_competencies: list[str] | None = None,
    now: datetime | None = None,
) -> str:
    """
    Operational availability classification for dispatch (not HR scheduling).
    """
    now = _aware_utc(now or utc_now())
    req = [c for c in (required_competencies or []) if c]

    ok_comp, _reason = engineer_has_valid_competencies(db, engineer_id=engineer_id, required_competencies=req, now=now)
    if not ok_comp:
        return "unavailable_competency"

    op = resolve_operational_position_for_engineer(db, engineer_id=engineer_id, now=now)
    if not op:
        return "stale_location"
    if op.freshness_status == "stale":
        return "stale_location"

    jobs = _active_assigned_jobs(db, engineer_id=engineer_id)
    if any(j.status in ON_JOB_STATUSES for j in jobs):
        return "on_job"
    if jobs:
        # Accepted / dispatched / created-with-assignment treated as committed workload.
        st = {j.status for j in jobs}
        if "accepted" in st:
            return "busy"
        return "travelling"

    lp = _last_open_punch(db, user_id=engineer_id)
    if lp and lp.kind == "in":
        return "on_job"

    # No shift calendar yet — treat as available when competency + telemetry ok.
    return "available"


def count_active_assigned_jobs(db: Session, *, engineer_id: str) -> int:
    return len(_active_assigned_jobs(db, engineer_id=engineer_id))


def compute_engineer_workload_band(db: Session, *, engineer_id: str) -> str:
    """
    Assignment/punch workload only (ignores telemetry freshness). Used by dispatch scoring.
    """
    jobs = _active_assigned_jobs(db, engineer_id=engineer_id)
    if any(j.status in ON_JOB_STATUSES for j in jobs):
        return "on_job"
    if jobs:
        if any(j.status == "accepted" for j in jobs):
            return "busy"
        return "travelling"

    lp = _last_open_punch(db, user_id=engineer_id)
    if lp and lp.kind == "in":
        return "on_job"

    return "available"
