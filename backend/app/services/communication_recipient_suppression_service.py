"""
Recipient-level suppression for contract customer communications (bounce / complaint / unsubscribe).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.communication_provider_event_models import CommunicationRecipientSuppression


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def find_active_suppressions(
    db: Session, *, customer_id: str, recipient_email: str
) -> list[CommunicationRecipientSuppression]:
    norm = normalize_email(recipient_email)
    if not norm:
        return []
    return (
        db.query(CommunicationRecipientSuppression)
        .filter(
            CommunicationRecipientSuppression.customer_id == customer_id,
            CommunicationRecipientSuppression.recipient_email_normalized == norm,
            CommunicationRecipientSuppression.active.is_(True),
        )
        .all()
    )


def is_outbound_blocked(
    db: Session, *, customer_id: str, recipient_email: str
) -> tuple[bool, str | None]:
    rows = find_active_suppressions(db, customer_id=customer_id, recipient_email=recipient_email)
    if not rows:
        return False, None
    kinds = sorted({r.kind for r in rows})
    review = any(r.requires_manual_review for r in rows)
    detail = f"Recipient suppressed ({', '.join(kinds)})"
    if review:
        detail += "; manual review required for at least one signal"
    return True, detail


def upsert_suppression(
    db: Session,
    *,
    customer_id: str,
    recipient_email: str,
    kind: str,
    requires_manual_review: bool,
    provider_event_id: str | None,
    notes: str | None,
    commit: bool = False,
) -> CommunicationRecipientSuppression:
    norm = normalize_email(recipient_email)
    row = (
        db.query(CommunicationRecipientSuppression)
        .filter(
            CommunicationRecipientSuppression.customer_id == customer_id,
            CommunicationRecipientSuppression.recipient_email_normalized == norm,
            CommunicationRecipientSuppression.kind == kind,
        )
        .first()
    )
    now = utc_now()
    if row:
        row.active = True
        row.requires_manual_review = row.requires_manual_review or requires_manual_review
        row.last_seen_at = now
        row.last_provider_event_id = provider_event_id or row.last_provider_event_id
        if notes:
            row.notes = (row.notes + "\n" if row.notes else "") + notes
        db.add(row)
    else:
        row = CommunicationRecipientSuppression(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            recipient_email_normalized=norm,
            kind=kind,
            active=True,
            requires_manual_review=requires_manual_review,
            first_seen_at=now,
            last_seen_at=now,
            last_provider_event_id=provider_event_id,
            notes=notes,
        )
        db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def list_suppressions_for_customer(db: Session, *, customer_id: str) -> list[CommunicationRecipientSuppression]:
    return (
        db.query(CommunicationRecipientSuppression)
        .filter(CommunicationRecipientSuppression.customer_id == customer_id)
        .order_by(CommunicationRecipientSuppression.last_seen_at.desc())
        .all()
    )


def dashboard_hygiene_summary(db: Session, *, limit: int = 100) -> dict[str, Any]:
    from backend.app.modules.contracts.communication_provider_event_models import CommunicationProviderEvent
    from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
        ContractCustomerCommunicationDelivery,
    )

    recent_bad_deliveries = (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.status.in_(("bounced", "complained", "failed")))
        .order_by(ContractCustomerCommunicationDelivery.started_at.desc())
        .limit(limit)
        .all()
    )
    active_suppressions = (
        db.query(CommunicationRecipientSuppression)
        .filter(CommunicationRecipientSuppression.active.is_(True))
        .order_by(CommunicationRecipientSuppression.last_seen_at.desc())
        .limit(limit)
        .all()
    )
    pending_review = (
        db.query(CommunicationRecipientSuppression)
        .filter(
            CommunicationRecipientSuppression.active.is_(True),
            CommunicationRecipientSuppression.requires_manual_review.is_(True),
        )
        .order_by(CommunicationRecipientSuppression.last_seen_at.desc())
        .limit(limit)
        .all()
    )
    recent_events = (
        db.query(CommunicationProviderEvent)
        .order_by(CommunicationProviderEvent.received_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "recent_failed_or_bad_deliveries": [
            {
                "delivery_id": d.id,
                "communication_id": d.communication_id,
                "status": d.status,
                "provider_message_id": d.provider_message_id,
                "recipient_address": d.recipient_address,
                "started_at": d.started_at.isoformat() if d.started_at else None,
            }
            for d in recent_bad_deliveries
        ],
        "active_suppressions": [
            {
                "suppression_id": s.id,
                "customer_id": s.customer_id,
                "recipient_email_normalized": s.recipient_email_normalized,
                "kind": s.kind,
                "requires_manual_review": s.requires_manual_review,
                "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
            }
            for s in active_suppressions
        ],
        "suppressions_pending_review": [
            {
                "suppression_id": s.id,
                "customer_id": s.customer_id,
                "recipient_email_normalized": s.recipient_email_normalized,
                "kind": s.kind,
                "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
            }
            for s in pending_review
        ],
        "recent_provider_events": [
            {
                "event_id": e.id,
                "provider_name": e.provider_name,
                "event_type": e.event_type,
                "normalized_status": e.normalized_status,
                "processing_status": e.processing_status,
                "delivery_id": e.delivery_id,
                "received_at": e.received_at.isoformat() if e.received_at else None,
            }
            for e in recent_events
        ],
    }


def dashboard_provider_events(db: Session, *, limit: int = 100) -> dict[str, Any]:
    from backend.app.modules.contracts.communication_provider_event_models import CommunicationProviderEvent

    rows = (
        db.query(CommunicationProviderEvent)
        .order_by(CommunicationProviderEvent.received_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": r.id,
                "provider_name": r.provider_name,
                "event_type": r.event_type,
                "normalized_status": r.normalized_status,
                "processing_status": r.processing_status,
                "provider_message_id": r.provider_message_id,
                "communication_id": r.communication_id,
                "delivery_id": r.delivery_id,
                "recipient_address": r.recipient_address,
                "received_at": r.received_at.isoformat() if r.received_at else None,
            }
            for r in rows
        ],
        "count": len(rows),
    }


def communication_safety_for_customer(db: Session, *, customer_id: str) -> dict[str, Any]:
    from backend.app.modules.crm.models import Customer

    if not db.get(Customer, customer_id):
        raise ValueError("Customer not found")
    prefs_blocked = list_suppressions_for_customer(db, customer_id=customer_id)
    return {
        "customer_id": customer_id,
        "suppressions": [
            {
                "id": s.id,
                "recipient_email_normalized": s.recipient_email_normalized,
                "kind": s.kind,
                "active": s.active,
                "requires_manual_review": s.requires_manual_review,
                "first_seen_at": s.first_seen_at.isoformat() if s.first_seen_at else None,
                "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
                "notes": s.notes,
            }
            for s in prefs_blocked
        ],
    }
