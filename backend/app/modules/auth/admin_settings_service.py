from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings as app_settings
from backend.app.modules.auth.admin_settings_models import AdminSettingAuditLog, AdminSettingValue
from backend.app.modules.auth.admin_settings_schemas import (
    DispatchSettings,
    FeatureFlagsSettings,
    NotificationsSettings,
    SecuritySettings,
    SettingsDomain,
)


def _domain_defaults(domain: SettingsDomain) -> dict[str, Any]:
    if domain == "feature_flags":
        return FeatureFlagsSettings(
            ai_assisted_drafting_enabled=bool(app_settings.AI_ASSISTED_DRAFTING_ENABLED),
            dispatch_recommend_stale=bool(app_settings.PHI_DPS_DISPATCH_RECOMMEND_STALE),
            strict_parts_reconciliation=bool(app_settings.STRICT_PARTS_RECONCILIATION),
            engineer_media_phase2_enabled=False,
        ).model_dump()
    if domain == "dispatch":
        return DispatchSettings(
            telemetry_fresh_seconds=float(app_settings.PHI_DPS_TELEMETRY_FRESH_SECONDS),
            telemetry_aging_seconds=float(app_settings.PHI_DPS_TELEMETRY_AGING_SECONDS),
            avg_vehicle_speed_mps=float(app_settings.PHI_DPS_AVG_VEHICLE_SPEED_MPS),
        ).model_dump()
    if domain == "security":
        return SecuritySettings(
            access_token_expire_minutes=int(app_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ).model_dump()
    if domain == "notifications":
        return NotificationsSettings(
            communication_enabled=bool(app_settings.COMMUNICATION_ENABLED),
            communication_email_provider=str(app_settings.COMMUNICATION_EMAIL_PROVIDER or "none").strip().lower(),
            communication_sms_provider=str(app_settings.COMMUNICATION_SMS_PROVIDER or "none").strip().lower(),
            communication_template_locale=str(app_settings.COMMUNICATION_TEMPLATE_LOCALE or "en").strip(),
            communication_template_catalog_version=str(app_settings.COMMUNICATION_TEMPLATE_CATALOG_VERSION or "1").strip(),
            portal_support_email=str(app_settings.PORTAL_SUPPORT_EMAIL or "support@example.com").strip(),
            portal_support_phone=str(app_settings.PORTAL_SUPPORT_PHONE or "+44 20 0000 0000").strip(),
        ).model_dump()
    raise ValueError(f"Unsupported settings domain: {domain}")


def _validate_domain_values(domain: SettingsDomain, values: dict[str, Any]) -> dict[str, Any]:
    if domain == "feature_flags":
        return FeatureFlagsSettings.model_validate(values).model_dump()
    if domain == "dispatch":
        return DispatchSettings.model_validate(values).model_dump()
    if domain == "security":
        return SecuritySettings.model_validate(values).model_dump()
    if domain == "notifications":
        return NotificationsSettings.model_validate(values).model_dump()
    raise ValueError(f"Unsupported settings domain: {domain}")


def get_domain_settings(db: Session, *, domain: SettingsDomain) -> dict[str, Any]:
    defaults = _domain_defaults(domain)
    row = db.query(AdminSettingValue).filter(AdminSettingValue.setting_key == domain).first()
    overrides: dict[str, Any] = {}
    if row and row.value_json:
        try:
            loaded = json.loads(row.value_json)
            if isinstance(loaded, dict):
                overrides = loaded
        except Exception:
            overrides = {}
    # Revalidate + normalize override payload.
    overrides = _validate_domain_values(domain, {**defaults, **overrides})
    effective = {**defaults, **overrides}
    return {
        "domain": domain,
        "defaults": defaults,
        "overrides": overrides,
        "effective": effective,
        "updated_at": row.updated_at if row else None,
        "updated_by_user_id": row.updated_by_user_id if row else None,
    }


def upsert_domain_settings(
    db: Session,
    *,
    domain: SettingsDomain,
    values: dict[str, Any],
    actor_user_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    defaults = _domain_defaults(domain)
    normalized = _validate_domain_values(domain, {**defaults, **values})

    row = db.query(AdminSettingValue).filter(AdminSettingValue.setting_key == domain).first()
    old_json = row.value_json if row else "{}"

    if row:
        row.value_json = json.dumps(normalized, separators=(",", ":"))
        row.updated_by_user_id = actor_user_id
    else:
        row = AdminSettingValue(
            setting_key=domain,
            value_json=json.dumps(normalized, separators=(",", ":")),
            updated_by_user_id=actor_user_id,
        )
        db.add(row)
    db.flush()

    db.add(
        AdminSettingAuditLog(
            setting_key=domain,
            old_value_json=old_json or "{}",
            new_value_json=row.value_json,
            reason=(reason or "").strip() or None,
            changed_by_user_id=actor_user_id,
        )
    )
    db.commit()
    db.refresh(row)
    return get_domain_settings(db, domain=domain)


def list_domain_audit_logs(db: Session, *, domain: SettingsDomain, limit: int = 50) -> list[AdminSettingAuditLog]:
    return (
        db.query(AdminSettingAuditLog)
        .filter(AdminSettingAuditLog.setting_key == domain)
        .order_by(AdminSettingAuditLog.changed_at.desc())
        .limit(limit)
        .all()
    )

