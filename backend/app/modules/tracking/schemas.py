from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TelemetryIn(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    heading: float | None = None
    speed_mps: float | None = None
    occurred_at: datetime | None = None


class TelemetryOut(BaseModel):
    id: str
    vehicle_id: str
    latitude: float
    longitude: float
    occurred_at: datetime

    class Config:
        from_attributes = True


class JobGeofenceIn(BaseModel):
    latitude: float
    longitude: float
    radius_m: float


class JobGeofenceOut(BaseModel):
    id: str
    job_id: str
    latitude: float
    longitude: float
    radius_m: float
    created_at: datetime

    class Config:
        from_attributes = True


class EngineerPhoneTelemetryIn(BaseModel):
    latitude: float
    longitude: float
    occurred_at: datetime | None = None
    accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None  # metres per second
    battery: float | None = None


class EngineerTelemetryPostOut(BaseModel):
    id: str
    engineer_id: str
    latitude: float
    longitude: float
    occurred_at: datetime

    class Config:
        from_attributes = True


class VehicleTelemetryIn(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    occurred_at: datetime | None = None
    assigned_engineer_id: str | None = None
    heading: float | None = None
    speed: float | None = None  # metres per second
    ignition: bool | None = None
    fuel: float | None = None


class VehicleTelemetryPostOut(BaseModel):
    id: str
    vehicle_id: str
    occurred_at: datetime

    class Config:
        from_attributes = True

