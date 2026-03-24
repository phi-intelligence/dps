"""
Structured commercial workflow: contract reviews, repricing records, commercial audit log.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractReview(Base):
    """
    First-class commercial review workflow (renewal / repricing / health / risk).
    Status drives pipeline views; decision is explicit, not inferred from notes.
    """

    __tablename__ = "contract_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)

    # renewal | repricing | health_review | risk_review
    review_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # open | in_review | waiting_input | ready_for_decision | completed | cancelled
    status: Mapped[str] = mapped_column(String(32), default="open", index=True, nullable=False)

    # manual | recommendation | profitability_signal | rules_engine
    triggered_by: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    triggered_reason: Mapped[str] = mapped_column(Text, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    assigned_to_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    priority: Mapped[str] = mapped_column(String(16), default="normal", index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # renew_as_is | renew_with_repricing | monitor | escalate | exit_contract | defer
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Link back to ops intelligence when applicable
    source_recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operational_recommendations.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ContractRepricingReview(Base):
    """Structured repricing decision payload linked to a contract review."""

    __tablename__ = "contract_repricing_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    review_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_reviews.id"), index=True, nullable=False)

    current_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # JSON array of reason codes e.g. ["negative_margin","reactive_burden"]
    repricing_reason_codes_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    margin_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    burden_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_basis_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer_risk_level: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ContractRepricingProposal(Base):
    """
    Formal commercial proposal / CPQ output derived from a repricing review.
    Distinct from ContractRepricingReview — does not mutate contract pricing.
    """

    __tablename__ = "contract_repricing_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    repricing_review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_repricing_reviews.id"), index=True, nullable=False
    )
    review_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contract_reviews.id"), nullable=True, index=True)

    # draft | generated | internal_review | approved_internal | ready_for_customer | superseded | withdrawn
    proposal_status: Mapped[str] = mapped_column(String(32), default="generated", index=True, nullable=False)
    proposal_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)

    current_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validity_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    generated_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    ready_for_customer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    superseded_by_proposal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    pricing_basis_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    change_summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    stored_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stored_documents.id"), nullable=True, index=True
    )

    # --- Customer-facing lifecycle (distinct from internal proposal_status) ---
    # not_released | ready_for_customer | released | viewed | responded | withdrawn | expired
    customer_release_status: Mapped[str] = mapped_column(
        String(32), default="not_released", index=True, nullable=False
    )
    released_to_customer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    customer_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # accepted | rejected | counter_requested | needs_follow_up | acknowledged
    customer_response_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    customer_response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_response_by_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_expiry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    # e.g. contract_customer — how the proposal is exposed in portal when released
    portal_visibility_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Completed formal ProposalAcceptanceRecord.id (no DB FK — avoids circular dependency with acceptance table)
    formal_acceptance_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class ProposalCustomerResponse(Base):
    """Immutable audit row for each customer response to a released repricing proposal."""

    __tablename__ = "proposal_customer_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    response_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    responded_by_customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), index=True, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContractRepricingProposalLine(Base):
    """Structured commercial lines for auditability and CPQ-style explanation."""

    __tablename__ = "contract_repricing_proposal_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id", ondelete="CASCADE"), index=True, nullable=False
    )

    line_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="ea", nullable=False)

    current_unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_line_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_line_total: Mapped[float] = mapped_column(Float, nullable=False)
    variance_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    variance_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    justification_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ContractCommercialActionLog(Base):
    """Leadership/account continuity audit for commercial workflow."""

    __tablename__ = "contract_commercial_action_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    review_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contract_reviews.id"), index=True, nullable=True)

    action_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_summary: Mapped[str] = mapped_column(Text, nullable=False)

    performed_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
