"""
Structured contract renewal / repricing / commercial review workflow.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractReview,
)


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


@pytest.fixture(autouse=True)
def _clear_contract_reviews():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(ContractCommercialActionLog).delete()
        from backend.app.modules.contracts.review_models import ContractRepricingReview

        db.query(ContractRepricingReview).delete()
        db.query(ContractReview).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_renewal_risk_recommendation_opens_structured_review(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_renewal_risk",
                category="contract_attention",
                severity="high",
                confidence="medium",
                title="Renewal risk",
                summary="Churn risk elevated",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"renew:{contract_id}",
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
    body = res.json()
    assert body["review_type"] == "renewal"
    assert body["contract_id"] == contract_id


def test_negative_margin_signal_opens_repricing_review(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

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
                recommendation_key=f"margin:{contract_id}",
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
    assert res.json()["review_type"] == "repricing"

    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    assert rr.status_code == 200, rr.text
    assert rr.json() is not None
    assert "contract_negative_margin" in rr.json()["repricing_reason_codes"]


def test_duplicate_open_review_deduped(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_renewal_risk",
                category="contract_attention",
                severity="high",
                confidence="medium",
                title="R1",
                summary="S1",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"r1:{contract_id}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    r1 = client.post(
        "/contracts/reviews/from-recommendation",
        headers=_auth(admin),
        json={"recommendation_id": rid},
    )
    assert r1.status_code == 201
    first_id = r1.json()["id"]

    rid2 = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid2,
                recommendation_type="contract_renewal_risk",
                category="contract_attention",
                severity="high",
                confidence="medium",
                title="R2",
                summary="S2",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"r2:{contract_id}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    r2 = client.post(
        "/contracts/reviews/from-recommendation",
        headers=_auth(admin),
        json={"recommendation_id": rid2},
    )
    assert r2.status_code == 201
    assert r2.json()["id"] == first_id

    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    types = [x["action_type"] for x in logs.json()]
    assert "review_deduped" in types


def test_review_decision_updates_contract_renewal_state(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    cr = client.post(
        f"/contracts/{contract_id}/reviews",
        headers=_auth(admin),
        json={
            "review_type": "renewal",
            "triggered_reason": "Test open",
            "summary": "Commercial renewal review",
            "triggered_by": "manual",
        },
    )
    assert cr.status_code == 201, cr.text
    review_id = cr.json()["id"]

    dec = client.post(
        f"/contracts/reviews/{review_id}/decision",
        headers=_auth(admin),
        json={"decision": "renew_as_is", "notes": "Approved path"},
    )
    assert dec.status_code == 200, dec.text

    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["renewal_status"] == "ready_to_renew"
    assert c.json()["renewal_decision"] == "renew_as_is"


def test_review_pipeline_dashboard_lists_open_review(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    client.post(
        f"/contracts/{contract_id}/reviews",
        headers=_auth(admin),
        json={
            "review_type": "health_review",
            "triggered_reason": "Operational review",
            "summary": "Health check",
        },
    )

    pipe = client.get("/contracts/dashboard/review-pipeline", headers=_auth(admin))
    assert pipe.status_code == 200
    ids = {x["contract_id"] for x in pipe.json()["items"]}
    assert contract_id in ids


def test_commercial_action_log_captures_workflow(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    client.post(
        f"/contracts/{contract_id}/reviews",
        headers=_auth(admin),
        json={
            "review_type": "risk_review",
            "triggered_reason": "SLA pattern",
            "summary": "Risk escalation path",
        },
    )
    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    assert logs.status_code == 200
    types = {x["action_type"] for x in logs.json()}
    assert "review_opened" in types


def test_patch_review_owner_and_notes(client):
    admin = _admin_token(client)
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Dispatcher").one()
        am = User(
            email=f"am_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("pw"),
            roles=[role],
        )
        db.add(am)
        db.commit()
        db.refresh(am)
        am_id = am.id
    finally:
        db.close()

    _cid, contract_id = _customer_and_contract(client, admin)
    cr = client.post(
        f"/contracts/{contract_id}/reviews",
        headers=_auth(admin),
        json={
            "review_type": "renewal",
            "triggered_reason": "Assignment test",
            "summary": "Needs owner",
        },
    )
    review_id = cr.json()["id"]

    patch = client.patch(
        f"/contracts/reviews/{review_id}",
        headers=_auth(admin),
        json={"assigned_to_user_id": am_id, "notes": "Account manager engaged", "status": "in_review"},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["assigned_to_user_id"] == am_id
    assert "in_review" == patch.json()["status"]


def test_repricing_review_stores_proposed_value_and_reasons(client):
    admin = _admin_token(client)
    _cid, contract_id = _customer_and_contract(client, admin)

    res = client.post(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={
            "current_contract_value": 10000.0,
            "proposed_contract_value": 11800.0,
            "repricing_reason_codes": ["margin_pressure", "reactive_burden"],
            "margin_summary": {"gross_percent": -2.5},
            "customer_risk_level": "medium",
            "notes": "Awaiting AM approval",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["proposed_contract_value"] == 11800.0
    assert body["margin_summary"]["gross_percent"] == -2.5
    assert "margin_pressure" in body["repricing_reason_codes"]
