"""
Enterprise org hierarchy: internal groups, group grants, entity scopes, customer portal groups.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.auth.models import Role, User
from backend.app.modules.auth.permission_models import UserPermissionGrant
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
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz
from backend.app.services import org_access_service as oas
from backend.app.services import portal_customer_scope_service as pcscope
from backend.app.services import scoped_access_service as scoped
from backend.app.services.permission_grant_service import create_grant


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def _ensure_org_tables_exist():
    """Fresh test.db may predate new models; ensure tables and dev users exist."""
    from backend.app.db.base import Base
    from backend.app.db.session import SessionLocal, engine
    from backend.app.db.sqlite_migrations import migrate_sqlite_schema
    from backend.app.modules.auth.service import ensure_default_admin

    import backend.app.main  # noqa: F401, registers models on Base.metadata

    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _clear_org_access():
    from sqlalchemy import inspect

    from backend.app.db.session import SessionLocal, engine

    insp = inspect(engine)
    db = SessionLocal()
    try:
        if not insp.has_table("internal_access_groups"):
            db.close()
            yield
            return
        db.query(OrgAccessAuditLog).delete()
        db.query(CustomerGroupEntityAccess).delete()
        db.query(CustomerAccessGroupMembership).delete()
        db.query(CustomerAccessGroup).delete()
        db.query(GroupEntityAccess).delete()
        db.query(GroupPermissionGrant).delete()
        db.query(InternalAccessGroupMembership).delete()
        db.query(InternalAccessGroup).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_user_inherits_permission_from_group_allow():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        assert not authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
        g = oas.create_internal_group(
            db,
            name="Ops automation",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="ops_team",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=eng.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_grant(
            db,
            group_id=g.id,
            permission_key=policy.CAN_RUN_OPS_AUTOMATION,
            effect="allow",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        eng = db.get(User, eng.id)
        assert authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
    finally:
        db.close()


def test_user_level_deny_overrides_group_allow():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    eng_id: str | None = None
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        eng_id = eng.id
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        g = oas.create_internal_group(
            db,
            name="G",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=eng.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_grant(
            db,
            group_id=g.id,
            permission_key=policy.CAN_RUN_OPS_AUTOMATION,
            effect="allow",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        create_grant(
            db,
            target_user_id=eng.id,
            permission_key=policy.CAN_RUN_OPS_AUTOMATION,
            effect="deny",
            actor_user_id=admin.id,
            notes="test",
            commit=True,
        )
        assert not authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
    finally:
        if eng_id:
            db.query(UserPermissionGrant).filter(UserPermissionGrant.user_id == eng_id).delete()
            db.commit()
        db.close()


def test_group_deny_overrides_role_allow_without_user_override():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        disp = db.query(User).filter(User.email == "dispatcher@example.com").one()
        assert authz.user_has_permission(disp, policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION, db=db)
        g = oas.create_internal_group(
            db,
            name="Lockdown",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=disp.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_grant(
            db,
            group_id=g.id,
            permission_key=policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION,
            effect="deny",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        assert not authz.user_has_permission(disp, policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION, db=db)
    finally:
        db.close()


def test_scoped_access_allows_one_contract_not_another():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        disp = db.query(User).filter(User.email == "dispatcher@example.com").one()
        cust = Customer(id=str(uuid.uuid4()), name="C", email=f"c_{uuid.uuid4().hex[:6]}@t.com")
        db.add(cust)
        db.flush()
        now = datetime.now(timezone.utc)
        ca = Contract(
            id=str(uuid.uuid4()),
            customer_id=cust.id,
            name="A",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="ppm_only",
            term_start_at=now,
            next_ppm_due_at=now,
            contract_value=1.0,
            ppm_interval_days=365,
        )
        cb = Contract(
            id=str(uuid.uuid4()),
            customer_id=cust.id,
            name="B",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="ppm_only",
            term_start_at=now,
            next_ppm_due_at=now,
            contract_value=2.0,
            ppm_interval_days=365,
        )
        db.add_all([ca, cb])
        db.commit()

        g = oas.create_internal_group(
            db,
            name="Regional",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="commercial_team",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=disp.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_scope(
            db,
            group_id=g.id,
            entity_type="contract",
            entity_id=ca.id,
            access_scope="view",
            notes=None,
            actor_user_id=None,
            commit=True,
        )
        assert scoped.user_can_access_internal_entity(
            db, disp, entity_type="contract", entity_id=ca.id, required_scope="view"
        )
        assert not scoped.user_can_access_internal_entity(
            db, disp, entity_type="contract", entity_id=cb.id, required_scope="view"
        )
    finally:
        db.close()


def test_customer_group_scoped_proposal_access():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        cust = Customer(id=str(uuid.uuid4()), name="C2", email="portal_scope@test.com")
        db.add(cust)
        db.commit()
        cg = oas.create_customer_group(
            db,
            customer_id=cust.id,
            name="Billing",
            group_type="billing_contacts",
            notes=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_customer_group_member(
            db,
            customer_access_group_id=cg.id,
            portal_login_email="portal_scope@test.com",
            member_contact_scope="billing",
            notes=None,
            actor_user_id=None,
            commit=True,
        )
        oas.create_customer_group_scope(
            db,
            customer_access_group_id=cg.id,
            entity_type="proposal",
            entity_id="prop-only-1",
            access_scope="view",
            notes=None,
            actor_user_id=None,
            commit=True,
        )
        assert pcscope.customer_portal_proposal_allowed(
            db,
            customer=cust,
            portal_login_email="portal_scope@test.com",
            proposal_id="prop-only-1",
            contract_id="any-contract",
        )
        assert not pcscope.customer_portal_proposal_allowed(
            db,
            customer=cust,
            portal_login_email="portal_scope@test.com",
            proposal_id="other-prop",
            contract_id="any-contract",
        )
    finally:
        db.close()


def test_admin_org_apis_require_org_permission(client):
    fin = _login(client, username="finance@example.com", password="finance")
    r = client.get("/admin/access-groups", headers=_auth(fin))
    assert r.status_code == 403


def test_permission_sources_include_group_grants():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        g = oas.create_internal_group(
            db,
            name="Src",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=eng.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_grant(
            db,
            group_id=g.id,
            permission_key=policy.CAN_RUN_OPS_AUTOMATION,
            effect="allow",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        eng = db.get(User, eng.id)
        assert authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
        src = authz.list_user_permission_sources(db, eng)
        entry = next(x for x in src if x["permission_key"] == policy.CAN_RUN_OPS_AUTOMATION)
        assert entry["effective"] is True
        assert any(s.get("source") == "group_grant" for s in entry.get("sources", []))
    finally:
        db.close()


def test_backward_compatible_when_no_groups():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        assert not authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
        disp = db.query(User).filter(User.email == "dispatcher@example.com").one()
        assert authz.user_has_permission(disp, policy.CAN_TRIGGER_CUSTOMER_NOTIFICATION, db=db)
    finally:
        db.close()


def test_multi_role_union_respects_group_deny():
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rf = db.query(Role).filter(Role.name == "Finance").one()
        rc = db.query(Role).filter(Role.name == "Commercial").one()
        em = f"multi_{uuid.uuid4().hex[:8]}@test.com"
        u = User(id=str(uuid.uuid4()), email=em, hashed_password=hash_password("x"), roles=[rf, rc])
        db.add(u)
        db.commit()
        db.refresh(u)
        assert authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
        assert authz.user_has_permission(u, policy.CAN_DECIDE_CONTRACT_REVIEW, db=db)
        g = oas.create_internal_group(
            db,
            name="Deny hold",
            code=f"t_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=g.id, user_id=u.id, notes=None, actor_user_id=None, commit=True)
        oas.create_group_grant(
            db,
            group_id=g.id,
            permission_key=policy.CAN_HOLD_INVOICE,
            effect="deny",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        assert not authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
        assert authz.user_has_permission(u, policy.CAN_DECIDE_CONTRACT_REVIEW, db=db)
    finally:
        db.close()


def test_internal_nested_group_inherits_parent_grant():
    """§5.13 — child group members receive parent group permission grants when inheritance is on."""
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        assert not authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
        parent = oas.create_internal_group(
            db,
            name="Parent org",
            code=f"t_p_{uuid.uuid4().hex[:8]}",
            group_type="ops",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        oas.create_group_grant(
            db,
            group_id=parent.id,
            permission_key=policy.CAN_RUN_OPS_AUTOMATION,
            effect="allow",
            notes=None,
            expires_at=None,
            actor_user_id=None,
            commit=True,
        )
        child = oas.create_internal_group(
            db,
            name="Child team",
            code=f"t_c_{uuid.uuid4().hex[:8]}",
            group_type="ops",
            description=None,
            parent_group_id=parent.id,
            inherit_parent_grants=True,
            actor_user_id=None,
            commit=True,
        )
        oas.add_internal_member(db, group_id=child.id, user_id=eng.id, notes=None, actor_user_id=None, commit=True)
        eng = db.get(User, eng.id)
        assert authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)

        oas.patch_internal_group(
            db,
            group_id=child.id,
            name=None,
            active=None,
            description=None,
            inherit_parent_grants=False,
            actor_user_id=None,
            commit=True,
        )
        eng = db.get(User, eng.id)
        assert not authz.user_has_permission(eng, policy.CAN_RUN_OPS_AUTOMATION, db=db)
    finally:
        db.close()


def test_internal_group_parent_cycle_rejected():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        a = oas.create_internal_group(
            db,
            name="A",
            code=f"t_a_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            actor_user_id=None,
            commit=True,
        )
        b = oas.create_internal_group(
            db,
            name="B",
            code=f"t_b_{uuid.uuid4().hex[:8]}",
            group_type="custom",
            description=None,
            parent_group_id=a.id,
            inherit_parent_grants=True,
            actor_user_id=None,
            commit=True,
        )
        with pytest.raises(ValueError, match="cycle"):
            oas.patch_internal_group(
                db,
                group_id=a.id,
                name=None,
                active=None,
                description=None,
                parent_group_id=b.id,
                actor_user_id=None,
                commit=True,
            )
    finally:
        db.close()


def test_admin_can_create_access_group_via_api(client):
    admin = _login(client, username="admin@example.com", password="admin")
    code = f"api_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/admin/access-groups",
        headers=_auth(admin),
        json={"name": "API Group", "code": code, "group_type": "custom"},
    )
    assert r.status_code == 201, r.text
    lst = client.get("/admin/access-groups", headers=_auth(admin))
    assert lst.status_code == 200
    assert any(g["code"] == code for g in lst.json())
