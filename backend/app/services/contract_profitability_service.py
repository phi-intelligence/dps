"""
Contract-level commercial intelligence: profitability, burden, renewal signals, health score.
All calculations are deterministic from platform truth (jobs, invoices, snapshots, SLA, PPM, recommendations).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.assets.models import Asset
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.performance_models import ContractPerformanceSnapshot
from backend.app.modules.contracts.sla_clock_service import compute_job_sla_status
from backend.app.modules.costing.models import JobCostSnapshot
from backend.app.modules.dispatch.models import Job
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.ops.models import OperationalRecommendation
from backend.app.modules.ppm.models import PpmSchedule
from backend.app.modules.sites.models import Site


PERIOD_WINDOWS = ("last_30_days", "last_90_days", "year_to_date", "contract_lifetime")
DEFAULT_PERIOD = "last_90_days"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def resolve_period_bounds(
    contract: Contract, period_window: str, *, now: datetime | None = None
) -> tuple[datetime, datetime]:
    now = _aware(now or utc_now()) or utc_now()
    end = now
    if period_window == "last_30_days":
        start = end - timedelta(days=30)
    elif period_window == "last_90_days":
        start = end - timedelta(days=90)
    elif period_window == "year_to_date":
        start = datetime(end.year, 1, 1, tzinfo=timezone.utc)
    elif period_window == "contract_lifetime":
        ts = _aware(contract.term_start_at)
        start = ts if ts else end - timedelta(days=365 * 5)
    else:
        start = end - timedelta(days=90)
    return start, end


def _jobs_for_contract_in_period(
    db: Session, *, contract_id: str, start: datetime, end: datetime
) -> list[Job]:
    return (
        db.query(Job)
        .filter(
            Job.contract_id == contract_id,
            Job.created_at >= start,
            Job.created_at <= end,
        )
        .all()
    )


def _completed_jobs_resolved_in_period(
    db: Session, *, contract_id: str, start: datetime, end: datetime
) -> list[Job]:
    return (
        db.query(Job)
        .filter(
            Job.contract_id == contract_id,
            Job.status.in_(["completed", "closed"]),
            Job.resolved_at.isnot(None),
            Job.resolved_at >= start,
            Job.resolved_at <= end,
        )
        .all()
    )


def _invoices_for_contract_jobs(
    db: Session, *, contract_id: str, start: datetime | None, end: datetime | None
) -> list[tuple[Invoice, Job]]:
    q = (
        db.query(Invoice, Job)
        .join(Job, Invoice.job_id == Job.id)
        .filter(Job.contract_id == contract_id)
    )
    rows = q.all()
    if start is not None and end is not None:
        out = []
        for inv, job in rows:
            ic = _aware(inv.created_at) or inv.created_at
            if ic and start <= ic <= end:
                out.append((inv, job))
        return out
    return list(rows)


def build_contract_profitability(
    db: Session,
    *,
    contract_id: str,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Full profitability + operational metrics for one contract and window.
    """
    now = _aware(now or utc_now()) or utc_now()
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    start, end = resolve_period_bounds(contract, period_window, now=now)
    warnings: list[str] = []
    basis: dict[str, Any] = {
        "period_window": period_window,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "revenue_basis_primary": "invoiced",
        "revenue_basis_secondary": "paid",
        "cost_basis": "job_cost_snapshots",
        "margin_formula": "gross_margin_amount = revenue_invoiced_period - (material + labour_work + travel_labour)",
    }

    jobs_created = _jobs_for_contract_in_period(db, contract_id=contract_id, start=start, end=end)
    planned_job_count = sum(1 for j in jobs_created if (j.work_type or "") == "planned_maintenance")
    reactive_job_count = sum(1 for j in jobs_created if (j.work_type or "") == "reactive")
    completed_job_count = len(
        _completed_jobs_resolved_in_period(db, contract_id=contract_id, start=start, end=end)
    )

    inv_rows_period = _invoices_for_contract_jobs(db, contract_id=contract_id, start=start, end=end)
    revenue_invoiced = round(sum(float(inv.grand_total or 0) for inv, _ in inv_rows_period), 2)

    revenue_paid = 0.0
    for inv, _j in inv_rows_period:
        if inv.status == "paid" and inv.paid_at:
            pt = _aware(inv.paid_at)
            if pt and start <= pt <= end:
                revenue_paid += float(inv.grand_total or 0)
    revenue_paid = round(revenue_paid, 2)

    all_inv = _invoices_for_contract_jobs(db, contract_id=contract_id, start=None, end=None)
    revenue_unpaid = round(
        sum(float(inv.grand_total or 0) for inv, _ in all_inv if inv.status != "paid" or not inv.paid_at), 2
    )
    overdue_days = int(getattr(settings, "PHI_DPS_CONTRACT_OVERDUE_INVOICE_DAYS", 30))
    revenue_overdue = 0.0
    for inv, _ in all_inv:
        if inv.status == "paid":
            continue
        ic = _aware(inv.created_at) or inv.created_at
        if ic and (now - ic).days >= overdue_days:
            revenue_overdue += float(inv.grand_total or 0)
    revenue_overdue = round(revenue_overdue, 2)

    material_cost = 0.0
    labour_cost = 0.0
    travel_labour_cost = 0.0
    jobs_without_snapshot = 0
    completed_missing_snapshot = 0
    labour_comp_rank = {"complete": 0, "partial": 1, "fallback": 2, "unavailable": 3}
    worst_labour_completeness = "complete"
    rules_comp_rank = {"clean": 0, "partial": 1, "fallback": 2}
    worst_rules_completeness = "clean"
    ooh_labour_total = 0.0
    snapshots_without_rule_id = 0
    holiday_weekend_segment_jobs = 0

    cost_jobs = (
        db.query(Job, JobCostSnapshot)
        .join(JobCostSnapshot, JobCostSnapshot.job_id == Job.id)
        .filter(
            Job.contract_id == contract_id,
            JobCostSnapshot.completed_at >= start,
            JobCostSnapshot.completed_at <= end,
        )
        .all()
    )
    for _job, snap in cost_jobs:
        material_cost += float(snap.actual_material_cost or 0)
        labour_cost += float(snap.labour_cost or 0)
        travel_labour_cost += float(getattr(snap, "travel_cost", 0) or 0)
        lc = getattr(snap, "labour_cost_completeness", None) or "unavailable"
        if labour_comp_rank.get(lc, 1) > labour_comp_rank.get(worst_labour_completeness, 0):
            worst_labour_completeness = lc

    if cost_jobs and worst_labour_completeness != "complete":
        warnings.append(f"labour_costing_completeness:{worst_labour_completeness}")
    if cost_jobs and worst_rules_completeness != "clean":
        warnings.append(f"labour_rules_completeness:{worst_rules_completeness}")
    if cost_jobs and labour_cost > 1e-6 and (ooh_labour_total / labour_cost) > 0.35:
        warnings.append("high_out_of_hours_labour_share_in_period")
    if cost_jobs and snapshots_without_rule_id == len(cost_jobs):
        warnings.append("labour_rules:no_rule_set_attribution_on_snapshots_in_period")

    for j in _completed_jobs_resolved_in_period(db, contract_id=contract_id, start=start, end=end):
        snap = db.query(JobCostSnapshot).filter(JobCostSnapshot.job_id == j.id).first()
        if not snap:
            completed_missing_snapshot += 1
            warnings.append(f"completed_job_missing_cost_snapshot:{j.id}")

    all_contract_jobs = db.query(Job).filter(Job.contract_id == contract_id).all()
    for j in all_contract_jobs:
        if not db.query(JobCostSnapshot).filter(JobCostSnapshot.job_id == j.id).first():
            if j.status in ("completed", "closed"):
                jobs_without_snapshot += 1

    total_cost = round(material_cost + labour_cost + travel_labour_cost, 2)
    gross_margin_amount = round(revenue_invoiced - total_cost, 2)
    gross_margin_percent: float | None
    if revenue_invoiced > 1e-6:
        gross_margin_percent = round((gross_margin_amount / revenue_invoiced) * 100.0, 2)
    else:
        gross_margin_percent = None
        if total_cost > 0:
            warnings.append("no_invoiced_revenue_in_period_but_cost_recognized")

    overdue_ppm = (
        db.query(PpmSchedule)
        .filter(
            PpmSchedule.contract_id == contract_id,
            PpmSchedule.active.is_(True),
            PpmSchedule.next_due_date < now,
        )
        .count()
    )

    sla_breach_count = 0
    resp_vals: list[float] = []
    att_vals: list[float] = []
    res_vals: list[float] = []
    for j in jobs_created:
        st = compute_job_sla_status(db, job_id=j.id, now=now)
        if st.get("sla_status_summary") == "no_sla_context":
            continue
        if st.get("response_breached") or st.get("attendance_breached") or st.get("resolution_breached"):
            sla_breach_count += 1
        if st.get("response_time_minutes") is not None:
            resp_vals.append(float(st["response_time_minutes"]))
        if st.get("attendance_time_minutes") is not None:
            att_vals.append(float(st["attendance_time_minutes"]))
        if st.get("resolution_time_minutes") is not None:
            res_vals.append(float(st["resolution_time_minutes"]))

    open_recs = (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.related_contract_id == contract_id,
            OperationalRecommendation.status == "open",
        )
        .count()
    )

    cx_recs = (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.related_contract_id == contract_id,
            OperationalRecommendation.status == "open",
            OperationalRecommendation.category == "customer_experience_risk",
        )
        .count()
    )

    compliance_recent = (
        db.query(Certificate)
        .join(Job, Certificate.job_id == Job.id)
        .filter(Job.contract_id == contract_id, Certificate.created_at >= start, Certificate.created_at <= end)
        .count()
    )

    site_burden = _build_site_burden(db, contract_id=contract_id, start=start, end=end)
    asset_burden = _build_asset_burden(db, contract_id=contract_id, start=start, end=end)

    if completed_missing_snapshot:
        warnings.append("incomplete_costing:completed_jobs_without_snapshot_in_period")
        basis["cost_confidence"] = "partial"
    else:
        basis["cost_confidence"] = "high" if cost_jobs else "none"

    perf = {
        "contract_id": contract_id,
        "contract_code": contract.contract_code,
        "period_window": period_window,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "currency": "GBP",
        "contract_value": float(contract.contract_value or 0) if contract.contract_value else None,
        "revenue": {
            "invoiced_in_period": revenue_invoiced,
            "paid_in_period": revenue_paid,
            "unpaid_outstanding": revenue_unpaid,
            "overdue_outstanding": revenue_overdue,
        },
        "cost": {
            "material": round(material_cost, 2),
            "labour": round(labour_cost, 2),
            "travel_labour": round(travel_labour_cost, 2),
            "total": total_cost,
            "labour_completeness": worst_labour_completeness,
            "out_of_hours_labour": round(ooh_labour_total, 2),
        },
        "labour_rules": {
            "worst_completeness": worst_rules_completeness,
            "snapshots_in_period": len(cost_jobs),
            "snapshots_without_rule_set_id": snapshots_without_rule_id,
            "jobs_with_holiday_or_weekend_segments": holiday_weekend_segment_jobs,
            "ooh_labour_to_total_labour_ratio": round(ooh_labour_total / labour_cost, 4)
            if labour_cost > 1e-6
            else None,
        },
        "margin": {
            "gross_amount": gross_margin_amount,
            "gross_percent": gross_margin_percent,
            "basis_revenue": "invoiced_in_period",
        },
        "jobs": {
            "planned_created_in_period": planned_job_count,
            "reactive_created_in_period": reactive_job_count,
            "completed_resolved_in_period": completed_job_count,
        },
        "operational": {
            "overdue_ppm_count": int(overdue_ppm or 0),
            "sla_breach_count_jobs_in_period": sla_breach_count,
            "open_recommendation_count": open_recs,
            "customer_experience_open_recommendations": cx_recs,
            "certificates_created_in_period": compliance_recent,
        },
        "sla_averages": {
            "avg_response_minutes": round(sum(resp_vals) / len(resp_vals), 2) if resp_vals else None,
            "avg_attendance_minutes": round(sum(att_vals) / len(att_vals), 2) if att_vals else None,
            "avg_resolution_minutes": round(sum(res_vals) / len(res_vals), 2) if res_vals else None,
        },
        "data_completeness": {
            "jobs_without_cost_snapshot_total": jobs_without_snapshot,
            "completed_jobs_missing_snapshot_in_period": completed_missing_snapshot,
            "labour_costing_worst": worst_labour_completeness,
        },
        "site_burden": site_burden,
        "asset_burden": asset_burden,
        "warnings": warnings,
        "calculation_basis": basis,
    }

    health = _compute_health_score(perf, contract, now=now)
    perf["health"] = health

    renewal = _compute_renewal_intelligence(perf, contract, health, now=now)
    perf["renewal"] = renewal

    return perf


def _build_site_burden(
    db: Session, *, contract_id: str, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    by_site: dict[str, dict[str, Any]] = {}
    rows = (
        db.query(Job, JobCostSnapshot)
        .outerjoin(JobCostSnapshot, JobCostSnapshot.job_id == Job.id)
        .filter(
            Job.contract_id == contract_id,
            Job.created_at >= start,
            Job.created_at <= end,
        )
        .all()
    )
    for job, snap in rows:
        sid = job.site_id or "_none"
        if sid not in by_site:
            by_site[sid] = {
                "site_id": None if sid == "_none" else sid,
                "reactive_jobs": 0,
                "planned_jobs": 0,
                "material_cost": 0.0,
                "labour_cost": 0.0,
                "travel_cost": 0.0,
            }
        b = by_site[sid]
        if (job.work_type or "") == "reactive":
            b["reactive_jobs"] += 1
        else:
            b["planned_jobs"] += 1
        if snap:
            b["material_cost"] += float(snap.actual_material_cost or 0)
            b["labour_cost"] += float(snap.labour_cost or 0)
            b["travel_cost"] += float(getattr(snap, "travel_cost", 0) or 0)
    for b in by_site.values():
        b["total_cost"] = round(
            b["material_cost"] + b["labour_cost"] + float(b.get("travel_cost", 0) or 0),
            2,
        )
        pj, rj = b["planned_jobs"], b["reactive_jobs"]
        b["reactive_to_planned_ratio"] = round(rj / max(pj, 1), 3)
    ranked = sorted(by_site.values(), key=lambda x: x["total_cost"], reverse=True)
    for r in ranked[:20]:
        if r.get("site_id"):
            s = db.get(Site, r["site_id"])
            r["site_name"] = s.name if s else None
    return ranked[:50]


def _build_asset_burden(
    db: Session, *, contract_id: str, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    by_asset: dict[str, dict[str, Any]] = {}
    rows = (
        db.query(Job, JobCostSnapshot)
        .outerjoin(JobCostSnapshot, JobCostSnapshot.job_id == Job.id)
        .filter(
            Job.contract_id == contract_id,
            Job.created_at >= start,
            Job.created_at <= end,
        )
        .all()
    )
    for job, snap in rows:
        aid = job.asset_id or "_none"
        if aid not in by_asset:
            by_asset[aid] = {
                "asset_id": None if aid == "_none" else aid,
                "reactive_jobs": 0,
                "repeat_fault_proxy": 0,
                "material_cost": 0.0,
                "labour_cost": 0.0,
                "travel_cost": 0.0,
            }
        b = by_asset[aid]
        if (job.work_type or "") == "reactive":
            b["reactive_jobs"] += 1
            b["repeat_fault_proxy"] += 1
        if snap:
            b["material_cost"] += float(snap.actual_material_cost or 0)
            b["labour_cost"] += float(snap.labour_cost or 0)
            b["travel_cost"] += float(getattr(snap, "travel_cost", 0) or 0)
    for b in by_asset.values():
        b["total_cost"] = round(
            b["material_cost"] + b["labour_cost"] + float(b.get("travel_cost", 0) or 0),
            2,
        )
    ranked = sorted(by_asset.values(), key=lambda x: (x["reactive_jobs"], x["total_cost"]), reverse=True)
    for r in ranked[:30]:
        if r.get("asset_id"):
            a = db.get(Asset, r["asset_id"])
            r["asset_name"] = a.name if a else None
    return ranked[:50]


def _compute_health_score(perf: dict[str, Any], contract: Contract, *, now: datetime) -> dict[str, Any]:
    components: dict[str, float] = {}
    score = 0.0

    m_pct = perf["margin"]["gross_percent"]
    if m_pct is None:
        components["margin"] = 10.0
        score += 10
    elif m_pct >= 25:
        components["margin"] = 25.0
        score += 25
    elif m_pct >= 10:
        components["margin"] = 18.0
        score += 18
    elif m_pct >= 0:
        components["margin"] = 10.0
        score += 10
    else:
        components["margin"] = 0.0

    jn = max(perf["jobs"]["planned_created_in_period"] + perf["jobs"]["reactive_created_in_period"], 1)
    br = perf["operational"]["sla_breach_count_jobs_in_period"]
    sla_score = max(0.0, 20.0 - min(20.0, (br / jn) * 40))
    components["sla"] = round(sla_score, 2)
    score += sla_score

    react = perf["jobs"]["reactive_created_in_period"]
    plan = perf["jobs"]["planned_created_in_period"]
    ratio = react / max(plan + react + 1, 1)
    burden_score = max(0.0, 15.0 - min(15.0, ratio * 20))
    components["reactive_burden"] = round(burden_score, 2)
    score += burden_score

    od = perf["operational"]["overdue_ppm_count"]
    ppm_pen = min(15.0, od * 3.0)
    components["ppm"] = max(0.0, 15.0 - ppm_pen)
    score += components["ppm"]

    unpaid = perf["revenue"]["unpaid_outstanding"]
    inv = perf["revenue"]["invoiced_in_period"] or 1
    pay_score = max(0.0, 10.0 - min(10.0, (unpaid / max(inv, 1)) * 5))
    components["payment"] = round(pay_score, 2)
    score += pay_score

    orc = perf["operational"]["open_recommendation_count"]
    rec_pen = min(10.0, orc * 2.0)
    components["recommendations"] = max(0.0, 10.0 - rec_pen)
    score += components["recommendations"]

    term = _aware(contract.term_end_at)
    if term:
        days = (term - now).days
        if days < 0:
            components["expiry"] = 0.0
        elif days <= 30:
            components["expiry"] = 3.0
        elif days <= 90:
            components["expiry"] = 7.0
        else:
            components["expiry"] = 10.0
    else:
        components["expiry"] = 10.0
    score += components["expiry"]

    score_i = int(max(0, min(100, round(score))))
    if score_i >= 75:
        status = "healthy"
    elif score_i >= 55:
        status = "watch"
    elif score_i >= 35:
        status = "risk"
    else:
        status = "critical"

    return {"score": score_i, "status": status, "components": components}


def _compute_renewal_intelligence(
    perf: dict[str, Any], contract: Contract, health: dict[str, Any], *, now: datetime
) -> dict[str, Any]:
    reasons: list[str] = []
    risk = "low"
    opportunity = "low"
    status = "stable"

    term = _aware(contract.term_end_at)
    days_to_end = (term - now).days if term else 9999
    review_window = int(getattr(settings, "PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS", 90))
    review_due = bool(term and days_to_end <= review_window)

    if health["score"] < 40:
        risk = "high"
        reasons.append("low_health_score")
    elif health["score"] < 60:
        risk = "medium"
        reasons.append("health_watch")

    m = perf["margin"]["gross_percent"]
    if m is not None and m < 0:
        risk = "high"
        reasons.append("negative_margin")
    elif m is not None and m < 8:
        risk = "medium" if risk == "low" else risk
        reasons.append("thin_margin")

    if perf["operational"]["overdue_ppm_count"] >= 2:
        reasons.append("overdue_ppm")
        risk = "high" if risk == "low" else risk

    if perf["operational"]["sla_breach_count_jobs_in_period"] >= 3:
        reasons.append("sla_breaches_elevated")

    if perf["revenue"]["overdue_outstanding"] > 0 and perf["revenue"]["overdue_outstanding"] > perf["revenue"]["paid_in_period"]:
        reasons.append("payment_discipline_weak")

    if perf["operational"]["customer_experience_open_recommendations"] >= 2:
        reasons.append("customer_experience_risks_open")

    if days_to_end <= 60 and health["score"] < 55:
        status = "at_risk"
        reasons.append("expiry_proximity_with_weak_health")

    if health["score"] >= 70 and m is not None and 5 <= m <= 15 and perf["jobs"]["reactive_created_in_period"] < perf["jobs"]["planned_created_in_period"]:
        opportunity = "medium"
        reasons.append("stable_ops_moderate_margin_repricing_candidate")

    if health["score"] >= 80 and m is not None and m > 20:
        opportunity = "high"
        reasons.append("strong_performance_renewal_uplift_potential")

    if review_due and risk in ("high", "medium"):
        status = "review_required"

    return {
        "renewal_status": status,
        "renewal_risk_level": risk,
        "renewal_opportunity_level": opportunity,
        "renewal_reasons": reasons,
        "review_due": review_due,
        "days_to_term_end": days_to_end if term else None,
    }


def persist_performance_snapshot(
    db: Session,
    *,
    contract_id: str,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
) -> ContractPerformanceSnapshot:
    perf = build_contract_profitability(db, contract_id=contract_id, period_window=period_window, now=now)
    now = _aware(now or utc_now()) or utc_now()
    contract = db.get(Contract, contract_id)
    health = perf["health"]
    renewal = perf["renewal"]

    row = ContractPerformanceSnapshot(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        period_window=period_window,
        snapshot_at=now,
        currency="GBP",
        contract_value_at_snapshot=float(contract.contract_value) if contract and contract.contract_value else None,
        revenue_invoiced=perf["revenue"]["invoiced_in_period"],
        revenue_paid=perf["revenue"]["paid_in_period"],
        revenue_unpaid=perf["revenue"]["unpaid_outstanding"],
        revenue_overdue=perf["revenue"]["overdue_outstanding"],
        material_cost=perf["cost"]["material"],
        labour_cost=perf["cost"]["labour"],
        total_cost=perf["cost"]["total"],
        gross_margin_amount=perf["margin"]["gross_amount"],
        gross_margin_percent=perf["margin"]["gross_percent"],
        planned_job_count=perf["jobs"]["planned_created_in_period"],
        reactive_job_count=perf["jobs"]["reactive_created_in_period"],
        completed_job_count=perf["jobs"]["completed_resolved_in_period"],
        overdue_ppm_count=perf["operational"]["overdue_ppm_count"],
        sla_breach_count=perf["operational"]["sla_breach_count_jobs_in_period"],
        open_recommendation_count=perf["operational"]["open_recommendation_count"],
        jobs_without_costing_snapshot=perf["data_completeness"]["jobs_without_cost_snapshot_total"],
        completed_jobs_missing_snapshot=perf["data_completeness"]["completed_jobs_missing_snapshot_in_period"],
        health_score=health["score"],
        health_status=health["status"],
        renewal_status=renewal["renewal_status"],
        renewal_risk_level=renewal["renewal_risk_level"],
        renewal_opportunity_level=renewal["renewal_opportunity_level"],
        renewal_review_due=1 if renewal["review_due"] else 0,
        avg_response_minutes=perf["sla_averages"]["avg_response_minutes"],
        avg_attendance_minutes=perf["sla_averages"]["avg_attendance_minutes"],
        avg_resolution_minutes=perf["sla_averages"]["avg_resolution_minutes"],
        warnings_json=json.dumps(perf["warnings"]),
        calculation_basis_json=json.dumps(perf["calculation_basis"]),
        renewal_reasons_json=json.dumps(renewal["renewal_reasons"]),
        health_components_json=json.dumps(health["components"]),
        site_burden_json=json.dumps(perf["site_burden"]),
        asset_burden_json=json.dumps(perf["asset_burden"]),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_latest_snapshot(
    db: Session, *, contract_id: str, period_window: str
) -> ContractPerformanceSnapshot | None:
    return (
        db.query(ContractPerformanceSnapshot)
        .filter(
            ContractPerformanceSnapshot.contract_id == contract_id,
            ContractPerformanceSnapshot.period_window == period_window,
        )
        .order_by(ContractPerformanceSnapshot.snapshot_at.desc())
        .first()
    )


def list_snapshots(
    db: Session, *, contract_id: str, period_window: str | None = None, limit: int = 20
) -> list[ContractPerformanceSnapshot]:
    q = db.query(ContractPerformanceSnapshot).filter(ContractPerformanceSnapshot.contract_id == contract_id)
    if period_window:
        q = q.filter(ContractPerformanceSnapshot.period_window == period_window)
    return q.order_by(ContractPerformanceSnapshot.snapshot_at.desc()).limit(limit).all()


def run_snapshots_all_active(
    db: Session, *, period_window: str = DEFAULT_PERIOD, now: datetime | None = None
) -> dict[str, Any]:
    now = _aware(now or utc_now()) or utc_now()
    ids = [c.id for c in db.query(Contract).filter(Contract.status == "active").all()]
    created = []
    for cid in ids:
        try:
            created.append(persist_performance_snapshot(db, contract_id=cid, period_window=period_window, now=now).id)
        except Exception:
            continue
    return {"snapshots_created": len(created), "contract_ids_processed": len(ids)}


def dashboard_profitability(
    db: Session,
    *,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    now = _aware(now or utc_now()) or utc_now()
    rows: list[dict[str, Any]] = []
    for c in db.query(Contract).filter(Contract.status == "active").all():
        try:
            p = build_contract_profitability(db, contract_id=c.id, period_window=period_window, now=now)
            rows.append(
                {
                    "contract_id": c.id,
                    "contract_code": c.contract_code,
                    "name": c.name,
                    "margin_percent": p["margin"]["gross_percent"],
                    "margin_amount": p["margin"]["gross_amount"],
                    "reactive_jobs": p["jobs"]["reactive_created_in_period"],
                    "planned_jobs": p["jobs"]["planned_created_in_period"],
                    "health_status": p["health"]["status"],
                    "health_score": p["health"]["score"],
                    "renewal_risk_level": p["renewal"]["renewal_risk_level"],
                }
            )
        except Exception:
            continue
    lowest_margin = sorted(
        [r for r in rows if r["margin_percent"] is not None],
        key=lambda x: (x["margin_percent"] or 0, x["margin_amount"] or 0),
    )[:limit]
    highest_margin = sorted(
        [r for r in rows if r["margin_percent"] is not None],
        key=lambda x: (-(x["margin_percent"] or 0), -(x["margin_amount"] or 0)),
    )[:limit]
    highest_reactive = sorted(rows, key=lambda x: x["reactive_jobs"], reverse=True)[:limit]
    return {
        "period_window": period_window,
        "lowest_margin_contracts": lowest_margin,
        "highest_margin_contracts": highest_margin,
        "highest_reactive_burden": highest_reactive,
        "totals_contracts_considered": len(rows),
    }


def dashboard_renewals(
    db: Session,
    *,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    now = _aware(now or utc_now()) or utc_now()
    at_risk: list[dict[str, Any]] = []
    review_due: list[dict[str, Any]] = []
    for c in db.query(Contract).filter(Contract.status == "active").all():
        try:
            p = build_contract_profitability(db, contract_id=c.id, period_window=period_window, now=now)
            r = p["renewal"]
            h = p["health"]
            entry = {
                "contract_id": c.id,
                "contract_code": c.contract_code,
                "name": c.name,
                "renewal_status": r["renewal_status"],
                "renewal_risk_level": r["renewal_risk_level"],
                "renewal_opportunity_level": r["renewal_opportunity_level"],
                "review_due": r["review_due"],
                "days_to_term_end": r["days_to_term_end"],
                "health_score": h["score"],
                "renewal_reasons": r["renewal_reasons"],
            }
            if r["renewal_risk_level"] in ("high", "medium") or r["renewal_status"] in ("at_risk", "review_required"):
                at_risk.append(entry)
            if r["review_due"]:
                review_due.append(entry)
        except Exception:
            continue
    at_risk.sort(key=lambda x: (x["renewal_risk_level"] != "high", -(x["health_score"] or 0)))
    return {
        "period_window": period_window,
        "at_risk_renewals": at_risk[:limit],
        "contracts_with_review_due": review_due[:limit],
    }


def dashboard_attention_summary(
    db: Session,
    *,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    now = _aware(now or utc_now()) or utc_now()
    prof = dashboard_profitability(db, period_window=period_window, now=now, limit=limit)
    ren = dashboard_renewals(db, period_window=period_window, now=now, limit=limit)
    ppm_list: list[dict[str, Any]] = []
    sla_list: list[dict[str, Any]] = []
    for c in db.query(Contract).filter(Contract.status == "active").all():
        p = build_contract_profitability(db, contract_id=c.id, period_window=period_window, now=now)
        if p["operational"]["overdue_ppm_count"] > 0:
            ppm_list.append(
                {
                    "contract_id": c.id,
                    "contract_code": c.contract_code,
                    "overdue_ppm_count": p["operational"]["overdue_ppm_count"],
                }
            )
        if p["operational"]["sla_breach_count_jobs_in_period"] >= 2:
            sla_list.append(
                {
                    "contract_id": c.id,
                    "contract_code": c.contract_code,
                    "sla_breach_count": p["operational"]["sla_breach_count_jobs_in_period"],
                }
            )
    ppm_list.sort(key=lambda x: x["overdue_ppm_count"], reverse=True)
    sla_list.sort(key=lambda x: x["sla_breach_count"], reverse=True)
    return {
        "period_window": period_window,
        "profitability_highlights": {
            "lowest_margin": prof["lowest_margin_contracts"][:10],
            "highest_reactive": prof["highest_reactive_burden"][:10],
        },
        "renewal_highlights": {
            "at_risk": ren["at_risk_renewals"][:10],
            "review_due": ren["contracts_with_review_due"][:10],
        },
        "overdue_ppm_contracts": ppm_list[:limit],
        "sla_breach_contracts": sla_list[:limit],
    }


def contract_labour_summary(
    db: Session,
    *,
    contract_id: str,
    period_window: str = DEFAULT_PERIOD,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Aggregated labour + travel labour from job cost snapshots in the contract window.
    """
    if period_window not in PERIOD_WINDOWS:
        raise ValueError("Invalid period_window")
    p = build_contract_profitability(db, contract_id=contract_id, period_window=period_window, now=now)
    lw = p["cost"]["labour"]
    tw = p["cost"]["travel_labour"]
    return {
        "contract_id": contract_id,
        "period_window": period_window,
        "labour_work_cost": lw,
        "travel_labour_cost": tw,
        "labour_plus_travel_cost": round(lw + tw, 2),
        "labour_completeness_worst": p["cost"]["labour_completeness"],
        "warnings": [w for w in p.get("warnings", []) if "labour" in w],
        "calculation_basis": {
            "source": "job_cost_snapshots_in_period",
            "aligned_with": "contract_profitability.cost",
        },
    }


def snapshot_to_api_dict(row: ContractPerformanceSnapshot) -> dict[str, Any]:
    return {
        "id": row.id,
        "contract_id": row.contract_id,
        "period_window": row.period_window,
        "snapshot_at": row.snapshot_at.isoformat(),
        "currency": row.currency,
        "contract_value_at_snapshot": row.contract_value_at_snapshot,
        "revenue_invoiced": row.revenue_invoiced,
        "revenue_paid": row.revenue_paid,
        "revenue_unpaid": row.revenue_unpaid,
        "revenue_overdue": row.revenue_overdue,
        "material_cost": row.material_cost,
        "labour_cost": row.labour_cost,
        "total_cost": row.total_cost,
        "gross_margin_amount": row.gross_margin_amount,
        "gross_margin_percent": row.gross_margin_percent,
        "planned_job_count": row.planned_job_count,
        "reactive_job_count": row.reactive_job_count,
        "completed_job_count": row.completed_job_count,
        "overdue_ppm_count": row.overdue_ppm_count,
        "sla_breach_count": row.sla_breach_count,
        "open_recommendation_count": row.open_recommendation_count,
        "health_score": row.health_score,
        "health_status": row.health_status,
        "renewal_status": row.renewal_status,
        "renewal_risk_level": row.renewal_risk_level,
        "renewal_opportunity_level": row.renewal_opportunity_level,
        "renewal_review_due": bool(row.renewal_review_due),
        "warnings": json.loads(row.warnings_json or "[]"),
        "calculation_basis": json.loads(row.calculation_basis_json or "{}"),
        "renewal_reasons": json.loads(row.renewal_reasons_json or "[]"),
        "health_components": json.loads(row.health_components_json or "{}"),
        "site_burden": json.loads(row.site_burden_json or "[]"),
        "asset_burden": json.loads(row.asset_burden_json or "[]"),
    }
