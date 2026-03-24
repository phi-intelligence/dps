from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.dispatch.models import Job
from backend.app.modules.equipment.models import (
    EquipmentCalibrationRecord,
    EquipmentInspectionRecord,
    EquipmentMovement,
    FieldEquipment,
    JobEquipmentRequirement,
)
from backend.app.modules.equipment.schemas import (
    FieldEquipmentCreateIn,
    FieldEquipmentPatchIn,
    JobEquipmentRequirementCreateIn,
)
from backend.app.services.equipment_readiness_service import (
    compute_calibration_status,
    count_jobs_blocked_by_equipment,
    evaluate_job_equipment_readiness,
    sync_equipment_calibration_status,
    utc_now,
)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def create_equipment(db: Session, payload: FieldEquipmentCreateIn) -> FieldEquipment:
    row = FieldEquipment(
        id=str(uuid.uuid4()),
        equipment_code=payload.equipment_code.strip(),
        name=payload.name.strip(),
        equipment_type=payload.equipment_type.strip(),
        category=(payload.category or "general").strip(),
        manufacturer=payload.manufacturer,
        model=payload.model,
        serial_number=payload.serial_number,
        status=payload.status,
        ownership_type=payload.ownership_type,
        current_location_type=payload.current_location_type,
        current_location_id=payload.current_location_id,
        assigned_engineer_id=payload.assigned_engineer_id,
        assigned_vehicle_id=payload.assigned_vehicle_id,
        assigned_site_id=payload.assigned_site_id,
        purchase_date=_aware(payload.purchase_date),
        warranty_expiry=_aware(payload.warranty_expiry),
        service_due_date=_aware(payload.service_due_date),
        inspection_due_date=_aware(payload.inspection_due_date),
        calibration_required=bool(payload.calibration_required),
        calibration_due_date=_aware(payload.calibration_due_date),
        notes=payload.notes,
        metadata_json=payload.metadata_json,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    row.calibration_status = compute_calibration_status(row)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def patch_equipment(db: Session, *, equipment_id: str, payload: FieldEquipmentPatchIn) -> FieldEquipment:
    row = db.get(FieldEquipment, equipment_id)
    if not row:
        raise ValueError("Equipment not found")
    data = payload.model_dump(exclude_unset=True)
    prev_status = row.status
    for k, v in data.items():
        if k in {"service_due_date", "inspection_due_date", "calibration_due_date"}:
            v = _aware(v)
        setattr(row, k, v)
    row.updated_at = utc_now()
    if row.calibration_required or row.calibration_due_date is not None:
        row.calibration_status = compute_calibration_status(row)
    else:
        row.calibration_status = "not_required"
    db.add(row)
    if "status" in data and data["status"] != prev_status:
        mov = EquipmentMovement(
            id=str(uuid.uuid4()),
            equipment_id=row.id,
            movement_type="status_change",
            prev_status=prev_status,
            new_status=row.status,
            assigned_engineer_id_after=row.assigned_engineer_id,
            assigned_vehicle_id_after=row.assigned_vehicle_id,
            assigned_site_id_after=row.assigned_site_id,
            notes="Metadata/status patch",
            created_at=utc_now(),
        )
        db.add(mov)
    db.commit()
    db.refresh(row)
    return row


def list_equipment(
    db: Session,
    *,
    status: str | None = None,
    category: str | None = None,
    assigned_engineer_id: str | None = None,
    assigned_vehicle_id: str | None = None,
    calibration_status: str | None = None,
    equipment_type: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[FieldEquipment]:
    q = db.query(FieldEquipment).order_by(FieldEquipment.equipment_code.asc())
    if status:
        q = q.filter(FieldEquipment.status == status)
    if category:
        q = q.filter(FieldEquipment.category == category)
    if assigned_engineer_id:
        q = q.filter(FieldEquipment.assigned_engineer_id == assigned_engineer_id)
    if assigned_vehicle_id:
        q = q.filter(FieldEquipment.assigned_vehicle_id == assigned_vehicle_id)
    if calibration_status:
        q = q.filter(FieldEquipment.calibration_status == calibration_status)
    if equipment_type:
        q = q.filter(FieldEquipment.equipment_type == equipment_type)
    return q.offset(offset).limit(limit).all()


def list_equipment_needing_inspection(db: Session, *, within_days: int = 30) -> list[FieldEquipment]:
    now = utc_now()
    until = now + timedelta(days=within_days)
    return (
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.inspection_due_date.isnot(None),
            FieldEquipment.inspection_due_date <= until,
        )
        .order_by(FieldEquipment.inspection_due_date.asc())
        .limit(500)
        .all()
    )


def list_equipment_needing_service(db: Session, *, within_days: int = 30) -> list[FieldEquipment]:
    now = utc_now()
    until = now + timedelta(days=within_days)
    return (
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.service_due_date.isnot(None),
            FieldEquipment.service_due_date <= until,
        )
        .order_by(FieldEquipment.service_due_date.asc())
        .limit(500)
        .all()
    )


def append_movement(
    db: Session,
    *,
    equipment: FieldEquipment,
    movement_type: str,
    prev_loc_t: str | None,
    prev_loc_id: str | None,
    new_loc_t: str | None,
    new_loc_id: str | None,
    prev_status: str | None,
    new_status: str | None,
    performed_by_user_id: str | None,
    notes: str | None,
) -> EquipmentMovement:
    mov = EquipmentMovement(
        id=str(uuid.uuid4()),
        equipment_id=equipment.id,
        movement_type=movement_type,
        prev_location_type=prev_loc_t,
        prev_location_id=prev_loc_id,
        new_location_type=new_loc_t,
        new_location_id=new_loc_id,
        prev_status=prev_status,
        new_status=new_status,
        assigned_engineer_id_after=equipment.assigned_engineer_id,
        assigned_vehicle_id_after=equipment.assigned_vehicle_id,
        assigned_site_id_after=equipment.assigned_site_id,
        notes=notes,
        performed_by_user_id=performed_by_user_id,
        created_at=utc_now(),
    )
    db.add(mov)
    return mov


def assign_or_move_equipment(
    db: Session,
    *,
    equipment_id: str,
    target: str,
    target_id: str | None,
    performed_by_user_id: str | None,
    notes: str | None,
) -> FieldEquipment:
    eq = db.get(FieldEquipment, equipment_id)
    if not eq:
        raise ValueError("Equipment not found")

    prev_lt, prev_lid = eq.current_location_type, eq.current_location_id
    prev_st = eq.status

    target = target.strip().lower()
    if target == "engineer":
        if not target_id:
            raise ValueError("target_id (engineer user id) required")
        eq.assigned_engineer_id = target_id
        eq.assigned_vehicle_id = None
        eq.assigned_site_id = None
        eq.current_location_type = "engineer"
        eq.current_location_id = target_id
        eq.status = "assigned"
        mt = "assign_engineer"
    elif target == "vehicle":
        if not target_id:
            raise ValueError("target_id (vehicle id) required")
        eq.assigned_vehicle_id = target_id
        eq.assigned_engineer_id = None
        eq.assigned_site_id = None
        eq.current_location_type = "van"
        eq.current_location_id = target_id
        eq.status = "assigned"
        mt = "assign_vehicle"
    elif target == "warehouse":
        if not target_id:
            raise ValueError("target_id (stock_location id) required")
        eq.assigned_engineer_id = None
        eq.assigned_vehicle_id = None
        eq.assigned_site_id = None
        eq.current_location_type = "warehouse"
        eq.current_location_id = target_id
        eq.status = "available"
        mt = "move_warehouse"
    elif target == "site":
        if not target_id:
            raise ValueError("target_id (site id) required")
        eq.assigned_site_id = target_id
        eq.assigned_engineer_id = None
        eq.assigned_vehicle_id = None
        eq.current_location_type = "site"
        eq.current_location_id = target_id
        eq.status = "assigned"
        mt = "move_site"
    elif target == "workshop":
        eq.assigned_engineer_id = None
        eq.assigned_vehicle_id = None
        eq.assigned_site_id = None
        eq.current_location_type = "workshop"
        eq.current_location_id = target_id or "main"
        eq.status = "under_repair"
        mt = "workshop"
    elif target == "out_of_service":
        eq.status = "out_of_service"
        mt = "out_of_service"
    elif target == "return_from_repair":
        eq.status = "available"
        if not eq.current_location_type or eq.current_location_type == "workshop":
            eq.current_location_type = "warehouse"
            eq.current_location_id = target_id
        mt = "return_from_repair"
    else:
        raise ValueError("Unknown target")

    eq.updated_at = utc_now()
    append_movement(
        db,
        equipment=eq,
        movement_type=mt,
        prev_loc_t=prev_lt,
        prev_loc_id=prev_lid,
        new_loc_t=eq.current_location_type,
        new_loc_id=eq.current_location_id,
        prev_status=prev_st,
        new_status=eq.status,
        performed_by_user_id=performed_by_user_id,
        notes=notes,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


def add_calibration_record(
    db: Session,
    *,
    equipment_id: str,
    performed_at: datetime,
    next_due_date: datetime | None,
    certificate_document_id: str | None,
    notes: str | None,
    performed_by_user_id: str | None,
) -> EquipmentCalibrationRecord:
    eq = db.get(FieldEquipment, equipment_id)
    if not eq:
        raise ValueError("Equipment not found")
    rec = EquipmentCalibrationRecord(
        id=str(uuid.uuid4()),
        equipment_id=equipment_id,
        performed_at=_aware(performed_at) or performed_at,
        next_due_date=_aware(next_due_date),
        certificate_document_id=certificate_document_id,
        notes=notes,
        performed_by_user_id=performed_by_user_id,
        created_at=utc_now(),
    )
    db.add(rec)
    eq.calibration_required = True
    eq.calibration_due_date = _aware(next_due_date)
    sync_equipment_calibration_status(db, eq)
    db.add(eq)
    db.commit()
    db.refresh(rec)
    return rec


def add_inspection_record(
    db: Session,
    *,
    equipment_id: str,
    performed_at: datetime,
    next_inspection_due_date: datetime | None,
    next_service_due_date: datetime | None,
    certificate_document_id: str | None,
    notes: str | None,
    performed_by_user_id: str | None,
) -> EquipmentInspectionRecord:
    eq = db.get(FieldEquipment, equipment_id)
    if not eq:
        raise ValueError("Equipment not found")
    rec = EquipmentInspectionRecord(
        id=str(uuid.uuid4()),
        equipment_id=equipment_id,
        performed_at=_aware(performed_at) or performed_at,
        next_inspection_due_date=_aware(next_inspection_due_date),
        next_service_due_date=_aware(next_service_due_date),
        certificate_document_id=certificate_document_id,
        notes=notes,
        performed_by_user_id=performed_by_user_id,
        created_at=utc_now(),
    )
    db.add(rec)
    if next_inspection_due_date:
        eq.inspection_due_date = _aware(next_inspection_due_date)
    if next_service_due_date:
        eq.service_due_date = _aware(next_service_due_date)
    eq.updated_at = utc_now()
    db.add(eq)
    db.commit()
    db.refresh(rec)
    return rec


def list_movements(db: Session, *, equipment_id: str, limit: int = 100) -> list[EquipmentMovement]:
    return (
        db.query(EquipmentMovement)
        .filter(EquipmentMovement.equipment_id == equipment_id)
        .order_by(EquipmentMovement.created_at.desc())
        .limit(limit)
        .all()
    )


def add_job_requirement(db: Session, *, job_id: str, payload: JobEquipmentRequirementCreateIn) -> JobEquipmentRequirement:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    row = JobEquipmentRequirement(
        id=str(uuid.uuid4()),
        job_id=job_id,
        equipment_type=payload.equipment_type.strip(),
        category=(payload.category or "general").strip(),
        specific_equipment_id=payload.specific_equipment_id,
        calibration_required=bool(payload.calibration_required),
        mandatory=bool(payload.mandatory),
        quantity=max(1, int(payload.quantity)),
        notes=payload.notes,
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_job_requirements(db: Session, *, job_id: str) -> list[JobEquipmentRequirement]:
    return (
        db.query(JobEquipmentRequirement)
        .filter(JobEquipmentRequirement.job_id == job_id)
        .order_by(JobEquipmentRequirement.created_at.asc())
        .all()
    )


def build_readiness_dashboard(db: Session) -> dict[str, Any]:
    def cnt(st: str) -> int:
        return int(db.query(FieldEquipment).filter(FieldEquipment.status == st).count())

    blocked = count_jobs_blocked_by_equipment(db)
    warn_jobs = 0
    risks: list[dict[str, Any]] = []
    window_days = int(getattr(settings, "PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS", 30))
    now = utc_now()
    tomorrow = now + timedelta(days=1)

    for job in (
        db.query(Job)
        .filter(
            Job.status.not_in(["completed", "closed", "cancelled"]),
            Job.assigned_engineer_id.isnot(None),
        )
        .all()
    ):
        if not db.query(JobEquipmentRequirement).filter(JobEquipmentRequirement.job_id == job.id).first():
            continue
        ev = evaluate_job_equipment_readiness(db, job_id=job.id, for_engineer_id=job.assigned_engineer_id)
        if ev.readiness_status == "warning":
            warn_jobs += 1
        if job.scheduled_at and _aware(job.scheduled_at) and _aware(job.scheduled_at) <= tomorrow:
            if ev.readiness_status != "ready":
                risks.append(
                    {
                        "job_id": job.id,
                        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
                        "readiness_status": ev.readiness_status,
                        "blocking_flags": ev.blocking_flags,
                    }
                )

    return {
        "available_count": cnt("available"),
        "assigned_count": cnt("assigned"),
        "in_service_count": cnt("in_service"),
        "under_repair_count": cnt("under_repair"),
        "out_of_service_count": cnt("out_of_service"),
        "lost_count": cnt("lost"),
        "retired_count": cnt("retired"),
        "jobs_blocked_by_equipment": blocked,
        "jobs_with_equipment_warnings": warn_jobs,
        "upcoming_readiness_risks": risks[:50],
    }


def build_calibration_dashboard(db: Session) -> dict[str, Any]:
    now = utc_now()
    window = now + timedelta(days=due_soon_window_days())
    req_total = int(db.query(FieldEquipment).filter(FieldEquipment.calibration_required.is_(True)).count())
    expired = 0
    due_soon = 0
    valid = 0
    for eq in db.query(FieldEquipment).filter(FieldEquipment.calibration_required.is_(True)).all():
        st = compute_calibration_status(eq, now=now)
        if st == "expired":
            expired += 1
        elif st == "due_soon":
            due_soon += 1
        else:
            valid += 1
    insp = (
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.inspection_due_date.isnot(None),
            FieldEquipment.inspection_due_date <= window,
        )
        .count()
    )
    svc = (
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.service_due_date.isnot(None),
            FieldEquipment.service_due_date <= window,
        )
        .count()
    )
    return {
        "calibration_required_total": req_total,
        "calibration_valid": valid,
        "calibration_due_soon": due_soon,
        "calibration_expired": expired,
        "inspection_due_within_window": int(insp),
        "service_due_within_window": int(svc),
    }


def due_soon_window_days() -> int:
    return int(getattr(settings, "PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS", 30))


def build_attention_dashboard(db: Session) -> dict[str, Any]:
    now = utc_now()
    window = now + timedelta(days=due_soon_window_days())
    oos = int(db.query(FieldEquipment).filter(FieldEquipment.status == "out_of_service").count())
    ur = int(db.query(FieldEquipment).filter(FieldEquipment.status == "under_repair").count())
    exp_cal = 0
    due_soon_cal = 0
    for eq in db.query(FieldEquipment).filter(FieldEquipment.calibration_required.is_(True)).all():
        st = compute_calibration_status(eq, now=now)
        if st == "expired":
            exp_cal += 1
        elif st == "due_soon":
            due_soon_cal += 1
    insp_due = int(
        db.query(FieldEquipment)
        .filter(
            FieldEquipment.inspection_due_date.isnot(None),
            FieldEquipment.inspection_due_date <= window,
        )
        .count()
    )

    top: list[dict[str, Any]] = []
    for eq in (
        db.query(FieldEquipment)
        .filter(
            or_(
                FieldEquipment.status.in_(["out_of_service", "under_repair"]),
                FieldEquipment.calibration_required.is_(True),
            )
        )
        .order_by(FieldEquipment.updated_at.desc())
        .limit(80)
        .all()
    ):
        cal_st = compute_calibration_status(eq, now=now) if eq.calibration_required else "not_required"
        if eq.status in ("out_of_service", "under_repair") or cal_st in ("expired", "due_soon"):
            top.append(
                {
                    "equipment_id": eq.id,
                    "equipment_code": eq.equipment_code,
                    "name": eq.name,
                    "status": eq.status,
                    "calibration_status": cal_st,
                    "calibration_due_date": eq.calibration_due_date.isoformat() if eq.calibration_due_date else None,
                }
            )
        if len(top) >= 25:
            break

    return {
        "out_of_service_count": oos,
        "under_repair_count": ur,
        "expired_calibration_count": exp_cal,
        "due_soon_calibration_count": due_soon_cal,
        "inspection_overdue_or_due": insp_due,
        "top_attention_items": top,
    }
