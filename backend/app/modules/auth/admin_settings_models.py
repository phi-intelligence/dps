from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AdminSettingValue(Base):
    """
    Domain-level settings override (JSON blob per domain).
    Example keys: feature_flags, dispatch
    """

    __tablename__ = "admin_setting_values"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class AdminSettingAuditLog(Base):
    """
    Immutable audit log for settings changes.
    """

    __tablename__ = "admin_setting_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    old_value_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    new_value_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

