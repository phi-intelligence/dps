from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HolidayCalendar(Base):
    """
    Configurable holiday calendar for a region / tenant slice.
    Days are explicit rows (no hardcoded country lists in code).
    """

    __tablename__ = "holiday_calendars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # §5.18 — optional external feed (ICS or JSON) for admin-triggered imports
    external_feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_feed_format: Mapped[str] = mapped_column(String(16), default="ics", nullable=False)
    last_feed_import_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_feed_import_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_feed_import_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class HolidayCalendarDay(Base):
    __tablename__ = "holiday_calendar_days"

    __table_args__ = (UniqueConstraint("holiday_calendar_id", "calendar_date", name="uq_holiday_cal_day"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    holiday_calendar_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("holiday_calendars.id", ondelete="CASCADE"), index=True, nullable=False
    )
    calendar_date: Mapped[date] = mapped_column("calendar_date", Date, nullable=False, index=True)
    day_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # public_holiday | company_holiday | special_workday | normal_override
    label: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class LabourRuleSet(Base):
    """
    Regional labour segmentation: local work window, thresholds, weekend/holiday policies.
    Scoped by contract / site / engineer, else matched as default by region_code.
    """

    __tablename__ = "labour_rule_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    applies_to_contract_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contracts.id"), nullable=True, index=True
    )
    applies_to_site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True, index=True)
    applies_to_engineer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

    labour_rate_profile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("labour_rate_profiles.id"), nullable=True, index=True
    )
    holiday_calendar_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("holiday_calendars.id"), nullable=True, index=True
    )

    # Local minute-of-day 0–1439 in timezone_name
    normal_workday_start_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=9 * 60)
    normal_workday_end_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=17 * 60)

    overtime_threshold_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doubletime_threshold_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # weekend_policy: doubletime | out_of_hours | weekday_window
    weekend_policy: Mapped[str] = mapped_column(String(32), default="weekday_window", nullable=False)
    # holiday_public_policy / holiday_company_policy: doubletime | out_of_hours | normal_window
    holiday_public_policy: Mapped[str] = mapped_column(String(32), default="doubletime", nullable=False)
    holiday_company_policy: Mapped[str] = mapped_column(String(32), default="out_of_hours", nullable=False)
    special_workday_uses_normal_rates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # outside_window_ooh | threshold_only (pool all minutes for OT thresholds, no OOH split)
    out_of_hours_policy: Mapped[str] = mapped_column(String(32), default="outside_window_ooh", nullable=False)

    minimum_billable_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
