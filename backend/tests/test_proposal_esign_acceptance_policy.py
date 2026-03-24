"""
Legal e-sign provider flows, webhooks, acceptance policy gates, dashboards.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import pytest

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
    email = f"es_{uuid.uuid4().hex[:10]}@example.com"
    password = "es-test-pw"
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

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation

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


def _esign_hmac_hex(body: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


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


@pytest.fixture
def esign_env(monkeypatch):
    secret = "test-esign-whsec"
    monkeypatch.setenv("PHI_DPS_ESIGN_ENABLED", "1")
    monkeypatch.setenv("PHI_DPS_ESIGN_PROVIDER", "stub")
    monkeypatch.setenv("PHI_DPS_ESIGN_WEBHOOK_SECRET", secret)
    return secret


def test_eligible_released_proposal_can_create_provider_esign_session(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    res = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["acceptance_record_id"]
    assert body["session_id"]
    assert body["signing_url"]
    assert body["provider_envelope_id"]
    assert body["provider"] == "stub"


def test_unreleased_proposal_cannot_create_esign_session(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    res = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    assert res.status_code == 400


def test_provider_webhook_signed_finalizes_acceptance_record(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    cr = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    assert cr.status_code == 201, cr.text
    env_id = cr.json()["provider_envelope_id"]
    rid = cr.json()["acceptance_record_id"]

    payload = {
        "format": "phi_stub_esign_v1",
        "envelope_id": env_id,
        "status": "signed",
        "event_id": "evt-1",
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    sig = _esign_hmac_hex(raw, esign_env)
    wh = client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={"Content-Type": "application/json", "X-Phi-Dps-Esign-Signature": sig},
    )
    assert wh.status_code == 200, wh.text
    assert wh.json().get("applied") is True

    ar = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin))
    assert ar.status_code == 200
    row = ar.json()
    assert row["acceptance_status"] == "completed"
    assert row["acceptance_evidence_type"] == "provider_esign"
    assert row["provider_status"] == "signed"
    assert row["immutable_hash"]

    prop = client.get(f"/contracts/repricing-proposals/{pid}", headers=_auth(admin)).json()
    assert prop["customer_response_status"] == "accepted"
    assert prop["formal_acceptance_record_id"] == rid


def test_provider_webhook_declined_updates_session_safely(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    cr = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    env_id = cr.json()["provider_envelope_id"]
    rid = cr.json()["acceptance_record_id"]
    sid = cr.json()["session_id"]

    payload = {"format": "phi_stub_esign_v1", "envelope_id": env_id, "status": "declined", "event_id": "d1"}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    sig = _esign_hmac_hex(raw, esign_env)
    wh = client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={"Content-Type": "application/json", "X-Phi-Dps-Esign-Signature": sig},
    )
    assert wh.status_code == 200

    ar = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin)).json()
    assert ar["provider_status"] == "declined"
    assert ar["acceptance_status"] == "cancelled"

    sess = client.get(f"/contracts/acceptance-sessions/{sid}", headers=_auth(admin)).json()
    assert sess["session_status"] == "cancelled"


def test_acceptance_policy_blocks_amendment_creation_when_formal_missing(client, monkeypatch):
    monkeypatch.setenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "require_formal_acceptance_for_amendment")
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, pid)
        assert p is not None
        p.customer_response_status = "accepted"
        p.customer_release_status = "released"
        p.formal_acceptance_record_id = None
        db.commit()
    finally:
        db.close()

    am = client.post(f"/contracts/repricing-proposals/{pid}/create-amendment", headers=_auth(admin), json={})
    assert am.status_code == 400
    assert "acceptance_policy_blocked_amendment" in am.json()["detail"] or "not ready" in am.json()["detail"].lower()


def test_acceptance_policy_blocks_activation_when_provider_esign_required(client, monkeypatch, esign_env):
    monkeypatch.setenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "require_provider_esign_for_activation")
    admin = _admin_token(client)
    email, _cid, _ct, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "In App Only", "confirm_binding_acknowledgement": True},
    )

    am = client.post(f"/contracts/repricing-proposals/{pid}/create-amendment", headers=_auth(admin), json={})
    assert am.status_code == 201, am.text
    aid = am.json()["id"]
    if am.json().get("status") == "draft":
        assert client.post(f"/contracts/amendments/{aid}/submit-for-approval", headers=_auth(admin)).status_code == 200
    assert client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={}).status_code == 200

    act = client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))
    assert act.status_code == 400
    det = act.json()["detail"].lower()
    assert "acceptance_policy" in det or "esign" in det or "provider" in det


def test_warn_only_in_product_acceptance_still_works_for_amendment(client, monkeypatch):
    monkeypatch.setenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "warn_only")
    admin = _admin_token(client)
    email, _cid, _ct, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "Warn Only", "confirm_binding_acknowledgement": True},
    )
    am = client.post(f"/contracts/repricing-proposals/{pid}/create-amendment", headers=_auth(admin), json={})
    assert am.status_code == 201, am.text


def test_dashboard_esign_and_policy_blockers(client, monkeypatch, esign_env):
    monkeypatch.setenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "require_formal_acceptance_for_amendment")
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200
    assert client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={}).status_code == 201

    d1 = client.get("/contracts/dashboard/esign-status", headers=_auth(admin))
    assert d1.status_code == 200
    assert d1.json().get("integration_enabled") is True
    assert len(d1.json().get("in_progress") or []) >= 1

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, pid)
        assert p
        p.customer_response_status = "accepted"
        p.customer_release_status = "released"
        p.formal_acceptance_record_id = None
        db.commit()
    finally:
        db.close()

    d2 = client.get("/contracts/dashboard/acceptance-policy-blockers", headers=_auth(admin))
    assert d2.status_code == 200
    body = d2.json()
    assert body["acceptance_policy_mode"] == "require_formal_acceptance_for_amendment"
    assert body["counts"]["amendment_creation_blocked"] >= 1
    assert any(x["proposal_id"] == pid for x in body["amendment_creation_blocked"])
    hit = next(x for x in body["amendment_creation_blocked"] if x["proposal_id"] == pid)
    assert hit.get("reason_messages") and len(hit["reason_messages"]) == len(hit["reasons"])
    assert body.get("policy_matrix")
    assert body.get("active_mode_explainer", {}).get("mode") == "require_formal_acceptance_for_amendment"
    assert isinstance(body.get("requirements_for_amendment"), list) and body["requirements_for_amendment"]
    assert isinstance(body.get("requirements_for_activation"), list) and body["requirements_for_activation"]
    assert body.get("evidence_types_explainer")
    assert body.get("config_env_var") == "PHI_DPS_ACCEPTANCE_POLICY_MODE"


def test_esign_webhook_bad_signature_does_not_mutate_state(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    cr = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    env_id = cr.json()["provider_envelope_id"]
    rid = cr.json()["acceptance_record_id"]
    before = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin)).json()["provider_status"]

    payload = {"format": "phi_stub_esign_v1", "envelope_id": env_id, "status": "viewed", "event_id": "x"}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    bad = client.post(
        "/webhooks/esign/provider",
        content=raw,
        headers={"Content-Type": "application/json", "X-Phi-Dps-Esign-Signature": "deadbeef"},
    )
    assert bad.status_code == 401

    after = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin)).json()["provider_status"]
    assert after == before


def test_provider_status_endpoint_and_amendment_linkage_after_sign(client, esign_env):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    assert client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={}).status_code == 200

    cr = client.post(f"/contracts/repricing-proposals/{pid}/esign-sessions", headers=_auth(admin), json={})
    env_id = cr.json()["provider_envelope_id"]
    rid = cr.json()["acceptance_record_id"]

    raw = json.dumps(
        {"format": "phi_stub_esign_v1", "envelope_id": env_id, "status": "signed", "event_id": "e2"},
        separators=(",", ":"),
        sort_keys=True,
    )
    assert (
        client.post(
            "/webhooks/esign/provider",
            content=raw,
            headers={"Content-Type": "application/json", "X-Phi-Dps-Esign-Signature": _esign_hmac_hex(raw, esign_env)},
        ).status_code
        == 200
    )

    ps = client.get(f"/contracts/acceptance-records/{rid}/provider-status", headers=_auth(admin))
    assert ps.status_code == 200
    assert ps.json()["acceptance_record_id"] == rid
    assert "stored_payload_top_level_keys" in ps.json()

    am = client.post(f"/contracts/repricing-proposals/{pid}/create-amendment", headers=_auth(admin), json={})
    assert am.status_code == 201, am.text
    aid = am.json()["id"]
    linked = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin)).json()
    assert linked["amendment_id"] == aid
