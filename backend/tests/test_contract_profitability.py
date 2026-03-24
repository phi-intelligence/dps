"""
Contract profitability, renewal intelligence, snapshots, dashboards, commercial recommendations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _customer_and_contract(client, admin_token: str) -> tuple[str, str]:
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
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    cres = client.post(
        "/contracts",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "name": "Intel Contract",
            "term_start_at": (now - timedelta(days=120)).isoformat(),
            "term_end_at": (now + timedelta(days=200)).isoformat(),
            "billing_frequency": "monthly",
            "ppm_interval_days": 90,
            "next_ppm_due_at": now.isoformat(),
            "sla_response_minutes": 60,
            "sla_attendance_minutes": 240,
            "sla_completion_minutes": 720,
            "contract_value": 50000,
        },
    )
    assert cres.status_code == 201, cres.text
    return cid, cres.json()["id"]


@pytest.fixture()
def admin_token(client):
    return _login(client, username="admin@example.com", password="admin")


def test_contract_profitability_with_invoice_and_snapshot(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "address": "1 Profit St",
            "contract_id": contract_id,
            "work_type": "reactive",
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        j.status = "completed"
        j.resolved_at = now - timedelta(days=5)
        db.add(
            JobCostSnapshot(
                job_id=job_id,
                actual_material_cost=20.0,
                labour_cost=30.0,
                estimated_material_cost=20.0,
                reserved_material_cost=20.0,
                estimated_material_qty=1.0,
                reserved_material_qty=1.0,
                actual_material_qty=1.0,
                material_cost_variance_vs_estimate=0.0,
                material_cost_variance_vs_reserved=0.0,
                labour_seconds=3600,
                labour_hours=1.0,
                completed_at=now - timedelta(days=5),
            )
        )
        db.add(
            Invoice(
                job_id=job_id,
                currency="GBP",
                status="unpaid",
                labour_total=100.0,
                materials_total=50.0,
                grand_total=150.0,
                job_cost_snapshot_id=None,
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get(
        f"/contracts/{contract_id}/profitability",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["margin"]["gross_amount"] > 0
    assert body["revenue"]["invoiced_in_period"] >= 150.0


def test_negative_margin_produces_commercial_recommendation(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "Neg", "contract_id": contract_id, "work_type": "reactive"},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.invoicing.models import Invoice

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        j.status = "completed"
        j.resolved_at = now - timedelta(days=2)
        db.add(
            JobCostSnapshot(
                job_id=job_id,
                actual_material_cost=500.0,
                labour_cost=800.0,
                estimated_material_cost=100.0,
                reserved_material_cost=100.0,
                estimated_material_qty=1.0,
                reserved_material_qty=1.0,
                actual_material_qty=1.0,
                material_cost_variance_vs_estimate=0.0,
                material_cost_variance_vs_reserved=0.0,
                labour_seconds=7200,
                labour_hours=2.0,
                completed_at=now - timedelta(days=2),
            )
        )
        db.add(
            Invoice(
                job_id=job_id,
                currency="GBP",
                status="unpaid",
                labour_total=50.0,
                materials_total=50.0,
                grand_total=100.0,
                job_cost_snapshot_id=None,
            )
        )
        db.commit()
    finally:
        db.close()

    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import contract_profitability_service as cps
    from backend.app.services.contract_commercial_recommendations import register_contract_commercial_recommendations

    db = SessionLocal()
    try:
        scan_now = datetime.now(timezone.utc)
        p = cps.build_contract_profitability(db, contract_id=contract_id, period_window="last_90_days", now=scan_now)
        assert p["margin"]["gross_amount"] < 0, p
        active: set[str] = set()
        register_contract_commercial_recommendations(db, active, now=scan_now)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"commercial:negative-margin:{contract_id}")
            .first()
        )
        assert rec is not None
        assert rec.category == "contract_attention"
    finally:
        db.close()


def test_renewal_risk_near_expiry_poor_health(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.models import Contract

    db = SessionLocal()
    try:
        c = db.get(Contract, contract_id)
        c.term_end_at = datetime.now(timezone.utc) + timedelta(days=20)
        db.commit()
    finally:
        db.close()

    r = client.get(
        f"/contracts/{contract_id}/renewal-intelligence",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    ren = r.json()["renewal"]
    assert ren["review_due"] is True
    assert ren["days_to_term_end"] is not None
    assert ren["days_to_term_end"] <= 30


def test_high_reactive_burden_in_performance_and_recommendation(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    for i in range(4):
        job = client.post(
            "/jobs",
            headers=_auth(admin_token),
            json={"customer_id": cid, "address": f"R{i}", "contract_id": contract_id, "work_type": "reactive"},
        )
        assert job.status_code == 201, job.text

    jobp = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "P1", "contract_id": contract_id, "work_type": "planned_maintenance"},
    )
    assert jobp.status_code == 201, jobp.text

    perf = client.get(
        f"/contracts/{contract_id}/performance",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert perf.status_code == 200, perf.text
    assert perf.json()["jobs"]["reactive_created_in_period"] >= 4
    assert perf.json()["jobs"]["planned_created_in_period"] >= 1

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import contract_profitability_service as cps
    from backend.app.services.contract_commercial_recommendations import register_contract_commercial_recommendations

    db = SessionLocal()
    try:
        scan_now = datetime.now(timezone.utc)
        p = cps.build_contract_profitability(db, contract_id=contract_id, period_window="last_90_days", now=scan_now)
        assert p["jobs"]["reactive_created_in_period"] >= 4, p["jobs"]
        assert p["jobs"]["planned_created_in_period"] >= 1, p["jobs"]
        active: set[str] = set()
        register_contract_commercial_recommendations(db, active, now=scan_now)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"commercial:reactive-burden:{contract_id}")
            .first()
        )
        assert rec is not None
    finally:
        db.close()


def test_site_burden_identifies_top_cost_site(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    s1 = client.post(
        "/sites",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "site_code": f"A-{uuid.uuid4().hex[:4]}",
            "name": "Site A",
            "address_line1": "A",
        },
    )
    assert s1.status_code == 201, s1.text
    site_a = s1.json()["id"]
    s2 = client.post(
        "/sites",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "site_code": f"B-{uuid.uuid4().hex[:4]}",
            "name": "Site B",
            "address_line1": "B",
        },
    )
    assert s2.status_code == 201, s2.text
    site_b = s2.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        for site_id, mat, lab in [(site_a, 900.0, 100.0), (site_b, 50.0, 50.0)]:
            j = Job(
                customer_id=cid,
                contract_id=contract_id,
                site_id=site_id,
                address="x",
                status="completed",
                work_type="reactive",
                resolved_at=now - timedelta(days=3),
            )
            db.add(j)
            db.flush()
            db.add(
                JobCostSnapshot(
                    job_id=j.id,
                    actual_material_cost=mat,
                    labour_cost=lab,
                    estimated_material_cost=mat,
                    reserved_material_cost=mat,
                    estimated_material_qty=1.0,
                    reserved_material_qty=1.0,
                    actual_material_qty=1.0,
                    material_cost_variance_vs_estimate=0.0,
                    material_cost_variance_vs_reserved=0.0,
                    labour_seconds=3600,
                    labour_hours=1.0,
                    completed_at=now - timedelta(days=3),
                )
            )
        db.commit()
    finally:
        db.close()

    r = client.get(
        f"/contracts/{contract_id}/sites/performance",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    sites = r.json()["site_burden"]
    top = next(s for s in sites if s.get("site_id") == site_a)
    assert top["total_cost"] > 500


def test_asset_burden_repeat_reactive(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    ast = client.post(
        "/assets",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "contract_id": contract_id,
            "asset_type": "boiler",
            "name": "Boiler X",
            "location_address": "1",
        },
    )
    assert ast.status_code == 201, ast.text
    aid = ast.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        for _ in range(3):
            j = Job(
                customer_id=cid,
                contract_id=contract_id,
                asset_id=aid,
                address="a",
                status="created",
                work_type="reactive",
            )
            db.add(j)
        db.commit()
    finally:
        db.close()

    r = client.get(
        f"/contracts/{contract_id}/assets/burden",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    assets = [a for a in r.json()["asset_burden"] if a.get("asset_id") == aid]
    assert len(assets) == 1
    assert assets[0]["reactive_jobs"] == 3

    from backend.app.db.session import SessionLocal
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import contract_profitability_service as cps
    from backend.app.services.contract_commercial_recommendations import register_contract_commercial_recommendations

    db = SessionLocal()
    try:
        scan_now = datetime.now(timezone.utc)
        p = cps.build_contract_profitability(db, contract_id=contract_id, period_window="last_90_days", now=scan_now)
        assert any(
            a.get("asset_id") == aid and int(a.get("reactive_jobs", 0) or 0) >= 3 for a in p.get("asset_burden", [])
        ), p.get("asset_burden")
        active: set[str] = set()
        register_contract_commercial_recommendations(db, active, now=scan_now)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"commercial:asset-hotspot:{contract_id}:{aid}")
            .first()
        )
        assert rec is not None
    finally:
        db.close()


def test_missing_costing_snapshot_surfaces_warning(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    now = datetime.now(timezone.utc)

    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={"customer_id": cid, "address": "No snap", "contract_id": contract_id},
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        j = db.get(Job, job_id)
        j.status = "completed"
        j.resolved_at = now - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    p = client.get(
        f"/contracts/{contract_id}/performance",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert p.status_code == 200, p.text
    assert p.json()["data_completeness"]["completed_jobs_missing_snapshot_in_period"] >= 1
    assert any("missing_cost_snapshot" in w for w in p.json()["warnings"])


def test_snapshot_generation_and_list(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    rs = client.post(
        "/contracts/performance/run-snapshot",
        headers=_auth(admin_token),
        params={"contract_id": contract_id, "period_window": "last_90_days"},
    )
    assert rs.status_code == 200, rs.text
    assert "snapshot_id" in rs.json()

    lst = client.get(
        f"/contracts/{contract_id}/performance/snapshots",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert lst.status_code == 200, lst.text
    assert len(lst.json()) >= 1
    assert lst.json()[0]["contract_id"] == contract_id


def test_dashboard_profitability_sorting(client, admin_token):
    r = client.get(
        "/contracts/dashboard/profitability",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days", "limit": 5},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "lowest_margin_contracts" in body
    assert "highest_margin_contracts" in body
    lows = body["lowest_margin_contracts"]
    if len(lows) >= 2:
        assert lows[0]["margin_percent"] <= lows[1]["margin_percent"]


def test_dashboard_renewals_surfaces_at_risk(client, admin_token):
    cid, contract_id = _customer_and_contract(client, admin_token)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.models import Contract

    db = SessionLocal()
    try:
        c = db.get(Contract, contract_id)
        c.term_end_at = datetime.now(timezone.utc) + timedelta(days=15)
        db.commit()
    finally:
        db.close()

    r = client.get(
        "/contracts/dashboard/renewals",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    ids = {x["contract_id"] for x in r.json()["contracts_with_review_due"]}
    assert contract_id in ids
