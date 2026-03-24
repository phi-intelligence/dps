from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.compliance.schemas import CertificateGenerateIn, CertificateOut
from backend.app.modules.compliance.service import generate_certificate, list_certificates
from backend.app.modules.documents.persist import regenerate_certificate_document
from backend.app.modules.documents.schemas import StoredDocumentOut
from backend.app.modules.documents.service import stored_document_out_from_row


router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/certificates/generate", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
def generate_certificate_endpoint(
    payload: CertificateGenerateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> CertificateOut:
    try:
        return generate_certificate(db, payload=payload, acting_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/certificates/{certificate_id}/regenerate-pdf",
    response_model=StoredDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def regenerate_certificate_pdf_endpoint(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> StoredDocumentOut:
    if not db.get(Certificate, certificate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    try:
        row = regenerate_certificate_document(
            db, certificate_id=certificate_id, uploaded_by_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return stored_document_out_from_row(row)


@router.get("/certificates", response_model=list[CertificateOut])
def list_certificates_endpoint(
    job_id: str | None = Query(default=None),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[CertificateOut]:
    return list_certificates(db, job_id=job_id, limit=limit, offset=offset)

