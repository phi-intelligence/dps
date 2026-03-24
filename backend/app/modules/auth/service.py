from __future__ import annotations

import os

from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.modules.auth.models import Role, User


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(subject=user.id, roles=user.role_names())


def ensure_default_roles(db: Session) -> None:
    default_roles = [
        "Admin",
        "Dispatcher",
        "Engineer",
        "Client",
        "Finance",
        "Commercial",
        "Ops_Manager",
        "Viewer",
    ]
    for name in default_roles:
        existing = db.query(Role).filter(Role.name == name).first()
        if not existing:
            db.add(Role(name=name))
    db.commit()


def ensure_default_admin(db: Session) -> None:
    """
    Dev-only helper to make first run easier.
    Creates default dev users:
    - admin@example.com / admin (Admin)
    - dispatcher@example.com / dispatcher (Dispatcher)
    - engineer@example.com / engineer (Engineer)
    """

    from backend.app.core.config import settings

    ensure_default_roles(db)

    admin_email = os.getenv("PHI_DPS_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("PHI_DPS_ADMIN_PASSWORD", "admin")

    dispatcher_email = os.getenv("PHI_DPS_DISPATCHER_EMAIL", "dispatcher@example.com")
    dispatcher_password = os.getenv("PHI_DPS_DISPATCHER_PASSWORD", "dispatcher")

    engineer_email = os.getenv("PHI_DPS_ENGINEER_EMAIL", "engineer@example.com")
    engineer_password = os.getenv("PHI_DPS_ENGINEER_PASSWORD", "engineer")

    client_email = os.getenv("PHI_DPS_CLIENT_EMAIL", "client@example.com")
    client_password = os.getenv("PHI_DPS_CLIENT_PASSWORD", "client")

    finance_email = os.getenv("PHI_DPS_FINANCE_EMAIL", "finance@example.com")
    finance_password = os.getenv("PHI_DPS_FINANCE_PASSWORD", "finance")

    commercial_email = os.getenv("PHI_DPS_COMMERCIAL_EMAIL", "commercial@example.com")
    commercial_password = os.getenv("PHI_DPS_COMMERCIAL_PASSWORD", "commercial")

    ops_manager_email = os.getenv("PHI_DPS_OPS_MANAGER_EMAIL", "ops.manager@example.com")
    ops_manager_password = os.getenv("PHI_DPS_OPS_MANAGER_PASSWORD", "opsmanager")

    def upsert_user(email: str, password: str, role_name: str) -> None:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            # Keep existing; don't change password/roles automatically.
            return
        role = db.query(Role).filter(Role.name == role_name).one()
        user = User(
            email=email,
            hashed_password=hash_password(password),
            roles=[role],
        )
        db.add(user)
        db.commit()

    upsert_user(admin_email, admin_password, "Admin")
    upsert_user(dispatcher_email, dispatcher_password, "Dispatcher")
    upsert_user(engineer_email, engineer_password, "Engineer")
    upsert_user(client_email, client_password, "Client")
    upsert_user(finance_email, finance_password, "Finance")
    upsert_user(commercial_email, commercial_password, "Commercial")
    upsert_user(ops_manager_email, ops_manager_password, "Ops_Manager")

