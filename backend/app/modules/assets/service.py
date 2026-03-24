from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset, MaintenanceSchedule
from backend.app.modules.assets.schemas import AssetCreateIn, AssetPatchIn, MaintenanceScheduleCreateIn
from backend.app.modules.dispatch.models import Job
from backend.app.modules.sites.models import Site


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def create_asset(db: Session, *, payload: AssetCreateIn) -> Asset:
    if payload.site_id and not db.get(Site, payload.site_id):
        raise ValueError("Site not found")
    code = (payload.asset_code or "").strip() or f"A-{uuid.uuid4().hex[:8].upper()}"
    asset = Asset(
        customer_id=payload.customer_id,
        site_id=payload.site_id,
        contract_id=payload.contract_id,
        asset_code=code,
        asset_type=payload.asset_type,
        name=payload.name,
        manufacturer=payload.manufacturer,
        model=payload.model,
        serial_number=payload.serial_number,
        install_date=payload.install_date,
        commissioning_date=payload.commissioning_date,
        warranty_expiry=payload.warranty_expiry,
        status=payload.status,
        criticality=payload.criticality,
        service_interval_value=payload.service_interval_value,
        service_interval_unit=payload.service_interval_unit,
        last_service_date=payload.last_service_date,
        next_service_date=payload.next_service_date,
        notes=payload.notes,
        compliance_tags_json=payload.compliance_tags_json or "[]",
        required_competencies_json=payload.required_competencies_json or "[]",
        location_address=payload.location_address,
        next_maintenance_eta_at=payload.next_maintenance_eta_at,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset(db: Session, *, asset_id: str) -> Asset | None:
    return db.get(Asset, asset_id)


def patch_asset(db: Session, *, asset_id: str, payload: AssetPatchIn) -> Asset:
    a = db.get(Asset, asset_id)
    if not a:
        raise ValueError("Asset not found")
    if payload.site_id is not None and payload.site_id and not db.get(Site, payload.site_id):
        raise ValueError("Site not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


def list_assets(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    site_id: str | None = None,
    customer_id: str | None = None,
) -> list[Asset]:
    q = db.query(Asset).order_by(Asset.created_at.desc())
    if site_id:
        q = q.filter(Asset.site_id == site_id)
    if customer_id:
        q = q.filter(Asset.customer_id == customer_id)
    return q.offset(offset).limit(limit).all()


def create_maintenance_schedule(
    db: Session, *, payload: MaintenanceScheduleCreateIn
) -> MaintenanceSchedule:
    schedule = MaintenanceSchedule(
        asset_id=payload.asset_id,
        schedule_type=payload.schedule_type,
        next_due_at=payload.next_due_at,
        interval_days=payload.interval_days,
        notes=payload.notes,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def list_maintenance_schedules(
    db: Session, *, limit: int = 50, offset: int = 0
) -> list[MaintenanceSchedule]:
    return (
        db.query(MaintenanceSchedule)
        .order_by(MaintenanceSchedule.next_due_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def run_due_maintenance(
    db: Session, *, now: datetime | None = None, contract_id: str | None = None
) -> list[str]:
    now = _to_utc_naive(now or utc_now())

    if contract_id:
        due_schedules = (
            db.query(MaintenanceSchedule)
            .join(Asset, MaintenanceSchedule.asset_id == Asset.id)
            .filter(Asset.contract_id == contract_id)
            .filter(MaintenanceSchedule.next_due_at <= now)
            .all()
        )
    else:
        due_schedules = (
            db.query(MaintenanceSchedule)
            .filter(MaintenanceSchedule.next_due_at <= now)
            .all()
        )

    created_job_ids: list[str] = []

    for sched in due_schedules:
        asset = db.get(Asset, sched.asset_id)
        if not asset:
            continue

        job_status = "ppm_created" if asset.contract_id else "maintenance_created"

        job = Job(
            customer_id=asset.customer_id,
            contract_id=asset.contract_id,
            site_id=asset.site_id,
            asset_id=asset.id,
            quote_id=None,
            address=asset.location_address,
            scheduled_at=None,
            status=job_status,
            work_type="planned_maintenance",
            covered_under_contract=bool(asset.contract_id),
            site_latitude=None,
            site_longitude=None,
        )
        db.add(job)
        db.flush()
        created_job_ids.append(job.id)

        sched.next_due_at = sched.next_due_at + timedelta(days=int(sched.interval_days or 0))

    db.commit()
    return created_job_ids
