from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"), nullable=True)
    quote_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("quotes.id"), nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=True)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), index=True, nullable=True)
    ppm_schedule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ppm_schedules.id"), index=True, nullable=True
    )

    # reactive | planned_maintenance
    work_type: Mapped[str] = mapped_column(String(32), default="reactive", index=True, nullable=False)

    sla_policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sla_policies.id"), nullable=True, index=True)
    sla_priority: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    asset_criticality: Mapped[str | None] = mapped_column(String(32), nullable=True)
    covered_under_contract: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compliance_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # SLA clock milestones (set by workflow / integrations).
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    en_route_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    on_site_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    address: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="created", index=True, nullable=False)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_engineer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    # Dispatch / site geometry (do not parse free-text address for distance math).
    site_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    site_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address_geocoded_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address_geocoded_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # materials_optional | materials_required | no_materials_expected
    material_policy: Mapped[str] = mapped_column(String(32), default="materials_optional", index=True, nullable=False)
    dispatch_priority: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    required_competencies_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Customer ETA / tracking / comms (portal slice).
    on_my_way_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_link_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    manual_eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_eta_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobEtaState(Base):
    """
    Tracks last computed ETA so we can detect worsening conditions and trigger delay notices.
    """

    __tablename__ = "job_eta_states"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), primary_key=True)
    last_eta_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    last_eta_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobEtaDelayNotice(Base):
    """
    Best-effort delay notices for customer communication (automation step from the spec).
    """

    __tablename__ = "job_eta_delay_notices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    eta_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobFormRequirement(Base):
    """
    Defines required keys a form submission must provide to let a job complete.

    This is a minimal Phase 3.1 implementation slice:
    - required_keys stored as JSON list in `required_keys_json`
    - satisfied_at set when engineer submits a passing form
    """

    __tablename__ = "job_form_requirements"

    __table_args__ = (
        UniqueConstraint("job_id", "form_key", name="uq_job_form_requirements_job_form_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    form_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    required_keys_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobFormSubmission(Base):
    """
    Engineer submissions for a specific job + form_key.
    """

    __tablename__ = "job_form_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    form_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Arbitrary JSON object from the engineer app.
    data_json: Mapped[str] = mapped_column(Text, nullable=False)

    submitted_by_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobSignatureRequirement(Base):
    """
    Required engineer signature for job completion (configured per job).
    """

    __tablename__ = "job_signature_requirements"

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_job_signature_requirement_job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobSignatureSubmission(Base):
    __tablename__ = "job_signature_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    signed_by_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    # Keep it generic: store signature as JSON metadata (or base64 in a later phase).
    signature_json: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobMediaRequirement(Base):
    """
    Required number of photos/videos (configured per job).
    """

    __tablename__ = "job_media_requirements"

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_job_media_requirement_job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    required_photo_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobMediaSubmission(Base):
    __tablename__ = "job_media_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), default="photo", index=True, nullable=False)  # photo/video
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_by_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobMediaUploadSession(Base):
    __tablename__ = "job_media_upload_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), default="photo", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True, nullable=False)  # open|committed|expired
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

class JobPartsUsageRequirement(Base):
    """
    Required parts usage count for job completion (configured per job).
    """

    __tablename__ = "job_parts_usage_requirements"

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_job_parts_usage_requirement_job_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    required_parts_items_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobPartsUsageSubmission(Base):
    __tablename__ = "job_parts_usage_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    # Generic payload for now; later phases will normalize stock reservations.
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_by_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobPartUsageLine(Base):
    """
    Normalized line from engineer parts usage with explicit reconciliation vs reservations.
    """

    __tablename__ = "job_part_usage_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_parts_usage_submissions.id"), index=True, nullable=False
    )

    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # matched | overused | unreserved | unavailable | shortage
    match_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    reserved_available_for_sku: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobPartsReconciliationApproval(Base):
    """
    Dispatcher/admin override when strict reconciliation blocks completion.
    """

    __tablename__ = "job_parts_reconciliation_approvals"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), primary_key=True)
    approved_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobActivityEvent(Base):
    """
    Auditable timeline events for engineer job activity.

    Wave 8 initial slice stores engineer notes as timeline events.
    """

    __tablename__ = "job_activity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    author_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(32), default="note", index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="engineer_note", index=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class DispatchDecisionLog(Base):
    """
    Auditable record for dispatch intelligence (recommendations, auto-assign, future manual overrides).
    """

    __tablename__ = "dispatch_decision_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    decision_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    # recommendation | auto_assign | manual_override (future)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    chosen_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    ranked_candidates_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    scoring_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

