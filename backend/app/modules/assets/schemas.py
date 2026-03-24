from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AssetCreateIn(BaseModel):
    customer_id: str
    site_id: str | None = None
    contract_id: str | None = None
    asset_code: str | None = None
    asset_type: str
    name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    install_date: datetime | None = None
    commissioning_date: datetime | None = None
    warranty_expiry: datetime | None = None
    status: str = "in_service"
    criticality: str = "standard"
    service_interval_value: int | None = None
    service_interval_unit: str | None = None
    last_service_date: datetime | None = None
    next_service_date: datetime | None = None
    notes: str | None = None
    compliance_tags_json: str = "[]"
    required_competencies_json: str = "[]"
    location_address: str
    next_maintenance_eta_at: datetime | None = None


class AssetPatchIn(BaseModel):
    site_id: str | None = None
    contract_id: str | None = None
    asset_code: str | None = None
    asset_type: str | None = None
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    install_date: datetime | None = None
    commissioning_date: datetime | None = None
    warranty_expiry: datetime | None = None
    status: str | None = None
    criticality: str | None = None
    service_interval_value: int | None = None
    service_interval_unit: str | None = None
    last_service_date: datetime | None = None
    next_service_date: datetime | None = None
    notes: str | None = None
    compliance_tags_json: str | None = None
    required_competencies_json: str | None = None
    location_address: str | None = None
    next_maintenance_eta_at: datetime | None = None


class AssetOut(BaseModel):
    id: str
    customer_id: str
    site_id: str | None
    contract_id: str | None
    asset_code: str
    asset_type: str
    name: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    install_date: datetime | None
    commissioning_date: datetime | None
    warranty_expiry: datetime | None
    status: str
    criticality: str
    service_interval_value: int | None
    service_interval_unit: str | None
    last_service_date: datetime | None
    next_service_date: datetime | None
    notes: str | None
    compliance_tags_json: str
    required_competencies_json: str
    location_address: str
    next_maintenance_eta_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceScheduleCreateIn(BaseModel):
    asset_id: str
    schedule_type: str = "date"
    next_due_at: datetime
    interval_days: int = 90
    notes: str | None = None


class MaintenanceScheduleOut(BaseModel):
    id: str
    asset_id: str
    schedule_type: str
    next_due_at: datetime
    interval_days: int
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunDueOut(BaseModel):
    created_job_ids: list[str]
