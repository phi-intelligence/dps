"""
SMS outbound abstraction (Twilio REST) — mirrors email provider pattern; tests use override.
"""
from __future__ import annotations

import base64
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.services.runtime_settings_service import get_effective_notifications_settings


@dataclass
class OutboundSmsMessage:
    to_e164: str
    body: str


@dataclass
class OutboundSmsResult:
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


class SmsOutboundProvider(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def send_sms(self, msg: OutboundSmsMessage) -> OutboundSmsResult:
        raise NotImplementedError


_sms_provider_override: SmsOutboundProvider | None = None


def set_sms_provider_override(provider: SmsOutboundProvider | None) -> None:
    global _sms_provider_override
    _sms_provider_override = provider


def get_sms_provider() -> SmsOutboundProvider:
    if _sms_provider_override is not None:
        return _sms_provider_override
    return build_sms_provider_from_settings()


def build_sms_provider_from_settings() -> SmsOutboundProvider:
    effective = get_effective_notifications_settings(None)
    if not bool(effective["communication_enabled"]):
        return SimulatedSmsProvider(reason="COMMUNICATION_ENABLED is false")
    prov = str(effective["communication_sms_provider"]).strip().lower()
    if prov == "twilio":
        return TwilioSmsProvider()
    return SimulatedSmsProvider(reason="COMMUNICATION_SMS_PROVIDER is none")


class SimulatedSmsProvider(SmsOutboundProvider):
    def __init__(self, *, reason: str) -> None:
        self._reason = reason

    def provider_name(self) -> str:
        return "simulated_sms"

    def send_sms(self, msg: OutboundSmsMessage) -> OutboundSmsResult:
        mid = f"sms-sim-{uuid.uuid4()}"
        return OutboundSmsResult(
            ok=True,
            provider_message_id=mid,
            raw_response={"simulated": True, "reason": self._reason, "to": msg.to_e164},
        )


class TwilioSmsProvider(SmsOutboundProvider):
    def provider_name(self) -> str:
        return "twilio"

    def validate_config(self) -> tuple[bool, str | None]:
        if not settings.TWILIO_ACCOUNT_SID:
            return False, "PHI_DPS_TWILIO_ACCOUNT_SID is not set"
        if not settings.TWILIO_AUTH_TOKEN:
            return False, "PHI_DPS_TWILIO_AUTH_TOKEN is not set"
        if not settings.TWILIO_FROM_NUMBER:
            return False, "PHI_DPS_TWILIO_FROM_NUMBER is not set"
        return True, None

    def send_sms(self, msg: OutboundSmsMessage) -> OutboundSmsResult:
        ok, err = self.validate_config()
        if not ok:
            return OutboundSmsResult(ok=False, error_code="config", error_message=err or "invalid config")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        auth = base64.b64encode(
            f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "To": msg.to_e164,
            "From": settings.TWILIO_FROM_NUMBER,
            "Body": msg.body[:1600] if msg.body else "",
        }
        try:
            r = httpx.post(url, data=data, headers=headers, timeout=45.0)
        except httpx.HTTPError as e:
            return OutboundSmsResult(
                ok=False,
                error_code="http",
                error_message=str(e)[:2000],
                raw_response={"exc_type": type(e).__name__},
            )

        try:
            body = r.json()
        except json.JSONDecodeError:
            body = {"raw": r.text[:2000]}

        if r.status_code >= 400:
            em = str(body.get("message") or body.get("more_info") or r.text or "twilio error")[:2000]
            return OutboundSmsResult(
                ok=False,
                error_code="twilio_api",
                error_message=em,
                raw_response={"status_code": r.status_code, "body": body},
            )

        sid = str(body.get("sid") or "") or None
        return OutboundSmsResult(
            ok=True,
            provider_message_id=sid,
            raw_response={"status_code": r.status_code, "sid": sid},
        )


def dumps_sms_response_payload(d: dict[str, Any]) -> str:
    return json.dumps(d, separators=(",", ":"), default=str)
