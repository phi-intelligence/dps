from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.dispatch.live_map_service import build_live_dispatch_map
from backend.app.modules.dispatch.models import DispatchDecisionLog, Job
from backend.app.modules.dispatch.recommendation_engine import (
    DispatchRecommendationRow,
    compute_ranked_dispatch_recommendations,
)
from backend.app.modules.dispatch.schemas import (
    AssignBestIn,
    AssignBestOut,
    DispatchRecommendationRowOut,
    EngineerAvailabilityRowOut,
    JobDispatchRecommendationsOut,
    LiveMapEngineerOut,
    LiveMapJobOut,
    LiveMapOut,
    LiveMapVehicleOut,
    VehicleBindingIn,
)
from backend.app.modules.dispatch.service import assign_job
from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.availability_service import count_active_assigned_jobs, compute_engineer_availability
from backend.app.services.equipment_readiness_service import evaluate_job_equipment_readiness
from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness


router = APIRouter(prefix="/dispatch", tags=["dispatch"])


def _row_out(r: DispatchRecommendationRow) -> DispatchRecommendationRowOut:
    return DispatchRecommendationRowOut(
        engineer_id=r.engineer_id,
        distance_km=r.distance_km,
        estimated_travel_minutes=r.estimated_travel_minutes,
        availability_state=r.availability_state,
        telemetry_freshness_seconds=r.telemetry_freshness_seconds,
        competency_match=r.competency_match,
        active_job_count=r.active_job_count,
        recommendation_score=r.recommendation_score,
        recommendation_reasons=r.recommendation_reasons,
        operational_latitude=r.operational_latitude,
        operational_longitude=r.operational_longitude,
        operational_source=r.operational_source,
        last_occurred_at=r.last_occurred_at,
        equipment_readiness_status=r.equipment_readiness_status,
        equipment_readiness_reasons=list(r.equipment_readiness_reasons or []),
        vehicle_readiness_status=r.vehicle_readiness_status,
        vehicle_readiness_reasons=list(r.vehicle_readiness_reasons or []),
    )


@router.get("/jobs/{job_id}/recommendations", response_model=JobDispatchRecommendationsOut)
def dispatch_job_recommendations_endpoint(
    job_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    include_stale: bool = Query(default=False),
    required_competencies: str | None = Query(
        default=None,
        description="Comma-separated competencies; overrides job.required_competencies when non-empty.",
    ),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobDispatchRecommendationsOut:
    req_list = [c.strip() for c in (required_competencies or "").split(",") if c.strip()] or None
    try:
        result = compute_ranked_dispatch_recommendations(
            db,
            job_id=job_id,
            limit=limit,
            required_competencies=req_list,
            include_stale=include_stale,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    job_eq = None
    try:
        job_eq = evaluate_job_equipment_readiness(db, job_id=job_id).to_dict()
    except Exception:
        job_eq = None

    job_vr = None
    j = db.get(Job, job_id)
    if j and j.assigned_engineer_id:
        eu = db.get(User, j.assigned_engineer_id)
        if eu and eu.assigned_vehicle_id:
            try:
                job_vr = evaluate_vehicle_readiness(db, vehicle_id=eu.assigned_vehicle_id.strip()).to_dict()
            except Exception:
                job_vr = None

    return JobDispatchRecommendationsOut(
        job_id=result.job_id,
        dispatch_point_source=result.dispatch_point_source,
        recommendations=[_row_out(r) for r in result.recommendations],
        job_equipment_readiness=job_eq,
        job_vehicle_readiness=job_vr,
    )


@router.post("/jobs/{job_id}/assign-best", response_model=AssignBestOut)
def dispatch_assign_best_endpoint(
    job_id: str,
    payload: AssignBestIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> AssignBestOut:
    payload = payload or AssignBestIn()
    try:
        result = compute_ranked_dispatch_recommendations(
            db,
            job_id=job_id,
            limit=25,
            required_competencies=payload.required_competencies,
            include_stale=payload.include_stale,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not result.recommendations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No suitable engineers found for auto-assign",
        )

    best = result.recommendations[0]
    merged_req: list[str] = []
    if payload.required_competencies:
        merged_req = [c for c in payload.required_competencies if c]
    if not merged_req:
        job = db.get(Job, job_id)
        if job:
            try:
                raw = json.loads(job.required_competencies_json or "[]")
                if isinstance(raw, list):
                    merged_req = [str(x).strip() for x in raw if str(x).strip()]
            except Exception:
                merged_req = []

    try:
        assign_job(db, job_id=job_id, engineer_id=best.engineer_id, required_competencies=merged_req or None)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    audit_rows = [r.to_audit_dict() for r in result.recommendations]
    log = DispatchDecisionLog(
        job_id=job_id,
        decision_type="auto_assign",
        actor_user_id=current_user.id,
        chosen_engineer_id=best.engineer_id,
        ranked_candidates_json=json.dumps(audit_rows),
        scoring_breakdown_json=json.dumps(result.scoring_notes),
        notes=payload.notes,
    )
    db.add(log)
    db.commit()

    explanation = list(best.recommendation_reasons)
    explanation.insert(0, f"selected_highest_score:{best.recommendation_score}")
    if best.equipment_readiness_status and best.equipment_readiness_status != "ready":
        explanation.append(f"equipment_readiness:{best.equipment_readiness_status}")
    if best.vehicle_readiness_status and best.vehicle_readiness_status != "ready":
        explanation.append(f"vehicle_readiness:{best.vehicle_readiness_status}")

    return AssignBestOut(
        job_id=job_id,
        selected_engineer_id=best.engineer_id,
        recommendation_score=best.recommendation_score,
        explanation_reasons=explanation,
        ranked=[_row_out(r) for r in result.recommendations[:10]],
    )


@router.get("/live-map", response_model=LiveMapOut)
def dispatch_live_map_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> LiveMapOut:
    m = build_live_dispatch_map(db)
    return LiveMapOut(
        engineers=[
            LiveMapEngineerOut(
                engineer_id=e.engineer_id,
                latitude=e.latitude,
                longitude=e.longitude,
                operational_source=e.operational_source,
                freshness_status=e.freshness_status,
                availability_state=e.availability_state,
                stale=e.stale,
            )
            for e in m.engineers
        ],
        vehicles=[
            LiveMapVehicleOut(
                vehicle_id=v.vehicle_id,
                latitude=v.latitude,
                longitude=v.longitude,
                assigned_engineer_id=v.assigned_engineer_id,
                freshness_status=v.freshness_status,
                readiness_status=v.readiness_status,
                readiness_warnings=v.readiness_warnings,
                readiness_blocking_flags=v.readiness_blocking_flags,
            )
            for v in m.vehicles
        ],
        jobs=[
            LiveMapJobOut(
                job_id=j.job_id,
                status=j.status,
                assigned_engineer_id=j.assigned_engineer_id,
                site_latitude=j.site_latitude,
                site_longitude=j.site_longitude,
            )
            for j in m.jobs
        ],
    )


@router.get("/engineers/availability", response_model=list[EngineerAvailabilityRowOut])
def dispatch_engineers_availability_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[EngineerAvailabilityRowOut]:
    users = db.query(User).all()
    engineer_ids = [u.id for u in users if "Engineer" in set(u.role_names())]
    out: list[EngineerAvailabilityRowOut] = []
    for eid in engineer_ids:
        av = compute_engineer_availability(db, engineer_id=eid, required_competencies=None)
        out.append(
            EngineerAvailabilityRowOut(
                engineer_id=eid,
                availability_state=av,
                active_job_count=count_active_assigned_jobs(db, engineer_id=eid),
            )
        )
    return out


@router.post("/vehicle-bindings", status_code=status.HTTP_200_OK)
def bind_engineer_vehicle_endpoint(
    payload: VehicleBindingIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    user = db.get(User, payload.engineer_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engineer not found")
    if "Engineer" not in set(user.role_names()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an engineer")
    user.assigned_vehicle_id = payload.vehicle_id
    db.commit()
    return {"status": "ok", "engineer_id": payload.engineer_id, "vehicle_id": payload.vehicle_id}
