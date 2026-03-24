from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.services.authorization_policy import CAN_OVERRIDE_EQUIPMENT_BLOCK
from backend.app.services.authorization_service import require_permission_http
from backend.app.services.break_glass_audit_service import (
    MIN_BREAK_GLASS_REASON_LEN,
    record_break_glass_override,
)
from backend.app.modules.auth.models import User
from backend.app.modules.equipment.models import FieldEquipment
from backend.app.modules.equipment.schemas import (
    CalibrationRecordCreateIn,
    CalibrationRecordOut,
    DashboardAttentionOut,
    DashboardCalibrationOut,
    DashboardReadinessOut,
    EquipmentAssignMoveIn,
    EquipmentMovementOut,
    EquipmentReadinessResultOut,
    FieldEquipmentCreateIn,
    FieldEquipmentOut,
    FieldEquipmentPatchIn,
    InspectionRecordCreateIn,
    InspectionRecordOut,
)
from backend.app.modules.equipment.service import (
    add_calibration_record,
    add_inspection_record,
    assign_or_move_equipment,
    build_attention_dashboard,
    build_calibration_dashboard,
    build_readiness_dashboard,
    create_equipment,
    list_equipment,
    list_movements,
    patch_equipment,
)
from backend.app.services.equipment_readiness_service import (
    evaluate_engineer_equipment_readiness,
    evaluate_job_equipment_readiness,
    evaluate_vehicle_equipment_readiness,
    sync_equipment_calibration_status,
)

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("/dashboard/readiness", response_model=DashboardReadinessOut)
def equipment_dashboard_readiness(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> DashboardReadinessOut:
    return DashboardReadinessOut(**build_readiness_dashboard(db))


@router.get("/dashboard/calibration", response_model=DashboardCalibrationOut)
def equipment_dashboard_calibration(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> DashboardCalibrationOut:
    return DashboardCalibrationOut(**build_calibration_dashboard(db))


@router.get("/dashboard/attention", response_model=DashboardAttentionOut)
def equipment_dashboard_attention(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> DashboardAttentionOut:
    return DashboardAttentionOut(**build_attention_dashboard(db))


@router.post("", response_model=FieldEquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment_endpoint(
    payload: FieldEquipmentCreateIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> FieldEquipmentOut:
    try:
        return create_equipment(db, payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[FieldEquipmentOut])
def list_equipment_endpoint(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    assigned_engineer_id: str | None = Query(default=None),
    assigned_vehicle_id: str | None = Query(default=None),
    calibration_status: str | None = Query(default=None),
    equipment_type: str | None = Query(default=None),
    inspection_due: bool = Query(default=False, description="If true, filter rows with inspection due within configured window"),
    service_due: bool = Query(default=False, description="If true, filter rows with service due within configured window"),
    limit: int = Query(default=200, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> list[FieldEquipmentOut]:
    from backend.app.modules.equipment.service import list_equipment_needing_inspection, list_equipment_needing_service

    if inspection_due:
        rows = list_equipment_needing_inspection(db)
    elif service_due:
        rows = list_equipment_needing_service(db)
    else:
        rows = list_equipment(
            db,
            status=status,
            category=category,
            assigned_engineer_id=assigned_engineer_id,
            assigned_vehicle_id=assigned_vehicle_id,
            calibration_status=calibration_status,
            equipment_type=equipment_type,
            limit=limit,
            offset=offset,
        )
    out: list[FieldEquipmentOut] = []
    for eq in rows:
        sync_equipment_calibration_status(db, eq)
    db.commit()
    for eq in rows:
        db.refresh(eq)
        out.append(FieldEquipmentOut.model_validate(eq))
    return out


@router.get("/engineers/{engineer_id}/readiness-summary")
def engineer_equipment_readiness_endpoint(
    engineer_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    return evaluate_engineer_equipment_readiness(db, engineer_id=engineer_id).to_dict()


@router.get("/vehicles/{vehicle_id}/readiness-summary")
def vehicle_equipment_readiness_endpoint(
    vehicle_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> dict:
    return evaluate_vehicle_equipment_readiness(db, vehicle_id=vehicle_id).to_dict()


@router.get("/{equipment_id}/movements", response_model=list[EquipmentMovementOut])
def list_equipment_movements(
    equipment_id: str,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> list[EquipmentMovementOut]:
    if not db.get(FieldEquipment, equipment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return list_movements(db, equipment_id=equipment_id, limit=limit)


@router.post("/{equipment_id}/calibration-records", response_model=CalibrationRecordOut, status_code=status.HTTP_201_CREATED)
def post_calibration_record(
    equipment_id: str,
    payload: CalibrationRecordCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> CalibrationRecordOut:
    try:
        return add_calibration_record(
            db,
            equipment_id=equipment_id,
            performed_at=payload.performed_at,
            next_due_date=payload.next_due_date,
            certificate_document_id=payload.certificate_document_id,
            notes=payload.notes,
            performed_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{equipment_id}/inspection-records", response_model=InspectionRecordOut, status_code=status.HTTP_201_CREATED)
def post_inspection_record(
    equipment_id: str,
    payload: InspectionRecordCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> InspectionRecordOut:
    try:
        return add_inspection_record(
            db,
            equipment_id=equipment_id,
            performed_at=payload.performed_at,
            next_inspection_due_date=payload.next_inspection_due_date,
            next_service_due_date=payload.next_service_due_date,
            certificate_document_id=payload.certificate_document_id,
            notes=payload.notes,
            performed_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{equipment_id}/assign", response_model=FieldEquipmentOut)
def assign_equipment_endpoint(
    equipment_id: str,
    payload: EquipmentAssignMoveIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Ops_Manager")),
) -> FieldEquipmentOut:
    eq = db.get(FieldEquipment, equipment_id)
    if not eq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    sync_equipment_calibration_status(db, eq)
    db.flush()
    cal_expired = (eq.calibration_status or "") == "expired"
    notes_for_audit = (payload.notes or "").strip()
    if cal_expired:
        require_permission_http(current_user, CAN_OVERRIDE_EQUIPMENT_BLOCK, db=db)
        if len(notes_for_audit) < MIN_BREAK_GLASS_REASON_LEN:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Notes must be at least {MIN_BREAK_GLASS_REASON_LEN} characters "
                    "when assigning equipment with expired calibration (break-glass audit)."
                ),
            )
    try:
        out = assign_or_move_equipment(
            db,
            equipment_id=equipment_id,
            target=payload.target,
            target_id=payload.target_id,
            performed_by_user_id=current_user.id,
            notes=payload.notes,
        )
        if cal_expired:
            record_break_glass_override(
                db,
                actor_user_id=current_user.id,
                override_kind="equipment_expired_calibration_assign",
                target_type="field_equipment",
                target_id=equipment_id,
                reason=notes_for_audit,
                metadata={
                    "target": payload.target,
                    "target_id": payload.target_id,
                },
                commit=True,
            )
        return FieldEquipmentOut.model_validate(out)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{equipment_id}/move", response_model=FieldEquipmentOut)
def move_equipment_endpoint(
    equipment_id: str,
    payload: EquipmentAssignMoveIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> FieldEquipmentOut:
    try:
        return assign_or_move_equipment(
            db,
            equipment_id=equipment_id,
            target=payload.target,
            target_id=payload.target_id,
            performed_by_user_id=current_user.id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{equipment_id}", response_model=FieldEquipmentOut)
def get_equipment_endpoint(
    equipment_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> FieldEquipmentOut:
    row = db.get(FieldEquipment, equipment_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    sync_equipment_calibration_status(db, row)
    db.commit()
    db.refresh(row)
    return FieldEquipmentOut.model_validate(row)


@router.patch("/{equipment_id}", response_model=FieldEquipmentOut)
def patch_equipment_endpoint(
    equipment_id: str,
    payload: FieldEquipmentPatchIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> FieldEquipmentOut:
    try:
        return patch_equipment(db, equipment_id=equipment_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

