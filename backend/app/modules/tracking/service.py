from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.tracking.models import JobGeofence, VehicleTelemetryPoint
from backend.app.modules.tracking.telemetry_state_service import record_engineer_phone_telemetry
from backend.app.modules.tracking.schemas import JobGeofenceIn, TelemetryIn
from backend.app.services.runtime_settings_service import get_effective_dispatch_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def haversine_m(*, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Straightforward haversine distance (meters) for geofence checks.
    """

    r = 6371000.0  # Earth radius (meters)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def ingest_telemetry(db: Session, *, payload: TelemetryIn) -> VehicleTelemetryPoint:
    occurred = payload.occurred_at or utc_now()
    point = VehicleTelemetryPoint(
        vehicle_id=payload.vehicle_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        heading=payload.heading,
        speed_mps=payload.speed_mps,
        occurred_at=occurred,
        raw_payload=None,
    )
    db.add(point)
    user = db.get(User, payload.vehicle_id)
    if user and "Engineer" in set(user.role_names()):
        record_engineer_phone_telemetry(
            db,
            engineer_id=payload.vehicle_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            occurred_at=occurred,
            heading=payload.heading,
            speed_mps=payload.speed_mps,
            commit=False,
        )
    db.commit()
    db.refresh(point)

    # Best-effort customer delay automation (spec step: "delay notices if appropriate").
    # This does not block telemetry ingestion: any failure is silently ignored.
    try:
        from backend.app.modules.dispatch.models import Job, JobEtaDelayNotice, JobEtaState

        ds = get_effective_dispatch_settings(db)
        avg_speed_mps = float(ds["avg_vehicle_speed_mps"])
        min_increase_minutes = float(getattr(settings, "PHI_DPS_ETA_DELAY_MIN_INCREASE_MINUTES", 10.0))
        multiplier = float(getattr(settings, "PHI_DPS_ETA_DELAY_MULTIPLIER", 1.2))
        suppression_minutes = float(getattr(settings, "PHI_DPS_ETA_DELAY_SUPPRESSION_MINUTES", 30.0))

        now = point.occurred_at

        # Only consider active jobs assigned to this engineer.
        active_jobs = (
            db.query(Job)
            .filter(Job.assigned_engineer_id == payload.vehicle_id)
            .filter(Job.status.not_in(["completed", "closed", "cancelled"]))
            .all()
        )

        if active_jobs:
            for job in active_jobs:
                geofence = get_job_geofence(db, job_id=job.id)
                if not geofence:
                    continue

                distance_m = haversine_m(
                    lat1=payload.latitude,
                    lon1=payload.longitude,
                    lat2=geofence.latitude,
                    lon2=geofence.longitude,
                )
                eta_minutes = float(distance_m / max(avg_speed_mps, 0.1) / 60.0)

                state = db.query(JobEtaState).filter(JobEtaState.job_id == job.id).one_or_none()
                if not state:
                    db.add(
                        JobEtaState(
                            job_id=job.id,
                            last_eta_minutes=eta_minutes,
                            last_eta_updated_at=now,
                        )
                    )
                    continue

                prev_eta = float(state.last_eta_minutes)
                should_trigger = False
                if eta_minutes >= prev_eta + min_increase_minutes:
                    should_trigger = True
                elif prev_eta > 0 and eta_minutes >= prev_eta * multiplier:
                    should_trigger = True

                if should_trigger:
                    last_notice = (
                        db.query(JobEtaDelayNotice)
                        .filter(JobEtaDelayNotice.job_id == job.id, JobEtaDelayNotice.status == "open")
                        .order_by(JobEtaDelayNotice.created_at.desc())
                        .first()
                    )

                    if not last_notice or (now - last_notice.created_at).total_seconds() >= suppression_minutes * 60:
                        db.add(
                            JobEtaDelayNotice(
                                job_id=job.id,
                                message=(
                                    f"Delay notice: ETA now ~{round(eta_minutes)} min "
                                    f"(was ~{round(prev_eta)} min)."
                                ),
                                eta_minutes=eta_minutes,
                                status="open",
                            )
                        )

                state.last_eta_minutes = eta_minutes
                state.last_eta_updated_at = now

            db.commit()
    except Exception:
        # telemetry should never be blocked by automation.
        pass

    return point


def set_job_geofence(
    db: Session,
    *,
    job_id: str,
    geofence_in: JobGeofenceIn,
) -> JobGeofence:
    existing = db.query(JobGeofence).filter(JobGeofence.job_id == job_id).one_or_none()
    if existing:
        existing.latitude = geofence_in.latitude
        existing.longitude = geofence_in.longitude
        existing.radius_m = geofence_in.radius_m
        db.commit()
        db.refresh(existing)
        return existing

    geofence = JobGeofence(
        job_id=job_id,
        latitude=geofence_in.latitude,
        longitude=geofence_in.longitude,
        radius_m=geofence_in.radius_m,
    )
    db.add(geofence)
    db.commit()
    db.refresh(geofence)
    return geofence


def check_point_in_geofence(
    *,
    latitude: float,
    longitude: float,
    geofence: JobGeofence,
) -> tuple[bool, float]:
    distance_m = haversine_m(
        lat1=latitude,
        lon1=longitude,
        lat2=geofence.latitude,
        lon2=geofence.longitude,
    )
    return distance_m <= geofence.radius_m, distance_m


def get_job_geofence(db: Session, *, job_id: str) -> JobGeofence | None:
    return db.query(JobGeofence).filter(JobGeofence.job_id == job_id).one_or_none()


def get_latest_vehicle_points(
    db: Session,
    *,
    vehicle_ids: list[str] | None = None,
) -> list[VehicleTelemetryPoint]:
    """
    Latest telemetry point per vehicle_id.

    Used for "nearest engineer" and live location intelligence.
    """
    latest_subq = (
        db.query(
            VehicleTelemetryPoint.vehicle_id.label("vehicle_id"),
            func.max(VehicleTelemetryPoint.occurred_at).label("max_occurred_at"),
        )
        .group_by(VehicleTelemetryPoint.vehicle_id)
        .subquery()
    )

    q = (
        db.query(VehicleTelemetryPoint)
        .join(
            latest_subq,
            and_(
                VehicleTelemetryPoint.vehicle_id == latest_subq.c.vehicle_id,
                VehicleTelemetryPoint.occurred_at == latest_subq.c.max_occurred_at,
            ),
        )
    )

    if vehicle_ids:
        q = q.filter(VehicleTelemetryPoint.vehicle_id.in_(vehicle_ids))

    return q.all()

