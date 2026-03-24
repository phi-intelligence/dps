"""
Immutable contract performance snapshots for auditable commercial reporting.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractPerformanceSnapshot(Base):
    """
    Point-in-time commercial performance for a contract and reporting window.
    """

    __tablename__ = "contract_performance_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    period_window: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)

    contract_value_at_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)

    revenue_invoiced: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_unpaid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    revenue_overdue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    labour_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    gross_margin_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gross_margin_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    planned_job_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reactive_job_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_job_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    overdue_ppm_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_breach_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_recommendation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    jobs_without_costing_snapshot: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_jobs_missing_snapshot: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    health_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health_status: Mapped[str] = mapped_column(String(24), default="unknown", nullable=False)

    renewal_status: Mapped[str] = mapped_column(String(24), default="unknown", nullable=False)
    renewal_risk_level: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    renewal_opportunity_level: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    renewal_review_due: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # bool as 0/1

    avg_response_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_attendance_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_resolution_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    calculation_basis_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    renewal_reasons_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    health_components_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    site_burden_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    asset_burden_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
