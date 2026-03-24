"""
Formal repricing proposals (CPQ-style) from repricing reviews: generation, workflow, PDF, dashboards.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ContractRepricingProposalLine,
    ContractRepricingReview,
    ContractReview,
    ProposalCustomerResponse,
)
from backend.app.modules.documents.models import StoredDocument


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


def _customer_and_contract(client, admin_token: str) -> tuple[str, str]:
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin_token),
        json={"name": f"L {uuid.uuid4().hex[:6]}", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin_token),
        json={"name": "C", "email": lead.json()["email"]},
    )
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "name": f"Contract {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
        },
    )
    assert ctr.status_code == 201, ctr.text
    return cid, ctr.json()["id"]


def _open_repricing_review_from_rec(client, admin: str, contract_id: str) -> str:
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
                title="Negative margin",
                summary="Margin below zero",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"margin:{contract_id}:{uuid.uuid4().hex[:6]}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()
    res = client.post(
        "/contracts/reviews/from-recommendation",
        headers=_auth(admin),
        json={"recommendation_id": rid},
    )
    assert res.status_code == 201, res.text
    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    assert rr.status_code == 200 and rr.json() is not None
    return rr.json()["id"]


@pytest.fixture(autouse=True)
def _clear_repricing_proposals_and_reviews():
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


def test_repricing_review_with_proposed_value_generates_structured_proposal(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)

    patch = client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 125000.0, "current_contract_value": 100000.0},
    )
    assert patch.status_code == 200, patch.text

    res = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["repricing_review_id"] == rr_id
    assert body["proposal_status"] == "generated"
    assert body["proposed_contract_value"] == 125000.0
    assert body["current_contract_value"] == 100000.0
    assert len(body["lines"]) >= 1
    line = next(ln for ln in body["lines"] if ln["line_type"] == "base_contract_value")
    assert line["proposed_line_total"] == 125000.0
    assert line["current_line_total"] == 100000.0


def test_proposal_lines_preserve_current_vs_proposed_context(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 48000.0, "current_contract_value": 45000.0},
    )
    res = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    assert res.status_code == 201
    line = res.json()["lines"][0]
    assert line["current_unit_price"] == 45000.0
    assert line["proposed_unit_price"] == 48000.0
    assert line["variance_amount"] == 3000.0


def test_proposal_does_not_alter_live_contract_pricing(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"contract_value": 50000.0},
    )
    c_before = client.get(f"/contracts/{contract_id}", headers=_auth(admin)).json()
    assert c_before["contract_value"] == 50000.0

    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 99999.0, "current_contract_value": 50000.0},
    )
    prop = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    assert prop.status_code == 201

    c_after = client.get(f"/contracts/{contract_id}", headers=_auth(admin)).json()
    assert c_after["contract_value"] == 50000.0


def test_proposal_internal_approval_flow_updates_status(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 60000.0, "current_contract_value": 55000.0},
    )
    cre = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    pid = cre.json()["id"]
    assert cre.json()["proposal_status"] == "generated"

    r1 = client.post(
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        headers=_auth(admin),
    )
    assert r1.status_code == 200
    assert r1.json()["proposal_status"] == "internal_review"

    r2 = client.post(f"/contracts/repricing-proposals/{pid}/approve-internal", headers=_auth(admin))
    assert r2.status_code == 200
    assert r2.json()["proposal_status"] == "approved_internal"
    assert r2.json()["approved_by_user_id"] is not None

    r3 = client.post(
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
        headers=_auth(admin),
    )
    assert r3.status_code == 200
    assert r3.json()["proposal_status"] == "ready_for_customer"
    assert r3.json()["ready_for_customer_at"] is not None


def test_new_proposal_supersedes_prior_when_requested(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 70000.0, "current_contract_value": 65000.0},
    )
    first = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id, "supersede_previous": False},
    )
    assert first.status_code == 201
    pid1 = first.json()["id"]

    second = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id, "supersede_previous": True},
    )
    assert second.status_code == 201
    pid2 = second.json()["id"]

    p1 = client.get(f"/contracts/repricing-proposals/{pid1}", headers=_auth(admin))
    assert p1.json()["proposal_status"] == "superseded"
    assert p1.json()["superseded_by_proposal_id"] == pid2


def test_proposal_pdf_generated_and_persisted_as_stored_document(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 80000.0, "current_contract_value": 75000.0},
    )
    prop = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    pid = prop.json()["id"]

    pdf = client.post(
        f"/contracts/repricing-proposals/{pid}/generate-pdf",
        headers=_auth(admin),
    )
    assert pdf.status_code == 200, pdf.text
    doc = pdf.json()
    assert doc["document_type"] == "repricing_proposal"
    assert doc["related_contract_id"] == contract_id

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        row = db.get(StoredDocument, doc["id"])
        assert row is not None
        assert row.visibility_scope == "internal_only"
        assert row.status == "ready"
        prop_row = db.get(ContractRepricingProposal, pid)
        assert prop_row.stored_document_id == doc["id"]
    finally:
        db.close()


def test_dashboard_lists_proposals_by_status(client):
    admin = _admin_token(client)
    _cid, c1 = _customer_and_contract(client, admin)
    rr1 = _open_repricing_review_from_rec(client, admin, c1)
    client.patch(
        f"/contracts/{c1}/repricing-review",
        headers=_auth(admin),
        json={"repricing_reason_codes": ["margin_pressure"], "proposed_contract_value": None},
    )
    d1 = client.post(
        f"/contracts/{c1}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr1},
    )
    assert d1.json()["proposal_status"] == "draft"

    _cid2, c2 = _customer_and_contract(client, admin)
    rr2 = _open_repricing_review_from_rec(client, admin, c2)
    client.patch(
        f"/contracts/{c2}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 40000.0, "current_contract_value": 38000.0},
    )
    d2 = client.post(
        f"/contracts/{c2}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr2},
    )
    pid2 = d2.json()["id"]
    client.post(f"/contracts/repricing-proposals/{pid2}/mark-internal-review", headers=_auth(admin))

    dash = client.get("/contracts/dashboard/repricing-proposals", headers=_auth(admin))
    assert dash.status_code == 200
    body = dash.json()
    assert body["by_status"].get("draft", 0) >= 1
    assert body["by_status"].get("internal_review", 0) >= 1
    listed = {r["proposal_id"] for r in body["rows"]}
    assert d1.json()["id"] in listed
    assert pid2 in listed


def test_repricing_review_shows_latest_proposal_linkage(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)
    rr_id = _open_repricing_review_from_rec(client, admin, contract_id)
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 33000.0, "current_contract_value": 30000.0},
    )
    prop = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    pid = prop.json()["id"]
    ref = prop.json()["proposal_reference"]

    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    assert rr.status_code == 200
    data = rr.json()
    assert data["latest_proposal_id"] == pid
    assert data["latest_proposal_reference"] == ref
    assert data["latest_proposal_status"] == "generated"
