from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.tracking.models import EngineerLatestLocation, VehicleLatestLocation
from backend.app.modules.tracking.telemetry_state_service import classify_telemetry_freshness, utc_now


@dataclass(frozen=True)
class OperationalPosition:
    latitude: float
    longitude: float
    source: str  # phone | vehicle
    occurred_at: datetime
    freshness_status: str
    vehicle_id: str | None = None


def _candidate_from_engineer_latest(row: EngineerLatestLocation) -> OperationalPosition:
    return OperationalPosition(
        latitude=row.last_latitude,
        longitude=row.last_longitude,
        source="phone",
        occurred_at=row.last_occurred_at,
        freshness_status=row.freshness_status,
        vehicle_id=None,
    )


def _candidate_from_vehicle_latest(row: VehicleLatestLocation) -> OperationalPosition:
    return OperationalPosition(
        latitude=row.last_latitude,
        longitude=row.last_longitude,
        source="vehicle",
        occurred_at=row.last_occurred_at,
        freshness_status=row.freshness_status,
        vehicle_id=row.vehicle_id,
    )


def resolve_operational_position_for_engineer(db: Session, *, engineer_id: str, now: datetime | None = None) -> OperationalPosition | None:
    """
    Decide which live coordinates to use for dispatch for an engineer (phone vs assigned/bound van).
    Centralised precedence — do not duplicate in route handlers.
    """
    now = now or utc_now()
    user = db.get(User, engineer_id)
    phone_row = db.get(EngineerLatestLocation, engineer_id)
    phone = _candidate_from_engineer_latest(phone_row) if phone_row else None

    vehicle_rows: list[VehicleLatestLocation] = []
    if user and user.assigned_vehicle_id:
        v = db.get(VehicleLatestLocation, user.assigned_vehicle_id)
        if v:
            vehicle_rows.append(v)
    extra = db.query(VehicleLatestLocation).filter(VehicleLatestLocation.assigned_engineer_id == engineer_id).all()
    for v in extra:
        if v not in vehicle_rows:
            vehicle_rows.append(v)

    vehicles = [_candidate_from_vehicle_latest(v) for v in vehicle_rows]

    mode = (settings.PHI_DPS_OPERATIONAL_POSITION_MODE or "freshest").lower()
    candidates: list[OperationalPosition] = []
    if phone:
        candidates.append(phone)
    candidates.extend(vehicles)

    if not candidates:
        return None

    def sort_key(c: OperationalPosition) -> tuple:
        freshness_rank = {"fresh": 0, "aging": 1, "stale": 2}.get(c.freshness_status, 3)
        ts = -c.occurred_at.timestamp()
        if mode == "vehicle_preferred":
            return (0 if c.source == "vehicle" else 1, freshness_rank, ts)
        if mode == "phone_preferred":
            return (0 if c.source == "phone" else 1, freshness_rank, ts)
        # freshest: best freshness first, then most recent fix.
        return (freshness_rank, ts)

    candidates.sort(key=sort_key)
    best = candidates[0]
    # Recompute freshness against `now` for consistency in scoring layer.
    live_fresh = classify_telemetry_freshness(occurred_at=best.occurred_at, now=now)
    return OperationalPosition(
        latitude=best.latitude,
        longitude=best.longitude,
        source=best.source,
        occurred_at=best.occurred_at,
        freshness_status=live_fresh,
        vehicle_id=best.vehicle_id,
    )
