from __future__ import annotations

from datetime import date

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_permission
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.modules.labour.schemas import (
    HolidayCalendarCreateIn,
    HolidayCalendarDayCreateIn,
    HolidayCalendarDayOut,
    HolidayCalendarFeedImportIn,
    HolidayCalendarFeedImportOut,
    HolidayCalendarOut,
    HolidayCalendarPatchIn,
    LabourRuleSetCreateIn,
    LabourRuleSetOut,
    LabourRuleSetPatchIn,
)
from backend.app.modules.labour.models import HolidayCalendar, LabourRuleSet
from backend.app.modules.labour.service import (
    add_calendar_day,
    create_holiday_calendar,
    create_labour_rule_set,
    list_calendar_days,
    list_holiday_calendars,
    list_labour_rule_sets,
    patch_holiday_calendar,
    patch_labour_rule_set,
)
from backend.app.services.holiday_calendar_feed_service import import_holiday_calendar_feed
from backend.app.services.authorization_policy import CAN_MANAGE_LABOUR_RULES

router = APIRouter(prefix="/labour", tags=["labour"])


@router.post("/calendars", response_model=HolidayCalendarOut, status_code=status.HTTP_201_CREATED)
def post_calendar(
    body: HolidayCalendarCreateIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> HolidayCalendarOut:
    try:
        return HolidayCalendarOut.model_validate(create_holiday_calendar(db, body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/calendars", response_model=list[HolidayCalendarOut])
def get_calendars(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> list[HolidayCalendarOut]:
    return [HolidayCalendarOut.model_validate(x) for x in list_holiday_calendars(db, active_only=active_only)]


@router.get("/calendars/{calendar_id}", response_model=HolidayCalendarOut)
def get_calendar(
    calendar_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> HolidayCalendarOut:
    row = db.get(HolidayCalendar, calendar_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return HolidayCalendarOut.model_validate(row)


@router.patch("/calendars/{calendar_id}", response_model=HolidayCalendarOut)
def patch_calendar(
    calendar_id: str,
    body: HolidayCalendarPatchIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> HolidayCalendarOut:
    try:
        return HolidayCalendarOut.model_validate(patch_holiday_calendar(db, calendar_id=calendar_id, body=body))
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e)) from e


@router.post("/calendars/{calendar_id}/days", response_model=HolidayCalendarDayOut, status_code=status.HTTP_201_CREATED)
def post_calendar_day(
    calendar_id: str,
    body: HolidayCalendarDayCreateIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> HolidayCalendarDayOut:
    try:
        return HolidayCalendarDayOut.model_validate(add_calendar_day(db, calendar_id=calendar_id, body=body))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/calendars/{calendar_id}/days", response_model=list[HolidayCalendarDayOut])
def get_calendar_days(
    calendar_id: str,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> list[HolidayCalendarDayOut]:
    try:
        rows = list_calendar_days(db, calendar_id=calendar_id, from_date=from_date, to_date=to_date)
        return [HolidayCalendarDayOut.model_validate(x) for x in rows]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/calendars/{calendar_id}/import-feed", response_model=HolidayCalendarFeedImportOut)
def post_calendar_import_feed(
    calendar_id: str,
    body: HolidayCalendarFeedImportIn | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> HolidayCalendarFeedImportOut:
    """§5.18 — fetch external ICS/JSON feed and upsert holiday days (admin-managed)."""
    b = body or HolidayCalendarFeedImportIn()
    try:
        result = import_holiday_calendar_feed(
            db,
            calendar_id=calendar_id,
            feed_url=b.feed_url,
            dry_run=b.dry_run,
            apply_region_code=b.apply_region_code,
        )
        return HolidayCalendarFeedImportOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Feed fetch failed: {e}") from e


@router.post("/rule-sets", response_model=LabourRuleSetOut, status_code=status.HTTP_201_CREATED)
def post_rule_set(
    body: LabourRuleSetCreateIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> LabourRuleSetOut:
    return LabourRuleSetOut.model_validate(create_labour_rule_set(db, body))


@router.get("/rule-sets", response_model=list[LabourRuleSetOut])
def get_rule_sets(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> list[LabourRuleSetOut]:
    return [LabourRuleSetOut.model_validate(x) for x in list_labour_rule_sets(db, active_only=active_only)]


@router.get("/rule-sets/{rule_set_id}", response_model=LabourRuleSetOut)
def get_rule_set(
    rule_set_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> LabourRuleSetOut:
    row = db.get(LabourRuleSet, rule_set_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return LabourRuleSetOut.model_validate(row)


@router.patch("/rule-sets/{rule_set_id}", response_model=LabourRuleSetOut)
def patch_rule_set(
    rule_set_id: str,
    body: LabourRuleSetPatchIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_LABOUR_RULES)),
) -> LabourRuleSetOut:
    try:
        return LabourRuleSetOut.model_validate(patch_labour_rule_set(db, rule_set_id=rule_set_id, body=body))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
