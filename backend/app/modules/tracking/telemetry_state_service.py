from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.tracking.models import (
    EngineerLatestLocation,
    EngineerTelemetryEvent,
    VehicleLatestLocation,
    VehicleTelemetryEvent,
)
from backend.app.services.runtime_settings_service import get_effective_dispatch_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def classify_telemetry_freshness(*, occurred_at: datetime, now: datetime | None = None, db: Session | None = None) -> str:
    now = _ensure_aware_utc(now or utc_now())
    occurred_at = _ensure_aware_utc(occurred_at)
    age_s = max(0.0, (now - occurred_at).total_seconds())
    ds = get_effective_dispatch_settings(db)
    fresh_s = float(ds["telemetry_fresh_seconds"])
    aging_s = float(ds["telemetry_aging_seconds"])
    if age_s < fresh_s:
        return "fresh"
    if age_s < aging_s:
        return "aging"
    return "stale"


def telemetry_freshness_seconds(*, occurred_at: datetime, now: datetime | None = None) -> float:
    now = _ensure_aware_utc(now or utc_now())
    occurred_at = _ensure_aware_utc(occurred_at)
    return max(0.0, (now - occurred_at).total_seconds())


def record_engineer_phone_telemetry(
    db: Session,
    *,
    engineer_id: str,
    latitude: float,
    longitude: float,
    occurred_at: datetime,
    accuracy_m: float | None = None,
    heading: float | None = None,
    speed_mps: float | None = None,
    battery_pct: float | None = None,
    commit: bool = True,
) -> EngineerTelemetryEvent:
    received_at = utc_now()
    ev = EngineerTelemetryEvent(
        engineer_id=engineer_id,
        source="phone",
        latitude=latitude,
        longitude=longitude,
        accuracy_m=accuracy_m,
        heading=heading,
        speed_mps=speed_mps,
        occurred_at=occurred_at,
        received_at=received_at,
        battery_pct=battery_pct,
    )
    db.add(ev)

    fresh = classify_telemetry_freshness(occurred_at=occurred_at, now=received_at, db=db)
    row = db.get(EngineerLatestLocation, engineer_id)
    if row:
        row.last_latitude = latitude
        row.last_longitude = longitude
        row.last_accuracy_m = accuracy_m
        row.last_heading = heading
        row.last_speed_mps = speed_mps
        row.last_battery_pct = battery_pct
        row.last_occurred_at = occurred_at
        row.last_received_at = received_at
        row.freshness_status = fresh
        row.last_source = "phone"
    else:
        db.add(
            EngineerLatestLocation(
                engineer_id=engineer_id,
                last_latitude=latitude,
                last_longitude=longitude,
                last_accuracy_m=accuracy_m,
                last_heading=heading,
                last_speed_mps=speed_mps,
                last_battery_pct=battery_pct,
                last_occurred_at=occurred_at,
                last_received_at=received_at,
                freshness_status=fresh,
                last_source="phone",
            )
        )

    if commit:
        db.commit()
        db.refresh(ev)
    else:
        db.flush()
    return ev


def append_engineer_phone_telemetry(
    db: Session,
    *,
    engineer_id: str,
    latitude: float,
    longitude: float,
    occurred_at: datetime,
    accuracy_m: float | None = None,
    heading: float | None = None,
    speed_mps: float | None = None,
    battery_pct: float | None = None,
) -> EngineerTelemetryEvent:
    return record_engineer_phone_telemetry(
        db,
        engineer_id=engineer_id,
        latitude=latitude,
        longitude=longitude,
        occurred_at=occurred_at,
        accuracy_m=accuracy_m,
        heading=heading,
        speed_mps=speed_mps,
        battery_pct=battery_pct,
        commit=True,
    )


def record_vehicle_telemetry(
    db: Session,
    *,
    vehicle_id: str,
    latitude: float,
    longitude: float,
    occurred_at: datetime,
    assigned_engineer_id: str | None = None,
    heading: float | None = None,
    speed_mps: float | None = None,
    ignition_on: bool | None = None,
    fuel_level_pct: float | None = None,
    commit: bool = True,
) -> VehicleTelemetryEvent:
    received_at = utc_now()
    ev = VehicleTelemetryEvent(
        vehicle_id=vehicle_id,
        assigned_engineer_id=assigned_engineer_id,
        latitude=latitude,
        longitude=longitude,
        heading=heading,
        speed_mps=speed_mps,
        occurred_at=occurred_at,
        received_at=received_at,
        ignition_on=ignition_on,
        fuel_level_pct=fuel_level_pct,
    )
    db.add(ev)

    fresh = classify_telemetry_freshness(occurred_at=occurred_at, now=received_at, db=db)
    row = db.get(VehicleLatestLocation, vehicle_id)
    if row:
        row.last_latitude = latitude
        row.last_longitude = longitude
        row.last_heading = heading
        row.last_speed_mps = speed_mps
        row.last_ignition_on = ignition_on
        row.last_fuel_level_pct = fuel_level_pct
        row.last_occurred_at = occurred_at
        row.last_received_at = received_at
        row.freshness_status = fresh
        if assigned_engineer_id is not None:
            row.assigned_engineer_id = assigned_engineer_id
    else:
        db.add(
            VehicleLatestLocation(
                vehicle_id=vehicle_id,
                assigned_engineer_id=assigned_engineer_id,
                last_latitude=latitude,
                last_longitude=longitude,
                last_heading=heading,
                last_speed_mps=speed_mps,
                last_ignition_on=ignition_on,
                last_fuel_level_pct=fuel_level_pct,
                last_occurred_at=occurred_at,
                last_received_at=received_at,
                freshness_status=fresh,
            )
        )

    if commit:
        db.commit()
        db.refresh(ev)
    else:
        db.flush()
    return ev


def append_vehicle_telemetry(
    db: Session,
    *,
    vehicle_id: str,
    latitude: float,
    longitude: float,
    occurred_at: datetime,
    assigned_engineer_id: str | None = None,
    heading: float | None = None,
    speed_mps: float | None = None,
    ignition_on: bool | None = None,
    fuel_level_pct: float | None = None,
) -> VehicleTelemetryEvent:
    return record_vehicle_telemetry(
        db,
        vehicle_id=vehicle_id,
        latitude=latitude,
        longitude=longitude,
        occurred_at=occurred_at,
        assigned_engineer_id=assigned_engineer_id,
        heading=heading,
        speed_mps=speed_mps,
        ignition_on=ignition_on,
        fuel_level_pct=fuel_level_pct,
        commit=True,
    )


@dataclass(frozen=True)
class EngineerTelemetryMirrorIn:
    engineer_id: str
    latitude: float
    longitude: float
    occurred_at: datetime
    heading: float | None
    speed_mps: float | None


def mirror_legacy_vehicle_point_to_engineer_state(db: Session, payload: EngineerTelemetryMirrorIn) -> None:
    """
    Keep legacy /tracking/telemetry (vehicle_id == engineer user id) aligned with engineer latest-state tables.
    """
    received_at = utc_now()
    fresh = classify_telemetry_freshness(occurred_at=payload.occurred_at, now=received_at, db=db)
    row = db.get(EngineerLatestLocation, payload.engineer_id)
    if row:
        row.last_latitude = payload.latitude
        row.last_longitude = payload.longitude
        row.last_heading = payload.heading
        row.last_speed_mps = payload.speed_mps
        row.last_occurred_at = payload.occurred_at
        row.last_received_at = received_at
        row.freshness_status = fresh
        row.last_source = "phone"
    else:
        db.add(
            EngineerLatestLocation(
                engineer_id=payload.engineer_id,
                last_latitude=payload.latitude,
                last_longitude=payload.longitude,
                last_heading=payload.heading,
                last_speed_mps=payload.speed_mps,
                last_occurred_at=payload.occurred_at,
                last_received_at=received_at,
                freshness_status=fresh,
                last_source="phone",
            )
        )
