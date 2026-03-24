from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PunchInOutIn(BaseModel):
    job_id: str
    latitude: float
    longitude: float
    occurred_at: datetime | None = None
    offline_device_id: str | None = None


class PunchOut(BaseModel):
    id: str
    user_id: str
    job_id: str
    kind: str
    occurred_at: datetime
    latitude: float
    longitude: float
    valid: bool
    distance_m: float | None
    offline_device_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TimesheetSessionOut(BaseModel):
    job_id: str
    clock_in_punch_id: str
    clock_out_punch_id: str
    clock_in_at: datetime
    clock_out_at: datetime
    duration_seconds: int


class TimesheetOut(BaseModel):
    user_id: str
    date: str  # YYYY-MM-DD
    total_seconds: int
    sessions: list[TimesheetSessionOut]


class TimesheetApprovalIn(BaseModel):
    user_id: str
    date_str: str  # YYYY-MM-DD


class TimesheetApprovalOut(BaseModel):
    id: str
    user_id: str
    date_str: str
    total_seconds: int
    regular_seconds: int
    overtime_seconds: int
    status: str
    approved_by_user_id: str | None
    approved_at: datetime | None

    class Config:
        from_attributes = True


class PayrollLineOut(BaseModel):
    user_id: str
    date_str: str
    total_seconds: int
    regular_seconds: int
    overtime_seconds: int
    amount: float


class PayrollExportOut(BaseModel):
    date_str: str
    lines: list[PayrollLineOut]

