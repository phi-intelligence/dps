from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job, JobEtaDelayNotice
from backend.app.modules.dispatch.operational_tracking_service import compute_internal_job_eta
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.portal.portal_access_service import portal_job_ids, portal_jobs_base_query


def get_client_customer(db: Session, *, email: str) -> Customer | None:
    return db.query(Customer).filter(Customer.email == email).one_or_none()


def list_client_jobs(db: Session, *, customer: Customer) -> list[Job]:
    jobs = portal_jobs_base_query(db, customer=customer).order_by(Job.created_at.desc()).all()

    # Attach ETA from shared operational layer (falls back to schedule / manual as appropriate).
    for job in jobs:
        try:
            eta_payload = compute_internal_job_eta(db, job_id=job.id)
            eta_minutes = eta_payload.get("eta_minutes")
            if isinstance(eta_minutes, (int, float)):
                setattr(job, "eta_minutes", float(eta_minutes))
            else:
                setattr(job, "eta_minutes", None)
        except Exception:
            setattr(job, "eta_minutes", None)

        # Best-effort delay notice (open) for customer communication.
        latest_notice = (
            db.query(JobEtaDelayNotice)
            .filter(JobEtaDelayNotice.job_id == job.id, JobEtaDelayNotice.status == "open")
            .order_by(JobEtaDelayNotice.created_at.desc())
            .first()
        )
        setattr(job, "delay_notice", latest_notice.message if latest_notice else None)
        setattr(job, "delay_notice_at", latest_notice.created_at if latest_notice else None)

    return jobs


def list_client_certificates(db: Session, *, customer: Customer) -> list[Certificate]:
    job_ids = list(portal_job_ids(db, customer=customer))
    if not job_ids:
        return []
    return db.query(Certificate).filter(Certificate.job_id.in_(job_ids)).order_by(Certificate.created_at.desc()).all()


def list_client_invoices(db: Session, *, customer: Customer) -> list[Invoice]:
    job_ids = list(portal_job_ids(db, customer=customer))
    if not job_ids:
        return []
    return db.query(Invoice).filter(Invoice.job_id.in_(job_ids)).order_by(Invoice.created_at.desc()).all()


def anonymize_client_customer_for_email(db: Session, *, email: str) -> Customer | None:
    """
    GDPR-style anonymization (Phase 4 demo):
    - removes the customer email match so future lookups fail
    - keeps the record so existing historical invoices/jobs can remain consistent
    """
    customer = db.query(Customer).filter(Customer.email == email).one_or_none()
    if not customer:
        return None

    customer.email = None
    # Keep non-identifying fields minimal for privacy.
    customer.name = "Deleted customer"
    db.commit()
    return customer

