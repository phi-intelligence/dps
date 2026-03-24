from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job
from backend.app.modules.ppm.models import PpmSchedule
from backend.app.modules.portal.portal_access_service import list_portal_sites_for_customer, portal_jobs_base_query
from backend.app.modules.portal.utils import list_client_certificates, list_client_invoices


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_portal_dashboard(db: Session, *, customer: Customer) -> dict[str, Any]:
    now = utc_now()
    q = portal_jobs_base_query(db, customer=customer)
    all_jobs = q.order_by(Job.created_at.desc()).limit(500).all()

    open_jobs = [j for j in all_jobs if j.status not in ("completed", "closed", "cancelled")]
    upcoming = [
        j
        for j in all_jobs
        if j.scheduled_at and j.scheduled_at > now and j.status not in ("completed", "closed", "cancelled")
    ]
    recent_done = [j for j in all_jobs if j.status in ("completed", "closed")][:10]

    invoices = list_client_invoices(db, customer=customer)
    outstanding = [i for i in invoices if i.status == "unpaid" and not i.paid_at]
    certs = list_client_certificates(db, customer=customer)[:10]

    contracts = (
        db.query(Contract).filter(Contract.customer_id == customer.id).order_by(Contract.created_at.desc()).limit(20).all()
    )
    sites = list_portal_sites_for_customer(db, customer=customer)

    ppm_upcoming: list[dict[str, Any]] = []
    overdue_ppm = 0
    if customer.portal_profile == "commercial" and sites:
        site_ids = [s.id for s in sites]
        for sch in (
            db.query(PpmSchedule)
            .filter(PpmSchedule.site_id.in_(site_ids), PpmSchedule.active.is_(True))
            .order_by(PpmSchedule.next_due_date.asc())
            .limit(15)
            .all()
        ):
            nd = sch.next_due_date
            if nd.tzinfo is None:
                nd = nd.replace(tzinfo=timezone.utc)
            if nd < now:
                overdue_ppm += 1
            ppm_upcoming.append(
                {
                    "schedule_id": sch.id,
                    "site_id": sch.site_id,
                    "title": sch.title,
                    "next_due_date": sch.next_due_date.isoformat(),
                }
            )

    alerts: list[str] = []
    if overdue_ppm:
        alerts.append(f"{overdue_ppm} overdue scheduled service visit(s) on your sites")

    return {
        "profile": customer.portal_profile,
        "summary": {
            "open_jobs_count": len(open_jobs),
            "upcoming_visits_count": len(upcoming),
            "outstanding_invoices_count": len(outstanding),
        },
        "open_jobs": [
            {
                "id": j.id,
                "status": j.status,
                "address": j.address[:120],
                "scheduled_at": j.scheduled_at.isoformat() if j.scheduled_at else None,
                "site_id": j.site_id,
            }
            for j in open_jobs[:20]
        ],
        "upcoming_visits": [
            {
                "job_id": j.id,
                "scheduled_at": j.scheduled_at.isoformat() if j.scheduled_at else None,
                "address": j.address[:120],
                "site_id": j.site_id,
            }
            for j in sorted(upcoming, key=lambda x: x.scheduled_at or now)[:15]
        ],
        "recent_completed": [
            {"id": j.id, "status": j.status, "address": j.address[:120], "site_id": j.site_id} for j in recent_done
        ],
        "outstanding_invoices": [
            {
                "id": i.id,
                "job_id": i.job_id,
                "grand_total": i.grand_total,
                "currency": i.currency,
                "status": i.status,
                "created_at": i.created_at.isoformat(),
            }
            for i in outstanding[:20]
        ],
        "recent_certificates": [
            {
                "id": c.id,
                "job_id": c.job_id,
                "type": c.certificate_type,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in certs
        ],
        "contracts": [
            {
                "id": c.id,
                "name": c.name,
                "contract_code": c.contract_code,
                "status": c.status,
                "term_end_at": c.term_end_at.isoformat() if c.term_end_at else None,
            }
            for c in contracts
        ],
        "sites": [{"id": s.id, "name": s.name, "site_code": s.site_code} for s in sites[:50]],
        "upcoming_ppm": ppm_upcoming,
        "alerts": alerts,
    }
