from __future__ import annotations

import uuid


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_follow_on_jobs_created_for_each_defect(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

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

    # Create a base quote+job (no materials needed for this test).
    quote_res = client.post(
        "/quotes",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "currency": "GBP",
            "notes": "Phase3c base quote",
            "items": [
                {"item_type": "labour", "description": "Base work", "quantity": 1, "unit_price": 100.0},
            ],
        },
    )
    assert quote_res.status_code == 201, quote_res.text
    quote_id = quote_res.json()["id"]

    accept_res = client.post(
        f"/quotes/{quote_id}/accept",
        headers=_auth_headers(admin_token),
    )
    assert accept_res.status_code == 200, accept_res.text

    job_res = client.post(
        "/jobs",
        headers=_auth_headers(admin_token),
        json={"customer_id": customer_id, "quote_id": quote_id, "address": "1 Test Street"},
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]

    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]

    assign_res = client.post(
        f"/jobs/{job_id}/assign",
        headers=_auth_headers(admin_token),
        json={"engineer_id": engineer_id},
    )
    assert assign_res.status_code == 200, assign_res.text

    defects = ["Defect A", "Defect B", "Defect C"]
    follow_res = client.post(
        f"/jobs/{job_id}/follow-on/from-defects",
        headers=_auth_headers(engineer_token),
        json={"defects": defects},
    )
    assert follow_res.status_code == 200, follow_res.text
    created_job_ids = follow_res.json()["created_job_ids"]
    assert len(created_job_ids) == len(defects)

    # Ensure new jobs have quote_ids.
    jobs_res = client.get("/jobs?limit=50&offset=0", headers=_auth_headers(admin_token))
    assert jobs_res.status_code == 200, jobs_res.text
    jobs = {j["id"]: j for j in jobs_res.json()}
    for new_job_id in created_job_ids:
        assert new_job_id in jobs
        assert jobs[new_job_id]["quote_id"] is not None
        assert jobs[new_job_id]["customer_id"] == customer_id

