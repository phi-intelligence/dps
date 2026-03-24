from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class User(Base):
    __tablename__ = "users"

    # Using UUID strings keeps it portable across services later (microservice-ready).
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Optional van / hardware id for dispatch (operational position resolver).
    assigned_vehicle_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    roles: Mapped[list[Role]] = relationship("Role", secondary=user_roles, lazy="joined")

    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

