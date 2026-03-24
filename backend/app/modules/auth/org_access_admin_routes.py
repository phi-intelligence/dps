"""Admin APIs: internal access groups, customer portal groups, grants, scopes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.modules.auth.models import User
from backend.app.modules.auth.org_access_models import InternalAccessGroup
from backend.app.modules.auth.org_access_schemas import (
    CustomerAccessGroupCreateIn,
    CustomerAccessGroupOut,
    CustomerAccessGroupPatchIn,
    CustomerGroupEntityAccessCreateIn,
    CustomerGroupEntityAccessOut,
    CustomerGroupEntityAccessPatchIn,
    CustomerMembershipCreateIn,
    CustomerMembershipOut,
    CustomerMembershipPatchIn,
    GroupEntityAccessCreateIn,
    GroupEntityAccessOut,
    GroupEntityAccessPatchIn,
    GroupPermissionGrantCreateIn,
    GroupPermissionGrantOut,
    GroupPermissionGrantPatchIn,
    InternalAccessGroupCreateIn,
    InternalAccessGroupOut,
    InternalAccessGroupPatchIn,
    InternalMembershipCreateIn,
    InternalMembershipOut,
    InternalMembershipPatchIn,
)
from backend.app.modules.crm.models import Customer
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz
from backend.app.services import org_access_service as oas

router = APIRouter()


def require_org_access_admin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    authz.require_permission_http(user, policy.CAN_ADMIN_ORG_ACCESS, db=db)
    return user


@router.get("/access-groups", response_model=list[InternalAccessGroupOut])
def list_access_groups(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[InternalAccessGroupOut]:
    rows = oas.list_internal_groups(db)
    return [InternalAccessGroupOut.model_validate(r) for r in rows]


@router.post("/access-groups", response_model=InternalAccessGroupOut, status_code=status.HTTP_201_CREATED)
def create_access_group(
    body: InternalAccessGroupCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> InternalAccessGroupOut:
    try:
        row = oas.create_internal_group(
            db,
            name=body.name,
            code=body.code,
            group_type=body.group_type,
            description=body.description,
            parent_group_id=body.parent_group_id,
            inherit_parent_grants=body.inherit_parent_grants,
            actor_user_id=admin.id,
            commit=True,
        )
        return InternalAccessGroupOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/access-groups/{group_id}", response_model=InternalAccessGroupOut)
def patch_access_group(
    group_id: str,
    body: InternalAccessGroupPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> InternalAccessGroupOut:
    data = body.model_dump(exclude_unset=True)
    try:
        kw: dict = {
            "db": db,
            "group_id": group_id,
            "name": data.get("name"),
            "active": data.get("active"),
            "description": data.get("description"),
            "actor_user_id": admin.id,
            "commit": True,
        }
        if "parent_group_id" in data:
            kw["parent_group_id"] = data["parent_group_id"]
        if "inherit_parent_grants" in data:
            kw["inherit_parent_grants"] = data["inherit_parent_grants"]
        row = oas.patch_internal_group(**kw)
        return InternalAccessGroupOut.model_validate(row)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if msg == "Group not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e


@router.get("/access-groups/{group_id}/members", response_model=list[InternalMembershipOut])
def list_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[InternalMembershipOut]:
    if not db.get(InternalAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    rows = oas.list_internal_members(db, group_id=group_id)
    return [InternalMembershipOut.model_validate(r) for r in rows]


@router.post(
    "/access-groups/{group_id}/members",
    response_model=InternalMembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def add_group_member(
    group_id: str,
    body: InternalMembershipCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> InternalMembershipOut:
    try:
        row = oas.add_internal_member(
            db,
            group_id=group_id,
            user_id=body.user_id,
            notes=body.notes,
            actor_user_id=admin.id,
            commit=True,
        )
        return InternalMembershipOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/access-group-memberships/{membership_id}", response_model=InternalMembershipOut)
def patch_group_membership(
    membership_id: str,
    body: InternalMembershipPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> InternalMembershipOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_internal_membership(
            db,
            membership_id=membership_id,
            active=data.get("active"),
            notes=data.get("notes"),
            left_at_clear=data.get("left_at_clear"),
            actor_user_id=admin.id,
            commit=True,
        )
        return InternalMembershipOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/access-groups/{group_id}/permissions", response_model=list[GroupPermissionGrantOut])
def list_group_permissions(
    group_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[GroupPermissionGrantOut]:
    if not db.get(InternalAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    rows = oas.list_group_grants(db, group_id=group_id)
    return [GroupPermissionGrantOut.model_validate(r) for r in rows]


@router.post(
    "/access-groups/{group_id}/permissions",
    response_model=GroupPermissionGrantOut,
    status_code=status.HTTP_201_CREATED,
)
def add_group_permission(
    group_id: str,
    body: GroupPermissionGrantCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> GroupPermissionGrantOut:
    if body.permission_key not in policy.ALL_PERMISSION_KEYS:
        raise HTTPException(status_code=400, detail="Unknown permission_key")
    try:
        row = oas.create_group_grant(
            db,
            group_id=group_id,
            permission_key=body.permission_key,
            effect=body.effect,
            notes=body.notes,
            expires_at=body.expires_at,
            actor_user_id=admin.id,
            commit=True,
        )
        return GroupPermissionGrantOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/access-group-permissions/{grant_id}", response_model=GroupPermissionGrantOut)
def patch_group_permission(
    grant_id: str,
    body: GroupPermissionGrantPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> GroupPermissionGrantOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_group_grant(
            db,
            grant_id=grant_id,
            effect=data.get("effect"),
            active=data.get("active"),
            notes=data.get("notes"),
            expires_at=data.get("expires_at"),
            actor_user_id=admin.id,
            commit=True,
        )
        return GroupPermissionGrantOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/access-group-permissions/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_permission(
    grant_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> None:
    try:
        oas.delete_group_grant(db, grant_id=grant_id, actor_user_id=admin.id, commit=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/access-groups/{group_id}/scopes", response_model=list[GroupEntityAccessOut])
def list_group_scopes(
    group_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[GroupEntityAccessOut]:
    if not db.get(InternalAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    rows = oas.list_group_scopes(db, group_id=group_id)
    return [GroupEntityAccessOut.model_validate(r) for r in rows]


@router.post(
    "/access-groups/{group_id}/scopes",
    response_model=GroupEntityAccessOut,
    status_code=status.HTTP_201_CREATED,
)
def add_group_scope(
    group_id: str,
    body: GroupEntityAccessCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> GroupEntityAccessOut:
    try:
        row = oas.create_group_scope(
            db,
            group_id=group_id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            access_scope=body.access_scope,
            notes=body.notes,
            actor_user_id=admin.id,
            commit=True,
        )
        return GroupEntityAccessOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/access-group-scopes/{scope_id}", response_model=GroupEntityAccessOut)
def patch_group_scope(
    scope_id: str,
    body: GroupEntityAccessPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> GroupEntityAccessOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_group_scope(
            db,
            scope_id=scope_id,
            access_scope=data.get("access_scope"),
            active=data.get("active"),
            notes=data.get("notes"),
            actor_user_id=admin.id,
            commit=True,
        )
        return GroupEntityAccessOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/access-group-scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_scope(
    scope_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> None:
    try:
        oas.delete_group_scope(db, scope_id=scope_id, actor_user_id=admin.id, commit=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# --- Customer groups (per customer) ---


@router.get("/customers/{customer_id}/access-groups", response_model=list[CustomerAccessGroupOut])
def list_customer_access_groups(
    customer_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[CustomerAccessGroupOut]:
    if not db.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    rows = oas.list_customer_groups(db, customer_id=customer_id)
    return [CustomerAccessGroupOut.model_validate(r) for r in rows]


@router.post(
    "/customers/{customer_id}/access-groups",
    response_model=CustomerAccessGroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_access_group(
    customer_id: str,
    body: CustomerAccessGroupCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerAccessGroupOut:
    if not db.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    row = oas.create_customer_group(
        db,
        customer_id=customer_id,
        name=body.name,
        group_type=body.group_type,
        notes=body.notes,
        actor_user_id=admin.id,
        commit=True,
    )
    return CustomerAccessGroupOut.model_validate(row)


@router.patch("/customer-access-groups/{group_id}", response_model=CustomerAccessGroupOut)
def patch_customer_access_group(
    group_id: str,
    body: CustomerAccessGroupPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerAccessGroupOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_customer_group(
            db,
            group_id=group_id,
            name=data.get("name"),
            group_type=data.get("group_type"),
            active=data.get("active"),
            notes=data.get("notes"),
            actor_user_id=admin.id,
            commit=True,
        )
        return CustomerAccessGroupOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/customer-access-groups/{group_id}/members",
    response_model=list[CustomerMembershipOut],
)
def list_customer_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[CustomerMembershipOut]:
    from backend.app.modules.auth.org_access_models import CustomerAccessGroup

    if not db.get(CustomerAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Customer group not found")
    rows = oas.list_customer_group_members(db, customer_access_group_id=group_id)
    return [CustomerMembershipOut.model_validate(r) for r in rows]


@router.post(
    "/customer-access-groups/{group_id}/members",
    response_model=CustomerMembershipOut,
    status_code=status.HTTP_201_CREATED,
)
def add_customer_group_member(
    group_id: str,
    body: CustomerMembershipCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerMembershipOut:
    from backend.app.modules.auth.org_access_models import CustomerAccessGroup

    if not db.get(CustomerAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Customer group not found")
    try:
        row = oas.add_customer_group_member(
            db,
            customer_access_group_id=group_id,
            portal_login_email=body.portal_login_email,
            member_contact_scope=body.member_contact_scope,
            notes=body.notes,
            actor_user_id=admin.id,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return CustomerMembershipOut.model_validate(row)


@router.patch("/customer-access-group-memberships/{membership_id}", response_model=CustomerMembershipOut)
def patch_customer_group_membership(
    membership_id: str,
    body: CustomerMembershipPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerMembershipOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_customer_group_member(
            db,
            membership_id=membership_id,
            active=data.get("active"),
            member_contact_scope=data.get("member_contact_scope"),
            notes=data.get("notes"),
            actor_user_id=admin.id,
            commit=True,
        )
        return CustomerMembershipOut.model_validate(row)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e


@router.get(
    "/customer-access-groups/{group_id}/scopes",
    response_model=list[CustomerGroupEntityAccessOut],
)
def list_customer_group_scopes(
    group_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_org_access_admin),
) -> list[CustomerGroupEntityAccessOut]:
    from backend.app.modules.auth.org_access_models import CustomerAccessGroup

    if not db.get(CustomerAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Customer group not found")
    rows = oas.list_customer_group_scopes(db, customer_access_group_id=group_id)
    return [CustomerGroupEntityAccessOut.model_validate(r) for r in rows]


@router.post(
    "/customer-access-groups/{group_id}/scopes",
    response_model=CustomerGroupEntityAccessOut,
    status_code=status.HTTP_201_CREATED,
)
def add_customer_group_scope(
    group_id: str,
    body: CustomerGroupEntityAccessCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerGroupEntityAccessOut:
    from backend.app.modules.auth.org_access_models import CustomerAccessGroup

    if not db.get(CustomerAccessGroup, group_id):
        raise HTTPException(status_code=404, detail="Customer group not found")
    row = oas.create_customer_group_scope(
        db,
        customer_access_group_id=group_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        access_scope=body.access_scope,
        notes=body.notes,
        actor_user_id=admin.id,
        commit=True,
    )
    return CustomerGroupEntityAccessOut.model_validate(row)


@router.patch("/customer-access-group-scopes/{scope_id}", response_model=CustomerGroupEntityAccessOut)
def patch_customer_group_scope(
    scope_id: str,
    body: CustomerGroupEntityAccessPatchIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> CustomerGroupEntityAccessOut:
    data = body.model_dump(exclude_unset=True)
    try:
        row = oas.patch_customer_group_scope(
            db,
            scope_id=scope_id,
            access_scope=data.get("access_scope"),
            active=data.get("active"),
            notes=data.get("notes"),
            actor_user_id=admin.id,
            commit=True,
        )
        return CustomerGroupEntityAccessOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/customer-access-group-scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_group_scope(
    scope_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_org_access_admin),
) -> None:
    try:
        oas.delete_customer_group_scope(db, scope_id=scope_id, actor_user_id=admin.id, commit=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
