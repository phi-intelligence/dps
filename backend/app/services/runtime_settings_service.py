from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings as env_settings
from backend.app.modules.auth import admin_settings_service as admin_settings

# Small in-process cache so effective settings diagnostics and hot-path callers
# don't need a DB round-trip on every request.
_CACHE_TTL_SECONDS = 10.0
_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _now() -> float:
    try:
        import time

        return time.time()
    except Exception:
        return 0.0


def _cached_effective(domain: str) -> dict[str, Any] | None:
    row = _cache.get(domain)
    if not row:
        return None
    ts, val = row
    if _now() - ts > _CACHE_TTL_SECONDS:
        return None
    return val


def _update_cache(domain: str, effective: dict[str, Any]) -> None:
    _cache[domain] = (_now(), effective)


def warm_runtime_settings_cache(db) -> None:
    """
    Best-effort cache prefill on startup.
    """

    try:
        _update_cache("feature_flags", admin_settings.get_domain_settings(db, domain="feature_flags")["effective"])
        _update_cache("dispatch", admin_settings.get_domain_settings(db, domain="dispatch")["effective"])
        _update_cache("security", admin_settings.get_domain_settings(db, domain="security")["effective"])
        _update_cache("notifications", admin_settings.get_domain_settings(db, domain="notifications")["effective"])
    except Exception:
        # Never block server boot.
        pass


def refresh_runtime_settings_cache(db) -> None:
    """
    Clears and re-warms the in-process runtime cache.
    Intended for admin-triggered "apply now" diagnostics.
    """

    try:
        _cache.clear()
    except Exception:
        pass
    warm_runtime_settings_cache(db)


def _effective_domain_from_db(db: Session, *, domain: str) -> dict[str, Any]:
    raw = admin_settings.get_domain_settings(db, domain=domain)  # type: ignore[arg-type]
    eff = raw.get("effective")
    return eff if isinstance(eff, dict) else {}


def get_effective_feature_flags(db: Session | None) -> dict[str, Any]:
    defaults = {
        "ai_assisted_drafting_enabled": bool(env_settings.AI_ASSISTED_DRAFTING_ENABLED),
        "dispatch_recommend_stale": bool(env_settings.PHI_DPS_DISPATCH_RECOMMEND_STALE),
        "strict_parts_reconciliation": bool(env_settings.STRICT_PARTS_RECONCILIATION),
        "engineer_media_phase2_enabled": False,
    }
    cached = _cached_effective("feature_flags")
    if cached is not None:
        return {**defaults, **cached}
    if db is None:
        return defaults
    try:
        eff = _effective_domain_from_db(db, domain="feature_flags")
        _update_cache("feature_flags", eff)
        return {**defaults, **eff}
    except Exception:
        return defaults


def get_effective_dispatch_settings(db: Session | None) -> dict[str, Any]:
    defaults = {
        "telemetry_fresh_seconds": float(env_settings.PHI_DPS_TELEMETRY_FRESH_SECONDS),
        "telemetry_aging_seconds": float(env_settings.PHI_DPS_TELEMETRY_AGING_SECONDS),
        "avg_vehicle_speed_mps": float(env_settings.PHI_DPS_AVG_VEHICLE_SPEED_MPS),
    }
    cached = _cached_effective("dispatch")
    if cached is not None:
        return {**defaults, **cached}
    if db is None:
        return defaults
    try:
        eff = _effective_domain_from_db(db, domain="dispatch")
        _update_cache("dispatch", eff)
        return {**defaults, **eff}
    except Exception:
        return defaults


def get_effective_security_settings(db: Session | None) -> dict[str, Any]:
    defaults = {"access_token_expire_minutes": int(env_settings.ACCESS_TOKEN_EXPIRE_MINUTES)}
    cached = _cached_effective("security")
    if cached is not None:
        return {**defaults, **cached}
    if db is None:
        return defaults
    try:
        eff = _effective_domain_from_db(db, domain="security")
        _update_cache("security", eff)
        return {**defaults, **eff}
    except Exception:
        return defaults


def get_effective_notifications_settings(db: Session | None) -> dict[str, Any]:
    defaults = {
        "communication_enabled": bool(env_settings.COMMUNICATION_ENABLED),
        "communication_email_provider": str(env_settings.COMMUNICATION_EMAIL_PROVIDER or "none").strip().lower(),
        "communication_sms_provider": str(env_settings.COMMUNICATION_SMS_PROVIDER or "none").strip().lower(),
        "communication_template_locale": str(env_settings.COMMUNICATION_TEMPLATE_LOCALE or "en").strip(),
        "communication_template_catalog_version": str(env_settings.COMMUNICATION_TEMPLATE_CATALOG_VERSION or "1").strip(),
        "portal_support_email": str(env_settings.PORTAL_SUPPORT_EMAIL or "support@example.com").strip(),
        "portal_support_phone": str(env_settings.PORTAL_SUPPORT_PHONE or "+44 20 0000 0000").strip(),
    }
    cached = _cached_effective("notifications")
    if cached is not None:
        return {**defaults, **cached}
    if db is None:
        return defaults
    try:
        eff = _effective_domain_from_db(db, domain="notifications")
        _update_cache("notifications", eff)
        return {**defaults, **eff}
    except Exception:
        return defaults


def get_effective_runtime_diagnostics(db: Session | None) -> dict[str, Any]:
    """
    Returns both defaults + overrides + effective values for supported domains.
    Intended for admin diagnostics only.
    """

    # If db isn't available, fall back to env defaults only.
    if db is None:
        return {
            "feature_flags": {
                "defaults": {
                    "ai_assisted_drafting_enabled": bool(env_settings.AI_ASSISTED_DRAFTING_ENABLED),
                    "dispatch_recommend_stale": bool(env_settings.PHI_DPS_DISPATCH_RECOMMEND_STALE),
                    "strict_parts_reconciliation": bool(env_settings.STRICT_PARTS_RECONCILIATION),
                    "engineer_media_phase2_enabled": False,
                },
                "overrides": {},
                "effective": {
                    "ai_assisted_drafting_enabled": bool(env_settings.AI_ASSISTED_DRAFTING_ENABLED),
                    "dispatch_recommend_stale": bool(env_settings.PHI_DPS_DISPATCH_RECOMMEND_STALE),
                    "strict_parts_reconciliation": bool(env_settings.STRICT_PARTS_RECONCILIATION),
                    "engineer_media_phase2_enabled": False,
                },
                "updated_at": None,
                "updated_by_user_id": None,
            },
            "dispatch": {
                "defaults": {
                    "telemetry_fresh_seconds": float(env_settings.PHI_DPS_TELEMETRY_FRESH_SECONDS),
                    "telemetry_aging_seconds": float(env_settings.PHI_DPS_TELEMETRY_AGING_SECONDS),
                    "avg_vehicle_speed_mps": float(env_settings.PHI_DPS_AVG_VEHICLE_SPEED_MPS),
                },
                "overrides": {},
                "effective": {
                    "telemetry_fresh_seconds": float(env_settings.PHI_DPS_TELEMETRY_FRESH_SECONDS),
                    "telemetry_aging_seconds": float(env_settings.PHI_DPS_TELEMETRY_AGING_SECONDS),
                    "avg_vehicle_speed_mps": float(env_settings.PHI_DPS_AVG_VEHICLE_SPEED_MPS),
                },
                "updated_at": None,
                "updated_by_user_id": None,
            },
            "security": {
                "defaults": {"access_token_expire_minutes": int(env_settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
                "overrides": {},
                "effective": {"access_token_expire_minutes": int(env_settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
                "updated_at": None,
                "updated_by_user_id": None,
            },
            "notifications": {
                "defaults": get_effective_notifications_settings(None),
                "overrides": {},
                "effective": get_effective_notifications_settings(None),
                "updated_at": None,
                "updated_by_user_id": None,
            },
        }

    out: dict[str, Any] = {}
    for domain in ("feature_flags", "dispatch", "security", "notifications"):
        try:
            raw = admin_settings.get_domain_settings(db, domain=domain)  # type: ignore[arg-type]
            out[domain] = raw
        except Exception:
            # Keep best-effort; fallback to cache/env values.
            if domain == "feature_flags":
                eff = get_effective_feature_flags(db)
                out[domain] = {"domain": domain, "defaults": {}, "overrides": {}, "effective": eff, "updated_at": None, "updated_by_user_id": None}
            if domain == "dispatch":
                eff = get_effective_dispatch_settings(db)
                out[domain] = {"domain": domain, "defaults": {}, "overrides": {}, "effective": eff, "updated_at": None, "updated_by_user_id": None}
            if domain == "security":
                eff = get_effective_security_settings(db)
                out[domain] = {"domain": domain, "defaults": {}, "overrides": {}, "effective": eff, "updated_at": None, "updated_by_user_id": None}
            if domain == "notifications":
                eff = get_effective_notifications_settings(db)
                out[domain] = {"domain": domain, "defaults": {}, "overrides": {}, "effective": eff, "updated_at": None, "updated_by_user_id": None}
    return out

