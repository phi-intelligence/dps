from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PpmSchedule(Base):
    __tablename__ = "ppm_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), index=True, nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assets.id"), index=True, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency_value: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency_unit: Mapped[str] = mapped_column(String(16), nullable=False)  # day | week | month | year
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)

    next_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    planning_window_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checklist_template_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    compliance_template_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_competencies_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PpmGenerationRecord(Base):
    """
    Idempotency: one generated job per schedule per due anchor (logical period).
    """

    __tablename__ = "ppm_generation_records"
    __table_args__ = (UniqueConstraint("ppm_schedule_id", "due_anchor", name="uq_ppm_gen_schedule_anchor"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ppm_schedule_id: Mapped[str] = mapped_column(String(36), ForeignKey("ppm_schedules.id"), index=True, nullable=False)
    due_anchor: Mapped[str] = mapped_column(String(32), nullable=False)  # ISO date of due used for generation
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
