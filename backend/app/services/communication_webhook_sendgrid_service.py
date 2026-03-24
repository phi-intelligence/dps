"""
Normalize SendGrid Event Webhook payloads (JSON array) into phi_generic_v1 and ingest.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.services.communication_provider_event_service import (
    ingest_phi_generic_webhook,
    normalize_provider_message_id_key,
)


def _occurred_at_iso(ev: dict[str, Any]) -> str | None:
    ts = ev.get("timestamp")
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    return None


def sendgrid_event_to_phi_generic_v1(ev: dict[str, Any]) -> dict[str, Any]:
    """Map one SendGrid event object to our normalized webhook envelope."""
    event = str(ev.get("event") or "").lower()
    email = str(ev.get("email") or "").strip()
    sg_mid_raw = str(ev.get("sg_message_id") or ev.get("smtp-id") or "").strip()
    sg_mid = normalize_provider_message_id_key(sg_mid_raw) or sg_mid_raw
    status = str(ev.get("status") or "")
    reason = str(ev.get("reason") or ev.get("type") or ev.get("bounce_classification") or "")

    if event == "delivered":
        et = "delivered"
    elif event == "open":
        et = "opened"
    elif event == "click":
        et = "clicked"
    elif event == "spamreport":
        et = "spam_complaint"
    elif event in ("unsubscribe", "group_unsubscribe"):
        et = "unsubscribe"
    elif event == "bounce":
        et = "hard_bounce" if status.startswith("5") else "soft_bounce"
    elif event == "dropped":
        et = "deferred"
    else:
        et = event or "unknown"

    detail_parts = [p for p in (reason, status, event) if p]
    detail = "; ".join(detail_parts) if detail_parts else event

    ext = str(ev.get("sg_event_id") or "").strip()
    if not ext:
        ext = f"sendgrid|{sg_mid}|{event}|{email}|{ev.get('timestamp', '')}"[:500]

    return {
        "format": "phi_generic_v1",
        "external_event_id": ext[:512],
        "provider_name": "sendgrid",
        "event_type": et,
        "provider_message_id": sg_mid or None,
        "recipient": email,
        "occurred_at": _occurred_at_iso(ev),
        "detail": detail[:2000],
        "status": et,
    }


def ingest_sendgrid_events_batch(
    db: Session,
    events: list[Any],
    *,
    commit: bool = True,
) -> dict[str, Any]:
    if not isinstance(events, list):
        return {"accepted": False, "reason": "expected_array", "results": []}

    results: list[dict[str, Any]] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        phi = sendgrid_event_to_phi_generic_v1(ev)
        raw_store = json.dumps(ev, separators=(",", ":"), default=str)
        results.append(
            ingest_phi_generic_webhook(
                db,
                payload=phi,
                raw_body_for_storage=raw_store,
                commit=False,
            )
        )
    if commit:
        db.commit()
    return {"accepted": True, "processed": len(results), "results": results}
