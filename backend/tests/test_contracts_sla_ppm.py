from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_contract_ppm_generation_filters_by_contract_and_sla_risk(client):
    admin_token = _login(client, username="admin@example.com", password="admin")

    # Create customer via lead->convert (reuse the Phase 4 flow).
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
    customer_id = convert_res.json()["customer"]["id"]

    now = datetime.now(timezone.utc)

    # Create contract with "always breached when far future" SLA completion (0 minutes).
    contract_res = client.post(
        "/contracts",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "name": "Test Contract",
            "term_start_at": (now - timedelta(days=1)).isoformat(),
            "term_end_at": (now + timedelta(days=365)).isoformat(),
            "billing_frequency": "monthly",
            "ppm_interval_days": 90,
            "next_ppm_due_at": now.isoformat(),
            "sla_response_minutes": 60,
            "sla_attendance_minutes": 240,
            "sla_completion_minutes": 0,
        },
    )
    assert contract_res.status_code == 201, contract_res.text
    contract_id = contract_res.json()["id"]

    # Asset under this contract (maintenance schedule due).
    asset1_res = client.post(
        "/assets",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "contract_id": contract_id,
            "asset_type": "boiler",
            "name": "Asset One",
            "serial_number": None,
            "location_address": "1 Test Road",
            "next_maintenance_eta_at": None,
        },
    )
    assert asset1_res.status_code == 201, asset1_res.text
    asset1_id = asset1_res.json()["id"]

    sched1_res = client.post(
        f"/assets/{asset1_id}/schedules",
        headers=_auth_headers(admin_token),
        json={
            "asset_id": asset1_id,
            "next_due_at": (now - timedelta(days=1)).isoformat(),
            "interval_days": 90,
            "notes": "due",
        },
    )
    assert sched1_res.status_code == 201, sched1_res.text

    # Asset not under this contract (maintenance schedule due) should not create jobs.
    asset2_res = client.post(
        "/assets",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "contract_id": None,
            "asset_type": "boiler",
            "name": "Asset Two",
            "serial_number": None,
            "location_address": "2 Test Road",
            "next_maintenance_eta_at": None,
        },
    )
    assert asset2_res.status_code == 201, asset2_res.text
    asset2_id = asset2_res.json()["id"]

    sched2_res = client.post(
        f"/assets/{asset2_id}/schedules",
        headers=_auth_headers(admin_token),
        json={
            "asset_id": asset2_id,
            "next_due_at": (now - timedelta(days=1)).isoformat(),
            "interval_days": 90,
            "notes": "due-but-other-contract",
        },
    )
    assert sched2_res.status_code == 201, sched2_res.text

    # Generate due PPM for the contract (should create only asset1's maintenance jobs).
    generate_url = f"/contracts/{contract_id}/ppm/generate-due?now={quote(now.isoformat())}"
    gen_res = client.post(generate_url, headers=_auth_headers(admin_token))
    assert gen_res.status_code == 200, gen_res.text
    created_job_ids = gen_res.json()["created_job_ids"]

    assert len(created_job_ids) == 1, gen_res.text
    job_id = created_job_ids[0]

    # SLA risk endpoint: with completion_minutes=0, far future must be breached.
    far_future = datetime(2100, 1, 1, tzinfo=timezone.utc)
    risk_url = f"/contracts/jobs/{job_id}/sla/risk?now={quote(far_future.isoformat())}"
    risk_res = client.get(risk_url, headers=_auth_headers(admin_token))
    assert risk_res.status_code == 200, risk_res.text
    assert risk_res.json()["risk_state"] == "breached"

