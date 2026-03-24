from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.dispatch.operational_tracking_service import (
    build_internal_job_timeline,
    compute_internal_job_eta,
    get_operational_tracking_state,
)
from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.models import Job
from backend.app.services.equipment_readiness_service import evaluate_job_equipment_readiness
from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness
from backend.app.modules.dispatch.service import mark_job_on_my_way_for_customer, set_job_manual_eta_minutes


class InternalJobEtaOut(BaseModel):
    job_id: str
    eta_minutes: float | None
    eta_window_start: datetime | None
    eta_window_end: datetime | None
    eta_confidence: str
    eta_source: str
    last_updated_at: datetime | None
    operational_position_source: str | None
    telemetry_freshness_status: str


class OnMyWayIn(BaseModel):
    source: str = "dispatcher_manual"
    set_en_route: bool = True


class ManualEtaIn(BaseModel):
    eta_minutes: int | None = None


router = APIRouter(prefix="/dispatch", tags=["dispatch-tracking"])


@router.get("/jobs/{job_id}/tracking")
def dispatch_job_tracking_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    try:
        state = get_operational_tracking_state(db, job_id=job_id)
        state["internal_timeline_events"] = build_internal_job_timeline(db, job_id=job_id)
        try:
            state["equipment_readiness"] = evaluate_job_equipment_readiness(db, job_id=job_id).to_dict()
        except Exception:
            state["equipment_readiness"] = None
        state["vehicle_readiness"] = None
        try:
            job = db.get(Job, job_id)
            if job and job.assigned_engineer_id:
                eu = db.get(User, job.assigned_engineer_id)
                if eu and eu.assigned_vehicle_id:
                    state["vehicle_readiness"] = evaluate_vehicle_readiness(
                        db, vehicle_id=eu.assigned_vehicle_id.strip()
                    ).to_dict()
        except Exception:
            state["vehicle_readiness"] = None
        return state
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/jobs/{job_id}/eta", response_model=InternalJobEtaOut)
def dispatch_job_eta_endpoint(
    job_id: str,
    now: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> InternalJobEtaOut:
    try:
        raw = compute_internal_job_eta(db, job_id=job_id, now=now)
        return InternalJobEtaOut(
            job_id=raw["job_id"],
            eta_minutes=raw.get("eta_minutes"),
            eta_window_start=raw.get("eta_window_start"),
            eta_window_end=raw.get("eta_window_end"),
            eta_confidence=str(raw.get("eta_confidence")),
            eta_source=str(raw.get("eta_source")),
            last_updated_at=raw.get("last_updated_at"),
            operational_position_source=raw.get("operational_position_source"),
            telemetry_freshness_status=str(raw.get("telemetry_freshness_status") or "unknown"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/jobs/{job_id}/timeline")
def dispatch_job_timeline_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    try:
        return {"job_id": job_id, "events": build_internal_job_timeline(db, job_id=job_id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/jobs/{job_id}/customer-notify/on-my-way", status_code=status.HTTP_200_OK)
def dispatch_mark_on_my_way_endpoint(
    job_id: str,
    payload: OnMyWayIn | None = None,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    payload = payload or OnMyWayIn()
    try:
        job = mark_job_on_my_way_for_customer(
            db,
            job_id=job_id,
            source=payload.source,
            set_en_route=payload.set_en_route,
        )
        return {
            "job_id": job.id,
            "on_my_way_sent_at": job.on_my_way_sent_at.isoformat() if job.on_my_way_sent_at else None,
            "customer_notified_at": job.customer_notified_at.isoformat() if job.customer_notified_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/jobs/{job_id}/manual-eta", status_code=status.HTTP_200_OK)
def dispatch_manual_eta_endpoint(
    job_id: str,
    payload: ManualEtaIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    try:
        job = set_job_manual_eta_minutes(db, job_id=job_id, eta_minutes=payload.eta_minutes)
        return {"job_id": job.id, "manual_eta_minutes": job.manual_eta_minutes}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
