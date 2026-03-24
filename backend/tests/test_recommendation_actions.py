"""
Decision-support workflow for operational recommendations: suggestions, preview, confirm, audit.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from backend.app.modules.ops.models import (
    OperationalRecommendation,
    RecommendationActionDecision,
    RecommendationActionSuggestion,
)


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


def _create_engineer_user(email: str, password: str) -> str:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        u = User(email=email, hashed_password=hash_password(password), roles=[role])
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _clear_rec_actions():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(RecommendationActionDecision).delete()
        db.query(RecommendationActionSuggestion).delete()
        db.query(OperationalRecommendation).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(autouse=True)
def _zero_recommendation_cooldowns(monkeypatch):
    monkeypatch.setattr("backend.app.core.config.settings.PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS", 0.0)
    monkeypatch.setattr("backend.app.core.config.settings.PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS", 0.0)


def test_dashboard_actions_summary_endpoint(client):
    admin = _admin_token(client)
    res = client.get("/ops/dashboard/actions/summary", headers=_auth(admin))
    assert res.status_code == 200
    body = res.json()
    assert "pending_confirmations" in body
    assert "action_decisions_last_7d_by_type" in body


def test_sla_risk_lists_assign_best_engineer_suggestion(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="sla_breach_risk",
                category="sla_risk",
                severity="high",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="job",
                entity_id="job-x",
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.get(f"/ops/recommendations/{rid}/actions", headers=_auth(admin))
    assert res.status_code == 200, res.text
    types = {x["action_type"] for x in res.json()}
    assert "assign_best_engineer" in types


def _add_qual(client, admin_token: str, engineer_id: str, competency: str) -> None:
    res = client.post(
        "/competence/qualifications",
        headers=_auth(admin_token),
        json={"engineer_user_id": engineer_id, "competency": competency, "expires_at": None},
    )
    assert res.status_code == 201, res.text


def test_preview_assign_best_shows_candidate_and_warnings(client):
    admin = _admin_token(client)
    e_email = f"e_{uuid.uuid4().hex[:8]}@example.com"
    e_id = _create_engineer_user(e_email, "pw")
    e_tok = _login(client, username=e_email, password="pw")

    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "address": "1 Way",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "required_competencies": ["gas"],
        },
    )
    assert job.status_code == 201
    job_id = job.json()["id"]

    _add_qual(client, admin, e_id, "gas")

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="sla_breach_risk",
                category="sla_risk",
                severity="high",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="job",
                entity_id=job_id,
                related_job_id=job_id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e_tok),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )

    res = client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer", "input_payload": {}},
    )
    assert res.status_code == 200, res.text
    prev = res.json()["preview"]
    assert prev.get("allowed") is True
    cand_ids = {c["engineer_id"] for c in prev.get("candidates", [])}
    assert e_id in cand_ids
    assert prev.get("selected_candidate", {}).get("engineer_id") in cand_ids


def test_confirm_assign_best_executes_dispatch_and_audits(client):
    admin = _admin_token(client)
    e_email = f"e_{uuid.uuid4().hex[:8]}@example.com"
    e_id = _create_engineer_user(e_email, "pw")
    e_tok = _login(client, username=e_email, password="pw")

    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "address": "1 Way",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "required_competencies": ["gas"],
        },
    )
    job_id = job.json()["id"]

    _add_qual(client, admin, e_id, "gas")

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="sla_breach_risk",
                category="sla_risk",
                severity="high",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="job",
                entity_id=job_id,
                related_job_id=job_id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e_tok),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )

    pv = client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer"},
    )
    assert pv.status_code == 200, pv.text
    picked = pv.json()["preview"]["selected_candidate"]["engineer_id"]
    ex = client.post(
        f"/ops/recommendations/{rid}/actions/confirm",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer", "confirmed": True},
    )
    assert ex.status_code == 200, ex.text
    assert ex.json()["execution"]["assigned_engineer_id"] == picked

    db = SessionLocal()
    try:
        from backend.app.modules.dispatch.models import Job

        j = db.get(Job, job_id)
        assert j.assigned_engineer_id == picked
        decisions = (
            db.query(RecommendationActionDecision)
            .filter(RecommendationActionDecision.recommendation_id == rid)
            .order_by(RecommendationActionDecision.decided_at.asc())
            .all()
        )
        types = [d.decision_type for d in decisions]
        assert "previewed" in types
        assert "confirmed" in types
        assert "executed" in types
    finally:
        db.close()


def test_inventory_risk_lists_transfer_and_po_draft(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.ledger_service import ensure_default_inventory_locations
    from backend.app.modules.inventory.models import StockItem

    db = SessionLocal()
    try:
        ensure_default_inventory_locations(db)
        sku = f"SKU-{uuid.uuid4().hex[:6]}"
        item = StockItem(sku=sku, name="N", unit_cost=1.0, on_hand_quantity=0.0, reserved_quantity=5.0)
        db.add(item)
        db.flush()
        iid = item.id
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="stock_shortage_reserved",
                category="inventory_risk",
                severity="critical",
                confidence="high",
                title="short",
                summary="s",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=iid,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.get(f"/ops/recommendations/{rid}/actions", headers=_auth(admin))
    assert res.status_code == 200
    types = {x["action_type"] for x in res.json()}
    assert "create_transfer_request" in types
    assert "create_purchase_order_draft" in types


def test_invoice_hold_execute_blocked_when_preconditions_clear(client):
    admin = _admin_token(client)
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={"customer_id": cid, "address": "Inv Way", "site_latitude": 51.0, "site_longitude": -0.2},
    )
    assert job.status_code == 201
    jid = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice
    from backend.app.modules.compliance.models import Certificate

    db = SessionLocal()
    try:
        j = db.get(Job, jid)
        j.status = "completed"
        iid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        db.add(Invoice(id=iid, job_id=jid, status="unpaid", grand_total=10.0))
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="invoice_release_hold",
                category="invoice_hold",
                severity="high",
                confidence="medium",
                title="hold",
                summary="s",
                detail_json="{}",
                entity_type="invoice",
                entity_id=iid,
                related_invoice_id=iid,
                related_job_id=jid,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    # Preconditions for hold exist (no cert)
    pv = client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "hold_invoice"},
    )
    assert pv.status_code == 200
    assert pv.json()["preview"]["allowed"] is True

    db = SessionLocal()
    try:
        from backend.app.services.job_costing import persist_job_cost_snapshot

        snap = persist_job_cost_snapshot(db, job_id=jid, commit=True)
        db.add(
            Certificate(
                id=str(uuid.uuid4()),
                job_id=jid,
                certificate_type="completion",
                status="generated",
                signed_by_engineer=False,
                signed_by_client=False,
            )
        )
        inv = db.get(Invoice, iid)
        inv.job_cost_snapshot_id = snap.id
        db.add(inv)
        db.commit()
    finally:
        db.close()

    bad = client.post(
        f"/ops/recommendations/{rid}/actions/confirm",
        headers=_auth(admin),
        json={"action_type": "hold_invoice", "confirmed": True},
    )
    assert bad.status_code == 400


def test_vehicle_readiness_lists_resolve_defect(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal

    vid = f"v-{uuid.uuid4().hex[:6]}"
    did = str(uuid.uuid4())
    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="vehicle_critical_defect_open",
                category="vehicle_readiness",
                severity="critical",
                confidence="high",
                title="def",
                summary="s",
                detail_json=json.dumps({"vehicle_id": vid, "defect_id": did}),
                entity_type="vehicle",
                entity_id=vid,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.get(f"/ops/recommendations/{rid}/actions", headers=_auth(admin))
    types = {x["action_type"] for x in res.json()}
    assert "resolve_defect" in types


def test_reject_stores_reason(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="sla_breach_risk",
                category="sla_risk",
                severity="high",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="job",
                entity_id="j1",
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.get(f"/ops/recommendations/{rid}/actions", headers=_auth(admin))
    rj = client.post(
        f"/ops/recommendations/{rid}/actions/reject",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer", "rejection_reason": "Prefer manual assign for this site"},
    )
    assert rj.status_code == 200
    assert rj.json()["action_status"] == "rejected"

    hist = client.get(f"/ops/recommendations/{rid}/actions/history", headers=_auth(admin))
    assert hist.status_code == 200
    rej = [x for x in hist.json() if x["decision_type"] == "rejected"]
    assert rej and rej[0]["override_reason"] == "Prefer manual assign for this site"


def test_history_records_preview_confirm_flow(client):
    admin = _admin_token(client)
    e_email = f"e_{uuid.uuid4().hex[:8]}@example.com"
    e_id = _create_engineer_user(e_email, "pw")
    e_tok = _login(client, username=e_email, password="pw")

    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "address": "1 Way",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "required_competencies": ["gas"],
        },
    )
    job_id = job.json()["id"]

    _add_qual(client, admin, e_id, "gas")

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="sla_breach_risk",
                category="sla_risk",
                severity="high",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="job",
                entity_id=job_id,
                related_job_id=job_id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e_tok),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )

    client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer"},
    )
    client.post(
        f"/ops/recommendations/{rid}/actions/confirm",
        headers=_auth(admin),
        json={"action_type": "assign_best_engineer", "confirmed": True},
    )
    hist = client.get(f"/ops/recommendations/{rid}/actions/history", headers=_auth(admin))
    seq = [x["decision_type"] for x in hist.json()]
    assert seq.count("previewed") >= 1
    assert seq.count("confirmed") >= 1
    assert seq.count("executed") >= 1


def test_preview_does_not_resolve_recommendation(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.ledger_service import ensure_default_inventory_locations
    from backend.app.modules.inventory.models import StockItem

    db = SessionLocal()
    try:
        ensure_default_inventory_locations(db)
        sku = f"SKU-{uuid.uuid4().hex[:6]}"
        item = StockItem(sku=sku, name="N", unit_cost=1.0, on_hand_quantity=1.0, reserved_quantity=0.0)
        db.add(item)
        db.flush()
        iid = item.id
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="stock_shortage_reserved",
                category="inventory_risk",
                severity="critical",
                confidence="high",
                title="t",
                summary="s",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=iid,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "mark_for_stock_review"},
    )
    db = SessionLocal()
    try:
        r = db.get(OperationalRecommendation, rid)
        assert r.status == "open"
        assert r.resolved_at is None
    finally:
        db.close()


def test_resolve_defect_auto_resolves_recommendation(client):
    admin = _admin_token(client)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.vehicles.models import VehicleDefect

    vid = f"v-{uuid.uuid4().hex[:6]}"
    db = SessionLocal()
    try:
        did = str(uuid.uuid4())
        db.add(
            VehicleDefect(
                id=did,
                vehicle_id=vid,
                defect_type="tyre",
                severity="critical",
                title="Tyre",
                status="open",
                reported_at=datetime.now(timezone.utc),
            )
        )
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="vehicle_critical_defect_open",
                category="vehicle_readiness",
                severity="critical",
                confidence="high",
                title="def",
                summary="s",
                detail_json=json.dumps({"vehicle_id": vid, "defect_id": did}),
                entity_type="vehicle",
                entity_id=vid,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.post(
        f"/ops/recommendations/{rid}/actions/preview",
        headers=_auth(admin),
        json={"action_type": "resolve_defect", "input_payload": {"vehicle_id": vid, "defect_id": did}},
    )
    ex = client.post(
        f"/ops/recommendations/{rid}/actions/confirm",
        headers=_auth(admin),
        json={
            "action_type": "resolve_defect",
            "confirmed": True,
            "input_payload": {"vehicle_id": vid, "defect_id": did, "resolution_notes": "Fixed"},
        },
    )
    assert ex.status_code == 200, ex.text

    db = SessionLocal()
    try:
        r = db.get(OperationalRecommendation, rid)
        assert r.status == "resolved"
        d = db.get(VehicleDefect, did)
        assert d.status == "resolved"
    finally:
        db.close()
