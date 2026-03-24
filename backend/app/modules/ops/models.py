from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecommendationSuppression(Base):
    """
    Scope-based suppression for scans: block new rows / match category+contract/site until expiry.
    """

    __tablename__ = "recommendation_suppressions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    recommendation_key: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=True)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)

    suppressed_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RecommendationOccurrenceEvent(Base):
    """One row each time a recommendation_key is emitted by a scan (for escalation)."""

    __tablename__ = "recommendation_occurrence_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


class OperationalRecommendation(Base):
    """
    Deterministic, explainable ops intelligence record (not dispatch engineer ranking).
    """

    __tablename__ = "operational_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    recommendation_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    related_job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=True)
    related_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    related_site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)
    related_asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), index=True, nullable=True)
    related_contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=True)
    related_invoice_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("invoices.id"), index=True, nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="open", index=True, nullable=False)

    recommendation_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_rule_version: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # dismissed | resolved | auto_resolved — set when leaving open/acknowledged
    closed_as: Mapped[str | None] = mapped_column(String(24), nullable=True)
    # UI snooze: hide from default lists until this time (scan may still refresh the row).
    suppressed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suppression_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RecommendationActionSuggestion(Base):
    """
    Deterministic suggested next step for an operational recommendation (advisory only).
    """

    __tablename__ = "recommendation_action_suggestions"
    __table_args__ = (UniqueConstraint("recommendation_id", "action_type", name="uq_rec_action_suggestion_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    recommendation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operational_recommendations.id"), index=True, nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_label: Mapped[str] = mapped_column(String(255), nullable=False)
    action_description: Mapped[str] = mapped_column(Text, nullable=False)

    # available | previewed | confirmed | executed | failed | cancelled | rejected
    action_status: Mapped[str] = mapped_column(String(24), default="available", index=True, nullable=False)

    preview_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_schema_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    requires_confirmation: Mapped[bool] = mapped_column(default=True, nullable=False)
    requires_override_reason: Mapped[bool] = mapped_column(default=False, nullable=False)
    # low | medium | high
    risk_level: Mapped[str] = mapped_column(String(16), default="medium", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RecommendationActionDecision(Base):
    """Audit trail for previews, confirmations, rejections, and execution outcomes."""

    __tablename__ = "recommendation_action_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    recommendation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operational_recommendations.id"), index=True, nullable=False
    )
    action_suggestion_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recommendation_action_suggestions.id"), index=True, nullable=True
    )

    # previewed | confirmed | rejected | executed | dismissed
    decision_type: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    decided_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
