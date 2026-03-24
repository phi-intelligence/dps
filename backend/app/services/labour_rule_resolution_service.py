"""
Resolve which LabourRuleSet + HolidayCalendar + timezone apply to a job.

Precedence (first match wins):
1. Contract-specific rule set
2. Site-specific rule set
3. Engineer-specific rule set
4. Default active rule set (no scope columns), preferring region_code match to inferred job region
5. Legacy fallback: no rule set → caller uses UTC + LabourRateProfile windows only
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from backend.app.modules.dispatch.models import Job
from backend.app.modules.labour.models import HolidayCalendar, HolidayCalendarDay, LabourRuleSet
from backend.app.modules.sites.models import Site


def _infer_region_code(db: Session, job: Job) -> str:
    if job.site_id:
        s = db.get(Site, job.site_id)
        if s and (s.service_region or "").strip():
            return (s.service_region or "").strip()
    return "DEFAULT"


def _load_calendar_days_map(db: Session, calendar_id: str) -> dict[date, HolidayCalendarDay]:
    rows = (
        db.query(HolidayCalendarDay)
        .filter(HolidayCalendarDay.holiday_calendar_id == calendar_id)
        .all()
    )
    return {r.calendar_date: r for r in rows}


@dataclass
class ResolvedLabourRules:
    rule_set: LabourRuleSet | None
    holiday_calendar: HolidayCalendar | None
    calendar_days_by_date: dict[date, HolidayCalendarDay]
    timezone_name: str
    tz: ZoneInfo
    resolution_source: str  # contract | site | engineer | default | legacy
    inferred_region_code: str
    warnings: list[str] = field(default_factory=list)
    rules_completeness_status: str = "clean"  # clean | partial | fallback

    def to_attribution_dict(self) -> dict[str, Any]:
        return {
            "labour_rule_set_id": self.rule_set.id if self.rule_set else None,
            "labour_rule_set_name": self.rule_set.name if self.rule_set else None,
            "holiday_calendar_id": self.holiday_calendar.id if self.holiday_calendar else None,
            "holiday_calendar_name": self.holiday_calendar.name if self.holiday_calendar else None,
            "local_timezone_name": self.timezone_name,
            "resolution_source": self.resolution_source,
            "inferred_region_code": self.inferred_region_code,
            "rules_completeness_status": self.rules_completeness_status,
            "labour_rule_warnings": list(self.warnings),
        }


def resolve_zoneinfo(timezone_name: str) -> tuple[ZoneInfo, list[str]]:
    w: list[str] = []
    try:
        return ZoneInfo(timezone_name), w
    except ZoneInfoNotFoundError:
        w.append(f"invalid_timezone:{timezone_name}:using_UTC")
        return ZoneInfo("UTC"), w


def resolve_labour_rules_for_job(db: Session, job: Job) -> ResolvedLabourRules:
    inferred = _infer_region_code(db, job)
    q_base = db.query(LabourRuleSet).filter(LabourRuleSet.active.is_(True))

    picked: LabourRuleSet | None = None
    source = "legacy"

    if job.contract_id:
        picked = q_base.filter(LabourRuleSet.applies_to_contract_id == job.contract_id).first()
        if picked:
            source = "contract"
    if not picked and job.site_id:
        picked = q_base.filter(LabourRuleSet.applies_to_site_id == job.site_id).first()
        if picked:
            source = "site"
    if not picked and job.assigned_engineer_id:
        picked = q_base.filter(LabourRuleSet.applies_to_engineer_id == job.assigned_engineer_id).first()
        if picked:
            source = "engineer"

    if not picked:
        defaults = (
            q_base.filter(
                LabourRuleSet.applies_to_contract_id.is_(None),
                LabourRuleSet.applies_to_site_id.is_(None),
                LabourRuleSet.applies_to_engineer_id.is_(None),
            )
            .order_by(LabourRuleSet.created_at.asc())
            .all()
        )
        for cand in defaults:
            if cand.region_code in ("*", "DEFAULT", inferred):
                picked = cand
                source = "default"
                break
        if not picked and defaults:
            picked = defaults[0]
            source = "default"
            inferred_w = f"labour_rule_default_region_mismatch:using_rule_region={picked.region_code}:inferred={inferred}"
            return _finalize_resolution(db, job, picked, source, inferred, extra_warnings=[inferred_w])

    if not picked:
        tz, tw = resolve_zoneinfo("UTC")
        return ResolvedLabourRules(
            rule_set=None,
            holiday_calendar=None,
            calendar_days_by_date={},
            timezone_name="UTC",
            tz=tz,
            resolution_source="legacy",
            inferred_region_code=inferred,
            warnings=["no_labour_rule_set_configured:using_legacy_utc_labour_window"] + tw,
            # Regional rules layer incomplete; labour_completeness still reflects profile/timesheet quality.
            rules_completeness_status="partial",
        )

    return _finalize_resolution(db, job, picked, source, inferred, extra_warnings=[])


def _finalize_resolution(
    db: Session,
    job: Job,
    picked: LabourRuleSet,
    source: str,
    inferred: str,
    *,
    extra_warnings: list[str],
) -> ResolvedLabourRules:
    warnings = list(extra_warnings)
    cal: HolidayCalendar | None = None
    days_map: dict[date, HolidayCalendarDay] = {}

    if picked.holiday_calendar_id:
        cal = db.get(HolidayCalendar, picked.holiday_calendar_id)
        if cal and cal.active:
            days_map = _load_calendar_days_map(db, cal.id)
        else:
            warnings.append("labour_rule_holiday_calendar_missing_or_inactive")
            cal = None

    # Policy expects holiday treatment but no calendar linked
    if (
        picked.holiday_public_policy in ("doubletime", "out_of_hours")
        or picked.holiday_company_policy in ("doubletime", "out_of_hours")
    ) and cal is None:
        warnings.append("holiday_policy_requires_calendar:no_active_calendar_linked")

    tz, tw = resolve_zoneinfo(picked.timezone_name)
    warnings.extend(tw)

    completeness = "clean"
    if warnings:
        completeness = "partial"
    if extra_warnings:
        completeness = "partial"

    if job.site_id:
        s = db.get(Site, job.site_id)
        sr = (s.service_region or "").strip() if s else ""
        if (
            sr
            and picked.region_code not in ("*", "DEFAULT")
            and sr != picked.region_code
        ):
            warnings.append(f"labour_rule_region_mismatch:rule={picked.region_code}:site_region={sr}")

    return ResolvedLabourRules(
        rule_set=picked,
        holiday_calendar=cal,
        calendar_days_by_date=days_map,
        timezone_name=str(tz.key) if hasattr(tz, "key") else picked.timezone_name,
        tz=tz,
        resolution_source=source,
        inferred_region_code=inferred,
        warnings=warnings,
        rules_completeness_status=completeness,
    )


def segment_treatment_for_local_date(
    *,
    local_d: date,
    calendar_days: dict[date, HolidayCalendarDay],
    weekend_policy: str,
    holiday_public_policy: str,
    holiday_company_policy: str,
    special_workday_uses_normal: bool,
    profile_weekend_doubletime: bool,
) -> tuple[str, dict[str, Any]]:
    """
    Returns (treatment, meta) where treatment is:
    - doubletime: all minutes bucketed as doubletime
    - out_of_hours: all minutes as OOH
    - window: normal in-window / OOH / threshold split
    meta includes day_type, holiday_applied, weekend_applied, natural_weekend
    """
    day_row = calendar_days.get(local_d)
    meta: dict[str, Any] = {
        "local_date": local_d.isoformat(),
        "day_type": day_row.day_type if day_row else None,
        "label": day_row.label if day_row else None,
        "holiday_applied": False,
        "weekend_applied": False,
        "natural_weekend": local_d.weekday() >= 5,
    }

    if day_row:
        meta["holiday_applied"] = True
        if day_row.day_type == "public_holiday":
            meta["weekend_applied"] = False
            pol = holiday_public_policy
            if pol == "doubletime":
                return "doubletime", meta
            if pol == "out_of_hours":
                return "out_of_hours", meta
            return "window", meta
        if day_row.day_type == "company_holiday":
            pol = holiday_company_policy
            if pol == "doubletime":
                return "doubletime", meta
            if pol == "out_of_hours":
                return "out_of_hours", meta
            return "window", meta
        if day_row.day_type == "special_workday":
            if special_workday_uses_normal:
                return "window", meta
            if weekend_policy == "doubletime":
                return "doubletime", meta
            if weekend_policy == "out_of_hours":
                return "out_of_hours", meta
            return "window", meta
        if day_row.day_type == "normal_override":
            return "window", meta

    if local_d.weekday() >= 5:
        meta["weekend_applied"] = True
        if weekend_policy == "doubletime" or profile_weekend_doubletime:
            return "doubletime", meta
        if weekend_policy == "out_of_hours":
            return "out_of_hours", meta
        return "window", meta

    return "window", meta
