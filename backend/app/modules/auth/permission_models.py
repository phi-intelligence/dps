"""
Per-user permission grants (enterprise refinements on top of role baselines).

Secrets and AI keys do not belong here — only permission metadata.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserPermissionGrant(Base):
    """
    Explicit allow/deny overlay for a single permission key.
    Precedence (see authorization_service): user deny > user allow > group deny >
    group allow > union of role permissions > deny.
    """

    __tablename__ = "user_permission_grants"
    __table_args__ = (UniqueConstraint("user_id", "permission_key", name="uq_user_permission_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    permission_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # allow | deny
    effect: Mapped[str] = mapped_column(String(16), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class PermissionGrantAuditLog(Base):
    """Audit trail for grant lifecycle (enterprise accountability)."""

    __tablename__ = "permission_grant_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    grant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user_permission_grants.id"), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    target_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    permission_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # created | updated | deleted
    action: Mapped[str] = mapped_column(String(24), nullable=False)

    old_effect: Mapped[str | None] = mapped_column(String(16), nullable=True)
    new_effect: Mapped[str | None] = mapped_column(String(16), nullable=True)
    old_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    new_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
