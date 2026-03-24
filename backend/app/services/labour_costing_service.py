"""
Deterministic labour cost segmentation: regular / overtime / doubletime / out-of-hours / travel.

When a LabourRuleSet applies: local timezone, configurable weekend/holiday policies, and
HolidayCalendarDay rows drive treatment. Otherwise legacy UTC window + profile behaviour.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.costing.models import LabourRateProfile
from backend.app.modules.dispatch.models import Job
from backend.app.modules.labour.models import LabourRuleSet
from backend.app.modules.time_tracking.models import Punch, TimesheetApproval
from backend.app.services.labour_rule_resolution_service import (
    ResolvedLabourRules,
    resolve_labour_rules_for_job,
    segment_treatment_for_local_date,
)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_date_str(dt: datetime) -> str:
    a = _aware(dt)
    return a.date().isoformat() if a else ""


class _ProfileLike(Protocol):
    id: str | None
    name: str
    base_hourly_rate: float
    overtime_hourly_rate: float | None
    doubletime_hourly_rate: float | None
    travel_hourly_rate: float | None
    out_of_hours_hourly_rate: float | None
    minimum_billable_minutes: int | None
    work_window_start_minutes_utc: int | None
    work_window_end_minutes_utc: int | None
    overtime_threshold_minutes_per_day: int | None
    doubletime_threshold_minutes_per_day: int | None
    weekend_uses_doubletime_rate: bool
    travel_costing_enabled: bool


@dataclass
class _FallbackProfile:
    """Env-driven profile when no DB row matches."""

    id: None = None
    name: str = "env_fallback"
    base_hourly_rate: float = 60.0
    overtime_hourly_rate: float | None = None
    doubletime_hourly_rate: float | None = None
    travel_hourly_rate: float | None = None
    out_of_hours_hourly_rate: float | None = None
    minimum_billable_minutes: int | None = None
    work_window_start_minutes_utc: int | None = 9 * 60
    work_window_end_minutes_utc: int | None = 17 * 60
    overtime_threshold_minutes_per_day: int | None = 480
    doubletime_threshold_minutes_per_day: int | None = None
    weekend_uses_doubletime_rate: bool = False
    travel_costing_enabled: bool = True


def resolve_labour_rate_profile(db: Session, job: Job) -> tuple[LabourRateProfile | _FallbackProfile, list[str]]:
    warnings: list[str] = []
    q = db.query(LabourRateProfile).filter(LabourRateProfile.active.is_(True))

    if job.assigned_engineer_id:
        p = q.filter(LabourRateProfile.applies_to_engineer_id == job.assigned_engineer_id).first()
        if p:
            return p, warnings

    if job.contract_id:
        p = q.filter(LabourRateProfile.applies_to_contract_id == job.contract_id).first()
        if p:
            return p, warnings

    user = db.get(User, job.assigned_engineer_id) if job.assigned_engineer_id else None
    if user and user.roles:
        for role in user.roles:
            p = q.filter(LabourRateProfile.applies_to_role_name == role.name).first()
            if p:
                return p, warnings

    default_p = q.filter(LabourRateProfile.default_profile.is_(True)).first()
    if default_p:
        return default_p, warnings

    warnings.append("no_labour_rate_profile:using_env_fallback")
    fb = _FallbackProfile(
        base_hourly_rate=float(settings.PHI_DPS_LABOUR_HOURLY_RATE),
        overtime_hourly_rate=round(
            float(settings.PHI_DPS_LABOUR_HOURLY_RATE) * float(settings.PHI_DPS_OVERTIME_MULTIPLIER), 4
        ),
    )
    return fb, warnings


def resolve_labour_rate_profile_with_ruleset(
    db: Session, job: Job, rule_set: LabourRuleSet | None
) -> tuple[LabourRateProfile | _FallbackProfile, list[str]]:
    if rule_set and rule_set.labour_rate_profile_id:
        p = db.get(LabourRateProfile, rule_set.labour_rate_profile_id)
        if p and p.active:
            return p, []
        return resolve_labour_rate_profile(db, job)
    return resolve_labour_rate_profile(db, job)


def _split_segment_at_midnight(t0: datetime, t1: datetime) -> list[tuple[datetime, datetime]]:
    out: list[tuple[datetime, datetime]] = []
    cur = _aware(t0) or t0
    end = _aware(t1) or t1
    while cur < end:
        next_midnight = cur.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seg_end = min(end, next_midnight)
        if cur < seg_end:
            out.append((cur, seg_end))
        cur = seg_end
    return out


def _split_segment_at_local_midnight(
    t0: datetime, t1: datetime, tz: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    """Split [t0,t1) at each local midnight in tz. Returns UTC-aware bounds."""
    out: list[tuple[datetime, datetime]] = []
    cur = (_aware(t0) or t0).astimezone(tz)
    end = (_aware(t1) or t1).astimezone(tz)
    while cur < end:
        next_mid = cur.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seg_end = min(end, next_mid)
        if cur < seg_end:
            out.append((cur.astimezone(timezone.utc), seg_end.astimezone(timezone.utc)))
        cur = seg_end
    return out


def _ooh_minutes_in_segment(t0: datetime, t1: datetime, ws: int | None, we: int | None) -> tuple[int, int]:
    if ws is None or we is None or ws >= we:
        a0, a1 = _aware(t0), _aware(t1)
        if not a0 or not a1:
            return 0, 0
        total = max(0, int((a1 - a0).total_seconds() // 60))
        return total, 0

    in_win = 0
    ooh = 0
    for a, b in _split_segment_at_midnight(t0, t1):
        total_seg = max(0, int((b - a).total_seconds() // 60))
        if total_seg == 0:
            continue
        sod = a.replace(hour=0, minute=0, second=0, microsecond=0)
        ma = int((a - sod).total_seconds() // 60)
        mb = int((b - sod).total_seconds() // 60)
        lo = max(ma, ws)
        hi = min(mb, we)
        inside = max(0, hi - lo)
        in_win += inside
        ooh += total_seg - inside
    return in_win, ooh


def _ooh_minutes_in_segment_local(
    t0_utc: datetime, t1_utc: datetime, ws: int, we: int, tz: ZoneInfo
) -> tuple[int, int]:
    """In-window vs OOH using minute-of-day in local timezone (same calendar day per segment)."""
    if ws >= we:
        a0, a1 = _aware(t0_utc), _aware(t1_utc)
        if not a0 or not a1:
            return 0, 0
        total = max(0, int((a1 - a0).total_seconds() // 60))
        return total, 0
    in_win = 0
    ooh = 0
    for u0, u1 in _split_segment_at_local_midnight(t0_utc, t1_utc, tz):
        a = u0.astimezone(tz)
        b = u1.astimezone(tz)
        total_seg = max(0, int((b - a).total_seconds() // 60))
        if total_seg == 0:
            continue
        sod = a.replace(hour=0, minute=0, second=0, microsecond=0)
        ma = int((a - sod).total_seconds() // 60)
        mb = int((b - sod).total_seconds() // 60)
        lo = max(ma, ws)
        hi = min(mb, we)
        inside = max(0, hi - lo)
        in_win += inside
        ooh += total_seg - inside
    return in_win, ooh


def _gather_punch_sessions(db: Session, *, job_id: str) -> list[tuple[str, datetime, datetime]]:
    punches = (
        db.query(Punch)
        .filter(Punch.job_id == job_id, Punch.kind.in_(["in", "out"]))
        .order_by(Punch.occurred_at.asc())
        .all()
    )
    open_by_user: dict[str, Punch] = {}
    sessions: list[tuple[str, datetime, datetime]] = []
    for p in punches:
        if p.kind == "in":
            open_by_user[p.user_id] = p
        elif p.kind == "out":
            pin = open_by_user.pop(p.user_id, None)
            if pin:
                t0, t1 = _aware(pin.occurred_at), _aware(p.occurred_at)
                if t0 and t1 and t1 > t0:
                    sessions.append((p.user_id, t0, t1))
    return sessions


def _travel_minutes_from_job(job: Job) -> tuple[int, list[str]]:
    warnings: list[str] = []
    d = _aware(job.dispatched_at)
    e = _aware(job.en_route_at)
    if d and e and e > d:
        return max(0, int((e - d).total_seconds() // 60)), warnings
    if d or e:
        warnings.append("travel_timestamps_incomplete")
    return 0, warnings


def _timesheet_approval_warnings(db: Session, sessions: list[tuple[str, datetime, datetime]]) -> list[str]:
    warnings: list[str] = []
    keys = {(uid, utc_date_str(t0)) for uid, t0, _t1 in sessions}
    for uid, d in keys:
        ta = (
            db.query(TimesheetApproval)
            .filter(
                TimesheetApproval.user_id == uid,
                TimesheetApproval.date_str == d,
                TimesheetApproval.status == "approved",
            )
            .first()
        )
        if not ta:
            warnings.append(f"timesheet_not_approved_for_day:{uid}:{d}")
    return warnings


def _accumulate_rules_path(
    *,
    sessions: list[tuple[str, datetime, datetime]],
    resolved: ResolvedLabourRules,
    rs: LabourRuleSet,
    profile: _ProfileLike,
) -> tuple[int, int, int, int, list[dict[str, Any]]]:
    """Returns reg_m, ot_m, dt_m, ooh_m and day attribution rows."""
    tz = resolved.tz
    ws = int(rs.normal_workday_start_minutes)
    we = int(rs.normal_workday_end_minutes)
    ot_threshold = (
        rs.overtime_threshold_minutes
        if rs.overtime_threshold_minutes is not None
        else profile.overtime_threshold_minutes_per_day
    )
    dt_threshold = (
        rs.doubletime_threshold_minutes
        if rs.doubletime_threshold_minutes is not None
        else profile.doubletime_threshold_minutes_per_day
    )
    threshold_only = rs.out_of_hours_policy == "threshold_only"
    weekend_pol = rs.weekend_policy
    cal_days = resolved.calendar_days_by_date

    by_user_day: dict[tuple[str, str], int] = defaultdict(int)
    dt_m = ooh_m = 0
    day_rows: list[dict[str, Any]] = []

    for user_id, t0, t1 in sessions:
        for u0, u1 in _split_segment_at_local_midnight(t0, t1, tz):
            if u0 >= u1:
                continue
            local_d = u0.astimezone(tz).date()
            total_m = max(0, int((u1 - u0).total_seconds() // 60))
            if total_m == 0:
                continue
            treat, meta = segment_treatment_for_local_date(
                local_d=local_d,
                calendar_days=cal_days,
                weekend_policy=weekend_pol,
                holiday_public_policy=rs.holiday_public_policy,
                holiday_company_policy=rs.holiday_company_policy,
                special_workday_uses_normal=rs.special_workday_uses_normal_rates,
                profile_weekend_doubletime=profile.weekend_uses_doubletime_rate,
            )
            meta["treatment"] = treat
            meta["minutes"] = total_m
            day_rows.append(meta)

            key = (user_id, local_d.isoformat())
            if treat == "doubletime":
                dt_m += total_m
            elif treat == "out_of_hours":
                ooh_m += total_m
            else:
                if threshold_only:
                    by_user_day[key] += total_m
                else:
                    iw, oh = _ooh_minutes_in_segment_local(u0, u1, ws, we, tz)
                    ooh_m += oh
                    by_user_day[key] += iw

    reg_m = ot_m = 0
    for _key, iw in by_user_day.items():
        if iw <= 0:
            continue
        if ot_threshold is None:
            reg_m += iw
            continue
        reg_take = min(iw, ot_threshold)
        reg_m += reg_take
        rem = max(0, iw - reg_take)
        if rem <= 0:
            continue
        if dt_threshold is not None and dt_threshold > ot_threshold:
            ot_band = dt_threshold - ot_threshold
            ot_take = min(rem, ot_band)
            ot_m += ot_take
            dt_m += max(0, rem - ot_take)
        else:
            ot_m += rem

    return reg_m, ot_m, dt_m, ooh_m, day_rows


def _accumulate_legacy_path(
    *,
    sessions: list[tuple[str, datetime, datetime]],
    profile: _ProfileLike,
) -> tuple[int, int, int, int]:
    ws, we = profile.work_window_start_minutes_utc, profile.work_window_end_minutes_utc
    ot_threshold = profile.overtime_threshold_minutes_per_day
    dt_threshold = profile.doubletime_threshold_minutes_per_day

    by_user_day: dict[tuple[str, str], dict[str, int]] = {}
    for user_id, t0, t1 in sessions:
        for seg0, seg1 in _split_segment_at_midnight(t0, t1):
            day_key = utc_date_str(seg0)
            seg_a = _aware(seg0)
            wk = seg_a.weekday() if seg_a else 0
            is_weekend = wk >= 5
            total_m = max(0, int((seg1 - seg0).total_seconds() // 60))
            if total_m == 0:
                continue
            key = (user_id, day_key)
            if key not in by_user_day:
                by_user_day[key] = {"in_window": 0, "ooh": 0, "weekend": 0}
            if is_weekend and profile.weekend_uses_doubletime_rate:
                by_user_day[key]["weekend"] += total_m
            else:
                iw, ooh = _ooh_minutes_in_segment(seg0, seg1, ws, we)
                by_user_day[key]["in_window"] += iw
                by_user_day[key]["ooh"] += ooh

    reg_m = ot_m = dt_m = ooh_m = 0
    for _key, buckets in by_user_day.items():
        wend = buckets["weekend"]
        if wend > 0:
            dt_m += wend
            continue
        iw = buckets["in_window"]
        ooh = buckets["ooh"]
        ooh_m += ooh
        if ot_threshold is None:
            reg_m += iw
            continue
        reg_take = min(iw, ot_threshold)
        reg_m += reg_take
        rem = max(0, iw - reg_take)
        if rem <= 0:
            continue
        if dt_threshold is not None and dt_threshold > ot_threshold:
            ot_band = dt_threshold - ot_threshold
            ot_take = min(rem, ot_band)
            ot_m += ot_take
            dt_m += max(0, rem - ot_take)
        else:
            ot_m += rem
    return reg_m, ot_m, dt_m, ooh_m


def compute_job_labour_costing(db: Session, *, job_id: str) -> dict[str, Any]:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    resolved = resolve_labour_rules_for_job(db, job)
    profile, res_warnings = resolve_labour_rate_profile_with_ruleset(db, job, resolved.rule_set)
    warnings = list(res_warnings) + list(resolved.warnings)

    min_bill = profile.minimum_billable_minutes
    if resolved.rule_set and resolved.rule_set.minimum_billable_minutes is not None:
        min_bill = resolved.rule_set.minimum_billable_minutes

    basis: dict[str, Any] = {
        "profile_id": getattr(profile, "id", None),
        "profile_name": profile.name,
        "source": "labour_rate_profile" if isinstance(profile, LabourRateProfile) else "env_fallback",
        "overtime_threshold_minutes_per_day": profile.overtime_threshold_minutes_per_day,
        "doubletime_threshold_configured": profile.doubletime_threshold_minutes_per_day is not None,
        "work_window_utc_configured": profile.work_window_start_minutes_utc is not None
        and profile.work_window_end_minutes_utc is not None,
        "labour_rules": resolved.to_attribution_dict(),
    }

    sessions = _gather_punch_sessions(db, job_id=job_id)
    if not sessions:
        warnings.append("no_punch_sessions_for_job")
        return {
            "regular_minutes": 0,
            "overtime_minutes": 0,
            "doubletime_minutes": 0,
            "travel_minutes": 0,
            "out_of_hours_minutes": 0,
            "break_minutes_excluded": 0,
            "regular_cost": 0.0,
            "overtime_cost": 0.0,
            "doubletime_cost": 0.0,
            "travel_cost": 0.0,
            "out_of_hours_cost": 0.0,
            "labour_cost_total": 0.0,
            "labour_minutes_total": 0,
            "labour_seconds": 0,
            "labour_rate_profile_id": getattr(profile, "id", None),
            "labour_rate_profile_name": profile.name,
            "labour_completeness_status": "unavailable",
            "warnings": warnings,
            "calculation_basis": basis,
            "labour_hours": 0.0,
            "labour_cost_breakdown": {},
            "labour_rules_attribution": resolved.to_attribution_dict()
            | {
                "local_day_segments": [],
                "holiday_applied_any": False,
                "weekend_applied_any": False,
            },
            "rules_completeness_status": resolved.rules_completeness_status,
        }

    warnings.extend(_timesheet_approval_warnings(db, sessions))

    ot_threshold = profile.overtime_threshold_minutes_per_day
    dt_threshold = profile.doubletime_threshold_minutes_per_day
    if resolved.rule_set:
        if resolved.rule_set.overtime_threshold_minutes is not None:
            ot_threshold = resolved.rule_set.overtime_threshold_minutes
        if resolved.rule_set.doubletime_threshold_minutes is not None:
            dt_threshold = resolved.rule_set.doubletime_threshold_minutes
        basis["overtime_threshold_effective"] = ot_threshold
        basis["doubletime_threshold_effective"] = dt_threshold
        basis["work_window_mode"] = "local_labour_rule_set"
    else:
        basis["work_window_mode"] = "legacy_utc_profile"

    if ot_threshold is None:
        warnings.append("overtime_threshold_not_configured:using_base_rate_only_for_all_work_minutes")
    if profile.doubletime_hourly_rate and dt_threshold is None:
        warnings.append("doubletime_rate_set_but_threshold_missing:doubletime_bucket_not_applied")

    day_attribution: list[dict[str, Any]] = []
    if resolved.rule_set:
        reg_m, ot_m, dt_m, ooh_m, day_attribution = _accumulate_rules_path(
            sessions=sessions, resolved=resolved, rs=resolved.rule_set, profile=profile
        )
    else:
        reg_m, ot_m, dt_m, ooh_m = _accumulate_legacy_path(sessions=sessions, profile=profile)

    travel_minutes, tw = _travel_minutes_from_job(job)
    warnings.extend(tw)
    if profile.travel_costing_enabled and travel_minutes > 0 and profile.travel_hourly_rate is None:
        warnings.append("travel_time_present_but_travel_hourly_rate_not_configured")

    work_minutes_pre_min = reg_m + ot_m + dt_m + ooh_m
    if min_bill and work_minutes_pre_min > 0 and work_minutes_pre_min < min_bill:
        delta = min_bill - work_minutes_pre_min
        reg_m += delta
        warnings.append(f"minimum_billable_minutes_applied:+{delta}m_to_regular_bucket")
        work_minutes_pre_min = reg_m + ot_m + dt_m + ooh_m

    base = float(profile.base_hourly_rate)
    rate_ot = float(profile.overtime_hourly_rate) if profile.overtime_hourly_rate is not None else None
    rate_dt = float(profile.doubletime_hourly_rate) if profile.doubletime_hourly_rate is not None else None
    rate_ooh = float(profile.out_of_hours_hourly_rate) if profile.out_of_hours_hourly_rate is not None else None
    rate_travel = float(profile.travel_hourly_rate) if profile.travel_hourly_rate is not None else None

    reg_cost = round((reg_m / 60.0) * base, 4)
    if rate_ot is None and ot_m > 0:
        warnings.append("overtime_minutes_unpriced:using_base_rate")
        ot_cost = round((ot_m / 60.0) * base, 4)
    else:
        ot_cost = round((ot_m / 60.0) * (rate_ot or base), 4)

    if dt_m > 0:
        if rate_dt is None:
            warnings.append("doubletime_minutes_unpriced:using_base_rate")
            dt_cost = round((dt_m / 60.0) * base, 4)
        else:
            dt_cost = round((dt_m / 60.0) * rate_dt, 4)
    else:
        dt_cost = 0.0

    if ooh_m > 0:
        if rate_ooh is None:
            warnings.append("out_of_hours_minutes_used_base_rate")
            ooh_cost = round((ooh_m / 60.0) * base, 4)
        else:
            ooh_cost = round((ooh_m / 60.0) * rate_ooh, 4)
    else:
        ooh_cost = 0.0

    if profile.travel_costing_enabled and travel_minutes > 0:
        if rate_travel is None:
            travel_cost = 0.0
        else:
            travel_cost = round((travel_minutes / 60.0) * rate_travel, 4)
    else:
        travel_cost = 0.0
        if travel_minutes > 0 and not profile.travel_costing_enabled:
            warnings.append("travel_costing_disabled_on_profile")

    labour_work_total = round(reg_cost + ot_cost + dt_cost + ooh_cost, 4)
    labour_seconds = int((reg_m + ot_m + dt_m + ooh_m) * 60)

    def _warn_affects_completeness(w: str) -> bool:
        # Informational: legacy path is still valid; regional rules are optional until configured.
        if w.startswith("no_labour_rule_set_configured"):
            return False
        return True

    sig_warnings = [w for w in warnings if _warn_affects_completeness(w)]
    completeness = "complete"
    if sig_warnings:
        if any("no_punch" in w or "unavailable" in w for w in sig_warnings):
            completeness = "unavailable"
        elif any("not_approved" in w or "incomplete" in w or "not_configured" in w for w in sig_warnings):
            completeness = "partial"
        else:
            completeness = "partial"
    if isinstance(profile, _FallbackProfile) and completeness != "unavailable":
        completeness = "fallback"
    if resolved.rule_set is not None:
        if resolved.rules_completeness_status == "fallback":
            completeness = "fallback"
        elif resolved.rules_completeness_status == "partial" and completeness == "complete":
            completeness = "partial"

    rules_attr = resolved.to_attribution_dict()
    rules_attr["local_day_segments"] = day_attribution
    rules_attr["holiday_applied_any"] = any(x.get("holiday_applied") for x in day_attribution)
    rules_attr["weekend_applied_any"] = any(x.get("weekend_applied") for x in day_attribution)

    pid = profile.id if isinstance(profile, LabourRateProfile) else None
    lm_total = reg_m + ot_m + dt_m + ooh_m
    out: dict[str, Any] = {
        "regular_minutes": reg_m,
        "overtime_minutes": ot_m,
        "doubletime_minutes": dt_m,
        "travel_minutes": travel_minutes,
        "out_of_hours_minutes": ooh_m,
        "break_minutes_excluded": 0,
        "regular_cost": reg_cost,
        "overtime_cost": ot_cost,
        "doubletime_cost": dt_cost,
        "travel_cost": travel_cost,
        "out_of_hours_cost": ooh_cost,
        "labour_cost_total": labour_work_total,
        "labour_minutes_total": lm_total,
        "labour_seconds": labour_seconds,
        "labour_rate_profile_id": pid,
        "labour_rate_profile_name": profile.name,
        "labour_completeness_status": completeness,
        "warnings": warnings,
        "calculation_basis": basis,
        "labour_hours": round(lm_total / 60.0, 4) if lm_total else 0.0,
        "labour_cost_breakdown": {
            "regular_minutes": reg_m,
            "overtime_minutes": ot_m,
            "doubletime_minutes": dt_m,
            "travel_minutes": travel_minutes,
            "out_of_hours_minutes": ooh_m,
            "regular_cost": reg_cost,
            "overtime_cost": ot_cost,
            "doubletime_cost": dt_cost,
            "travel_cost": travel_cost,
            "out_of_hours_cost": ooh_cost,
            "labour_work_cost": labour_work_total,
            "labour_plus_travel_cost": round(labour_work_total + travel_cost, 4),
        },
        "labour_rules_attribution": rules_attr,
        "rules_completeness_status": resolved.rules_completeness_status,
    }
    return out


def labour_costing_for_contract_jobs(
    db: Session, *, contract_id: str, job_ids: list[str]
) -> dict[str, Any]:
    if not job_ids:
        return {
            "labour_work_cost": 0.0,
            "travel_cost": 0.0,
            "labour_plus_travel_cost": 0.0,
            "labour_completeness_worst": "unavailable",
            "warnings": [],
            "jobs_considered": 0,
        }
    total_work = 0.0
    total_travel = 0.0
    worst = "complete"
    rank = {"complete": 0, "partial": 1, "fallback": 2, "unavailable": 3}
    all_w: list[str] = []
    for jid in job_ids:
        row = compute_job_labour_costing(db, job_id=jid)
        total_work += float(row["labour_cost_total"])
        total_travel += float(row["travel_cost"])
        st = str(row["labour_completeness_status"])
        if rank.get(st, 1) > rank.get(worst, 0):
            worst = st
        all_w.extend(row.get("warnings", []))
    return {
        "labour_work_cost": round(total_work, 4),
        "travel_cost": round(total_travel, 4),
        "labour_plus_travel_cost": round(total_work + total_travel, 4),
        "labour_completeness_worst": worst,
        "warnings": list(dict.fromkeys(all_w))[:50],
        "jobs_considered": len(job_ids),
    }
