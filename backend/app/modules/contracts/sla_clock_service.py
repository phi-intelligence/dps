from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.dispatch.models import Job
from backend.app.modules.sla.models import SlaPolicy


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    return (_aware(end) - _aware(start)).total_seconds() / 60.0


def resolve_sla_targets_for_job(db: Session, *, job: Job) -> tuple[int, int, int] | None:
    if job.sla_policy_id:
        p = db.get(SlaPolicy, job.sla_policy_id)
        if p:
            return (p.response_target_minutes, p.attendance_target_minutes, p.resolution_target_minutes)
    if job.contract_id:
        c = db.get(Contract, job.contract_id)
        if not c:
            return None
        if c.default_sla_policy_id:
            p = db.get(SlaPolicy, c.default_sla_policy_id)
            if p:
                return (p.response_target_minutes, p.attendance_target_minutes, p.resolution_target_minutes)
        return (c.sla_response_minutes, c.sla_attendance_minutes, c.sla_completion_minutes)
    return None


def _warning_level(
    elapsed: float | None, target: int | None, thresholds: dict[str, Any], *, key: str
) -> bool:
    if elapsed is None or not target or target <= 0:
        return False
    pct = (elapsed / target) * 100.0
    warn_at = 80.0
    if isinstance(thresholds, dict):
        raw = thresholds.get(key) or thresholds.get("default")
        if raw is not None:
            try:
                warn_at = float(raw)
            except (TypeError, ValueError):
                pass
    return pct >= warn_at


def compute_job_sla_status(db: Session, *, job_id: str, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    targets = resolve_sla_targets_for_job(db, job=job)
    if not targets:
        return {
            "job_id": job_id,
            "response_time_minutes": None,
            "attendance_time_minutes": None,
            "resolution_time_minutes": None,
            "response_breached": False,
            "attendance_breached": False,
            "resolution_breached": False,
            "warning_state": "none",
            "sla_status_summary": "no_sla_context",
            "computed_at": now,
        }

    resp_t, att_t, res_t = targets
    pol = db.get(SlaPolicy, job.sla_policy_id) if job.sla_policy_id else None
    thresholds: dict[str, Any] = {}
    if pol:
        try:
            thresholds = json.loads(pol.warning_threshold_percent_json or "{}")
            if not isinstance(thresholds, dict):
                thresholds = {}
        except Exception:
            thresholds = {}

    created = job.created_at
    response_end = job.acknowledged_at or job.dispatched_at
    attendance_end = job.on_site_at
    resolution_end = job.resolved_at

    response_minutes = _minutes_between(created, response_end) if response_end else _minutes_between(created, now)
    attendance_minutes = (
        _minutes_between(created, attendance_end) if attendance_end else _minutes_between(created, now)
    )
    resolution_minutes = (
        _minutes_between(created, resolution_end) if resolution_end else _minutes_between(created, now)
    )

    resp_b = response_minutes is not None and response_minutes > resp_t
    att_b = attendance_minutes is not None and attendance_minutes > att_t
    res_b = resolution_minutes is not None and resolution_minutes > res_t

    warn = "none"
    if _warning_level(attendance_minutes, att_t, thresholds, key="attendance"):
        warn = "attendance_warning"
    if _warning_level(response_minutes, resp_t, thresholds, key="response"):
        warn = "response_warning"

    parts = []
    if resp_b:
        parts.append("response_breach")
    if att_b:
        parts.append("attendance_breach")
    if res_b:
        parts.append("resolution_breach")
    summary = ",".join(parts) if parts else "within_targets"

    return {
        "job_id": job_id,
        "response_time_minutes": response_minutes,
        "attendance_time_minutes": attendance_minutes,
        "resolution_time_minutes": resolution_minutes,
        "response_breached": resp_b,
        "attendance_breached": att_b,
        "resolution_breached": res_b,
        "warning_state": warn,
        "sla_status_summary": summary,
        "computed_at": now,
    }


def aggregate_contract_sla_performance(db: Session, *, contract_id: str) -> dict[str, Any]:
    jobs = db.query(Job).filter(Job.contract_id == contract_id).all()
    breached = 0
    for j in jobs:
        st = compute_job_sla_status(db, job_id=j.id)
        if st.get("sla_status_summary") == "no_sla_context":
            continue
        if st.get("response_breached") or st.get("attendance_breached") or st.get("resolution_breached"):
            breached += 1
    open_jobs = len([j for j in jobs if j.status not in ("completed", "closed", "cancelled")])
    planned = len([j for j in jobs if (j.work_type or "") == "planned_maintenance" or j.status == "ppm_created"])
    reactive = len([j for j in jobs if (j.work_type or "") == "reactive"])
    return {
        "contract_id": contract_id,
        "jobs_considered": len(jobs),
        "open_jobs": open_jobs,
        "planned_maintenance_jobs": planned,
        "reactive_jobs": reactive,
        "breached_job_count": breached,
    }
