"""
Non-secret integration readiness for support (§5.7): email, e-sign, storage, DB.
"""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.services.esign_provider_service import esign_integration_enabled, get_esign_provider
from backend.app.services.runtime_settings_service import get_effective_feature_flags, get_effective_notifications_settings


def integration_status_summary(db: Session) -> dict[str, Any]:
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    prov = get_esign_provider()
    s3_ready = bool(settings.PHI_DPS_S3_BUCKET.strip()) if settings.PHI_DPS_DOCUMENT_STORAGE_PROVIDER == "s3" else True

    eff_notifications = get_effective_notifications_settings(db)
    eff_feature_flags = get_effective_feature_flags(db)
    ai_enabled = bool(eff_feature_flags.get("ai_assisted_drafting_enabled", False))

    return {
        "database_reachable": db_ok,
        "communication": {
            "enabled": bool(eff_notifications["communication_enabled"]),
            "template_catalog_version": str(eff_notifications["communication_template_catalog_version"]).strip(),
            "template_default_locale": str(eff_notifications["communication_template_locale"]).strip(),
            "email_provider": str(eff_notifications["communication_email_provider"]),
            "sms_provider": str(eff_notifications["communication_sms_provider"]),
            "from_email_configured": bool(settings.COMMUNICATION_FROM_EMAIL.strip()),
            "sendgrid_api_key_configured": bool(settings.SENDGRID_API_KEY.strip()),
            "sendgrid_webhook_ingest_configured": bool(settings.SENDGRID_WEBHOOK_INGEST_SECRET.strip()),
            "twilio_sms_configured": bool(
                settings.TWILIO_ACCOUNT_SID.strip()
                and settings.TWILIO_AUTH_TOKEN.strip()
                and settings.TWILIO_FROM_NUMBER.strip()
            ),
            "type_channel_map_configured": bool(settings.COMMUNICATION_TYPE_CHANNEL_MAP_JSON.strip()),
        },
        "esign": {
            "enabled": settings.ESIGN_ENABLED,
            "provider": settings.ESIGN_PROVIDER,
            "fallback_provider": settings.ESIGN_FALLBACK_PROVIDER or None,
            "provider_configured": prov.is_configured(),
            "integration_ready": esign_integration_enabled(),
        },
        "document_storage": {
            "provider": settings.PHI_DPS_DOCUMENT_STORAGE_PROVIDER,
            "s3_bucket_configured": s3_ready,
        },
        "process": {
            "dev_bootstrap_enabled": os.getenv("PHI_DPS_DEV_BOOTSTRAP", "1") == "1",
            "rollout_runner_enabled": os.getenv("PHI_DPS_ROLLOUT_RUNNER_ENABLED", "0") == "1",
        },
        "ai": {
            "assisted_drafting_feature_flag": ai_enabled,
            "gemini_enabled": settings.GEMINI_ENABLED,
            "gemini_api_key_configured": bool(str(settings.GEMINI_API_KEY or "").strip()),
            "assisted_drafting_ready": bool(
                ai_enabled
                and settings.GEMINI_ENABLED
                and str(settings.GEMINI_API_KEY or "").strip()
            ),
        },
        "labour": {
            "holiday_calendar_feed_import_enabled": True,
        },
    }
