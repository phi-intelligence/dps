from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobCreateIn(BaseModel):
    customer_id: str | None = None
    quote_id: str | None = None
    address: str
    scheduled_at: datetime | None = None
    site_id: str | None = None
    asset_id: str | None = None
    contract_id: str | None = None
    work_type: str = "reactive"
    site_latitude: float | None = None
    site_longitude: float | None = None
    address_geocoded_latitude: float | None = None
    address_geocoded_longitude: float | None = None
    material_policy: str = "materials_optional"
    dispatch_priority: int = 0
    required_competencies: list[str] | None = None


class JobOut(BaseModel):
    id: str
    customer_id: str | None
    quote_id: str | None
    contract_id: str | None = None
    site_id: str | None = None
    asset_id: str | None = None
    ppm_schedule_id: str | None = None
    work_type: str = "reactive"
    sla_policy_id: str | None = None
    sla_priority: str | None = None
    asset_criticality: str | None = None
    covered_under_contract: bool = False
    compliance_required: bool = False
    address: str
    status: str
    scheduled_at: datetime | None
    assigned_engineer_id: str | None
    site_latitude: float | None = None
    site_longitude: float | None = None
    address_geocoded_latitude: float | None = None
    address_geocoded_longitude: float | None = None
    material_policy: str = "materials_optional"
    dispatch_priority: int = 0
    eta_minutes: float | None = None
    delay_notice: str | None = None
    delay_notice_at: datetime | None = None
    sla_risk_state: str | None = None
    sla_target_completion_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobAssignIn(BaseModel):
    engineer_id: str
    required_competencies: list[str] | None = None


class JobStatusUpdateIn(BaseModel):
    status: str


class JobEngineerAcceptIn(BaseModel):
    """
    Engineer-side "accept job" action for mobile/field app.
    """

    required_competencies: list[str] | None = None


class JobFormRequirementSetIn(BaseModel):
    """
    Configure which keys must be present in an engineer form submission.
    """

    required_keys: list[str]


class JobFormSubmitIn(BaseModel):
    data: dict[str, object]


class JobFormRequirementOut(BaseModel):
    id: str
    job_id: str
    form_key: str
    required_keys_json: str
    satisfied_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobFormSubmissionOut(BaseModel):
    id: str
    job_id: str
    form_key: str
    data_json: str
    submitted_by_user_id: str
    submitted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class JobSignatureRequirementSetIn(BaseModel):
    required: bool = True


class JobSignatureRequirementOut(BaseModel):
    id: str
    job_id: str
    satisfied_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobSignatureSubmitIn(BaseModel):
    # Generic JSON signature payload. In production this could be a base64 blob or a structured capture.
    signature: dict[str, object]


class JobMediaRequirementSetIn(BaseModel):
    required_photo_count: int = 1


class JobMediaRequirementOut(BaseModel):
    id: str
    job_id: str
    required_photo_count: int
    satisfied_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobMediaSubmitIn(BaseModel):
    media_type: str = "photo"
    payloads: list[dict[str, object]]


class JobMediaCapabilitiesOut(BaseModel):
    phase2_enabled: bool
    mode: str
    max_json_payload_bytes: int
    legacy_json_enabled: bool = True


class JobMediaUploadSessionCreateIn(BaseModel):
    media_type: str = "photo"


class JobMediaUploadSessionOut(BaseModel):
    id: str
    job_id: str
    media_type: str
    status: str
    upload_mode: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class JobMediaUploadSessionCommitIn(BaseModel):
    payloads: list[dict[str, object]]


class JobPartsUsageRequirementSetIn(BaseModel):
    required_parts_items_count: int = 1


class JobPartsUsageRequirementOut(BaseModel):
    id: str
    job_id: str
    required_parts_items_count: int
    satisfied_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobPartsUsageSubmitIn(BaseModel):
    items: list[dict[str, object]]


class JobCompletionRequirementsBundleOut(BaseModel):
    """Aggregated completion gate requirements for a job (read-only)."""

    job_id: str
    material_policy: str
    form_requirements: list[JobFormRequirementOut]
    signature_requirements: list[JobSignatureRequirementOut]
    media_requirements: list[JobMediaRequirementOut]
    parts_requirements: list[JobPartsUsageRequirementOut]


class FollowOnFromDefectsIn(BaseModel):
    defects: list[str]


class FollowOnCreatedOut(BaseModel):
    source_job_id: str
    created_job_ids: list[str]


class JobActivityNoteCreateIn(BaseModel):
    body: str
    source: str = "engineer_note"


class JobActivityEventOut(BaseModel):
    id: str
    job_id: str
    author_user_id: str
    activity_type: str
    source: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True



class EngineerRecommendationOut(BaseModel):
    engineer_id: str
    distance_m: float
    eta_minutes: float
    latitude: float
    longitude: float
    last_seen_at: datetime

    class Config:
        from_attributes = True


class JobRecommendationOut(BaseModel):
    job_id: str
    recommendations: list[EngineerRecommendationOut]


class DispatchRecommendationRowOut(BaseModel):
    engineer_id: str
    distance_km: float
    estimated_travel_minutes: float
    availability_state: str
    telemetry_freshness_seconds: float | None
    competency_match: bool
    active_job_count: int
    recommendation_score: float
    recommendation_reasons: list[str]
    operational_latitude: float
    operational_longitude: float
    operational_source: str
    last_occurred_at: datetime | None = None
    equipment_readiness_status: str | None = None
    equipment_readiness_reasons: list[str] = []
    vehicle_readiness_status: str | None = None
    vehicle_readiness_reasons: list[str] = []


class JobDispatchRecommendationsOut(BaseModel):
    job_id: str
    dispatch_point_source: str
    recommendations: list[DispatchRecommendationRowOut]
    job_equipment_readiness: dict[str, Any] | None = None
    job_vehicle_readiness: dict[str, Any] | None = None


class AssignBestIn(BaseModel):
    required_competencies: list[str] | None = None
    include_stale: bool | None = None
    notes: str | None = None


class AssignBestOut(BaseModel):
    job_id: str
    selected_engineer_id: str
    recommendation_score: float
    explanation_reasons: list[str]
    ranked: list[DispatchRecommendationRowOut]


class LiveMapEngineerOut(BaseModel):
    engineer_id: str
    latitude: float | None
    longitude: float | None
    operational_source: str | None
    freshness_status: str | None
    availability_state: str
    stale: bool


class LiveMapVehicleOut(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    assigned_engineer_id: str | None
    freshness_status: str
    readiness_status: str | None = None
    readiness_warnings: list[str] = []
    readiness_blocking_flags: list[str] = []


class LiveMapJobOut(BaseModel):
    job_id: str
    status: str
    assigned_engineer_id: str | None
    site_latitude: float | None
    site_longitude: float | None


class LiveMapOut(BaseModel):
    engineers: list[LiveMapEngineerOut]
    vehicles: list[LiveMapVehicleOut]
    jobs: list[LiveMapJobOut]


class EngineerAvailabilityRowOut(BaseModel):
    engineer_id: str
    availability_state: str
    active_job_count: int


class VehicleBindingIn(BaseModel):
    engineer_id: str
    vehicle_id: str

