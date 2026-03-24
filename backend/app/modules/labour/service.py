from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from backend.app.modules.labour.models import HolidayCalendar, HolidayCalendarDay, LabourRuleSet
from backend.app.modules.labour.schemas import (
    HolidayCalendarCreateIn,
    HolidayCalendarDayCreateIn,
    HolidayCalendarPatchIn,
    LabourRuleSetCreateIn,
    LabourRuleSetPatchIn,
)


def create_holiday_calendar(db: Session, body: HolidayCalendarCreateIn) -> HolidayCalendar:
    fmt = (body.external_feed_format or "ics").strip().lower()
    if fmt not in ("ics", "json"):
        raise ValueError("external_feed_format must be ics or json")
    row = HolidayCalendar(
        id=str(uuid.uuid4()),
        name=body.name,
        region_code=body.region_code,
        timezone_name=body.timezone_name,
        active=body.active,
        notes=body.notes,
        external_feed_url=(body.external_feed_url or None),
        external_feed_format=fmt,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_holiday_calendar(db: Session, *, calendar_id: str, body: HolidayCalendarPatchIn) -> HolidayCalendar:
    row = db.get(HolidayCalendar, calendar_id)
    if not row:
        raise ValueError("Calendar not found")
    data = body.model_dump(exclude_unset=True)
    if "external_feed_format" in data and data["external_feed_format"] is not None:
        fmt = str(data["external_feed_format"]).strip().lower()
        if fmt not in ("ics", "json"):
            raise ValueError("external_feed_format must be ics or json")
        data["external_feed_format"] = fmt
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def list_holiday_calendars(db: Session, *, active_only: bool = False) -> list[HolidayCalendar]:
    q = db.query(HolidayCalendar)
    if active_only:
        q = q.filter(HolidayCalendar.active.is_(True))
    return q.order_by(HolidayCalendar.name.asc()).all()


def add_calendar_day(
    db: Session, *, calendar_id: str, body: HolidayCalendarDayCreateIn
) -> HolidayCalendarDay:
    cal = db.get(HolidayCalendar, calendar_id)
    if not cal:
        raise ValueError("Calendar not found")
    existing = (
        db.query(HolidayCalendarDay)
        .filter(
            HolidayCalendarDay.holiday_calendar_id == calendar_id,
            HolidayCalendarDay.calendar_date == body.calendar_date,
        )
        .first()
    )
    if existing:
        existing.day_type = body.day_type
        existing.label = body.label
        existing.notes = body.notes
        db.commit()
        db.refresh(existing)
        return existing
    row = HolidayCalendarDay(
        id=str(uuid.uuid4()),
        holiday_calendar_id=calendar_id,
        calendar_date=body.calendar_date,
        day_type=body.day_type,
        label=body.label,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_calendar_days(
    db: Session, *, calendar_id: str, from_date: date | None = None, to_date: date | None = None
) -> list[HolidayCalendarDay]:
    cal = db.get(HolidayCalendar, calendar_id)
    if not cal:
        raise ValueError("Calendar not found")
    q = db.query(HolidayCalendarDay).filter(HolidayCalendarDay.holiday_calendar_id == calendar_id)
    if from_date is not None:
        q = q.filter(HolidayCalendarDay.calendar_date >= from_date)
    if to_date is not None:
        q = q.filter(HolidayCalendarDay.calendar_date <= to_date)
    return q.order_by(HolidayCalendarDay.calendar_date.asc()).all()


def upsert_holiday_calendar_days(
    db: Session,
    *,
    calendar_id: str,
    days: list[tuple[date, str, str]],
) -> int:
    """
    Insert or update days (calendar_date, label, day_type). Single commit.
    """
    cal = db.get(HolidayCalendar, calendar_id)
    if not cal:
        raise ValueError("Calendar not found")
    n = 0
    for cal_date, label, day_type in days:
        existing = (
            db.query(HolidayCalendarDay)
            .filter(
                HolidayCalendarDay.holiday_calendar_id == calendar_id,
                HolidayCalendarDay.calendar_date == cal_date,
            )
            .first()
        )
        if existing:
            existing.day_type = day_type
            existing.label = label
        else:
            db.add(
                HolidayCalendarDay(
                    id=str(uuid.uuid4()),
                    holiday_calendar_id=calendar_id,
                    calendar_date=cal_date,
                    day_type=day_type,
                    label=label,
                    notes=None,
                )
            )
        n += 1
    db.commit()
    return n


def create_labour_rule_set(db: Session, body: LabourRuleSetCreateIn) -> LabourRuleSet:
    row = LabourRuleSet(
        id=str(uuid.uuid4()),
        **body.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_labour_rule_set(db: Session, *, rule_set_id: str, body: LabourRuleSetPatchIn) -> LabourRuleSet:
    row = db.get(LabourRuleSet, rule_set_id)
    if not row:
        raise ValueError("Labour rule set not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def list_labour_rule_sets(db: Session, *, active_only: bool = False) -> list[LabourRuleSet]:
    q = db.query(LabourRuleSet)
    if active_only:
        q = q.filter(LabourRuleSet.active.is_(True))
    return q.order_by(LabourRuleSet.name.asc()).all()
