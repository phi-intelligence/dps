from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FieldEquipmentCreateIn(BaseModel):
    equipment_code: str
    name: str
    equipment_type: str
    category: str = "general"
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    status: str = "available"
    ownership_type: str = "owned"
    current_location_type: str = "warehouse"
    current_location_id: str | None = None
    assigned_engineer_id: str | None = None
    assigned_vehicle_id: str | None = None
    assigned_site_id: str | None = None
    purchase_date: datetime | None = None
    warranty_expiry: datetime | None = None
    service_due_date: datetime | None = None
    inspection_due_date: datetime | None = None
    calibration_required: bool = False
    calibration_due_date: datetime | None = None
    notes: str | None = None
    metadata_json: str | None = None


class FieldEquipmentPatchIn(BaseModel):
    name: str | None = None
    equipment_type: str | None = None
    category: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    status: str | None = None
    ownership_type: str | None = None
    notes: str | None = None
    metadata_json: str | None = None
    service_due_date: datetime | None = None
    inspection_due_date: datetime | None = None
    calibration_required: bool | None = None
    calibration_due_date: datetime | None = None


class FieldEquipmentOut(BaseModel):
    id: str
    equipment_code: str
    name: str
    equipment_type: str
    category: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    status: str
    ownership_type: str
    current_location_type: str
    current_location_id: str | None
    assigned_engineer_id: str | None
    assigned_vehicle_id: str | None
    assigned_site_id: str | None
    purchase_date: datetime | None
    warranty_expiry: datetime | None
    service_due_date: datetime | None
    inspection_due_date: datetime | None
    calibration_required: bool
    calibration_due_date: datetime | None
    calibration_status: str
    notes: str | None
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EquipmentMovementOut(BaseModel):
    id: str
    equipment_id: str
    movement_type: str
    prev_location_type: str | None
    prev_location_id: str | None
    new_location_type: str | None
    new_location_id: str | None
    prev_status: str | None
    new_status: str | None
    assigned_engineer_id_after: str | None
    assigned_vehicle_id_after: str | None
    assigned_site_id_after: str | None
    notes: str | None
    performed_by_user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EquipmentAssignMoveIn(BaseModel):
    """Assign equipment to engineer, vehicle, warehouse location, site, or workshop."""

    target: str = Field(
        description="engineer | vehicle | warehouse | site | workshop | out_of_service | return_from_repair"
    )
    target_id: str | None = Field(default=None, description="User id, vehicle id, stock_location id, site id, or workshop code")
    notes: str | None = None


class JobEquipmentRequirementCreateIn(BaseModel):
    equipment_type: str
    category: str = "general"
    specific_equipment_id: str | None = None
    calibration_required: bool = False
    mandatory: bool = True
    quantity: int = 1
    notes: str | None = None


class JobEquipmentRequirementOut(BaseModel):
    id: str
    job_id: str
    equipment_type: str
    category: str
    specific_equipment_id: str | None
    calibration_required: bool
    mandatory: bool
    quantity: int
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CalibrationRecordCreateIn(BaseModel):
    performed_at: datetime
    next_due_date: datetime | None = None
    certificate_document_id: str | None = None
    notes: str | None = None


class CalibrationRecordOut(BaseModel):
    id: str
    equipment_id: str
    performed_at: datetime
    next_due_date: datetime | None
    certificate_document_id: str | None
    notes: str | None
    performed_by_user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InspectionRecordCreateIn(BaseModel):
    performed_at: datetime
    next_inspection_due_date: datetime | None = None
    next_service_due_date: datetime | None = None
    certificate_document_id: str | None = None
    notes: str | None = None


class InspectionRecordOut(BaseModel):
    id: str
    equipment_id: str
    performed_at: datetime
    next_inspection_due_date: datetime | None
    next_service_due_date: datetime | None
    certificate_document_id: str | None
    notes: str | None
    performed_by_user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EquipmentReadinessResultOut(BaseModel):
    job_id: str
    evaluated_for_engineer_id: str | None
    readiness_status: str
    missing_required_equipment: list[dict[str, Any]]
    expired_required_equipment: list[dict[str, Any]]
    due_soon_equipment: list[dict[str, Any]]
    assigned_matching_equipment: list[dict[str, Any]]
    warnings: list[str]
    blocking_flags: list[str]


class DashboardReadinessOut(BaseModel):
    available_count: int
    assigned_count: int
    in_service_count: int
    under_repair_count: int
    out_of_service_count: int
    lost_count: int
    retired_count: int
    jobs_blocked_by_equipment: int
    jobs_with_equipment_warnings: int
    upcoming_readiness_risks: list[dict[str, Any]]


class DashboardCalibrationOut(BaseModel):
    calibration_required_total: int
    calibration_valid: int
    calibration_due_soon: int
    calibration_expired: int
    inspection_due_within_window: int
    service_due_within_window: int


class DashboardAttentionOut(BaseModel):
    out_of_service_count: int
    under_repair_count: int
    expired_calibration_count: int
    due_soon_calibration_count: int
    inspection_overdue_or_due: int
    top_attention_items: list[dict[str, Any]]
