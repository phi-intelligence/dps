from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PpmScheduleCreateIn(BaseModel):
    contract_id: str
    site_id: str
    asset_id: str | None = None
    title: str
    frequency_value: int
    frequency_unit: str  # day | week | month | year
    recurrence_rule: str | None = None
    next_due_date: datetime
    planning_window_days: int = 30
    estimated_duration_minutes: int | None = None
    checklist_template_ref: str | None = None
    compliance_template_ref: str | None = None
    required_competencies_json: str = "[]"
    active: bool = True


class PpmSchedulePatchIn(BaseModel):
    title: str | None = None
    frequency_value: int | None = None
    frequency_unit: str | None = None
    recurrence_rule: str | None = None
    next_due_date: datetime | None = None
    planning_window_days: int | None = None
    estimated_duration_minutes: int | None = None
    checklist_template_ref: str | None = None
    compliance_template_ref: str | None = None
    required_competencies_json: str | None = None
    active: bool | None = None


class PpmScheduleOut(BaseModel):
    id: str
    contract_id: str
    site_id: str
    asset_id: str | None
    title: str
    frequency_value: int
    frequency_unit: str
    recurrence_rule: str | None
    next_due_date: datetime
    planning_window_days: int
    estimated_duration_minutes: int | None
    checklist_template_ref: str | None
    compliance_template_ref: str | None
    required_competencies_json: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PpmRunGenerationIn(BaseModel):
    run_date: datetime | None = None
    planning_window_days: int | None = None


class PpmRunGenerationOut(BaseModel):
    created_job_ids: list[str]
    skipped_schedule_ids: list[str]
