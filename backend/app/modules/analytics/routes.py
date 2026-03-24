from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.analytics.schemas import DashboardOut, EtlRunOut
from backend.app.modules.analytics.service import (
    etl_run,
    get_job_margin_summary,
    get_latest_dashboard,
    list_job_cost_variance_rows,
)
from backend.app.modules.costing.schemas import JobCostVarianceRowOut, JobMarginSummaryOut


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/etl/run", response_model=EtlRunOut)
def run_etl_endpoint(
    date: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> EtlRunOut:
    try:
        if not date:
            date = datetime.now(timezone.utc).date().isoformat()
        snapshot_id = etl_run(db, snapshot_date=date)
        return EtlRunOut(snapshot_id=snapshot_id, snapshot_date=date)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard", response_model=DashboardOut)
def dashboard_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> DashboardOut:
    snap = get_latest_dashboard(db)
    if not snap:
        return DashboardOut(snapshot_date=None, data={})
    import json

    payload = json.loads(snap.data_json)
    return DashboardOut(snapshot_date=snap.snapshot_date, data=payload)


@router.get("/jobs/{job_id}/margin-summary", response_model=JobMarginSummaryOut)
def job_margin_summary_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobMarginSummaryOut:
    try:
        return JobMarginSummaryOut.model_validate(get_job_margin_summary(db, job_id=job_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/dashboard/job-cost-variance", response_model=list[JobCostVarianceRowOut])
def job_cost_variance_dashboard_endpoint(
    job_status: str | None = Query(default="completed"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[JobCostVarianceRowOut]:
    rows = list_job_cost_variance_rows(db, job_status=job_status, limit=limit)
    return [JobCostVarianceRowOut.model_validate(r) for r in rows]

