"""
Low-risk workflow automation: auditable runs and internal follow-up tasks (draft-first, no silent finals).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutomationRun(Base):
    """
    First-class record for each automation attempt (success, skip, or failure).
    """

    __tablename__ = "automation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    automation_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    # recommendation | customer_proposal | manual | scheduled
    trigger_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    trigger_entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    source_recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operational_recommendations.id"), nullable=True, index=True
    )
    source_event_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # created | draft_created | skipped | failed | cancelled
    status: Mapped[str] = mapped_column(String(24), default="created", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    result_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    draft_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    draft_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


class InternalFollowUpTask(Base):
    """
    Structured internal work item (not a final customer/commercial commitment).
    """

    __tablename__ = "internal_follow_up_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    task_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # open | in_progress | completed | cancelled
    status: Mapped[str] = mapped_column(String(24), default="open", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="normal", index=True, nullable=False)

    related_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    source_recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operational_recommendations.id"), nullable=True, index=True
    )
    source_automation_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("automation_runs.id"), nullable=True, index=True
    )

    assigned_to_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
