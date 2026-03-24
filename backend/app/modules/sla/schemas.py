from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SlaPolicyCreateIn(BaseModel):
    name: str
    priority: str
    response_target_minutes: int
    attendance_target_minutes: int
    resolution_target_minutes: int
    service_window_json: str = "{}"
    warning_threshold_percent_json: str = "{}"
    escalation_notes: str | None = None
    active: bool = True


class SlaPolicyPatchIn(BaseModel):
    name: str | None = None
    priority: str | None = None
    response_target_minutes: int | None = None
    attendance_target_minutes: int | None = None
    resolution_target_minutes: int | None = None
    service_window_json: str | None = None
    warning_threshold_percent_json: str | None = None
    escalation_notes: str | None = None
    active: bool | None = None


class SlaPolicyOut(BaseModel):
    id: str
    name: str
    priority: str
    response_target_minutes: int
    attendance_target_minutes: int
    resolution_target_minutes: int
    service_window_json: str
    warning_threshold_percent_json: str
    escalation_notes: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
