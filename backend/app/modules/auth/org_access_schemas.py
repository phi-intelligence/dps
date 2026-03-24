from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class InternalAccessGroupOut(BaseModel):
    id: str
    name: str
    code: str
    group_type: str
    parent_group_id: str | None
    inherit_parent_grants: bool
    active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InternalAccessGroupCreateIn(BaseModel):
    name: str
    code: str
    group_type: str
    description: str | None = None
    parent_group_id: str | None = None
    inherit_parent_grants: bool = True


class InternalAccessGroupPatchIn(BaseModel):
    name: str | None = None
    active: bool | None = None
    description: str | None = None
    parent_group_id: str | None = None
    inherit_parent_grants: bool | None = None


class InternalMembershipOut(BaseModel):
    id: str
    group_id: str
    user_id: str
    active: bool
    joined_at: datetime
    left_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class InternalMembershipCreateIn(BaseModel):
    user_id: str
    notes: str | None = None


class InternalMembershipPatchIn(BaseModel):
    active: bool | None = None
    notes: str | None = None
    left_at_clear: bool | None = None


class GroupPermissionGrantOut(BaseModel):
    id: str
    group_id: str
    permission_key: str
    effect: str
    active: bool
    notes: str | None
    created_at: datetime
    created_by_user_id: str | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class GroupPermissionGrantCreateIn(BaseModel):
    permission_key: str
    effect: Literal["allow", "deny"]
    notes: str | None = None
    expires_at: datetime | None = None


class GroupPermissionGrantPatchIn(BaseModel):
    effect: Literal["allow", "deny"] | None = None
    active: bool | None = None
    notes: str | None = None
    expires_at: datetime | None = None


class GroupEntityAccessOut(BaseModel):
    id: str
    group_id: str
    entity_type: str
    entity_id: str
    access_scope: str
    active: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupEntityAccessCreateIn(BaseModel):
    entity_type: str
    entity_id: str
    access_scope: Literal["view", "manage", "full_access"]
    notes: str | None = None


class GroupEntityAccessPatchIn(BaseModel):
    access_scope: Literal["view", "manage", "full_access"] | None = None
    active: bool | None = None
    notes: str | None = None


class CustomerAccessGroupOut(BaseModel):
    id: str
    customer_id: str
    name: str
    group_type: str
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerAccessGroupCreateIn(BaseModel):
    name: str
    group_type: str
    notes: str | None = None


class CustomerAccessGroupPatchIn(BaseModel):
    name: str | None = None
    group_type: str | None = None
    active: bool | None = None
    notes: str | None = None


PortalMemberContactScope = Literal["full", "billing", "operations"]


class CustomerMembershipOut(BaseModel):
    id: str
    customer_access_group_id: str
    portal_login_email: str
    member_contact_scope: str
    active: bool
    joined_at: datetime
    notes: str | None

    model_config = {"from_attributes": True}


class CustomerMembershipCreateIn(BaseModel):
    portal_login_email: str
    member_contact_scope: PortalMemberContactScope = "full"
    notes: str | None = None


class CustomerMembershipPatchIn(BaseModel):
    active: bool | None = None
    member_contact_scope: PortalMemberContactScope | None = None
    notes: str | None = None


class CustomerGroupEntityAccessOut(BaseModel):
    id: str
    customer_access_group_id: str
    entity_type: str
    entity_id: str
    access_scope: str
    active: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerGroupEntityAccessCreateIn(BaseModel):
    entity_type: str
    entity_id: str
    access_scope: Literal["view", "manage", "full_access"]
    notes: str | None = None


class CustomerGroupEntityAccessPatchIn(BaseModel):
    access_scope: Literal["view", "manage", "full_access"] | None = None
    active: bool | None = None
    notes: str | None = None
