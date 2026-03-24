"""
§5.17 — versioned template keys + locale normalization + registry listing for customer communications.

Template key shape: ``phi_dps/cv{catalog_version}/{locale}/{communication_type}``.
"""
from __future__ import annotations

from typing import Any

from backend.app.services.runtime_settings_service import get_effective_notifications_settings

SUPPORTED_LOCALES: tuple[str, ...] = ("en", "fr")


def normalize_locale(raw: str | None) -> str:
    if not raw:
        return "en"
    s = raw.strip().lower().replace("_", "-")
    if s.startswith("fr"):
        return "fr"
    return "en"


def template_catalog_version() -> str:
    eff = get_effective_notifications_settings(None)
    return str(eff["communication_template_catalog_version"]).strip()


def build_template_key(communication_type: str, *, locale: str | None = None) -> str:
    loc = normalize_locale(locale)
    cv = template_catalog_version()
    return f"phi_dps/cv{cv}/{loc}/{communication_type}"


def resolve_communication_locale_for_contract(contract: Any | None) -> str:
    raw = None
    if contract is not None:
        raw = getattr(contract, "communication_locale", None)
    if not raw:
        eff = get_effective_notifications_settings(None)
        raw = eff["communication_template_locale"]
    return normalize_locale(raw)


def list_communication_template_registry() -> list[dict[str, Any]]:
    from backend.app.services.contract_customer_communication_templates import ALL_COMMUNICATION_TYPES

    cv = template_catalog_version()
    return [
        {
            "communication_type": t,
            "catalog_version": cv,
            "supported_locales": list(SUPPORTED_LOCALES),
            "template_key_example": f"phi_dps/cv{cv}/en/{t}",
        }
        for t in sorted(ALL_COMMUNICATION_TYPES)
    ]
