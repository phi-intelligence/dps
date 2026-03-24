from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SettingsDomain = Literal["feature_flags", "dispatch", "security", "notifications"]


class FeatureFlagsSettings(BaseModel):
    ai_assisted_drafting_enabled: bool = False
    dispatch_recommend_stale: bool = False
    strict_parts_reconciliation: bool = False
    engineer_media_phase2_enabled: bool = False


class DispatchSettings(BaseModel):
    telemetry_fresh_seconds: float = Field(default=60.0, ge=10.0, le=3600.0)
    telemetry_aging_seconds: float = Field(default=300.0, ge=30.0, le=86400.0)
    avg_vehicle_speed_mps: float = Field(default=13.89, ge=1.0, le=60.0)


class SecuritySettings(BaseModel):
    # Access token expiry (minutes). Used by auth token creation.
    access_token_expire_minutes: int = Field(default=60, ge=1, le=10080)


class NotificationsSettings(BaseModel):
    communication_enabled: bool = False
    communication_email_provider: str = Field(default="none")
    communication_sms_provider: str = Field(default="none")
    communication_template_locale: str = Field(default="en")
    communication_template_catalog_version: str = Field(default="1")
    portal_support_email: str = Field(default="support@example.com")
    portal_support_phone: str = Field(default="+44 20 0000 0000")

    # Keep providers intentionally permissive (string) because some values can be
    # safely treated as "simulated" by runtime consumers when unrecognized.


class SettingsDomainCatalogEntryOut(BaseModel):
    domain: SettingsDomain
    label: str
    description: str


class SettingsDomainOut(BaseModel):
    domain: SettingsDomain
    defaults: dict[str, Any]
    overrides: dict[str, Any]
    effective: dict[str, Any]
    updated_at: datetime | None = None
    updated_by_user_id: str | None = None


class SettingsDomainUpdateIn(BaseModel):
    values: dict[str, Any]
    reason: str | None = Field(default=None, max_length=1000)


class SettingsAuditEntryOut(BaseModel):
    id: str
    setting_key: str
    old_value_json: str
    new_value_json: str
    reason: str | None
    changed_by_user_id: str | None
    changed_at: datetime

    model_config = {"from_attributes": True}


class RuntimeSettingsEffectiveOut(BaseModel):
    feature_flags: SettingsDomainOut
    dispatch: SettingsDomainOut
    security: SettingsDomainOut
    notifications: SettingsDomainOut

