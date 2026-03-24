"""
Low-risk automation: draft artifacts, internal tasks, dedupe, audit runs (no silent finals).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.modules.automation.models import AutomationRun, InternalFollowUpTask
from backend.app.modules.contracts.review_models import ContractRepricingProposal
from backend.app.modules.inventory.models import StockItem
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.ops.models import OperationalRecommendation


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


@pytest.fixture(autouse=True)
def _clear_automation_tables():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.query(InternalFollowUpTask).delete()
        db.query(AutomationRun).delete()
        db.commit()
    finally:
        db.close()
    yield


def _stock_item(db) -> StockItem:
    sku = f"SKU-{uuid.uuid4().hex[:8]}"
    item = StockItem(
        sku=sku,
        name="Test part",
        unit_of_measure="ea",
        unit_cost=10.0,
        on_hand_quantity=0.0,
        reserved_quantity=5.0,
        reorder_point_quantity=2.0,
    )
    db.add(item)
    db.flush()
    return item


def test_inventory_risk_creates_draft_transfer_not_final_ship(client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.models import StockTransfer
    from backend.app.services import low_risk_automation_service as lra

    admin = _admin_token(client)
    db = SessionLocal()
    try:
        item = _stock_item(db)
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="inventory_risk",
                category="inventory",
                severity="high",
                confidence="high",
                title="Shortage",
                summary="Need stock",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=item.id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_INVENTORY_TRANSFER_DRAFT},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "draft_created"
    tid = body["payload"]["stock_transfer_id"]
    db = SessionLocal()
    try:
        t = db.get(StockTransfer, tid)
        assert t is not None
        assert t.status == "draft"
    finally:
        db.close()


def test_invoice_hold_rec_creates_finance_review_task(client):
    from backend.app.db.session import SessionLocal

    admin = _admin_token(client)
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"fin_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    job_res = client.post(
        "/jobs",
        headers=_auth(admin),
        json={"customer_id": cid, "address": "1 Test St"},
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]

    db = SessionLocal()
    try:
        inv = Invoice(job_id=job_id, currency="GBP", status="unpaid")
        db.add(inv)
        db.flush()
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="invoice_release_hold",
                category="invoice",
                severity="high",
                confidence="high",
                title="Hold",
                summary="Invoice blocked",
                detail_json="{}",
                entity_type="invoice",
                entity_id=inv.id,
                related_invoice_id=inv.id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
        inv_id = inv.id
    finally:
        db.close()

    res = client.post(f"/automation/run-for-recommendation/{rid}", headers=_auth(admin), json={})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "draft_created"
    task_id = res.json()["payload"]["task_id"]

    db = SessionLocal()
    try:
        task = db.get(InternalFollowUpTask, task_id)
        assert task is not None
        assert task.task_type == "finance_review"
        assert task.related_entity_id == inv_id
    finally:
        db.close()


def test_contract_attention_creates_contract_review_task(client):
    from backend.app.db.session import SessionLocal

    admin = _admin_token(client)
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin),
        json={"name": "L", "email": f"ctr_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"Ctr {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 10000.0,
        },
    )
    assert ctr.status_code == 201, ctr.text
    contract_id = ctr.json()["id"]

    db = SessionLocal()
    try:
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_attention",
                category="contract",
                severity="medium",
                confidence="high",
                title="Attention",
                summary="Review contract",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.post(f"/automation/run-for-recommendation/{rid}", headers=_auth(admin), json={})
    assert res.status_code == 200, res.text
    payload = res.json()["payload"]
    assert payload.get("task_id")
    assert payload.get("contract_review_id")

    db = SessionLocal()
    try:
        task = db.get(InternalFollowUpTask, payload["task_id"])
        assert task.task_type == "contract_review"
        assert task.related_entity_id == contract_id
    finally:
        db.close()


def test_proposal_rejected_creates_follow_up_task(client):
    from backend.tests.test_customer_repricing_portal import _customer_contract_and_repricing_proposal

    admin = _admin_token(client)
    _email, _cust_id, contract_id, _rr, proposal_id, pw = _customer_contract_and_repricing_proposal(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text
    client_token = _login(client, username=_email, password=pw)

    p = client.post(
        f"/portal/me/repricing-proposals/{proposal_id}/respond",
        headers=_auth(client_token),
        json={"response_type": "rejected", "notes": "No thanks"},
    )
    assert p.status_code == 200, p.text

    db_session = __import__("backend.app.db.session", fromlist=["SessionLocal"]).SessionLocal()
    try:
        tasks = (
            db_session.query(InternalFollowUpTask)
            .filter(
                InternalFollowUpTask.related_entity_type == "repricing_proposal",
                InternalFollowUpTask.related_entity_id == proposal_id,
            )
            .all()
        )
        assert any(t.task_type == "customer_follow_up" for t in tasks)
    finally:
        db_session.close()


def test_proposal_counter_requested_creates_repricing_follow_up(client):
    from backend.tests.test_customer_repricing_portal import _customer_contract_and_repricing_proposal

    admin = _admin_token(client)
    _email, _cust_id, _contract_id, _rr, proposal_id, pw = _customer_contract_and_repricing_proposal(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text
    client_token = _login(client, username=_email, password=pw)

    p = client.post(
        f"/portal/me/repricing-proposals/{proposal_id}/respond",
        headers=_auth(client_token),
        json={"response_type": "counter_requested", "notes": "Lower rate"},
    )
    assert p.status_code == 200, p.text

    db_session = __import__("backend.app.db.session", fromlist=["SessionLocal"]).SessionLocal()
    try:
        tasks = (
            db_session.query(InternalFollowUpTask)
            .filter(
                InternalFollowUpTask.related_entity_type == "repricing_proposal",
                InternalFollowUpTask.related_entity_id == proposal_id,
                InternalFollowUpTask.task_type == "repricing_follow_up",
            )
            .all()
        )
        assert len(tasks) >= 1
    finally:
        db_session.close()


def test_duplicate_automation_skips_second_run(client):
    from backend.app.db.session import SessionLocal
    from backend.app.services import low_risk_automation_service as lra

    admin = _admin_token(client)
    db = SessionLocal()
    try:
        item = _stock_item(db)
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="inventory_risk",
                category="inventory",
                severity="high",
                confidence="high",
                title="Shortage",
                summary="Need stock",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=item.id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    r1 = client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_INVENTORY_PO_DRAFT},
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "draft_created"
    r2 = client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_INVENTORY_PO_DRAFT},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "skipped"


def test_automation_dashboard_reports_skipped_and_drafts(client):
    from backend.app.db.session import SessionLocal

    admin = _admin_token(client)
    db = SessionLocal()
    try:
        item = _stock_item(db)
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="inventory_risk",
                category="inventory",
                severity="high",
                confidence="high",
                title="Shortage",
                summary="Need stock",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=item.id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    from backend.app.services import low_risk_automation_service as lra

    client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_INVENTORY_TRANSFER_DRAFT},
    )
    client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_INVENTORY_TRANSFER_DRAFT},
    )

    dash = client.get("/automation/dashboard/summary", headers=_auth(admin))
    assert dash.status_code == 200
    body = dash.json()
    assert body["by_status"].get("draft_created", 0) >= 1
    assert body["by_status"].get("skipped", 0) >= 1


def test_task_completion_is_auditable(client):
    from backend.app.db.session import SessionLocal
    from backend.app.services import low_risk_automation_service as lra

    admin = _admin_token(client)
    db = SessionLocal()
    try:
        item = _stock_item(db)
        rid = str(uuid.uuid4())
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="parts_reconciliation_block",
                category="inventory",
                severity="medium",
                confidence="high",
                title="Reco",
                summary="Reconcile",
                detail_json="{}",
                entity_type="stock_item",
                entity_id=item.id,
                status="open",
                recommendation_key=f"test:{rid}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    run = client.post(
        f"/automation/run-for-recommendation/{rid}",
        headers=_auth(admin),
        json={"automation_type": lra.AUTOMATION_STOCK_REVIEW_TASK},
    )
    assert run.status_code == 200
    task_id = run.json()["payload"]["task_id"]

    done = client.post(
        f"/tasks/{task_id}/complete",
        headers=_auth(admin),
        json={"completion_notes": "Reviewed and cleared"},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None
    assert "Reviewed and cleared" in (done.json().get("notes") or "")

    single = client.get(f"/tasks/{task_id}", headers=_auth(admin))
    assert single.status_code == 200
    assert single.json()["status"] == "completed"


def test_viewed_proposal_follow_up_manual_trigger(client):
    """Operator-run check for viewed-but-silent proposals (threshold in request body)."""
    from backend.tests.test_customer_repricing_portal import _customer_contract_and_repricing_proposal

    admin = _admin_token(client)
    email, _cust_id, _contract_id, _rr, proposal_id, pw = _customer_contract_and_repricing_proposal(client, admin)
    rel = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text
    ctok = _login(client, username=email, password=pw)
    view = client.get(f"/portal/me/repricing-proposals/{proposal_id}", headers=_auth(ctok))
    assert view.status_code == 200, view.text

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        prop = db.get(ContractRepricingProposal, proposal_id)
        assert prop is not None
        prop.customer_viewed_at = datetime.now(timezone.utc) - timedelta(days=30)
        prop.customer_release_status = "viewed"
        db.add(prop)
        db.commit()
    finally:
        db.close()

    res = client.post(
        f"/automation/run-for-proposal/{proposal_id}",
        headers=_auth(admin),
        json={"kind": "viewed_no_response_follow_up", "viewed_no_response_days": 7},
    )
    assert res.status_code == 200
    assert res.json() is not None
    assert res.json()["status"] == "draft_created"
