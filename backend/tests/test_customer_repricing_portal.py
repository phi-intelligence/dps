"""
Customer-facing repricing proposal release, portal visibility, responses, dashboards, expiry.
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


def _customer_contract_and_repricing_proposal(client, admin: str, *, with_pdf: bool = True):
    """Returns (customer_email, customer_id, contract_id, repricing_review_id, proposal_id, client_password)."""
    email = f"crp_{uuid.uuid4().hex[:10]}@example.com"
    password = "portal-cr-test"
    _ensure_client_user(email, password)

    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": email},
    )
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

    client.post(
        "/contracts/reviews/from-recommendation",
        headers=_auth(admin),
        json={"recommendation_id": rid},
    )
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
    if with_pdf:
        pdf = client.post(f"/contracts/repricing-proposals/{pid}/generate-pdf", headers=_auth(admin))
        assert pdf.status_code == 200, pdf.text
    for ep, _ in [
        (f"/contracts/repricing-proposals/{pid}/mark-internal-review", {}),
        (f"/contracts/repricing-proposals/{pid}/approve-internal", {}),
        (f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer", {}),
    ]:
        r = client.post(ep, headers=_auth(admin))
        assert r.status_code == 200, r.text

    return email, cid, contract_id, rr_id, pid, password


@pytest.fixture(autouse=True)
def _clear_customer_repricing_tables():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
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


def test_internally_ready_proposal_can_be_released_to_customer(client):
    admin = _admin_token(client)
    _email, _cid, _ct, _rr, pid, _pw = _customer_contract_and_repricing_proposal(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text
    assert rel.json()["customer_release_status"] == "released"
    assert rel.json()["released_to_customer_at"] is not None


def test_unreleased_proposal_not_visible_in_portal(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    ctok = _login(client, username=email, password=password)
    lst = client.get(
        f"/portal/me/contracts/{contract_id}/repricing-proposals",
        headers=_auth(ctok),
    )
    assert lst.status_code == 200
    assert lst.json() == []
    det = client.get(f"/portal/me/repricing-proposals/{pid}", headers=_auth(ctok))
    assert det.status_code == 404


def test_released_proposal_visible_only_to_authorized_customer(client):
    admin = _admin_token(client)
    email, cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    lst = client.get(
        f"/portal/me/contracts/{contract_id}/repricing-proposals",
        headers=_auth(ctok),
    )
    assert len(lst.json()) == 1
    assert lst.json()[0]["id"] == pid

    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    _ensure_client_user(other_email, "x")
    from backend.app.db.session import SessionLocal
    from backend.app.modules.crm.models import Customer

    db = SessionLocal()
    try:
        db.add(Customer(name="Other", email=other_email))
        db.commit()
    finally:
        db.close()
    otok = _login(client, username=other_email, password="x")
    assert client.get(f"/portal/me/repricing-proposals/{pid}", headers=_auth(otok)).status_code == 404
    assert contract_id and cid


def test_customer_can_download_released_proposal_pdf(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    dl = client.get(f"/portal/me/repricing-proposals/{pid}/download", headers=_auth(ctok))
    assert dl.status_code == 200
    assert dl.headers.get("content-type", "").startswith("application/pdf")


def test_customer_response_updates_customer_facing_state(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    res = client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted", "notes": "OK to proceed"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["customer_response_status"] == "accepted"
    assert body["customer_release_status"] == "responded"


def test_accepted_response_does_not_change_contract_value(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted"},
    )
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0


def test_rejected_response_creates_follow_up_commercial_logs(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "rejected", "notes": "Too high"},
    )
    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    types = [x["action_type"] for x in logs.json()]
    assert "proposal_response_recorded" in types
    assert "follow_up_required" in types

    email2, _c2, c2, _rr2, pid2, pw2 = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid2}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    t2 = _login(client, username=email2, password=pw2)
    client.post(
        f"/portal/me/repricing-proposals/{pid2}/respond",
        headers=_auth(t2),
        json={"response_type": "counter_requested"},
    )
    logs2 = client.get(f"/contracts/{c2}/commercial-actions", headers=_auth(admin))
    t2types = [x["action_type"] for x in logs2.json()]
    assert "follow_up_required" in t2types


def test_customer_proposal_dashboard_shows_states(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    dash = client.get("/contracts/dashboard/customer-proposals", headers=_auth(admin))
    assert dash.status_code == 200
    body = dash.json()
    assert body["total"] >= 1
    assert "released" in body["by_customer_release_status"]
    fu = client.get("/contracts/dashboard/customer-proposal-follow-up", headers=_auth(admin))
    assert fu.status_code == 200


def test_expired_proposal_blocks_non_acknowledge_response(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    rel = client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={"customer_expiry_at": past},
    )
    assert rel.status_code == 200, rel.text
    ctok = _login(client, username=email, password=password)
    client.get(f"/portal/me/repricing-proposals/{pid}", headers=_auth(ctok))
    bad = client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted"},
    )
    assert bad.status_code == 400
    ok = client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "acknowledged", "notes": "Seen"},
    )
    assert ok.status_code == 200, ok.text


def test_viewed_timestamp_on_portal_access(client):
    admin = _admin_token(client)
    email, _cid, contract_id, _rr, pid, password = _customer_contract_and_repricing_proposal(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    before = client.get(f"/contracts/repricing-proposals/{pid}", headers=_auth(admin))
    assert before.json().get("customer_viewed_at") is None
    client.get(f"/portal/me/repricing-proposals/{pid}", headers=_auth(ctok))
    after = client.get(f"/contracts/repricing-proposals/{pid}", headers=_auth(admin))
    assert after.json().get("customer_viewed_at") is not None
    assert after.json()["customer_release_status"] == "viewed"

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        n_view = 0
        for row in (
            db.query(ContractCommercialActionLog)
            .filter(ContractCommercialActionLog.contract_id == contract_id)
            .all()
        ):
            if row.action_type != "proposal_viewed_by_customer":
                continue
            pj = json.loads(row.payload_json) if row.payload_json else {}
            if pj.get("proposal_id") == pid:
                n_view += 1
        assert n_view == 1
    finally:
        db.close()
