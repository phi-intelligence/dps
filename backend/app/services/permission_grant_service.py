"""CRUD for user permission grants + audit rows."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

_UNSET: Any = object()
# Public sentinel for PATCH: leave expires_at unchanged.
GRANT_EXPIRES_UNCHANGED: Any = _UNSET

from backend.app.modules.auth.permission_models import PermissionGrantAuditLog, UserPermissionGrant


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    grant_id: str | None,
    actor_user_id: str | None,
    target_user_id: str,
    permission_key: str,
    action: str,
    old_effect: str | None = None,
    new_effect: str | None = None,
    old_active: bool | None = None,
    new_active: bool | None = None,
    notes: str | None = None,
) -> None:
    db.add(
        PermissionGrantAuditLog(
            id=str(uuid.uuid4()),
            grant_id=grant_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            permission_key=permission_key,
            action=action,
            old_effect=old_effect,
            new_effect=new_effect,
            old_active=old_active,
            new_active=new_active,
            notes=notes,
        )
    )


def list_grants_for_user(db: Session, *, user_id: str, include_inactive: bool = False) -> list[UserPermissionGrant]:
    q = db.query(UserPermissionGrant).filter(UserPermissionGrant.user_id == user_id)
    if not include_inactive:
        q = q.filter(UserPermissionGrant.active.is_(True))
    return q.order_by(UserPermissionGrant.permission_key.asc()).all()


def get_grant(db: Session, *, grant_id: str) -> UserPermissionGrant | None:
    return db.get(UserPermissionGrant, grant_id)


def create_grant(
    db: Session,
    *,
    target_user_id: str,
    permission_key: str,
    effect: str,
    actor_user_id: str | None,
    notes: str | None = None,
    expires_at: datetime | None = None,
    commit: bool = True,
) -> UserPermissionGrant:
    if effect not in ("allow", "deny"):
        raise ValueError("effect must be allow or deny")
    exists = (
        db.query(UserPermissionGrant)
        .filter(
            UserPermissionGrant.user_id == target_user_id,
            UserPermissionGrant.permission_key == permission_key,
        )
        .one_or_none()
    )
    if exists:
        raise ValueError("A grant for this user and permission_key already exists; use PATCH.")

    row = UserPermissionGrant(
        id=str(uuid.uuid4()),
        user_id=target_user_id,
        permission_key=permission_key,
        effect=effect,
        active=True,
        notes=notes,
        created_by_user_id=actor_user_id,
        expires_at=expires_at,
    )
    db.add(row)
    db.flush()
    _audit(
        db,
        grant_id=row.id,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        permission_key=permission_key,
        action="created",
        new_effect=effect,
        new_active=True,
        notes=notes,
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def patch_grant(
    db: Session,
    *,
    grant_id: str,
    actor_user_id: str | None,
    effect: str | None = None,
    active: bool | None = None,
    notes: str | None = None,
    expires_at: datetime | None | Any = _UNSET,
    commit: bool = True,
) -> UserPermissionGrant:
    row = db.get(UserPermissionGrant, grant_id)
    if not row:
        raise ValueError("Grant not found")
    old_effect, old_active = row.effect, row.active
    if effect is not None:
        if effect not in ("allow", "deny"):
            raise ValueError("effect must be allow or deny")
        row.effect = effect
    if active is not None:
        row.active = active
    if notes is not None:
        row.notes = notes
    if expires_at is not _UNSET:
        row.expires_at = expires_at
    db.add(row)
    db.flush()
    _audit(
        db,
        grant_id=row.id,
        actor_user_id=actor_user_id,
        target_user_id=row.user_id,
        permission_key=row.permission_key,
        action="updated",
        old_effect=old_effect,
        new_effect=row.effect,
        old_active=old_active,
        new_active=row.active,
        notes=notes,
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def delete_grant(db: Session, *, grant_id: str, actor_user_id: str | None, commit: bool = True) -> None:
    row = db.get(UserPermissionGrant, grant_id)
    if not row:
        raise ValueError("Grant not found")
    uid, pk, eff, act = row.user_id, row.permission_key, row.effect, row.active
    _audit(
        db,
        grant_id=None,
        actor_user_id=actor_user_id,
        target_user_id=uid,
        permission_key=pk,
        action="deleted",
        old_effect=eff,
        old_active=act,
        notes="Grant row deleted",
    )
    db.delete(row)
    if commit:
        db.commit()
    else:
        db.flush()
