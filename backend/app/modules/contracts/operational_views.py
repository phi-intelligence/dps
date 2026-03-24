from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.sla_clock_service import aggregate_contract_sla_performance
from backend.app.modules.dispatch.models import Job
from backend.app.modules.ppm.models import PpmSchedule


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _naive_utc(dt: datetime) -> datetime:
    return _aware(dt).replace(tzinfo=None)


def contract_jobs_summary(db: Session, *, contract_id: str) -> dict[str, Any]:
    jobs = db.query(Job).filter(Job.contract_id == contract_id).order_by(Job.created_at.desc()).limit(500).all()
    open_j = [j for j in jobs if j.status not in ("completed", "closed", "cancelled")]
    return {
        "contract_id": contract_id,
        "total_jobs": len(jobs),
        "open_jobs": [{"id": j.id, "status": j.status, "work_type": j.work_type, "site_id": j.site_id} for j in open_j],
        "recent_jobs": [
            {"id": j.id, "status": j.status, "work_type": j.work_type, "created_at": j.created_at.isoformat()}
            for j in jobs[:25]
        ],
    }


def contract_ppm_summary(db: Session, *, contract_id: str) -> dict[str, Any]:
    now = utc_now()
    schedules = db.query(PpmSchedule).filter(PpmSchedule.contract_id == contract_id).all()
    jobs = db.query(Job).filter(Job.contract_id == contract_id).all()
    ppm_jobs = [
        j
        for j in jobs
        if j.work_type == "planned_maintenance" or j.status == "ppm_created" or j.ppm_schedule_id is not None
    ]
    overdue = [s for s in schedules if s.active and _naive_utc(s.next_due_date) < _naive_utc(now)]
    return {
        "contract_id": contract_id,
        "active_schedules": len([s for s in schedules if s.active]),
        "overdue_schedules": len(overdue),
        "ppm_job_count": len(ppm_jobs),
        "schedules": [
            {
                "id": s.id,
                "title": s.title,
                "next_due_date": s.next_due_date.isoformat(),
                "active": s.active,
                "site_id": s.site_id,
                "asset_id": s.asset_id,
            }
            for s in schedules[:50]
        ],
    }


def contracts_attention_dashboard(db: Session) -> dict[str, Any]:
    now = utc_now()
    items: list[dict[str, Any]] = []
    for c in db.query(Contract).filter(Contract.status == "active").all():
        reasons: list[str] = []
        if c.term_end_at and _aware(c.term_end_at) - now < timedelta(days=90):
            reasons.append("nearing_expiry")
        if c.renewal_review_date and _aware(c.renewal_review_date) <= now + timedelta(days=30):
            reasons.append("renewal_review_due")
        sch = (
            db.query(PpmSchedule)
            .filter(PpmSchedule.contract_id == c.id, PpmSchedule.active.is_(True))
            .all()
        )
        overdue = sum(1 for s in sch if _naive_utc(s.next_due_date) < _naive_utc(now))
        if overdue > 0:
            reasons.append(f"overdue_ppm:{overdue}")
        perf = aggregate_contract_sla_performance(db, contract_id=c.id)
        if perf.get("breached_job_count", 0) > 0:
            reasons.append(f"sla_breaches:{perf['breached_job_count']}")
        reactive = perf.get("reactive_jobs", 0)
        if reactive > 20:
            reasons.append("high_reactive_volume")

        health = "ok"
        if reasons:
            health = "review"
        if "nearing_expiry" in reasons and overdue > 2:
            health = "critical"

        if reasons:
            items.append(
                {
                    "contract_id": c.id,
                    "contract_code": c.contract_code,
                    "customer_id": c.customer_id,
                    "health": health,
                    "reasons": reasons,
                    "term_end_at": c.term_end_at.isoformat() if c.term_end_at else None,
                }
            )

    return {"contracts": items}


def site_jobs_summary(db: Session, *, site_id: str) -> dict[str, Any]:
    jobs = db.query(Job).filter(Job.site_id == site_id).order_by(Job.created_at.desc()).limit(300).all()
    open_j = [j for j in jobs if j.status not in ("completed", "closed", "cancelled")]
    return {
        "site_id": site_id,
        "open_count": len(open_j),
        "jobs": [
            {
                "id": j.id,
                "status": j.status,
                "work_type": j.work_type,
                "contract_id": j.contract_id,
                "created_at": j.created_at.isoformat(),
            }
            for j in jobs[:50]
        ],
    }
