"""
Deterministic commercial / renewal recommendations from contract profitability intelligence.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

_log = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.contracts.models import Contract
from backend.app.services import contract_profitability_service as cps


def _top_site_burden(p: dict[str, Any]) -> dict[str, Any] | None:
    sites = [s for s in p.get("site_burden", []) if s.get("site_id")]
    if not sites:
        return None
    return max(sites, key=lambda x: x.get("total_cost", 0))


def _top_asset_burden(p: dict[str, Any]) -> dict[str, Any] | None:
    assets = [a for a in p.get("asset_burden", []) if a.get("asset_id")]
    if not assets:
        return None
    return max(assets, key=lambda x: (x.get("reactive_jobs", 0), x.get("total_cost", 0)))


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    from datetime import timezone

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def register_contract_commercial_recommendations(db: Session, active_keys: set[str], *, now: datetime) -> None:
    from backend.app.services import recommendation_engine as reng

    _register = reng._register
    window = "last_90_days"
    for c in db.query(Contract).filter(Contract.status == "active").all():
        try:
            p = cps.build_contract_profitability(db, contract_id=c.id, period_window=window, now=now)
        except Exception:
            _log.exception(
                "contract commercial recommendations: build_contract_profitability failed for contract %s",
                c.id,
            )
            continue

        m_pct = p["margin"]["gross_percent"]
        m_amt = p["margin"]["gross_amount"]
        health = p["health"]
        ren = p["renewal"]
        react = p["jobs"]["reactive_created_in_period"]
        plan = p["jobs"]["planned_created_in_period"]

        # Amount < 0 must trigger even when revenue is zero (margin % undefined).
        negative_margin = (m_amt is not None and m_amt < 0) or (m_pct is not None and m_pct < 0)
        if negative_margin:
            sev = "critical" if (m_pct is not None and m_pct < -12) or m_amt < -5000 else "high"
            top_site = _top_site_burden(p)
            top_asset = _top_asset_burden(p)
            key = f"commercial:negative-margin:{c.id}"
            pct_txt = f"{m_pct:.1f}%" if m_pct is not None else "n/a (no/zero invoiced revenue in window)"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="contract_negative_margin",
                category="contract_attention",
                severity=sev,
                confidence="high" if p["data_completeness"]["completed_jobs_missing_snapshot_in_period"] == 0 else "medium",
                title=f"Negative margin on contract {c.contract_code}",
                summary=f"Gross margin {pct_txt}, amount {m_amt} (invoiced vs snapshot costs, {window}).",
                detail={
                    "reasons": ["invoiced_revenue_below_recognized_costs_in_window"],
                    "current_value": {"margin_percent": m_pct, "margin_amount": m_amt, "window": window},
                    "top_site": top_site,
                    "top_asset": top_asset,
                    "suggested_action": "Commercial review, scope, pricing, or operational recovery plan.",
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
                related_site_id=top_site.get("site_id") if top_site else None,
                related_asset_id=top_asset.get("asset_id") if top_asset else None,
            )

        snaps = cps.list_snapshots(db, contract_id=c.id, period_window=window, limit=2)
        if len(snaps) >= 2:
            newer, older = snaps[0], snaps[1]
            if (
                newer.gross_margin_percent is not None
                and older.gross_margin_percent is not None
                and (older.gross_margin_percent - newer.gross_margin_percent) >= 12
            ):
                key = f"commercial:margin-deterioration:{c.id}"
                _register(
                    db,
                    active_keys=active_keys,
                    recommendation_key=key,
                    recommendation_type="contract_margin_deterioration",
                    category="contract_attention",
                    severity="high",
                    confidence="medium",
                    title=f"Margin deterioration on {c.contract_code}",
                    summary="Gross margin % dropped materially between last two stored snapshots.",
                    detail={
                        "reasons": ["snapshot_margin_percent_decline"],
                        "current_value": {
                            "older_margin_pct": older.gross_margin_percent,
                            "newer_margin_pct": newer.gross_margin_percent,
                        },
                        "suggested_action": "Validate costing completeness then reprice or reset scope.",
                    },
                    entity_type="contract",
                    entity_id=c.id,
                    related_contract_id=c.id,
                )

        if plan >= 1 and react >= 3 and (react / max(plan, 1)) >= 2.5:
            key = f"commercial:reactive-burden:{c.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="contract_high_reactive_burden",
                category="contract_attention",
                severity="medium",
                confidence="high",
                title=f"High reactive load vs planned on {c.contract_code}",
                summary=f"{react} reactive vs {plan} planned jobs in {window}.",
                detail={
                    "reasons": ["reactive_to_planned_ratio_elevated"],
                    "current_value": {"reactive": react, "planned": plan},
                    "suggested_action": "Asset reliability review, PPM effectiveness, or contract uplift.",
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
            )

        term = _aware(c.term_end_at)
        days_left = (term - _aware(now)).days if term and _aware(now) else 9999
        rw = int(getattr(settings, "PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS", 90))
        if days_left <= rw and (ren["renewal_risk_level"] == "high" or health["score"] < 45):
            key = f"commercial:renewal-risk:{c.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="contract_renewal_risk",
                category="contract_attention",
                severity="high",
                confidence="high",
                title=f"Renewal risk: {c.contract_code}",
                summary="Contract in renewal window with weak health or elevated risk signals.",
                detail={
                    "reasons": ren.get("renewal_reasons", []),
                    "current_value": {"health_score": health["score"], "days_to_term_end": days_left},
                    "suggested_action": "Executive renewal review; align SLA, price, and scope.",
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
            )

        if ren.get("renewal_opportunity_level") in ("medium", "high") and health["score"] >= 68:
            key = f"commercial:repricing-opportunity:{c.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="contract_repricing_opportunity",
                category="contract_attention",
                severity="low",
                confidence="medium",
                title=f"Repricing opportunity: {c.contract_code}",
                summary="Operationally solid contract with moderate margin — review pricing at renewal.",
                detail={
                    "reasons": ren.get("renewal_reasons", []),
                    "current_value": {"margin_percent": m_pct, "health_score": health["score"]},
                    "suggested_action": "Prepare uplift / indexation case for renewal discussion.",
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
            )

        sites = [s for s in p.get("site_burden", []) if s.get("site_id")]
        total_site_cost = sum(float(s.get("total_cost", 0) or 0) for s in sites)
        if total_site_cost > 500 and sites:
            top = max(sites, key=lambda x: x.get("total_cost", 0))
            if top.get("total_cost", 0) / total_site_cost >= 0.5:
                sid = top["site_id"]
                key = f"commercial:site-hotspot:{c.id}:{sid}"
                _register(
                    db,
                    active_keys=active_keys,
                    recommendation_key=key,
                    recommendation_type="contract_site_cost_hotspot",
                    category="contract_attention",
                    severity="medium",
                    confidence="high",
                    title=f"Site cost concentration on {c.contract_code}",
                    summary=f"One site absorbs ~{(top.get('total_cost', 0) / total_site_cost) * 100:.0f}% of recognized costs in window.",
                    detail={
                        "reasons": ["disproportionate_site_cost_share"],
                        "current_value": top,
                        "suggested_action": "Site walkdown, asset strategy, or local pricing adjustment.",
                    },
                    entity_type="site",
                    entity_id=sid,
                    related_contract_id=c.id,
                    related_site_id=sid,
                )

        for a in p.get("asset_burden", []):
            aid = a.get("asset_id")
            if not aid:
                continue
            if int(a.get("reactive_jobs", 0) or 0) >= 3:
                key = f"commercial:asset-hotspot:{c.id}:{aid}"
                _register(
                    db,
                    active_keys=active_keys,
                    recommendation_key=key,
                    recommendation_type="contract_asset_reactive_hotspot",
                    category="asset_attention",
                    severity="medium",
                    confidence="high",
                    title=f"Repeat reactive burden on asset under {c.contract_code}",
                    summary=f"{a.get('reactive_jobs')} reactive jobs in {window} with cost {a.get('total_cost')}.",
                    detail={
                        "reasons": ["reactive_job_count_threshold"],
                        "current_value": a,
                        "suggested_action": "Replace/refurb plan, warranty discussion, or PPM intensification.",
                    },
                    entity_type="asset",
                    entity_id=aid,
                    related_contract_id=c.id,
                    related_asset_id=aid,
                )
