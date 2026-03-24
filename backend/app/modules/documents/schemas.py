from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StoredDocumentOut(BaseModel):
    """Internal API: never includes raw storage_key."""

    id: str
    document_type: str
    filename: str
    content_type: str
    size_bytes: int
    storage_provider: str
    checksum_sha256: str | None = None
    related_job_id: str | None = None
    related_site_id: str | None = None
    related_asset_id: str | None = None
    related_contract_id: str | None = None
    related_invoice_id: str | None = None
    related_certificate_id: str | None = None
    uploaded_by_user_id: str | None = None
    created_at: datetime
    source_type: str
    visibility_scope: str
    status: str
    metadata_json: str | None = None
    downloadable: bool = Field(
        default=False,
        description="True when status is ready and binary is present in storage.",
    )
    integrity_warning: str | None = Field(
        default=None,
        description="Set when metadata claims ready but object is missing or checksum fails.",
    )

    model_config = {"from_attributes": True}


class PortalStoredDocumentOut(BaseModel):
    """Customer-safe metadata only."""

    id: str
    document_type: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    status: str
    related_job_id: str | None = None
    related_site_id: str | None = None
    related_asset_id: str | None = None
    related_contract_id: str | None = None
    related_invoice_id: str | None = None
    related_certificate_id: str | None = None
    downloadable: bool
    warning: str | None = None


class DocumentDownloadLinkOut(BaseModel):
    """App-relative URL; clients prepend their API origin."""

    download_url: str
    expires_in_seconds: int


class DocumentDownloadLinkIn(BaseModel):
    """Optional override for short tests; production uses server TTL."""

    ttl_seconds: int | None = None
