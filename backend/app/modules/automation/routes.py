"""Internal automation + follow-up task APIs (RBAC; draft-first, auditable)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_permission
from backend.app.modules.auth.models import User
from backend.app.services.authorization_policy import CAN_RUN_OPS_AUTOMATION
from backend.app.modules.automation.schemas import (
    AutomationRunOut,
    InternalFollowUpTaskCompleteIn,
    InternalFollowUpTaskOut,
    InternalFollowUpTaskPatchIn,
    RunAutomationForProposalIn,
    RunAutomationForRecommendationIn,
)
from backend.app.services import low_risk_automation_service as lra

automation_router = APIRouter(prefix="/automation", tags=["automation"])
tasks_router = APIRouter(prefix="/tasks", tags=["internal-tasks"])

_DEP_CAN_RUN_OPS_AUTOMATION = Depends(require_permission(CAN_RUN_OPS_AUTOMATION))


def _run_out(row: Any) -> AutomationRunOut:
    return AutomationRunOut.model_validate(lra.automation_run_to_dict(row))


def _task_out(row: Any) -> InternalFollowUpTaskOut:
    return InternalFollowUpTaskOut.model_validate(lra.task_to_dict(row))


@automation_router.get("/runs", response_model=list[AutomationRunOut])
def list_automation_runs(
    status: str | None = Query(default=None),
    automation_type: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> list[AutomationRunOut]:
    rows = lra.list_runs(db, status=status, automation_type=automation_type, limit=limit, offset=offset)
    return [_run_out(r) for r in rows]


@automation_router.get("/runs/{automation_run_id}", response_model=AutomationRunOut)
def get_automation_run(
    automation_run_id: str,
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> AutomationRunOut:
    r = lra.get_run(db, run_id=automation_run_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation run not found")
    return _run_out(r)


@automation_router.get("/dashboard/summary")
def automation_dashboard_summary(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> dict[str, Any]:
    return lra.dashboard_summary(db, limit=limit)


@automation_router.post("/run-for-recommendation/{recommendation_id}", response_model=AutomationRunOut)
def run_automation_for_recommendation_endpoint(
    recommendation_id: str,
    body: RunAutomationForRecommendationIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> AutomationRunOut:
    body = body or RunAutomationForRecommendationIn()
    try:
        run = lra.run_automation_for_recommendation(
            db,
            recommendation_id=recommendation_id,
            actor_user_id=current_user.id,
            automation_type=body.automation_type,
            payload=body.payload,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _run_out(run)


@automation_router.post("/run-for-proposal/{proposal_id}", response_model=AutomationRunOut | None)
def run_automation_for_proposal_endpoint(
    proposal_id: str,
    body: RunAutomationForProposalIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> AutomationRunOut | None:
    body = body or RunAutomationForProposalIn()
    try:
        run = lra.maybe_create_proposal_viewed_follow_up(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            viewed_no_response_days=body.viewed_no_response_days,
            kind=body.kind,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if run is None:
        return None
    return _run_out(run)


# Dashboard paths must be registered before /{task_id} so "dashboard" is not captured as an id.
@tasks_router.get("/dashboard/follow-up")
def tasks_dashboard_follow_up_route(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> dict[str, Any]:
    return lra.tasks_dashboard_follow_up(db, limit=limit)


@tasks_router.get("/dashboard/commercial")
def tasks_dashboard_commercial_route(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> dict[str, Any]:
    return lra.tasks_dashboard_commercial(db, limit=limit)


@tasks_router.get("/dashboard/finance")
def tasks_dashboard_finance_route(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> dict[str, Any]:
    return lra.tasks_dashboard_finance(db, limit=limit)


@tasks_router.get("", response_model=list[InternalFollowUpTaskOut])
def list_internal_tasks(
    status: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> list[InternalFollowUpTaskOut]:
    rows = lra.list_tasks(db, status=status, task_type=task_type, limit=limit, offset=offset)
    return [_task_out(t) for t in rows]


@tasks_router.get("/{task_id}", response_model=InternalFollowUpTaskOut)
def get_internal_task(
    task_id: str,
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> InternalFollowUpTaskOut:
    t = lra.get_task(db, task_id=task_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _task_out(t)


@tasks_router.patch("/{task_id}", response_model=InternalFollowUpTaskOut)
def patch_internal_task(
    task_id: str,
    body: InternalFollowUpTaskPatchIn,
    db: Session = Depends(get_db),
    _user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> InternalFollowUpTaskOut:
    try:
        t = lra.patch_task(
            db,
            task_id=task_id,
            status=body.status,
            priority=body.priority,
            assigned_to_user_id=body.assigned_to_user_id,
            due_at=body.due_at,
            notes=body.notes,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return _task_out(t)


@tasks_router.post("/{task_id}/complete", response_model=InternalFollowUpTaskOut)
def complete_internal_task(
    task_id: str,
    body: InternalFollowUpTaskCompleteIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = _DEP_CAN_RUN_OPS_AUTOMATION,
) -> InternalFollowUpTaskOut:
    body = body or InternalFollowUpTaskCompleteIn()
    try:
        t = lra.complete_task(
            db,
            task_id=task_id,
            completed_by_user_id=current_user.id,
            completion_notes=body.completion_notes,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return _task_out(t)
