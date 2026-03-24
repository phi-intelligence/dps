"""Start-4: ledger-based inventory, partial usage vs reservation, ops APIs."""
from __future__ import annotations

import uuid


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_material_shortage_preview_and_partial_usage_consume(client):
    admin = _login(client, username="admin@example.com", password="admin")
    eng = _login(client, username="engineer@example.com", password="engineer")

    customer_email = f"c-{uuid.uuid4().hex[:6]}@example.com"
    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": customer_email})
    assert lead.status_code == 201, lead.text
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": customer_email},
    )
    assert conv.status_code == 200, conv.text
    customer_id = conv.json()["customer"]["id"]

    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    inv = client.post(
        "/inventory/items",
        headers=_auth(admin),
        json={
            "sku": sku,
            "name": "Part",
            "unit_cost": 1.0,
            "on_hand_quantity": 100.0,
            "reorder_point_quantity": 0.0,
        },
    )
    assert inv.status_code == 201, inv.text

    quote = client.post(
        "/quotes",
        headers=_auth(admin),
        json={
            "customer_id": customer_id,
            "currency": "GBP",
            "notes": "t",
            "items": [
                {"item_type": "labour", "description": "L", "quantity": 1, "unit_price": 10.0},
                {"item_type": "materials", "description": sku, "quantity": 5, "unit_price": 2.0},
            ],
        },
    )
    assert quote.status_code == 201, quote.text
    qid = quote.json()["id"]

    short = client.get(f"/inventory/quotes/{qid}/material-shortage-preview", headers=_auth(admin))
    assert short.status_code == 200, short.text
    assert short.json() == []

    acc = client.post(f"/quotes/{qid}/accept", headers=_auth(admin))
    assert acc.status_code == 200, acc.text

    job = client.post(
        "/jobs",
        headers=_auth(admin),
        json={"customer_id": customer_id, "quote_id": qid, "address": "1 St"},
    )
    assert job.status_code == 201, job.text
    jid = job.json()["id"]

    me = client.get("/auth/me", headers=_auth(eng))
    eid = me.json()["id"]
    client.post(f"/jobs/{jid}/assign", headers=_auth(admin), json={"engineer_id": eid})

    locs = client.get("/inventory/locations", headers=_auth(admin))
    assert locs.status_code == 200, locs.text
    wh_id = next(x["id"] for x in locs.json() if x["code"] == "DEFAULT_WH")

    parts = client.post(
        f"/jobs/{jid}/parts-usage",
        headers=_auth(eng),
        json={"items": [{"sku": sku, "quantity": 2, "location_id": wh_id}]},
    )
    assert parts.status_code == 200, parts.text

    lat, lon = 51.5074, -0.1278
    client.post(f"/tracking/geofences/{jid}", headers=_auth(admin), json={"latitude": lat, "longitude": lon, "radius_m": 250})
    client.post("/time/punch/in", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})
    client.post("/time/punch/out", headers=_auth(eng), json={"job_id": jid, "latitude": lat, "longitude": lon})

    items = client.get("/inventory/items?limit=50", headers=_auth(admin))
    assert items.status_code == 200, items.text
    row = next(x for x in items.json() if x["sku"] == sku)
    assert abs(float(row["on_hand_quantity"]) - 98.0) < 0.01
    assert float(row["reserved_quantity"]) < 0.01


def test_transfer_wh_to_van(client):
    admin = _login(client, username="admin@example.com", password="admin")
    sku = f"SKU-{uuid.uuid4().hex[:6]}"
    client.post(
        "/inventory/items",
        headers=_auth(admin),
        json={"sku": sku, "name": "P", "unit_cost": 1.0, "on_hand_quantity": 50.0, "reorder_point_quantity": 0.0},
    )
    locs = client.get("/inventory/locations", headers=_auth(admin))
    wh_id = next(x["id"] for x in locs.json() if x["code"] == "DEFAULT_WH")
    van = client.post(
        "/inventory/locations/van",
        headers=_auth(admin),
        json={"code": f"VAN-{uuid.uuid4().hex[:4]}", "name": "Van 1"},
    )
    assert van.status_code == 201, van.text
    van_id = van.json()["id"]

    tr = client.post(
        "/inventory/transfers",
        headers=_auth(admin),
        json={
            "from_location_id": wh_id,
            "to_location_id": van_id,
            "lines": [{"sku": sku, "quantity": 10.0}],
        },
    )
    assert tr.status_code == 201, tr.text
    tid = tr.json()["transfer_id"]
    assert client.post(f"/inventory/transfers/{tid}/ship", headers=_auth(admin)).status_code == 200
    assert client.post(f"/inventory/transfers/{tid}/receive", headers=_auth(admin)).status_code == 200

    items = client.get("/inventory/items?limit=50", headers=_auth(admin))
    row = next(x for x in items.json() if x["sku"] == sku)
    assert abs(float(row["on_hand_quantity"]) - 50.0) < 0.01
