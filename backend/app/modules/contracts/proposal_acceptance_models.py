"""
Formal customer proposal acceptance: auditable records and optional tokenized sessions.

This is not a substitute for third-party e-sign; evidence captures what the system observed
(name/email confirmation, channel, timestamps, IP/UA when available).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProposalAcceptanceRecord(Base):
    """Immutable-after-completion acceptance artifact linked to proposal / contract / customer."""

    __tablename__ = "proposal_acceptance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)

    source_proposal_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # initiated | viewed | completed | cancelled | expired
    acceptance_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # portal_acceptance | token_link_acceptance | acknowledgement_only
    acceptance_type: Mapped[str] = mapped_column(String(32), nullable=False)

    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    accepted_by_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accepted_by_customer_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    acceptance_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acceptance_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # portal | secure_link | internal_assisted
    acceptance_channel: Mapped[str] = mapped_column(String(32), nullable=False)

    acceptance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    immutable_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Distinguishes in-product confirmation vs third-party e-sign completion (orthogonal to acceptance_type).
    # in_product_acceptance | provider_esign | acknowledgement_only
    acceptance_evidence_type: Mapped[str] = mapped_column(
        String(32), default="in_product_acceptance", index=True, nullable=False
    )

    provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    provider_envelope_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    # draft | sent | viewed | signed | declined | voided | expired | failed
    provider_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    provider_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    amendment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_amendments.id"), nullable=True, index=True
    )


class ProposalAcceptanceSession(Base):
    """Session backing portal or secure-link acceptance; raw tokens are never persisted."""

    __tablename__ = "proposal_acceptance_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    acceptance_record_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("proposal_acceptance_records.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # active | completed | expired | cancelled
    session_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # When true, session tracks an external e-sign provider flow (not in-product click-through).
    esign_provider_flow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
