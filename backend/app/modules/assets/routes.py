from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.assets.schemas import (
    AssetCreateIn,
    AssetOut,
    AssetPatchIn,
    MaintenanceScheduleCreateIn,
    MaintenanceScheduleOut,
    RunDueOut,
)
from backend.app.modules.assets.service import (
    create_asset,
    create_maintenance_schedule,
    get_asset,
    list_assets,
    list_maintenance_schedules,
    patch_asset,
    run_due_maintenance,
)
from backend.app.modules.contracts.history_service import build_asset_history

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(
    payload: AssetCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> AssetOut:
    try:
        return create_asset(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[AssetOut])
def list_assets_endpoint(
    limit: int = 50,
    offset: int = 0,
    site_id: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[AssetOut]:
    return list_assets(db, limit=limit, offset=offset, site_id=site_id, customer_id=customer_id)


@router.get("/schedules", response_model=list[MaintenanceScheduleOut])
def list_schedules_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[MaintenanceScheduleOut]:
    return list_maintenance_schedules(db, limit=limit, offset=offset)


@router.post("/maintenance/run-due", response_model=RunDueOut)
def run_due_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RunDueOut:
    job_ids = run_due_maintenance(db)
    return RunDueOut(created_job_ids=job_ids)


@router.get("/{asset_id}/history")
def asset_history_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_asset(db, asset_id=asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return {"asset_id": asset_id, "entries": build_asset_history(db, asset_id=asset_id)}


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> AssetOut:
    a = get_asset(db, asset_id=asset_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return a


@router.patch("/{asset_id}", response_model=AssetOut)
def patch_asset_endpoint(
    asset_id: str,
    payload: AssetPatchIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> AssetOut:
    try:
        return patch_asset(db, asset_id=asset_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{asset_id}/schedules", response_model=MaintenanceScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule_endpoint(
    asset_id: str,
    payload: MaintenanceScheduleCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> MaintenanceScheduleOut:
    if payload.asset_id != asset_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="asset_id mismatch")
    return create_maintenance_schedule(db, payload=payload)
