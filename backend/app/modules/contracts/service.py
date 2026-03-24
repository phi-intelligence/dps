from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset
from backend.app.modules.contracts.schemas import ContractCreateIn, ContractPatchIn
from backend.app.modules.contracts.models import Contract
from backend.app.modules.dispatch.models import Job


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def create_contract(db: Session, *, payload: ContractCreateIn) -> Contract:
    code = (payload.contract_code or "").strip() or f"C-{uuid.uuid4().hex[:8].upper()}"
    contract = Contract(
        customer_id=payload.customer_id,
        site_id=payload.site_id,
        name=payload.name,
        contract_code=code,
        contract_type=payload.contract_type,
        status=payload.status,
        term_start_at=payload.term_start_at,
        term_end_at=payload.term_end_at,
        renewal_review_date=payload.renewal_review_date,
        billing_frequency=payload.billing_frequency,
        contract_value=payload.contract_value,
        covered_assets_mode=payload.covered_assets_mode,
        covered_asset_ids_json=payload.covered_asset_ids_json or "[]",
        service_inclusions_json=payload.service_inclusions_json or "[]",
        exclusions_json=payload.exclusions_json or "[]",
        notes=payload.notes,
        default_sla_policy_id=payload.default_sla_policy_id,
        ppm_interval_days=payload.ppm_interval_days,
        next_ppm_due_at=payload.next_ppm_due_at,
        sla_response_minutes=payload.sla_response_minutes,
        sla_attendance_minutes=payload.sla_attendance_minutes,
        sla_completion_minutes=payload.sla_completion_minutes,
        communication_locale=(payload.communication_locale or None),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def get_contract(db: Session, *, contract_id: str) -> Contract | None:
    return db.get(Contract, contract_id)


def patch_contract(db: Session, *, contract_id: str, payload: ContractPatchIn) -> Contract:
    """Low-level field apply + commit. Prefer `apply_manual_contract_update_with_versioning` for API updates."""
    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


def list_contracts(db: Session) -> list[Contract]:
    return db.query(Contract).order_by(Contract.created_at.desc()).all()


def generate_due_ppm_jobs_for_contract(
    db: Session, *, contract_id: str, now: datetime | None = None
) -> list[str]:
    now = now or utc_now()
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    if contract.next_ppm_due_at and _to_utc_naive(contract.next_ppm_due_at) > _to_utc_naive(now):
        return []

    from backend.app.modules.assets.service import run_due_maintenance

    created_job_ids = run_due_maintenance(db, now=now, contract_id=contract_id)

    contract.next_ppm_due_at = contract.next_ppm_due_at + timedelta(days=int(contract.ppm_interval_days or 0))
    db.commit()
    return created_job_ids


def compute_sla_breach_risk(
    db: Session, *, job_id: str, now: datetime | None = None
) -> dict[str, object]:
    now = now or utc_now()
    now_naive = _to_utc_naive(now)
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    if not job.contract_id:
        return {
            "job_id": job_id,
            "contract_id": None,
            "risk_state": "on_track",
            "target_completion_at": None,
            "computed_at": now,
        }

    contract = db.get(Contract, job.contract_id)
    if not contract:
        return {
            "job_id": job_id,
            "contract_id": job.contract_id,
            "risk_state": "on_track",
            "target_completion_at": None,
            "computed_at": now,
        }

    start_at = job.scheduled_at or job.created_at
    start_at_naive = _to_utc_naive(start_at)
    target_completion_at = start_at_naive + timedelta(minutes=int(contract.sla_completion_minutes or 0))

    if job.status in {"completed", "closed"}:
        return {
            "job_id": job_id,
            "contract_id": contract.id,
            "risk_state": "on_track",
            "target_completion_at": target_completion_at,
            "computed_at": now,
        }

    if now_naive <= target_completion_at:
        risk_state: Literal["on_track", "at_risk", "breached"] = "on_track"
    elif now_naive <= target_completion_at + timedelta(minutes=60):
        risk_state = "at_risk"
    else:
        risk_state = "breached"

    return {
        "job_id": job_id,
        "contract_id": contract.id,
        "risk_state": risk_state,
        "target_completion_at": target_completion_at,
        "computed_at": now,
    }
