"""
DocuSign eSign REST API v2.1 — JWT grant, envelope create with PDF, embedded recipient view, Connect webhooks.

All network I/O is isolated here; business code uses EsignProvider only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

import httpx
from jose import jwt as jose_jwt

from backend.app.core.config import settings
from backend.app.services.esign_provider_service import (
    EsignProvider,
    EsignProviderError,
    EsignSignatureRequestContext,
    EsignSignatureRequestResult,
    NormalizedEsignEvent,
)


# Test seam: patch this to stub HTTP without network.
HttpSend = Callable[..., httpx.Response]


def _default_http_send(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    data: dict[str, str] | None = None,
    timeout: float = 60.0,
) -> httpx.Response:
    with httpx.Client(timeout=timeout) as client:
        if data is not None:
            return client.request(method, url, headers=headers or {}, data=data)
        return client.request(method, url, headers=headers or {}, json=json_body)


_http_send: HttpSend = _default_http_send


def set_http_send_for_tests(fn: HttpSend | None) -> None:
    global _http_send
    _http_send = fn or _default_http_send


def _header(headers: dict[str, str | None], name: str) -> str | None:
    lower = {str(k).lower(): v for k, v in headers.items()}
    return lower.get(name.lower())


_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def reset_docusign_auth_state_for_tests() -> None:
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0.0


class DocusignEsignProvider(EsignProvider):
    """
    DocuSign: JWT app auth, envelope with one PDF + one embedded signer, Connect JSON webhooks.
    """

    def provider_name(self) -> str:
        return "docusign"

    def is_configured(self) -> bool:
        return bool(
            self._client_id()
            and settings.ESIGN_USER_ID.strip()
            and settings.ESIGN_ACCOUNT_ID.strip()
            and self._private_key_pem()
            and settings.ESIGN_BASE_URL.strip()
            and settings.ESIGN_AUTH_SERVER.strip()
        )

    def _client_id(self) -> str:
        cid = settings.ESIGN_CLIENT_ID.strip()
        if cid:
            return cid
        return settings.ESIGN_API_KEY.strip()

    def _private_key_pem(self) -> str | None:
        p = settings.ESIGN_RSA_PRIVATE_KEY_PATH.strip()
        if not p:
            return None
        path = Path(p)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def _api_base(self) -> str:
        base = settings.ESIGN_BASE_URL.strip().rstrip("/")
        if not base.endswith("/restapi"):
            base = f"{base}/restapi"
        return base

    def _jwt_assertion(self) -> str:
        pem = self._private_key_pem()
        if not pem:
            raise EsignProviderError("DocuSign RSA private key is not available")
        now = datetime.now(timezone.utc)
        aud = settings.ESIGN_AUTH_SERVER.strip()
        claim = {
            "iss": self._client_id(),
            "sub": settings.ESIGN_USER_ID.strip(),
            "aud": aud,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=9)).timestamp()),
            "scope": "signature impersonation",
        }
        assertion = jose_jwt.encode(claim, pem, algorithm="RS256")
        if isinstance(assertion, bytes):
            return assertion.decode("utf-8")
        return str(assertion)

    def _access_token(self) -> str:
        now = time.time()
        tok = _token_cache.get("access_token")
        exp = float(_token_cache.get("expires_at") or 0)
        if tok and now < exp - 60:
            return str(tok)

        token_url = f"https://{settings.ESIGN_AUTH_SERVER.strip()}/oauth/token"
        assertion = self._jwt_assertion()
        resp = _http_send(
            "POST",
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        if resp.status_code >= 400:
            raise EsignProviderError(f"DocuSign OAuth token request failed (HTTP {resp.status_code})")
        try:
            body = resp.json()
        except Exception as e:
            raise EsignProviderError("DocuSign OAuth response was not valid JSON") from e
        access = body.get("access_token")
        if not access:
            raise EsignProviderError("DocuSign OAuth response missing access_token")
        expires_in = int(body.get("expires_in") or 3600)
        _token_cache["access_token"] = access
        _token_cache["expires_at"] = now + expires_in
        return str(access)

    def _account_envelopes_url(self) -> str:
        aid = settings.ESIGN_ACCOUNT_ID.strip()
        return urljoin(self._api_base() + "/", f"v2.1/accounts/{aid}/envelopes")

    def verify_webhook(self, *, raw_body: str, headers: dict[str, str | None]) -> bool:
        secret = settings.ESIGN_WEBHOOK_SECRET.strip()
        if not secret:
            return False
        sig_b64 = _header(headers, "X-DocuSign-Signature-1")
        if not sig_b64:
            return False
        digest = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).digest()
        expected = base64.b64encode(digest).decode("ascii")
        return hmac.compare_digest(expected.strip(), sig_b64.strip())

    def create_signature_request(self, ctx: EsignSignatureRequestContext) -> EsignSignatureRequestResult:
        if not ctx.document_pdf_bytes:
            raise EsignProviderError("Proposal PDF bytes are required for DocuSign")
        if not (ctx.signer_email or "").strip():
            raise EsignProviderError("Signer email is required for DocuSign")

        email = ctx.signer_email.strip()
        name = (ctx.signer_name or "Customer signer").strip() or "Customer signer"
        client_user_id = ctx.callback_reference[:100]
        b64 = base64.b64encode(ctx.document_pdf_bytes).decode("ascii")
        fname = (ctx.document_file_name or "proposal.pdf").strip() or "proposal.pdf"
        if not fname.lower().endswith(".pdf"):
            fname = f"{fname}.pdf"

        body: dict[str, Any] = {
            "emailSubject": ctx.document_title[:200],
            "status": "sent",
            "documents": [
                {
                    "documentBase64": b64,
                    "name": fname[:200],
                    "fileExtension": "pdf",
                    "documentId": "1",
                }
            ],
            "recipients": {
                "signers": [
                    {
                        "email": email,
                        "name": name,
                        "recipientId": "1",
                        "routingOrder": "1",
                        "clientUserId": client_user_id,
                    }
                ]
            },
        }
        token = self._access_token()
        env_url = self._account_envelopes_url()
        resp = _http_send(
            "POST",
            env_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body=body,
        )
        if resp.status_code >= 400:
            raise EsignProviderError(f"DocuSign create envelope failed (HTTP {resp.status_code})")
        try:
            env = resp.json()
        except Exception as e:
            raise EsignProviderError("DocuSign create envelope returned invalid JSON") from e
        envelope_id = env.get("envelopeId")
        if not envelope_id:
            raise EsignProviderError("DocuSign create envelope response missing envelopeId")

        signing_url = self._create_recipient_view(
            access_token=token,
            envelope_id=str(envelope_id),
            client_user_id=client_user_id,
            email=email,
            name=name,
        )
        return EsignSignatureRequestResult(
            envelope_id=str(envelope_id),
            provider_session_id=str(envelope_id),
            signing_url=signing_url,
            provider_metadata={
                "provider": "docusign",
                "envelope_id": str(envelope_id),
                "client_user_id_set": True,
            },
        )

    def _create_recipient_view(
        self,
        *,
        access_token: str,
        envelope_id: str,
        client_user_id: str,
        email: str,
        name: str,
    ) -> str:
        aid = settings.ESIGN_ACCOUNT_ID.strip()
        url = urljoin(
            self._api_base() + "/",
            f"v2.1/accounts/{aid}/envelopes/{envelope_id}/views/recipient",
        )
        ret = settings.ESIGN_RETURN_URL.strip() or (settings.PHI_DPS_PORTAL_WEB_BASE or "https://localhost/esign/return").strip()
        body = {
            "returnUrl": ret[:2000],
            "authenticationMethod": "none",
            "email": email,
            "userName": name,
            "clientUserId": client_user_id,
        }
        resp = _http_send(
            "POST",
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body=body,
        )
        if resp.status_code >= 400:
            raise EsignProviderError(f"DocuSign recipient view failed (HTTP {resp.status_code})")
        try:
            data = resp.json()
        except Exception as e:
            raise EsignProviderError("DocuSign recipient view returned invalid JSON") from e
        su = data.get("url")
        if not su:
            raise EsignProviderError("DocuSign recipient view response missing url")
        return str(su)

    def get_signing_link(
        self,
        *,
        envelope_id: str,
        client_user_id: str | None = None,
        signer_email: str | None = None,
        signer_name: str | None = None,
    ) -> str | None:
        if not client_user_id or not signer_email:
            return None
        token = self._access_token()
        name = (signer_name or "Signer").strip() or "Signer"
        return self._create_recipient_view(
            access_token=token,
            envelope_id=envelope_id,
            client_user_id=client_user_id[:100],
            email=signer_email.strip(),
            name=name,
        )

    def cancel_signature_request(self, *, envelope_id: str) -> None:
        token = self._access_token()
        aid = settings.ESIGN_ACCOUNT_ID.strip()
        url = urljoin(
            self._api_base() + "/",
            f"v2.1/accounts/{aid}/envelopes/{envelope_id}",
        )
        resp = _http_send(
            "PUT",
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body={"status": "voided", "voidedReason": "Cancelled via PHI-DPS"},
        )
        if resp.status_code >= 400:
            raise EsignProviderError(f"DocuSign void envelope failed (HTTP {resp.status_code})")

    def normalize_webhook_event(self, payload: dict[str, Any]) -> NormalizedEsignEvent | None:
        if not isinstance(payload, dict):
            return None
        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        env_id = data.get("envelopeId")
        summary = data.get("envelopeSummary")
        if not env_id and isinstance(summary, dict):
            env_id = summary.get("envelopeId")
        if not env_id:
            return None
        env_id = str(env_id)

        event = str(payload.get("event") or "").lower()
        env_status = ""
        if isinstance(summary, dict):
            env_status = str(summary.get("status") or "").lower()

        status = self._map_docusign_to_normalized(event, env_status)
        if not status:
            return None

        safe = {
            "provider": "docusign",
            "envelope_id": env_id,
            "connect_event": payload.get("event"),
            "envelope_status": env_status or None,
            "generatedDateTime": payload.get("generatedDateTime"),
            "configurationId": payload.get("configurationId"),
            "uri": payload.get("uri"),
        }
        return NormalizedEsignEvent(
            envelope_id=env_id,
            status=status,
            event_type=event or env_status or "unknown",
            safe_payload=safe,
        )

    def _map_docusign_to_normalized(self, event: str, env_status: str) -> str | None:
        if "voided" in event or env_status == "voided":
            return "voided"
        if "declined" in event or env_status == "declined":
            return "declined"
        if "completed" in event or env_status == "completed":
            return "signed"
        if "expire" in event or "timedout" in event or env_status in ("expired", "autoresponded"):
            return "expired"
        if "delivered" in event or env_status == "delivered":
            return "viewed"
        if "sent" in event or env_status == "sent":
            return "sent"
        if env_status in ("created", "processing"):
            return "sent"
        if "authenticationfailed" in event or "failed" in event:
            return "failed"
        if env_status == "signed":
            return "viewed"
        return None
