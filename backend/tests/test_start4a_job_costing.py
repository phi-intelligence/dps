"""Start-4a: job costing, snapshots, invoice cost basis, variance APIs."""
from __future__ import annotations

import uuid


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


def _customer_and_quote(
    client,
    admin: str,
    *,
    sku: str,
    mat_qty: float,
    mat_unit_price: float,
    unit_cost: float,
    stock_on_hand: float,
):
    email = f"c-{uuid.uuid4().hex[:6]}@example.com"
    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]

    inv = client.post(
        "/inventory/items",
        headers=_auth(admin),
        json={
            "sku": sku,
            "name": "P",
            "unit_cost": unit_cost,
            "on_hand_quantity": stock_on_hand,
            "reorder_point_quantity": 0.0,
        },
    )
    assert inv.status_code == 201

    quote = client.post(
        "/quotes",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "currency": "GBP",
            "notes": "t",
            "items": [
                {"item_type": "labour", "description": "L", "quantity": 1, "unit_price": 100.0},
                {"item_type": "materials", "description": sku, "quantity": mat_qty, "unit_price": mat_unit_price},
            ],
        },
    )
    assert quote.status_code == 201
    qid = quote.json()["id"]
    assert client.post(f"/quotes/{qid}/accept", headers=_auth(admin)).status_code == 200
    return cid, qid


def test_costing_partial_usage_positive_variance_and_snapshot(client):
    """Quote 5 reserved 5, actual 2 → estimated cost > actual; snapshot on completion."""
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    cid, qid = _customer_and_quote(
        client, admin, sku=sku, mat_qty=5.0, mat_unit_price=10.0, unit_cost=3.0, stock_on_hand=100.0
    )

    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={"customer_id": cid, "quote_id": qid, "address": "1 St"},
    )
    assert job.status_code == 201
    jid = job.json()["id"]
    me = client.get("/auth/me", headers=_auth(eng))
    eid = me.json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})

    locs = client.get("/inventory/locations", headers=_auth(admin))
    wh_id = next(x["id"] for x in locs.json() if x["code"] == "DEFAULT_WH")

    client.post(
        f"/jobs/{jid}/parts-usage",
        headers=_auth(eng),
        json={"items": [{"sku": sku, "quantity": 2.0, "location_id": wh_id}]},
    )

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})

    assert client.post("/compliance/certificates/generate", headers=_auth(admin), json={"job_id": jid, "certificate_type": "CP12"}).status_code == 201

    cost = client.get(f"/jobs/{jid}/costing", headers=_auth(admin))
    assert cost.status_code == 200, cost.text
    body = cost.json()
    assert body["source"] == "snapshot"
    assert body["estimated_material_cost"] == 15.0  # 5 * 3
    assert body["actual_material_cost"] == 6.0  # 2 * 3
    assert body["material_cost_variance_vs_estimate"] < 0
    assert body["costing_status"] in ("clean", "warning")


def test_costing_overuse_needs_review_and_actual_includes_extra(client):
    """Reserved 5, actual 7 with enough free stock → overuse flags; actual cost 7 * unit."""
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    cid, qid = _customer_and_quote(
        client, admin, sku=sku, mat_qty=5.0, mat_unit_price=10.0, unit_cost=4.0, stock_on_hand=100.0
    )

    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={"customer_id": cid, "quote_id": qid, "address": "1 St"},
    )
    jid = job.json()["id"]
    eid = client.get("/auth/me", headers=_auth(eng)).json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})
    wh_id = next(x["id"] for x in client.get("/inventory/locations", headers=_auth(admin)).json() if x["code"] == "DEFAULT_WH")

    client.post(
        f"/jobs/{jid}/parts-usage",
        headers=_auth(eng),
        json={"items": [{"sku": sku, "quantity": 7.0, "location_id": wh_id}]},
    )

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/compliance/certificates/generate", headers=_auth(admin), json={"job_id": jid, "certificate_type": "CP12"})

    cost = client.get(f"/jobs/{jid}/costing", headers=_auth(admin))
    assert cost.status_code == 200
    assert cost.json()["actual_material_cost"] == 28.0  # 7 * 4
    assert cost.json()["costing_status"] == "needs_review"
    assert any("overused" in f for line in cost.json()["lines"] for f in line["variance_flags"])


def test_costing_zero_unit_cost_warning(client):
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    cid, qid = _customer_and_quote(
        client, admin, sku=sku, mat_qty=3.0, mat_unit_price=10.0, unit_cost=0.0, stock_on_hand=50.0
    )

    job = client.post("/jobs", headers=_auth(admin), json={"customer_id": cid, "quote_id": qid, "address": "1 St"})
    jid = job.json()["id"]
    eid = client.get("/auth/me", headers=_auth(eng)).json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})
    wh_id = next(x["id"] for x in client.get("/inventory/locations", headers=_auth(admin)).json() if x["code"] == "DEFAULT_WH")
    client.post(f"/jobs/{jid}/parts-usage", headers=_auth(eng), json={"items": [{"sku": sku, "quantity": 1.0, "location_id": wh_id}]})

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/compliance/certificates/generate", headers=_auth(admin), json={"job_id": jid, "certificate_type": "CP12"})

    cost = client.get(f"/jobs/{jid}/costing", headers=_auth(admin))
    assert cost.status_code == 200
    w = " ".join(cost.json()["costing_warnings"])
    assert "zero_standard_cost" in w or sku in w


def test_invoice_uses_snapshot_billable_and_actual_cost(client):
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    cid, qid = _customer_and_quote(
        client, admin, sku=sku, mat_qty=5.0, mat_unit_price=10.0, unit_cost=2.0, stock_on_hand=100.0
    )

    job = client.post("/jobs", headers=_auth(admin), json={"customer_id": cid, "quote_id": qid, "address": "1 St"})
    jid = job.json()["id"]
    eid = client.get("/auth/me", headers=_auth(eng)).json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})
    wh_id = next(x["id"] for x in client.get("/inventory/locations", headers=_auth(admin)).json() if x["code"] == "DEFAULT_WH")
    client.post(f"/jobs/{jid}/parts-usage", headers=_auth(eng), json={"items": [{"sku": sku, "quantity": 2.0, "location_id": wh_id}]})

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/compliance/certificates/generate", headers=_auth(admin), json={"job_id": jid, "certificate_type": "CP12"})

    inv = client.post("/invoicing/invoices/generate", headers=_auth(admin), json={"job_id": jid})
    assert inv.status_code == 201, inv.text
    inv_body = inv.json()
    assert inv_body["materials_total"] == 20.0  # 2 * 10 sell
    assert inv_body["materials_actual_cost"] == 4.0  # 2 * 2 cost
    assert inv_body["job_cost_snapshot_id"] is not None


def test_legacy_no_usage_lines_invoice_quote_materials_sell(client):
    """No parts-usage POST → legacy quote materials line totals for invoice materials."""
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    cid, qid = _customer_and_quote(
        client, admin, sku=sku, mat_qty=2.0, mat_unit_price=15.0, unit_cost=5.0, stock_on_hand=100.0
    )

    job = client.post("/jobs", headers=_auth(admin), json={"customer_id": cid, "quote_id": qid, "address": "1 St"})
    jid = job.json()["id"]
    eid = client.get("/auth/me", headers=_auth(eng)).json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/compliance/certificates/generate", headers=_auth(admin), json={"job_id": jid, "certificate_type": "CP12"})

    inv = client.post("/invoicing/invoices/generate", headers=_auth(admin), json={"job_id": jid})
    assert inv.status_code == 201, inv.text
    assert inv.json()["materials_total"] == 30.0  # 2 * 15 line sell

    cost = client.get(f"/jobs/{jid}/costing", headers=_auth(admin))
    assert cost.json()["actual_material_qty"] == 0.0
