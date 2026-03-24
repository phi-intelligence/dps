from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VehicleInspection(Base):
    """Daily / pre-use vehicle inspection (H&S operational readiness)."""

    __tablename__ = "vehicle_inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    vehicle_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)

    inspection_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    odometer: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # passed | failed_minor | failed_critical
    overall_status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class VehicleInspectionItem(Base):
    __tablename__ = "vehicle_inspection_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    inspection_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicle_inspections.id"), index=True, nullable=False)

    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_label: Mapped[str] = mapped_column(String(255), nullable=False)

    # pass | fail | advisory | n_a
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stored_documents.id"), nullable=True)

    # When result=fail, whether this failure is safety-critical for readiness.
    fail_criticality: Mapped[str] = mapped_column(String(16), nullable=False, default="minor")


class VehicleDefect(Base):
    __tablename__ = "vehicle_defects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    vehicle_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    inspection_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicle_inspections.id"), nullable=True, index=True)

    defect_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # open | resolved
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="open")

    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reported_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
