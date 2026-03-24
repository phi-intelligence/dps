from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VehicleTelemetryPoint(Base):
    __tablename__ = "vehicle_telemetry_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)


class JobGeofence(Base):
    __tablename__ = "job_geofences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), unique=True, index=True, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class EngineerTelemetryEvent(Base):
    """
    Append-only engineer (phone) telemetry history for dispatch intelligence.
    """

    __tablename__ = "engineer_telemetry_events"
    __table_args__ = (Index("ix_engineer_telemetry_engineer_occurred", "engineer_id", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    engineer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)

    source: Mapped[str] = mapped_column(String(16), default="phone", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    battery_pct: Mapped[float | None] = mapped_column(Float, nullable=True)


class EngineerLatestLocation(Base):
    """
    Latest known engineer position for fast dispatch queries (not a history scan).
    """

    __tablename__ = "engineer_latest_locations"

    engineer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)

    last_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    last_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    last_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_battery_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # fresh | aging | stale
    last_source: Mapped[str] = mapped_column(String(16), default="phone", nullable=False)


class VehicleTelemetryEvent(Base):
    """
    Append-only vehicle telemetry (van hardware or integrated feeds).
    """

    __tablename__ = "vehicle_telemetry_events"
    __table_args__ = (Index("ix_vehicle_telemetry_vehicle_occurred", "vehicle_id", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    assigned_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    ignition_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fuel_level_pct: Mapped[float | None] = mapped_column(Float, nullable=True)


class VehicleLatestLocation(Base):
    __tablename__ = "vehicle_latest_locations"

    vehicle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assigned_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)

    last_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    last_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    last_heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_ignition_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_fuel_level_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(16), index=True, nullable=False)

