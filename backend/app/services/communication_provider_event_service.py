"""
Normalize inbound provider delivery webhooks and integrate with deliveries, suppressions, and preferences.

Policy (explicit):
- **delivered / opened / clicked**: enrich delivery state or engagement metadata; no suppression.
- **soft bounce / deferred**: record normalized ``deferred``; optional delivery note; no suppression.
- **hard bounce**: delivery → ``bounced``; active ``hard_bounce`` suppression (blocks future sends).
- **spam complaint**: delivery → ``complained`` if was ``sent``/``delivered``; ``spam_complaint`` suppression
  with ``requires_manual_review=True``; disable per-address email preference.
- **unsubscribe / list_unsubscribe**: ``provider_unsubscribe`` suppression; disable per-address email preference;
  delivery left as ``sent`` unless provider signals otherwise.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.communication_provider_event_models import CommunicationProviderEvent
from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.models import Contract
from backend.app.services import customer_communication_preference_service as pref_svc
from backend.app.services.communication_recipient_suppression_service import (
    normalize_email,
    upsert_suppression,
)
from backend.app.services.contract_customer_communication_service import log_communication_provider_audit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def _parse_occurred_at(raw: Any) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


EVENT_TYPE_TO_NORMALIZED: dict[str, str] = {
    "delivered": "delivered",
    "email.delivered": "delivered",
    "delivery.delivered": "delivered",
    "bounce": "bounced",
    "hard_bounce": "bounced",
    "email.bounced": "bounced",
    "soft_bounce": "deferred",
    "deferred": "deferred",
    "complained": "complained",
    "spam_complaint": "complained",
    "email.complained": "complained",
    "unsubscribe": "unsubscribed",
    "list_unsubscribe": "unsubscribed",
    "email.unsubscribed": "unsubscribed",
    "opened": "opened",
    "email.opened": "opened",
    "clicked": "clicked",
    "email.clicked": "clicked",
}


def _normalize_event_type(event_type: str) -> str:
    et = (event_type or "").strip().lower()
    return EVENT_TYPE_TO_NORMALIZED.get(et, "unknown")


def normalize_provider_message_id_key(raw: str | None) -> str:
    """Strip SendGrid filter suffixes (e.g. ``abc.filter0000.0.0`` → ``abc``) for delivery correlation."""
    if not raw:
        return ""
    s = raw.strip().strip("<>")
    return s.split(".")[0].strip()


def find_delivery_by_provider_message_id(
    db: Session, *, provider_message_id: str
) -> ContractCustomerCommunicationDelivery | None:
    if not provider_message_id:
        return None
    row = (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.provider_message_id == provider_message_id)
        .order_by(ContractCustomerCommunicationDelivery.attempt_number.desc())
        .first()
    )
    if row:
        return row
    norm = normalize_provider_message_id_key(provider_message_id)
    if not norm:
        return None
    return (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(
            ContractCustomerCommunicationDelivery.provider_message_id.isnot(None),
            ContractCustomerCommunicationDelivery.provider_message_id.like(f"{norm}%"),
        )
        .order_by(ContractCustomerCommunicationDelivery.attempt_number.desc())
        .first()
    )


def _resolve_customer_id(db: Session, *, comm: ContractCustomerCommunication) -> str | None:
    if comm.recipient_customer_id:
        return comm.recipient_customer_id
    ctr = db.get(Contract, comm.contract_id)
    return ctr.customer_id if ctr else None


def _merge_engagement(
    delivery: ContractCustomerCommunicationDelivery, *, key: str, event_id: str, occurred_at: datetime | None
) -> None:
    existing = _loads(delivery.response_payload_json) or {}
    eng = dict(existing.get("provider_engagement") or {})
    eng[key] = {"event_id": event_id, "occurred_at": occurred_at.isoformat() if occurred_at else None}
    existing["provider_engagement"] = eng
    delivery.response_payload_json = _dumps(existing)


def _apply_delivery_enrichment(
    db: Session,
    *,
    delivery: ContractCustomerCommunicationDelivery,
    comm: ContractCustomerCommunication,
    normalized: str,
    detail: str,
    event_row: CommunicationProviderEvent,
) -> None:
    if normalized == "delivered":
        if delivery.status == "sent":
            delivery.status = "delivered"
            delivery.completed_at = delivery.completed_at or utc_now()
            log_communication_provider_audit(
                db,
                contract_id=comm.contract_id,
                action_type="communication_delivered",
                summary=f"Delivery {delivery.id} marked delivered via provider event",
                payload={
                    "delivery_id": delivery.id,
                    "communication_id": comm.id,
                    "provider_event_id": event_row.id,
                },
            )
        return

    if normalized == "deferred":
        payload = _loads(delivery.response_payload_json) or {}
        payload["provider_deferred"] = {"detail": detail[:1000], "event_id": event_row.id}
        delivery.response_payload_json = _dumps(payload)
        return

    if normalized == "bounced":
        delivery.status = "bounced"
        delivery.completed_at = utc_now()
        delivery.error_code = "provider_bounce"
        delivery.error_message = detail[:2000] or "Provider reported bounce"
        log_communication_provider_audit(
            db,
            contract_id=comm.contract_id,
            action_type="communication_bounced",
            summary=f"Delivery {delivery.id} bounced",
            payload={
                "delivery_id": delivery.id,
                "communication_id": comm.id,
                "provider_event_id": event_row.id,
            },
        )
        return

    if normalized == "complained":
        if delivery.status in ("sent", "delivered"):
            delivery.status = "complained"
        delivery.completed_at = delivery.completed_at or utc_now()
        payload = _loads(delivery.response_payload_json) or {}
        payload["spam_complaint"] = {"event_id": event_row.id, "detail": detail[:1000]}
        delivery.response_payload_json = _dumps(payload)
        log_communication_provider_audit(
            db,
            contract_id=comm.contract_id,
            action_type="communication_complained",
            summary=f"Spam complaint recorded for delivery {delivery.id}",
            payload={
                "delivery_id": delivery.id,
                "communication_id": comm.id,
                "provider_event_id": event_row.id,
            },
        )
        return

    if normalized in ("opened", "clicked"):
        _merge_engagement(
            delivery, key=normalized, event_id=event_row.id, occurred_at=event_row.occurred_at
        )
        return

    # unsubscribed: do not rewrite delivery success; suppression handles future safety
    if normalized == "unsubscribed":
        log_communication_provider_audit(
            db,
            contract_id=comm.contract_id,
            action_type="communication_unsubscribed",
            summary=f"Provider unsubscribe for delivery {delivery.id}",
            payload={
                "delivery_id": delivery.id,
                "communication_id": comm.id,
                "provider_event_id": event_row.id,
            },
        )


def _apply_suppression_and_preferences(
    db: Session,
    *,
    contract_id: str,
    customer_id: str,
    email: str,
    normalized: str,
    event_row: CommunicationProviderEvent,
    detail: str,
) -> None:
    if normalized == "bounced":
        upsert_suppression(
            db,
            customer_id=customer_id,
            recipient_email=email,
            kind="hard_bounce",
            requires_manual_review=False,
            provider_event_id=event_row.id,
            notes=f"hard_bounce: {detail[:500]}",
            commit=False,
        )
        return

    if normalized == "complained":
        upsert_suppression(
            db,
            customer_id=customer_id,
            recipient_email=email,
            kind="spam_complaint",
            requires_manual_review=True,
            provider_event_id=event_row.id,
            notes=f"spam_complaint: {detail[:500]}",
            commit=False,
        )
        pref_svc.disable_email_address_from_provider_event(
            db,
            customer_id=customer_id,
            email=email,
            audit_note=f"[provider] spam complaint event {event_row.id}",
            commit=False,
        )
        log_communication_provider_audit(
            db,
            contract_id=contract_id,
            action_type="communication_preference_disabled_from_provider_event",
            summary=f"Disabled email preference for {email} after spam complaint",
            payload={"customer_id": customer_id, "provider_event_id": event_row.id},
        )
        return

    if normalized == "unsubscribed":
        upsert_suppression(
            db,
            customer_id=customer_id,
            recipient_email=email,
            kind="provider_unsubscribe",
            requires_manual_review=False,
            provider_event_id=event_row.id,
            notes=f"unsubscribe: {detail[:500]}",
            commit=False,
        )
        pref_svc.disable_email_address_from_provider_event(
            db,
            customer_id=customer_id,
            email=email,
            audit_note=f"[provider] unsubscribe event {event_row.id}",
            commit=False,
        )
        log_communication_provider_audit(
            db,
            contract_id=contract_id,
            action_type="communication_preference_disabled_from_provider_event",
            summary=f"Disabled email preference for {email} after provider unsubscribe",
            payload={"customer_id": customer_id, "provider_event_id": event_row.id},
        )


def ingest_phi_generic_webhook(
    db: Session,
    *,
    payload: dict[str, Any],
    raw_body_for_storage: str,
    commit: bool = True,
) -> dict[str, Any]:
    """
    Process ``phi_generic_v1`` JSON envelope after signature verification.

    Returns a result dict suitable for HTTP JSON (includes processing_status, event id, etc.).
    """
    fmt = (payload.get("format") or "").strip()
    if fmt != "phi_generic_v1":
        return {"accepted": False, "reason": "unsupported_format", "processing_status": "failed"}

    ext_id = (payload.get("external_event_id") or payload.get("idempotency_key") or "").strip() or None
    if ext_id:
        dup = (
            db.query(CommunicationProviderEvent)
            .filter(CommunicationProviderEvent.external_event_id == ext_id)
            .first()
        )
        if dup:
            return {
                "accepted": True,
                "duplicate": True,
                "provider_event_id": dup.id,
                "processing_status": dup.processing_status,
            }

    provider_name = (payload.get("provider_name") or "unknown").strip()[:64]
    event_type = (payload.get("event_type") or "").strip()[:128]
    provider_message_id = (payload.get("provider_message_id") or "").strip() or None
    recipient = (payload.get("recipient") or payload.get("recipient_address") or "").strip() or None
    occurred_at = _parse_occurred_at(payload.get("occurred_at"))
    detail = (payload.get("detail") or payload.get("message") or "").strip()
    raw_status = (payload.get("status") or event_type or "unknown")[:32]

    normalized = _normalize_event_type(event_type)
    if raw_status and normalized == "unknown":
        normalized = _normalize_event_type(str(raw_status))

    delivery = (
        find_delivery_by_provider_message_id(db, provider_message_id=provider_message_id)
        if provider_message_id
        else None
    )
    comm: ContractCustomerCommunication | None = None
    if delivery:
        comm = db.get(ContractCustomerCommunication, delivery.communication_id)

    event_row = CommunicationProviderEvent(
        id=str(uuid.uuid4()),
        provider_name=provider_name,
        event_type=event_type or "unknown",
        provider_message_id=provider_message_id,
        communication_id=comm.id if comm else None,
        delivery_id=delivery.id if delivery else None,
        recipient_address=recipient,
        occurred_at=occurred_at,
        received_at=utc_now(),
        status=raw_status,
        normalized_status=normalized if normalized != "unknown" else None,
        payload_json=raw_body_for_storage,
        processing_status="received",
        external_event_id=ext_id,
    )
    db.add(event_row)
    db.flush()

    result: dict[str, Any] = {
        "accepted": True,
        "duplicate": False,
        "provider_event_id": event_row.id,
        "normalized_status": normalized,
    }

    if not delivery or not comm:
        event_row.processing_status = "ignored"
        event_row.processing_result_json = _dumps(
            {"reason": "no_matching_delivery", "provider_message_id": provider_message_id}
        )
        if commit:
            db.commit()
            db.refresh(event_row)
        else:
            db.flush()
        result["processing_status"] = "ignored"
        return result

    event_row.communication_id = comm.id
    event_row.delivery_id = delivery.id
    customer_id = _resolve_customer_id(db, comm=comm)
    email_guess = normalize_email(recipient or (delivery.recipient_address or ""))

    if normalized == "unknown":
        event_row.processing_status = "ignored"
        event_row.processing_result_json = _dumps({"reason": "unknown_event_type", "event_type": event_type})
        if commit:
            db.commit()
        else:
            db.flush()
        result["processing_status"] = "ignored"
        return result

    _apply_delivery_enrichment(
        db,
        delivery=delivery,
        comm=comm,
        normalized=normalized,
        detail=detail,
        event_row=event_row,
    )

    if customer_id and email_guess and normalized in ("bounced", "complained", "unsubscribed"):
        _apply_suppression_and_preferences(
            db,
            contract_id=comm.contract_id,
            customer_id=customer_id,
            email=email_guess,
            normalized=normalized,
            event_row=event_row,
            detail=detail,
        )

    event_row.processing_status = "processed"
    event_row.processing_result_json = _dumps(
        {"delivery_id": delivery.id, "communication_id": comm.id, "normalized_status": normalized}
    )
    event_row.normalized_status = normalized

    db.add(delivery)
    db.add(comm)
    if commit:
        db.commit()
        db.refresh(event_row)
    else:
        db.flush()

    result["processing_status"] = "processed"
    return result


def list_events_for_communication(db: Session, *, communication_id: str) -> list[CommunicationProviderEvent]:
    return (
        db.query(CommunicationProviderEvent)
        .filter(CommunicationProviderEvent.communication_id == communication_id)
        .order_by(CommunicationProviderEvent.received_at.desc())
        .all()
    )