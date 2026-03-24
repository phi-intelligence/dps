from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _new_customer(client, admin_token: str) -> str:
    customer_email = f"client-{uuid.uuid4().hex[:6]}@example.com"
    lead_name = f"Lead {uuid.uuid4().hex[:8]}"
    lead_res = client.post(
        "/crm/leads",
        headers=_auth_headers(admin_token),
        json={"name": lead_name, "email": customer_email},
    )
    assert lead_res.status_code == 201, lead_res.text
    lead_id = lead_res.json()["id"]
    convert_res = client.post(
        f"/crm/leads/{lead_id}/convert",
        headers=_auth_headers(admin_token),
        json={"name": f"{lead_name} Customer", "email": customer_email},
    )
    assert convert_res.status_code == 200, convert_res.text
    return convert_res.json()["customer"]["id"]


def test_ppm_generation_creates_planned_maintenance_job_linked(client):
    """Test 1: site + asset + contract + quarterly PPM → one planned_maintenance job."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    site_res = client.post(
        "/sites",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_code": f"S-{uuid.uuid4().hex[:6]}",
            "name": "Main plant",
            "address_line1": "1 Industrial Way",
            "city": "London",
            "postcode": "E1 1AA",
            "latitude": 51.5,
            "longitude": -0.1,
        },
    )
    assert site_res.status_code == 201, site_res.text
    site_id = site_res.json()["id"]

    now = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
    contract_res = client.post(
        "/contracts",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "name": "Full maintenance",
            "contract_code": f"C-{uuid.uuid4().hex[:6]}",
            "contract_type": "full_maintenance",
            "term_start_at": (now - timedelta(days=30)).isoformat(),
            "term_end_at": (now + timedelta(days=365)).isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "ppm_interval_days": 90,
        },
    )
    assert contract_res.status_code == 201, contract_res.text
    contract_id = contract_res.json()["id"]

    asset_res = client.post(
        "/assets",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "contract_id": contract_id,
            "asset_type": "boiler",
            "name": "Plant boiler",
            "location_address": "1 Industrial Way",
        },
    )
    assert asset_res.status_code == 201, asset_res.text
    asset_id = asset_res.json()["id"]

    sched_res = client.post(
        "/ppm/schedules",
        headers=h,
        json={
            "contract_id": contract_id,
            "site_id": site_id,
            "asset_id": asset_id,
            "title": "Quarterly service",
            "frequency_value": 3,
            "frequency_unit": "month",
            "next_due_date": now.isoformat(),
            "planning_window_days": 30,
        },
    )
    assert sched_res.status_code == 201, sched_res.text
    schedule_id = sched_res.json()["id"]

    gen_res = client.post(
        "/ppm/run-generation",
        headers=h,
        json={"run_date": now.isoformat(), "planning_window_days": 30},
    )
    assert gen_res.status_code == 200, gen_res.text
    created = gen_res.json()["created_job_ids"]
    assert len(created) == 1, gen_res.text

    job_res = client.get(f"/jobs/{created[0]}", headers=h)
    assert job_res.status_code == 200, job_res.text
    body = job_res.json()
    assert body["work_type"] == "planned_maintenance"
    assert body["contract_id"] == contract_id
    assert body["site_id"] == site_id
    assert body["asset_id"] == asset_id
    assert body["ppm_schedule_id"] == schedule_id


def test_ppm_generation_twice_no_duplicate_for_same_anchor(client):
    """Test 2: second run does not create another job for the same due anchor."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    site_res = client.post(
        "/sites",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_code": f"S-{uuid.uuid4().hex[:6]}",
            "name": "Site B",
            "address_line1": "2 Road",
        },
    )
    assert site_res.status_code == 201, site_res.text
    site_id = site_res.json()["id"]

    run_day = datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc)
    contract_res = client.post(
        "/contracts",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "name": "Contract B",
            "contract_code": f"C-{uuid.uuid4().hex[:6]}",
            "contract_type": "ppm_only",
            "term_start_at": (run_day - timedelta(days=10)).isoformat(),
            "term_end_at": (run_day + timedelta(days=200)).isoformat(),
            "next_ppm_due_at": run_day.isoformat(),
            "ppm_interval_days": 90,
        },
    )
    assert contract_res.status_code == 201, contract_res.text
    contract_id = contract_res.json()["id"]

    client.post(
        "/ppm/schedules",
        headers=h,
        json={
            "contract_id": contract_id,
            "site_id": site_id,
            "asset_id": None,
            "title": "Site walkdown",
            "frequency_value": 1,
            "frequency_unit": "month",
            "next_due_date": run_day.isoformat(),
            "planning_window_days": 14,
        },
    )

    g1 = client.post(
        "/ppm/run-generation",
        headers=h,
        json={"run_date": run_day.isoformat(), "planning_window_days": 14},
    )
    assert g1.status_code == 200, g1.text
    assert len(g1.json()["created_job_ids"]) == 1

    g2 = client.post(
        "/ppm/run-generation",
        headers=h,
        json={"run_date": run_day.isoformat(), "planning_window_days": 14},
    )
    assert g2.status_code == 200, g2.text
    assert g2.json()["created_job_ids"] == []


def test_reactive_job_inherits_contract_and_sla_context(client):
    """Test 3: reactive job on contracted asset picks up contract + SLA policy."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    site_res = client.post(
        "/sites",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_code": f"S-{uuid.uuid4().hex[:6]}",
            "name": "Tower A",
            "address_line1": "10 High St",
        },
    )
    site_id = site_res.json()["id"]

    pol_res = client.post(
        "/sla/policies",
        headers=h,
        json={
            "name": "Urgent care",
            "priority": "urgent",
            "response_target_minutes": 30,
            "attendance_target_minutes": 120,
            "resolution_target_minutes": 480,
        },
    )
    assert pol_res.status_code == 201, pol_res.text
    policy_id = pol_res.json()["id"]

    now = datetime.now(timezone.utc)
    contract_res = client.post(
        "/contracts",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "name": "Reactive bundle",
            "contract_code": f"C-{uuid.uuid4().hex[:6]}",
            "contract_type": "ppm_plus_reactive",
            "default_sla_policy_id": policy_id,
            "term_start_at": (now - timedelta(days=1)).isoformat(),
            "term_end_at": (now + timedelta(days=365)).isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "ppm_interval_days": 90,
        },
    )
    contract_id = contract_res.json()["id"]

    asset_res = client.post(
        "/assets",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "contract_id": contract_id,
            "asset_type": "pump",
            "name": "Circ pump",
            "location_address": "10 High St",
        },
    )
    asset_id = asset_res.json()["id"]

    job_res = client.post(
        "/jobs",
        headers=h,
        json={
            "customer_id": customer_id,
            "asset_id": asset_id,
            "address": "10 High St",
        },
    )
    assert job_res.status_code == 201, job_res.text
    j = job_res.json()
    assert j["contract_id"] == contract_id
    assert j["site_id"] == site_id
    assert j["sla_policy_id"] == policy_id
    assert j["sla_priority"] == "urgent"
    assert j["covered_under_contract"] is True
    assert j["work_type"] == "reactive"


def test_sla_attendance_breach_computed(client):
    """Test 4: late on_site breaches attendance target."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    pol_res = client.post(
        "/sla/policies",
        headers=h,
        json={
            "name": "Tight attendance",
            "priority": "routine",
            "response_target_minutes": 9999,
            "attendance_target_minutes": 60,
            "resolution_target_minutes": 9999,
        },
    )
    policy_id = pol_res.json()["id"]

    t0 = datetime(2026, 2, 1, 8, 0, tzinfo=timezone.utc)
    job_res = client.post(
        "/jobs",
        headers=h,
        json={"customer_id": customer_id, "address": "Nowhere"},
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        row = db.get(Job, job_id)
        assert row is not None
        row.sla_policy_id = policy_id
        row.created_at = t0
        row.on_site_at = t0 + timedelta(minutes=500)
        db.commit()
    finally:
        db.close()

    sla_res = client.get(f"/jobs/{job_id}/sla", headers=h)
    assert sla_res.status_code == 200, sla_res.text
    body = sla_res.json()
    assert body["attendance_breached"] is True
    assert "attendance_breach" in body["sla_status_summary"]


def test_certificate_visible_in_asset_history(client):
    """Test 5: certificate on asset-linked job appears in asset history."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    site_res = client.post(
        "/sites",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_code": f"S-{uuid.uuid4().hex[:6]}",
            "name": "Cert site",
            "address_line1": "5 Cert Lane",
        },
    )
    site_id = site_res.json()["id"]

    now = datetime.now(timezone.utc)
    contract_res = client.post(
        "/contracts",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "name": "Cert contract",
            "contract_code": f"C-{uuid.uuid4().hex[:6]}",
            "contract_type": "compliance_only",
            "term_start_at": (now - timedelta(days=1)).isoformat(),
            "term_end_at": (now + timedelta(days=100)).isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "ppm_interval_days": 90,
        },
    )
    contract_id = contract_res.json()["id"]

    asset_res = client.post(
        "/assets",
        headers=h,
        json={
            "customer_id": customer_id,
            "site_id": site_id,
            "contract_id": contract_id,
            "asset_type": "electrical_panel",
            "name": "LV panel",
            "location_address": "5 Cert Lane",
        },
    )
    asset_id = asset_res.json()["id"]

    job_res = client.post(
        "/jobs",
        headers=h,
        json={
            "customer_id": customer_id,
            "asset_id": asset_id,
            "address": "5 Cert Lane",
        },
    )
    job_id = job_res.json()["id"]

    cert_res = client.post(
        "/compliance/certificates/generate",
        headers=h,
        json={"job_id": job_id, "certificate_type": "eicr"},
    )
    assert cert_res.status_code == 201, cert_res.text
    cert_id = cert_res.json()["id"]

    hist_res = client.get(f"/assets/{asset_id}/history", headers=h)
    assert hist_res.status_code == 200, hist_res.text
    kinds = {e["kind"] for e in hist_res.json()["entries"]}
    assert "certificate" in kinds
    cert_entries = [e for e in hist_res.json()["entries"] if e["kind"] == "certificate"]
    assert any(e["id"] == cert_id for e in cert_entries)


def test_contract_sla_performance_summary(client):
    """Test 6: contract SLA performance returns useful aggregates."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    now = datetime.now(timezone.utc)
    contract_res = client.post(
        "/contracts",
        headers=h,
        json={
            "customer_id": customer_id,
            "name": "Perf contract",
            "contract_code": f"C-{uuid.uuid4().hex[:6]}",
            "contract_type": "labour_only",
            "term_start_at": (now - timedelta(days=1)).isoformat(),
            "term_end_at": (now + timedelta(days=200)).isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "ppm_interval_days": 90,
        },
    )
    contract_id = contract_res.json()["id"]

    client.post(
        "/jobs",
        headers=h,
        json={"customer_id": customer_id, "address": "A", "contract_id": contract_id},
    )

    perf = client.get(f"/contracts/{contract_id}/sla-performance", headers=h)
    assert perf.status_code == 200, perf.text
    data = perf.json()
    assert data["contract_id"] == contract_id
    assert "jobs_considered" in data
    assert "open_jobs" in data
    assert "reactive_jobs" in data
    assert "breached_job_count" in data


def test_simple_job_without_site_contract_asset_still_works(client):
    """Test 7: backward compatibility — customer + address only."""
    token = _login(client, username="admin@example.com", password="admin")
    h = _auth_headers(token)
    customer_id = _new_customer(client, token)

    job_res = client.post(
        "/jobs",
        headers=h,
        json={"customer_id": customer_id, "address": "Loose address only"},
    )
    assert job_res.status_code == 201, job_res.text
    j = job_res.json()
    assert j["customer_id"] == customer_id
    assert j["contract_id"] is None
    assert j["site_id"] is None
    assert j["asset_id"] is None
