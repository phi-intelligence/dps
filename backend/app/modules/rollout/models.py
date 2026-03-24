from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PilotUser(Base):
    __tablename__ = "pilot_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    cohort: Mapped[str] = mapped_column(String(64), default="pilot-a", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="invited", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RolloutWave(Base):
    __tablename__ = "rollout_waves"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    target_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rollout_percent: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pause_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_automation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PilotFeedback(Base):
    __tablename__ = "pilot_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="workflow", nullable=False)
    rating: Mapped[int | None] = mapped_column(nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    triage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RolloutPolicy(Base):
    __tablename__ = "rollout_policy"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    low_rating_threshold: Mapped[int] = mapped_column(default=3, nullable=False)
    error_events_threshold: Mapped[int] = mapped_column(default=5, nullable=False)
    evaluation_window_hours: Mapped[int] = mapped_column(default=24, nullable=False)
    ramp_steps_csv: Mapped[str] = mapped_column(String(128), default="10,25,50,100", nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    rollback_percent: Mapped[int] = mapped_column(default=0, nullable=False)
    runner_interval_minutes: Mapped[int] = mapped_column(default=15, nullable=False)
    last_runner_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alert_suppression_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    notify_email_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_webhook_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    notification_max_attempts: Mapped[int] = mapped_column(default=3, nullable=False)
    notification_backoff_base_seconds: Mapped[int] = mapped_column(default=30, nullable=False)
    auto_pause_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RolloutAlert(Base):
    __tablename__ = "rollout_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    severity: Mapped[str] = mapped_column(String(16), default="warning", nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    acknowledged_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedup_count: Mapped[int] = mapped_column(default=1, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("rollout_alerts.id"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)  # email|webhook
    status: Mapped[str] = mapped_column(
        String(16), default="queued", nullable=False
    )  # queued|sent|failed|dead_letter
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class NotificationWebhookEvent(Base):
    __tablename__ = "notification_webhook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel: Mapped[str] = mapped_column(String(16), nullable=False)  # email|webhook
    external_event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(default=False, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

