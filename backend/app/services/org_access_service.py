"""CRUD + audit for internal/customer access groups, grants, and scopes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.auth.org_access_models import (
    CustomerAccessGroup,
    CustomerAccessGroupMembership,
    CustomerGroupEntityAccess,
    GroupEntityAccess,
    GroupPermissionGrant,
    InternalAccessGroup,
    InternalAccessGroupMembership,
    OrgAccessAuditLog,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_SKIP_PATCH = object()


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def write_audit(
    db: Session,
    *,
    actor_user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    detail: dict[str, Any] | None = None,
    commit: bool = False,
) -> None:
    db.add(
        OrgAccessAuditLog(
            id=str(uuid.uuid4()),
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail_json=_dumps(detail) if detail else None,
            created_at=utc_now(),
        )
    )
    if commit:
        db.commit()


# --- Internal groups ---


def list_internal_groups(db: Session) -> list[InternalAccessGroup]:
    return db.query(InternalAccessGroup).order_by(InternalAccessGroup.code.asc()).all()


def assert_internal_group_parent_valid(db: Session, *, group_id: str | None, parent_group_id: str | None) -> None:
    """Reject missing parent, self-parent, or cycles in internal_access_groups.parent_group_id."""
    if not parent_group_id:
        return
    if group_id and parent_group_id == group_id:
        raise ValueError("Group cannot be its own parent")
    p = db.get(InternalAccessGroup, parent_group_id)
    if not p:
        raise ValueError("Parent group not found")
    cur: InternalAccessGroup | None = p
    seen: set[str] = set()
    while cur is not None:
        if group_id and cur.id == group_id:
            raise ValueError("Parent assignment would create a cycle")
        if cur.id in seen:
            raise ValueError("Corrupt group hierarchy (cycle)")
        seen.add(cur.id)
        pid = cur.parent_group_id
        if not pid:
            break
        cur = db.get(InternalAccessGroup, pid)


def expanded_internal_group_ids_for_user(db: Session, *, user_id: str) -> set[str]:
    """
    Active direct membership groups plus ancestors when inherit_parent_grants is true on each step.
    Used for permission grants and internal entity scopes (§5.13).
    """
    groups = (
        db.query(InternalAccessGroup)
        .join(
            InternalAccessGroupMembership,
            InternalAccessGroupMembership.group_id == InternalAccessGroup.id,
        )
        .filter(
            InternalAccessGroupMembership.user_id == user_id,
            InternalAccessGroupMembership.active.is_(True),
            InternalAccessGroupMembership.left_at.is_(None),
            InternalAccessGroup.active.is_(True),
        )
        .all()
    )
    out: set[str] = set()
    for g in groups:
        cur: InternalAccessGroup | None = g
        while cur is not None and cur.active:
            out.add(cur.id)
            pid = cur.parent_group_id
            if not pid or not cur.inherit_parent_grants:
                break
            parent = db.get(InternalAccessGroup, pid)
            if not parent or not parent.active:
                break
            cur = parent
    return out


def create_internal_group(
    db: Session,
    *,
    name: str,
    code: str,
    group_type: str,
    description: str | None = None,
    parent_group_id: str | None = None,
    inherit_parent_grants: bool = True,
    actor_user_id: str | None = None,
    commit: bool = True,
) -> InternalAccessGroup:
    code_clean = code.strip()
    if db.query(InternalAccessGroup).filter(InternalAccessGroup.code == code_clean).first():
        raise ValueError("code already exists")
    pid = (parent_group_id or "").strip() or None
    if pid:
        assert_internal_group_parent_valid(db, group_id=None, parent_group_id=pid)
    now = utc_now()
    row = InternalAccessGroup(
        id=str(uuid.uuid4()),
        name=name.strip(),
        code=code_clean,
        group_type=group_type.strip(),
        parent_group_id=pid,
        inherit_parent_grants=inherit_parent_grants,
        active=True,
        description=description,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="internal_group_created",
        resource_type="internal_access_group",
        resource_id=row.id,
        detail={"code": row.code, "name": row.name, "parent_group_id": pid},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_internal_group(
    db: Session,
    *,
    group_id: str,
    name: str | None,
    active: bool | None,
    description: str | None,
    parent_group_id: Any = _SKIP_PATCH,
    inherit_parent_grants: Any = _SKIP_PATCH,
    actor_user_id: str | None = None,
    commit: bool = True,
) -> InternalAccessGroup:
    row = db.get(InternalAccessGroup, group_id)
    if not row:
        raise ValueError("Group not found")
    if name is not None:
        row.name = name.strip()
    if active is not None:
        row.active = active
    if description is not None:
        row.description = description
    if parent_group_id is not _SKIP_PATCH:
        if parent_group_id is None:
            pid = None
        else:
            pid = str(parent_group_id).strip() or None
        assert_internal_group_parent_valid(db, group_id=group_id, parent_group_id=pid)
        row.parent_group_id = pid
    if inherit_parent_grants is not _SKIP_PATCH:
        row.inherit_parent_grants = bool(inherit_parent_grants)
    row.updated_at = utc_now()
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="internal_group_updated",
        resource_type="internal_access_group",
        resource_id=row.id,
        detail={"active": row.active, "parent_group_id": row.parent_group_id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def list_internal_members(db: Session, *, group_id: str) -> list[InternalAccessGroupMembership]:
    return (
        db.query(InternalAccessGroupMembership)
        .filter(InternalAccessGroupMembership.group_id == group_id)
        .order_by(InternalAccessGroupMembership.joined_at.desc())
        .all()
    )


def add_internal_member(
    db: Session,
    *,
    group_id: str,
    user_id: str,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> InternalAccessGroupMembership:
    if not db.get(InternalAccessGroup, group_id):
        raise ValueError("Group not found")
    existing = (
        db.query(InternalAccessGroupMembership)
        .filter(
            InternalAccessGroupMembership.group_id == group_id,
            InternalAccessGroupMembership.user_id == user_id,
        )
        .one_or_none()
    )
    if existing:
        existing.active = True
        existing.left_at = None
        existing.notes = notes
        db.add(existing)
        write_audit(
            db,
            actor_user_id=actor_user_id,
            action="internal_membership_reactivated",
            resource_type="internal_access_group_membership",
            resource_id=existing.id,
            detail={"group_id": group_id, "user_id": user_id},
        )
        if commit:
            db.commit()
            db.refresh(existing)
        else:
            db.flush()
            db.refresh(existing)
        return existing
    row = InternalAccessGroupMembership(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=user_id,
        active=True,
        joined_at=utc_now(),
        left_at=None,
        notes=notes,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="internal_membership_created",
        resource_type="internal_access_group_membership",
        resource_id=row.id,
        detail={"group_id": group_id, "user_id": user_id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_internal_membership(
    db: Session,
    *,
    membership_id: str,
    active: bool | None,
    notes: str | None,
    left_at_clear: bool | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> InternalAccessGroupMembership:
    row = db.get(InternalAccessGroupMembership, membership_id)
    if not row:
        raise ValueError("Membership not found")
    if notes is not None:
        row.notes = notes
    if active is not None:
        row.active = active
        if not active:
            row.left_at = utc_now()
    if left_at_clear:
        row.left_at = None
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="internal_membership_updated",
        resource_type="internal_access_group_membership",
        resource_id=row.id,
        detail={"active": row.active},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def list_group_grants(db: Session, *, group_id: str) -> list[GroupPermissionGrant]:
    return (
        db.query(GroupPermissionGrant)
        .filter(GroupPermissionGrant.group_id == group_id)
        .order_by(GroupPermissionGrant.permission_key.asc())
        .all()
    )


def create_group_grant(
    db: Session,
    *,
    group_id: str,
    permission_key: str,
    effect: str,
    notes: str | None,
    expires_at: datetime | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> GroupPermissionGrant:
    if not db.get(InternalAccessGroup, group_id):
        raise ValueError("Group not found")
    existing = (
        db.query(GroupPermissionGrant)
        .filter(
            GroupPermissionGrant.group_id == group_id,
            GroupPermissionGrant.permission_key == permission_key,
        )
        .one_or_none()
    )
    if existing:
        existing.effect = effect
        existing.active = True
        existing.notes = notes
        existing.expires_at = expires_at
        existing.created_by_user_id = actor_user_id
        db.add(existing)
        write_audit(
            db,
            actor_user_id=actor_user_id,
            action="group_grant_upserted",
            resource_type="group_permission_grant",
            resource_id=existing.id,
            detail={"permission_key": permission_key, "effect": effect},
        )
        if commit:
            db.commit()
            db.refresh(existing)
        else:
            db.flush()
            db.refresh(existing)
        return existing
    row = GroupPermissionGrant(
        id=str(uuid.uuid4()),
        group_id=group_id,
        permission_key=permission_key,
        effect=effect,
        active=True,
        notes=notes,
        created_at=utc_now(),
        created_by_user_id=actor_user_id,
        expires_at=expires_at,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_grant_created",
        resource_type="group_permission_grant",
        resource_id=row.id,
        detail={"permission_key": permission_key, "effect": effect},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_group_grant(
    db: Session,
    *,
    grant_id: str,
    effect: str | None,
    active: bool | None,
    notes: str | None,
    expires_at: datetime | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> GroupPermissionGrant:
    row = db.get(GroupPermissionGrant, grant_id)
    if not row:
        raise ValueError("Grant not found")
    if effect is not None:
        row.effect = effect
    if active is not None:
        row.active = active
    if notes is not None:
        row.notes = notes
    if expires_at is not None:
        row.expires_at = expires_at
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_grant_updated",
        resource_type="group_permission_grant",
        resource_id=row.id,
        detail={},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def delete_group_grant(
    db: Session, *, grant_id: str, actor_user_id: str | None, commit: bool = True
) -> None:
    row = db.get(GroupPermissionGrant, grant_id)
    if not row:
        raise ValueError("Grant not found")
    gid = row.id
    db.delete(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_grant_deleted",
        resource_type="group_permission_grant",
        resource_id=gid,
        detail={},
    )
    if commit:
        db.commit()


def list_group_scopes(db: Session, *, group_id: str) -> list[GroupEntityAccess]:
    return (
        db.query(GroupEntityAccess)
        .filter(GroupEntityAccess.group_id == group_id)
        .order_by(GroupEntityAccess.entity_type.asc(), GroupEntityAccess.entity_id.asc())
        .all()
    )


def create_group_scope(
    db: Session,
    *,
    group_id: str,
    entity_type: str,
    entity_id: str,
    access_scope: str,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> GroupEntityAccess:
    if not db.get(InternalAccessGroup, group_id):
        raise ValueError("Group not found")
    row = GroupEntityAccess(
        id=str(uuid.uuid4()),
        group_id=group_id,
        entity_type=entity_type.strip(),
        entity_id=entity_id.strip(),
        access_scope=access_scope.strip(),
        active=True,
        notes=notes,
        created_at=utc_now(),
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_entity_scope_created",
        resource_type="group_entity_access",
        resource_id=row.id,
        detail={"entity_type": entity_type, "entity_id": entity_id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_group_scope(
    db: Session,
    *,
    scope_id: str,
    access_scope: str | None,
    active: bool | None,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> GroupEntityAccess:
    row = db.get(GroupEntityAccess, scope_id)
    if not row:
        raise ValueError("Scope not found")
    if access_scope is not None:
        row.access_scope = access_scope.strip()
    if active is not None:
        row.active = active
    if notes is not None:
        row.notes = notes
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_entity_scope_updated",
        resource_type="group_entity_access",
        resource_id=row.id,
        detail={},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def delete_group_scope(
    db: Session, *, scope_id: str, actor_user_id: str | None, commit: bool = True
) -> None:
    row = db.get(GroupEntityAccess, scope_id)
    if not row:
        raise ValueError("Scope not found")
    sid = row.id
    db.delete(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="group_entity_scope_deleted",
        resource_type="group_entity_access",
        resource_id=sid,
        detail={},
    )
    if commit:
        db.commit()


# --- Customer groups ---


def list_customer_groups(db: Session, *, customer_id: str) -> list[CustomerAccessGroup]:
    return (
        db.query(CustomerAccessGroup)
        .filter(CustomerAccessGroup.customer_id == customer_id)
        .order_by(CustomerAccessGroup.name.asc())
        .all()
    )


def create_customer_group(
    db: Session,
    *,
    customer_id: str,
    name: str,
    group_type: str,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerAccessGroup:
    now = utc_now()
    row = CustomerAccessGroup(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        name=name.strip(),
        group_type=group_type.strip(),
        active=True,
        notes=notes,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_access_group_created",
        resource_type="customer_access_group",
        resource_id=row.id,
        detail={"customer_id": customer_id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_customer_group(
    db: Session,
    *,
    group_id: str,
    name: str | None,
    group_type: str | None,
    active: bool | None,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerAccessGroup:
    row = db.get(CustomerAccessGroup, group_id)
    if not row:
        raise ValueError("Customer group not found")
    if name is not None:
        row.name = name.strip()
    if group_type is not None:
        row.group_type = group_type.strip()
    if active is not None:
        row.active = active
    if notes is not None:
        row.notes = notes
    row.updated_at = utc_now()
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_access_group_updated",
        resource_type="customer_access_group",
        resource_id=row.id,
        detail={},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def list_customer_group_members(db: Session, *, customer_access_group_id: str) -> list[CustomerAccessGroupMembership]:
    return (
        db.query(CustomerAccessGroupMembership)
        .filter(CustomerAccessGroupMembership.customer_access_group_id == customer_access_group_id)
        .all()
    )


def _normalize_portal_member_contact_scope(scope: str) -> str:
    s = (scope or "full").strip().lower()
    if s not in ("full", "billing", "operations"):
        raise ValueError("member_contact_scope must be full, billing, or operations")
    return s


def add_customer_group_member(
    db: Session,
    *,
    customer_access_group_id: str,
    portal_login_email: str,
    member_contact_scope: str,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerAccessGroupMembership:
    em = portal_login_email.strip().lower()
    mscope = _normalize_portal_member_contact_scope(member_contact_scope)
    existing = (
        db.query(CustomerAccessGroupMembership)
        .filter(
            CustomerAccessGroupMembership.customer_access_group_id == customer_access_group_id,
            CustomerAccessGroupMembership.portal_login_email == em,
        )
        .one_or_none()
    )
    if existing:
        existing.active = True
        existing.notes = notes
        existing.member_contact_scope = mscope
        db.add(existing)
        write_audit(
            db,
            actor_user_id=actor_user_id,
            action="customer_group_membership_reactivated",
            resource_type="customer_access_group_membership",
            resource_id=existing.id,
            detail={"email": em},
        )
        if commit:
            db.commit()
            db.refresh(existing)
        else:
            db.flush()
            db.refresh(existing)
        return existing
    row = CustomerAccessGroupMembership(
        id=str(uuid.uuid4()),
        customer_access_group_id=customer_access_group_id,
        portal_login_email=em,
        member_contact_scope=mscope,
        active=True,
        joined_at=utc_now(),
        notes=notes,
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_group_membership_created",
        resource_type="customer_access_group_membership",
        resource_id=row.id,
        detail={"email": em},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_customer_group_member(
    db: Session,
    *,
    membership_id: str,
    active: bool | None,
    member_contact_scope: str | None,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerAccessGroupMembership:
    row = db.get(CustomerAccessGroupMembership, membership_id)
    if not row:
        raise ValueError("Membership not found")
    if active is not None:
        row.active = active
    if member_contact_scope is not None:
        row.member_contact_scope = _normalize_portal_member_contact_scope(member_contact_scope)
    if notes is not None:
        row.notes = notes
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_group_membership_updated",
        resource_type="customer_access_group_membership",
        resource_id=row.id,
        detail={},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def list_customer_group_scopes(db: Session, *, customer_access_group_id: str) -> list[CustomerGroupEntityAccess]:
    return (
        db.query(CustomerGroupEntityAccess)
        .filter(CustomerGroupEntityAccess.customer_access_group_id == customer_access_group_id)
        .all()
    )


def create_customer_group_scope(
    db: Session,
    *,
    customer_access_group_id: str,
    entity_type: str,
    entity_id: str,
    access_scope: str,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerGroupEntityAccess:
    row = CustomerGroupEntityAccess(
        id=str(uuid.uuid4()),
        customer_access_group_id=customer_access_group_id,
        entity_type=entity_type.strip(),
        entity_id=entity_id.strip(),
        access_scope=access_scope.strip(),
        active=True,
        notes=notes,
        created_at=utc_now(),
    )
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_group_entity_scope_created",
        resource_type="customer_group_entity_access",
        resource_id=row.id,
        detail={"entity_type": entity_type, "entity_id": entity_id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_customer_group_scope(
    db: Session,
    *,
    scope_id: str,
    access_scope: str | None,
    active: bool | None,
    notes: str | None,
    actor_user_id: str | None,
    commit: bool = True,
) -> CustomerGroupEntityAccess:
    row = db.get(CustomerGroupEntityAccess, scope_id)
    if not row:
        raise ValueError("Scope not found")
    if access_scope is not None:
        row.access_scope = access_scope.strip()
    if active is not None:
        row.active = active
    if notes is not None:
        row.notes = notes
    db.add(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_group_entity_scope_updated",
        resource_type="customer_group_entity_access",
        resource_id=row.id,
        detail={},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def delete_customer_group_scope(
    db: Session, *, scope_id: str, actor_user_id: str | None, commit: bool = True
) -> None:
    row = db.get(CustomerGroupEntityAccess, scope_id)
    if not row:
        raise ValueError("Scope not found")
    sid = row.id
    db.delete(row)
    write_audit(
        db,
        actor_user_id=actor_user_id,
        action="customer_group_entity_scope_deleted",
        resource_type="customer_group_entity_access",
        resource_id=sid,
        detail={},
    )
    if commit:
        db.commit()
