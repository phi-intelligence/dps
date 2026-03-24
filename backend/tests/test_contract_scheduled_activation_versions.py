"""
Scheduled amendment activation, ContractVersion timeline, ContractActivationRun idempotency.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

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


def _accepted_proposal(client, admin: str) -> tuple[str, str]:
    """Returns (contract_id, proposal_id)."""
    email = f"sv_{uuid.uuid4().hex[:10]}@example.com"
    password = "sv-test"
    _ensure_client_user(email, password)

    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
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
    pid = pr.json()["id"]
    client.post(f"/contracts/repricing-proposals/{pid}/generate-pdf", headers=_auth(admin))
    for ep in [
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ]:
        client.post(ep, headers=_auth(admin))
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    ctok = _login(client, username=email, password=password)
    client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted"},
    )
    return contract_id, pid


def _released_proposal_no_response(client, admin: str) -> tuple[str, str]:
    """Returns (contract_id, proposal_id) after customer release without a portal response."""
    email = f"nr_{uuid.uuid4().hex[:10]}@example.com"
    password = "nr-test"
    _ensure_client_user(email, password)

    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
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
    pid = pr.json()["id"]
    client.post(f"/contracts/repricing-proposals/{pid}/generate-pdf", headers=_auth(admin))
    for ep in [
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ]:
        client.post(ep, headers=_auth(admin))
    client.post(f"/contracts/repricing-proposals/{pid}/release-to-customer", headers=_auth(admin), json={})
    return contract_id, pid


@pytest.fixture(autouse=True)
def _clear_version_tables():
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


def test_manual_activation_creates_contract_version(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        versions = (
            db.query(ContractVersion).filter(ContractVersion.contract_id == contract_id).order_by(
                ContractVersion.version_number.asc()
            ).all()
        )
        assert len(versions) >= 1
        active = [v for v in versions if v.effective_to is None]
        assert len(active) == 1
        assert active[0].version_type == "amendment_activation"
        assert active[0].source_amendment_id == aid
    finally:
        db.close()


def test_future_dated_amendment_not_activated_early_by_scheduler(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    future = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={"effective_date": future},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    batch = client.post(
        "/contracts/amendments/run-scheduled-activations",
        headers=_auth(admin),
        json={"dry_run": False},
    )
    assert batch.status_code == 200
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0


def test_due_scheduled_amendment_activates_via_scheduler(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    batch = client.post(
        "/contracts/amendments/run-scheduled-activations",
        headers=_auth(admin),
        json={"dry_run": False},
    )
    assert batch.status_code == 200
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 45000.0


def test_repeated_scheduler_idempotent_no_duplicate_versions(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    client.post("/contracts/amendments/run-scheduled-activations", headers=_auth(admin), json={})
    client.post("/contracts/amendments/run-scheduled-activations", headers=_auth(admin), json={})

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        v_count = db.query(ContractVersion).filter(ContractVersion.contract_id == contract_id).count()
        act_versions = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_type == "amendment_activation",
            )
            .count()
        )
        assert act_versions == 1
        assert v_count >= 1
    finally:
        db.close()


def test_failed_activation_creates_activation_run_record(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    # Leave pending_approval — activation must fail
    if cr.json()["status"] != "pending_approval":
        pytest.skip("Amendment not pending approval")
    act = client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))
    assert act.status_code == 400

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        failed = (
            db.query(ContractActivationRun)
            .filter(ContractActivationRun.amendment_id == aid, ContractActivationRun.status == "failed")
            .all()
        )
        assert len(failed) >= 1
    finally:
        db.close()


def test_contract_version_history_ordered_and_queryable(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))

    lst = client.get(f"/contracts/{contract_id}/versions", headers=_auth(admin))
    assert lst.status_code == 200
    body = lst.json()
    assert len(body) >= 2
    nums = [x["version_number"] for x in body]
    assert nums == sorted(nums)
    last = body[-1]
    assert last["effective_to"] is None
    assert last["source_amendment_id"] == aid

    one = client.get(f"/contracts/versions/{last['id']}", headers=_auth(admin))
    assert one.status_code == 200
    assert one.json()["contract_id"] == contract_id


def test_previous_version_gets_effective_to_on_activation(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        closed = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.effective_to.isnot(None),
            )
            .all()
        )
        assert len(closed) >= 1
    finally:
        db.close()


def test_dashboards_due_future_failures(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    future = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={"effective_date": future},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    fut = client.get("/contracts/dashboard/future-activations", headers=_auth(admin))
    assert fut.status_code == 200
    assert fut.json()["count"] >= 1

    due = client.get("/contracts/dashboard/activations-due", headers=_auth(admin))
    assert due.status_code == 200

    fails = client.get("/contracts/dashboard/activation-failures", headers=_auth(admin))
    assert fails.status_code == 200


def test_dry_run_scheduled_no_mutation(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    batch = client.post(
        "/contracts/amendments/run-scheduled-activations",
        headers=_auth(admin),
        json={"dry_run": True},
    )
    assert batch.status_code == 200
    assert batch.json()["dry_run"] is True
    assert batch.json()["candidate_count"] >= 1
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0


def test_amendment_version_linkage_after_activation(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    act = client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))
    assert act.status_code == 200
    vid = act.json().get("resulting_contract_version_id")
    assert vid
    v = client.get(f"/contracts/versions/{vid}", headers=_auth(admin))
    assert v.json()["source_amendment_id"] == aid


def test_dry_run_single_amendment_endpoint(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    dr = client.post(f"/contracts/amendments/{aid}/dry-run-activation", headers=_auth(admin))
    assert dr.status_code == 200
    assert dr.json()["would_activate"] is True
    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 40000.0
