from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HolidayCalendarCreateIn(BaseModel):
    name: str
    region_code: str
    timezone_name: str
    active: bool = True
    notes: str | None = None
    external_feed_url: str | None = None
    external_feed_format: str = "ics"


class HolidayCalendarPatchIn(BaseModel):
    name: str | None = None
    region_code: str | None = None
    timezone_name: str | None = None
    active: bool | None = None
    notes: str | None = None
    external_feed_url: str | None = None
    external_feed_format: str | None = None


class HolidayCalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    region_code: str
    timezone_name: str
    active: bool
    notes: str | None = None
    external_feed_url: str | None = None
    external_feed_format: str = "ics"
    last_feed_import_at: datetime | None = None
    last_feed_import_status: str | None = None
    last_feed_import_detail: str | None = None
    created_at: datetime


class HolidayCalendarFeedImportIn(BaseModel):
    """Trigger import from ``external_feed_url`` or a one-off ``feed_url`` override."""

    feed_url: str | None = None
    dry_run: bool = False
    apply_region_code: str | None = Field(None, max_length=64)


class HolidayCalendarFeedImportOut(BaseModel):
    calendar_id: str
    format_used: str
    imported_days: int
    dry_run: bool
    status: str
    detail: str | None = None


class HolidayCalendarDayCreateIn(BaseModel):
    calendar_date: date
    day_type: str
    label: str = ""
    notes: str | None = None


class HolidayCalendarDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    holiday_calendar_id: str
    calendar_date: date
    day_type: str
    label: str
    notes: str | None = None
    created_at: datetime


class LabourRuleSetCreateIn(BaseModel):
    name: str
    region_code: str
    timezone_name: str
    active: bool = True
    applies_to_contract_id: str | None = None
    applies_to_site_id: str | None = None
    applies_to_engineer_id: str | None = None
    labour_rate_profile_id: str | None = None
    holiday_calendar_id: str | None = None
    normal_workday_start_minutes: int = 9 * 60
    normal_workday_end_minutes: int = 17 * 60
    overtime_threshold_minutes: int | None = None
    doubletime_threshold_minutes: int | None = None
    weekend_policy: str = "weekday_window"
    holiday_public_policy: str = "doubletime"
    holiday_company_policy: str = "out_of_hours"
    special_workday_uses_normal_rates: bool = True
    out_of_hours_policy: str = "outside_window_ooh"
    minimum_billable_minutes: int | None = None
    notes: str | None = None


class LabourRuleSetPatchIn(BaseModel):
    name: str | None = None
    region_code: str | None = None
    timezone_name: str | None = None
    active: bool | None = None
    applies_to_contract_id: str | None = None
    applies_to_site_id: str | None = None
    applies_to_engineer_id: str | None = None
    labour_rate_profile_id: str | None = None
    holiday_calendar_id: str | None = None
    normal_workday_start_minutes: int | None = None
    normal_workday_end_minutes: int | None = None
    overtime_threshold_minutes: int | None = None
    doubletime_threshold_minutes: int | None = None
    weekend_policy: str | None = None
    holiday_public_policy: str | None = None
    holiday_company_policy: str | None = None
    special_workday_uses_normal_rates: bool | None = None
    out_of_hours_policy: str | None = None
    minimum_billable_minutes: int | None = None
    notes: str | None = None


class LabourRuleSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    region_code: str
    timezone_name: str
    active: bool
    applies_to_contract_id: str | None = None
    applies_to_site_id: str | None = None
    applies_to_engineer_id: str | None = None
    labour_rate_profile_id: str | None = None
    holiday_calendar_id: str | None = None
    normal_workday_start_minutes: int
    normal_workday_end_minutes: int
    overtime_threshold_minutes: int | None = None
    doubletime_threshold_minutes: int | None = None
    weekend_policy: str
    holiday_public_policy: str
    holiday_company_policy: str
    special_workday_uses_normal_rates: bool
    out_of_hours_policy: str
    minimum_billable_minutes: int | None = None
    notes: str | None = None
    created_at: datetime


class LabourRuleSetOutWithMeta(LabourRuleSetOut):
    """Same row plus optional resolved hints for APIs."""

    meta: dict[str, Any] = Field(default_factory=dict)
