from __future__ import annotations

from datetime import datetime
from typing import Any

import json

from pydantic import BaseModel, Field, field_validator


class RecurringSystemJobOut(BaseModel):
    id: str
    job_key: str
    job_type: str
    name: str
    description: str | None
    enabled: bool
    schedule_type: str
    schedule_expression: str | None
    timezone_name: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    max_runtime_seconds: int | None
    dry_run_default: bool
    payload_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("payload_json", mode="before")
    @classmethod
    def _pj(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                o = json.loads(v)
                return o if isinstance(o, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class RecurringSystemJobPatchIn(BaseModel):
    enabled: bool | None = None
    schedule_type: str | None = None
    schedule_expression: str | None = None
    timezone_name: str | None = None
    dry_run_default: bool | None = None
    payload_json: dict[str, Any] | None = None
    next_run_at: datetime | None = None


class RecurringSystemJobRunOut(BaseModel):
    id: str
    recurring_job_id: str
    job_key: str
    trigger_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    dry_run: bool
    triggered_by_user_id: str | None
    result_summary: str | None
    result_json: dict[str, Any] | None = None
    error_json: dict[str, Any] | None = None
    created_count: int | None
    updated_count: int | None
    skipped_count: int | None
    failed_count: int | None
    idempotency_key: str | None

    model_config = {"from_attributes": True}

    @field_validator("result_json", "error_json", mode="before")
    @classmethod
    def _pj(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                o = json.loads(v)
                return o if isinstance(o, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class RunJobIn(BaseModel):
    dry_run: bool | None = Field(
        default=None,
        description="Override job dry_run_default when set.",
    )


class RunDueJobsIn(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=50)
    dry_run: bool | None = None
