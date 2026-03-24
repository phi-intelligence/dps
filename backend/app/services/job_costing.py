"""
Job material costing (standard cost basis) + quote/reserved/actual variance.

Assumptions (documented):
- **Material cost** uses `StockItem.unit_cost` as standard cost unless extended later
  with explicit cost on usage/reservation rows.
- **Estimated material cost** = quote materials line quantity × standard cost for that SKU
  (not quote `unit_price`, which is customer sell).
- **Labour** uses ``labour_costing_service`` (``LabourRateProfile`` + punch segmentation +
  travel from job timestamps). Env rates remain fallback when no profile matches.
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.costing.models import JobCostSnapshot, JobCostSnapshotLine
from backend.app.modules.dispatch.models import Job, JobPartUsageLine
from backend.app.modules.inventory.models import StockItem, StockReservation
from backend.app.services.labour_costing_service import compute_job_labour_costing
from backend.app.modules.quoting.models import Quote, QuoteItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _cost_basis_for_item(item: StockItem | None) -> tuple[float, str | None]:
    """Return (unit_cost, warning_key if missing/zero)."""
    if not item:
        return 0.0, "missing_stock_item"
    c = float(item.unit_cost or 0.0)
    if c <= 1e-12:
        return 0.0, "zero_standard_cost"
    return c, None


def _quote_materials_by_sku(db: Session, *, quote_id: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    quote = db.get(Quote, quote_id)
    if not quote:
        return out
    for it in quote.items:
        if it.item_type != "materials":
            continue
        sku = (it.description or "").strip()
        if not sku:
            continue
        out[sku] = {
            "qty": float(it.quantity),
            "unit_sell": float(it.unit_price),
            "description": sku,
            "line_total_sell": float(it.line_total),
        }
    return out


def _reservations_by_sku(db: Session, *, quote_id: str) -> dict[str, float]:
    rows = (
        db.query(StockReservation)
        .filter(StockReservation.quote_id == quote_id, StockReservation.status == "reserved")
        .all()
    )
    acc: dict[str, float] = defaultdict(float)
    for r in rows:
        acc[(r.sku or "").strip()] += float(r.quantity)
    return dict(acc)


def _usage_aggregate_by_sku(db: Session, *, job_id: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    """sku -> total qty, sku -> list of match_status values (for warnings)."""
    lines = db.query(JobPartUsageLine).filter(JobPartUsageLine.job_id == job_id).all()
    qty: dict[str, float] = defaultdict(float)
    flags: dict[str, list[str]] = defaultdict(list)
    for ln in lines:
        item = db.get(StockItem, ln.stock_item_id)
        sku = item.sku if item else ""
        if not sku:
            continue
        qty[sku] += float(ln.quantity)
        flags[sku].append(ln.match_status)
    return dict(qty), {k: list(v) for k, v in flags.items()}


@dataclass
class CostingLineComputed:
    sku: str
    description: str
    stock_item_id: str | None
    estimated_qty: float
    reserved_qty: float
    actual_qty: float
    unit_cost_basis: float
    unit_sell_quote: float
    estimated_cost: float
    reserved_cost: float
    actual_cost: float
    billable_from_actual: float
    variance_flags: list[str] = field(default_factory=list)
    cost_basis_note: str | None = None


def compute_job_costing_lines(db: Session, *, job_id: str) -> tuple[list[CostingLineComputed], list[str], str]:
    """
    Returns (lines, global_warnings, costing_status).
    costing_status: clean | warning | needs_review
    """
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    warnings: list[str] = []
    quote_map = _quote_materials_by_sku(db, quote_id=job.quote_id) if job.quote_id else {}
    res_map = _reservations_by_sku(db, quote_id=job.quote_id) if job.quote_id else {}
    usage_qty, usage_flags = _usage_aggregate_by_sku(db, job_id=job_id)

    all_skus = sorted(set(quote_map.keys()) | set(res_map.keys()) | set(usage_qty.keys()))

    lines: list[CostingLineComputed] = []
    status_rank = {"clean": 0, "warning": 1, "needs_review": 2}
    roll = "clean"

    for sku in all_skus:
        qd = quote_map.get(sku, {})
        est_qty = float(qd.get("qty", 0.0))
        unit_sell = float(qd.get("unit_sell", 0.0))
        description = str(qd.get("description", sku))
        res_qty = float(res_map.get(sku, 0.0))
        act_qty = float(usage_qty.get(sku, 0.0))

        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        unit_cost, w = _cost_basis_for_item(item)
        if w:
            warnings.append(f"{sku}: {w}")
            if roll == "clean":
                roll = "warning"

        vf: list[str] = []
        for st in usage_flags.get(sku, []):
            if st in ("overused", "unreserved", "unavailable"):
                vf.append(st)
                roll = "needs_review"
            elif st == "matched":
                pass

        if est_qty > 0 and act_qty > 0 and abs(est_qty - act_qty) > 1e-6:
            vf.append("qty_variance_estimate_vs_actual")
        if res_qty > 0 and act_qty > 0 and abs(res_qty - act_qty) > 1e-6:
            vf.append("qty_variance_reserved_vs_actual")

        est_cost = round(est_qty * unit_cost, 4)
        res_cost = round(res_qty * unit_cost, 4)
        act_cost = round(act_qty * unit_cost, 4)
        billable = round(act_qty * unit_sell, 4) if act_qty > 0 and unit_sell > 0 else 0.0
        if act_qty > 0 and unit_sell <= 0 and sku in quote_map:
            # fallback: proportional sell from line if single materials line
            billable = round(float(qd.get("line_total_sell", 0.0)) * (act_qty / est_qty), 4) if est_qty > 0 else 0.0

        note = None
        if w == "zero_standard_cost":
            note = "Used StockItem.unit_cost=0; actual cost treated as 0"
        elif w == "missing_stock_item":
            note = "No StockItem for SKU"

        lines.append(
            CostingLineComputed(
                sku=sku,
                description=description,
                stock_item_id=item.id if item else None,
                estimated_qty=est_qty,
                reserved_qty=res_qty,
                actual_qty=act_qty,
                unit_cost_basis=unit_cost,
                unit_sell_quote=unit_sell,
                estimated_cost=est_cost,
                reserved_cost=res_cost,
                actual_cost=act_cost,
                billable_from_actual=billable,
                variance_flags=vf,
                cost_basis_note=note,
            )
        )

    for sku in usage_qty:
        if sku and sku not in quote_map:
            warnings.append(f"usage_without_quote_line:{sku}")
            roll = "needs_review"

    return lines, warnings, roll


def compute_job_costing_summary_dict(db: Session, *, job_id: str) -> dict[str, Any]:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    lines, warnings, costing_status = compute_job_costing_lines(db, job_id=job_id)

    est_c = sum(x.estimated_cost for x in lines)
    res_c = sum(x.reserved_cost for x in lines)
    act_c = sum(x.actual_cost for x in lines)
    est_q = sum(x.estimated_qty for x in lines)
    res_q = sum(x.reserved_qty for x in lines)
    act_q = sum(x.actual_qty for x in lines)

    var_est = round(act_c - est_c, 4)
    var_res = round(act_c - res_c, 4)
    billable = sum(x.billable_from_actual for x in lines)

    labour = compute_job_labour_costing(db, job_id=job_id)
    work_seconds = int(labour.get("labour_seconds") or 0)
    work_hours = float(labour.get("labour_hours") or 0.0)
    labour_cost = round(float(labour.get("labour_cost_total") or 0), 4)
    labour_overtime_cost = round(float(labour.get("overtime_cost") or 0), 4)
    travel_cost = round(float(labour.get("travel_cost") or 0), 4)
    labour_warnings = list(labour.get("warnings") or [])
    for lw in labour_warnings:
        warnings.append(f"labour:{lw}")

    if labour.get("labour_completeness_status") in ("partial", "fallback", "unavailable"):
        if costing_status == "clean":
            costing_status = "warning"

    currency = "GBP"
    if job.quote_id:
        q = db.get(Quote, job.quote_id)
        if q:
            currency = q.currency or currency

    return {
        "job_id": job_id,
        "currency": currency,
        "estimated_material_cost": round(est_c, 4),
        "reserved_material_cost": round(res_c, 4),
        "actual_material_cost": round(act_c, 4),
        "material_cost_variance_vs_estimate": var_est,
        "material_cost_variance_vs_reserved": var_res,
        "estimated_material_qty": round(est_q, 4),
        "reserved_material_qty": round(res_q, 4),
        "actual_material_qty": round(act_q, 4),
        "materials_billable_from_actual": round(billable, 4),
        "labour_seconds": work_seconds,
        "labour_hours": round(work_hours, 4),
        "labour_cost": labour_cost,
        "labour_overtime_cost": labour_overtime_cost,
        "labour_doubletime_cost": round(float(labour.get("doubletime_cost") or 0), 4),
        "labour_regular_cost": round(float(labour.get("regular_cost") or 0), 4),
        "labour_out_of_hours_cost": round(float(labour.get("out_of_hours_cost") or 0), 4),
        "travel_cost": travel_cost,
        "labour_completeness_status": labour.get("labour_completeness_status"),
        "labour_warnings": labour_warnings,
        "labour_rate_profile_id": labour.get("labour_rate_profile_id"),
        "labour_rate_profile_name": labour.get("labour_rate_profile_name"),
        "labour_cost_breakdown": labour.get("labour_cost_breakdown") or {},
        "labour_calculation_basis": labour.get("calculation_basis") or {},
        "labour_note": "Labour from LabourRateProfile + regional LabourRuleSet (when configured) with timezone/holiday-aware segmentation; else legacy UTC window.",
        "labour_rules_attribution": labour.get("labour_rules_attribution") or {},
        "rules_completeness_status": labour.get("rules_completeness_status"),
        "labour_detail": labour,
        "costing_warnings": warnings,
        "costing_status": costing_status,
        "lines": [
            {
                "sku": x.sku,
                "description": x.description,
                "stock_item_id": x.stock_item_id,
                "estimated_qty": x.estimated_qty,
                "reserved_qty": x.reserved_qty,
                "actual_qty": x.actual_qty,
                "unit_cost": x.unit_cost_basis,
                "unit_sell_quote": x.unit_sell_quote,
                "estimated_cost": x.estimated_cost,
                "reserved_cost": x.reserved_cost,
                "actual_cost": x.actual_cost,
                "billable_from_actual": x.billable_from_actual,
                "variance_flags": x.variance_flags,
                "cost_basis_note": x.cost_basis_note,
            }
            for x in lines
        ],
    }


def get_job_cost_snapshot(db: Session, *, job_id: str) -> JobCostSnapshot | None:
    return db.query(JobCostSnapshot).filter(JobCostSnapshot.job_id == job_id).one_or_none()


def persist_job_cost_snapshot(db: Session, *, job_id: str, commit: bool = True) -> JobCostSnapshot:
    """
    Persist costing snapshot for a job (typically once when status becomes `completed`).
    Idempotent: replaces existing snapshot for the same job_id.
    """
    summary = compute_job_costing_summary_dict(db, job_id=job_id)
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    existing = get_job_cost_snapshot(db, job_id=job_id)
    if existing:
        db.query(JobCostSnapshotLine).filter(JobCostSnapshotLine.snapshot_id == existing.id).delete()
        db.delete(existing)
        db.flush()

    lb: dict[str, Any] = summary.get("labour_detail") or {}
    snap = JobCostSnapshot(
        id=str(uuid.uuid4()),
        job_id=job_id,
        currency=summary["currency"],
        completed_at=utc_now(),
        estimated_material_cost=float(summary["estimated_material_cost"]),
        reserved_material_cost=float(summary["reserved_material_cost"]),
        actual_material_cost=float(summary["actual_material_cost"]),
        estimated_material_qty=float(summary["estimated_material_qty"]),
        reserved_material_qty=float(summary["reserved_material_qty"]),
        actual_material_qty=float(summary["actual_material_qty"]),
        material_cost_variance_vs_estimate=float(summary["material_cost_variance_vs_estimate"]),
        material_cost_variance_vs_reserved=float(summary["material_cost_variance_vs_reserved"]),
        labour_seconds=int(summary["labour_seconds"]),
        labour_hours=float(summary["labour_hours"]),
        labour_cost=float(summary["labour_cost"]),
        labour_overtime_cost=float(summary.get("labour_overtime_cost") or 0),
        travel_cost=float(summary.get("travel_cost") or 0),
        regular_labour_minutes=int(lb.get("regular_minutes") or 0),
        overtime_labour_minutes=int(lb.get("overtime_minutes") or 0),
        doubletime_labour_minutes=int(lb.get("doubletime_minutes") or 0),
        travel_labour_minutes=int(lb.get("travel_minutes") or 0),
        out_of_hours_labour_minutes=int(lb.get("out_of_hours_minutes") or 0),
        break_minutes_excluded=int(lb.get("break_minutes_excluded") or 0),
        regular_labour_cost=float(lb.get("regular_cost") or 0),
        doubletime_labour_cost=float(lb.get("doubletime_cost") or 0),
        out_of_hours_labour_cost=float(lb.get("out_of_hours_cost") or 0),
        labour_rate_profile_id=lb.get("labour_rate_profile_id"),
        labour_cost_warnings_json=json.dumps(lb.get("warnings") or []),
        labour_cost_completeness=str(lb.get("labour_completeness_status") or "unavailable"),
        labour_rule_set_id=(lb.get("labour_rules_attribution") or {}).get("labour_rule_set_id"),
        holiday_calendar_id=(lb.get("labour_rules_attribution") or {}).get("holiday_calendar_id"),
        labour_local_timezone_name=(lb.get("labour_rules_attribution") or {}).get("local_timezone_name"),
        labour_rules_completeness_status=lb.get("rules_completeness_status"),
        labour_rules_attribution_json=json.dumps(lb.get("labour_rules_attribution") or {}),
        costing_status=summary["costing_status"],
        warnings_json=json.dumps(summary["costing_warnings"]),
        materials_billable_total=float(summary["materials_billable_from_actual"]),
    )
    db.add(snap)
    db.flush()

    for row in summary["lines"]:
        db.add(
            JobCostSnapshotLine(
                id=str(uuid.uuid4()),
                snapshot_id=snap.id,
                sku=row["sku"],
                description=row["description"][:255],
                stock_item_id=row["stock_item_id"],
                estimated_qty=float(row["estimated_qty"]),
                reserved_qty=float(row["reserved_qty"]),
                actual_qty=float(row["actual_qty"]),
                unit_cost_basis=float(row["unit_cost"]),
                unit_sell_quote=float(row["unit_sell_quote"]),
                estimated_cost=float(row["estimated_cost"]),
                reserved_cost=float(row["reserved_cost"]),
                actual_cost=float(row["actual_cost"]),
                billable_from_actual=float(row["billable_from_actual"]),
                variance_flags_json=json.dumps(row["variance_flags"]),
                cost_basis_note=row.get("cost_basis_note"),
            )
        )
    if commit:
        db.commit()
        db.refresh(snap)
    else:
        db.flush()
    return snap


def costing_summary_from_snapshot(snap: JobCostSnapshot, lines: list[JobCostSnapshotLine]) -> dict[str, Any]:
    w = json.loads(snap.warnings_json or "[]")
    lw = json.loads(getattr(snap, "labour_cost_warnings_json", None) or "[]")
    breakdown = {
        "regular_minutes": getattr(snap, "regular_labour_minutes", 0) or 0,
        "overtime_minutes": getattr(snap, "overtime_labour_minutes", 0) or 0,
        "doubletime_minutes": getattr(snap, "doubletime_labour_minutes", 0) or 0,
        "travel_minutes": getattr(snap, "travel_labour_minutes", 0) or 0,
        "out_of_hours_minutes": getattr(snap, "out_of_hours_labour_minutes", 0) or 0,
        "regular_cost": float(getattr(snap, "regular_labour_cost", 0) or 0),
        "overtime_cost": float(snap.labour_overtime_cost or 0),
        "doubletime_cost": float(getattr(snap, "doubletime_labour_cost", 0) or 0),
        "travel_cost": float(snap.travel_cost or 0),
        "out_of_hours_cost": float(getattr(snap, "out_of_hours_labour_cost", 0) or 0),
        "labour_work_cost": float(snap.labour_cost or 0),
        "labour_plus_travel_cost": round(float(snap.labour_cost or 0) + float(snap.travel_cost or 0), 4),
    }
    return {
        "job_id": snap.job_id,
        "currency": snap.currency,
        "source": "snapshot",
        "estimated_material_cost": snap.estimated_material_cost,
        "reserved_material_cost": snap.reserved_material_cost,
        "actual_material_cost": snap.actual_material_cost,
        "material_cost_variance_vs_estimate": snap.material_cost_variance_vs_estimate,
        "material_cost_variance_vs_reserved": snap.material_cost_variance_vs_reserved,
        "estimated_material_qty": snap.estimated_material_qty,
        "reserved_material_qty": snap.reserved_material_qty,
        "actual_material_qty": snap.actual_material_qty,
        "materials_billable_from_actual": snap.materials_billable_total,
        "labour_seconds": snap.labour_seconds,
        "labour_hours": snap.labour_hours,
        "labour_cost": snap.labour_cost,
        "labour_overtime_cost": snap.labour_overtime_cost,
        "labour_doubletime_cost": float(getattr(snap, "doubletime_labour_cost", 0) or 0),
        "labour_regular_cost": float(getattr(snap, "regular_labour_cost", 0) or 0),
        "labour_out_of_hours_cost": float(getattr(snap, "out_of_hours_labour_cost", 0) or 0),
        "travel_cost": snap.travel_cost,
        "labour_completeness_status": getattr(snap, "labour_cost_completeness", None) or "unavailable",
        "labour_warnings": lw,
        "labour_rate_profile_id": getattr(snap, "labour_rate_profile_id", None),
        "labour_rate_profile_name": None,
        "labour_cost_breakdown": breakdown,
        "labour_calculation_basis": {"source": "snapshot_frozen"},
        "labour_note": "Frozen snapshot labour segmentation and costs.",
        "labour_rules_attribution": json.loads(getattr(snap, "labour_rules_attribution_json", None) or "{}"),
        "rules_completeness_status": getattr(snap, "labour_rules_completeness_status", None),
        "costing_warnings": w,
        "costing_status": snap.costing_status,
        "lines": [
            {
                "sku": ln.sku,
                "description": ln.description,
                "stock_item_id": ln.stock_item_id,
                "estimated_qty": ln.estimated_qty,
                "reserved_qty": ln.reserved_qty,
                "actual_qty": ln.actual_qty,
                "unit_cost": ln.unit_cost_basis,
                "unit_sell_quote": ln.unit_sell_quote,
                "estimated_cost": ln.estimated_cost,
                "reserved_cost": ln.reserved_cost,
                "actual_cost": ln.actual_cost,
                "billable_from_actual": ln.billable_from_actual,
                "variance_flags": json.loads(ln.variance_flags_json or "[]"),
                "cost_basis_note": ln.cost_basis_note,
            }
            for ln in lines
        ],
    }


def get_job_costing_for_api(db: Session, *, job_id: str, prefer_snapshot: bool = True) -> dict[str, Any]:
    if prefer_snapshot:
        snap = get_job_cost_snapshot(db, job_id=job_id)
        if snap:
            line_rows = (
                db.query(JobCostSnapshotLine).filter(JobCostSnapshotLine.snapshot_id == snap.id).order_by(JobCostSnapshotLine.sku.asc()).all()
            )
            return costing_summary_from_snapshot(snap, line_rows)
    d = compute_job_costing_summary_dict(db, job_id=job_id)
    d["source"] = "live"
    return d


def get_job_labour_costing_for_api(db: Session, *, job_id: str, prefer_snapshot: bool = True) -> dict[str, Any]:
    if prefer_snapshot:
        snap = get_job_cost_snapshot(db, job_id=job_id)
        if snap:
            line_rows = (
                db.query(JobCostSnapshotLine).filter(JobCostSnapshotLine.snapshot_id == snap.id).order_by(JobCostSnapshotLine.sku.asc()).all()
            )
            full = costing_summary_from_snapshot(snap, line_rows)
            return {
                "job_id": job_id,
                "source": "snapshot",
                "labour_completeness_status": full.get("labour_completeness_status"),
                "labour_warnings": list(full.get("labour_warnings") or []),
                "labour_rate_profile_id": full.get("labour_rate_profile_id"),
                "labour_rate_profile_name": full.get("labour_rate_profile_name"),
                "labour_cost_breakdown": dict(full.get("labour_cost_breakdown") or {}),
                "labour_calculation_basis": dict(full.get("labour_calculation_basis") or {}),
                "labour_rules_attribution": dict(full.get("labour_rules_attribution") or {}),
                "rules_completeness_status": full.get("rules_completeness_status"),
            }
    labour = compute_job_labour_costing(db, job_id=job_id)
    return {
        "job_id": job_id,
        "source": "live",
        "labour_completeness_status": labour.get("labour_completeness_status"),
        "labour_warnings": list(labour.get("warnings") or []),
        "labour_rate_profile_id": labour.get("labour_rate_profile_id"),
        "labour_rate_profile_name": labour.get("labour_rate_profile_name"),
        "labour_cost_breakdown": dict(labour.get("labour_cost_breakdown") or {}),
        "labour_calculation_basis": dict(labour.get("calculation_basis") or {}),
        "labour_rules_attribution": dict(labour.get("labour_rules_attribution") or {}),
        "rules_completeness_status": labour.get("rules_completeness_status"),
    }
