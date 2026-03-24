from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PilotUserUpsertIn(BaseModel):
    user_id: str
    cohort: str = "pilot-a"
    status: str = "invited"
    notes: str | None = None


class PilotUserOut(BaseModel):
    id: str
    user_id: str
    cohort: str
    status: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RolloutWaveCreateIn(BaseModel):
    name: str
    target_role: str | None = None
    rollout_percent: int = Field(default=0, ge=0, le=100)


class RolloutWaveOut(BaseModel):
    id: str
    name: str
    target_role: str | None
    rollout_percent: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    paused_at: datetime | None
    pause_reason: str | None
    last_automation_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreateIn(BaseModel):
    category: str = "workflow"
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str


class FeedbackTriageIn(BaseModel):
    status: str
    triage_notes: str | None = None


class FeedbackOut(BaseModel):
    id: str
    user_id: str
    category: str
    rating: int | None
    message: str
    status: str
    triage_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UsageEventCreateIn(BaseModel):
    module: str
    event_name: str
    metadata: dict[str, Any] | None = None


class UsageEventOut(BaseModel):
    id: str
    user_id: str
    module: str
    event_name: str
    metadata_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RolloutDashboardOut(BaseModel):
    pilot_users_total: int
    pilot_users_active: int
    feedback_total: int
    feedback_open: int
    rollout_waves_total: int
    rollout_waves_completed: int
    rollout_waves_paused: int
    usage_events_24h: int
    events_by_module: dict[str, int]


class RolloutGuardOut(BaseModel):
    allowed: bool
    reason: str


class RolloutPolicyUpsertIn(BaseModel):
    low_rating_threshold: int = Field(default=3, ge=1, le=50)
    error_events_threshold: int = Field(default=5, ge=1, le=1000)
    evaluation_window_hours: int = Field(default=24, ge=1, le=168)
    ramp_steps: list[int] = Field(default=[10, 25, 50, 100], min_length=1, max_length=10)
    cooldown_minutes: int = Field(default=30, ge=0, le=10080)
    rollback_percent: int = Field(default=0, ge=0, le=100)
    runner_interval_minutes: int = Field(default=15, ge=1, le=10080)
    alert_suppression_minutes: int = Field(default=30, ge=0, le=10080)
    notify_email_enabled: bool = True
    notify_webhook_enabled: bool = False
    notification_max_attempts: int = Field(default=3, ge=1, le=20)
    notification_backoff_base_seconds: int = Field(default=30, ge=1, le=3600)
    auto_pause_enabled: bool = True


class RolloutPolicyOut(BaseModel):
    id: str
    low_rating_threshold: int
    error_events_threshold: int
    evaluation_window_hours: int
    ramp_steps_csv: str
    cooldown_minutes: int
    rollback_percent: int
    runner_interval_minutes: int
    last_runner_at: datetime | None
    alert_suppression_minutes: int
    notify_email_enabled: bool
    notify_webhook_enabled: bool
    notification_max_attempts: int
    notification_backoff_base_seconds: int
    auto_pause_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class RolloutHealthEvaluationOut(BaseModel):
    evaluated_at: datetime
    active_waves_before: int
    paused_waves_now: int
    low_ratings_in_window: int
    error_events_in_window: int


class RolloutAutomationRunOut(BaseModel):
    ran_at: datetime
    waves_started: int
    waves_ramped: int
    waves_completed: int


class RolloutAlertOut(BaseModel):
    id: str
    severity: str
    code: str
    message: str
    status: str
    acknowledged_by_user_id: str | None
    acknowledged_at: datetime | None
    dedup_count: int
    last_seen_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class RolloutCycleRunOut(BaseModel):
    ran: bool
    skipped_reason: str | None
    ran_at: datetime
    tick: RolloutAutomationRunOut | None
    health: RolloutHealthEvaluationOut | None


class RolloutAlertDigestOut(BaseModel):
    total_alerts: int
    open_alerts: int
    acknowledged_alerts: int
    critical_open_alerts: int
    warnings_open_alerts: int
    alerts_last_24h: int
    open_by_code: dict[str, int]


class NotificationDeliveryOut(BaseModel):
    id: str
    alert_id: str
    channel: str
    status: str
    attempts: int
    last_error: str | None
    last_attempt_at: datetime | None
    next_retry_at: datetime | None
    dead_lettered_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationRetryRunOut(BaseModel):
    processed: int
    resent_ok: int
    still_failed: int
    dead_lettered: int


class NotificationWebhookIn(BaseModel):
    event_type: str
    status: str | None = None
    metadata: dict[str, Any] | None = None


class NotificationWebhookOut(BaseModel):
    accepted: bool
    duplicate: bool
    event_id: str

