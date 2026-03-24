from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.vehicles.models import VehicleDefect, VehicleInspection, VehicleInspectionItem
from backend.app.modules.vehicles.schemas import (
    VehicleDefectCreateIn,
    VehicleInspectionCreateIn,
)
from backend.app.services.vehicle_readiness_service import derive_overall_status_from_items, utc_now, evaluate_vehicle_readiness


def _performed_at(payload: VehicleInspectionCreateIn) -> datetime:
    if payload.performed_at:
        p = payload.performed_at
        if p.tzinfo is None:
            return p.replace(tzinfo=timezone.utc)
        return p.astimezone(timezone.utc)
    return utc_now()


def _inspection_date(payload: VehicleInspectionCreateIn, performed: datetime) -> date:
    if payload.inspection_date:
        return payload.inspection_date
    return performed.date()


def create_vehicle_inspection(
    db: Session,
    *,
    vehicle_id: str,
    payload: VehicleInspectionCreateIn,
) -> VehicleInspection:
    performed = _performed_at(payload)
    idate = _inspection_date(payload, performed)
    items_payload = [it.model_dump() for it in payload.items]
    overall = payload.overall_status
    if not overall:
        overall = derive_overall_status_from_items(items_payload)
    if overall not in ("passed", "failed_minor", "failed_critical"):
        raise ValueError("overall_status must be passed, failed_minor, or failed_critical")

    row = VehicleInspection(
        id=str(uuid.uuid4()),
        vehicle_id=vehicle_id.strip(),
        engineer_id=payload.engineer_id,
        inspection_date=idate,
        performed_at=performed,
        odometer=payload.odometer,
        latitude=payload.latitude,
        longitude=payload.longitude,
        overall_status=overall,
        notes=payload.notes,
        created_at=utc_now(),
    )
    db.add(row)
    db.flush()

    for it in payload.items:
        db.add(
            VehicleInspectionItem(
                id=str(uuid.uuid4()),
                inspection_id=row.id,
                item_code=it.item_code.strip(),
                item_label=it.item_label.strip(),
                result=it.result.strip().lower(),
                notes=it.notes,
                photo_document_id=it.photo_document_id,
                fail_criticality=it.fail_criticality.strip().lower() if it.result.lower() == "fail" else "minor",
            )
        )

    db.commit()
    db.refresh(row)
    return row


def get_inspection_with_items(db: Session, *, inspection_id: str) -> VehicleInspection | None:
    return db.get(VehicleInspection, inspection_id)


def list_vehicle_inspections(
    db: Session, *, vehicle_id: str, limit: int = 50, offset: int = 0
) -> list[VehicleInspection]:
    return (
        db.query(VehicleInspection)
        .filter(VehicleInspection.vehicle_id == vehicle_id.strip())
        .order_by(desc(VehicleInspection.performed_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def latest_vehicle_inspection(db: Session, *, vehicle_id: str) -> VehicleInspection | None:
    return (
        db.query(VehicleInspection)
        .filter(VehicleInspection.vehicle_id == vehicle_id.strip())
        .order_by(desc(VehicleInspection.performed_at))
        .first()
    )


def inspection_to_out(db: Session, row: VehicleInspection) -> dict[str, Any]:
    items = (
        db.query(VehicleInspectionItem)
        .filter(VehicleInspectionItem.inspection_id == row.id)
        .order_by(VehicleInspectionItem.item_code.asc())
        .all()
    )
    from backend.app.modules.vehicles.schemas import VehicleInspectionItemOut, VehicleInspectionOut

    return VehicleInspectionOut(
        id=row.id,
        vehicle_id=row.vehicle_id,
        engineer_id=row.engineer_id,
        inspection_date=row.inspection_date,
        performed_at=row.performed_at,
        odometer=row.odometer,
        latitude=row.latitude,
        longitude=row.longitude,
        overall_status=row.overall_status,
        notes=row.notes,
        created_at=row.created_at,
        items=[VehicleInspectionItemOut.model_validate(i) for i in items],
    ).model_dump()


def create_defect(
    db: Session,
    *,
    vehicle_id: str,
    payload: VehicleDefectCreateIn,
    reported_by_user_id: str | None,
) -> VehicleDefect:
    row = VehicleDefect(
        id=str(uuid.uuid4()),
        vehicle_id=vehicle_id.strip(),
        inspection_id=payload.inspection_id,
        defect_type=payload.defect_type.strip(),
        severity=payload.severity.strip().lower(),
        title=payload.title.strip(),
        description=payload.description,
        status="open",
        reported_at=utc_now(),
        reported_by_user_id=reported_by_user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_vehicle_defects(
    db: Session, *, vehicle_id: str, status: str | None = None, limit: int = 100
) -> list[VehicleDefect]:
    q = db.query(VehicleDefect).filter(VehicleDefect.vehicle_id == vehicle_id.strip())
    if status:
        q = q.filter(VehicleDefect.status == status)
    return q.order_by(desc(VehicleDefect.reported_at)).limit(limit).all()


def resolve_defect(
    db: Session,
    *,
    vehicle_id: str,
    defect_id: str,
    resolved_by_user_id: str | None,
    resolution_notes: str | None,
) -> VehicleDefect:
    row = db.get(VehicleDefect, defect_id)
    if not row or row.vehicle_id != vehicle_id.strip():
        raise ValueError("Defect not found")
    if row.status == "resolved":
        return row
    row.status = "resolved"
    row.resolved_at = utc_now()
    row.resolved_by_user_id = resolved_by_user_id
    row.resolution_notes = resolution_notes
    db.commit()
    db.refresh(row)
    return row


def build_inspection_attention_dashboard(db: Session) -> dict[str, Any]:
    from backend.app.modules.tracking.models import VehicleLatestLocation

    vehicles: set[str] = set()
    for u in db.query(User).filter(User.assigned_vehicle_id.isnot(None)).all():
        if u.assigned_vehicle_id:
            vehicles.add(u.assigned_vehicle_id.strip())
    for v in db.query(VehicleLatestLocation).all():
        vehicles.add(v.vehicle_id)

    items: list[dict[str, Any]] = []
    for vid in sorted(vehicles):
        r = evaluate_vehicle_readiness(db, vehicle_id=vid)
        if r.readiness_status != "ready":
            items.append(r.to_dict())
    return {"attention_count": len(items), "items": items}
