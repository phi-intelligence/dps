from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FieldEquipment(Base):
    """
    Non-consumable operational asset (tools, test gear). Not inventory stock.
    """

    __tablename__ = "field_equipment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    equipment_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    equipment_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(128), index=True, nullable=False, default="general")

    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # available | assigned | in_service | under_repair | out_of_service | lost | retired
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="available")
    # owned | leased | customer_provided
    ownership_type: Mapped[str] = mapped_column(String(32), nullable=False, default="owned")

    # warehouse | van | engineer | site | workshop
    current_location_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="warehouse")
    current_location_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    assigned_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    assigned_vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    assigned_site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True, index=True)

    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    warranty_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    inspection_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    calibration_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    calibration_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    # not_required | valid | due_soon | expired
    calibration_status: Mapped[str] = mapped_column(String(24), index=True, nullable=False, default="not_required")

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class EquipmentMovement(Base):
    """Append-only movement / assignment audit trail."""

    __tablename__ = "equipment_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("field_equipment.id"), index=True, nullable=False)

    movement_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # assign_engineer | assign_vehicle | move_warehouse | move_van | move_site | workshop | out_of_service | return_from_repair | status_change | other

    prev_location_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    prev_location_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_location_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_location_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    prev_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    assigned_engineer_id_after: Mapped[str | None] = mapped_column(String(36), nullable=True)
    assigned_vehicle_id_after: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_site_id_after: Mapped[str | None] = mapped_column(String(36), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class JobEquipmentRequirement(Base):
    __tablename__ = "job_equipment_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    equipment_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(128), index=True, nullable=False, default="general")
    specific_equipment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("field_equipment.id"), nullable=True)

    calibration_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class EquipmentCalibrationRecord(Base):
    __tablename__ = "equipment_calibration_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("field_equipment.id"), index=True, nullable=False)

    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    certificate_document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stored_documents.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class EquipmentInspectionRecord(Base):
    __tablename__ = "equipment_inspection_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("field_equipment.id"), index=True, nullable=False)

    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_inspection_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    next_service_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    certificate_document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stored_documents.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
