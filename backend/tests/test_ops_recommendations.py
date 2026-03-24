"""
Operational intelligence: deterministic recommendation engine, API, dedupe, lifecycle.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services import recommendation_engine as rec_engine


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


def _customer_id(client, admin_token: str) -> str:
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin_token),
        json={"name": f"L {uuid.uuid4().hex[:6]}", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201, lead.text
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin_token),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200, conv.text
    return conv.json()["customer"]["id"]


@pytest.fixture(autouse=True)
def _zero_recommendation_cooldowns(monkeypatch):
    """Keep tests fast: by default no dismiss/resolve cooldown on new open rows."""
    monkeypatch.setattr("backend.app.core.config.settings.PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS", 0.0)
    monkeypatch.setattr("backend.app.core.config.settings.PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS", 0.0)


@pytest.fixture(autouse=True)
def _clear_operational_recommendations():
    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import (
        OperationalRecommendation,
        RecommendationOccurrenceEvent,
        RecommendationSuppression,
    )

    db = SessionLocal()
    try:
        db.query(RecommendationOccurrenceEvent).delete()
        db.query(RecommendationSuppression).delete()
        db.query(OperationalRecommendation).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_sla_imminent_generates_sla_recommendation(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    pol = client.post(
        "/sla/policies",
        headers=_auth(admin_token),
        json={
            "name": f"Pol {uuid.uuid4().hex[:6]}",
            "priority": "routine",
            "response_target_minutes": 120,
            "attendance_target_minutes": 60,
            "resolution_target_minutes": 480,
            "warning_threshold_percent_json": '{"attendance": 80}',
        },
    )
    assert pol.status_code == 201, pol.text
    policy_id = pol.json()["id"]

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "1 SLA Way", "site_latitude": 51.5, "site_longitude": -0.1},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.sla_policy_id = policy_id
        j.status = "dispatched"
        j.created_at = datetime.now(timezone.utc) - timedelta(minutes=50)
        j.on_site_at = None
        db.commit()
        rec_engine.scan_job_recommendations(db, job_id=job_id)
        row = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"sla-risk:job:{job_id}")
            .first()
        )
        assert row is not None
        assert row.category == "sla_risk"
        assert row.status == "open"
    finally:
        db.close()


def test_stale_telemetry_on_active_assignment_generates_dispatch_risk(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "2 Tel Way", "site_latitude": 51.5, "site_longitude": -0.1},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.tracking.models import EngineerLatestLocation

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        j = db.get(Job, job_id)
        assert j
        j.status = "dispatched"
        j.assigned_engineer_id = eng.id
        db.commit()

        stale_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        row = db.get(EngineerLatestLocation, eng.id)
        if row:
            row.last_latitude = 51.5
            row.last_longitude = -0.1
            row.last_occurred_at = stale_at
            row.last_received_at = stale_at
            row.freshness_status = "stale"
        else:
            db.add(
                EngineerLatestLocation(
                    engineer_id=eng.id,
                    last_latitude=51.5,
                    last_longitude=-0.1,
                    last_occurred_at=stale_at,
                    last_received_at=stale_at,
                    freshness_status="stale",
                )
            )
        db.commit()

        rec_engine.scan_job_recommendations(db, job_id=job_id)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"dispatch:stale-telemetry:job:{job_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "dispatch_risk"
    finally:
        db.close()


def test_low_stock_reserved_generates_inventory_recommendation(client):
    admin_token = _admin_token(client)
    _ = admin_token

    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.models import StockItem

    db = SessionLocal()
    try:
        sku = f"SKU-OPS-{uuid.uuid4().hex[:8]}"
        item = StockItem(sku=sku, name="Test part", on_hand_quantity=1.0, reserved_quantity=5.0)
        db.add(item)
        db.commit()
        db.refresh(item)

        rec_engine.scan_inventory_recommendations(db)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.entity_id == item.id)
            .filter(rec_engine.OperationalRecommendation.category == "inventory_risk")
            .first()
        )
        assert rec is not None
        assert "shortage" in rec.recommendation_key
    finally:
        db.close()


def test_completed_job_high_material_variance_generates_costing_recommendation(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "3 Cost Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.add(
            JobCostSnapshot(
                job_id=job_id,
                estimated_material_cost=100.0,
                reserved_material_cost=100.0,
                actual_material_cost=140.0,
                estimated_material_qty=1.0,
                reserved_material_qty=1.0,
                actual_material_qty=1.0,
                material_cost_variance_vs_estimate=40.0,
                material_cost_variance_vs_reserved=40.0,
                labour_seconds=0,
                labour_hours=0.0,
                labour_cost=0.0,
            )
        )
        db.commit()

        rec_engine.scan_job_recommendations(db, job_id=job_id)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"costing:material-variance:job:{job_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "costing_variance"
    finally:
        db.close()


def test_invoice_missing_snapshot_and_compliance_generates_invoice_hold(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "4 Inv Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=10.0,
            materials_total=0.0,
            grand_total=10.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()

        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"invoice:hold:{inv.id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "invoice_hold"
    finally:
        db.close()


def test_contract_nearing_expiry_generates_contract_attention(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)
    now = datetime.now(timezone.utc)

    cres = client.post(
        "/contracts",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "name": "Near end",
            "term_start_at": (now - timedelta(days=30)).isoformat(),
            "term_end_at": (now + timedelta(days=20)).isoformat(),
            "billing_frequency": "monthly",
            "ppm_interval_days": 90,
            "next_ppm_due_at": (now + timedelta(days=60)).isoformat(),
            "sla_response_minutes": 60,
            "sla_attendance_minutes": 240,
            "sla_completion_minutes": 720,
        },
    )
    assert cres.status_code == 201, cres.text
    contract_id = cres.json()["id"]

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rec_engine.scan_contract_recommendations(db, contract_id=contract_id)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"contract:expiry:{contract_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "contract_attention"
    finally:
        db.close()


def test_repeated_sla_breaches_on_contract_generates_recommendation(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)
    now = datetime.now(timezone.utc)

    cres = client.post(
        "/contracts",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "name": "SLA heavy",
            "term_start_at": (now - timedelta(days=400)).isoformat(),
            "term_end_at": (now + timedelta(days=365)).isoformat(),
            "billing_frequency": "monthly",
            "ppm_interval_days": 90,
            "next_ppm_due_at": now.isoformat(),
            "sla_response_minutes": 60,
            "sla_attendance_minutes": 240,
            "sla_completion_minutes": 0,
        },
    )
    assert cres.status_code == 201, cres.text
    contract_id = cres.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        for _ in range(3):
            j = Job(
                customer_id=cid,
                contract_id=contract_id,
                address="SLA breach seed",
                status="completed",
                created_at=now - timedelta(days=2),
                resolved_at=now - timedelta(days=1),
            )
            db.add(j)
        db.commit()

        rec_engine.scan_contract_recommendations(db, contract_id=contract_id)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"contract:sla-breaches:{contract_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "contract_attention"
    finally:
        db.close()


def test_ppm_overdue_generates_recommendation(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)
    now = datetime.now(timezone.utc)

    cres = client.post(
        "/contracts",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "name": "PPM ctr",
            "term_start_at": (now - timedelta(days=60)).isoformat(),
            "term_end_at": (now + timedelta(days=300)).isoformat(),
            "billing_frequency": "monthly",
            "ppm_interval_days": 90,
            "next_ppm_due_at": now.isoformat(),
            "sla_response_minutes": 60,
            "sla_attendance_minutes": 240,
            "sla_completion_minutes": 720,
        },
    )
    assert cres.status_code == 201, cres.text
    contract_id = cres.json()["id"]

    site = client.post(
        "/sites",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "site_code": f"S-{uuid.uuid4().hex[:6]}",
            "name": "Main",
            "address_line1": "1 Site St",
        },
    )
    assert site.status_code == 201, site.text
    site_id = site.json()["id"]

    sched = client.post(
        "/ppm/schedules",
        headers=_auth(admin_token),
        json={
            "contract_id": contract_id,
            "site_id": site_id,
            "title": "Annual",
            "frequency_value": 1,
            "frequency_unit": "year",
            "next_due_date": (now - timedelta(days=3)).isoformat(),
        },
    )
    assert sched.status_code == 201, sched.text
    schedule_id = sched.json()["id"]

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rec_engine.scan_contract_recommendations(db, contract_id=contract_id)
        rec = (
            db.query(rec_engine.OperationalRecommendation)
            .filter(rec_engine.OperationalRecommendation.recommendation_key == f"contract:ppm-overdue:{schedule_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "contract_attention"
    finally:
        db.close()


def test_recommendation_scan_dedupes_open_rows(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    pol = client.post(
        "/sla/policies",
        headers=_auth(admin_token),
        json={
            "name": f"Pol {uuid.uuid4().hex[:6]}",
            "priority": "routine",
            "response_target_minutes": 120,
            "attendance_target_minutes": 60,
            "resolution_target_minutes": 480,
            "warning_threshold_percent_json": '{"attendance": 80}',
        },
    )
    assert pol.status_code == 201, pol.text
    policy_id = pol.json()["id"]

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Dedupe Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.ops.models import OperationalRecommendation

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.sla_policy_id = policy_id
        j.status = "dispatched"
        j.created_at = datetime.now(timezone.utc) - timedelta(minutes=50)
        db.commit()

        key = f"sla-risk:job:{job_id}"
        rec_engine.scan_job_recommendations(db, job_id=job_id)
        n1 = db.query(OperationalRecommendation).filter(OperationalRecommendation.recommendation_key == key).count()
        rec_engine.scan_job_recommendations(db, job_id=job_id)
        n2 = db.query(OperationalRecommendation).filter(OperationalRecommendation.recommendation_key == key).count()
        assert n1 == 1 == n2
    finally:
        db.close()


def test_acknowledge_resolve_dismiss_endpoints(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Lifecycle Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice
    from backend.app.modules.ops.models import OperationalRecommendation

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=1.0,
            materials_total=0.0,
            grand_total=1.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()

        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"invoice:hold:{inv.id}")
            .one()
        )
        rid = rec.id

        inv2_job = Job(customer_id=cid, address="J2", status="completed")
        db.add(inv2_job)
        db.commit()
        db.refresh(inv2_job)
        inv2 = Invoice(
            job_id=inv2_job.id,
            currency="GBP",
            status="unpaid",
            labour_total=1.0,
            materials_total=0.0,
            grand_total=1.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv2)
        db.commit()
        db.refresh(inv2)
        ak2: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv2, ak2)
        db.commit()
        rec2 = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"invoice:hold:{inv2.id}")
            .one()
        )
        rid2 = rec2.id
    finally:
        db.close()

    ack = client.post(
        f"/ops/recommendations/{rid}/acknowledge",
        headers=_auth(admin_token),
        json={"notes": "seen"},
    )
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "acknowledged"

    res = client.post(
        f"/ops/recommendations/{rid}/resolve",
        headers=_auth(admin_token),
        json={"notes": "fixed"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "resolved"

    dis = client.post(
        f"/ops/recommendations/{rid2}/dismiss",
        headers=_auth(admin_token),
        json={"notes": "noise"},
    )
    assert dis.status_code == 200, dis.text
    assert dis.json()["status"] == "dismissed"

    summ = client.get("/ops/dashboard/recommendations/summary", headers=_auth(admin_token))
    assert summ.status_code == 200, summ.text
    assert "open_by_severity" in summ.json()


def test_dismiss_cooldown_blocks_reopen_until_manual_reopen(client, monkeypatch):
    monkeypatch.setattr("backend.app.core.config.settings.PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS", 72.0)
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Cooldown Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import recommendation_engine as rec_engine

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=1.0,
            materials_total=0.0,
            grand_total=1.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"invoice:hold:{inv.id}")
            .one()
        )
        rid = rec.id
        key = rec.recommendation_key
    finally:
        db.close()

    dis = client.post(f"/ops/recommendations/{rid}/dismiss", headers=_auth(admin_token), json={})
    assert dis.status_code == 200, dis.text

    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(Invoice.job_id == job_id).one()
        active_keys = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()
        open_n = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == key, OperationalRecommendation.status == "open")
            .count()
        )
        assert open_n == 0
    finally:
        db.close()

    ro = client.post(f"/ops/recommendations/{rid}/reopen", headers=_auth(admin_token), json={"notes": "valid again"})
    assert ro.status_code == 200, ro.text
    assert ro.json()["status"] == "open"


def test_snooze_hides_from_default_list(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Snooze Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import recommendation_engine as rec_engine

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=1.0,
            materials_total=0.0,
            grand_total=1.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"invoice:hold:{inv.id}")
            .one()
        )
        rid = rec.id
    finally:
        db.close()

    sn = client.post(
        f"/ops/recommendations/{rid}/snooze",
        headers=_auth(admin_token),
        json={"hours": 48, "notes": "incident"},
    )
    assert sn.status_code == 200, sn.text

    listed = client.get("/ops/recommendations?status=open", headers=_auth(admin_token))
    assert listed.status_code == 200
    ids_default = {x["id"] for x in listed.json()}
    assert rid not in ids_default

    listed_all = client.get("/ops/recommendations?status=open&include_suppressed=true", headers=_auth(admin_token))
    assert rid in {x["id"] for x in listed_all.json()}


def test_global_suppression_blocks_new_recommendation_row(client):
    admin_token = _admin_token(client)
    cid = _customer_id(client, admin_token)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Sup Way"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import recommendation_engine as rec_engine

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        assert j
        j.status = "completed"
        db.commit()
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=1.0,
            materials_total=0.0,
            grand_total=1.0,
            job_cost_snapshot_id=None,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()
        key = f"invoice:hold:{inv.id}"
        rid = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == key)
            .one()
            .id
        )
    finally:
        db.close()

    sup = client.post(
        "/ops/recommendations/suppressions",
        headers=_auth(admin_token),
        json={"recommendation_key": key, "hours": 24, "notes": "noise"},
    )
    assert sup.status_code == 201, sup.text

    dis = client.post(f"/ops/recommendations/{rid}/dismiss", headers=_auth(admin_token), json={})
    assert dis.status_code == 200, dis.text

    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(Invoice.job_id == job_id).one()
        active_keys: set[str] = set()
        rec_engine.rule_invoice_hold(db, inv, active_keys)
        db.commit()
        open_n = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == key, OperationalRecommendation.status == "open")
            .count()
        )
        assert open_n == 0
    finally:
        db.close()
