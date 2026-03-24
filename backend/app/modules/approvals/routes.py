from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.approvals.schemas import (
    ApprovalDecisionIn,
    ApprovalRequestCreateIn,
    ApprovalRequestOut,
    ApprovalsDashboardSummaryOut,
)
from backend.app.modules.approvals import service as approval_service
from backend.app.modules.auth.models import User

router = APIRouter(prefix="/approvals", tags=["approvals"])

_INTERNAL_CREATORS = (
    "Admin",
    "Dispatcher",
    "Engineer",
    "Finance",
    "Commercial",
    "Ops_Manager",
)
_REVIEWERS = ("Admin", "Finance", "Commercial", "Ops_Manager", "Dispatcher")


@router.get("/dashboard/summary", response_model=ApprovalsDashboardSummaryOut)
def approvals_dashboard_summary_endpoint(
    overdue_hours: float = Query(default=72.0, ge=1.0, le=720.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_REVIEWERS)),
) -> ApprovalsDashboardSummaryOut:
    raw = approval_service.dashboard_summary(db, current_user_id=current_user.id, overdue_hours=overdue_hours)
    return ApprovalsDashboardSummaryOut(**raw)


@router.get("", response_model=list[ApprovalRequestOut])
def list_approvals_endpoint(
    status: str | None = Query(default=None),
    approval_type: str | None = Query(default=None),
    assigned_to_user_id: str | None = Query(default=None),
    target_entity_type: str | None = Query(default=None),
    target_entity_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_REVIEWERS)),
) -> list[ApprovalRequestOut]:
    rows = approval_service.list_approval_requests(
        db,
        status=status,
        approval_type=approval_type,
        assigned_to_user_id=assigned_to_user_id,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        limit=limit,
        offset=offset,
    )
    return [ApprovalRequestOut.from_row(r) for r in rows]


@router.get("/{approval_id}", response_model=ApprovalRequestOut)
def get_approval_endpoint(
    approval_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(*_REVIEWERS)),
) -> ApprovalRequestOut:
    row = approval_service.get_approval_request(db, approval_id=approval_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return ApprovalRequestOut.from_row(row)


@router.post("", response_model=ApprovalRequestOut, status_code=status.HTTP_201_CREATED)
def create_approval_endpoint(
    payload: ApprovalRequestCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*_INTERNAL_CREATORS)),
) -> ApprovalRequestOut:
    try:
        row = approval_service.create_approval_request(
            db,
            approval_type=payload.approval_type,
            target_entity_type=payload.target_entity_type,
            target_entity_id=payload.target_entity_id,
            reason=payload.reason,
            requested_by_user_id=current_user.id,
            payload=payload.payload_json,
            assigned_to_user_id=payload.assigned_to_user_id,
        )
        return ApprovalRequestOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{approval_id}/approve", response_model=ApprovalRequestOut)
def approve_approval_endpoint(
    approval_id: str,
    payload: ApprovalDecisionIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequestOut:
    payload = payload or ApprovalDecisionIn()
    try:
        row = approval_service.approve_request(
            db,
            approval_id=approval_id,
            approver=current_user,
            decision_notes=payload.decision_notes,
        )
        return ApprovalRequestOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{approval_id}/reject", response_model=ApprovalRequestOut)
def reject_approval_endpoint(
    approval_id: str,
    payload: ApprovalDecisionIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequestOut:
    payload = payload or ApprovalDecisionIn()
    try:
        row = approval_service.reject_request(
            db,
            approval_id=approval_id,
            approver=current_user,
            decision_notes=payload.decision_notes,
        )
        return ApprovalRequestOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
