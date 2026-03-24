"""
Contract-scoped customer communications: drafts, approval-safe send, dashboards, RBAC, audit.
"""
from __future__ import annotations

import pytest

from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.review_models import ContractCommercialActionLog
from backend.tests.test_contract_activation_confirmation_workflow import _activate_amendment
from backend.tests.test_contract_amendment_activation import (
    _admin_token,
    _auth,
    _login,
    _proposal_ready_for_customer_release,
)


@pytest.fixture(autouse=True)
def _clear_customer_communications():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ContractCustomerCommunication).delete()
        db.commit()
    finally:
        db.close()
    yield


def _comms_for_proposal(client, admin: str, proposal_id: str) -> list[dict]:
    r = client.get(
        "/contracts/communications",
        headers=_auth(admin),
        params={"source_entity_type": "repricing_proposal", "source_entity_id": proposal_id},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_1_proposal_release_creates_contract_scoped_communication_draft(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text

    rows = _comms_for_proposal(client, admin, proposal_id)
    assert len(rows) >= 1
    assert any(r["communication_type"] == "repricing_proposal_released" for r in rows)
    hit = next(r for r in rows if r["communication_type"] == "repricing_proposal_released")
    assert hit["contract_id"] == contract_id
    assert hit["status"] == "draft"
    assert hit["source_proposal_id"] == proposal_id


def test_2_activation_confirmation_release_creates_communication_draft(client):
    admin = _admin_token(client)
    contract_id, _pid, amend_id, _email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    assert c.status_code == 201
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    r = client.get(
        "/contracts/communications",
        headers=_auth(admin),
        params={"source_entity_type": "activation_confirmation", "source_entity_id": conf_id},
    )
    assert r.status_code == 200
    rows = r.json()
    assert any(x["communication_type"] == "activation_confirmation_released" for x in rows)
    hit = next(x for x in rows if x["communication_type"] == "activation_confirmation_released")
    assert hit["contract_id"] == contract_id
    assert hit["source_activation_confirmation_id"] == conf_id


def test_3_draft_mark_ready_and_sent(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    rows = _comms_for_proposal(client, admin, proposal_id)
    cid = next(r["id"] for r in rows if r["communication_type"] == "repricing_proposal_released")
    assert client.post(f"/contracts/communications/{cid}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{cid}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "sent"
    assert s.json()["sent_at"]


def test_4_approval_required_cannot_send_before_approve(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    rem = client.post(
        f"/contracts/communications/drafts/repricing-proposals/{proposal_id}/reminder",
        headers=_auth(admin),
    )
    assert rem.status_code == 201, rem.text
    assert rem.json()["requires_approval"] is True
    rid = rem.json()["id"]
    assert client.post(f"/contracts/communications/{rid}/mark-ready", headers=_auth(admin)).status_code == 200
    bad = client.post(f"/contracts/communications/{rid}/send", headers=_auth(admin))
    assert bad.status_code == 400
    fin = _login(client, username="finance@example.com", password="finance")
    ap = client.post(f"/contracts/communications/{rid}/approve", headers=_auth(fin))
    assert ap.status_code == 200, ap.text
    ok = client.post(f"/contracts/communications/{rid}/send", headers=_auth(admin))
    assert ok.status_code == 200, ok.text


def test_5_cancelled_communication_not_sendable(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    rows = _comms_for_proposal(client, admin, proposal_id)
    cid = next(r["id"] for r in rows if r["communication_type"] == "repricing_proposal_released")
    client.post(f"/contracts/communications/{cid}/mark-ready", headers=_auth(admin))
    assert (
        client.post(
            f"/contracts/communications/{cid}/cancel",
            headers=_auth(admin),
            json={"reason": "test"},
        ).status_code
        == 200
    )
    assert client.post(f"/contracts/communications/{cid}/send", headers=_auth(admin)).status_code == 400


def test_6_dashboards_reflect_states(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    dash = client.get("/contracts/dashboard/customer-communications", headers=_auth(admin))
    assert dash.status_code == 200
    assert dash.json()["by_status"]["draft"] >= 1

    fu = client.get("/contracts/dashboard/customer-communications-follow-up", headers=_auth(admin))
    assert fu.status_code == 200
    assert "repricing_proposal_reminder_candidates" in fu.json()


def test_7_communication_content_has_proposal_context(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    pr0 = client.get(f"/contracts/repricing-proposals/{proposal_id}", headers=_auth(admin))
    assert pr0.status_code == 200, pr0.text
    pref = pr0.json()["proposal_reference"]
    pr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert pr.status_code == 200, pr.text
    rows = _comms_for_proposal(client, admin, proposal_id)
    body = next(r for r in rows if r["communication_type"] == "repricing_proposal_released")["body_text"]
    assert pref in (body or "")


def test_8_dedupe_open_reminder_drafts(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    a = client.post(
        f"/contracts/communications/drafts/repricing-proposals/{proposal_id}/reminder",
        headers=_auth(admin),
    )
    b = client.post(
        f"/contracts/communications/drafts/repricing-proposals/{proposal_id}/reminder",
        headers=_auth(admin),
    )
    assert a.status_code == 201 and b.status_code == 201
    assert a.json()["id"] == b.json()["id"]


def test_9_commercial_log_records_communication_lifecycle(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    rows = _comms_for_proposal(client, admin, proposal_id)
    cid = next(r["id"] for r in rows if r["communication_type"] == "repricing_proposal_released")
    client.post(f"/contracts/communications/{cid}/mark-ready", headers=_auth(admin))
    client.post(f"/contracts/communications/{cid}/send", headers=_auth(admin))

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rows = (
            db.query(ContractCommercialActionLog)
            .filter(ContractCommercialActionLog.contract_id == contract_id)
            .all()
        )
        types = {r.action_type for r in rows}
        assert "contract_customer_communication_created" in types
        assert "contract_customer_communication_ready" in types
        assert "contract_customer_communication_sent" in types
    finally:
        db.close()


def test_10_engineer_cannot_access_communications_api(client):
    admin = _admin_token(client)
    eng = _login(client, username="engineer@example.com", password="engineer")
    r = client.get("/contracts/communications", headers=_auth(eng))
    assert r.status_code == 403
