from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.modules.system.schemas import (
    RecurringSystemJobOut,
    RecurringSystemJobPatchIn,
    RecurringSystemJobRunOut,
    RunDueJobsIn,
    RunJobIn,
)
from backend.app.services import integration_status_service as integ
from backend.app.services.communication_template_registry import list_communication_template_registry
from backend.app.services import operations_diagnostics_service as ops_diag
from backend.app.services import operations_overview_service as ops_overview
from backend.app.services import recurring_job_runner_service as rjr
import json

router = APIRouter(prefix="/system", tags=["system"])

_SYSTEM_MUTATE_ROLES = ("Admin", "Ops_Manager")
_SYSTEM_READ_ROLES = ("Admin", "Ops_Manager", "Dispatcher", "Commercial", "Finance")


def _payload_str(payload: dict | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, separators=(",", ":"), default=str)


@router.get("/jobs", response_model=list[RecurringSystemJobOut])
def list_recurring_jobs_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> list[RecurringSystemJobOut]:
    rows = rjr.list_jobs(db)
    return [RecurringSystemJobOut.model_validate(r) for r in rows]


@router.get("/jobs/{job_id}", response_model=RecurringSystemJobOut)
def get_recurring_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> RecurringSystemJobOut:
    row = rjr.get_job(db, job_id=job_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return RecurringSystemJobOut.model_validate(row)


@router.patch("/jobs/{job_id}", response_model=RecurringSystemJobOut)
def patch_recurring_job_endpoint(
    job_id: str,
    payload: RecurringSystemJobPatchIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_MUTATE_ROLES)),
) -> RecurringSystemJobOut:
    try:
        data = payload.model_dump(exclude_unset=True)
        pj = None
        if "payload_json" in data:
            pj = _payload_str(data["payload_json"])
        row = rjr.patch_job(
            db,
            job_id=job_id,
            enabled=data.get("enabled"),
            schedule_type=data.get("schedule_type"),
            schedule_expression=data.get("schedule_expression"),
            timezone_name=data.get("timezone_name"),
            dry_run_default=data.get("dry_run_default"),
            payload_json=pj,
            next_run_at=data.get("next_run_at"),
            commit=True,
        )
        return RecurringSystemJobOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/jobs/{job_id}/run", response_model=RecurringSystemJobRunOut)
def run_recurring_job_endpoint(
    job_id: str,
    body: RunJobIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_SYSTEM_MUTATE_ROLES)),
) -> RecurringSystemJobRunOut:
    job = rjr.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    dry = body.dry_run if body and body.dry_run is not None else job.dry_run_default
    try:
        run = rjr.run_job(
            db,
            job_key=job.job_key,
            dry_run=dry,
            actor_user_id=current_user.id,
            trigger_type="manual",
            advance_schedule=not dry,
            commit=True,
        )
        return RecurringSystemJobRunOut.model_validate(run)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/jobs/run-due", response_model=list[RecurringSystemJobRunOut])
def run_due_recurring_jobs_endpoint(
    body: RunDueJobsIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_SYSTEM_MUTATE_ROLES)),
) -> list[RecurringSystemJobRunOut]:
    b = body or RunDueJobsIn()
    runs = rjr.run_due_jobs(
        db,
        limit=b.limit,
        dry_run_override=b.dry_run,
        actor_user_id=current_user.id,
        commit=True,
    )
    return [RecurringSystemJobRunOut.model_validate(r) for r in runs]


@router.get("/job-runs", response_model=list[RecurringSystemJobRunOut])
def list_recurring_job_runs_endpoint(
    job_key: str | None = Query(default=None),
    run_status: str | None = Query(default=None, description="Filter by run status"),
    trigger_type: str | None = Query(default=None),
    dry_run: bool | None = Query(default=None),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> list[RecurringSystemJobRunOut]:
    rows = rjr.list_runs(
        db,
        job_key=job_key,
        status=run_status,
        trigger_type=trigger_type,
        dry_run=dry_run,
        started_after=started_after,
        started_before=started_before,
        limit=limit,
        offset=offset,
    )
    return [RecurringSystemJobRunOut.model_validate(r) for r in rows]


@router.get("/job-runs/{run_id}", response_model=RecurringSystemJobRunOut)
def get_recurring_job_run_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> RecurringSystemJobRunOut:
    row = rjr.get_run(db, run_id=run_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RecurringSystemJobRunOut.model_validate(row)


@router.post("/job-runs/{run_id}/retry", response_model=RecurringSystemJobRunOut)
def retry_recurring_job_run_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_SYSTEM_MUTATE_ROLES)),
) -> RecurringSystemJobRunOut:
    try:
        run = rjr.retry_run(db, run_id=run_id, actor_user_id=current_user.id, commit=True)
        return RecurringSystemJobRunOut.model_validate(run)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/jobs")
def system_dashboard_jobs_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return rjr.dashboard_jobs(db)


@router.get("/dashboard/job-failures")
def system_dashboard_job_failures_endpoint(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return rjr.dashboard_job_failures(db, limit=limit)


@router.get("/dashboard/operations-diagnostics")
def system_dashboard_operations_diagnostics_endpoint(
    limit_each: int = Query(default=40, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return ops_diag.operations_diagnostics_summary(db, limit_each=limit_each)


@router.get("/integration-status")
def system_integration_status_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return integ.integration_status_summary(db)


@router.get("/communication-template-registry")
def system_communication_template_registry_endpoint(
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> list[dict]:
    """§5.17 — versioned/locale-aware customer communication templates (catalog metadata)."""
    return list_communication_template_registry()


@router.get("/dashboard/operations-blockers-overview")
def system_dashboard_operations_blockers_overview_endpoint(
    limit_each: int = Query(default=5, le=50),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return ops_overview.operations_blockers_overview(db, limit_each=limit_each)


@router.get("/dashboard/jobs-due")
def system_dashboard_jobs_due_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_SYSTEM_READ_ROLES)),
) -> dict:
    return rjr.dashboard_jobs_due(db)
