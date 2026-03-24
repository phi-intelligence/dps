"""
Cross-cutting operational failure visibility (§5.7): jobs, activations, comms delivery,
inbound provider webhooks, rollout notification pipeline.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.communication_provider_event_models import CommunicationProviderEvent
from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.contract_version_models import ContractActivationRun
from backend.app.modules.rollout.models import NotificationDelivery, NotificationWebhookEvent
from backend.app.modules.system.recurring_system_job_models import RecurringSystemJobRun


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def operations_diagnostics_summary(
    db: Session,
    *,
    limit_each: int = 40,
) -> dict[str, Any]:
    cap = min(max(limit_each, 1), 200)

    failed_jobs = (
        db.query(RecurringSystemJobRun)
        .filter(RecurringSystemJobRun.status == "failed")
        .order_by(RecurringSystemJobRun.started_at.desc())
        .limit(cap)
        .all()
    )
    failed_activations = (
        db.query(ContractActivationRun)
        .filter(ContractActivationRun.status == "failed")
        .order_by(ContractActivationRun.started_at.desc())
        .limit(cap)
        .all()
    )
    failed_deliveries = (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.status == "failed")
        .order_by(ContractCustomerCommunicationDelivery.started_at.desc())
        .limit(cap)
        .all()
    )

    failed_comm_provider_events = (
        db.query(CommunicationProviderEvent)
        .filter(CommunicationProviderEvent.processing_status == "failed")
        .order_by(CommunicationProviderEvent.received_at.desc())
        .limit(cap)
        .all()
    )

    bad_rollout_webhooks = (
        db.query(NotificationWebhookEvent)
        .filter(NotificationWebhookEvent.signature_valid.is_(False))
        .order_by(NotificationWebhookEvent.created_at.desc())
        .limit(cap)
        .all()
    )

    rollout_delivery_failures = (
        db.query(NotificationDelivery)
        .filter(NotificationDelivery.status.in_(("failed", "dead_letter")))
        .order_by(NotificationDelivery.created_at.desc())
        .limit(cap)
        .all()
    )

    return {
        "recurring_job_failures": [
            {
                "id": r.id,
                "job_key": r.job_key,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "dry_run": r.dry_run,
                "error_message": (_loads(r.error_json) or {}).get("message"),
            }
            for r in failed_jobs
        ],
        "contract_activation_failures": [
            {
                "id": r.id,
                "amendment_id": r.amendment_id,
                "contract_id": r.contract_id,
                "run_type": r.run_type,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "result_summary": (r.result_summary or "")[:500] if r.result_summary else None,
            }
            for r in failed_activations
        ],
        "customer_communication_delivery_failures": [
            {
                "id": d.id,
                "communication_id": d.communication_id,
                "channel": d.channel,
                "provider_name": d.provider_name,
                "started_at": d.started_at.isoformat() if d.started_at else None,
                "error_code": d.error_code,
                "error_message": (d.error_message or "")[:400] if d.error_message else None,
            }
            for d in failed_deliveries
        ],
        "communication_provider_webhook_failures": [
            {
                "id": e.id,
                "provider_name": e.provider_name,
                "event_type": e.event_type,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "error_message": (e.error_message or "")[:400] if e.error_message else None,
                "communication_id": e.communication_id,
                "delivery_id": e.delivery_id,
            }
            for e in failed_comm_provider_events
        ],
        "rollout_notification_delivery_failures": [
            {
                "id": d.id,
                "alert_id": d.alert_id,
                "channel": d.channel,
                "status": d.status,
                "attempts": d.attempts,
                "last_error": (d.last_error or "")[:400] if d.last_error else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in rollout_delivery_failures
        ],
        "rollout_webhook_invalid_signatures": [
            {
                "id": e.id,
                "channel": e.channel,
                "external_event_id": e.external_event_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "processed": e.processed,
            }
            for e in bad_rollout_webhooks
        ],
        "counts": {
            "recurring_job_failures_shown": len(failed_jobs),
            "activation_failures_shown": len(failed_activations),
            "communication_delivery_failures_shown": len(failed_deliveries),
            "communication_provider_webhook_failures_shown": len(failed_comm_provider_events),
            "rollout_notification_delivery_failures_shown": len(rollout_delivery_failures),
            "rollout_webhook_invalid_signatures_shown": len(bad_rollout_webhooks),
        },
    }
