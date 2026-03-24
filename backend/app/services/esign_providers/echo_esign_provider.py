"""
Second in-tree e-sign provider (§5.16): deterministic, no network — distinct from ``stub`` for routing tests.

Webhook format: ``phi_echo_esign_v1`` (parallel to stub; use for multi-vendor webhook normalization checks).
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

from backend.app.core.config import settings
from backend.app.services.esign_provider_service import (
    EsignProvider,
    EsignSignatureRequestContext,
    EsignSignatureRequestResult,
    NormalizedEsignEvent,
)


class EchoEsignProvider(EsignProvider):
    WEBHOOK_FORMAT = "phi_echo_esign_v1"

    def provider_name(self) -> str:
        return "echo"

    def is_configured(self) -> bool:
        return True

    def create_signature_request(self, ctx: EsignSignatureRequestContext) -> EsignSignatureRequestResult:
        env_id = f"echo-env-{ctx.proposal_id[:8]}-{uuid.uuid4().hex[:10]}"
        sess_id = f"echo-sess-{uuid.uuid4().hex[:12]}"
        token = hashlib.sha256(f"{env_id}:{ctx.callback_reference}:echo".encode()).hexdigest()[:24]
        base = settings.PHI_DPS_PORTAL_WEB_BASE or "https://portal.example.invalid"
        signing_url = f"{base}/external-esign/echo/{env_id}?t={token}"
        return EsignSignatureRequestResult(
            envelope_id=env_id,
            provider_session_id=sess_id,
            signing_url=signing_url,
            provider_metadata={"format": self.WEBHOOK_FORMAT, "echo": True},
        )

    def get_signing_link(
        self,
        *,
        envelope_id: str,
        client_user_id: str | None = None,
        signer_email: str | None = None,
        signer_name: str | None = None,
    ) -> str | None:
        base = settings.PHI_DPS_PORTAL_WEB_BASE or "https://portal.example.invalid"
        return f"{base}/external-esign/echo/{envelope_id}"

    def cancel_signature_request(self, *, envelope_id: str) -> None:
        return

    def normalize_webhook_event(self, payload: dict[str, Any]) -> NormalizedEsignEvent | None:
        if payload.get("format") != self.WEBHOOK_FORMAT:
            return None
        env = str(payload.get("envelope_id") or "")
        if not env:
            return None
        st = str(payload.get("status") or "").lower()
        if st not in ("viewed", "signed", "declined", "voided", "expired", "failed", "sent"):
            return None
        safe = {
            "format": self.WEBHOOK_FORMAT,
            "envelope_id": env,
            "status": st,
            "event_id": payload.get("event_id"),
        }
        return NormalizedEsignEvent(
            envelope_id=env,
            status=st,
            event_type=str(payload.get("event_type") or st),
            safe_payload=safe,
        )
