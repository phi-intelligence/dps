from __future__ import annotations

import uuid


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_signature_requirement_blocks_job_completion_and_invoice_release(client):
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

    # Inventory for materials line items.
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    inv_res = client.post(
        "/inventory/items",
        headers=_auth_headers(admin_token),
        json={
            "sku": sku,
            "name": "Test Part",
            "unit_cost": 5.0,
            "on_hand_quantity": 100.0,
            "reorder_point_quantity": 0.0,
        },
    )
    assert inv_res.status_code == 201, inv_res.text

    quote_res = client.post(
        "/quotes",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "currency": "GBP",
            "notes": "Phase3b signature test quote",
            "items": [
                {"item_type": "labour", "description": "Labour", "quantity": 1, "unit_price": 100.0},
                {"item_type": "materials", "description": sku, "quantity": 2, "unit_price": 10.0},
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

    # Configure geofence so punch-in/out works.
    lat = 51.5074
    lon = -0.1278
    fence_res = client.post(
        f"/tracking/geofences/{job_id}",
        headers=_auth_headers(admin_token),
        json={"latitude": lat, "longitude": lon, "radius_m": 250.0},
    )
    assert fence_res.status_code == 200, fence_res.text

    # Require engineer signature for completion.
    req_res = client.post(
        f"/jobs/{job_id}/completion/signature/require",
        headers=_auth_headers(admin_token),
        json={"required": True},
    )
    assert req_res.status_code == 200, req_res.text

    # Engineer punches in/out: should block completion until signature submitted.
    punch_in = client.post(
        "/time/punch/in",
        headers=_auth_headers(engineer_token),
        json={"job_id": job_id, "latitude": lat, "longitude": lon},
    )
    assert punch_in.status_code == 200, punch_in.text

    punch_out = client.post(
        "/time/punch/out",
        headers=_auth_headers(engineer_token),
        json={"job_id": job_id, "latitude": lat, "longitude": lon},
    )
    assert punch_out.status_code == 200, punch_out.text

    jobs_res = client.get("/jobs?limit=50&offset=0", headers=_auth_headers(admin_token))
    assert jobs_res.status_code == 200, jobs_res.text
    job = next((j for j in jobs_res.json() if j["id"] == job_id), None)
    assert job is not None
    assert job["status"] == "completion_blocked_forms"

    # Compliance can still generate.
    cert_res = client.post(
        "/compliance/certificates/generate",
        headers=_auth_headers(admin_token),
        json={"job_id": job_id, "certificate_type": "CP12"},
    )
    assert cert_res.status_code == 201, cert_res.text

    # Invoice release blocked.
    invoice_res = client.post(
        "/invoicing/invoices/generate",
        headers=_auth_headers(admin_token),
        json={"job_id": job_id},
    )
    assert invoice_res.status_code == 400, invoice_res.text

    # Submit signature -> should allow completion and invoice.
    sig_res = client.post(
        f"/jobs/{job_id}/signature",
        headers=_auth_headers(engineer_token),
        json={"signature": {"signed": True, "method": "mobile_draw_stub"}},
    )
    assert sig_res.status_code == 200, sig_res.text

    invoice_res2 = client.post(
        "/invoicing/invoices/generate",
        headers=_auth_headers(admin_token),
        json={"job_id": job_id},
    )
    assert invoice_res2.status_code == 201, invoice_res2.text

