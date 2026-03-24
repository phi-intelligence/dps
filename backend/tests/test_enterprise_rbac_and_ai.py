"""
Enterprise RBAC: per-user grants, effective resolution, admin APIs, AI config wiring (no secrets exposed).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.core.config import Settings
from backend.app.modules.auth.permission_models import PermissionGrantAuditLog, UserPermissionGrant
from backend.app.services import ai_provider_service as ai_svc
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz
from backend.app.services.permission_grant_service import create_grant


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _clear_grants_and_audit():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(PermissionGrantAuditLog).delete()
        db.query(UserPermissionGrant).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_role_baseline_when_no_grant(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "finance@example.com").one()
        assert authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
    finally:
        db.close()


def test_user_deny_overrides_role_allow(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "admin@example.com").one()
        assert authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
        create_grant(
            db,
            target_user_id=u.id,
            permission_key=policy.CAN_HOLD_INVOICE,
            effect="deny",
            actor_user_id=u.id,
            notes="test deny",
            commit=True,
        )
        assert not authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
    finally:
        db.close()


def test_commercial_user_can_create_po_when_granted(client):
    """Integration: permission-only gate on create PO + user-level allow grant."""
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    admin_tok = _login(client, username="admin@example.com", password="admin")
    com_tok = _login(client, username="commercial@example.com", password="commercial")

    sku = f"RBAC-SKU-{uuid.uuid4().hex[:6]}"
    stock = client.post(
        "/inventory/items",
        headers=_auth(admin_tok),
        json={
            "sku": sku,
            "name": "RBAC part",
            "unit_of_measure": "ea",
            "unit_cost": 1.0,
            "on_hand_quantity": 10.0,
            "reorder_point_quantity": 1.0,
        },
    )
    assert stock.status_code == 201, stock.text

    db = SessionLocal()
    try:
        com = db.query(User).filter(User.email == "commercial@example.com").one()
        adm = db.query(User).filter(User.email == "admin@example.com").one()
        create_grant(
            db,
            target_user_id=com.id,
            permission_key=policy.CAN_CREATE_PURCHASE_ORDER,
            effect="allow",
            actor_user_id=adm.id,
            commit=True,
        )
    finally:
        db.close()

    po = client.post(
        "/inventory/purchase-orders",
        headers=_auth(com_tok),
        json={"supplier_name": "ACME", "lines": [{"sku": sku, "quantity": 1.0, "unit_cost": 1.0}]},
    )
    assert po.status_code == 201, po.text


def test_user_allow_grants_not_in_role(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "commercial@example.com").one()
        assert policy.CAN_CREATE_PURCHASE_ORDER not in authz.role_permissions_for_user(u)
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        create_grant(
            db,
            target_user_id=u.id,
            permission_key=policy.CAN_CREATE_PURCHASE_ORDER,
            effect="allow",
            actor_user_id=admin.id,
            commit=True,
        )
        assert authz.user_has_permission(u, policy.CAN_CREATE_PURCHASE_ORDER, db=db)
    finally:
        db.close()


def test_expired_grant_ignored(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "engineer@example.com").one()
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        past = datetime.now(timezone.utc) - timedelta(days=1)
        create_grant(
            db,
            target_user_id=u.id,
            permission_key=policy.CAN_HOLD_INVOICE,
            effect="allow",
            actor_user_id=admin.id,
            expires_at=past,
            commit=True,
        )
        assert not authz.user_has_permission(u, policy.CAN_HOLD_INVOICE, db=db)
    finally:
        db.close()


def test_admin_permission_endpoints_restricted(client):
    admin_tok = _login(client, username="admin@example.com", password="admin")
    disp_tok = _login(client, username="dispatcher@example.com", password="dispatcher")

    ok = client.get("/admin/permissions/catalog", headers=_auth(admin_tok))
    assert ok.status_code == 200

    bad = client.get("/admin/permissions/catalog", headers=_auth(disp_tok))
    assert bad.status_code == 403


def test_sensitive_route_respects_deny_grant(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    admin_tok = _login(client, username="admin@example.com", password="admin")
    fin_tok = _login(client, username="finance@example.com", password="finance")

    db = SessionLocal()
    try:
        fin = db.query(User).filter(User.email == "finance@example.com").one()
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        create_grant(
            db,
            target_user_id=fin.id,
            permission_key=policy.CAN_HOLD_INVOICE,
            effect="deny",
            actor_user_id=admin.id,
            notes="revoke hold for test",
            commit=True,
        )
    finally:
        db.close()

    # Create job+invoice via API for valid hold target
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin_tok),
        json={"name": "L", "email": f"rbac_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin_tok),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    job_res = client.post("/jobs", headers=_auth(admin_tok), json={"customer_id": cid, "address": "1 St"})
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]
    from backend.app.db.session import SessionLocal
    from backend.app.modules.invoicing.models import Invoice

    dbi = SessionLocal()
    try:
        dbi.add(
            Invoice(
                job_id=job_id,
                currency="GBP",
                status="unpaid",
                labour_total=0.0,
                materials_total=0.0,
                grand_total=0.0,
            )
        )
        dbi.commit()
        invoice_id = dbi.query(Invoice).filter(Invoice.job_id == job_id).one().id
    finally:
        dbi.close()

    hold = client.post(
        f"/invoicing/invoices/{invoice_id}/hold",
        headers=_auth(fin_tok),
        json={"note": "t"},
    )
    assert hold.status_code == 403


def test_gemini_status_never_exposes_secret(client, monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://example.invalid")

    admin_tok = _login(client, username="admin@example.com", password="admin")
    res = client.get("/admin/ai/status", headers=_auth(admin_tok))
    assert res.status_code == 200
    body = res.json()
    assert body["api_key_configured"] is True
    assert body["enabled"] is True
    dumped = json.dumps(body)
    assert "super-secret" not in dumped


def test_ai_provider_service_enabled_flag(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_ENABLED", "0")
    s = Settings()
    svc = ai_svc.AIProviderService(s)
    assert svc.is_enabled() is False

    monkeypatch.setenv("GEMINI_ENABLED", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    s2 = Settings()
    svc2 = ai_svc.AIProviderService(s2)
    assert svc2.is_enabled() is True
    assert svc2.build_client() is None
