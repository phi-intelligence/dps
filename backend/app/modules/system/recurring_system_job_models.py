"""
Recurring system jobs: definitions + run history (orchestration above domain services).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecurringSystemJob(Base):
    __tablename__ = "recurring_system_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    job_key: Mapped[str] = mapped_column(String(96), unique=True, index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # manual_only | interval_minutes | daily | cron_like
    schedule_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    schedule_expression: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    max_runtime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dry_run_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RecurringSystemJobRun(Base):
    __tablename__ = "recurring_system_job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    recurring_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recurring_system_jobs.id"), index=True, nullable=False
    )
    job_key: Mapped[str] = mapped_column(String(96), index=True, nullable=False)

    # scheduled | manual | retry
    trigger_type: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    # started | succeeded | failed | skipped | cancelled
    status: Mapped[str] = mapped_column(String(24), index=True, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    triggered_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skipped_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
