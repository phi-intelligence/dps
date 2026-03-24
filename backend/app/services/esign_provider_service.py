"""
Third-party e-sign provider abstraction. Routes and webhooks must not call vendor SDKs directly.

Concrete providers register here; only non-secret metadata and URLs are returned to callers.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.app.core.config import settings


class EsignProviderError(RuntimeError):
    """Third-party e-sign API/transport failure; messages must not contain secrets or raw vendor bodies."""


def _header_ci(headers: dict[str, str | None], name: str) -> str | None:
    lower = {str(k).lower(): v for k, v in headers.items()}
    return lower.get(name.lower())


@dataclass(frozen=True)
class EsignSignatureRequestContext:
    proposal_id: str
    proposal_reference: str
    contract_id: str
    customer_id: str
    signer_email: str | None
    signer_name: str | None
    document_title: str
    callback_reference: str  # internal correlation (e.g. acceptance_record_id)
    document_pdf_bytes: bytes | None = None
    document_file_name: str | None = None


@dataclass
class EsignSignatureRequestResult:
    envelope_id: str
    provider_session_id: str
    signing_url: str
    provider_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedEsignEvent:
    """Vendor-neutral lifecycle update (no secrets)."""

    envelope_id: str
    status: str  # viewed | signed | declined | voided | expired | failed | sent
    event_type: str
    safe_payload: dict[str, Any] = field(default_factory=dict)


class EsignProvider(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_signature_request(self, ctx: EsignSignatureRequestContext) -> EsignSignatureRequestResult:
        raise NotImplementedError

    @abstractmethod
    def get_signing_link(
        self,
        *,
        envelope_id: str,
        client_user_id: str | None = None,
        signer_email: str | None = None,
        signer_name: str | None = None,
    ) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def cancel_signature_request(self, *, envelope_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def normalize_webhook_event(self, payload: dict[str, Any]) -> NormalizedEsignEvent | None:
        raise NotImplementedError

    def verify_webhook(self, *, raw_body: str, headers: dict[str, str | None]) -> bool:
        sig = _header_ci(headers, "X-Phi-Dps-Esign-Signature")
        return validate_esign_webhook(raw_body=raw_body, provided_signature=sig)


class StubEsignProvider(EsignProvider):
    """
    Deterministic stub for dev/tests. Webhook format: phi_stub_esign_v1.
    Never performs network I/O; never stores secrets in returned metadata.
    """

    WEBHOOK_FORMAT = "phi_stub_esign_v1"

    def provider_name(self) -> str:
        return "stub"

    def is_configured(self) -> bool:
        return True

    def create_signature_request(self, ctx: EsignSignatureRequestContext) -> EsignSignatureRequestResult:
        env_id = f"stub-env-{ctx.proposal_id[:8]}-{uuid.uuid4().hex[:10]}"
        sess_id = f"stub-sess-{uuid.uuid4().hex[:12]}"
        token = hashlib.sha256(f"{env_id}:{ctx.callback_reference}".encode()).hexdigest()[:24]
        base = settings.PHI_DPS_PORTAL_WEB_BASE or "https://portal.example.invalid"
        signing_url = f"{base}/external-esign/stub/{env_id}?t={token}"
        return EsignSignatureRequestResult(
            envelope_id=env_id,
            provider_session_id=sess_id,
            signing_url=signing_url,
            provider_metadata={"format": self.WEBHOOK_FORMAT, "stub": True},
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
        return f"{base}/external-esign/stub/{envelope_id}"

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


def _build_esign_provider(name: str) -> EsignProvider:
    n = (name or "stub").strip().lower()
    if n == "stub":
        return StubEsignProvider()
    if n == "echo":
        from backend.app.services.esign_providers.echo_esign_provider import EchoEsignProvider

        return EchoEsignProvider()
    if n == "docusign":
        from backend.app.services.esign_providers.docusign_esign_provider import DocusignEsignProvider

        return DocusignEsignProvider()
    return StubEsignProvider()


def get_esign_provider() -> EsignProvider:
    """
    Resolve primary ``PHI_DPS_ESIGN_PROVIDER``; if it is not configured, optionally use
    ``PHI_DPS_ESIGN_FALLBACK_PROVIDER`` when set and distinct (§5.16).
    """
    primary_name = (settings.ESIGN_PROVIDER or "stub").strip().lower()
    primary = _build_esign_provider(primary_name)
    if primary.is_configured():
        return primary
    fb = (settings.ESIGN_FALLBACK_PROVIDER or "").strip().lower()
    if fb and fb != primary_name:
        secondary = _build_esign_provider(fb)
        if secondary.is_configured():
            return secondary
    return primary


def esign_integration_enabled() -> bool:
    return settings.ESIGN_ENABLED and get_esign_provider().is_configured()


def validate_esign_webhook(*, raw_body: str, provided_signature: str | None) -> bool:
    secret = settings.ESIGN_WEBHOOK_SECRET.strip()
    if not secret or not provided_signature:
        return False
    mac = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, provided_signature.strip().lower())


def redact_provider_payload_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip keys that may contain secrets before persisting."""
    deny = {"api_key", "client_secret", "password", "token", "authorization", "access_token", "refresh_token"}
    out: dict[str, Any] = {}
    for k, v in payload.items():
        lk = str(k).lower()
        if lk in deny:
            continue
        if isinstance(v, dict):
            out[k] = redact_provider_payload_for_storage(v)
        else:
            out[k] = v
    return out


def dumps_safe_metadata(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, default=str)
