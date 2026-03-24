"""§5.15 multi-provider comms: channel routing, SendGrid webhook ingest, SMS provider path."""
from __future__ import annotations

import json

import pytest

from backend.app.core import config
from backend.app.db.session import SessionLocal
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer
from backend.app.services.communication_channel_routing_service import effective_channel_for_communication_type
from backend.app.services.communication_webhook_sendgrid_service import (
    ingest_sendgrid_events_batch,
    sendgrid_event_to_phi_generic_v1,
)
from backend.app.services import contract_customer_communication_templates as tpl
from backend.app.services.outbound_communication_provider import set_email_provider_override
from backend.app.services.outbound_sms_provider import (
    OutboundSmsMessage,
    OutboundSmsResult,
    SmsOutboundProvider,
    set_sms_provider_override,
)
from backend.tests.test_contract_amendment_activation import (
    _admin_token,
    _auth,
    _proposal_ready_for_customer_release,
)
from backend.tests.test_outbound_customer_communications import FakeEmailProvider


class FakeSmsProvider(SmsOutboundProvider):
    def __init__(self, *, ok: bool = True) -> None:
        self.ok = ok
        self.sent: list[OutboundSmsMessage] = []

    def provider_name(self) -> str:
        return "fake_sms"

    def send_sms(self, msg: OutboundSmsMessage) -> OutboundSmsResult:
        self.sent.append(msg)
        if self.ok:
            return OutboundSmsResult(ok=True, provider_message_id="sms-1", raw_response={})
        return OutboundSmsResult(ok=False, error_code="fake", error_message="sms down", raw_response={})


@pytest.fixture(autouse=True)
def _teardown_overrides():
    yield
    set_email_provider_override(None)
    set_sms_provider_override(None)


def test_effective_channel_env_map_override(monkeypatch):
    monkeypatch.setattr(
        config.settings,
        "COMMUNICATION_TYPE_CHANNEL_MAP_JSON",
        '{"repricing_proposal_released":"sms"}',
        raising=False,
    )
    assert effective_channel_for_communication_type(tpl.COMMS_REPRICING_PROPOSAL_RELEASED) == "sms"
    assert effective_channel_for_communication_type(tpl.COMMS_REPRICING_PROPOSAL_REMINDER) == "email"


def test_sendgrid_event_maps_to_phi_generic():
    phi = sendgrid_event_to_phi_generic_v1(
        {
            "event": "delivered",
            "email": "a@b.com",
            "sg_message_id": "abc.filter0000.0.0",
            "timestamp": 1_700_000_000,
            "sg_event_id": "evt-1",
        }
    )
    assert phi["format"] == "phi_generic_v1"
    assert phi["event_type"] == "delivered"
    assert phi["provider_message_id"] == "abc"
    assert phi["external_event_id"] == "evt-1"


def test_sendgrid_webhook_http_updates_delivery(client, monkeypatch):
    monkeypatch.setattr(config.settings, "SENDGRID_WEBHOOK_INGEST_SECRET", "ingest-test-secret", raising=False)

    admin = _admin_token(client)
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
    comm_id = next(x["id"] for x in lst.json() if x["communication_type"] == "repricing_proposal_released")
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    del_rows = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    mid = del_rows[0]["provider_message_id"]
    to_addr = del_rows[0]["recipient_address"]

    events = [
        {
            "event": "delivered",
            "email": to_addr,
            "sg_message_id": f"{mid}.filter0",
            "timestamp": 1_700_000_001,
            "sg_event_id": "sg-test-delivered-1",
        }
    ]
    raw = json.dumps(events)
    r = client.post(
        "/webhooks/communications/sendgrid-events",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Phi-Dps-Sendgrid-Ingest-Secret": "ingest-test-secret",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json().get("processed") == 1

    del2 = client.get(f"/contracts/communications/{comm_id}/deliveries", headers=_auth(admin)).json()
    assert del2[0]["status"] == "delivered"


def test_sendgrid_ingest_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.setattr(config.settings, "SENDGRID_WEBHOOK_INGEST_SECRET", "", raising=False)
    r = client.post(
        "/webhooks/communications/sendgrid-events",
        json=[],
        headers={"X-Phi-Dps-Sendgrid-Ingest-Secret": "x"},
    )
    assert r.status_code == 503


def test_sms_communication_send_uses_sms_provider(client, monkeypatch):
    monkeypatch.setattr(
        config.settings,
        "COMMUNICATION_TYPE_CHANNEL_MAP_JSON",
        '{"repricing_proposal_released":"sms"}',
        raising=False,
    )
    fake_sms = FakeSmsProvider(ok=True)
    set_sms_provider_override(fake_sms)

    admin = _admin_token(client)
    fake = FakeEmailProvider(ok=True)
    set_email_provider_override(fake)

    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    db = SessionLocal()
    try:
        ctr = db.get(Contract, contract_id)
        assert ctr is not None
        cust = db.get(Customer, ctr.customer_id)
        assert cust is not None
        cust.phone = "+447700900123"
        db.add(cust)
        db.commit()
    finally:
        db.close()

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
    hit = next(x for x in lst.json() if x["communication_type"] == "repricing_proposal_released")
    assert hit["channel"] == "sms"
    comm_id = hit["id"]
    assert client.post(f"/contracts/communications/{comm_id}/mark-ready", headers=_auth(admin)).status_code == 200
    s = client.post(f"/contracts/communications/{comm_id}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "sent"
    assert len(fake_sms.sent) == 1
    assert fake_sms.sent[0].to_e164 == "+447700900123"
    assert not fake.sent, "email provider should not run for SMS channel"


def test_ingest_sendgrid_batch_rejects_non_array():
    db = SessionLocal()
    try:
        out = ingest_sendgrid_events_batch(db, {}, commit=False)
        assert out["accepted"] is False
        assert out.get("reason") == "expected_array"
    finally:
        db.close()
