"""
DocuSign provider: mocked HTTP, real routing, webhook HMAC, policy, and API safety.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord, ProposalAcceptanceSession
from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ContractRepricingProposalLine,
    ContractRepricingReview,
    ContractReview,
    ProposalCustomerResponse,
)
from backend.app.services.esign_providers import docusign_esign_provider as dsp


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


def _ensure_client_user(email: str, password: str) -> None:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return
        role = db.query(Role).filter(Role.name == "Client").one()
        db.add(User(email=email, hashed_password=hash_password(password), roles=[role]))
        db.commit()
    finally:
        db.close()


def _customer_contract_and_repricing_proposal(client, admin: str):
    import uuid
    from datetime import datetime, timezone

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation

    email = f"ds_{uuid.uuid4().hex[:10]}@example.com"
    password = "ds-test-pw"
    _ensure_client_user(email, password)

    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
    assert conv.status_code == 200, conv.text
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"Contract {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 40000.0,
        },
    )
    assert ctr.status_code == 201, ctr.text
    contract_id = ctr.json()["id"]

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_negative_margin",
                category="contract_attention",
                severity="critical",
                confidence="high",
                title="Margin",
                summary="S",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"m:{contract_id}:{uuid.uuid4().hex[:6]}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.post("/contracts/reviews/from-recommendation", headers=_auth(admin), json={"recommendation_id": rid})
    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    rr_id = rr.json()["id"]
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 45000.0, "current_contract_value": 40000.0},
    )
    pr = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    assert pr.status_code == 201, pr.text
    pid = pr.json()["id"]
    pdf = client.post(f"/contracts/repricing-proposals/{pid}/generate-pdf", headers=_auth(admin))
    assert pdf.status_code == 200, pdf.text
    for ep in [
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ]:
        r = client.post(ep, headers=_auth(admin))
        assert r.status_code == 200, r.text

    return email, cid, contract_id, rr_id, pid, password


def _docusign_sig(body: str, secret: str) -> str:
    d = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(d).decode("ascii")


@pytest.fixture(autouse=True)
def _clear_acceptance_and_repricing():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ProposalAcceptanceSession).delete()
        db.query(ProposalAcceptanceRecord).delete()
        db.query(ContractAmendment).delete()
        db.query(ProposalCustomerResponse).delete()
        db.query(ContractRepricingProposalLine).delete()
        db.query(ContractRepricingProposal).delete()
        db.query(ContractCommercialActionLog).delete()
        db.query(ContractRepricingReview).delete()
        db.query(ContractReview).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(scope="session")
def _docusign_test_rsa_pem_path(tmp_path_factory):
    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    p = tmp_path_factory.mktemp("docusign_keys") / "test_signer.pem"
    p.write_bytes(pem)
    return p


@pytest.fixture
def docusign_env(monkeypatch, _docusign_test_rsa_pem_path):
    pem_path = _docusign_test_rsa_pem_path
    secret = "docusign-connect-hmac-test"
    monkeypatch.setenv("PHI_DPS_ESIGN_ENABLED", "1")
    monkeypatch.setenv("PHI_DPS_ESIGN_PROVIDER", "docusign")
    monkeypatch.setenv("PHI_DPS_ESIGN_CLIENT_ID", "integration-key-test")
    monkeypatch.setenv("PHI_DPS_ESIGN_USER_ID", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    monkeypatch.setenv("PHI_DPS_ESIGN_ACCOUNT_ID", "11111111-2222-3333-4444-555555555555")
    monkeypatch.setenv("PHI_DPS_ESIGN_RSA_PRIVATE_KEY_PATH", str(pem_path))
    monkeypatch.setenv("PHI_DPS_ESIGN_AUTH_SERVER", "account-d.docusign.com")
    monkeypatch.setenv("PHI_DPS_ESIGN_BASE_URL", "https://demo.docusign.net/restapi")
    monkeypatch.setenv("PHI_DPS_ESIGN_WEBHOOK_SECRET", secret)
    monkeypatch.setenv("PHI_DPS_ESIGN_RETURN_URL", "https://portal.example.invalid/esign/return")
    return {"secret": secret, "envelope_id": "env-ds-mock-001"}


@pytest.fixture
def docusign_mock_http(docusign_env):
    env_id = docusign_env["envelope_id"]
    dsp.reset_docusign_auth_state_for_tests()

    class R:
        def __init__(self, code: int, j: dict):
            self.status_code = code
            self._j = j

        def json(self) -> dict:
            return self._j

    def send(method: str, url: str, **kwargs) -> R:  # type: ignore[no-untyped-def]
        if "oauth/token" in url:
            return R(200, {"access_token": "SECRET_SHOULD_NOT_LEAK_VIA_API", "expires_in": 3600})
        if method == "POST" and "/envelopes" in url and "views/recipient" not in url:
            return R(201, {"envelopeId": env_id})
        if "views/recipient" in url:
            return R(201, {"url": "https://demo.docusign.net/signing/embedded-session-test"})
        return R(500, {"error": "unexpected mock url", "url": url})

    dsp.set_http_send_for_tests(send)
    yield
    dsp.set_http_send_for_tests(None)
    dsp.reset_docusign_auth_state_for_tests()


def test_docusign_esign_session_stores_envelope_and_signing_url(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    res = client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "signer@customer.example"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["provider"] == "docusign"
    assert body["provider_envelope_id"] == docusign_env["envelope_id"]
    assert "demo.docusign.net" in body["signing_url"]
    assert "SECRET_SHOULD_NOT_LEAK" not in res.text
    assert "integration-key-test" not in res.text
    assert "docusign_test.pem" not in res.text


def test_docusign_create_failure_surfaces_without_sent_envelope(client, docusign_env, monkeypatch):
    dsp.reset_docusign_auth_state_for_tests()

    class R:
        def __init__(self, code: int, j: dict):
            self.status_code = code
            self._j = j

        def json(self) -> dict:
            return self._j

    def send(method: str, url: str, **kwargs) -> R:  # type: ignore[no-untyped-def]
        if "oauth/token" in url:
            return R(200, {"access_token": "tok", "expires_in": 3600})
        if method == "POST" and "/envelopes" in url and "views/recipient" not in url:
            return R(400, {"errorCode": "UNIT_TEST_FAIL", "message": "bad request"})
        return R(201, {"envelopeId": "x"})

    dsp.set_http_send_for_tests(send)
    try:
        admin = _admin_token(client)
        _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
        assert (
            client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code
            == 200
        )
        res = client.post(
            f"/contracts/repricing-proposals/{pid}/esign-sessions",
            headers=_auth(admin),
            json={"signer_email": "a@b.com"},
        )
        assert res.status_code == 400
        assert "DocuSign" in res.json()["detail"]

        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        try:
            rec = db.query(ProposalAcceptanceRecord).filter(ProposalAcceptanceRecord.proposal_id == pid).one_or_none()
            assert rec is not None
            assert rec.provider_status == "failed"
            assert rec.acceptance_status == "cancelled"
            assert not rec.provider_envelope_id
        finally:
            db.close()
    finally:
        dsp.set_http_send_for_tests(None)
        dsp.reset_docusign_auth_state_for_tests()


def _connect_payload(envelope_id: str, event: str, env_status: str, gen: str) -> dict:
    return {
        "event": event,
        "generatedDateTime": gen,
        "data": {
            "envelopeId": envelope_id,
            "envelopeSummary": {"status": env_status, "envelopeId": envelope_id},
        },
    }


def test_docusign_webhook_signed_completes_acceptance(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    cr = client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "signer@customer.example"},
    )
    assert cr.status_code == 201, cr.text
    rid = cr.json()["acceptance_record_id"]
    env_id = docusign_env["envelope_id"]

    raw = json.dumps(
        _connect_payload(env_id, "envelope-completed", "completed", "2025-03-22T10:00:00Z"),
        separators=(",", ":"),
        sort_keys=True,
    )
    wh = client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-DocuSign-Signature-1": _docusign_sig(raw, docusign_env["secret"]),
        },
    )
    assert wh.status_code == 200, wh.text
    assert wh.json().get("effect") == "signed_completed"

    ar = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin))
    assert ar.json()["acceptance_status"] == "completed"
    assert ar.json()["provider_status"] == "signed"


def test_docusign_webhook_declined_cancels_session(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    cr = client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "signer@customer.example"},
    )
    sid = cr.json()["session_id"]
    env_id = docusign_env["envelope_id"]

    raw = json.dumps(
        _connect_payload(env_id, "envelope-declined", "declined", "2025-03-22T11:00:00Z"),
        separators=(",", ":"),
        sort_keys=True,
    )
    wh = client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-DocuSign-Signature-1": _docusign_sig(raw, docusign_env["secret"]),
        },
    )
    assert wh.status_code == 200
    sess = client.get(f"/contracts/acceptance-sessions/{sid}", headers=_auth(admin))
    assert sess.json()["session_status"] == "cancelled"


def test_docusign_duplicate_webhook_idempotent(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "signer@customer.example"},
    )
    env_id = docusign_env["envelope_id"]
    raw = json.dumps(
        _connect_payload(env_id, "envelope-completed", "completed", "2025-03-22T12:00:00Z"),
        separators=(",", ":"),
        sort_keys=True,
    )
    hdr = {
        "Content-Type": "application/json",
        "X-DocuSign-Signature-1": _docusign_sig(raw, docusign_env["secret"]),
    }
    assert client.post("/webhooks/esign/provider", content=raw, headers=hdr).json()["effect"] == "signed_completed"
    dup = client.post("/webhooks/esign/provider", content=raw, headers=hdr)
    assert dup.status_code == 200
    assert dup.json().get("effect") == "duplicate_ignored"


def test_policy_still_blocks_activation_without_provider_signatures(client, docusign_env, docusign_mock_http, monkeypatch):
    monkeypatch.setenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "require_provider_esign_for_activation")
    admin = _admin_token(client)
    email, _cid, _ct, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "Portal", "confirm_binding_acknowledgement": True},
    )
    am = client.post(f"/contracts/repricing-proposals/{pid}/create-amendment", headers=_auth(admin), json={})
    assert am.status_code == 201, am.text
    aid = am.json()["id"]
    if am.json().get("status") == "draft":
        client.post(f"/contracts/amendments/{aid}/submit-for-approval", headers=_auth(admin))
    client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    act = client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))
    assert act.status_code == 400


def test_provider_status_and_dashboard_normalized_fields(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    cr = client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "signer@customer.example"},
    )
    rid = cr.json()["acceptance_record_id"]
    env_id = docusign_env["envelope_id"]
    raw = json.dumps(
        _connect_payload(env_id, "envelope-sent", "sent", "2025-03-22T09:00:00Z"),
        separators=(",", ":"),
        sort_keys=True,
    )
    client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-DocuSign-Signature-1": _docusign_sig(raw, docusign_env["secret"]),
        },
    )
    ps = client.get(f"/contracts/acceptance-records/{rid}/provider-status", headers=_auth(admin))
    assert ps.status_code == 200
    pj = ps.json()
    assert pj["provider_name"] == "docusign"
    assert pj["last_connect_event"] == "envelope-sent"
    assert pj["last_webhook_generated_at"]

    dash = client.get("/contracts/dashboard/esign-status", headers=_auth(admin))
    assert dash.status_code == 200
    rows = dash.json()["in_progress"] + dash.json()["signed_completed"] + dash.json()["declined_or_terminal"]
    assert any(r.get("acceptance_record_id") == rid for r in rows)
    blob = json.dumps(dash.json())
    assert "SECRET_SHOULD_NOT_LEAK" not in blob


def test_api_responses_never_include_config_secrets(client, docusign_env, docusign_mock_http):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    res = client.post(
        f"/contracts/repricing-proposals/{pid}/esign-sessions",
        headers=_auth(admin),
        json={"signer_email": "x@y.z"},
    )
    text = res.text.lower()
    assert "integration-key-test" not in text
    assert "11111111-2222-3333-4444-555555555555" not in res.text
    assert "docusign-connect-hmac-test" not in text
    assert "secret_should_not_leak" not in text
