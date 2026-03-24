"""
Provider delivery webhooks: verification, delivery updates, suppression, preferences, dashboards.
"""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.modules.contracts.communication_provider_event_models import (
    CommunicationProviderEvent,
    CommunicationRecipientSuppression,
)
from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.crm.customer_communication_preference_models import CustomerCommunicationPreference
from backend.app.services.outbound_communication_provider import set_email_provider_override
from backend.tests.test_contract_amendment_activation import (
    _admin_token,
    _auth,
    _proposal_ready_for_customer_release,
)
from backend.tests.test_outbound_customer_communications import FakeEmailProvider


def _sign(body: str) -> str:
    secret = settings.COMMUNICATION_WEBHOOK_SECRET.encode("utf-8")
    return hmac.new(secret, body.encode("utf-8"), hashlib.sha256).hexdigest()


def _post_webhook(client, body: dict, *, sign: bool = True):
    raw = json.dumps(body, separators=(",", ":"))
    headers = {"Content-Type": "application/json"}
    if sign:
        headers["X-Phi-Dps-Communication-Signature"] = _sign(raw)
    return client.post("/webhooks/communications/provider", content=raw, headers=headers)


@pytest.fixture(autouse=True)
def _clear_provider_hygiene_tables():
    db = SessionLocal()
    try:
        db.query(CommunicationRecipientSuppression).delete()
        db.query(CommunicationProviderEvent).delete()
        db.query(CustomerCommunicationPreference).delete()
        # FakeEmailProvider reuses provider_message_id "pmsg-1"; clear attempts so webhooks match this test only.
        db.query(ContractCustomerCommunicationDelivery).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _teardown_provider():
    yield
    set_email_provider_override(None)


def _send_release_comm(client, admin: str) -> tuple[str, str, str]:
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text
    lst = client.get(
        "/contracts/communications",
        headers=_auth(admin),
        params={"source_entity_type": "repricing_proposal", "source_entity_id": proposal_id},
    )
    assert lst.status_code == 200
    comm_id = next(
        x["id"] for x in lst.json() if x["communication_type"] == "repricing_proposal_released"
    )
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "sent"
    return contract_id, proposal_id, comm_id


def _set_communication_status_failed(communication_id: str) -> None:
    """Harness: retry-send only accepts ``failed``; no public transition from ``sent``."""
    db = SessionLocal()
    try:
        row = db.get(ContractCustomerCommunication, communication_id)
        assert row is not None
        row.status = "failed"
        db.add(row)
        db.commit()
    finally:
        db.close()


def test_1_valid_delivered_creates_event_and_updates_delivery(client):
    admin = _admin_token(client)
    contract_id, _proposal_id, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    assert del_rows[0]["status"] == "sent"
    mid = del_rows[0]["provider_message_id"]

    body = {
        "format": "phi_generic_v1",
        "provider_name": "fake",
        "event_type": "delivered",
        "provider_message_id": mid,
        "recipient": del_rows[0]["recipient_address"],
    }
    r = _post_webhook(client, body)
    assert r.status_code == 200, r.text
    assert r.json()["processing_status"] == "processed"

    del2 = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    assert del2[0]["status"] == "delivered"

    ev = client.get(f"/contracts/communications/{comm_id}/provider-events", headers=_auth(admin))
    assert ev.status_code == 200
    assert len(ev.json()) == 1

    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    types = {x["action_type"] for x in logs.json()}
    assert "communication_delivered" in types


def test_2_bounce_updates_delivery_and_suppresses_recipient(client):
    admin = _admin_token(client)
    _contract_id, _proposal_id, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    mid = del_rows[0]["provider_message_id"]
    to_addr = del_rows[0]["recipient_address"]

    comm_json = client.get(f"/contracts/communications/{comm_id}", headers=_auth(admin)).json()
    cust_id = comm_json["recipient_customer_id"]

    body = {
        "format": "phi_generic_v1",
        "provider_name": "fake",
        "event_type": "hard_bounce",
        "provider_message_id": mid,
        "recipient": to_addr,
        "detail": "550 mailbox unavailable",
    }
    r = _post_webhook(client, body)
    assert r.status_code == 200, r.json()["processing_status"] == "processed"

    del2 = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    assert del2[0]["status"] == "bounced"

    db = SessionLocal()
    try:
        sup = (
            db.query(CommunicationRecipientSuppression)
            .filter(
                CommunicationRecipientSuppression.customer_id == cust_id,
                CommunicationRecipientSuppression.kind == "hard_bounce",
            )
            .one()
        )
        assert sup.active is True
    finally:
        db.close()


def test_3_unsubscribe_disables_preference(client):
    admin = _admin_token(client)
    _cid, _pid, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    mid = del_rows[0]["provider_message_id"]
    to_addr = del_rows[0]["recipient_address"]
    comm_json = client.get(f"/contracts/communications/{comm_id}", headers=_auth(admin)).json()
    cust_id = comm_json["recipient_customer_id"]

    body = {
        "format": "phi_generic_v1",
        "provider_name": "fake",
        "event_type": "unsubscribe",
        "provider_message_id": mid,
        "recipient": to_addr,
    }
    assert _post_webhook(client, body).status_code == 200

    prefs = client.get(f"/customers/{cust_id}/communication-preferences", headers=_auth(admin))
    assert prefs.status_code == 200
    rows = [p for p in prefs.json() if p.get("contact_reference") == to_addr.lower()]
    assert rows and rows[0]["enabled"] is False


def test_4_subsequent_send_blocked_for_suppressed_recipient(client):
    admin = _admin_token(client)
    _cid, _proposal_id, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    mid = del_rows[0]["provider_message_id"]
    to_addr = del_rows[0]["recipient_address"]

    assert _post_webhook(
        client,
        {
            "format": "phi_generic_v1",
            "provider_name": "fake",
            "event_type": "hard_bounce",
            "provider_message_id": mid,
            "recipient": to_addr,
        },
    ).status_code == 200

    _set_communication_status_failed(comm_id)
    rs = client.post(f"/contracts/communications/{comm_id}/retry-send", headers=_auth(admin))
    assert rs.status_code == 200, rs.text
    assert rs.json()["status"] == "failed"
    dlast = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()[-1]
    assert dlast["error_code"] == "recipient_suppressed"


def test_5_invalid_signature_no_mutation(client):
    admin = _admin_token(client)
    _send_release_comm(client, admin)
    db = SessionLocal()
    try:
        n_before = db.query(CommunicationProviderEvent).count()
    finally:
        db.close()

    raw = json.dumps(
        {
            "format": "phi_generic_v1",
            "provider_name": "fake",
            "event_type": "delivered",
            "provider_message_id": "pmsg-1",
        }
    )
    bad = client.post(
        "/webhooks/communications/provider",
        content=raw,
        headers={"X-Phi-Dps-Communication-Signature": "deadbeef", "Content-Type": "application/json"},
    )
    assert bad.status_code == 401

    db = SessionLocal()
    try:
        assert db.query(CommunicationProviderEvent).count() == n_before
    finally:
        db.close()


def test_6_unknown_message_id_stored_ignored(client):
    admin = _admin_token(client)
    _send_release_comm(client, admin)
    body = {
        "format": "phi_generic_v1",
        "provider_name": "fake",
        "event_type": "delivered",
        "provider_message_id": "no-such-provider-id",
        "recipient": "x@y.com",
    }
    r = _post_webhook(client, body)
    assert r.status_code == 200
    assert r.json()["processing_status"] == "ignored"

    db = SessionLocal()
    try:
        ev = (
            db.query(CommunicationProviderEvent)
            .filter(CommunicationProviderEvent.provider_message_id == "no-such-provider-id")
            .one()
        )
        assert ev.processing_status == "ignored"
    finally:
        db.close()


def test_7_hygiene_dashboard_surfaces_suppressions(client):
    admin = _admin_token(client)
    _contract_id, _proposal_id, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    _post_webhook(
        client,
        {
            "format": "phi_generic_v1",
            "event_type": "hard_bounce",
            "provider_message_id": del_rows[0]["provider_message_id"],
            "recipient": del_rows[0]["recipient_address"],
        },
    )
    h = client.get("/contracts/dashboard/customer-communications-hygiene", headers=_auth(admin))
    assert h.status_code == 200
    j = h.json()
    assert j["active_suppressions"]
    pe = client.get("/contracts/dashboard/customer-communications-provider-events", headers=_auth(admin))
    assert pe.status_code == 200
    assert pe.json()["count"] >= 1


def test_8_complaint_recorded_and_blocks_send(client):
    admin = _admin_token(client)
    _contract_id, _proposal_id, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    mid = del_rows[0]["provider_message_id"]
    to_addr = del_rows[0]["recipient_address"]

    assert _post_webhook(
        client,
        {
            "format": "phi_generic_v1",
            "event_type": "spam_complaint",
            "provider_message_id": mid,
            "recipient": to_addr,
        },
    ).json()["processing_status"] == "processed"

    db = SessionLocal()
    try:
        s = (
            db.query(CommunicationRecipientSuppression)
            .filter(CommunicationRecipientSuppression.kind == "spam_complaint")
            .one()
        )
        assert s.requires_manual_review is True
        d = db.get(ContractCustomerCommunicationDelivery, del_rows[0]["id"])
        assert d.status == "complained"
    finally:
        db.close()

    _set_communication_status_failed(comm_id)
    rs = client.post(f"/contracts/communications/{comm_id}/retry-send", headers=_auth(admin))
    assert rs.status_code == 200
    assert rs.json()["status"] == "failed"


def test_customer_communication_safety_endpoint(client):
    admin = _admin_token(client)
    _cid, _pid, comm_id = _send_release_comm(client, admin)
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    cust_id = client.get(f"/contracts/communications/{comm_id}", headers=_auth(admin)).json()[
        "recipient_customer_id"
    ]
    _post_webhook(
        client,
        {
            "format": "phi_generic_v1",
            "event_type": "hard_bounce",
            "provider_message_id": del_rows[0]["provider_message_id"],
            "recipient": del_rows[0]["recipient_address"],
        },
    )
    sf = client.get(f"/customers/{cust_id}/communication-safety", headers=_auth(admin))
    assert sf.status_code == 200
    assert sf.json()["suppressions"]
