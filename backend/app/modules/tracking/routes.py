from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from datetime import datetime, timezone

from backend.app.modules.tracking.schemas import (
    EngineerPhoneTelemetryIn,
    EngineerTelemetryPostOut,
    JobGeofenceIn,
    TelemetryIn,
    VehicleTelemetryIn,
    VehicleTelemetryPostOut,
)
from backend.app.modules.tracking.service import get_job_geofence, ingest_telemetry, set_job_geofence
from backend.app.modules.tracking.telemetry_state_service import append_engineer_phone_telemetry, append_vehicle_telemetry

from backend.app.modules.tracking.schemas import TelemetryOut, JobGeofenceOut
from backend.app.modules.dispatch.models import Job


router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/telemetry", response_model=TelemetryOut)
def telemetry_endpoint(
    payload: TelemetryIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> TelemetryOut:
    # Engineer phone location should only be able to report its own vehicle_id.
    # (We map phone vehicle_id to the engineer user id for now.)
    if "Engineer" in set(current_user.role_names()) and payload.vehicle_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden vehicle_id")
    return ingest_telemetry(db, payload=payload)


@router.post("/telemetry/engineer", response_model=EngineerTelemetryPostOut)
def engineer_phone_telemetry_endpoint(
    payload: EngineerPhoneTelemetryIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
) -> EngineerTelemetryPostOut:
    occurred = payload.occurred_at or datetime.now(timezone.utc)
    ev = append_engineer_phone_telemetry(
        db,
        engineer_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        occurred_at=occurred,
        accuracy_m=payload.accuracy,
        heading=payload.heading,
        speed_mps=payload.speed,
        battery_pct=payload.battery,
    )
    return EngineerTelemetryPostOut(
        id=ev.id,
        engineer_id=ev.engineer_id,
        latitude=ev.latitude,
        longitude=ev.longitude,
        occurred_at=ev.occurred_at,
    )


@router.post("/telemetry/vehicle", response_model=VehicleTelemetryPostOut)
def vehicle_telemetry_endpoint(
    payload: VehicleTelemetryIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> VehicleTelemetryPostOut:
    roles = set(current_user.role_names())
    if "Engineer" in roles and "Admin" not in roles and "Dispatcher" not in roles:
        if current_user.assigned_vehicle_id != payload.vehicle_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Engineer may only post telemetry for assigned_vehicle_id",
            )
    occurred = payload.occurred_at or datetime.now(timezone.utc)
    ev = append_vehicle_telemetry(
        db,
        vehicle_id=payload.vehicle_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        occurred_at=occurred,
        assigned_engineer_id=payload.assigned_engineer_id,
        heading=payload.heading,
        speed_mps=payload.speed,
        ignition_on=payload.ignition,
        fuel_level_pct=payload.fuel,
    )
    return VehicleTelemetryPostOut(id=ev.id, vehicle_id=ev.vehicle_id, occurred_at=ev.occurred_at)


@router.post("/geofences/{job_id}", response_model=JobGeofenceOut)
def geofence_endpoint(
    job_id: str,
    payload: JobGeofenceIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobGeofenceOut:
    # Basic existence check.
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    geofence = set_job_geofence(db, job_id=job_id, geofence_in=payload)
    return geofence


@router.get("/geofences/{job_id}", response_model=JobGeofenceOut)
def get_geofence_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> JobGeofenceOut:
    geofence = get_job_geofence(db, job_id=job_id)
    if not geofence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geofence not found")
    return geofence

