"""
Vehicle operational readiness from daily inspection + open defects (H&S pre-use).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.modules.vehicles.models import VehicleDefect, VehicleInspection


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_date(dt: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


@dataclass
class VehicleReadinessResult:
    vehicle_id: str
    readiness_status: str  # ready | warning | blocked
    reasons: list[str] = field(default_factory=list)
    blocking_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latest_inspection_id: str | None = None
    latest_inspection_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_vehicle_readiness(
    db: Session,
    *,
    vehicle_id: str,
    now: datetime | None = None,
) -> VehicleReadinessResult:
    """
    - Blocked: open critical defect OR today's inspection overall_status == failed_critical
    - Warning: no inspection completed today OR today's inspection failed_minor
    - Ready: today's inspection passed (and no blocking defects)
    """
    now = now or utc_now()
    today = _utc_date(now)
    vid = vehicle_id.strip()

    open_critical = (
        db.query(VehicleDefect)
        .filter(
            VehicleDefect.vehicle_id == vid,
            VehicleDefect.status == "open",
            VehicleDefect.severity == "critical",
        )
        .first()
    )
    if open_critical:
        return VehicleReadinessResult(
            vehicle_id=vid,
            readiness_status="blocked",
            reasons=["unresolved_critical_defect"],
            blocking_flags=["unresolved_critical_defect"],
            warnings=[],
            latest_inspection_id=None,
            latest_inspection_status=None,
        )

    today_insp = (
        db.query(VehicleInspection)
        .filter(VehicleInspection.vehicle_id == vid, VehicleInspection.inspection_date == today)
        .order_by(desc(VehicleInspection.performed_at))
        .first()
    )

    latest_any = (
        db.query(VehicleInspection)
        .filter(VehicleInspection.vehicle_id == vid)
        .order_by(desc(VehicleInspection.performed_at))
        .first()
    )

    if not today_insp:
        wr = VehicleReadinessResult(
            vehicle_id=vid,
            readiness_status="warning",
            reasons=["no_inspection_today"],
            blocking_flags=[],
            warnings=["No pre-use inspection recorded for this vehicle today (UTC)."],
            latest_inspection_id=latest_any.id if latest_any else None,
            latest_inspection_status=latest_any.overall_status if latest_any else None,
        )
        return wr

    if today_insp.overall_status == "failed_critical":
        return VehicleReadinessResult(
            vehicle_id=vid,
            readiness_status="blocked",
            reasons=["failed_critical_inspection"],
            blocking_flags=["failed_critical_inspection"],
            warnings=[],
            latest_inspection_id=today_insp.id,
            latest_inspection_status=today_insp.overall_status,
        )

    if today_insp.overall_status == "failed_minor":
        return VehicleReadinessResult(
            vehicle_id=vid,
            readiness_status="warning",
            reasons=["failed_minor_inspection"],
            blocking_flags=[],
            warnings=["Today's inspection recorded minor failures — review before heavy use."],
            latest_inspection_id=today_insp.id,
            latest_inspection_status=today_insp.overall_status,
        )

    return VehicleReadinessResult(
        vehicle_id=vid,
        readiness_status="ready",
        reasons=[],
        blocking_flags=[],
        warnings=[],
        latest_inspection_id=today_insp.id,
        latest_inspection_status=today_insp.overall_status,
    )


def derive_overall_status_from_items(
    items: list[dict[str, Any]],
) -> str:
    """Derive overall_status from line items when not explicitly supplied."""
    has_fail_critical = False
    has_fail_minor = False
    has_advisory = False
    for it in items:
        r = str(it.get("result", "")).lower()
        if r == "fail":
            crit = str(it.get("fail_criticality", "minor")).lower()
            if crit == "critical":
                has_fail_critical = True
            else:
                has_fail_minor = True
        elif r == "advisory":
            has_advisory = True
    if has_fail_critical:
        return "failed_critical"
    if has_fail_minor:
        return "failed_minor"
    if has_advisory:
        return "passed"
    return "passed"
