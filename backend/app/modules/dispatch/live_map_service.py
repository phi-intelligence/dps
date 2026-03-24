from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.availability_service import TERMINAL_JOB_STATUSES, compute_engineer_availability
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.tracking.models import VehicleLatestLocation
from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LiveMapEngineer:
    engineer_id: str
    latitude: float | None
    longitude: float | None
    operational_source: str | None
    freshness_status: str | None
    availability_state: str
    stale: bool


@dataclass
class LiveMapVehicle:
    vehicle_id: str
    latitude: float
    longitude: float
    assigned_engineer_id: str | None
    freshness_status: str
    readiness_status: str | None = None
    readiness_warnings: list[str] | None = None
    readiness_blocking_flags: list[str] | None = None


@dataclass
class LiveMapJob:
    job_id: str
    status: str
    assigned_engineer_id: str | None
    site_latitude: float | None
    site_longitude: float | None


@dataclass
class LiveDispatchMap:
    engineers: list[LiveMapEngineer]
    vehicles: list[LiveMapVehicle]
    jobs: list[LiveMapJob]


def build_live_dispatch_map(db: Session, *, now: datetime | None = None) -> LiveDispatchMap:
    now = now or utc_now()
    users = db.query(User).all()
    engineer_ids = [u.id for u in users if "Engineer" in set(u.role_names())]

    engineers: list[LiveMapEngineer] = []
    for eid in engineer_ids:
        op = resolve_operational_position_for_engineer(db, engineer_id=eid, now=now)
        av = compute_engineer_availability(db, engineer_id=eid, required_competencies=None, now=now)
        stale = op is None or (op.freshness_status == "stale")
        engineers.append(
            LiveMapEngineer(
                engineer_id=eid,
                latitude=op.latitude if op else None,
                longitude=op.longitude if op else None,
                operational_source=op.source if op else None,
                freshness_status=op.freshness_status if op else None,
                availability_state=av,
                stale=stale,
            )
        )

    vehicles: list[LiveMapVehicle] = []
    for v in db.query(VehicleLatestLocation).all():
        vr = evaluate_vehicle_readiness(db, vehicle_id=v.vehicle_id, now=now)
        vehicles.append(
            LiveMapVehicle(
                vehicle_id=v.vehicle_id,
                latitude=v.last_latitude,
                longitude=v.last_longitude,
                assigned_engineer_id=v.assigned_engineer_id,
                freshness_status=v.freshness_status,
                readiness_status=vr.readiness_status,
                readiness_warnings=vr.warnings,
                readiness_blocking_flags=vr.blocking_flags,
            )
        )

    jobs: list[LiveMapJob] = []
    for j in db.query(Job).filter(Job.status.not_in(TERMINAL_JOB_STATUSES)).all():
        jobs.append(
            LiveMapJob(
                job_id=j.id,
                status=j.status,
                assigned_engineer_id=j.assigned_engineer_id,
                site_latitude=j.site_latitude,
                site_longitude=j.site_longitude,
            )
        )

    return LiveDispatchMap(engineers=engineers, vehicles=vehicles, jobs=jobs)
