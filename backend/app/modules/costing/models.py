from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LabourRateProfile(Base):
    """
    Model-driven labour rates and segmentation rules (overtime, travel, out-of-hours).
    Resolution: engineer-specific → contract-specific → role name → default_profile → env fallback.
    """

    __tablename__ = "labour_rate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    base_hourly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    overtime_hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    doubletime_hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    travel_hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    out_of_hours_hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    minimum_billable_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_profile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    applies_to_role_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    applies_to_engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    applies_to_contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=True, index=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Segmentation (UTC minute-of-day 0–1439; null = skip in/out-of-hours split)
    work_window_start_minutes_utc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_window_end_minutes_utc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overtime_threshold_minutes_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doubletime_threshold_minutes_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekend_uses_doubletime_rate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    travel_costing_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    holiday_placeholder_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobCostSnapshot(Base):
    """
    Immutable costing truth at job completion (standard cost basis + qty variances).
    Do not recalculate invoices from live master data after this exists for the job.
    """

    __tablename__ = "job_cost_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), unique=True, index=True, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    estimated_material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    estimated_material_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_material_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_material_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    material_cost_variance_vs_estimate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    material_cost_variance_vs_reserved: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    labour_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    labour_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    labour_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    labour_overtime_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    travel_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Rich labour segmentation (frozen at snapshot time)
    regular_labour_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtime_labour_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    doubletime_labour_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    travel_labour_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    out_of_hours_labour_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    break_minutes_excluded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    regular_labour_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    doubletime_labour_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    out_of_hours_labour_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    labour_rate_profile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("labour_rate_profiles.id"), nullable=True, index=True
    )
    labour_cost_warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    labour_cost_completeness: Mapped[str] = mapped_column(String(16), default="unavailable", nullable=False)

    labour_rule_set_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    holiday_calendar_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    labour_local_timezone_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    labour_rules_completeness_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    labour_rules_attribution_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    costing_status: Mapped[str] = mapped_column(String(32), default="clean", index=True, nullable=False)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Billable materials (sell) from actual usage × quote sell unit where applicable
    materials_billable_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobCostSnapshotLine(Base):
    __tablename__ = "job_cost_snapshot_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_cost_snapshots.id"), index=True, nullable=False)

    sku: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    stock_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    estimated_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    unit_cost_basis: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit_sell_quote: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    billable_from_actual: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    variance_flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    cost_basis_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
