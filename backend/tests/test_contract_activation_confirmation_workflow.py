"""
Customer activation confirmation workflow: internal activation vs portal release, PDF, audit, dashboards.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.review_models import ContractCommercialActionLog
from backend.app.modules.documents.models import StoredDocument
from backend.tests.test_contract_amendment_activation import (
    _accepted_proposal,
    _admin_token,
    _auth,
    _ensure_client_user,
    _login,
)


@pytest.fixture(autouse=True)
def _clear_activation_confirmation_tables():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ContractActivationConfirmation).delete()
        db.query(StoredDocument).filter(StoredDocument.document_type == "contract_activation_confirmation").delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()
    yield


def _activate_amendment(client, admin: str) -> tuple[str, str, str, str]:
    """contract_id, proposal_id, amendment_id, customer_email"""
    contract_id, proposal_id, email = _accepted_proposal(client, admin)
    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert create.status_code == 201, create.text
    amend_id = create.json()["id"]
    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    act = client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))
    assert act.status_code == 200, act.text
    return contract_id, proposal_id, amend_id, email


def test_1_activated_amendment_can_create_activation_confirmation_record(client):
    admin = _admin_token(client)
    contract_id, _proposal_id, amend_id, _email = _activate_amendment(client, admin)

    r = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["contract_id"] == contract_id
    assert body["amendment_id"] == amend_id
    assert body["status"] == "pending_generation"
    assert body["confirmation_reference"].startswith("CAC-")


def test_2_confirmation_pdf_persisted_as_stored_document(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, _email = _activate_amendment(client, admin)

    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    g = client.post(
        f"/contracts/activation-confirmations/{conf_id}/generate-pdf",
        headers=_auth(admin),
    )
    assert g.status_code == 200, g.text
    assert g.json()["status"] == "generated"
    assert g.json()["stored_document_id"]

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        doc = db.get(StoredDocument, g.json()["stored_document_id"])
        assert doc is not None
        assert doc.document_type == "contract_activation_confirmation"
        assert doc.visibility_scope == "internal_only"
    finally:
        db.close()


def test_3_unreleased_confirmation_not_visible_in_portal(client):
    admin = _admin_token(client)
    contract_id, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))

    ctok = _login(client, username=email, password="am-test")
    lst = client.get(
        f"/portal/me/contracts/{contract_id}/activation-confirmations",
        headers=_auth(ctok),
    )
    assert lst.status_code == 200
    assert lst.json() == []

    one = client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok))
    assert one.status_code == 404


def test_4_released_confirmation_only_for_authorized_customer(client):
    admin = _admin_token(client)
    contract_id, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )

    other_email = f"other_{uuid.uuid4().hex[:10]}@example.com"
    _ensure_client_user(other_email, "pw")
    other_tok = _login(client, username=other_email, password="pw")
    bad = client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(other_tok))
    assert bad.status_code == 404

    ctok = _login(client, username=email, password="am-test")
    ok = client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok))
    assert ok.status_code == 200
    assert ok.json()["confirmation_reference"]


def test_5_portal_view_marks_viewed_once_in_logs(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password="am-test")

    def viewed_log_count() -> int:
        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        try:
            rows = db.query(ContractCommercialActionLog).all()
            n = 0
            for r in rows:
                if r.action_type != "activation_confirmation_viewed":
                    continue
                p = json.loads(r.payload_json or "{}")
                if p.get("activation_confirmation_id") == conf_id:
                    n += 1
            return n
        finally:
            db.close()

    assert viewed_log_count() == 0
    client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok))
    assert viewed_log_count() == 1
    client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok))
    assert viewed_log_count() == 1


def test_6_customer_acknowledgement_updates_state(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password="am-test")
    client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok))

    ack = client.post(
        f"/portal/me/activation-confirmations/{conf_id}/acknowledge",
        headers=_auth(ctok),
        json={"acknowledged_by_contact": "Jane Doe", "notes": "Confirmed"},
    )
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "acknowledged"
    assert ack.json()["customer_acknowledged_at"]


def test_7_release_withdraw_updates_visibility(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password="am-test")
    assert client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok)).status_code == 200

    w = client.post(
        f"/contracts/activation-confirmations/{conf_id}/withdraw-customer-release",
        headers=_auth(admin),
        json={"reason": "typo"},
    )
    assert w.status_code == 200, w.text
    assert w.json()["status"] == "withdrawn"

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        doc = db.get(StoredDocument, w.json()["stored_document_id"])
        assert doc.visibility_scope == "internal_only"
    finally:
        db.close()

    assert client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok)).status_code == 404


def test_8_dashboard_reflects_states(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, _email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))

    dash = client.get("/contracts/dashboard/activation-confirmations", headers=_auth(admin))
    assert dash.status_code == 200
    by_status = dash.json()["by_status"]
    assert by_status.get("generated", 0) >= 1

    awaiting = client.get(
        "/contracts/dashboard/activations-awaiting-customer-confirmation",
        headers=_auth(admin),
    )
    assert awaiting.status_code == 200
    assert awaiting.json()["count"] >= 1

    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    fu = client.get(
        "/contracts/dashboard/activation-confirmations-follow-up",
        headers=_auth(admin),
    )
    assert fu.status_code == 200
    assert conf_id in fu.json()["released_not_viewed"]


def test_9_portal_payload_excludes_internal_only_commercial_fields(client):
    admin = _admin_token(client)
    _cid, _pid, amend_id, email = _activate_amendment(client, admin)
    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    conf_id = c.json()["id"]
    client.post(f"/contracts/activation-confirmations/{conf_id}/generate-pdf", headers=_auth(admin))
    client.post(
        f"/contracts/activation-confirmations/{conf_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password="am-test")
    body = client.get(f"/portal/me/activation-confirmations/{conf_id}", headers=_auth(ctok)).json()
    assert "repricing_required" not in body
    assert "account_attention_level" not in body
    assert "notes" not in body
    for k in body.get("summary", {}):
        assert k in {
            "headline",
            "body_lines",
            "amendment_reference",
            "amendment_type",
            "prior_contract_value",
            "new_contract_value",
            "effective_date",
        }


def test_10_confirmation_links_amendment_version_proposal_chain(client):
    admin = _admin_token(client)
    contract_id, proposal_id, amend_id, _email = _activate_amendment(client, admin)
    amend_out = client.get(f"/contracts/amendments/{amend_id}", headers=_auth(admin))
    assert amend_out.status_code == 200
    version_id = amend_out.json().get("resulting_contract_version_id")
    assert version_id

    c = client.post(
        f"/contracts/amendments/{amend_id}/activation-confirmation",
        headers=_auth(admin),
    )
    assert c.status_code == 201
    body = c.json()
    assert body["amendment_id"] == amend_id
    assert body["contract_version_id"] == version_id
    assert body["source_proposal_id"] == proposal_id
    assert body["contract_id"] == contract_id


def test_11_auto_create_activation_confirmation_when_env_enabled(client, monkeypatch):
    monkeypatch.setenv("PHI_DPS_AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE", "1")
    admin = _admin_token(client)
    _cid, _pid, amend_id, _email = _activate_amendment(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.services.contract_activation_confirmation_service import get_active_confirmation_for_amendment

    db = SessionLocal()
    try:
        row = get_active_confirmation_for_amendment(db, amendment_id=amend_id)
        assert row is not None
        assert row.status == "pending_generation"
    finally:
        db.close()
