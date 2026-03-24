"""
Enterprise org structure: internal access groups, group grants/scopes, customer portal groups.

Distinct from Role: groups carry delegated grants and entity visibility scopes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InternalAccessGroup(Base):
    __tablename__ = "internal_access_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    group_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # §5.13 — optional parent; members may inherit grants/scopes from ancestors when inherit_parent_grants is true.
    parent_group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("internal_access_groups.id"), nullable=True, index=True
    )
    inherit_parent_grants: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class InternalAccessGroupMembership(Base):
    __tablename__ = "internal_access_group_memberships"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_internal_group_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("internal_access_groups.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class GroupPermissionGrant(Base):
    __tablename__ = "group_permission_grants"
    __table_args__ = (UniqueConstraint("group_id", "permission_key", name="uq_group_permission_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("internal_access_groups.id"), index=True, nullable=False)
    permission_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    effect: Mapped[str] = mapped_column(String(16), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class GroupEntityAccess(Base):
    __tablename__ = "group_entity_accesses"
    __table_args__ = (UniqueConstraint("group_id", "entity_type", "entity_id", name="uq_group_entity_scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("internal_access_groups.id"), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    access_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CustomerAccessGroup(Base):
    __tablename__ = "customer_access_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class CustomerAccessGroupMembership(Base):
    __tablename__ = "customer_access_group_memberships"
    __table_args__ = (UniqueConstraint("customer_access_group_id", "portal_login_email", name="uq_cag_member_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_access_group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customer_access_groups.id"), index=True, nullable=False
    )
    portal_login_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    # full | billing | operations — for comms routing / UX labels (§5.12); access still driven by entity scopes.
    member_contact_scope: Mapped[str] = mapped_column(String(32), default="full", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CustomerGroupEntityAccess(Base):
    __tablename__ = "customer_group_entity_accesses"
    __table_args__ = (
        UniqueConstraint(
            "customer_access_group_id", "entity_type", "entity_id", name="uq_customer_group_entity"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_access_group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customer_access_groups.id"), index=True, nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    access_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class OrgAccessAuditLog(Base):
    """Audit trail for org/group/grants/scopes (enterprise accountability)."""

    __tablename__ = "org_access_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
