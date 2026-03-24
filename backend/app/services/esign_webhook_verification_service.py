"""Verify e-sign provider webhook authenticity (provider-specific; headers-aware)."""

from __future__ import annotations

from backend.app.services.esign_provider_service import get_esign_provider


def verify_esign_webhook_request(*, raw_body: str, headers: dict[str, str | None]) -> bool:
    return get_esign_provider().verify_webhook(raw_body=raw_body, headers=headers)
