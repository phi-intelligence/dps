from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.analytics.models import AnalyticsSnapshot
from backend.app.modules.dispatch.models import Job
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.time_tracking.models import Punch
from backend.app.modules.auth.models import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def etl_run(db: Session, *, snapshot_date: str) -> str:
    """
    Minimal ETL snapshot:
    - job status distribution
    - total revenue (sum invoices)
    - attendance: total punched seconds per engineer for snapshot_date
    """
    jobs = db.query(Job).all()
    jobs_by_status: dict[str, int] = {}
    for j in jobs:
        jobs_by_status[j.status] = jobs_by_status.get(j.status, 0) + 1

    invoices = db.query(Invoice).all()
    total_revenue = float(sum(float(i.grand_total) for i in invoices))

    # Attendance (simple): sum all punch-in/out durations is more correct via pairing,
    # but for a lightweight ETL we approximate via counting only 'in' and 'out' events.
    # We'll compute from paired punches using the get_timesheet service in a later phase.
    start = datetime.fromisoformat(snapshot_date).replace(tzinfo=timezone.utc)
    end = start.replace(hour=23, minute=59, second=59)

    punches = (
        db.query(Punch)
        .filter(Punch.occurred_at >= start, Punch.occurred_at <= end)
        .all()
    )

    attendance_seconds_by_engineer: dict[str, int] = {}
    # Approximate duration by counting events: treat every in/out pair as equal 0.5 hour baseline not accurate.
    # Instead, for now compute from pairing using naive stack per user in Python.
    open_in: dict[str, Punch] = {}
    for p in sorted(punches, key=lambda x: x.occurred_at):
        if p.kind == "in":
            open_in[p.user_id] = p
        elif p.kind == "out":
            in_p = open_in.get(p.user_id)
            if not in_p:
                continue
            dur = int((p.occurred_at - in_p.occurred_at).total_seconds())
            attendance_seconds_by_engineer[p.user_id] = attendance_seconds_by_engineer.get(p.user_id, 0) + max(dur, 0)
            open_in.pop(p.user_id, None)

    # Build dashboard payload.
    data = {
        "jobs_by_status": jobs_by_status,
        "total_revenue": round(total_revenue, 2),
        "attendance_seconds_by_engineer": attendance_seconds_by_engineer,
    }

    snap = AnalyticsSnapshot(snapshot_date=snapshot_date, data_json=json.dumps(data))
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap.id


def get_latest_dashboard(db: Session) -> AnalyticsSnapshot | None:
    return db.query(AnalyticsSnapshot).order_by(AnalyticsSnapshot.created_at.desc()).first()


def get_job_margin_summary(db: Session, *, job_id: str) -> dict:
    from backend.app.services.job_costing import compute_job_costing_summary_dict, get_job_cost_snapshot

    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    snap = get_job_cost_snapshot(db, job_id=job_id)
    inv = db.query(Invoice).filter(Invoice.job_id == job_id).order_by(Invoice.created_at.desc()).first()

    if snap:
        est = float(snap.estimated_material_cost)
        act = float(snap.actual_material_cost)
        var_amt = float(snap.material_cost_variance_vs_estimate)
        costing_status = snap.costing_status
        snapshot_id = snap.id
        unreconciled = costing_status == "needs_review"
    else:
        live = compute_job_costing_summary_dict(db, job_id=job_id)
        est = float(live["estimated_material_cost"])
        act = float(live["actual_material_cost"])
        var_amt = float(live["material_cost_variance_vs_estimate"])
        costing_status = str(live["costing_status"])
        snapshot_id = None
        unreconciled = costing_status == "needs_review"

    var_pct = round((var_amt / est) * 100.0, 2) if est > 1e-9 else None
    currency = "GBP"
    if job.quote_id:
        from backend.app.modules.quoting.models import Quote

        q = db.get(Quote, job.quote_id)
        if q:
            currency = q.currency or currency

    flags_extra = unreconciled
    if job.status == "completed" and not snap:
        flags_extra = True

    return {
        "job_id": job_id,
        "customer_id": job.customer_id,
        "currency": currency,
        "estimated_material_cost": round(est, 4),
        "actual_material_cost": round(act, 4),
        "variance_amount": round(var_amt, 4),
        "variance_percent": var_pct,
        "unreconciled_costing_flag": flags_extra,
        "invoice_generated_flag": inv is not None,
        "costing_status": costing_status,
        "snapshot_id": snapshot_id,
        "invoice_before_snapshot_flag": bool(inv and snap and inv.created_at < snap.completed_at),
    }


def list_job_cost_variance_rows(
    db: Session,
    *,
    job_status: str | None = "completed",
    limit: int = 50,
) -> list[dict]:
    from backend.app.services.job_costing import compute_job_costing_summary_dict, get_job_cost_snapshot

    q = db.query(Job).order_by(Job.created_at.desc())
    if job_status:
        q = q.filter(Job.status == job_status)
    jobs = q.limit(limit).all()
    out: list[dict] = []
    for job in jobs:
        snap = get_job_cost_snapshot(db, job_id=job.id)
        inv = db.query(Invoice).filter(Invoice.job_id == job.id).first()
        flags: list[str] = []
        if job.status == "completed" and not snap:
            flags.append("completed_without_snapshot")
        if snap and snap.costing_status == "needs_review":
            flags.append("costing_needs_review")
        if snap and float(snap.actual_material_cost) > float(snap.estimated_material_cost) + 1e-6:
            flags.append("actual_cost_exceeds_estimate")

        if snap:
            out.append(
                {
                    "job_id": job.id,
                    "customer_id": job.customer_id,
                    "job_status": job.status,
                    "estimated_material_cost": snap.estimated_material_cost,
                    "actual_material_cost": snap.actual_material_cost,
                    "variance_amount": snap.material_cost_variance_vs_estimate,
                    "costing_status": snap.costing_status,
                    "has_snapshot": True,
                    "invoice_id": inv.id if inv else None,
                    "flags": flags,
                }
            )
        else:
            live = compute_job_costing_summary_dict(db, job_id=job.id)
            if job.status == "completed" and inv and not snap:
                flags.append("invoice_without_snapshot_possible")
            out.append(
                {
                    "job_id": job.id,
                    "customer_id": job.customer_id,
                    "job_status": job.status,
                    "estimated_material_cost": live["estimated_material_cost"],
                    "actual_material_cost": live["actual_material_cost"],
                    "variance_amount": live["material_cost_variance_vs_estimate"],
                    "costing_status": live["costing_status"],
                    "has_snapshot": False,
                    "invoice_id": inv.id if inv else None,
                    "flags": flags,
                }
            )
    return out

