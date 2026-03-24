from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.compliance.schemas import CertificateGenerateIn
from backend.app.modules.dispatch.models import Job


def generate_certificate(db: Session, *, payload: CertificateGenerateIn, acting_user_id: str | None = None) -> Certificate:
    job = db.get(Job, payload.job_id)
    if not job:
        raise ValueError("Job not found")

    cert = Certificate(
        job_id=payload.job_id,
        site_id=job.site_id,
        asset_id=job.asset_id,
        contract_id=job.contract_id,
        certificate_type=payload.certificate_type,
        status="generated",
        engineer_user_id=job.assigned_engineer_id,
        signed_by_engineer=False,
        signed_by_client=False,
    )
    db.add(cert)
    db.flush()
    db.refresh(cert)
    from backend.app.modules.documents.persist import persist_generated_certificate_document

    persist_generated_certificate_document(
        db, certificate=cert, uploaded_by_user_id=acting_user_id, commit=False
    )
    db.commit()
    db.refresh(cert)
    try:
        from backend.app.modules.portal.communication_hooks import emit_customer_comms_event

        emit_customer_comms_event(
            db,
            job_id=payload.job_id,
            event_type="certificate_ready",
            payload={"certificate_id": cert.id, "certificate_type": cert.certificate_type},
        )
    except Exception:
        pass
    return cert


def list_certificates(db: Session, *, job_id: str | None = None, limit: int = 50, offset: int = 0) -> list[Certificate]:
    q = db.query(Certificate).order_by(Certificate.created_at.desc())
    if job_id:
        q = q.filter(Certificate.job_id == job_id)
    return q.offset(offset).limit(limit).all()

