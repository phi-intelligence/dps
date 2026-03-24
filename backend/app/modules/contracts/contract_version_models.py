"""
Formal contract version history and activation run audit trail.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractVersion(Base):
    """
    Queryable contract state timeline. Each row is an immutable version window.
    """

    __tablename__ = "contract_versions"
    __table_args__ = (UniqueConstraint("contract_id", "version_number", name="uq_contract_version_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    source_amendment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_amendments.id"), index=True, nullable=True
    )

    # initial | amendment_activation | manual_update
    version_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    renewal_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    renewal_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    repricing_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    account_attention_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    churn_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)

    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContractActivationRun(Base):
    """
    Durable record of each activation attempt (manual, scheduled, retry).
    """

    __tablename__ = "contract_activation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    amendment_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_amendments.id"), index=True, nullable=False)
    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)

    # manual | scheduled
    run_type: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    # started | succeeded | failed | skipped
    status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    triggered_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
