from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=True)

    asset_code: Mapped[str] = mapped_column(String(64), index=True, default="", nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    install_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    commissioning_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    warranty_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="in_service", index=True, nullable=False)
    criticality: Mapped[str] = mapped_column(String(32), default="standard", nullable=False)

    service_interval_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_interval_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    required_competencies_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Legacy / denormalised location line (kept for backward compatibility).
    location_address: Mapped[str] = mapped_column(Text, nullable=False)

    next_maintenance_eta_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), index=True, nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(32), default="date", index=True, nullable=False)

    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
