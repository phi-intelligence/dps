from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AutomationRunOut(BaseModel):
    id: str
    automation_type: str
    trigger_type: str
    trigger_entity_type: str
    trigger_entity_id: str
    source_recommendation_id: str | None = None
    source_event_type: str | None = None
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    created_by_system: bool
    result_summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] | None = None
    draft_entity_type: str | None = None
    draft_entity_id: str | None = None
    performed_by_user_id: str | None = None


class InternalFollowUpTaskOut(BaseModel):
    id: str
    task_type: str
    title: str
    summary: str
    status: str
    priority: str
    related_entity_type: str
    related_entity_id: str
    source_recommendation_id: str | None = None
    source_automation_run_id: str | None = None
    assigned_to_user_id: str | None = None
    created_at: datetime
    due_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    payload: dict[str, Any] | None = None


class InternalFollowUpTaskPatchIn(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to_user_id: str | None = None
    due_at: datetime | None = None
    notes: str | None = None


class RunAutomationForRecommendationIn(BaseModel):
    """Optional override; default derived from recommendation_type mapping."""

    automation_type: str | None = None
    payload: dict[str, Any] | None = None


class InternalFollowUpTaskCompleteIn(BaseModel):
    completion_notes: str | None = None


class RunAutomationForProposalIn(BaseModel):
    kind: str = Field(
        default="viewed_no_response_follow_up",
        description="viewed_no_response_follow_up | expired_no_response_follow_up",
    )
    viewed_no_response_days: int = Field(default=7, ge=0, le=365)
