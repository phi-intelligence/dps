from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortalSiteAccess(Base):
    """
    When rows exist for a customer, portal job/document visibility can be scoped to these sites
    (commercial / FM). Empty set = no extra restriction (legacy residential behaviour).
    """

    __tablename__ = "portal_site_access"
    __table_args__ = (UniqueConstraint("customer_id", "site_id", name="uq_portal_site_access_customer_site"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=False)
    access_level: Mapped[str] = mapped_column(
        String(32), default="full_access", nullable=False
    )  # full_access | operations_view | billing_only

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CustomerCommsEvent(Base):
    """
    Structured customer-facing communication / milestone hooks (SMS/email/push later).
    """

    __tablename__ = "customer_comms_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(16), default="logged", index=True, nullable=False)
    # logged | pending_send | sent | failed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
