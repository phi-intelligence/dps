"""
Contract-scoped customer communication workflow (draft → ready → approve → send).
Distinct from commercial action logs and from actual channel delivery (stubbed until providers exist).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractCustomerCommunication(Base):
    __tablename__ = "contract_customer_communications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)

    # repricing_proposal | contract_amendment | activation_confirmation | contract | customer_response
    source_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    communication_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # draft | ready_to_send | sent | failed | cancelled
    status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    # email | sms | portal_notice | internal_draft
    channel: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_key: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)

    recipient_customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=True, index=True
    )
    recipient_contact_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    stored_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stored_documents.id"), nullable=True, index=True
    )

    source_proposal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id"), nullable=True, index=True
    )
    source_amendment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_amendments.id"), nullable=True, index=True
    )
    source_activation_confirmation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_activation_confirmations.id"), nullable=True, index=True
    )
