from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.vehicles.models import VehicleDefect
from backend.app.services.authorization_policy import CAN_OVERRIDE_VEHICLE_BLOCK
from backend.app.services.authorization_service import require_permission_http
from backend.app.services.break_glass_audit_service import (
    MIN_BREAK_GLASS_REASON_LEN,
    record_break_glass_override,
)
from backend.app.modules.auth.models import User
from backend.app.modules.vehicles.schemas import (
    InspectionAttentionDashboardOut,
    VehicleDefectCreateIn,
    VehicleDefectOut,
    VehicleDefectResolveIn,
    VehicleInspectionCreateIn,
    VehicleInspectionOut,
)
from backend.app.modules.vehicles.service import (
    build_inspection_attention_dashboard,
    create_defect,
    create_vehicle_inspection,
    inspection_to_out,
    latest_vehicle_inspection,
    list_vehicle_defects,
    list_vehicle_inspections,
    resolve_defect,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _roles(u: User) -> set[str]:
    return set(u.role_names())


def _ensure_vehicle_access(*, user: User, vehicle_id: str, write: bool) -> None:
    r = _roles(user)
    if "Admin" in r or "Dispatcher" in r:
        return
    if "Engineer" in r:
        if (user.assigned_vehicle_id or "").strip() == vehicle_id.strip():
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your assigned vehicle")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


@router.get("/dashboard/inspection-attention", response_model=InspectionAttentionDashboardOut)
def inspection_attention_dashboard(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> InspectionAttentionDashboardOut:
    return InspectionAttentionDashboardOut(**build_inspection_attention_dashboard(db))


@router.post("/{vehicle_id}/inspections", response_model=VehicleInspectionOut, status_code=status.HTTP_201_CREATED)
def post_vehicle_inspection(
    vehicle_id: str,
    payload: VehicleInspectionCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> VehicleInspectionOut:
    _ensure_vehicle_access(user=current_user, vehicle_id=vehicle_id, write=True)
    if "Engineer" in _roles(current_user) and "Admin" not in _roles(current_user) and "Dispatcher" not in _roles(current_user):
        if payload.engineer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="engineer_id must match current user")
    try:
        row = create_vehicle_inspection(db, vehicle_id=vehicle_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return VehicleInspectionOut(**inspection_to_out(db, row))


@router.get("/{vehicle_id}/inspections", response_model=list[VehicleInspectionOut])
def list_inspections_endpoint(
    vehicle_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> list[VehicleInspectionOut]:
    _ensure_vehicle_access(user=current_user, vehicle_id=vehicle_id, write=False)
    rows = list_vehicle_inspections(db, vehicle_id=vehicle_id, limit=limit, offset=offset)
    return [VehicleInspectionOut(**inspection_to_out(db, r)) for r in rows]


@router.get("/{vehicle_id}/inspections/latest", response_model=VehicleInspectionOut)
def latest_inspection_endpoint(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> VehicleInspectionOut:
    _ensure_vehicle_access(user=current_user, vehicle_id=vehicle_id, write=False)
    row = latest_vehicle_inspection(db, vehicle_id=vehicle_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inspections for this vehicle")
    return VehicleInspectionOut(**inspection_to_out(db, row))


@router.post("/{vehicle_id}/defects", response_model=VehicleDefectOut, status_code=status.HTTP_201_CREATED)
def post_vehicle_defect(
    vehicle_id: str,
    payload: VehicleDefectCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> VehicleDefectOut:
    _ensure_vehicle_access(user=current_user, vehicle_id=vehicle_id, write=True)
    try:
        return create_defect(
            db,
            vehicle_id=vehicle_id,
            payload=payload,
            reported_by_user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{vehicle_id}/defects", response_model=list[VehicleDefectOut])
def list_defects_endpoint(
    vehicle_id: str,
    defect_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> list[VehicleDefectOut]:
    _ensure_vehicle_access(user=current_user, vehicle_id=vehicle_id, write=False)
    rows = list_vehicle_defects(db, vehicle_id=vehicle_id, status=defect_status)
    return [VehicleDefectOut.model_validate(r) for r in rows]


@router.post("/{vehicle_id}/defects/{defect_id}/resolve", response_model=VehicleDefectOut)
def resolve_defect_endpoint(
    vehicle_id: str,
    defect_id: str,
    payload: VehicleDefectResolveIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher", "Ops_Manager")),
) -> VehicleDefectOut:
    d = db.get(VehicleDefect, defect_id)
    if not d or d.vehicle_id != vehicle_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Defect not found")
    is_critical = str(d.severity).lower() in ("critical", "blocking")
    payload = payload or VehicleDefectResolveIn()
    res_notes = (payload.resolution_notes or "").strip()
    if is_critical:
        require_permission_http(current_user, CAN_OVERRIDE_VEHICLE_BLOCK, db=db)
        if len(res_notes) < MIN_BREAK_GLASS_REASON_LEN:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Resolution notes must be at least {MIN_BREAK_GLASS_REASON_LEN} characters "
                    "when resolving a critical or blocking defect (break-glass audit)."
                ),
            )
    try:
        out = resolve_defect(
            db,
            vehicle_id=vehicle_id,
            defect_id=defect_id,
            resolved_by_user_id=current_user.id,
            resolution_notes=payload.resolution_notes,
        )
        if is_critical:
            record_break_glass_override(
                db,
                actor_user_id=current_user.id,
                override_kind="vehicle_critical_defect_resolve",
                target_type="vehicle_defect",
                target_id=str(defect_id),
                reason=res_notes,
                metadata={
                    "vehicle_id": vehicle_id,
                    "defect_id": defect_id,
                    "severity": str(d.severity),
                },
                commit=True,
            )
        return VehicleDefectOut.model_validate(out)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
