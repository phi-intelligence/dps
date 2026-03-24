from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class VehicleInspectionItemCreateIn(BaseModel):
    item_code: str
    item_label: str
    result: str = Field(description="pass | fail | advisory | n_a")
    notes: str | None = None
    photo_document_id: str | None = None
    fail_criticality: str = Field(default="minor", description="minor | critical when result=fail")


class VehicleInspectionCreateIn(BaseModel):
    engineer_id: str
    performed_at: datetime | None = None
    inspection_date: date | None = Field(
        default=None,
        description="Defaults to UTC date of performed_at",
    )
    odometer: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    overall_status: str | None = Field(
        default=None,
        description="passed | failed_minor | failed_critical; derived from items if omitted",
    )
    notes: str | None = None
    items: list[VehicleInspectionItemCreateIn] = Field(default_factory=list)


class VehicleInspectionItemOut(BaseModel):
    id: str
    inspection_id: str
    item_code: str
    item_label: str
    result: str
    notes: str | None
    photo_document_id: str | None
    fail_criticality: str

    model_config = {"from_attributes": True}


class VehicleInspectionOut(BaseModel):
    id: str
    vehicle_id: str
    engineer_id: str
    inspection_date: date
    performed_at: datetime
    odometer: float | None
    latitude: float | None
    longitude: float | None
    overall_status: str
    notes: str | None
    created_at: datetime
    items: list[VehicleInspectionItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class VehicleDefectCreateIn(BaseModel):
    defect_type: str
    severity: str = Field(description="critical | major | minor")
    title: str
    description: str | None = None
    inspection_id: str | None = None


class VehicleDefectOut(BaseModel):
    id: str
    vehicle_id: str
    inspection_id: str | None
    defect_type: str
    severity: str
    title: str
    description: str | None
    status: str
    reported_at: datetime
    reported_by_user_id: str | None
    resolved_at: datetime | None
    resolved_by_user_id: str | None
    resolution_notes: str | None

    model_config = {"from_attributes": True}


class VehicleDefectResolveIn(BaseModel):
    resolution_notes: str | None = None


class VehicleReadinessOut(BaseModel):
    vehicle_id: str
    readiness_status: str
    reasons: list[str]
    blocking_flags: list[str]
    warnings: list[str]
    latest_inspection_id: str | None
    latest_inspection_status: str | None


class InspectionAttentionDashboardOut(BaseModel):
    attention_count: int
    items: list[dict[str, Any]]
