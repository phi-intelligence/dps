from __future__ import annotations

import json
import uuid
from io import BytesIO
from typing import Any

from fastapi import HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job
from backend.app.modules.documents.download_token import create_document_download_token, decode_document_download_token
from backend.app.modules.documents.models import DocumentAccessLog, StoredDocument
from backend.app.modules.documents.schemas import DocumentDownloadLinkOut, PortalStoredDocumentOut, StoredDocumentOut
from backend.app.modules.contracts.review_models import ContractRepricingProposal
from backend.app.modules.portal.portal_access_service import (
    can_customer_access_contract,
    can_customer_access_job,
    can_customer_access_site,
    portal_job_ids,
)
from backend.app.services import document_storage_service as doc_store


def _client_ip(request: Request | None) -> str | None:
    if not request or not request.client:
        return None
    return request.client.host


def _user_agent(request: Request | None) -> str | None:
    if not request:
        return None
    return (request.headers.get("user-agent") or request.headers.get("User-Agent"))[:512]


def log_document_access(
    db: Session,
    *,
    document_id: str | None,
    user_id: str | None,
    customer_id: str | None,
    access_type: str,
    source_context: str,
    access_status: str,
    reason: str | None,
    request: Request | None,
) -> None:
    row = DocumentAccessLog(
        id=str(uuid.uuid4()),
        document_id=document_id,
        user_id=user_id,
        customer_id=customer_id,
        access_type=access_type,
        source_context=source_context,
        remote_ip=_client_ip(request),
        user_agent=_user_agent(request),
        status=access_status,
        reason=reason[:255] if reason else None,
    )
    db.add(row)
    db.commit()


def _binary_integrity_flags(doc: StoredDocument) -> tuple[bool, str | None]:
    if doc.status != "ready":
        return False, None
    if not doc_store.document_exists(storage_key=doc.storage_key):
        return False, "binary_missing"
    return True, None


def _verify_checksum_if_present(doc: StoredDocument, data: bytes) -> str | None:
    if not doc.checksum_sha256:
        return None
    if doc_store.sha256_hex(data) != doc.checksum_sha256:
        return "checksum_mismatch"
    return None


def stored_document_out_from_row(doc: StoredDocument) -> StoredDocumentOut:
    """Single place for downloadable + checksum integrity flags on StoredDocument rows."""
    dl, warn = _binary_integrity_flags(doc)
    integ: str | None = None
    if doc.status == "ready" and doc_store.document_exists(storage_key=doc.storage_key):
        data = doc_store.get_storage_backend().open_read(storage_key=doc.storage_key).read()
        integ = _verify_checksum_if_present(doc, data)
        if integ:
            dl = False
    elif doc.status == "ready":
        integ = warn or "binary_missing"
        dl = False
    return StoredDocumentOut.model_validate(doc).model_copy(
        update={"downloadable": dl and not integ, "integrity_warning": integ or warn}
    )


def _portal_activation_confirmation_access(
    db: Session, *, customer: Customer, doc: StoredDocument
) -> tuple[bool, ContractActivationConfirmation | None]:
    if doc.document_type != "contract_activation_confirmation":
        return False, None
    if doc.visibility_scope != "customer_activation_confirmation":
        return False, None
    try:
        meta = json.loads(doc.metadata_json or "{}")
    except json.JSONDecodeError:
        return False, None
    cid = meta.get("activation_confirmation_id")
    if not cid:
        return False, None
    conf = db.get(ContractActivationConfirmation, str(cid))
    if not conf:
        return False, None
    if conf.status not in ("released", "viewed", "acknowledged"):
        return False, None
    if conf.portal_visibility_scope != "contract_customer_portal":
        return False, None
    if not can_customer_access_contract(
        db, customer=customer, contract_id=conf.contract_id, portal_login_email=customer.email
    ):
        return False, None
    if doc.related_site_id and not can_customer_access_site(
        db, customer=customer, site_id=doc.related_site_id, portal_login_email=customer.email
    ):
        return False, None
    return True, conf


def _portal_repricing_proposal_access(
    db: Session, *, customer: Customer, doc: StoredDocument
) -> tuple[bool, ContractRepricingProposal | None]:
    """
    Released repricing proposal PDFs use visibility_scope=customer_repricing_proposal (no related_job_id).
    """
    if doc.document_type != "repricing_proposal" or doc.visibility_scope != "customer_repricing_proposal":
        return False, None
    if not doc.related_contract_id:
        return False, None
    if not can_customer_access_contract(
        db, customer=customer, contract_id=doc.related_contract_id, portal_login_email=customer.email
    ):
        return False, None
    prop = (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.stored_document_id == doc.id,
            ContractRepricingProposal.contract_id == doc.related_contract_id,
        )
        .first()
    )
    if not prop:
        return False, None
    if prop.proposal_status in ("superseded", "withdrawn"):
        return False, None
    if prop.customer_release_status not in ("released", "viewed", "responded", "expired"):
        return False, None
    return True, prop


def portal_customer_may_see_metadata(db: Session, *, customer: Customer, doc: StoredDocument) -> bool:
    if doc.visibility_scope == "internal_only":
        return False
    ok_ac, _ = _portal_activation_confirmation_access(db, customer=customer, doc=doc)
    if ok_ac:
        return True
    ok_rp, _ = _portal_repricing_proposal_access(db, customer=customer, doc=doc)
    if ok_rp:
        return True
    if not doc.related_job_id:
        return False
    if not can_customer_access_job(db, customer=customer, job_id=doc.related_job_id):
        return False
    if doc.visibility_scope == "site_scoped":
        if doc.related_site_id and not can_customer_access_site(db, customer=customer, site_id=doc.related_site_id):
            return False
    if doc.visibility_scope == "contract_scoped" and doc.related_contract_id:
        job = db.get(Job, doc.related_job_id)
        if not job or (job.contract_id or "") != doc.related_contract_id:
            return False
    return True


def portal_customer_may_download(db: Session, *, customer: Customer, doc: StoredDocument) -> tuple[bool, str | None]:
    ok_ac, _ = _portal_activation_confirmation_access(db, customer=customer, doc=doc)
    if ok_ac:
        downloadable, warn = _binary_integrity_flags(doc)
        if not downloadable:
            return False, warn or "not_ready"
        return True, None
    ok_rp, prop = _portal_repricing_proposal_access(db, customer=customer, doc=doc)
    if ok_rp and prop:
        from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry

        if prop.customer_release_status == "expired" or is_past_customer_expiry(prop):
            return False, "proposal_expired"
        downloadable, warn = _binary_integrity_flags(doc)
        if not downloadable:
            return False, warn or "not_ready"
        return True, None
    if not portal_customer_may_see_metadata(db, customer=customer, doc=doc):
        return False, "forbidden_visibility"
    downloadable, warn = _binary_integrity_flags(doc)
    if not downloadable:
        return False, warn or "not_ready"
    return True, None


def list_stored_documents_internal(
    db: Session,
    *,
    document_type: str | None = None,
    related_job_id: str | None = None,
    related_site_id: str | None = None,
    related_asset_id: str | None = None,
    related_contract_id: str | None = None,
    related_invoice_id: str | None = None,
    related_certificate_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[StoredDocumentOut]:
    q = db.query(StoredDocument).order_by(StoredDocument.created_at.desc())
    if document_type:
        q = q.filter(StoredDocument.document_type == document_type)
    if related_job_id:
        q = q.filter(StoredDocument.related_job_id == related_job_id)
    if related_site_id:
        q = q.filter(StoredDocument.related_site_id == related_site_id)
    if related_asset_id:
        q = q.filter(StoredDocument.related_asset_id == related_asset_id)
    if related_contract_id:
        q = q.filter(StoredDocument.related_contract_id == related_contract_id)
    if related_invoice_id:
        q = q.filter(StoredDocument.related_invoice_id == related_invoice_id)
    if related_certificate_id:
        q = q.filter(StoredDocument.related_certificate_id == related_certificate_id)
    rows = q.offset(offset).limit(limit).all()
    return [stored_document_out_from_row(row) for row in rows]


def get_stored_document_internal(db: Session, *, document_id: str) -> StoredDocument | None:
    return db.get(StoredDocument, document_id)


def get_portal_stored_document_out(
    db: Session, *, customer: Customer, document_id: str, request: Request | None
) -> PortalStoredDocumentOut:
    doc = db.get(StoredDocument, document_id)
    if not doc or not portal_customer_may_see_metadata(db, customer=customer, doc=doc):
        if doc:
            log_document_access(
                db,
                document_id=document_id,
                user_id=None,
                customer_id=customer.id,
                access_type="metadata_view",
                source_context="portal",
                access_status="denied",
                reason="forbidden",
                request=request,
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    ok_dl, reason = portal_customer_may_download(db, customer=customer, doc=doc)
    warning: str | None = None
    if doc.status == "ready" and not doc_store.document_exists(storage_key=doc.storage_key):
        warning = "Document is marked ready but the file is not available."
        ok_dl = False
    elif doc.status in ("pending_generation", "failed"):
        warning = f"Document status is {doc.status}."
        ok_dl = False
    elif doc.status == "archived":
        warning = "Document is archived."
        ok_dl = False

    log_document_access(
        db,
        document_id=document_id,
        user_id=None,
        customer_id=customer.id,
        access_type="metadata_view",
        source_context="portal",
        access_status="granted",
        reason=None,
        request=request,
    )

    return PortalStoredDocumentOut(
        id=doc.id,
        document_type=doc.document_type,
        filename=doc.filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        created_at=doc.created_at,
        status=doc.status,
        related_job_id=doc.related_job_id,
        related_site_id=doc.related_site_id,
        related_asset_id=doc.related_asset_id,
        related_contract_id=doc.related_contract_id,
        related_invoice_id=doc.related_invoice_id,
        related_certificate_id=doc.related_certificate_id,
        downloadable=ok_dl,
        warning=warning,
    )


def create_internal_download_link(
    db: Session,
    *,
    document_id: str,
    user_id: str,
    request: Request | None,
    ttl_seconds: int | None = None,
) -> DocumentDownloadLinkOut:
    doc = db.get(StoredDocument, document_id)
    if not doc:
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="download_link",
            source_context="internal",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    downloadable, warn = _binary_integrity_flags(doc)
    if not downloadable:
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="download_link",
            source_context="internal",
            access_status="denied",
            reason=warn or "not_downloadable",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is not available for download")

    token = create_document_download_token(
        document_id=doc.id,
        context="internal",
        customer_id=None,
        ttl_seconds=ttl_seconds,
    )
    from backend.app.core.config import settings

    ttl = ttl_seconds if ttl_seconds is not None else int(settings.PHI_DPS_DOCUMENT_DOWNLOAD_TOKEN_TTL_SECONDS)
    log_document_access(
        db,
        document_id=document_id,
        user_id=user_id,
        customer_id=None,
        access_type="download_link",
        source_context="internal",
        access_status="granted",
        reason=None,
        request=request,
    )
    return DocumentDownloadLinkOut(download_url=f"/documents/download?token={token}", expires_in_seconds=ttl)


def create_portal_download_link(
    db: Session,
    *,
    document_id: str,
    customer: Customer,
    request: Request | None,
    ttl_seconds: int | None = None,
) -> DocumentDownloadLinkOut:
    doc = db.get(StoredDocument, document_id)
    if not doc:
        log_document_access(
            db,
            document_id=document_id,
            user_id=None,
            customer_id=customer.id,
            access_type="download_link",
            source_context="portal",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    ok, reason = portal_customer_may_download(db, customer=customer, doc=doc)
    if not ok:
        log_document_access(
            db,
            document_id=document_id,
            user_id=None,
            customer_id=customer.id,
            access_type="download_link",
            source_context="portal",
            access_status="denied",
            reason=reason or "forbidden",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    token = create_document_download_token(
        document_id=doc.id,
        context="portal",
        customer_id=customer.id,
        ttl_seconds=ttl_seconds,
    )
    from backend.app.core.config import settings

    ttl = ttl_seconds if ttl_seconds is not None else int(settings.PHI_DPS_DOCUMENT_DOWNLOAD_TOKEN_TTL_SECONDS)
    log_document_access(
        db,
        document_id=document_id,
        user_id=None,
        customer_id=customer.id,
        access_type="download_link",
        source_context="portal",
        access_status="granted",
        reason=None,
        request=request,
    )
    return DocumentDownloadLinkOut(download_url=f"/documents/download?token={token}", expires_in_seconds=ttl)


def load_binary_for_document(doc: StoredDocument) -> tuple[bytes, str | None]:
    if not doc_store.document_exists(storage_key=doc.storage_key):
        return b"", "binary_missing"
    data = doc_store.get_storage_backend().open_read(storage_key=doc.storage_key).read()
    chk = _verify_checksum_if_present(doc, data)
    if chk:
        return b"", chk
    return data, None


def serve_internal_bearer_download(
    db: Session,
    *,
    document_id: str,
    user_id: str,
    request: Request | None,
) -> tuple[bytes, str, str]:
    doc = db.get(StoredDocument, document_id)
    if not doc:
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="binary_download",
            source_context="internal",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status != "ready":
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="binary_download",
            source_context="internal",
            access_status="denied",
            reason="not_ready",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document not ready")
    data, err = load_binary_for_document(doc)
    if err:
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="binary_download",
            source_context="internal",
            access_status="denied",
            reason=err,
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document binary unavailable")
    log_document_access(
        db,
        document_id=document_id,
        user_id=user_id,
        customer_id=None,
        access_type="binary_download",
        source_context="internal",
        access_status="granted",
        reason=None,
        request=request,
    )
    return data, doc.content_type, doc.filename


def serve_portal_bearer_download(
    db: Session,
    *,
    document_id: str,
    customer: Customer,
    request: Request | None,
) -> tuple[bytes, str, str]:
    doc = db.get(StoredDocument, document_id)
    if not doc:
        log_document_access(
            db,
            document_id=document_id,
            user_id=None,
            customer_id=customer.id,
            access_type="binary_download",
            source_context="portal",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    ok, reason = portal_customer_may_download(db, customer=customer, doc=doc)
    if not ok:
        log_document_access(
            db,
            document_id=document_id,
            user_id=None,
            customer_id=customer.id,
            access_type="binary_download",
            source_context="portal",
            access_status="denied",
            reason=reason or "forbidden",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    data, err = load_binary_for_document(doc)
    if err:
        log_document_access(
            db,
            document_id=document_id,
            user_id=None,
            customer_id=customer.id,
            access_type="binary_download",
            source_context="portal",
            access_status="denied",
            reason=err,
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document binary unavailable")
    log_document_access(
        db,
        document_id=document_id,
        user_id=None,
        customer_id=customer.id,
        access_type="binary_download",
        source_context="portal",
        access_status="granted",
        reason=None,
        request=request,
    )
    return data, doc.content_type, doc.filename


def serve_token_download(
    db: Session,
    *,
    token: str,
    request: Request | None,
) -> tuple[bytes, str, str]:
    try:
        payload = decode_document_download_token(token)
    except JWTError as e:
        log_document_access(
            db,
            document_id=None,
            user_id=None,
            customer_id=None,
            access_type="binary_download",
            source_context="token",
            access_status="denied",
            reason="invalid_or_expired_token",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired download token",
        ) from e

    doc_id = str(payload.get("sub") or "")
    ctx = str(payload.get("ctx") or "")
    cid = payload.get("cid")

    doc = db.get(StoredDocument, doc_id)
    if not doc:
        log_document_access(
            db,
            document_id=doc_id or "missing",
            user_id=None,
            customer_id=str(cid) if cid else None,
            access_type="binary_download",
            source_context="token",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if ctx == "internal":
        pass
    elif ctx == "portal":
        if not cid:
            log_document_access(
                db,
                document_id=doc_id,
                user_id=None,
                customer_id=None,
                access_type="binary_download",
                source_context="token",
                access_status="denied",
                reason="portal_token_missing_customer",
                request=request,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        cust = db.get(Customer, str(cid))
        if not cust:
            log_document_access(
                db,
                document_id=doc_id,
                user_id=None,
                customer_id=str(cid),
                access_type="binary_download",
                source_context="token",
                access_status="denied",
                reason="customer_not_found",
                request=request,
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        ok, reason = portal_customer_may_download(db, customer=cust, doc=doc)
        if not ok:
            log_document_access(
                db,
                document_id=doc_id,
                user_id=None,
                customer_id=str(cid),
                access_type="binary_download",
                source_context="token",
                access_status="denied",
                reason=reason or "forbidden",
                request=request,
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    else:
        log_document_access(
            db,
            document_id=doc_id,
            user_id=None,
            customer_id=str(cid) if cid else None,
            access_type="binary_download",
            source_context="token",
            access_status="denied",
            reason="bad_context",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if doc.status != "ready":
        log_document_access(
            db,
            document_id=doc_id,
            user_id=None,
            customer_id=str(cid) if cid else None,
            access_type="binary_download",
            source_context="token",
            access_status="denied",
            reason="not_ready",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document not ready")

    data, err = load_binary_for_document(doc)
    if err:
        log_document_access(
            db,
            document_id=doc_id,
            user_id=None,
            customer_id=str(cid) if cid else None,
            access_type="binary_download",
            source_context="token",
            access_status="denied",
            reason=err,
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document binary unavailable")

    log_document_access(
        db,
        document_id=doc_id,
        user_id=None,
        customer_id=str(cid) if cid else None,
        access_type="binary_download",
        source_context="token",
        access_status="granted",
        reason=None,
        request=request,
    )
    return data, doc.content_type, doc.filename


def resolve_stored_document_for_certificate(db: Session, *, certificate_id: str) -> StoredDocument | None:
    return (
        db.query(StoredDocument)
        .filter(StoredDocument.related_certificate_id == certificate_id)
        .order_by(StoredDocument.created_at.desc())
        .first()
    )


def resolve_stored_document_for_invoice(db: Session, *, invoice_id: str) -> StoredDocument | None:
    return (
        db.query(StoredDocument)
        .filter(StoredDocument.related_invoice_id == invoice_id)
        .order_by(StoredDocument.created_at.desc())
        .first()
    )


def internal_metadata_view(
    db: Session, *, document_id: str, user_id: str, request: Request | None
) -> StoredDocumentOut:
    doc = db.get(StoredDocument, document_id)
    if not doc:
        log_document_access(
            db,
            document_id=document_id,
            user_id=user_id,
            customer_id=None,
            access_type="metadata_view",
            source_context="internal",
            access_status="denied",
            reason="not_found",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    log_document_access(
        db,
        document_id=document_id,
        user_id=user_id,
        customer_id=None,
        access_type="metadata_view",
        source_context="internal",
        access_status="granted",
        reason=None,
        request=request,
    )
    return stored_document_out_from_row(doc)
