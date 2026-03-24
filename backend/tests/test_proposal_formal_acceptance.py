"""
Formal proposal acceptance sessions, immutable evidence, secure-link flow, dashboards, audit logs.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ContractRepricingProposalLine,
    ContractRepricingReview,
    ContractReview,
    ProposalCustomerResponse,
)
from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord, ProposalAcceptanceSession


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
    """Returns (customer_email, customer_id, contract_id, repricing_review_id, proposal_id, client_password)."""
    email = f"fa_{uuid.uuid4().hex[:10]}@example.com"
    password = "fa-test-pw"
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


def test_released_proposal_can_create_acceptance_session(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    rel = client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    assert rel.status_code == 200, rel.text

    res = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "portal_acceptance", "issue_secure_token": False},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["acceptance_record"]["proposal_id"] == pid
    assert body["session"]["session_status"] == "active"
    assert body["plain_token"] is None


def test_unreleased_proposal_cannot_create_acceptance_session(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    res = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "portal_acceptance", "issue_secure_token": False},
    )
    assert res.status_code == 400


def test_expired_proposal_cannot_create_acceptance_session(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    rel = client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={"customer_expiry_at": past},
    )
    assert rel.status_code == 200, rel.text

    res = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "portal_acceptance", "issue_secure_token": False},
    )
    assert res.status_code == 400


def test_portal_acceptance_completion_creates_immutable_evidence(client):
    admin = _admin_token(client)
    email, cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)

    ini = client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/initiate",
        headers=_auth(ctok),
        json={"acceptance_type": "portal_acceptance"},
    )
    assert ini.status_code == 200, ini.text

    done = client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={
            "signed_name": "Alex Customer",
            "signed_title": "Facilities",
            "confirm_binding_acknowledgement": True,
        },
    )
    assert done.status_code == 200, done.text
    assert done.json()["customer_response_status"] == "accepted"
    assert done.json()["formal_acceptance_record_id"]

    ar = client.get(
        f"/contracts/acceptance-records/{done.json()['formal_acceptance_record_id']}",
        headers=_auth(admin),
    )
    assert ar.status_code == 200, ar.text
    row = ar.json()
    assert row["acceptance_status"] == "completed"
    assert row["immutable_hash"]
    assert row["evidence_json"]["signed_name"] == "Alex Customer"
    assert "disclosure" in row["evidence_json"]
    from backend.app.services.proposal_acceptance_service import assert_acceptance_record_not_mutated_after_completion
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rec = db.get(ProposalAcceptanceRecord, row["id"])
        assert rec is not None
        assert_acceptance_record_not_mutated_after_completion(rec)
    finally:
        db.close()


def test_completed_acceptance_cannot_be_repeated_or_mutated_in_place(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/initiate",
        headers=_auth(ctok),
        json={},
    )
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "A", "confirm_binding_acknowledgement": True},
    )

    again = client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "B", "confirm_binding_acknowledgement": True},
    )
    assert again.status_code == 400

    from backend.app.db.session import SessionLocal
    from backend.app.services.proposal_acceptance_service import assert_acceptance_record_not_mutated_after_completion

    db = SessionLocal()
    try:
        rec = db.query(ProposalAcceptanceRecord).filter(ProposalAcceptanceRecord.proposal_id == pid).one()
        assert rec.evidence_json
        ev = json.loads(rec.evidence_json)
        ev["signed_name"] = "Tampered evidence"
        rec.evidence_json = json.dumps(ev, separators=(",", ":"), sort_keys=True)
        db.commit()
        db.refresh(rec)
        with pytest.raises(AssertionError):
            assert_acceptance_record_not_mutated_after_completion(rec)
    finally:
        db.close()


def test_acceptance_completion_updates_proposal_accepted_linkage(client):
    admin = _admin_token(client)
    email, cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "Signer", "confirm_binding_acknowledgement": True},
    )
    det = client.get(f"/contracts/repricing-proposals/{pid}", headers=_auth(admin))
    assert det.status_code == 200
    assert det.json()["customer_response_status"] == "accepted"
    assert det.json()["formal_acceptance_record_id"]


def test_secure_link_acceptance_happy_path(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    res = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "token_link_acceptance", "issue_secure_token": True},
    )
    assert res.status_code == 201, res.text
    tok = res.json()["plain_token"]
    assert tok
    g = client.get(f"/portal/acceptance/{tok}")
    assert g.status_code == 200, g.text
    assert g.json()["session_status"] == "active"
    c = client.post(
        f"/portal/acceptance/{tok}/complete",
        json={
            "signed_name": "Token User",
            "signed_email": "token.user@example.com",
            "confirm_binding_acknowledgement": True,
        },
    )
    assert c.status_code == 200, c.text
    assert c.json()["immutable_hash"]


def test_secure_link_token_expiry_enforced(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})

    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    res = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={
            "acceptance_type": "token_link_acceptance",
            "issue_secure_token": True,
            "expires_at": past,
        },
    )
    assert res.status_code == 201, res.text
    tok = res.json()["plain_token"]
    assert tok

    g = client.get(f"/portal/acceptance/{tok}")
    assert g.status_code == 404

    res2 = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "token_link_acceptance", "issue_secure_token": True},
    )
    assert res2.status_code == 201
    tok2 = res2.json()["plain_token"]
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        sess = db.query(ProposalAcceptanceSession).filter(ProposalAcceptanceSession.proposal_id == pid).order_by(
            ProposalAcceptanceSession.created_at.desc()
        ).first()
        assert sess
        sess.expires_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        db.commit()
    finally:
        db.close()

    bad = client.post(
        f"/portal/acceptance/{tok2}/complete",
        json={
            "signed_name": "X",
            "signed_email": "x@example.com",
            "confirm_binding_acknowledgement": True,
        },
    )
    assert bad.status_code == 400


def test_internal_acceptance_record_endpoints_show_linkage(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    cr = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "portal_acceptance", "issue_secure_token": False},
    )
    rid = cr.json()["acceptance_record"]["id"]

    lst = client.get(f"/contracts/repricing-proposals/{pid}/acceptance-records", headers=_auth(admin))
    assert lst.status_code == 200
    assert any(r["id"] == rid for r in lst.json())

    one = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin))
    assert one.json()["proposal_id"] == pid


def test_dashboards_accepted_and_awaiting_activation(client):
    admin = _admin_token(client)
    email, cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "D", "confirm_binding_acknowledgement": True},
    )

    dash1 = client.get("/contracts/dashboard/accepted-proposals", headers=_auth(admin))
    assert dash1.status_code == 200
    assert dash1.json()["count"] >= 1
    assert any(r["proposal_id"] == pid for r in dash1.json()["rows"])

    dash2 = client.get("/contracts/dashboard/acceptance-awaiting-activation", headers=_auth(admin))
    assert dash2.status_code == 200
    assert any(r["proposal_id"] == pid for r in dash2.json()["rows"])


def test_commercial_log_records_acceptance_lifecycle(client):
    admin = _admin_token(client)
    _e, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    cr = client.post(
        f"/contracts/repricing-proposals/{pid}/acceptance-sessions",
        headers=_auth(admin),
        json={"acceptance_type": "token_link_acceptance", "issue_secure_token": True},
    )
    assert cr.status_code == 201
    sid = cr.json()["session"]["id"]

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, pid)
        logs = (
            db.query(ContractCommercialActionLog)
            .filter(ContractCommercialActionLog.contract_id == p.contract_id)
            .all()
        )
        types = {lg.action_type for lg in logs}
        assert "proposal_acceptance_session_created" in types
    finally:
        db.close()

    cx = client.post(f"/contracts/acceptance-sessions/{sid}/cancel", headers=_auth(admin))
    assert cx.status_code == 200

    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, pid)
        logs = (
            db.query(ContractCommercialActionLog)
            .filter(ContractCommercialActionLog.contract_id == p.contract_id)
            .all()
        )
        types = {lg.action_type for lg in logs}
        assert "proposal_acceptance_cancelled" in types
    finally:
        db.close()


def test_acceptance_does_not_mutate_contract_value(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    before = client.get(f"/contracts/{contract_id}", headers=_auth(admin)).json()["contract_value"]
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "Z", "confirm_binding_acknowledgement": True},
    )
    after = client.get(f"/contracts/{contract_id}", headers=_auth(admin)).json()["contract_value"]
    assert after == before


def test_amendment_creation_links_formal_acceptance_record(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(f"/portal/me/repricing-proposals/{pid}/acceptance/initiate", headers=_auth(ctok), json={})
    client.post(
        f"/portal/me/repricing-proposals/{pid}/acceptance/complete",
        headers=_auth(ctok),
        json={"signed_name": "Link Test", "confirm_binding_acknowledgement": True},
    )
    rid = client.get(f"/contracts/repricing-proposals/{pid}", headers=_auth(admin)).json()[
        "formal_acceptance_record_id"
    ]

    am = client.post(
        f"/contracts/repricing-proposals/{pid}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert am.status_code == 201, am.text
    aid = am.json()["id"]

    rec = client.get(f"/contracts/acceptance-records/{rid}", headers=_auth(admin)).json()
    assert rec["amendment_id"] == aid

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, pid)
        logs = (
            db.query(ContractCommercialActionLog)
            .filter(ContractCommercialActionLog.contract_id == p.contract_id)
            .all()
        )
        assert any(lg.action_type == "proposal_acceptance_linked_to_amendment" for lg in logs)
    finally:
        db.close()
