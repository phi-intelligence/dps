from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.modules.documents.schemas import DocumentDownloadLinkIn, DocumentDownloadLinkOut, StoredDocumentOut
from backend.app.modules.documents.service import (
    create_internal_download_link,
    internal_metadata_view,
    list_stored_documents_internal,
    serve_internal_bearer_download,
    serve_token_download,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/download")
def download_document_via_token(
    request: Request,
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
) -> Response:
    data, content_type, filename = serve_token_download(db, token=token, request=request)
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get("", response_model=list[StoredDocumentOut])
def list_documents(
    document_type: str | None = Query(default=None),
    related_job_id: str | None = Query(default=None),
    related_site_id: str | None = Query(default=None),
    related_asset_id: str | None = Query(default=None),
    related_contract_id: str | None = Query(default=None),
    related_invoice_id: str | None = Query(default=None),
    related_certificate_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> list[StoredDocumentOut]:
    return list_stored_documents_internal(
        db,
        document_type=document_type,
        related_job_id=related_job_id,
        related_site_id=related_site_id,
        related_asset_id=related_asset_id,
        related_contract_id=related_contract_id,
        related_invoice_id=related_invoice_id,
        related_certificate_id=related_certificate_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=StoredDocumentOut)
def get_document_metadata(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> StoredDocumentOut:
    return internal_metadata_view(db, document_id=document_id, user_id=current_user.id, request=request)


@router.post("/{document_id}/download-link", response_model=DocumentDownloadLinkOut)
def create_document_download_link(
    document_id: str,
    request: Request,
    body: DocumentDownloadLinkIn | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> DocumentDownloadLinkOut:
    ttl = body.ttl_seconds if body else None
    return create_internal_download_link(
        db,
        document_id=document_id,
        user_id=current_user.id,
        request=request,
        ttl_seconds=ttl,
    )


@router.get("/{document_id}/download")
def download_document_bearer(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> Response:
    data, content_type, filename = serve_internal_bearer_download(
        db, document_id=document_id, user_id=current_user.id, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )
