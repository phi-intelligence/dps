from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.dispatch.models import Job
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.sites.models import Site


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_portal_invoice_detail(db: Session, *, invoice: Invoice) -> dict[str, Any]:
    job = db.get(Job, invoice.job_id)
    site = db.get(Site, job.site_id) if job and job.site_id else None
    now = _aware(utc_now())
    created = _aware(invoice.created_at)
    overdue = (
        invoice.status == "unpaid"
        and not invoice.paid_at
        and (now - created).total_seconds() > 30 * 86400
    )

    return {
        "invoice": {
            "id": invoice.id,
            "job_id": invoice.job_id,
            "currency": invoice.currency,
            "status": invoice.status,
            "labour_total": invoice.labour_total,
            "materials_total": invoice.materials_total,
            "grand_total": invoice.grand_total,
            "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
            "created_at": invoice.created_at.isoformat(),
            "overdue": overdue,
        },
        "service_context": {
            "job_address": job.address if job else None,
            "job_status": job.status if job else None,
            "scheduled_at": job.scheduled_at.isoformat() if job and job.scheduled_at else None,
            "work_type": job.work_type if job else None,
            "site_id": job.site_id if job else None,
            "site_name": site.name if site else None,
            "site_code": site.site_code if site else None,
        },
        "retrieval": {
            "pay_path": f"/portal/me/invoices/{invoice.id}/pay",
            "receipt_note": "Receipt available after payment is recorded." if invoice.paid_at else None,
        },
    }
