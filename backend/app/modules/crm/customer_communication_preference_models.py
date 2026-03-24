"""
Per-customer outbound communication preferences (channel enablement, preferred address, quiet hours).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CustomerCommunicationPreference(Base):
    __tablename__ = "customer_communication_preferences"
    __table_args__ = (UniqueConstraint("customer_id", "channel", "contact_reference", name="uq_customer_comm_pref"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)

    # email | sms | portal_notice (reserved)
    channel: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # When set, this row applies to a specific address (email/phone). NULL = channel-wide default.
    contact_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    quiet_hours_start: Mapped[str | None] = mapped_column(String(8), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[str | None] = mapped_column(String(8), nullable=True)
    timezone_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
