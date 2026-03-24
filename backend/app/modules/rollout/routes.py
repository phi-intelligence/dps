from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.modules.rollout.schemas import (
    FeedbackCreateIn,
    FeedbackOut,
    FeedbackTriageIn,
    RolloutGuardOut,
    RolloutHealthEvaluationOut,
    RolloutAutomationRunOut,
    RolloutAlertOut,
    RolloutAlertDigestOut,
    NotificationDeliveryOut,
    NotificationRetryRunOut,
    NotificationWebhookIn,
    NotificationWebhookOut,
    RolloutCycleRunOut,
    RolloutPolicyOut,
    RolloutPolicyUpsertIn,
    PilotUserOut,
    PilotUserUpsertIn,
    RolloutDashboardOut,
    RolloutWaveCreateIn,
    RolloutWaveOut,
    UsageEventCreateIn,
    UsageEventOut,
)
from backend.app.modules.rollout.service import (
    create_feedback,
    create_usage_event,
    create_wave,
    acknowledge_alert,
    evaluate_rollout_health,
    get_or_create_policy,
    is_user_rollout_allowed,
    list_feedback_for_user,
    list_pilot_users,
    list_waves,
    rollout_dashboard,
    run_scheduled_rollout_cycle,
    run_rollout_automation_tick,
    list_alerts,
    alert_digest,
    list_notification_deliveries,
    process_pending_notification_retries,
    process_notification_webhook_event,
    retry_delivery,
    triage_feedback,
    update_wave_state,
    upsert_policy,
    upsert_pilot_user,
)


router = APIRouter(prefix="/rollout", tags=["rollout"])


@router.post("/pilot/users", response_model=PilotUserOut, status_code=status.HTTP_201_CREATED)
def upsert_pilot_user_endpoint(
    payload: PilotUserUpsertIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> PilotUserOut:
    return upsert_pilot_user(db, payload=payload)


@router.get("/pilot/users", response_model=list[PilotUserOut])
def list_pilot_users_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[PilotUserOut]:
    return list_pilot_users(db)


@router.post("/waves", response_model=RolloutWaveOut, status_code=status.HTTP_201_CREATED)
def create_wave_endpoint(
    payload: RolloutWaveCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin")),
) -> RolloutWaveOut:
    try:
        return create_wave(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/waves", response_model=list[RolloutWaveOut])
def list_waves_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RolloutWaveOut]:
    return list_waves(db)


@router.post("/waves/{wave_id}/start", response_model=RolloutWaveOut)
def start_wave_endpoint(
    wave_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin")),
) -> RolloutWaveOut:
    try:
        return update_wave_state(db, wave_id=wave_id, to_state="active")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/waves/{wave_id}/complete", response_model=RolloutWaveOut)
def complete_wave_endpoint(
    wave_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin")),
) -> RolloutWaveOut:
    try:
        return update_wave_state(db, wave_id=wave_id, to_state="completed")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback_endpoint(
    payload: FeedbackCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FeedbackOut:
    try:
        return create_feedback(db, user_id=current_user.id, payload=payload)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/feedback/me", response_model=list[FeedbackOut])
def list_my_feedback_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[FeedbackOut]:
    return list_feedback_for_user(db, user_id=current_user.id)


@router.post("/feedback/{feedback_id}/triage", response_model=FeedbackOut)
def triage_feedback_endpoint(
    feedback_id: str,
    payload: FeedbackTriageIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> FeedbackOut:
    try:
        return triage_feedback(db, feedback_id=feedback_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/events", response_model=UsageEventOut, status_code=status.HTTP_201_CREATED)
def create_event_endpoint(
    payload: UsageEventCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UsageEventOut:
    try:
        return create_usage_event(db, user_id=current_user.id, payload=payload)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/guard/me", response_model=RolloutGuardOut)
def guard_me_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> RolloutGuardOut:
    allowed, reason = is_user_rollout_allowed(db, user_id=current_user.id)
    return RolloutGuardOut(allowed=allowed, reason=reason)


@router.get("/dashboard", response_model=RolloutDashboardOut)
def rollout_dashboard_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutDashboardOut:
    return RolloutDashboardOut(**rollout_dashboard(db))


@router.get("/policy", response_model=RolloutPolicyOut)
def rollout_policy_get_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutPolicyOut:
    return get_or_create_policy(db)


@router.post("/policy", response_model=RolloutPolicyOut)
def rollout_policy_upsert_endpoint(
    payload: RolloutPolicyUpsertIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin")),
) -> RolloutPolicyOut:
    return upsert_policy(
        db,
        low_rating_threshold=payload.low_rating_threshold,
        error_events_threshold=payload.error_events_threshold,
        evaluation_window_hours=payload.evaluation_window_hours,
        ramp_steps=payload.ramp_steps,
        cooldown_minutes=payload.cooldown_minutes,
        rollback_percent=payload.rollback_percent,
        runner_interval_minutes=payload.runner_interval_minutes,
        alert_suppression_minutes=payload.alert_suppression_minutes,
        notify_email_enabled=payload.notify_email_enabled,
        notify_webhook_enabled=payload.notify_webhook_enabled,
        notification_max_attempts=payload.notification_max_attempts,
        notification_backoff_base_seconds=payload.notification_backoff_base_seconds,
        auto_pause_enabled=payload.auto_pause_enabled,
    )


@router.post("/health/evaluate", response_model=RolloutHealthEvaluationOut)
def rollout_health_evaluate_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutHealthEvaluationOut:
    return RolloutHealthEvaluationOut(**evaluate_rollout_health(db))


@router.post("/automation/tick", response_model=RolloutAutomationRunOut)
def rollout_automation_tick_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutAutomationRunOut:
    return RolloutAutomationRunOut(**run_rollout_automation_tick(db))


@router.post("/automation/run-cycle", response_model=RolloutCycleRunOut)
def rollout_automation_run_cycle_endpoint(
    force: bool = False,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutCycleRunOut:
    return RolloutCycleRunOut(**run_scheduled_rollout_cycle(db, force=force))


@router.get("/alerts", response_model=list[RolloutAlertOut])
def rollout_alerts_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RolloutAlertOut]:
    return list_alerts(db)


@router.get("/alerts/digest", response_model=RolloutAlertDigestOut)
def rollout_alerts_digest_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutAlertDigestOut:
    return RolloutAlertDigestOut(**alert_digest(db))


@router.post("/alerts/{alert_id}/ack", response_model=RolloutAlertOut)
def rollout_alert_ack_endpoint(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> RolloutAlertOut:
    try:
        return acknowledge_alert(db, alert_id=alert_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/notifications/deliveries", response_model=list[NotificationDeliveryOut])
def rollout_notification_deliveries_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[NotificationDeliveryOut]:
    return list_notification_deliveries(db)


@router.post("/notifications/deliveries/{delivery_id}/retry", response_model=NotificationDeliveryOut)
def rollout_notification_retry_endpoint(
    delivery_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> NotificationDeliveryOut:
    try:
        return retry_delivery(db, delivery_id=delivery_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/notifications/retries/process", response_model=NotificationRetryRunOut)
def rollout_notification_process_retries_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> NotificationRetryRunOut:
    return NotificationRetryRunOut(**process_pending_notification_retries(db))


@router.post("/notifications/webhooks/{channel}", response_model=NotificationWebhookOut)
async def rollout_notification_webhook_endpoint(
    channel: str,
    request: Request,
    db: Session = Depends(get_db),
    x_event_id: str | None = Header(default=None, alias="X-Event-Id"),
    x_signature: str | None = Header(default=None, alias="X-Signature"),
) -> NotificationWebhookOut:
    if channel not in {"email", "webhook"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported channel")
    if not x_event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Event-Id")

    raw_body = (await request.body()).decode("utf-8")
    try:
        NotificationWebhookIn.model_validate(json.loads(raw_body))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload") from e

    result = process_notification_webhook_event(
        db,
        channel=channel,
        external_event_id=x_event_id,
        raw_body=raw_body,
        provided_signature=x_signature,
        secret=settings.NOTIFICATION_WEBHOOK_SECRET,
    )
    return NotificationWebhookOut(**result)

