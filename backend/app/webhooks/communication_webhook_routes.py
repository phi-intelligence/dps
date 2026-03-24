"""
Authenticated (HMAC) ingress for email provider delivery events.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services.communication_provider_event_service import ingest_phi_generic_webhook
from backend.app.services.communication_webhook_sendgrid_service import ingest_sendgrid_events_batch
from backend.app.services.communication_webhook_verification_service import verify_communication_webhook_signature

router = APIRouter(prefix="/webhooks/communications", tags=["webhooks-communications"])

_SENDGRID_INGEST_HEADER = "x-phi-dps-sendgrid-ingest-secret"


@router.post("/provider")
async def communication_provider_webhook_endpoint(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    raw_bytes = await request.body()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Body must be UTF-8"
        ) from e

    sig = request.headers.get("X-Phi-Dps-Communication-Signature") or request.headers.get(
        "x-phi-dps-communication-signature"
    )
    if not verify_communication_webhook_signature(raw_body=raw_text, provided_signature=sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body"
        ) from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON object required")

    return ingest_phi_generic_webhook(db, payload=payload, raw_body_for_storage=raw_text, commit=True)


@router.post("/sendgrid-events")
async def sendgrid_communication_events_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Ingest SendGrid Event Webhook JSON array. Protect with shared secret header
    ``X-Phi-Dps-Sendgrid-Ingest-Secret`` (``PHI_DPS_SENDGRID_WEBHOOK_INGEST_SECRET``).
    """
    if not settings.SENDGRID_WEBHOOK_INGEST_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SendGrid webhook ingest is not configured (PHI_DPS_SENDGRID_WEBHOOK_INGEST_SECRET)",
        )
    provided = (
        request.headers.get(_SENDGRID_INGEST_HEADER)
        or request.headers.get(_SENDGRID_INGEST_HEADER.upper())
        or ""
    ).strip()
    if provided != settings.SENDGRID_WEBHOOK_INGEST_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SendGrid ingest secret")

    try:
        body = await request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Body must be JSON"
        ) from e

    if not isinstance(body, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SendGrid event webhook expects a JSON array",
        )

    return ingest_sendgrid_events_batch(db, body, commit=True)
