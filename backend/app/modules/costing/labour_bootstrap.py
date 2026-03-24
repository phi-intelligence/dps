"""Seed default labour rate profile when the database is empty."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.costing.models import LabourRateProfile


def ensure_default_labour_profile(db: Session) -> None:
    if db.query(LabourRateProfile).first():
        return
    base = float(settings.PHI_DPS_LABOUR_HOURLY_RATE)
    mult = float(settings.PHI_DPS_OVERTIME_MULTIPLIER)
    p = LabourRateProfile(
        name="Default",
        active=True,
        base_hourly_rate=base,
        overtime_hourly_rate=round(base * mult, 4),
        doubletime_hourly_rate=None,
        travel_hourly_rate=None,
        out_of_hours_hourly_rate=None,
        minimum_billable_minutes=None,
        default_profile=True,
        applies_to_role_name=None,
        applies_to_engineer_id=None,
        applies_to_contract_id=None,
        notes="Bootstrap profile; replace with contract/engineer-specific profiles in production.",
        work_window_start_minutes_utc=9 * 60,
        work_window_end_minutes_utc=17 * 60,
        overtime_threshold_minutes_per_day=480,
        doubletime_threshold_minutes_per_day=None,
        weekend_uses_doubletime_rate=False,
        travel_costing_enabled=True,
        holiday_placeholder_json="[]",
    )
    db.add(p)
    db.commit()
