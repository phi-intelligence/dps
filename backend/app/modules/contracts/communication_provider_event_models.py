"""
Inbound provider delivery webhooks: durable event log + linkage to contract customer communications.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommunicationProviderEvent(Base):
    __tablename__ = "communication_provider_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    provider_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    communication_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_customer_communications.id"), index=True, nullable=True
    )
    delivery_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_customer_communication_deliveries.id"), index=True, nullable=True
    )

    recipient_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    normalized_status: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)

    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    processing_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    external_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)


class CommunicationRecipientSuppression(Base):
    """
    Explicit outbound safety: hard bounces, complaints, and provider-reported unsubscribes.
    Multiple active rows per (customer, email) are allowed if kinds differ; send is blocked if any active.
    """

    __tablename__ = "communication_recipient_suppressions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)
    recipient_email_normalized: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # hard_bounce | spam_complaint | provider_unsubscribe
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    requires_manual_review: Mapped[bool] = mapped_column(default=False, nullable=False)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    last_provider_event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("communication_provider_events.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
