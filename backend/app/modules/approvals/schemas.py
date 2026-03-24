from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApprovalRequestCreateIn(BaseModel):
    approval_type: str = Field(..., min_length=3)
    target_entity_type: str = Field(..., min_length=2)
    target_entity_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=3)
    payload_json: dict[str, Any] | None = None
    assigned_to_user_id: str | None = None


class ApprovalDecisionIn(BaseModel):
    decision_notes: str | None = None


class ApprovalRequestOut(BaseModel):
    id: str
    approval_type: str
    target_entity_type: str
    target_entity_id: str
    requested_by_user_id: str
    assigned_to_user_id: str | None
    status: str
    reason: str
    payload_json: dict[str, Any] | None
    created_at: datetime
    decided_at: datetime | None
    decided_by_user_id: str | None
    decision_notes: str | None
    execution_result_json: dict[str, Any] | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row: Any) -> ApprovalRequestOut:
        import json

        pj = None
        if row.payload_json:
            try:
                pj = json.loads(row.payload_json)
            except json.JSONDecodeError:
                pj = None
        ej = None
        if row.execution_result_json:
            try:
                ej = json.loads(row.execution_result_json)
            except json.JSONDecodeError:
                ej = None
        return cls(
            id=row.id,
            approval_type=row.approval_type,
            target_entity_type=row.target_entity_type,
            target_entity_id=row.target_entity_id,
            requested_by_user_id=row.requested_by_user_id,
            assigned_to_user_id=row.assigned_to_user_id,
            status=row.status,
            reason=row.reason,
            payload_json=pj,
            created_at=row.created_at,
            decided_at=row.decided_at,
            decided_by_user_id=row.decided_by_user_id,
            decision_notes=row.decision_notes,
            execution_result_json=ej,
        )


class ApprovalsDashboardSummaryOut(BaseModel):
    pending_total: int
    pending_by_type: dict[str, int]
    overdue_pending_count: int
    assigned_to_me_pending: int
    recently_decided: int
    overdue_hours_threshold: float
