import uuid


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_security_headers_applied(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"


def test_unauthorized_requests_require_auth(client):
    res = client.get("/crm/leads")
    assert res.status_code == 401


def test_end_to_end_flow_and_gdpr_delete(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")
    client_token = _login(client, username="client@example.com", password="client")

    # Admin creates lead -> customer.
    customer_email = "client@example.com"
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

    # Admin sets up inventory for the quote materials line items.
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

    # Create and accept quote (materials reservation is triggered on accept).
    quote_res = client.post(
        "/quotes",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "currency": "GBP",
            "notes": "Phase4 test quote",
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

    # Create job linked to the accepted quote.
    job_res = client.post(
        "/jobs",
        headers=_auth_headers(admin_token),
        json={"customer_id": customer_id, "quote_id": quote_id, "address": "1 Test Street"},
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]

    # Assign job to engineer.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]

    assign_res = client.post(
        f"/jobs/{job_id}/assign",
        headers=_auth_headers(admin_token),
        json={"engineer_id": engineer_id},
    )
    assert assign_res.status_code == 200, assign_res.text

    # Configure geofence so engineer punches can validate location.
    lat = 51.5074
    lon = -0.1278
    fence_res = client.post(
        f"/tracking/geofences/{job_id}",
        headers=_auth_headers(admin_token),
        json={"latitude": lat, "longitude": lon, "radius_m": 250.0},
    )
    assert fence_res.status_code == 200, fence_res.text

    # Engineer punches in/out.
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

    # Compliance certificate and invoice generation.
    cert_res = client.post(
        "/compliance/certificates/generate",
        headers=_auth_headers(admin_token),
        json={"job_id": job_id, "certificate_type": "CP12"},
    )
    assert cert_res.status_code == 201, cert_res.text

    invoice_res = client.post(
        "/invoicing/invoices/generate",
        headers=_auth_headers(admin_token),
        json={"job_id": job_id},
    )
    assert invoice_res.status_code == 201, invoice_res.text
    invoice_id = invoice_res.json()["id"]

    # Client portal: list and pay invoice.
    portal_invoices = client.get("/portal/me/invoices", headers=_auth_headers(client_token))
    assert portal_invoices.status_code == 200, portal_invoices.text
    assert len(portal_invoices.json()) >= 1

    pay_res = client.post(
        f"/portal/me/invoices/{invoice_id}/pay",
        headers=_auth_headers(client_token),
    )
    assert pay_res.status_code == 200, pay_res.text
    assert pay_res.json()["status"] == "paid"

    # GDPR export + delete + post-delete access denial.
    export_res = client.get("/portal/me/export", headers=_auth_headers(client_token))
    assert export_res.status_code == 200, export_res.text
    export_body = export_res.json()
    assert export_body["customer_email"] == customer_email
    assert len(export_body["jobs"]) >= 1

    delete_res = client.delete("/portal/me/delete", headers=_auth_headers(client_token))
    assert delete_res.status_code == 200, delete_res.text
    assert delete_res.json()["deleted"] is True

    export_after_delete = client.get("/portal/me/export", headers=_auth_headers(client_token))
    assert export_after_delete.status_code == 401

