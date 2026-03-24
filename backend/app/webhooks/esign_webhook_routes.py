"""
Authenticated (HMAC) ingress for legal e-sign provider lifecycle events.

Routes must not call vendor SDKs; normalization lives in esign_provider_service.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.esign_provider_service import get_esign_provider
from backend.app.services.esign_webhook_verification_service import verify_esign_webhook_request
from backend.app.services.proposal_acceptance_esign_service import apply_esign_webhook_event

router = APIRouter(prefix="/webhooks/esign", tags=["webhooks-esign"])


@router.post("/provider")
async def esign_provider_webhook_endpoint(
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

    header_map: dict[str, str | None] = {k: v for k, v in request.headers.items()}
    if not verify_esign_webhook_request(raw_body=raw_text, headers=header_map):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body"
        ) from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON object required")

    provider = get_esign_provider()
    event = provider.normalize_webhook_event(payload)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unrecognized e-sign webhook payload for configured provider",
        )

    result = apply_esign_webhook_event(db, event=event, raw_payload_for_audit=payload)
    db.commit()
    return {"ok": True, **result}
