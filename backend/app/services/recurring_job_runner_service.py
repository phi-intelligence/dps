"""
Recurring system job orchestration: definitions, scheduling, run history, safe catalog handlers.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.system.recurring_system_job_models import RecurringSystemJob, RecurringSystemJobRun
from backend.app.services import contract_activation_scheduler_service as casc
from backend.app.services import recommendation_engine as rec_engine
from backend.app.services import recurring_job_workflow_scans as scan_wf


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


# --- Catalog keys (stable) ---
JOB_SCHEDULED_CONTRACT_AMENDMENT_ACTIVATION = "scheduled_contract_amendment_activation"
JOB_RECOMMENDATION_SCAN = "recommendation_scan"
JOB_PROPOSAL_FOLLOW_UP_SCAN = "proposal_follow_up_scan"
JOB_ACTIVATION_CONFIRMATION_FOLLOW_UP_SCAN = "activation_confirmation_follow_up_scan"
JOB_LOW_RISK_AUTOMATION_SCAN = "low_risk_automation_scan"
JOB_EQUIPMENT_VEHICLE_ATTENTION_SCAN = "equipment_vehicle_attention_scan"


def system_actor_user_id(db: Session) -> str:
    u = db.query(User).filter(User.email == "admin@example.com").first()
    if u:
        return u.id
    u2 = db.query(User).first()
    if not u2:
        raise RuntimeError("No user for system job actor")
    return u2.id


def compute_next_run_at(job: RecurringSystemJob, *, after: datetime) -> datetime | None:
    if job.schedule_type == "manual_only":
        return None
    if job.schedule_type == "interval_minutes":
        mins = int((job.schedule_expression or "60").strip() or "60")
        return after + timedelta(minutes=max(1, mins))
    if job.schedule_type in ("daily", "cron_like"):
        expr = (job.schedule_expression or "09:00").strip()
        parts = expr.split(":")
        h = int(parts[0]) if parts else 9
        m = int(parts[1]) if len(parts) > 1 else 0
        tz_name = job.timezone_name or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        local_after = after.astimezone(tz)
        cand = local_after.replace(hour=h, minute=m, second=0, microsecond=0)
        if cand <= local_after:
            cand = cand + timedelta(days=1)
        return cand.astimezone(timezone.utc)
    return None


DEFAULT_JOB_SEED: list[dict[str, Any]] = [
    {
        "job_key": JOB_SCHEDULED_CONTRACT_AMENDMENT_ACTIVATION,
        "job_type": "activation",
        "name": "Scheduled contract amendment activation",
        "description": "Activates due approved/scheduled amendments (idempotent).",
        "schedule_type": "interval_minutes",
        "schedule_expression": "60",
        "dry_run_default": False,
        "payload_json": "{}",
    },
    {
        "job_key": JOB_RECOMMENDATION_SCAN,
        "job_type": "ops_scan",
        "name": "Operational recommendation scan",
        "description": "Full recommendation scan + auto-resolve stale (no direct final actions).",
        "schedule_type": "interval_minutes",
        "schedule_expression": "30",
        "dry_run_default": False,
        "payload_json": "{}",
    },
    {
        "job_key": JOB_PROPOSAL_FOLLOW_UP_SCAN,
        "job_type": "commercial_follow_up",
        "name": "Repricing proposal follow-up scan",
        "description": "Draft reminder comms + internal tasks for stale proposals.",
        "schedule_type": "interval_minutes",
        "schedule_expression": "180",
        "dry_run_default": False,
        "payload_json": json.dumps(
            {
                "released_no_view_days": 7,
                "viewed_no_response_days": 7,
                "esign_incomplete_days": 5,
            }
        ),
    },
    {
        "job_key": JOB_ACTIVATION_CONFIRMATION_FOLLOW_UP_SCAN,
        "job_type": "commercial_follow_up",
        "name": "Activation confirmation follow-up scan",
        "description": "Draft reminder / acknowledgement follow-ups for stale confirmations.",
        "schedule_type": "interval_minutes",
        "schedule_expression": "180",
        "dry_run_default": False,
        "payload_json": json.dumps(
            {"released_not_viewed_days": 7, "viewed_not_acknowledged_days": 7}
        ),
    },
    {
        "job_key": JOB_LOW_RISK_AUTOMATION_SCAN,
        "job_type": "automation",
        "name": "Low-risk automation scan",
        "description": "Draft/task automation for eligible open recommendations.",
        "schedule_type": "interval_minutes",
        "schedule_expression": "120",
        "dry_run_default": False,
        "payload_json": json.dumps({"recommendation_limit": 40}),
    },
    {
        "job_key": JOB_EQUIPMENT_VEHICLE_ATTENTION_SCAN,
        "job_type": "ops_scan",
        "name": "Equipment & vehicle attention scan",
        "description": "Registers equipment + vehicle readiness recommendations only.",
        "schedule_type": "interval_minutes",
        "schedule_expression": "180",
        "dry_run_default": False,
        "payload_json": "{}",
    },
]


def ensure_recurring_jobs_seeded(db: Session, *, commit: bool = True) -> int:
    n = 0
    now = utc_now()
    for row in DEFAULT_JOB_SEED:
        existing = db.query(RecurringSystemJob).filter(RecurringSystemJob.job_key == row["job_key"]).first()
        if existing:
            continue
        j = RecurringSystemJob(
            id=str(uuid.uuid4()),
            job_key=row["job_key"],
            job_type=row["job_type"],
            name=row["name"],
            description=row.get("description"),
            enabled=True,
            schedule_type=row["schedule_type"],
            schedule_expression=row.get("schedule_expression"),
            timezone_name=row.get("timezone_name"),
            last_run_at=None,
            next_run_at=now if row["schedule_type"] != "manual_only" else None,
            max_runtime_seconds=row.get("max_runtime_seconds"),
            dry_run_default=bool(row.get("dry_run_default", False)),
            payload_json=row.get("payload_json"),
            created_at=now,
            updated_at=now,
        )
        db.add(j)
        n += 1
    if commit and n:
        db.commit()
    elif not commit and n:
        db.flush()
    return n


Handler = Callable[[Session, bool, str | None, RecurringSystemJob], dict[str, Any]]


def _handle_scheduled_activation(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    uid = actor_user_id or system_actor_user_id(db)
    return casc.run_due_amendment_activations(db, now=None, limit=None, dry_run=dry_run, actor_user_id=uid)


def _handle_recommendation_scan(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    out = rec_engine.run_recommendation_scan(db, now=None, commit=not dry_run)
    if dry_run:
        db.rollback()
    return out


def _handle_proposal_follow_up(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    return scan_wf.run_proposal_follow_up_scan(
        db, dry_run=dry_run, actor_user_id=actor_user_id, payload_json=job.payload_json
    )


def _handle_activation_follow_up(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    return scan_wf.run_activation_confirmation_follow_up_scan(
        db, dry_run=dry_run, actor_user_id=actor_user_id, payload_json=job.payload_json
    )


def _handle_low_risk_automation(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    uid = actor_user_id or system_actor_user_id(db)
    return scan_wf.run_low_risk_automation_scan(
        db, dry_run=dry_run, actor_user_id=uid, payload_json=job.payload_json
    )


def _handle_equipment_vehicle(
    db: Session, dry_run: bool, actor_user_id: str | None, job: RecurringSystemJob
) -> dict[str, Any]:
    return scan_wf.run_equipment_vehicle_attention_scan(db, dry_run=dry_run, now=None)


JOB_HANDLERS: dict[str, Handler] = {
    JOB_SCHEDULED_CONTRACT_AMENDMENT_ACTIVATION: _handle_scheduled_activation,
    JOB_RECOMMENDATION_SCAN: _handle_recommendation_scan,
    JOB_PROPOSAL_FOLLOW_UP_SCAN: _handle_proposal_follow_up,
    JOB_ACTIVATION_CONFIRMATION_FOLLOW_UP_SCAN: _handle_activation_follow_up,
    JOB_LOW_RISK_AUTOMATION_SCAN: _handle_low_risk_automation,
    JOB_EQUIPMENT_VEHICLE_ATTENTION_SCAN: _handle_equipment_vehicle,
}


def list_jobs(db: Session) -> list[RecurringSystemJob]:
    ensure_recurring_jobs_seeded(db, commit=True)
    return db.query(RecurringSystemJob).order_by(RecurringSystemJob.job_key).all()


def get_job(db: Session, *, job_id: str) -> RecurringSystemJob | None:
    return db.get(RecurringSystemJob, job_id)


def get_job_by_key(db: Session, *, job_key: str) -> RecurringSystemJob | None:
    return db.query(RecurringSystemJob).filter(RecurringSystemJob.job_key == job_key).first()


def patch_job(
    db: Session,
    *,
    job_id: str,
    enabled: bool | None = None,
    schedule_type: str | None = None,
    schedule_expression: str | None = None,
    timezone_name: str | None = None,
    dry_run_default: bool | None = None,
    payload_json: str | None = None,
    next_run_at: datetime | None = None,
    commit: bool = True,
) -> RecurringSystemJob:
    j = db.get(RecurringSystemJob, job_id)
    if not j:
        raise ValueError("Job not found")
    if enabled is not None:
        j.enabled = enabled
    if schedule_type is not None:
        j.schedule_type = schedule_type
    if schedule_expression is not None:
        j.schedule_expression = schedule_expression
    if timezone_name is not None:
        j.timezone_name = timezone_name
    if dry_run_default is not None:
        j.dry_run_default = dry_run_default
    if payload_json is not None:
        j.payload_json = payload_json
    if next_run_at is not None:
        j.next_run_at = next_run_at
    j.updated_at = utc_now()
    db.add(j)
    if commit:
        db.commit()
        db.refresh(j)
    else:
        db.flush()
        db.refresh(j)
    return j


def list_due_jobs(db: Session, *, now: datetime | None = None) -> list[RecurringSystemJob]:
    now = now or utc_now()
    ensure_recurring_jobs_seeded(db, commit=True)
    return (
        db.query(RecurringSystemJob)
        .filter(
            RecurringSystemJob.enabled.is_(True),
            RecurringSystemJob.schedule_type != "manual_only",
            RecurringSystemJob.next_run_at.isnot(None),
            RecurringSystemJob.next_run_at <= now,
        )
        .order_by(RecurringSystemJob.next_run_at.asc())
        .all()
    )


def run_job(
    db: Session,
    *,
    job_key: str,
    dry_run: bool,
    actor_user_id: str | None,
    trigger_type: str,
    advance_schedule: bool = True,
    commit: bool = True,
) -> RecurringSystemJobRun:
    ensure_recurring_jobs_seeded(db, commit=True)
    job = get_job_by_key(db, job_key=job_key)
    if not job:
        raise ValueError("Unknown job_key")
    if not job.enabled and trigger_type == "scheduled":
        raise ValueError("Job is disabled")
    handler = JOB_HANDLERS.get(job_key)
    if not handler:
        raise ValueError(f"No handler for job_key={job_key}")

    run = RecurringSystemJobRun(
        id=str(uuid.uuid4()),
        recurring_job_id=job.id,
        job_key=job_key,
        trigger_type=trigger_type,
        status="started",
        started_at=utc_now(),
        dry_run=dry_run,
        triggered_by_user_id=actor_user_id,
        idempotency_key=f"{job_key}:{trigger_type}:{int(utc_now().timestamp() // 300)}",
    )
    db.add(run)
    db.flush()

    now = utc_now()
    try:
        result = handler(db, dry_run, actor_user_id, job)
        run.status = "succeeded"
        run.completed_at = utc_now()
        if isinstance(result, dict):
            run.result_summary = (result.get("result_summary") or _dumps(result))[:2000]
            run.result_json = _dumps(result)
            run.created_count = int(
                result.get("created")
                or result.get("candidate_count")
                or result.get("keys_active")
                or result.get("processed")
                or result.get("created_runs")
                or 0
            )
            run.skipped_count = int(result.get("skipped") or 0)
            run.failed_count = int(result.get("failed") or 0)
        else:
            run.result_summary = str(result)[:2000]
            run.result_json = _dumps({"value": str(result)})
            run.created_count = None
            run.skipped_count = None
            run.failed_count = None
        db.add(run)
        if advance_schedule and not dry_run and job.schedule_type != "manual_only":
            job.last_run_at = now
            job.next_run_at = compute_next_run_at(job, after=now)
            job.updated_at = utc_now()
            db.add(job)
        if commit:
            db.commit()
            db.refresh(run)
        else:
            db.flush()
            db.refresh(run)
        return run
    except Exception as e:
        run.status = "failed"
        run.completed_at = utc_now()
        run.error_json = _dumps({"message": str(e)[:4000]})
        run.result_summary = str(e)[:500]
        db.add(run)
        if commit:
            db.commit()
            db.refresh(run)
        else:
            db.flush()
            db.refresh(run)
        return run


def run_due_jobs(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int | None = None,
    dry_run_override: bool | None = None,
    actor_user_id: str | None = None,
    commit: bool = True,
) -> list[RecurringSystemJobRun]:
    due = list_due_jobs(db, now=now)
    if limit is not None:
        due = due[:limit]
    runs: list[RecurringSystemJobRun] = []
    for j in due:
        dr = dry_run_override if dry_run_override is not None else j.dry_run_default
        r = run_job(
            db,
            job_key=j.job_key,
            dry_run=dr,
            actor_user_id=actor_user_id,
            trigger_type="scheduled",
            advance_schedule=not dr,
            commit=commit,
        )
        runs.append(r)
    return runs


def retry_run(
    db: Session,
    *,
    run_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> RecurringSystemJobRun:
    prev = db.get(RecurringSystemJobRun, run_id)
    if not prev:
        raise ValueError("Run not found")
    if prev.status not in ("failed",):
        raise ValueError("Only failed runs can be retried")
    job = db.get(RecurringSystemJob, prev.recurring_job_id)
    if not job:
        raise ValueError("Job definition missing")
    return run_job(
        db,
        job_key=prev.job_key,
        dry_run=prev.dry_run,
        actor_user_id=actor_user_id,
        trigger_type="retry",
        advance_schedule=not prev.dry_run,
        commit=commit,
    )


def list_runs(
    db: Session,
    *,
    job_key: str | None = None,
    status: str | None = None,
    trigger_type: str | None = None,
    dry_run: bool | None = None,
    started_after: datetime | None = None,
    started_before: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[RecurringSystemJobRun]:
    q = db.query(RecurringSystemJobRun).order_by(RecurringSystemJobRun.started_at.desc())
    if job_key:
        q = q.filter(RecurringSystemJobRun.job_key == job_key)
    if status:
        q = q.filter(RecurringSystemJobRun.status == status)
    if trigger_type:
        q = q.filter(RecurringSystemJobRun.trigger_type == trigger_type)
    if dry_run is not None:
        q = q.filter(RecurringSystemJobRun.dry_run.is_(dry_run))
    if started_after:
        q = q.filter(RecurringSystemJobRun.started_at >= started_after)
    if started_before:
        q = q.filter(RecurringSystemJobRun.started_at <= started_before)
    return q.offset(offset).limit(limit).all()


def get_run(db: Session, *, run_id: str) -> RecurringSystemJobRun | None:
    return db.get(RecurringSystemJobRun, run_id)


def dashboard_jobs(db: Session) -> dict[str, Any]:
    ensure_recurring_jobs_seeded(db, commit=True)
    jobs = db.query(RecurringSystemJob).all()
    now = utc_now()
    due = list_due_jobs(db, now=now)
    return {
        "total_jobs": len(jobs),
        "enabled_jobs": sum(1 for j in jobs if j.enabled),
        "due_now_count": len(due),
        "due_job_keys": [j.job_key for j in due],
    }


def dashboard_job_failures(db: Session, *, limit: int = 50) -> dict[str, Any]:
    rows = (
        db.query(RecurringSystemJobRun)
        .filter(RecurringSystemJobRun.status == "failed")
        .order_by(RecurringSystemJobRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "failed_runs": [
            {
                "id": r.id,
                "job_key": r.job_key,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "error": (_loads(r.error_json) or {}).get("message"),
            }
            for r in rows
        ]
    }


def dashboard_jobs_due(db: Session) -> dict[str, Any]:
    now = utc_now()
    due = list_due_jobs(db, now=now)
    return {
        "now": now.isoformat(),
        "due": [
            {
                "job_id": j.id,
                "job_key": j.job_key,
                "name": j.name,
                "next_run_at": j.next_run_at.isoformat() if j.next_run_at else None,
                "schedule_type": j.schedule_type,
            }
            for j in due
        ],
    }
