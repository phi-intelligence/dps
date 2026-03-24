"""
Central permission resolution: role baseline + per-user grants + internal group grants.

Precedence for each permission_key (deterministic):
1. Active, non-expired user grant with effect=deny → not allowed
2. Active, non-expired user grant with effect=allow → allowed
3. Any active internal group grant (member of group) with effect=deny → not allowed
4. Any active internal group grant with effect=allow → allowed
5. Union of permissions from all assigned roles → allowed if any role includes the key
6. Otherwise → not allowed

Entity visibility (contracts/sites/…) for internal users is layered separately via
`scoped_access_service` (group entity scopes); Admin bypasses those scopes.

When Session is omitted, only role baseline is evaluated (legacy / offline checks).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.auth.org_access_models import (
    GroupPermissionGrant,
    InternalAccessGroup,
    InternalAccessGroupMembership,
)
from backend.app.modules.auth.permission_models import UserPermissionGrant
from backend.app.services import authorization_policy as policy
from backend.app.services import org_access_service as org_access


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def role_permissions_for_user(user: User) -> set[str]:
    """Permissions from role membership only (no user-level grants)."""
    out: set[str] = set()
    for role in user.roles:
        out |= set(policy.ROLE_PERMISSIONS.get(role.name, frozenset()))
    return out


def permissions_for_user(user: User) -> set[str]:
    """Backward-compatible alias: role-only permissions."""
    return role_permissions_for_user(user)


def _active_grant(
    db: Session, *, user_id: str, permission_key: str
) -> UserPermissionGrant | None:
    now = utc_now()
    return (
        db.query(UserPermissionGrant)
        .filter(
            UserPermissionGrant.user_id == user_id,
            UserPermissionGrant.permission_key == permission_key,
            UserPermissionGrant.active.is_(True),
            or_(UserPermissionGrant.expires_at.is_(None), UserPermissionGrant.expires_at > now),
        )
        .one_or_none()
    )


def _group_grant_effects_for_user(
    db: Session, *, user_id: str, permission_key: str
) -> tuple[bool, bool]:
    """Whether user's expanded internal groups (§5.13 inheritance) have any deny / any allow for this key."""
    now = utc_now()
    gid_set = org_access.expanded_internal_group_ids_for_user(db, user_id=user_id)
    if not gid_set:
        return False, False
    rows = (
        db.query(GroupPermissionGrant.effect)
        .join(InternalAccessGroup, InternalAccessGroup.id == GroupPermissionGrant.group_id)
        .filter(
            GroupPermissionGrant.group_id.in_(gid_set),
            InternalAccessGroup.active.is_(True),
            GroupPermissionGrant.permission_key == permission_key,
            GroupPermissionGrant.active.is_(True),
            or_(GroupPermissionGrant.expires_at.is_(None), GroupPermissionGrant.expires_at > now),
        )
        .all()
    )
    has_deny = any(r[0] == "deny" for r in rows)
    has_allow = any(r[0] == "allow" for r in rows)
    return has_deny, has_allow


def user_has_permission(user: User, permission_key: str, db: Session | None = None) -> bool:
    if permission_key not in policy.ALL_PERMISSION_KEYS:
        return False
    if db is None:
        return permission_key in role_permissions_for_user(user)
    grant = _active_grant(db, user_id=user.id, permission_key=permission_key)
    if grant is not None:
        return grant.effect == "allow"
    g_deny, g_allow = _group_grant_effects_for_user(db, user_id=user.id, permission_key=permission_key)
    if g_deny:
        return False
    if g_allow:
        return True
    return permission_key in role_permissions_for_user(user)


def get_effective_permissions(db: Session, user: User) -> set[str]:
    """All permission keys the user may exercise (grants override role per key)."""
    return {key for key in policy.ALL_PERMISSION_KEYS if user_has_permission(user, key, db=db)}


def permission_source_detail(
    db: Session | None, user: User, permission_key: str
) -> dict[str, Any]:
    """Single-key breakdown for admin visibility."""
    role = role_permissions_for_user(user)
    in_role = permission_key in role
    roles_granting = [r.name for r in user.roles if permission_key in policy.ROLE_PERMISSIONS.get(r.name, frozenset())]
    grant_row: UserPermissionGrant | None = None
    if db is not None:
        grant_row = (
            db.query(UserPermissionGrant)
            .filter(
                UserPermissionGrant.user_id == user.id,
                UserPermissionGrant.permission_key == permission_key,
            )
            .one_or_none()
        )
    now = utc_now()
    grant_active = bool(
        grant_row
        and grant_row.active
        and (grant_row.expires_at is None or grant_row.expires_at > now)
    )
    sources: list[dict[str, Any]] = []
    if in_role:
        sources.append({"source": "role", "roles": roles_granting, "precedence_rank": 5})
    if grant_row:
        sources.append(
            {
                "source": "user_grant",
                "precedence_rank": 1 if grant_row.effect == "deny" else 2,
                "grant_id": grant_row.id,
                "effect": grant_row.effect,
                "active": grant_row.active,
                "expires_at": grant_row.expires_at.isoformat() if grant_row.expires_at else None,
                "counts_for_effective": grant_active,
            }
        )
    if db is not None:
        gid_set = org_access.expanded_internal_group_ids_for_user(db, user_id=user.id)
        if gid_set:
            g_rows = (
                db.query(GroupPermissionGrant, InternalAccessGroup.code)
                .join(InternalAccessGroup, InternalAccessGroup.id == GroupPermissionGrant.group_id)
                .filter(
                    GroupPermissionGrant.group_id.in_(gid_set),
                    GroupPermissionGrant.permission_key == permission_key,
                )
                .all()
            )
        else:
            g_rows = []
        for gg, gcode in g_rows:
            sources.append(
                {
                    "source": "group_grant",
                    "precedence_rank": 3 if gg.effect == "deny" else 4,
                    "group_code": gcode,
                    "grant_id": gg.id,
                    "effect": gg.effect,
                    "active": gg.active,
                    "expires_at": gg.expires_at.isoformat() if gg.expires_at else None,
                    "counts_for_effective": bool(
                        gg.active
                        and (gg.expires_at is None or gg.expires_at > now)
                    ),
                }
            )
    return {
        "permission_key": permission_key,
        "effective": user_has_permission(user, permission_key, db=db),
        "role_baseline_allowed": in_role,
        "sources": sources,
    }


def list_user_permission_sources(db: Session, user: User) -> list[dict[str, Any]]:
    """Per-key source breakdown (admin / debug; no secrets)."""
    return [permission_source_detail(db, user, key) for key in sorted(policy.ALL_PERMISSION_KEYS)]


def resolve_user_groups(db: Session, user: User) -> list[dict[str, Any]]:
    rows = (
        db.query(InternalAccessGroup)
        .join(
            InternalAccessGroupMembership,
            InternalAccessGroupMembership.group_id == InternalAccessGroup.id,
        )
        .filter(
            InternalAccessGroupMembership.user_id == user.id,
            InternalAccessGroupMembership.active.is_(True),
            InternalAccessGroupMembership.left_at.is_(None),
            InternalAccessGroup.active.is_(True),
        )
        .order_by(InternalAccessGroup.code.asc())
        .all()
    )
    return [
        {
            "group_id": g.id,
            "code": g.code,
            "name": g.name,
            "group_type": g.group_type,
            "parent_group_id": g.parent_group_id,
            "inherit_parent_grants": g.inherit_parent_grants,
        }
        for g in rows
    ]


def user_has_scoped_access(
    db: Session,
    user: User,
    *,
    entity_type: str,
    entity_id: str,
    required_scope: str = "view",
) -> bool:
    from backend.app.services import scoped_access_service as scoped

    return scoped.user_can_access_internal_entity(
        db, user, entity_type=entity_type, entity_id=entity_id, required_scope=required_scope
    )


def resolve_effective_permissions(db: Session, user: User) -> set[str]:
    """Alias for get_effective_permissions (explicit naming for callers)."""
    return get_effective_permissions(db, user)


def require_permission_http(user: User, permission_key: str, db: Session | None = None) -> None:
    if not user_has_permission(user, permission_key, db=db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission_key}",
        )


def resolve_rec_action_permission_key(*, action_type: str, preview: dict[str, Any]) -> str | None:
    """Returns required fine-grained permission, or None if role-level route access is enough."""
    extra = preview.get("extra")
    ex: dict[str, Any] = extra if isinstance(extra, dict) else {}

    if action_type == "resolve_defect":
        sev = str(ex.get("defect_severity") or "").lower()
        if sev in ("critical", "blocking"):
            return policy.CAN_OVERRIDE_VEHICLE_BLOCK
        return None

    if action_type in ("assign_alternate_equipment", "move_equipment"):
        cs = str(ex.get("calibration_status") or "")
        if cs == "expired":
            return policy.CAN_OVERRIDE_EQUIPMENT_BLOCK
        return None

    return policy.RECOMMENDATION_ACTION_PERMISSION.get(action_type)


def describe_rec_action_authorization(
    *,
    db: Session | None,
    user: User,
    action_type: str,
    preview: dict[str, Any],
) -> dict[str, Any]:
    """
    Merged into recommendation action preview for UI / API consumers.
    """
    pk = resolve_rec_action_permission_key(action_type=action_type, preview=preview)
    has = user_has_permission(user, pk, db=db) if pk else True
    return {
        "required_permission": pk,
        "user_has_permission": has,
        "direct_execute_allowed": bool(has),
        "approval_request_allowed": pk is not None and not has,
        "notes": (
            None
            if has
            else (
                f"This action requires permission '{pk}'. "
                "Create an approval request or ask an authorized approver."
                if pk
                else None
            )
        ),
    }


def assert_rec_action_allowed(
    *,
    db: Session | None,
    user: User,
    action_type: str,
    preview: dict[str, Any],
) -> None:
    pk = resolve_rec_action_permission_key(action_type=action_type, preview=preview)
    if pk and not user_has_permission(user, pk, db=db):
        raise ValueError(
            f"Action '{action_type}' requires permission '{pk}'. "
            "Use POST /approvals to request execution if you lack this permission."
        )


def approver_permission_for_approval_type(approval_type: str) -> str:
    """Which permission the approver must hold to approve this request."""
    m = {
        "invoice_hold": policy.CAN_HOLD_INVOICE,
        "invoice_release": policy.CAN_RELEASE_INVOICE,
        "purchase_order_approval": policy.CAN_APPROVE_PURCHASE_ORDER,
        "repricing_approval": policy.CAN_APPROVE_REPRICING,
        "contract_exit_approval": policy.CAN_DECIDE_CONTRACT_REVIEW,
        "customer_notification_override": policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION,
        "vehicle_block_override": policy.CAN_OVERRIDE_VEHICLE_BLOCK,
        "equipment_block_override": policy.CAN_OVERRIDE_EQUIPMENT_BLOCK,
    }
    if approval_type not in m:
        raise ValueError(f"Unknown approval_type: {approval_type}")
    return m[approval_type]


def list_approval_types_visible_to_user(db: Session | None, user: User) -> set[str]:
    """Approval types this user may approve (for UI filters)."""
    out: set[str] = set()
    for at, req in [
        ("invoice_hold", policy.CAN_HOLD_INVOICE),
        ("invoice_release", policy.CAN_RELEASE_INVOICE),
        ("purchase_order_approval", policy.CAN_APPROVE_PURCHASE_ORDER),
        ("repricing_approval", policy.CAN_APPROVE_REPRICING),
        ("contract_exit_approval", policy.CAN_DECIDE_CONTRACT_REVIEW),
        ("customer_notification_override", policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION),
        ("vehicle_block_override", policy.CAN_OVERRIDE_VEHICLE_BLOCK),
        ("equipment_block_override", policy.CAN_OVERRIDE_EQUIPMENT_BLOCK),
    ]:
        if user_has_permission(user, req, db=db):
            out.add(at)
    return out
