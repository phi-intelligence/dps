from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset
from backend.app.modules.contracts.models import Contract
from backend.app.modules.dispatch.models import Job
from backend.app.modules.sites.models import Site
from backend.app.modules.sites.service import site_full_address


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _contract_covers_asset(db: Session, *, contract: Contract, asset: Asset) -> bool:
    mode = (contract.covered_assets_mode or "all_assets").lower()
    if mode == "all_assets":
        if asset.customer_id != contract.customer_id:
            return False
        if contract.site_id:
            return asset.site_id == contract.site_id
        return asset.contract_id == contract.id
    try:
        ids = json.loads(contract.covered_asset_ids_json or "[]")
        if isinstance(ids, list):
            return asset.id in ids
    except Exception:
        pass
    return False


def _contract_active(contract: Contract, *, now: datetime) -> bool:
    if (contract.status or "").lower() != "active":
        return False
    n = _aware(now)
    if _aware(contract.term_start_at) > n:
        return False
    if contract.term_end_at and _aware(contract.term_end_at) < n:
        return False
    return True


def _pick_contract_for_asset(db: Session, *, asset: Asset, now: datetime) -> Contract | None:
    if asset.contract_id:
        c = db.get(Contract, asset.contract_id)
        if c and _contract_active(c, now=now) and _contract_covers_asset(db, contract=c, asset=asset):
            return c
    q = db.query(Contract).filter(Contract.customer_id == asset.customer_id, Contract.status == "active")
    best: Contract | None = None
    for c in q.all():
        if not _contract_active(c, now=now):
            continue
        if _contract_covers_asset(db, contract=c, asset=asset):
            best = c
            break
    return best


def apply_reactive_commercial_context(
    db: Session,
    *,
    job: Job,
    site_id: str | None = None,
    asset_id: str | None = None,
    contract_id: str | None = None,
    now: datetime | None = None,
) -> None:
    """
    Mutates `job` before persist. Resolves site/asset/contract/SLA for reactive work.
    """
    explicit_contract_id = contract_id
    now = now or utc_now()
    site: Site | None = None
    asset: Asset | None = None

    if asset_id:
        asset = db.get(Asset, asset_id)
        if asset:
            job.asset_id = asset.id
            if not site_id and asset.site_id:
                site_id = asset.site_id
            if not job.customer_id:
                job.customer_id = asset.customer_id

    if site_id:
        site = db.get(Site, site_id)
        if site:
            job.site_id = site.id
            if not job.customer_id:
                job.customer_id = site.customer_id
            if job.site_latitude is None and site.latitude is not None:
                job.site_latitude = site.latitude
            if job.site_longitude is None and site.longitude is not None:
                job.site_longitude = site.longitude
            if not (job.address or "").strip():
                job.address = site_full_address(site)

    contract: Contract | None = None
    if explicit_contract_id:
        contract = db.get(Contract, explicit_contract_id)
    elif asset:
        contract = _pick_contract_for_asset(db, asset=asset, now=now)
    elif site:
        q = (
            db.query(Contract)
            .filter(Contract.customer_id == site.customer_id, Contract.status == "active")
            .filter(or_(Contract.site_id == site.id, Contract.site_id.is_(None)))
        )
        for c in q.all():
            if _contract_active(c, now=now):
                contract = c
                break

    if contract and _contract_active(contract, now=now):
        job.contract_id = contract.id
        if asset:
            job.covered_under_contract = _contract_covers_asset(db, contract=contract, asset=asset)
        elif site:
            if contract.site_id and contract.site_id != site.id:
                job.covered_under_contract = False
            elif explicit_contract_id:
                job.covered_under_contract = True
            else:
                mode = (contract.covered_assets_mode or "all_assets").lower()
                job.covered_under_contract = mode == "all_assets"
        else:
            job.covered_under_contract = bool(explicit_contract_id)
        if contract.default_sla_policy_id:
            job.sla_policy_id = contract.default_sla_policy_id
            from backend.app.modules.sla.models import SlaPolicy

            pol = db.get(SlaPolicy, contract.default_sla_policy_id)
            if pol:
                job.sla_priority = pol.priority
                pri = (pol.priority or "").lower()
                boost = {"emergency": 10, "urgent": 7, "routine": 3, "planned": 1}.get(pri, 0)
                job.dispatch_priority = max(job.dispatch_priority or 0, boost)
        if asset and asset.required_competencies_json:
            try:
                cur = json.loads(job.required_competencies_json or "[]")
                add = json.loads(asset.required_competencies_json or "[]")
                if isinstance(cur, list) and isinstance(add, list):
                    merged = list({*map(str, cur), *map(str, add)})
                    job.required_competencies_json = json.dumps(merged)
            except Exception:
                pass
        if asset:
            job.asset_criticality = asset.criticality
            try:
                tags = json.loads(asset.compliance_tags_json or "[]")
                job.compliance_required = isinstance(tags, list) and len(tags) > 0
            except Exception:
                job.compliance_required = False
