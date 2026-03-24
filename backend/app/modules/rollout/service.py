from __future__ import annotations

import hmac
import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.rollout.models import (
    NotificationDelivery,
    NotificationWebhookEvent,
    PilotFeedback,
    PilotUser,
    RolloutAlert,
    RolloutPolicy,
    RolloutWave,
    UsageEvent,
)
from backend.app.modules.rollout.schemas import (
    FeedbackCreateIn,
    FeedbackTriageIn,
    PilotUserUpsertIn,
    RolloutWaveCreateIn,
    UsageEventCreateIn,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def upsert_pilot_user(db: Session, *, payload: PilotUserUpsertIn) -> PilotUser:
    row = db.query(PilotUser).filter(PilotUser.user_id == payload.user_id).one_or_none()
    if row:
        row.cohort = payload.cohort
        row.status = payload.status
        row.notes = payload.notes
        db.commit()
        db.refresh(row)
        return row

    row = PilotUser(
        user_id=payload.user_id,
        cohort=payload.cohort,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_pilot_users(db: Session) -> list[PilotUser]:
    return db.query(PilotUser).order_by(PilotUser.created_at.desc()).all()


def create_wave(db: Session, *, payload: RolloutWaveCreateIn) -> RolloutWave:
    existing = db.query(RolloutWave).filter(RolloutWave.name == payload.name).one_or_none()
    if existing:
        raise ValueError("Rollout wave with this name already exists")
    wave = RolloutWave(
        name=payload.name,
        target_role=payload.target_role,
        rollout_percent=payload.rollout_percent,
        status="planned",
    )
    db.add(wave)
    db.commit()
    db.refresh(wave)
    return wave


def list_waves(db: Session) -> list[RolloutWave]:
    return db.query(RolloutWave).order_by(RolloutWave.created_at.desc()).all()


def update_wave_state(db: Session, *, wave_id: str, to_state: str) -> RolloutWave:
    wave = db.get(RolloutWave, wave_id)
    if not wave:
        raise ValueError("Rollout wave not found")

    if to_state == "active":
        wave.status = "active"
        if not wave.started_at:
            wave.started_at = utc_now()
    elif to_state == "completed":
        wave.status = "completed"
        if not wave.started_at:
            wave.started_at = utc_now()
        wave.completed_at = utc_now()
    else:
        raise ValueError("Unsupported rollout state")

    db.commit()
    db.refresh(wave)
    return wave


def create_feedback(db: Session, *, user_id: str, payload: FeedbackCreateIn) -> PilotFeedback:
    allowed, reason = is_user_rollout_allowed(db, user_id=user_id)
    if not allowed:
        raise PermissionError(reason)

    row = PilotFeedback(
        user_id=user_id,
        category=payload.category,
        rating=payload.rating,
        message=payload.message,
        status="new",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_feedback_for_user(db: Session, *, user_id: str) -> list[PilotFeedback]:
    return (
        db.query(PilotFeedback)
        .filter(PilotFeedback.user_id == user_id)
        .order_by(PilotFeedback.created_at.desc())
        .all()
    )


def triage_feedback(db: Session, *, feedback_id: str, payload: FeedbackTriageIn) -> PilotFeedback:
    row = db.get(PilotFeedback, feedback_id)
    if not row:
        raise ValueError("Feedback not found")
    row.status = payload.status
    row.triage_notes = payload.triage_notes
    db.commit()
    db.refresh(row)
    return row


def create_usage_event(db: Session, *, user_id: str, payload: UsageEventCreateIn) -> UsageEvent:
    allowed, reason = is_user_rollout_allowed(db, user_id=user_id)
    if not allowed:
        raise PermissionError(reason)

    row = UsageEvent(
        user_id=user_id,
        module=payload.module,
        event_name=payload.event_name,
        metadata_json=json.dumps(payload.metadata) if payload.metadata is not None else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _bucket_for_user_wave(*, user_id: str, wave_id: str) -> int:
    digest = hashlib.sha256(f"{user_id}:{wave_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def is_user_rollout_allowed(db: Session, *, user_id: str) -> tuple[bool, str]:
    pilot = db.query(PilotUser).filter(PilotUser.user_id == user_id).one_or_none()
    if pilot and pilot.status in {"active", "completed"}:
        return True, "pilot-allowed"

    user = db.get(User, user_id)
    if not user or not user.is_active:
        return False, "inactive-user"
    role_names = set(user.role_names())

    candidate_waves = (
        db.query(RolloutWave)
        .filter(RolloutWave.status.in_(["active", "completed"]))
        .order_by(RolloutWave.created_at.desc())
        .all()
    )
    for wave in candidate_waves:
        if wave.target_role and wave.target_role not in role_names:
            continue
        if _bucket_for_user_wave(user_id=user_id, wave_id=wave.id) < int(wave.rollout_percent):
            return True, f"wave-allowed:{wave.name}"

    return False, "user-not-in-active-rollout"


def get_or_create_policy(db: Session) -> RolloutPolicy:
    row = db.query(RolloutPolicy).order_by(RolloutPolicy.updated_at.desc()).first()
    if row:
        return row
    row = RolloutPolicy(
        low_rating_threshold=3,
        error_events_threshold=5,
        evaluation_window_hours=24,
        ramp_steps_csv="10,25,50,100",
        cooldown_minutes=30,
        rollback_percent=0,
        runner_interval_minutes=15,
        alert_suppression_minutes=30,
        notify_email_enabled=True,
        notify_webhook_enabled=False,
        notification_max_attempts=3,
        notification_backoff_base_seconds=30,
        auto_pause_enabled=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def upsert_policy(
    db: Session,
    *,
    low_rating_threshold: int,
    error_events_threshold: int,
    evaluation_window_hours: int,
    ramp_steps: list[int],
    cooldown_minutes: int,
    rollback_percent: int,
    runner_interval_minutes: int,
    alert_suppression_minutes: int,
    notify_email_enabled: bool,
    notify_webhook_enabled: bool,
    notification_max_attempts: int,
    notification_backoff_base_seconds: int,
    auto_pause_enabled: bool,
) -> RolloutPolicy:
    row = get_or_create_policy(db)
    row.low_rating_threshold = low_rating_threshold
    row.error_events_threshold = error_events_threshold
    row.evaluation_window_hours = evaluation_window_hours
    row.ramp_steps_csv = ",".join(str(int(x)) for x in ramp_steps)
    row.cooldown_minutes = cooldown_minutes
    row.rollback_percent = rollback_percent
    row.runner_interval_minutes = runner_interval_minutes
    row.alert_suppression_minutes = alert_suppression_minutes
    row.notify_email_enabled = notify_email_enabled
    row.notify_webhook_enabled = notify_webhook_enabled
    row.notification_max_attempts = notification_max_attempts
    row.notification_backoff_base_seconds = notification_backoff_base_seconds
    row.auto_pause_enabled = auto_pause_enabled
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def _parse_ramp_steps(csv_value: str) -> list[int]:
    steps = []
    for p in csv_value.split(","):
        p = p.strip()
        if not p:
            continue
        val = int(p)
        if val < 0 or val > 100:
            continue
        steps.append(val)
    if not steps:
        return [100]
    return sorted(set(steps))


def run_rollout_automation_tick(db: Session) -> dict[str, object]:
    policy = get_or_create_policy(db)
    now = utc_now()
    steps = _parse_ramp_steps(policy.ramp_steps_csv)
    cooldown_minutes = int(policy.cooldown_minutes)

    waves_started = 0
    waves_ramped = 0
    waves_completed = 0

    # Start planned waves at first configured step.
    planned_waves = db.query(RolloutWave).filter(RolloutWave.status == "planned").all()
    for wave in planned_waves:
        wave.status = "active"
        wave.started_at = wave.started_at or now
        wave.rollout_percent = min(int(steps[0]), 100)
        wave.last_automation_at = now
        waves_started += 1
        if wave.rollout_percent >= 100:
            wave.status = "completed"
            wave.completed_at = now
            waves_completed += 1

    # Ramp currently active waves by one step per tick after cooldown.
    active_waves = db.query(RolloutWave).filter(RolloutWave.status == "active").all()
    for wave in active_waves:
        if wave.last_automation_at and cooldown_minutes > 0:
            diff_mins = (now - wave.last_automation_at).total_seconds() / 60.0
            if diff_mins < cooldown_minutes:
                continue

        current = int(wave.rollout_percent)
        next_step = None
        for step in steps:
            if step > current:
                next_step = step
                break
        if next_step is None:
            if current >= 100:
                wave.status = "completed"
                wave.completed_at = wave.completed_at or now
                waves_completed += 1
            continue

        wave.rollout_percent = int(next_step)
        wave.last_automation_at = now
        waves_ramped += 1
        if wave.rollout_percent >= 100:
            wave.status = "completed"
            wave.completed_at = now
            waves_completed += 1

    db.commit()
    return {
        "ran_at": now,
        "waves_started": waves_started,
        "waves_ramped": waves_ramped,
        "waves_completed": waves_completed,
    }


def evaluate_rollout_health(db: Session) -> dict[str, object]:
    policy = get_or_create_policy(db)
    now = utc_now()
    since = now - timedelta(hours=int(policy.evaluation_window_hours))

    active_waves = db.query(RolloutWave).filter(RolloutWave.status == "active").all()
    active_waves_before = len(active_waves)

    low_ratings_in_window = (
        db.query(PilotFeedback)
        .filter(PilotFeedback.created_at >= since, PilotFeedback.rating.is_not(None), PilotFeedback.rating <= 2)
        .count()
    )
    error_events_in_window = (
        db.query(UsageEvent)
        .filter(UsageEvent.created_at >= since, UsageEvent.event_name.ilike("%error%"))
        .count()
    )

    paused_waves_now = 0
    should_pause = bool(policy.auto_pause_enabled) and (
        low_ratings_in_window >= int(policy.low_rating_threshold)
        or error_events_in_window >= int(policy.error_events_threshold)
    )

    if should_pause:
        reason = (
            f"auto-paused: low_ratings={low_ratings_in_window}, "
            f"error_events={error_events_in_window}, window_h={policy.evaluation_window_hours}"
        )
        for wave in active_waves:
            wave.rollout_percent = min(int(wave.rollout_percent), int(policy.rollback_percent))
            wave.status = "paused"
            wave.paused_at = now
            wave.pause_reason = reason
            wave.last_automation_at = now
            paused_waves_now += 1
        db.commit()
        _create_rollout_alert(
            db,
            severity="critical",
            code="AUTO_PAUSE_TRIGGERED",
            message=reason,
        )
    elif low_ratings_in_window >= int(policy.low_rating_threshold) or error_events_in_window >= int(
        policy.error_events_threshold
    ):
        _create_rollout_alert(
            db,
            severity="warning",
            code="SLO_THRESHOLD_BREACH",
            message=(
                f"slo breach detected: low_ratings={low_ratings_in_window}, "
                f"error_events={error_events_in_window}, window_h={policy.evaluation_window_hours}"
            ),
        )

    return {
        "evaluated_at": now,
        "active_waves_before": active_waves_before,
        "paused_waves_now": paused_waves_now,
        "low_ratings_in_window": low_ratings_in_window,
        "error_events_in_window": error_events_in_window,
    }


def rollout_dashboard(db: Session) -> dict[str, object]:
    pilot_users = db.query(PilotUser).all()
    feedback = db.query(PilotFeedback).all()
    waves = db.query(RolloutWave).all()

    since = utc_now() - timedelta(hours=24)
    recent_events = db.query(UsageEvent).filter(UsageEvent.created_at >= since).all()
    events_by_module: dict[str, int] = {}
    for e in recent_events:
        events_by_module[e.module] = events_by_module.get(e.module, 0) + 1

    return {
        "pilot_users_total": len(pilot_users),
        "pilot_users_active": len([p for p in pilot_users if p.status == "active"]),
        "feedback_total": len(feedback),
        "feedback_open": len([f for f in feedback if f.status in {"new", "triaged"}]),
        "rollout_waves_total": len(waves),
        "rollout_waves_completed": len([w for w in waves if w.status == "completed"]),
        "rollout_waves_paused": len([w for w in waves if w.status == "paused"]),
        "usage_events_24h": len(recent_events),
        "events_by_module": events_by_module,
    }


def _create_rollout_alert(db: Session, *, severity: str, code: str, message: str) -> RolloutAlert:
    now = utc_now()
    policy = get_or_create_policy(db)
    suppression_mins = int(policy.alert_suppression_minutes)

    existing = (
        db.query(RolloutAlert)
        .filter(RolloutAlert.code == code, RolloutAlert.status == "open")
        .order_by(RolloutAlert.created_at.desc())
        .first()
    )
    if existing:
        ref_time = _to_utc_aware(existing.last_seen_at or existing.created_at)
        diff_mins = (now - ref_time).total_seconds() / 60.0
        if diff_mins <= suppression_mins:
            existing.dedup_count = int(existing.dedup_count) + 1
            existing.last_seen_at = now
            existing.message = message
            db.commit()
            db.refresh(existing)
            _dispatch_notifications_for_alert(db, alert=existing)
            return existing

    row = RolloutAlert(
        severity=severity,
        code=code,
        message=message,
        status="open",
        dedup_count=1,
        last_seen_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _dispatch_notifications_for_alert(db, alert=row)
    return row


def _send_channel_stub(*, channel: str, alert: RolloutAlert) -> tuple[bool, str | None]:
    # Stubbed notifier:
    # - webhook channel fails deterministically (simulates flaky downstream endpoint)
    # - any alert code containing FAIL_NOTIFY also fails
    if channel == "webhook":
        return False, "webhook transport failed (stub)"
    if "FAIL_NOTIFY" in alert.code:
        return False, f"{channel} transport failed (stub)"
    return True, None


def _dispatch_notifications_for_alert(db: Session, *, alert: RolloutAlert) -> None:
    policy = get_or_create_policy(db)
    channels: list[str] = []
    if policy.notify_email_enabled:
        channels.append("email")
    if policy.notify_webhook_enabled:
        channels.append("webhook")

    now = utc_now()
    for channel in channels:
        delivery = (
            db.query(NotificationDelivery)
            .filter(NotificationDelivery.alert_id == alert.id, NotificationDelivery.channel == channel)
            .order_by(NotificationDelivery.created_at.desc())
            .first()
        )
        if not delivery:
            delivery = NotificationDelivery(
                alert_id=alert.id,
                channel=channel,
                status="queued",
                attempts=0,
                next_retry_at=now,
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

        _attempt_delivery(db, delivery=delivery, alert=alert)


def _attempt_delivery(db: Session, *, delivery: NotificationDelivery, alert: RolloutAlert) -> NotificationDelivery:
    policy = get_or_create_policy(db)
    now = utc_now()

    ok, err = _send_channel_stub(channel=delivery.channel, alert=alert)
    delivery.attempts = int(delivery.attempts) + 1
    delivery.last_attempt_at = now
    if ok:
        delivery.status = "sent"
        delivery.last_error = None
        delivery.next_retry_at = None
        delivery.dead_lettered_at = None
    else:
        max_attempts = int(policy.notification_max_attempts)
        if int(delivery.attempts) >= max_attempts:
            delivery.status = "dead_letter"
            delivery.last_error = err
            delivery.dead_lettered_at = now
            delivery.next_retry_at = None
            _create_rollout_alert(
                db,
                severity="critical",
                code="NOTIFICATION_DEAD_LETTER",
                message=f"delivery dead-lettered for {delivery.channel}, alert_id={alert.id}",
            )
        else:
            base = int(policy.notification_backoff_base_seconds)
            backoff_seconds = base * (2 ** max(int(delivery.attempts) - 1, 0))
            delivery.status = "failed"
            delivery.last_error = err
            delivery.next_retry_at = now + timedelta(seconds=backoff_seconds)
    db.commit()
    db.refresh(delivery)
    return delivery


def list_notification_deliveries(db: Session) -> list[NotificationDelivery]:
    return db.query(NotificationDelivery).order_by(NotificationDelivery.created_at.desc()).all()


def retry_delivery(db: Session, *, delivery_id: str) -> NotificationDelivery:
    delivery = db.get(NotificationDelivery, delivery_id)
    if not delivery:
        raise ValueError("Delivery not found")
    alert = db.get(RolloutAlert, delivery.alert_id)
    if not alert:
        raise ValueError("Alert not found for delivery")

    return _attempt_delivery(db, delivery=delivery, alert=alert)


def process_pending_notification_retries(db: Session) -> dict[str, int]:
    now = utc_now()
    rows = (
        db.query(NotificationDelivery)
        .filter(
            NotificationDelivery.status == "failed",
            NotificationDelivery.next_retry_at.is_not(None),
            NotificationDelivery.next_retry_at <= now,
        )
        .all()
    )
    processed = 0
    resent_ok = 0
    still_failed = 0
    dead_lettered = 0
    for row in rows:
        alert = db.get(RolloutAlert, row.alert_id)
        if not alert:
            continue
        processed += 1
        updated = _attempt_delivery(db, delivery=row, alert=alert)
        if updated.status == "sent":
            resent_ok += 1
        elif updated.status == "dead_letter":
            dead_lettered += 1
        else:
            still_failed += 1
    return {
        "processed": processed,
        "resent_ok": resent_ok,
        "still_failed": still_failed,
        "dead_lettered": dead_lettered,
    }


def _verify_webhook_signature(*, secret: str, raw_body: str, provided_signature: str | None) -> bool:
    if not provided_signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_signature)


def process_notification_webhook_event(
    db: Session,
    *,
    channel: str,
    external_event_id: str,
    raw_body: str,
    provided_signature: str | None,
    secret: str,
) -> dict[str, object]:
    existing = (
        db.query(NotificationWebhookEvent)
        .filter(NotificationWebhookEvent.external_event_id == external_event_id)
        .one_or_none()
    )
    if existing:
        return {"accepted": True, "duplicate": True, "event_id": existing.external_event_id}

    valid = _verify_webhook_signature(
        secret=secret,
        raw_body=raw_body,
        provided_signature=provided_signature,
    )
    event = NotificationWebhookEvent(
        channel=channel,
        external_event_id=external_event_id,
        signature_valid=valid,
        payload_json=raw_body,
        processed=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if not valid:
        _create_rollout_alert(
            db,
            severity="warning",
            code="WEBHOOK_INVALID_SIGNATURE",
            message=f"Invalid webhook signature for channel={channel}",
        )
        return {"accepted": False, "duplicate": False, "event_id": external_event_id}

    # Apply minimal callback effect: if provider reports delivered, mark queued/failed deliveries as sent.
    try:
        payload = json.loads(raw_body)
    except Exception:
        payload = {}
    status = str(payload.get("status", "")).lower()
    if status in {"delivered", "sent", "ok"}:
        pending = (
            db.query(NotificationDelivery)
            .filter(NotificationDelivery.channel == channel, NotificationDelivery.status.in_(["queued", "failed"]))
            .all()
        )
        for d in pending:
            d.status = "sent"
            d.last_error = None
            d.next_retry_at = None

    event.processed = True
    event.processed_at = utc_now()
    db.commit()
    return {"accepted": True, "duplicate": False, "event_id": external_event_id}


def list_alerts(db: Session) -> list[RolloutAlert]:
    return db.query(RolloutAlert).order_by(RolloutAlert.created_at.desc()).all()


def acknowledge_alert(db: Session, *, alert_id: str, user_id: str) -> RolloutAlert:
    row = db.get(RolloutAlert, alert_id)
    if not row:
        raise ValueError("Alert not found")
    row.status = "acknowledged"
    row.acknowledged_by_user_id = user_id
    row.acknowledged_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def run_scheduled_rollout_cycle(db: Session, *, force: bool = False) -> dict[str, object]:
    policy = get_or_create_policy(db)
    now = utc_now()
    if not force and policy.last_runner_at is not None:
        mins_since_last = (now - _to_utc_aware(policy.last_runner_at)).total_seconds() / 60.0
        if mins_since_last < float(policy.runner_interval_minutes):
            return {
                "ran": False,
                "skipped_reason": "runner-interval-not-reached",
                "ran_at": now,
                "tick": None,
                "health": None,
            }

    tick = run_rollout_automation_tick(db)
    health = evaluate_rollout_health(db)
    policy.last_runner_at = now
    policy.updated_at = now
    db.commit()

    return {
        "ran": True,
        "skipped_reason": None,
        "ran_at": now,
        "tick": tick,
        "health": health,
    }


def alert_digest(db: Session) -> dict[str, object]:
    alerts = db.query(RolloutAlert).all()
    now = utc_now()
    since = now - timedelta(hours=24)

    total_alerts = len(alerts)
    open_alerts = [a for a in alerts if a.status == "open"]
    acknowledged_alerts = [a for a in alerts if a.status == "acknowledged"]
    critical_open_alerts = len([a for a in open_alerts if a.severity == "critical"])
    warnings_open_alerts = len([a for a in open_alerts if a.severity == "warning"])
    alerts_last_24h = len([a for a in alerts if _to_utc_aware(a.created_at) >= since])

    open_by_code: dict[str, int] = {}
    for a in open_alerts:
        open_by_code[a.code] = open_by_code.get(a.code, 0) + 1

    return {
        "total_alerts": total_alerts,
        "open_alerts": len(open_alerts),
        "acknowledged_alerts": len(acknowledged_alerts),
        "critical_open_alerts": critical_open_alerts,
        "warnings_open_alerts": warnings_open_alerts,
        "alerts_last_24h": alerts_last_24h,
        "open_by_code": open_by_code,
    }

