"""
Structured hooks for customer-facing milestones. Persist events; channel delivery is pluggable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.portal.models import CustomerCommsEvent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Canonical event types (extend as product grows)
QUOTE_SENT = "quote_sent"
QUOTE_ACCEPTED = "quote_accepted"
JOB_SCHEDULED = "job_scheduled"
ENGINEER_ON_THE_WAY = "engineer_on_the_way"
JOB_COMPLETED = "job_completed"
CERTIFICATE_READY = "certificate_ready"
INVOICE_ISSUED = "invoice_issued"
PAYMENT_RECEIVED = "payment_received"


def emit_customer_comms_event(
    db: Session,
    *,
    job_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    delivery_status: str = "logged",
    commit: bool = True,
) -> CustomerCommsEvent:
    row = CustomerCommsEvent(
        job_id=job_id,
        event_type=event_type,
        payload_json=json.dumps(payload or {}),
        delivery_status=delivery_status,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def log_quote_sent(db: Session, *, job_id: str | None, quote_id: str) -> None:
    if not job_id:
        return
    emit_customer_comms_event(db, job_id=job_id, event_type=QUOTE_SENT, payload={"quote_id": quote_id})


def log_quote_accepted(db: Session, *, job_id: str | None, quote_id: str) -> None:
    if not job_id:
        return
    emit_customer_comms_event(db, job_id=job_id, event_type=QUOTE_ACCEPTED, payload={"quote_id": quote_id})


def log_engineer_on_the_way(db: Session, *, job_id: str, source: str, commit: bool = True) -> None:
    emit_customer_comms_event(
        db,
        job_id=job_id,
        event_type=ENGINEER_ON_THE_WAY,
        payload={"source": source},
        commit=commit,
    )
