from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoredDocument(Base):
    """
    Metadata for a binary object in the document storage abstraction.
    Never expose storage_key to clients; use document id + authorized download paths.
    """

    __tablename__ = "stored_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    document_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="local", index=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    related_job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=True, index=True)
    related_site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True, index=True)
    related_asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), nullable=True, index=True)
    related_contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=True, index=True)
    related_invoice_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True, index=True)
    related_certificate_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("certificates.id"), nullable=True, index=True)

    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    source_type: Mapped[str] = mapped_column(String(24), nullable=False, default="generated", index=True)
    visibility_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="internal_only", index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ready", index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class DocumentAccessLog(Base):
    __tablename__ = "document_access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Nullable so denied/invalid-token attempts can still be persisted without a resolved row.
    document_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"), nullable=True, index=True)

    access_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_context: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    remote_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
