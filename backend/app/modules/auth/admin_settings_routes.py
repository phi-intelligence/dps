from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.modules.auth.admin_settings_schemas import (
    SettingsAuditEntryOut,
    SettingsDomainCatalogEntryOut,
    SettingsDomainOut,
    SettingsDomainUpdateIn,
    RuntimeSettingsEffectiveOut,
)
from backend.app.modules.auth.models import User
from backend.app.modules.auth import admin_settings_service as svc
from backend.app.services import runtime_settings_service as runtime_svc
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz

router = APIRouter(prefix="/settings", tags=["admin"])
_ALLOWED_DOMAINS = {"feature_flags", "dispatch", "security", "notifications"}


def _parse_domain_or_400(domain: str) -> str:
    d = (domain or "").strip()
    if d not in _ALLOWED_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported settings domain: {domain}",
        )
    return d


def require_settings_admin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    authz.require_permission_http(user, policy.CAN_ADMIN_PERMISSION_GRANTS, db=db)
    return user


@router.get("/domains", response_model=list[SettingsDomainCatalogEntryOut])
def list_settings_domains(
    _admin: User = Depends(require_settings_admin),
) -> list[SettingsDomainCatalogEntryOut]:
    return [
        SettingsDomainCatalogEntryOut(
            domain="feature_flags",
            label="Feature flags",
            description="High-level feature toggles with safe defaults.",
        ),
        SettingsDomainCatalogEntryOut(
            domain="dispatch",
            label="Dispatch",
            description="Core dispatch/runtime behavior controls.",
        ),
        SettingsDomainCatalogEntryOut(
            domain="security",
            label="Security",
            description="Auth and token hardening controls (non-secret).",
        ),
        SettingsDomainCatalogEntryOut(
            domain="notifications",
            label="Notifications",
            description="Communication runtime toggles and customer template routing.",
        ),
    ]


@router.get("/{domain}", response_model=SettingsDomainOut)
def get_domain_settings(
    domain: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_settings_admin),
) -> SettingsDomainOut:
    d = _parse_domain_or_400(domain)
    raw = svc.get_domain_settings(db, domain=d)  # type: ignore[arg-type]
    return SettingsDomainOut(**raw)


@router.put("/{domain}", response_model=SettingsDomainOut)
def put_domain_settings(
    domain: str,
    payload: SettingsDomainUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_settings_admin),
) -> SettingsDomainOut:
    d = _parse_domain_or_400(domain)
    raw = svc.upsert_domain_settings(
        db,
        domain=d,  # type: ignore[arg-type]
        values=payload.values,
        actor_user_id=current_user.id,
        reason=payload.reason,
    )
    return SettingsDomainOut(**raw)


@router.get("/{domain}/history", response_model=list[SettingsAuditEntryOut])
def list_domain_settings_history(
    domain: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_settings_admin),
) -> list[SettingsAuditEntryOut]:
    d = _parse_domain_or_400(domain)
    rows = svc.list_domain_audit_logs(db, domain=d, limit=limit)  # type: ignore[arg-type]
    return [SettingsAuditEntryOut.model_validate(r) for r in rows]


@router.get("/effective", response_model=RuntimeSettingsEffectiveOut)
def get_effective_runtime_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_settings_admin),
) -> RuntimeSettingsEffectiveOut:
    raw = runtime_svc.get_effective_runtime_diagnostics(db)
    # runtime_svc already returns a dict with both domains.
    return RuntimeSettingsEffectiveOut.model_validate(raw)


@router.post("/effective-cache/refresh")
def refresh_effective_cache(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_settings_admin),
) -> dict[str, str]:
    """
    Forces in-process runtime cache refresh (best-effort).
    """
    runtime_svc.refresh_runtime_settings_cache(db)
    return {"status": "ok"}

