"""
Verify authenticity of inbound communication provider webhooks.

Supports:
- ``phi_generic_v1`` JSON body (see ``communication_provider_event_service``) with HMAC-SHA256
  over the raw request body using ``Settings.COMMUNICATION_WEBHOOK_SECRET``.

Header: ``X-Phi-Dps-Communication-Signature`` = lowercase hex digest of HMAC-SHA256(body, secret).
"""
from __future__ import annotations

import hashlib
import hmac

from backend.app.core.config import settings


def verify_communication_webhook_signature(*, raw_body: str, provided_signature: str | None) -> bool:
    if not provided_signature:
        return False
    secret = (settings.COMMUNICATION_WEBHOOK_SECRET or "").strip()
    if not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_signature.strip())
