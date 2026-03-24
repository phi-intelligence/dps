"""High-trust admin APIs: permission grants catalog, per-user grants, safe AI status."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.modules.auth.admin_permission_schemas import (
    AiProviderStatusOut,
    PermissionCatalogEntryOut,
    UserPermissionGrantCreateIn,
    UserPermissionGrantOut,
    UserPermissionGrantPatchIn,
    UserPermissionsDetailOut,
    PermissionSourceEntryOut,
)
from backend.app.modules.auth.models import User
from backend.app.modules.auth.permission_models import UserPermissionGrant
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz
from backend.app.services.permission_grant_service import GRANT_EXPIRES_UNCHANGED
from backend.app.services import permission_grant_service as pgs
from backend.app.services import ai_provider_service as ai_svc
from backend.app.core import config as app_config
from backend.app.modules.auth.org_access_admin_routes import router as org_access_admin_router
from backend.app.modules.auth.admin_settings_routes import router as admin_settings_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(org_access_admin_router)
router.include_router(admin_settings_router)


def require_permission_grants_admin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    authz.require_permission_http(user, policy.CAN_ADMIN_PERMISSION_GRANTS, db=db)
    return user


@router.get("/permissions/catalog", response_model=list[PermissionCatalogEntryOut])
def admin_permissions_catalog(
    _admin: User = Depends(require_permission_grants_admin),
) -> list[PermissionCatalogEntryOut]:
    out: list[PermissionCatalogEntryOut] = []
    for key in sorted(policy.ALL_PERMISSION_KEYS):
        out.append(
            PermissionCatalogEntryOut(
                permission_key=key,
                label=policy.PERMISSION_LABELS.get(key, key),
                default_roles=policy.roles_including_permission(key),
            )
        )
    return out


def _grant_out(g: UserPermissionGrant) -> UserPermissionGrantOut:
    return UserPermissionGrantOut(
        id=g.id,
        user_id=g.user_id,
        permission_key=g.permission_key,
        effect=g.effect,
        active=g.active,
        notes=g.notes,
        created_at=g.created_at,
        created_by_user_id=g.created_by_user_id,
        expires_at=g.expires_at,
    )


@router.get("/permissions/users/{user_id}", response_model=UserPermissionsDetailOut)
def admin_get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_permission_grants_admin),
) -> UserPermissionsDetailOut:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    grants = (
        db.query(UserPermissionGrant)
        .filter(UserPermissionGrant.user_id == user_id)
        .order_by(UserPermissionGrant.permission_key.asc())
        .all()
    )
    role_perms = sorted(authz.role_permissions_for_user(u))
    effective = sorted(authz.get_effective_permissions(db, u))
    src_raw = authz.list_user_permission_sources(db, u)
    sources = [PermissionSourceEntryOut(**x) for x in src_raw]
    return UserPermissionsDetailOut(
        user_id=u.id,
        email=u.email,
        role_names=u.role_names(),
        role_permissions=role_perms,
        effective_permissions=effective,
        grants=[_grant_out(g) for g in grants],
        permission_sources=sources,
    )


@router.post(
    "/permissions/users/{user_id}/grants",
    response_model=UserPermissionGrantOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_user_grant(
    user_id: str,
    body: UserPermissionGrantCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission_grants_admin),
) -> UserPermissionGrantOut:
    if body.permission_key not in policy.ALL_PERMISSION_KEYS:
        raise HTTPException(status_code=400, detail="Unknown permission_key")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        row = pgs.create_grant(
            db,
            target_user_id=user_id,
            permission_key=body.permission_key,
            effect=body.effect,
            actor_user_id=admin.id,
            notes=body.notes,
            expires_at=body.expires_at,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _grant_out(row)


@router.patch("/permissions/grants/{grant_id}", response_model=UserPermissionGrantOut)
def admin_patch_user_grant(
    grant_id: str,
    body: UserPermissionGrantPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission_grants_admin),
) -> UserPermissionGrantOut:
    exp = body.expires_at if "expires_at" in body.model_fields_set else GRANT_EXPIRES_UNCHANGED
    try:
        row = pgs.patch_grant(
            db,
            grant_id=grant_id,
            actor_user_id=admin.id,
            effect=body.effect,
            active=body.active,
            notes=body.notes,
            expires_at=exp,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _grant_out(row)


@router.delete("/permissions/grants/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user_grant(
    grant_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission_grants_admin),
) -> None:
    try:
        pgs.delete_grant(db, grant_id=grant_id, actor_user_id=admin.id, commit=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/ai/status", response_model=AiProviderStatusOut)
def admin_ai_status(
    _admin: User = Depends(require_permission_grants_admin),
) -> AiProviderStatusOut:
    st = ai_svc.describe_safe_status(app_config.settings)
    return AiProviderStatusOut(**st)
