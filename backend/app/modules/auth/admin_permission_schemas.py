from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PermissionCatalogEntryOut(BaseModel):
    permission_key: str
    label: str
    default_roles: list[str] = Field(default_factory=list)


class UserPermissionGrantOut(BaseModel):
    id: str
    user_id: str
    permission_key: str
    effect: str
    active: bool
    notes: str | None = None
    created_at: datetime
    created_by_user_id: str | None = None
    expires_at: datetime | None = None


class PermissionSourceEntryOut(BaseModel):
    permission_key: str
    effective: bool
    role_baseline_allowed: bool
    sources: list[dict] = Field(default_factory=list)


class UserPermissionsDetailOut(BaseModel):
    user_id: str
    email: str
    role_names: list[str]
    role_permissions: list[str]
    effective_permissions: list[str]
    grants: list[UserPermissionGrantOut]
    permission_sources: list[PermissionSourceEntryOut]


class UserPermissionGrantCreateIn(BaseModel):
    permission_key: str
    effect: Literal["allow", "deny"]
    notes: str | None = None
    expires_at: datetime | None = None


class UserPermissionGrantPatchIn(BaseModel):
    effect: Literal["allow", "deny"] | None = None
    active: bool | None = None
    notes: str | None = None
    expires_at: datetime | None = None


class AiProviderStatusOut(BaseModel):
    enabled: bool
    provider_name: str
    model: str
    base_url_configured: bool
    api_key_configured: bool
    ai_assisted_drafting_feature_flag: bool = False
    ai_assisted_drafting_ready: bool = False
