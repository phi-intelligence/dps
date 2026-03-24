"""
Outbound email abstraction — no raw SMTP/SendGrid in workflow services.

Production: ``PHI_DPS_COMMUNICATION_ENABLED=1`` and ``PHI_DPS_COMMUNICATION_EMAIL_PROVIDER=smtp|sendgrid``.
Tests: monkeypatch ``set_email_provider_override`` with a fake provider.
"""
from __future__ import annotations

import json
import smtplib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.services.runtime_settings_service import get_effective_notifications_settings


@dataclass
class OutboundEmailMessage:
    to_address: str
    subject: str
    body_text: str | None
    body_html: str | None
    message_id_header: str | None = None  # optional Message-ID for tracing


@dataclass
class OutboundSendResult:
    ok: bool
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def normalize_for_storage(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "provider_message_id": self.provider_message_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


class OutboundCommunicationProvider(ABC):
    """Extensible outbound facade (email now; SMS later)."""

    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError  # pragma: no cover

    def validate_config(self) -> tuple[bool, str | None]:
        """Return (ok, error_message)."""
        return True, None

    @abstractmethod
    def send_email(self, msg: OutboundEmailMessage) -> OutboundSendResult:
        raise NotImplementedError

    def normalize_result(self, result: OutboundSendResult) -> OutboundSendResult:
        return result


_email_provider_override: OutboundCommunicationProvider | None = None


def set_email_provider_override(provider: OutboundCommunicationProvider | None) -> None:
    global _email_provider_override
    _email_provider_override = provider


def get_email_provider() -> OutboundCommunicationProvider:
    if _email_provider_override is not None:
        return _email_provider_override
    return build_email_provider_from_settings()


def build_email_provider_from_settings() -> OutboundCommunicationProvider:
    effective = get_effective_notifications_settings(None)
    if not bool(effective["communication_enabled"]):
        return SimulatedEmailProvider(reason="COMMUNICATION_ENABLED is false")
    prov = str(effective["communication_email_provider"]).strip().lower()
    if prov == "smtp":
        return SmtpOutboundEmailProvider()
    if prov == "sendgrid":
        return SendGridOutboundEmailProvider()
    return SimulatedEmailProvider(reason="COMMUNICATION_EMAIL_PROVIDER is none")


class SimulatedEmailProvider(OutboundCommunicationProvider):
    """No network; used when outbound is disabled or unconfigured."""

    def __init__(self, *, reason: str) -> None:
        self._reason = reason

    def provider_name(self) -> str:
        return "simulated"

    def send_email(self, msg: OutboundEmailMessage) -> OutboundSendResult:
        mid = f"sim-{uuid.uuid4()}"
        return OutboundSendResult(
            ok=True,
            provider_message_id=mid,
            raw_response={"simulated": True, "reason": self._reason, "to": msg.to_address},
        )


class SmtpOutboundEmailProvider(OutboundCommunicationProvider):
    def provider_name(self) -> str:
        return "smtp"

    def validate_config(self) -> tuple[bool, str | None]:
        if not settings.SMTP_HOST:
            return False, "SMTP_HOST is not set"
        if not settings.COMMUNICATION_FROM_EMAIL:
            return False, "COMMUNICATION_FROM_EMAIL is not set"
        return True, None

    def send_email(self, msg: OutboundEmailMessage) -> OutboundSendResult:
        ok, err = self.validate_config()
        if not ok:
            return OutboundSendResult(ok=False, error_code="config", error_message=err or "invalid config")

        mime = MIMEMultipart("alternative")
        mime["Subject"] = msg.subject or "(no subject)"
        mime["From"] = formataddr((settings.COMMUNICATION_FROM_NAME, settings.COMMUNICATION_FROM_EMAIL))
        mime["To"] = msg.to_address
        if settings.COMMUNICATION_REPLY_TO:
            mime["Reply-To"] = settings.COMMUNICATION_REPLY_TO
        mid = msg.message_id_header or f"<{uuid.uuid4()}@phi-dps.outbound>"
        mime["Message-ID"] = mid

        if msg.body_text:
            mime.attach(MIMEText(msg.body_text, "plain", "utf-8"))
        if msg.body_html:
            mime.attach(MIMEText(msg.body_html, "html", "utf-8"))
        if not msg.body_text and not msg.body_html:
            mime.attach(MIMEText("", "plain", "utf-8"))

        try:
            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.COMMUNICATION_FROM_EMAIL,
                [msg.to_address],
                mime.as_string(),
            )
            server.quit()
        except smtplib.SMTPException as e:
            return OutboundSendResult(
                ok=False,
                error_code="smtp",
                error_message=str(e)[:2000],
                raw_response={"exc_type": type(e).__name__},
            )
        except OSError as e:
            return OutboundSendResult(
                ok=False,
                error_code="network",
                error_message=str(e)[:2000],
                raw_response={"exc_type": type(e).__name__},
            )

        return OutboundSendResult(
            ok=True,
            provider_message_id=mid.strip("<>"),
            raw_response={"transport": "smtp", "host": settings.SMTP_HOST},
        )


class SendGridOutboundEmailProvider(OutboundCommunicationProvider):
    """SendGrid v3 Mail Send (HTTPS). Stores X-Message-Id (normalized) as provider_message_id for webhook correlation."""

    def provider_name(self) -> str:
        return "sendgrid"

    def validate_config(self) -> tuple[bool, str | None]:
        if not settings.SENDGRID_API_KEY:
            return False, "PHI_DPS_SENDGRID_API_KEY is not set"
        if not settings.COMMUNICATION_FROM_EMAIL:
            return False, "COMMUNICATION_FROM_EMAIL is not set"
        return True, None

    def send_email(self, msg: OutboundEmailMessage) -> OutboundSendResult:
        ok, err = self.validate_config()
        if not ok:
            return OutboundSendResult(ok=False, error_code="config", error_message=err or "invalid config")

        content: list[dict[str, str]] = []
        if msg.body_text:
            content.append({"type": "text/plain", "value": msg.body_text})
        if msg.body_html:
            content.append({"type": "text/html", "value": msg.body_html})
        if not content:
            content.append({"type": "text/plain", "value": ""})

        payload: dict[str, Any] = {
            "personalizations": [{"to": [{"email": msg.to_address}]}],
            "from": {
                "email": settings.COMMUNICATION_FROM_EMAIL,
                "name": settings.COMMUNICATION_FROM_NAME or "PHI-DPS",
            },
            "subject": msg.subject or "(no subject)",
            "content": content,
        }
        if settings.COMMUNICATION_REPLY_TO:
            payload["reply_to"] = {"email": settings.COMMUNICATION_REPLY_TO}

        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            r = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
                timeout=45.0,
            )
        except httpx.HTTPError as e:
            return OutboundSendResult(
                ok=False,
                error_code="http",
                error_message=str(e)[:2000],
                raw_response={"exc_type": type(e).__name__},
            )

        raw: dict[str, Any] = {"status_code": r.status_code}
        if r.status_code not in (200, 202):
            return OutboundSendResult(
                ok=False,
                error_code="sendgrid_api",
                error_message=(r.text or r.reason_phrase or "send failed")[:2000],
                raw_response=raw,
            )

        mid_hdr = (r.headers.get("X-Message-Id") or r.headers.get("x-message-id") or "").strip()
        mid = mid_hdr.strip("<>").split(".")[0].strip() if mid_hdr else None
        if not mid:
            mid = f"sg-{uuid.uuid4()}"
        raw["x_message_id"] = mid
        return OutboundSendResult(
            ok=True,
            provider_message_id=mid,
            raw_response=raw,
        )


def dumps_response_payload(d: dict[str, Any]) -> str:
    return json.dumps(d, separators=(",", ":"), default=str)
