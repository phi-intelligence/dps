from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), index=True, nullable=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=True)

    certificate_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="generated", index=True, nullable=False)

    engineer_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    signed_by_engineer: Mapped[bool] = mapped_column(default=False, nullable=False)
    signed_by_client: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

