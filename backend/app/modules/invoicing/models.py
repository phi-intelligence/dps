from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="unpaid", index=True, nullable=False)

    labour_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    materials_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Start-4a: link to frozen costing; materials_total = customer materials charge (prefer actual usage × quote sell).
    job_cost_snapshot_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_cost_snapshots.id"), nullable=True, index=True
    )
    materials_actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_basis_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    finance_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    finance_reviewed_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )

