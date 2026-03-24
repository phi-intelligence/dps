"""
Contract amendment / activation model for formal contract change workflow.
Turns accepted customer proposals into auditable live contract amendments.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractAmendment(Base):
    """
    Formal contract change record derived from accepted customer proposals.
    Distinct from proposal; amendment is the activation workflow object.
    Statuses: draft | pending_approval | approved | scheduled | activated | rejected | cancelled
    """

    __tablename__ = "contract_amendments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    source_proposal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_repricing_proposals.id"), index=True, nullable=True
    )
    source_review_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_reviews.id"), index=True, nullable=True
    )

    # repricing | renewal | commercial_update
    amendment_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # draft | pending_approval | approved | scheduled | activated | rejected | cancelled
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)

    amendment_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    current_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    pricing_basis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    prior_contract_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    resulting_contract_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Logical link to ContractVersion.id (no ORM FK — avoids circular dependency with source_amendment_id).
    resulting_contract_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
