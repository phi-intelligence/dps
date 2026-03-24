"""
Customer-facing activation confirmation workflow (distinct from internal amendment activation truth).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractActivationConfirmation(Base):
    """
    Structured record for commercial activation confirmation shown to customers after internal activation.
    Statuses: pending_generation | generated | ready_for_customer | released | viewed | acknowledged
              | withdrawn | superseded
    """

    __tablename__ = "contract_activation_confirmations"
    __table_args__ = (UniqueConstraint("confirmation_reference", name="uq_activation_confirmation_ref"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    amendment_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_amendments.id"), index=True, nullable=False)
    contract_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_versions.id"), index=True, nullable=True
    )
    source_proposal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id"), index=True, nullable=True
    )

    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    confirmation_reference: Mapped[str] = mapped_column(String(96), nullable=False)

    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    confirmation_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_to_customer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    customer_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_acknowledged_by_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_acknowledgement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portal_visibility_scope: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    stored_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stored_documents.id"), nullable=True, index=True
    )

    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
