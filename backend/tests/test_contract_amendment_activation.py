"""
Contract amendment / activation workflow: accepted proposals -> formal amendments -> live contract update.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.automation.models import InternalFollowUpTask
from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.contract_version_models import ContractActivationRun, ContractVersion
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


def _proposal_ready_for_customer_release(client, admin: str) -> tuple[str, str, str]:
    """Returns (contract_id, proposal_id, customer_email). Internal gates complete; not yet released."""
    email = f"am_{uuid.uuid4().hex[:10]}@example.com"
    password = "am-test"
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
    pdf = client.post(f"/contracts/repricing-proposals/{pid}/generate-pdf", headers=_auth(admin))
    assert pdf.status_code == 200, pdf.text
    for ep in [
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ]:
        r = client.post(ep, headers=_auth(admin))
        assert r.status_code == 200, r.text

    return contract_id, pid, email


def _accepted_proposal(client, admin: str) -> tuple[str, str, str]:
    """Returns (contract_id, proposal_id, customer_email). Proposal is released and customer accepted."""
    contract_id, pid, email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password="am-test")
    client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted", "notes": "OK"},
    )
    return contract_id, pid, email


@pytest.fixture(autouse=True)
def _clear_amendment_tables():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ContractActivationRun).delete()
        db.query(ContractVersion).delete()
        db.query(InternalFollowUpTask).filter(
            InternalFollowUpTask.related_entity_type == "contract_amendment"
        ).delete(synchronize_session=False)
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


def test_acceptance_policy_matrix_endpoint(client):
    admin = _admin_token(client)
    r = client.get("/contracts/dashboard/acceptance-policy-matrix", headers=_auth(admin))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("current_mode")
    assert len(j.get("rows") or []) >= 5
    modes = {row["mode"] for row in j["rows"]}
    assert "warn_only" in modes
    assert "require_provider_esign_for_amendment_and_activation" in modes


def test_accepted_proposal_creates_amendment_with_prior_snapshot(client):
    """Accepted customer proposal can create amendment record with prior contract snapshot."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    readiness = client.get(
        f"/contracts/repricing-proposals/{proposal_id}/activation-readiness",
        headers=_auth(admin),
    )
    assert readiness.status_code == 200
    body_r = readiness.json()
    assert body_r["ready"] is True
    assert body_r.get("acceptance_policy_mode") == "warn_only"
    assert isinstance(body_r.get("blocking_reason_messages"), list)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["contract_id"] == contract_id
    assert body["source_proposal_id"] == proposal_id
    assert body["status"] in ("pending_approval", "approved", "scheduled")
    assert body["current_contract_value"] == 40000.0
    assert body["proposed_contract_value"] == 45000.0
    # Prior snapshot is stored internally; verify via service
    from backend.app.modules.contracts import amendment_service as ams
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        a = ams.get_amendment(db, amendment_id=body["id"])
        assert a is not None
        import json
        snap = json.loads(a.prior_contract_snapshot_json)
        assert snap["contract_value"] == 40000.0
    finally:
        db.close()


def test_creating_amendment_does_not_mutate_contract(client):
    """Creating amendment does not mutate live contract immediately."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0


def test_approval_required_amendment_cannot_activate_before_approval(client):
    """Approval-required amendment cannot activate before approval."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert create.status_code == 201
    amend_id = create.json()["id"]
    if create.json()["status"] != "pending_approval":
        # If policy sets approval_required=False, skip this test
        pytest.skip("Amendment created without pending_approval (policy may not require approval)")

    act = client.post(
        f"/contracts/amendments/{amend_id}/activate",
        headers=_auth(admin),
    )
    assert act.status_code == 400
    assert "approval" in act.json().get("detail", "").lower() or "status" in act.json().get("detail", "").lower()

    client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    act2 = client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))
    assert act2.status_code == 200
    assert client.get(f"/contracts/{contract_id}", headers=_auth(admin)).json()["contract_value"] == 45000.0


def test_approved_amendment_activates_and_updates_contract(client):
    """Approved amendment activates and updates contract safely."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert create.status_code == 201
    amend_id = create.json()["id"]

    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})

    act = client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))
    assert act.status_code == 200, act.text
    assert act.json()["status"] == "activated"

    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 45000.0


def test_activated_amendment_stores_resulting_snapshot(client):
    """Activated amendment stores resulting contract snapshot."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = create.json()["id"]
    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))

    from backend.app.modules.contracts import amendment_service as ams
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        a = ams.get_amendment(db, amendment_id=amend_id)
        assert a.resulting_contract_snapshot_json
        import json
        snap = json.loads(a.resulting_contract_snapshot_json)
        assert snap["contract_value"] == 45000.0
    finally:
        db.close()


def test_future_dated_amendment_scheduled_state(client):
    """Future-dated amendment enters scheduled/pending activation state correctly."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    from datetime import timedelta
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={"effective_date": future},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] in ("pending_approval", "scheduled")

    if body["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{body['id']}/approve", headers=_auth(admin), json={})
        get_a = client.get(f"/contracts/amendments/{body['id']}", headers=_auth(admin))
        assert get_a.json()["status"] == "scheduled"

    act = client.post(f"/contracts/amendments/{body['id']}/activate", headers=_auth(admin))
    assert act.status_code == 400
    assert "future" in act.json().get("detail", "").lower()


def test_dashboard_shows_pending_activations(client):
    """Dashboard shows pending activations / awaiting activation correctly."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = create.json()["id"]
    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})

    pend = client.get("/contracts/dashboard/pending-activations", headers=_auth(admin))
    assert pend.status_code == 200
    lst = pend.json().get("pending_activations", [])
    ids = [x["amendment_id"] for x in lst]
    assert amend_id in ids

    dash = client.get("/contracts/dashboard/amendments", headers=_auth(admin))
    assert dash.status_code == 200
    amendments = dash.json().get("amendments", [])
    amend_refs = [a["amendment_id"] for a in amendments]
    assert amend_id in amend_refs


def test_commercial_action_log_records_steps(client):
    """Commercial action log records creation/approval/activation steps."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = create.json()["id"]
    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))

    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    types = [x["action_type"] for x in logs.json()]
    assert "amendment_created" in types
    assert "amendment_activated" in types
    if create.json()["status"] == "pending_approval":
        assert "amendment_approved" in types


def test_proposal_amendment_linkage_queryable(client):
    """Proposal-to-amendment linkage is queryable and correct."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = create.json()["id"]

    lst = client.get(
        "/contracts/amendments",
        headers=_auth(admin),
        params={"source_proposal_id": proposal_id},
    )
    assert lst.status_code == 200
    assert len(lst.json()) == 1
    assert lst.json()[0]["id"] == amend_id
    assert lst.json()[0]["source_proposal_id"] == proposal_id

    get_a = client.get(f"/contracts/amendments/{amend_id}", headers=_auth(admin))
    assert get_a.json()["source_proposal_id"] == proposal_id


def test_rejected_amendment_does_not_mutate_contract(client):
    """Rejected amendment does not mutate contract."""
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)

    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = create.json()["id"]
    if create.json()["status"] != "pending_approval":
        pytest.skip("Amendment not pending_approval; cannot test reject path")

    client.post(
        f"/contracts/amendments/{amend_id}/reject",
        headers=_auth(admin),
        json={"notes": "Not proceeding"},
    )

    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0

    act = client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))
    assert act.status_code == 400
