from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.ppm.schemas import (
    PpmRunGenerationIn,
    PpmRunGenerationOut,
    PpmScheduleCreateIn,
    PpmScheduleOut,
    PpmSchedulePatchIn,
)
from backend.app.modules.ppm.service import (
    create_ppm_schedule,
    generate_ppm_jobs,
    get_ppm_schedule,
    list_ppm_schedules,
    patch_ppm_schedule,
)

router = APIRouter(prefix="/ppm", tags=["ppm"])


@router.post("/schedules", response_model=PpmScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: PpmScheduleCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PpmScheduleOut:
    try:
        return create_ppm_schedule(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/schedules", response_model=list[PpmScheduleOut])
def list_schedules(
    contract_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[PpmScheduleOut]:
    return list_ppm_schedules(db, contract_id=contract_id, site_id=site_id)


@router.get("/schedules/{schedule_id}", response_model=PpmScheduleOut)
def get_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PpmScheduleOut:
    s = get_ppm_schedule(db, schedule_id=schedule_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return s


@router.patch("/schedules/{schedule_id}", response_model=PpmScheduleOut)
def patch_schedule(
    schedule_id: str,
    payload: PpmSchedulePatchIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PpmScheduleOut:
    try:
        return patch_ppm_schedule(db, schedule_id=schedule_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/run-generation", response_model=PpmRunGenerationOut)
def run_generation(
    payload: PpmRunGenerationIn | None = None,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PpmRunGenerationOut:
    payload = payload or PpmRunGenerationIn()
    created, skipped = generate_ppm_jobs(
        db,
        run_date=payload.run_date,
        planning_window_days=payload.planning_window_days,
    )
    return PpmRunGenerationOut(created_job_ids=created, skipped_schedule_ids=skipped)
