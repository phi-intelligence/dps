"""
Internal entity scoping for enterprise access groups.

When a user belongs to at least one active internal group that has active GroupEntityAccess rows,
visibility is restricted to the union of those scoped entities (unless the user is Admin).

Admin users bypass internal entity scope checks.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.auth.org_access_models import GroupEntityAccess
from backend.app.services import org_access_service as org_access


SCOPE_RANK: dict[str, int] = {
    "view": 1,
    "manage": 2,
    "full_access": 3,
}


def _scope_meets(required: str, granted: str) -> bool:
    return SCOPE_RANK.get(granted, 0) >= SCOPE_RANK.get(required, 99)


def user_is_admin(user: User) -> bool:
    return "Admin" in user.role_names()


def internal_entity_scope_restricts(db: Session, user: User) -> bool:
    """
    True when internal group-based entity scopes apply to this user (non-Admin).
    """
    if user_is_admin(user):
        return False
    return _user_internal_scoped_group_ids(db, user.id) is not None


def _user_internal_scoped_group_ids(db: Session, user_id: str) -> list[str] | None:
    """
    Returns expanded internal group ids (§5.13) when any of those groups has active entity scopes; else None.
    """
    gids = org_access.expanded_internal_group_ids_for_user(db, user_id=user_id)
    if not gids:
        return None
    has_scope = (
        db.query(GroupEntityAccess.id)
        .filter(
            GroupEntityAccess.group_id.in_(list(gids)),
            GroupEntityAccess.active.is_(True),
        )
        .limit(1)
        .first()
    )
    if not has_scope:
        return None
    return list(gids)


def _max_internal_scope_rank(
    db: Session, *, user_id: str, entity_type: str, entity_id: str
) -> int:
    group_ids = _user_internal_scoped_group_ids(db, user_id)
    if not group_ids:
        return 0
    rows = (
        db.query(GroupEntityAccess.access_scope)
        .filter(
            GroupEntityAccess.group_id.in_(group_ids),
            GroupEntityAccess.entity_type == entity_type,
            GroupEntityAccess.entity_id == entity_id,
            GroupEntityAccess.active.is_(True),
        )
        .all()
    )
    best = 0
    for (sc,) in rows:
        best = max(best, SCOPE_RANK.get(sc or "", 0))
    return best


def user_can_access_internal_entity(
    db: Session,
    user: User,
    *,
    entity_type: str,
    entity_id: str,
    required_scope: str = "view",
) -> bool:
    """
    If internal entity scoping does not apply, returns True (route RBAC still applies).
    If it applies, returns True only when a matching scope row meets required_scope.
    """
    if user_is_admin(user):
        return True
    if not internal_entity_scope_restricts(db, user):
        return True
    rank = _max_internal_scope_rank(db, user_id=user.id, entity_type=entity_type, entity_id=entity_id)
    if rank == 0:
        return False
    # any row that matched contributes at least its rank; required_scope must be met by max rank
    return rank >= SCOPE_RANK.get(required_scope, 99)


def filter_contracts_for_internal_user(db: Session, user: User, contracts: list) -> list:
    if not internal_entity_scope_restricts(db, user):
        return contracts
    out: list = []
    for c in contracts:
        cid = c.id if hasattr(c, "id") else str(c)
        if user_can_access_internal_entity(db, user, entity_type="contract", entity_id=cid, required_scope="view"):
            out.append(c)
        elif hasattr(c, "site_id") and c.site_id and user_can_access_internal_entity(
            db, user, entity_type="site", entity_id=c.site_id, required_scope="view"
        ):
            out.append(c)
    return out


def filter_sites_for_internal_user(db: Session, user: User, sites: list) -> list:
    if not internal_entity_scope_restricts(db, user):
        return sites
    out: list = []
    for s in sites:
        sid = s.id if hasattr(s, "id") else str(s)
        if user_can_access_internal_entity(db, user, entity_type="site", entity_id=sid, required_scope="view"):
            out.append(s)
    return out
