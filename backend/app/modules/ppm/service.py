from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset
from backend.app.modules.contracts.models import Contract
from backend.app.modules.dispatch.models import Job
from backend.app.modules.ppm.models import PpmGenerationRecord, PpmSchedule
from backend.app.modules.ppm.schemas import PpmScheduleCreateIn, PpmSchedulePatchIn
from backend.app.modules.sites.models import Site
from backend.app.modules.sites.service import site_full_address


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def add_frequency(dt: datetime, value: int, unit: str) -> datetime:
    dt = _aware(dt)
    u = (unit or "day").lower()
    if u == "day":
        return dt + timedelta(days=value)
    if u == "week":
        return dt + timedelta(weeks=value)
    if u == "month":
        return dt + timedelta(days=30 * value)
    if u == "year":
        return dt + timedelta(days=365 * value)
    return dt + timedelta(days=value)


def create_ppm_schedule(db: Session, *, payload: PpmScheduleCreateIn) -> PpmSchedule:
    if not db.get(Contract, payload.contract_id):
        raise ValueError("Contract not found")
    if not db.get(Site, payload.site_id):
        raise ValueError("Site not found")
    if payload.asset_id and not db.get(Asset, payload.asset_id):
        raise ValueError("Asset not found")

    sched = PpmSchedule(
        contract_id=payload.contract_id,
        site_id=payload.site_id,
        asset_id=payload.asset_id,
        title=payload.title.strip(),
        frequency_value=payload.frequency_value,
        frequency_unit=payload.frequency_unit.strip(),
        recurrence_rule=payload.recurrence_rule,
        next_due_date=payload.next_due_date,
        planning_window_days=payload.planning_window_days,
        estimated_duration_minutes=payload.estimated_duration_minutes,
        checklist_template_ref=payload.checklist_template_ref,
        compliance_template_ref=payload.compliance_template_ref,
        required_competencies_json=payload.required_competencies_json or "[]",
        active=payload.active,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


def list_ppm_schedules(
    db: Session,
    *,
    contract_id: str | None = None,
    site_id: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[PpmSchedule]:
    q = db.query(PpmSchedule).order_by(PpmSchedule.next_due_date.asc())
    if contract_id:
        q = q.filter(PpmSchedule.contract_id == contract_id)
    if site_id:
        q = q.filter(PpmSchedule.site_id == site_id)
    return q.offset(offset).limit(limit).all()


def get_ppm_schedule(db: Session, *, schedule_id: str) -> PpmSchedule | None:
    return db.get(PpmSchedule, schedule_id)


def patch_ppm_schedule(db: Session, *, schedule_id: str, payload: PpmSchedulePatchIn) -> PpmSchedule:
    s = db.get(PpmSchedule, schedule_id)
    if not s:
        raise ValueError("PPM schedule not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def generate_ppm_jobs(
    db: Session,
    *,
    run_date: datetime | None = None,
    planning_window_days: int | None = None,
) -> tuple[list[str], list[str]]:
    """
    Deterministic, idempotent PPM job generation for schedules whose next_due_date
    falls within [run_date, run_date + planning_window].
    """
    run_date = _aware(run_date or utc_now())
    run_day = run_date.date()

    created: list[str] = []
    skipped_ids: list[str] = []

    schedules = db.query(PpmSchedule).filter(PpmSchedule.active.is_(True)).all()

    for sched in schedules:
        contract = db.get(Contract, sched.contract_id)
        if not contract or (contract.status or "").lower() != "active":
            skipped_ids.append(sched.id)
            continue

        window_days = planning_window_days if planning_window_days is not None else int(sched.planning_window_days or 30)
        window_end_day = run_day + timedelta(days=max(window_days, 0))
        due_day = _aware(sched.next_due_date).date()

        if due_day < run_day or due_day > window_end_day:
            continue

        anchor = due_day.isoformat()
        exists = (
            db.query(PpmGenerationRecord)
            .filter(
                PpmGenerationRecord.ppm_schedule_id == sched.id,
                PpmGenerationRecord.due_anchor == anchor,
            )
            .first()
        )
        if exists:
            continue

        site = db.get(Site, sched.site_id)
        if not site:
            skipped_ids.append(sched.id)
            continue

        asset = db.get(Asset, sched.asset_id) if sched.asset_id else None

        address = site_full_address(site)
        req = sched.required_competencies_json or "[]"
        compliance_required = bool((asset and (asset.compliance_tags_json or "[]") not in ("[]", "null")))

        job = Job(
            customer_id=site.customer_id,
            contract_id=sched.contract_id,
            site_id=site.id,
            asset_id=asset.id if asset else None,
            ppm_schedule_id=sched.id,
            quote_id=None,
            address=address,
            scheduled_at=_aware(sched.next_due_date),
            status="created",
            work_type="planned_maintenance",
            site_latitude=site.latitude,
            site_longitude=site.longitude,
            required_competencies_json=req,
            covered_under_contract=True,
            compliance_required=compliance_required,
            sla_policy_id=contract.default_sla_policy_id,
            asset_criticality=asset.criticality if asset else None,
        )
        db.add(job)
        db.flush()

        db.add(
            PpmGenerationRecord(
                ppm_schedule_id=sched.id,
                due_anchor=anchor,
                job_id=job.id,
            )
        )

        sched.next_due_date = add_frequency(sched.next_due_date, sched.frequency_value, sched.frequency_unit)
        created.append(job.id)

    db.commit()
    return created, skipped_ids
