from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalRequest(Base):
    """
    First-class approval workflow for sensitive actions.
    Status transitions: pending → approved | rejected | cancelled
    """

    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    approval_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    requested_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    assigned_to_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    # pending | approved | rejected | cancelled
    status: Mapped[str] = mapped_column(String(24), index=True, nullable=False, default="pending")

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Set when approved path executes side effects (idempotency / audit).
    execution_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApprovalAuditLog(Base):
    """Append-only audit for approval lifecycle (who / when / what)."""

    __tablename__ = "approval_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    approval_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("approval_requests.id"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
