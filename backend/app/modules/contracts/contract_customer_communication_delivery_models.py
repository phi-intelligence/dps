"""
First-class delivery attempts for contract customer communications (audit + future webhooks).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractCustomerCommunicationDelivery(Base):
    __tablename__ = "contract_customer_communication_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    communication_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contract_customer_communications.id"), index=True, nullable=False
    )

    channel: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # started | sent | failed | delivered | bounced | complained | cancelled
    status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    recipient_address: Mapped[str | None] = mapped_column(String(512), nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    response_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
