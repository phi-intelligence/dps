"""
Operational equipment readiness (non-consumable tools / test gear).

Not coupled to inventory consumption — see FieldEquipment and job requirements.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.models import Job
from backend.app.modules.equipment.models import FieldEquipment, JobEquipmentRequirement


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


USABLE_STATUSES = frozenset({"available", "assigned", "in_service"})


def due_soon_days() -> int:
    return int(getattr(settings, "PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS", 30))


def compute_calibration_status(equipment: FieldEquipment, *, now: datetime | None = None) -> str:
    now = _aware(now or utc_now()) or utc_now()
    if not equipment.calibration_required:
        return "not_required"
    due = _aware(equipment.calibration_due_date)
    if not due:
        return "valid"
    if due < now:
        return "expired"
    if due <= now + timedelta(days=due_soon_days()):
        return "due_soon"
    return "valid"


def sync_equipment_calibration_status(db: Session, equipment: FieldEquipment, *, now: datetime | None = None) -> None:
    equipment.calibration_status = compute_calibration_status(equipment, now=now)
    equipment.updated_at = utc_now()
    db.add(equipment)


def equipment_usable_for_field(equipment: FieldEquipment) -> bool:
    return equipment.status in USABLE_STATUSES


def equipment_is_with_engineer(db: Session, equipment: FieldEquipment, engineer_id: str) -> bool:
    if equipment.assigned_engineer_id == engineer_id:
        return True
    if equipment.current_location_type == "engineer" and equipment.current_location_id == engineer_id:
        return True
    user = db.get(User, engineer_id)
    van = (user.assigned_vehicle_id or "").strip() if user else ""
    if van and equipment.assigned_vehicle_id == van:
        return True
    if van and equipment.current_location_type == "van" and equipment.current_location_id == van:
        return True
    return False


def _type_matches_requirement(req: JobEquipmentRequirement, eq: FieldEquipment) -> bool:
    if req.specific_equipment_id:
        return eq.id == req.specific_equipment_id
    et = (req.equipment_type or "").strip().lower()
    cat = (req.category or "").strip().lower()
    if et and eq.equipment_type.lower() == et:
        return True
    if et and eq.category.lower() == et:
        return True
    if cat and eq.category.lower() == cat:
        return True
    return False


def _calibration_satisfies_requirement(req: JobEquipmentRequirement, eq: FieldEquipment, *, now: datetime) -> tuple[bool, str | None]:
    if not req.calibration_required:
        return True, None
    if not eq.calibration_required:
        return False, "equipment_not_calibration_capable"
    st = compute_calibration_status(eq, now=now)
    if st == "expired":
        return False, "calibration_expired"
    return True, None


@dataclass
class EquipmentReadinessResult:
    job_id: str
    evaluated_for_engineer_id: str | None
    readiness_status: str  # ready | warning | blocked
    missing_required_equipment: list[dict[str, Any]] = field(default_factory=list)
    expired_required_equipment: list[dict[str, Any]] = field(default_factory=list)
    due_soon_equipment: list[dict[str, Any]] = field(default_factory=list)
    assigned_matching_equipment: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pool_for_engineer(db: Session, engineer_id: str) -> list[FieldEquipment]:
    user = db.get(User, engineer_id)
    van = (user.assigned_vehicle_id or "").strip() if user else ""
    q = db.query(FieldEquipment).filter(
        FieldEquipment.assigned_engineer_id == engineer_id,
    )
    rows = list(q.all())
    rows += (
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.current_location_type == "engineer",
            FieldEquipment.current_location_id == engineer_id,
        )
        .all()
    )
    if van:
        rows += db.query(FieldEquipment).filter(FieldEquipment.assigned_vehicle_id == van).all()
        rows += (
            db.query(FieldEquipment)
            .filter(
                FieldEquipment.current_location_type == "van",
                FieldEquipment.current_location_id == van,
            )
            .all()
        )
    seen: set[str] = set()
    out: list[FieldEquipment] = []
    for r in rows:
        if r.id not in seen:
            seen.add(r.id)
            out.append(r)
    return out


def evaluate_job_equipment_readiness(
    db: Session,
    *,
    job_id: str,
    for_engineer_id: str | None = None,
    now: datetime | None = None,
) -> EquipmentReadinessResult:
    now = _aware(now or utc_now()) or utc_now()
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    engineer_id = for_engineer_id or job.assigned_engineer_id
    reqs = (
        db.query(JobEquipmentRequirement)
        .filter(JobEquipmentRequirement.job_id == job_id)
        .order_by(JobEquipmentRequirement.created_at.asc())
        .all()
    )

    if not reqs:
        return EquipmentReadinessResult(
            job_id=job_id,
            evaluated_for_engineer_id=engineer_id,
            readiness_status="ready",
        )

    if not engineer_id:
        return EquipmentReadinessResult(
            job_id=job_id,
            evaluated_for_engineer_id=None,
            readiness_status="blocked",
            blocking_flags=["no_engineer_context_for_equipment_evaluation"],
            warnings=["Assign an engineer to evaluate equipment readiness for this job."],
        )

    pool = _pool_for_engineer(db, engineer_id)
    missing: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    due_soon: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    warnings: list[str] = []
    blocking: list[str] = []

    for req in reqs:
        candidates = [eq for eq in pool if _type_matches_requirement(req, eq) and equipment_usable_for_field(eq)]
        picked: list[FieldEquipment] = []
        for eq in candidates:
            ok_cal, reason = _calibration_satisfies_requirement(req, eq, now=now)
            if not ok_cal:
                continue
            picked.append(eq)
            if len(picked) >= max(1, int(req.quantity or 1)):
                break

        qty_need = max(1, int(req.quantity or 1))
        if len(picked) < qty_need:
            # distinguish missing vs expired-only
            any_type_match = [eq for eq in pool if _type_matches_requirement(req, eq)]
            cal_blocked = [
                eq
                for eq in any_type_match
                if equipment_usable_for_field(eq) and not _calibration_satisfies_requirement(req, eq, now=now)[0]
            ]
            entry = {
                "requirement_id": req.id,
                "equipment_type": req.equipment_type,
                "category": req.category,
                "quantity_required": qty_need,
                "mandatory": req.mandatory,
                "calibration_required": req.calibration_required,
            }
            if cal_blocked and req.mandatory and req.calibration_required:
                blocking.append(f"calibration_gap:{req.id}")
                for eq in cal_blocked:
                    expired.append(
                        {
                            "requirement_id": req.id,
                            "equipment_id": eq.id,
                            "equipment_code": eq.equipment_code,
                            "reason": _calibration_satisfies_requirement(req, eq, now=now)[1],
                        }
                    )
            elif req.mandatory:
                blocking.append(f"missing_equipment:{req.id}")
                missing.append(entry)
            else:
                warnings.append(f"Optional equipment not satisfied: {req.equipment_type}")
        else:
            for eq in picked:
                matched.append(
                    {
                        "requirement_id": req.id,
                        "equipment_id": eq.id,
                        "equipment_code": eq.equipment_code,
                        "equipment_type": eq.equipment_type,
                        "calibration_status": compute_calibration_status(eq, now=now),
                    }
                )
                st = compute_calibration_status(eq, now=now)
                if req.calibration_required and st == "due_soon":
                    due_soon.append(
                        {
                            "requirement_id": req.id,
                            "equipment_id": eq.id,
                            "equipment_code": eq.equipment_code,
                            "calibration_due_date": eq.calibration_due_date.isoformat() if eq.calibration_due_date else None,
                        }
                    )
                    warnings.append(f"Calibration due soon for {eq.equipment_code}")

    if blocking:
        status = "blocked"
    elif due_soon or warnings:
        status = "warning"
    else:
        status = "ready"

    return EquipmentReadinessResult(
        job_id=job_id,
        evaluated_for_engineer_id=engineer_id,
        readiness_status=status,
        missing_required_equipment=missing,
        expired_required_equipment=expired,
        due_soon_equipment=due_soon,
        assigned_matching_equipment=matched,
        warnings=warnings,
        blocking_flags=blocking,
    )


@dataclass
class EngineerEquipmentReadinessSummary:
    engineer_id: str
    equipment_count: int
    expired_calibration: list[dict[str, Any]]
    due_soon_calibration: list[dict[str, Any]]
    unusable_assigned: list[dict[str, Any]]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_engineer_equipment_readiness(
    db: Session, *, engineer_id: str, now: datetime | None = None
) -> EngineerEquipmentReadinessSummary:
    now = _aware(now or utc_now()) or utc_now()
    pool = _pool_for_engineer(db, engineer_id)
    expired: list[dict[str, Any]] = []
    due_soon: list[dict[str, Any]] = []
    unusable: list[dict[str, Any]] = []
    warnings: list[str] = []
    for eq in pool:
        if not equipment_usable_for_field(eq):
            unusable.append({"equipment_id": eq.id, "equipment_code": eq.equipment_code, "status": eq.status})
            continue
        if eq.calibration_required:
            st = compute_calibration_status(eq, now=now)
            if st == "expired":
                expired.append({"equipment_id": eq.id, "equipment_code": eq.equipment_code})
            elif st == "due_soon":
                due_soon.append(
                    {
                        "equipment_id": eq.id,
                        "equipment_code": eq.equipment_code,
                        "calibration_due_date": eq.calibration_due_date.isoformat() if eq.calibration_due_date else None,
                    }
                )
    if expired:
        warnings.append("One or more assigned devices have expired calibration.")
    return EngineerEquipmentReadinessSummary(
        engineer_id=engineer_id,
        equipment_count=len(pool),
        expired_calibration=expired,
        due_soon_calibration=due_soon,
        unusable_assigned=unusable,
        warnings=warnings,
    )


@dataclass
class VehicleEquipmentReadinessSummary:
    vehicle_id: str
    equipment_count: int
    expired_calibration: list[dict[str, Any]]
    due_soon_calibration: list[dict[str, Any]]
    unusable: list[dict[str, Any]]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_vehicle_equipment_readiness(
    db: Session, *, vehicle_id: str, now: datetime | None = None
) -> VehicleEquipmentReadinessSummary:
    now = _aware(now or utc_now()) or utc_now()
    rows = (
        db.query(FieldEquipment)
        .filter(
            (FieldEquipment.assigned_vehicle_id == vehicle_id)
            | (
                (FieldEquipment.current_location_type == "van")
                & (FieldEquipment.current_location_id == vehicle_id)
            )
        )
        .all()
    )
    expired: list[dict[str, Any]] = []
    due_soon: list[dict[str, Any]] = []
    unusable: list[dict[str, Any]] = []
    warnings: list[str] = []
    for eq in rows:
        if not equipment_usable_for_field(eq):
            unusable.append({"equipment_id": eq.id, "equipment_code": eq.equipment_code, "status": eq.status})
            continue
        if eq.calibration_required:
            st = compute_calibration_status(eq, now=now)
            if st == "expired":
                expired.append({"equipment_id": eq.id, "equipment_code": eq.equipment_code})
            elif st == "due_soon":
                due_soon.append(
                    {
                        "equipment_id": eq.id,
                        "equipment_code": eq.equipment_code,
                        "calibration_due_date": eq.calibration_due_date.isoformat() if eq.calibration_due_date else None,
                    }
                )
    if expired:
        warnings.append("Van carries equipment with expired calibration.")
    return VehicleEquipmentReadinessSummary(
        vehicle_id=vehicle_id,
        equipment_count=len(rows),
        expired_calibration=expired,
        due_soon_calibration=due_soon,
        unusable=unusable,
        warnings=warnings,
    )


def count_jobs_blocked_by_equipment(db: Session, *, now: datetime | None = None) -> int:
    now = _aware(now or utc_now()) or utc_now()
    n = 0
    jobs = (
        db.query(Job)
        .filter(Job.status.not_in(["completed", "closed", "cancelled"]))
        .all()
    )
    for job in jobs:
        if not job.assigned_engineer_id:
            continue
        if not db.query(JobEquipmentRequirement).filter(JobEquipmentRequirement.job_id == job.id).first():
            continue
        ev = evaluate_job_equipment_readiness(
            db, job_id=job.id, for_engineer_id=job.assigned_engineer_id, now=now
        )
        if ev.readiness_status == "blocked":
            n += 1
    return n
