"""
Outbound customer communications: provider abstraction, delivery rows, preferences, retry, dashboards.
"""
from __future__ import annotations

import pytest

from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.crm.customer_communication_preference_models import CustomerCommunicationPreference
from backend.app.services.outbound_communication_provider import (
    OutboundCommunicationProvider,
    OutboundEmailMessage,
    OutboundSendResult,
    set_email_provider_override,
)
from backend.tests.test_contract_amendment_activation import (
    _admin_token,
    _auth,
    _login,
    _proposal_ready_for_customer_release,
)


class FakeEmailProvider(OutboundCommunicationProvider):
    def __init__(self, *, ok: bool = True, err: str | None = None) -> None:
        self.ok = ok
        self.err = err
        self.sent: list[OutboundEmailMessage] = []

    def provider_name(self) -> str:
        return "fake"

    def send_email(self, msg: OutboundEmailMessage) -> OutboundSendResult:
        self.sent.append(msg)
        if self.ok:
            return OutboundSendResult(ok=True, provider_message_id="pmsg-1", raw_response={})
        return OutboundSendResult(
            ok=False,
            error_code="fake_err",
            error_message=self.err or "fail",
            raw_response={},
        )


@pytest.fixture(autouse=True)
def _teardown_provider():
    yield
    set_email_provider_override(None)


@pytest.fixture(autouse=True)
def _clear_deliveries_preferences():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ContractCustomerCommunicationDelivery).delete()
        db.query(CustomerCommunicationPreference).delete()
        db.commit()
    finally:
        db.close()
    yield


def _release_and_get_release_comm_id(client, admin: str) -> tuple[str, str, str]:
    """contract_id, proposal_id, communication_id (repricing_proposal_released draft)."""
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
    cid = next(
        x["id"] for x in lst.json() if x["communication_type"] == "repricing_proposal_released"
    )
    return contract_id, proposal_id, cid


def test_1_approved_ready_send_records_delivery_via_provider(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    admin = _admin_token(client)
    _cid, _pid, comm_id = _release_and_get_release_comm_id(client, admin)
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "sent"
    assert len(fake.sent) == 1
    d = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin))
    assert d.status_code == 200
    rows = d.json()
    assert len(rows) == 1
    assert rows[0]["status"] == "sent"
    assert rows[0]["provider_name"] == "fake"
    assert rows[0]["attempt_number"] == 1


def test_2_failed_provider_marks_communication_and_delivery_failed(client):
    fake = FakeEmailProvider(ok=False, err="smtp down")
    set_email_provider_override(fake)
    admin = _admin_token(client)
    _cid, _pid, comm_id = _release_and_get_release_comm_id(client, admin)
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "failed"
    d = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin))
    assert d.json()[0]["status"] == "failed"
    assert d.json()[0]["error_code"] == "fake_err"


def test_3_retry_creates_second_delivery_attempt(client):
    fake = FakeEmailProvider(ok=False, err="fail once")
    set_email_provider_override(fake)
    admin = _admin_token(client)
    contract_id, proposal_id, comm_id = _release_and_get_release_comm_id(client, admin)
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    assert client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin)).status_code == 200

    fake2 = FakeEmailProvider(ok=True)
    set_email_provider_override(fake2)
    r = client.post(f"/contracts/communications/{comm_id}/retry-send", headers=_auth(admin))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "sent"
    d = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin))
    attempts = sorted(d.json(), key=lambda x: x["attempt_number"])
    assert len(attempts) == 2
    assert attempts[0]["status"] == "failed"
    assert attempts[1]["status"] == "sent"


def test_4_disabled_global_email_preference_blocks_send(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    admin = _admin_token(client)
    contract_id, proposal_id, comm_id = _release_and_get_release_comm_id(client, admin)
    cust = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert cust.status_code == 200
    customer_id = cust.json()["customer_id"]
    pref = client.post(
        f"/customers/{customer_id}/communication-preferences",
        headers=_auth(admin),
        json={"channel": "email", "enabled": False, "contact_reference": None},
    )
    assert pref.status_code == 201, pref.text
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "failed"
    assert len(fake.sent) == 0
    d = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin))
    assert d.json()[0]["error_code"] == "recipient_blocked"


def test_5_preferred_recipient_resolution_uses_preference_email(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    admin = _admin_token(client)
    contract_id, proposal_id, comm_id = _release_and_get_release_comm_id(client, admin)
    cust = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    customer_id = cust.json()["customer_id"]
    p1 = client.post(
        f"/customers/{customer_id}/communication-preferences",
        headers=_auth(admin),
        json={
            "channel": "email",
            "enabled": True,
            "contact_reference": "billing-preferred@example.com",
            "preferred": True,
        },
    )
    assert p1.status_code == 201, p1.text
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    assert client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin)).status_code == 200
    assert fake.sent and fake.sent[0].to_address == "billing-preferred@example.com"


def test_6_cancelled_communication_cannot_send(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    admin = _admin_token(client)
    _cid, _pid, comm_id = _release_and_get_release_comm_id(client, admin)
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    assert (
        client.post(
            f"/contracts/communications/{comm_id}/cancel",
            headers=_auth(admin),
            json={"reason": "stop"},
        ).status_code
        == 200
    )
    assert client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin)).status_code == 400


def test_7_approval_required_blocks_send_until_approved(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
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
    rid = rem.json()["id"]
    assert client.post(f"/contracts/communications/{rid}/mark-ready", headers=_auth(admin)).status_code == 200
    assert client.post(f"/contracts/communications/{rid}/send", headers=_auth(admin)).status_code == 400
    fin = _login(client, username="finance@example.com", password="finance")
    assert client.post(f"/contracts/communications/{rid}/approve", headers=_auth(fin)).status_code == 200
    assert client.post(f"/contracts/communications/{rid}/send", headers=_auth(admin)).status_code == 200


def test_8_delivery_dashboards_expose_counts(client):
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)
    admin = _admin_token(client)
    _cid, _pid, comm_id = _release_and_get_release_comm_id(client, admin)
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    assert client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin)).status_code == 200
    d1 = client.get("/contracts/dashboard/customer-communications-delivery", headers=_auth(admin))
    assert d1.status_code == 200
    body = d1.json()
    assert "delivery_attempts_by_status" in body
    assert "communications_failed" in body
    assert body.get("total_delivery_attempts", 0) >= 1
    d2 = client.get("/contracts/dashboard/customer-communications-failures", headers=_auth(admin))
    assert d2.status_code == 200
    assert "failed_communication_count" in d2.json()
