"""Finance RBAC, approvals workflow, and sensitive-flow hardening."""
from __future__ import annotations

import uuid

import pytest


def _tok(client, email: str, password: str) -> str:
    r = client.post("/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


def _ensure_customer_id(client, admin_t: str) -> str:
    lead = client.post(
        "/crm/leads",
        headers=_h(admin_t),
        json={"name": f"L {uuid.uuid4().hex[:6]}", "email": f"rbac_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201, lead.text
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_h(admin_t),
        json={"name": "RBAC Customer", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200, conv.text
    return conv.json()["customer"]["id"]


@pytest.fixture(autouse=True)
def _clear_approvals():
    from backend.app.db.session import SessionLocal
    from backend.app.modules.approvals.models import ApprovalAuditLog, ApprovalRequest

    db = SessionLocal()
    try:
        db.query(ApprovalAuditLog).delete()
        db.query(ApprovalRequest).delete()
        db.commit()
    finally:
        db.close()
    yield


def _job_complete_invoice(client, admin_t: str, customer_id: str) -> tuple[str, str]:
    job_r = client.post(
        "/jobs",
        headers=_h(admin_t),
        json={"customer_id": customer_id, "address": "RBAC finance job"},
    )
    assert job_r.status_code == 201, job_r.text
    job_id = job_r.json()["id"]
    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
    finally:
        db.close()
    client.post(
        "/compliance/certificates/generate",
        headers=_h(admin_t),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    inv_r = client.post("/invoicing/invoices/generate", headers=_h(admin_t), json={"job_id": job_id})
    assert inv_r.status_code == 201, inv_r.text
    return job_id, inv_r.json()["id"]


def test_dispatcher_cannot_hold_invoice_without_finance_permission(client):
    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)
    r = client.post(
        f"/invoicing/invoices/{inv_id}/hold",
        headers=_h(disp),
        json={"note": "Should fail"},
    )
    assert r.status_code == 403


def test_finance_user_can_hold_invoice_directly(client):
    fin = _tok(client, "finance@example.com", "finance")
    admin = _tok(client, "admin@example.com", "admin")
    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)
    r = client.post(
        f"/invoicing/invoices/{inv_id}/hold",
        headers=_h(fin),
        json={"note": "Finance hold"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "held"


def test_user_without_hold_permission_can_create_approval_request(client):
    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)
    r = client.post(
        "/approvals",
        headers=_h(disp),
        json={
            "approval_type": "invoice_hold",
            "target_entity_type": "invoice",
            "target_entity_id": inv_id,
            "reason": "Need finance sign-off to hold this invoice",
            "payload_json": {"invoice_id": inv_id, "hold_note": "Via approval"},
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"


def test_approval_approve_records_decider_and_holds_invoice(client):
    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    fin = _tok(client, "finance@example.com", "finance")
    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)
    cr = client.post(
        "/approvals",
        headers=_h(disp),
        json={
            "approval_type": "invoice_hold",
            "target_entity_type": "invoice",
            "target_entity_id": inv_id,
            "reason": "Hold please",
            "payload_json": {"invoice_id": inv_id, "hold_note": "Approved path"},
        },
    )
    aid = cr.json()["id"]
    ap = client.post(f"/approvals/{aid}/approve", headers=_h(fin), json={})
    assert ap.status_code == 200, ap.text
    body = ap.json()
    assert body["status"] == "approved"
    assert body["decided_by_user_id"]
    inv = client.get("/invoicing/invoices", headers=_h(admin)).json()
    row = next(x for x in inv if x["id"] == inv_id)
    assert row["status"] == "held"


def test_rejected_approval_does_not_execute_hold(client):
    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    fin = _tok(client, "finance@example.com", "finance")
    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)
    cr = client.post(
        "/approvals",
        headers=_h(disp),
        json={
            "approval_type": "invoice_hold",
            "target_entity_type": "invoice",
            "target_entity_id": inv_id,
            "reason": "Reject me",
            "payload_json": {"invoice_id": inv_id},
        },
    )
    aid = cr.json()["id"]
    rj = client.post(f"/approvals/{aid}/reject", headers=_h(fin), json={"decision_notes": "no"})
    assert rj.status_code == 200, rj.text
    assert rj.json()["status"] == "rejected"
    inv = client.get("/invoicing/invoices", headers=_h(admin)).json()
    row = next(x for x in inv if x["id"] == inv_id)
    assert row["status"] == "unpaid"


def test_recommendation_preview_shows_approval_required_for_hold_invoice(client):
    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation

    cid = _ensure_customer_id(client, admin)
    _job, inv_id = _job_complete_invoice(client, admin, cid)

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="invoice_release_hold",
                category="invoice_hold",
                severity="medium",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="invoice",
                entity_id=inv_id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
                related_job_id=None,
                related_contract_id=None,
                related_invoice_id=inv_id,
            )
        )
        db.commit()
    finally:
        db.close()
    client.get(f"/ops/recommendations/{rid}/actions", headers=_h(admin))
    pr = client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_h(disp),
        json={"action_type": "hold_invoice", "input_payload": {}},
    )
    assert pr.status_code == 200, pr.text
    auth = pr.json()["preview"].get("authorization") or {}
    assert auth.get("required_permission") == "can_hold_invoice"
    assert auth.get("direct_execute_allowed") is False
    assert auth.get("approval_request_allowed") is True


def test_critical_vehicle_defect_resolve_requires_override_permission(client):
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.vehicles.models import VehicleDefect

    vid = f"v-test-{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        eng_email = f"eng-veh-{uuid.uuid4().hex[:6]}@example.com"
        eng = User(email=eng_email, hashed_password=hash_password("e"), roles=[role])
        db.add(eng)
        db.commit()
        db.refresh(eng)
        did = str(uuid.uuid4())
        db.add(
            VehicleDefect(
                id=did,
                vehicle_id=vid,
                inspection_id=None,
                defect_type="brake",
                severity="critical",
                title="Brake fault",
                description=None,
                status="open",
                reported_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                reported_by_user_id=eng.id,
            )
        )
        db.commit()
    finally:
        db.close()

    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    ops = _tok(client, "ops.manager@example.com", "opsmanager")
    r403 = client.post(
        f"/vehicles/{vid}/defects/{did}/resolve",
        headers=_h(disp),
        json={"resolution_notes": "fixed"},
    )
    assert r403.status_code == 403
    r200 = client.post(
        f"/vehicles/{vid}/defects/{did}/resolve",
        headers=_h(ops),
        json={
            "resolution_notes": "Workshop replaced brake components and cleared the fault; vehicle released per H&S sign-off.",
        },
    )
    assert r200.status_code == 200, r200.text


def test_repricing_approve_requires_commercial_or_finance_boundary(client):
    from datetime import datetime, timezone

    admin = _tok(client, "admin@example.com", "admin")
    disp = _tok(client, "dispatcher@example.com", "dispatcher")
    comm = _tok(client, "commercial@example.com", "commercial")

    lead = client.post(
        "/crm/leads",
        headers=_h(admin),
        json={"name": f"L {uuid.uuid4().hex[:6]}", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_h(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_h(admin),
        json={
            "customer_id": cid,
            "name": f"RBAC repricing {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
        },
    )
    assert ctr.status_code == 201, ctr.text
    contract_id = ctr.json()["id"]

    cr = client.post(
        f"/contracts/{contract_id}/repricing-review",
        headers=_h(admin),
        json={
            "current_contract_value": 1000.0,
            "proposed_contract_value": 1100.0,
            "repricing_reason_codes": ["test"],
            "customer_risk_level": "medium",
            "notes": "n",
        },
    )
    assert cr.status_code == 201, cr.text

    bad = client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_h(disp),
        json={"approved": True, "notes": "dispatcher try"},
    )
    assert bad.status_code == 403

    ok = client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_h(comm),
        json={"approved": True, "notes": "commercial ok"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json().get("approved") is True
