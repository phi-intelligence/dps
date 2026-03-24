"""
Wave 7: engineer mobile idempotency, workflow guards, and conflict behavior.
"""

from __future__ import annotations

import uuid

import pytest


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str, **extra: str) -> dict[str, str]:
    h = {"Authorization": f"Bearer {token}"}
    h.update(extra)
    return h


@pytest.fixture
def engineer_job_with_geofence(client):
    """Admin creates job assigned to engineer + geofence for punch validation."""
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200
    engineer_id = engineer_me.json()["id"]

    customer_email = f"cust-{uuid.uuid4().hex[:8]}@example.com"
    lead_res = client.post(
        "/crm/leads",
        headers=_auth_headers(admin_token),
        json={"name": f"Lead {uuid.uuid4().hex[:8]}", "email": customer_email},
    )
    assert lead_res.status_code == 201, lead_res.text
    lead_id = lead_res.json()["id"]

    convert_res = client.post(
        f"/crm/leads/{lead_id}/convert",
        headers=_auth_headers(admin_token),
        json={"name": "Wave7 Customer", "email": customer_email},
    )
    assert convert_res.status_code == 200, convert_res.text
    customer_id = convert_res.json()["customer"]["id"]

    quote_res = client.post(
        "/quotes",
        headers=_auth_headers(admin_token),
        json={
            "customer_id": customer_id,
            "currency": "GBP",
            "notes": "Wave7",
            "items": [{"item_type": "labour", "description": "Labour", "quantity": 1, "unit_price": 100.0}],
        },
    )
    assert quote_res.status_code == 201, quote_res.text
    quote_id = quote_res.json()["id"]

    accept_quote = client.post(f"/quotes/{quote_id}/accept", headers=_auth_headers(admin_token))
    assert accept_quote.status_code == 200, accept_quote.text

    job_res = client.post(
        "/jobs",
        headers=_auth_headers(admin_token),
        json={"customer_id": customer_id, "quote_id": quote_id, "address": "1 Test Street"},
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]

    assign_res = client.post(
        f"/jobs/{job_id}/assign",
        headers=_auth_headers(admin_token),
        json={"engineer_id": engineer_id},
    )
    assert assign_res.status_code == 200, assign_res.text

    lat, lon = 51.5074, -0.1278
    fence_res = client.post(
        f"/tracking/geofences/{job_id}",
        headers=_auth_headers(admin_token),
        json={"latitude": lat, "longitude": lon, "radius_m": 250.0},
    )
    assert fence_res.status_code == 200, fence_res.text

    return {
        "admin_token": admin_token,
        "engineer_token": engineer_token,
        "engineer_id": engineer_id,
        "job_id": job_id,
        "lat": lat,
        "lon": lon,
    }


def test_punch_in_idempotency_replay_returns_same_punch(engineer_job_with_geofence, client):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    lat, lon = ctx["lat"], ctx["lon"]
    key = f"punch-in-{uuid.uuid4().hex}"
    payload = {"job_id": job_id, "latitude": lat, "longitude": lon}
    h = _auth_headers(ctx["engineer_token"], **{"Idempotency-Key": key})

    r1 = client.post("/time/punch/in", headers=h, json=payload)
    assert r1.status_code == 200, r1.text
    r2 = client.post("/time/punch/in", headers=h, json=payload)
    assert r2.status_code == 200, r2.text
    assert r1.json()["id"] == r2.json()["id"]


def test_punch_idempotency_conflict_different_body(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    lat, lon = ctx["lat"], ctx["lon"]
    key = f"idem-{uuid.uuid4().hex}"
    base = _auth_headers(ctx["engineer_token"], **{"Idempotency-Key": key})

    r1 = client.post("/time/punch/in", headers=base, json={"job_id": job_id, "latitude": lat, "longitude": lon})
    assert r1.status_code == 200, r1.text

    r2 = client.post(
        "/time/punch/in",
        headers=base,
        json={"job_id": job_id, "latitude": lat + 0.01, "longitude": lon},
    )
    assert r2.status_code == 409


def test_accept_job_replay_after_progression(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]
    key = f"accept-{uuid.uuid4().hex}"
    h = _auth_headers(eng, **{"Idempotency-Key": key})

    r1 = client.post(f"/jobs/{job_id}/accept", headers=h, json={"required_competencies": []})
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "accepted"

    r2 = client.post(f"/jobs/{job_id}/accept", headers=h, json={"required_competencies": []})
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == job_id
    assert r2.json()["status"] in {"accepted", "on_site"}


def test_form_submit_duplicate_payload_is_idempotent(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]
    form_key = "safety"

    r0 = client.post(
        f"/jobs/{job_id}/accept",
        headers=_auth_headers(eng),
        json={"required_competencies": []},
    )
    assert r0.status_code == 200, r0.text

    body = {"data": {"a": 1, "b": "x"}}
    r1 = client.post(f"/jobs/{job_id}/forms/{form_key}/submit", headers=_auth_headers(eng), json=body)
    assert r1.status_code == 200, r1.text
    sid = r1.json()["id"]

    r2 = client.post(f"/jobs/{job_id}/forms/{form_key}/submit", headers=_auth_headers(eng), json=body)
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == sid


def test_media_payload_too_large_returns_413(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]

    r0 = client.post(
        f"/jobs/{job_id}/accept",
        headers=_auth_headers(eng),
        json={"required_competencies": []},
    )
    assert r0.status_code == 200, r0.text

    # Slightly over the 2 MiB engineer-mobile JSON cap (faster than multi‑MB strings in CI).
    huge = "x" * (2 * 1024 * 1024 + 1024)
    res = client.post(
        f"/jobs/{job_id}/media",
        headers=_auth_headers(eng),
        json={"media_type": "photo", "payloads": [{"b64": huge}]},
    )
    assert res.status_code == 413


def test_engineer_can_search_inventory_items_for_parts_entry(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    admin_token = ctx["admin_token"]
    eng_token = ctx["engineer_token"]

    sku = f"WAVE8-SKU-{uuid.uuid4().hex[:6]}".upper()
    create = client.post(
        "/inventory/items",
        headers=_auth_headers(admin_token),
        json={
            "sku": sku,
            "name": "Wave8 Searchable Item",
            "unit_cost": 1.0,
            "on_hand_quantity": 10.0,
            "reorder_point_quantity": 0.0,
        },
    )
    assert create.status_code == 201, create.text

    search = client.get(
        "/inventory/engineer/items/search",
        headers=_auth_headers(eng_token),
        params={"q": "WAVE8-SKU", "limit": 10},
    )
    assert search.status_code == 200, search.text
    rows = search.json()
    assert any(r.get("sku") == sku for r in rows)


def test_engineer_can_create_and_list_job_notes(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]

    accept = client.post(
        f"/jobs/{job_id}/accept",
        headers=_auth_headers(eng),
        json={"required_competencies": []},
    )
    assert accept.status_code == 200, accept.text

    key = f"note-{uuid.uuid4().hex}"
    create = client.post(
        f"/jobs/{job_id}/notes",
        headers=_auth_headers(eng, **{"Idempotency-Key": key}),
        json={"body": "Engineer arrived on site", "source": "engineer_note"},
    )
    assert create.status_code == 201, create.text
    note_id = create.json()["id"]

    replay = client.post(
        f"/jobs/{job_id}/notes",
        headers=_auth_headers(eng, **{"Idempotency-Key": key}),
        json={"body": "Engineer arrived on site", "source": "engineer_note"},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == note_id

    listed = client.get(f"/jobs/{job_id}/activity", headers=_auth_headers(eng))
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert any(r.get("id") == note_id and r.get("activity_type") == "note" for r in rows)


def test_engineer_note_creation_validates_body(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]

    deny = client.post(
        f"/jobs/{job_id}/notes",
        headers=_auth_headers(eng),
        json={"body": "   "},
    )
    assert deny.status_code == 400


def test_job_activity_includes_typed_domain_events(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    job_id = ctx["job_id"]
    eng = ctx["engineer_token"]
    lat, lon = ctx["lat"], ctx["lon"]

    accept = client.post(
        f"/jobs/{job_id}/accept",
        headers=_auth_headers(eng),
        json={"required_competencies": []},
    )
    assert accept.status_code == 200, accept.text

    pin = client.post(
        "/time/punch/in",
        headers=_auth_headers(eng),
        json={"job_id": job_id, "latitude": lat, "longitude": lon},
    )
    assert pin.status_code == 200, pin.text

    form = client.post(
        f"/jobs/{job_id}/forms/safety/submit",
        headers=_auth_headers(eng),
        json={"data": {"checklist": "ok"}},
    )
    assert form.status_code == 200, form.text

    listed = client.get(f"/jobs/{job_id}/activity", headers=_auth_headers(eng))
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    activity_types = {r.get("activity_type") for r in rows}
    assert "punch" in activity_types
    assert "form_submission" in activity_types


def test_auth_me_exposes_assigned_vehicle_id_field(client):
    token = _login(client, username="engineer@example.com", password="engineer")
    me = client.get("/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200, me.text
    payload = me.json()
    assert "assigned_vehicle_id" in payload


def test_media_phase2_capabilities_default_disabled(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    eng = ctx["engineer_token"]
    res = client.get("/jobs/media/capabilities", headers=_auth_headers(eng))
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("phase2_enabled") is False
    assert data.get("legacy_json_enabled") is True


def test_media_phase2_session_create_and_commit_when_flag_enabled(client, engineer_job_with_geofence):
    ctx = engineer_job_with_geofence
    admin = ctx["admin_token"]
    eng = ctx["engineer_token"]
    job_id = ctx["job_id"]

    # Enable feature flag via admin settings domain.
    put = client.put(
        "/settings/feature_flags",
        headers=_auth_headers(admin),
        json={
            "values": {
                "ai_assisted_drafting_enabled": False,
                "dispatch_recommend_stale": False,
                "strict_parts_reconciliation": False,
                "engineer_media_phase2_enabled": True,
            }
        },
    )
    assert put.status_code == 200, put.text

    session = client.post(
        f"/jobs/{job_id}/media/upload-sessions",
        headers=_auth_headers(eng),
        json={"media_type": "photo"},
    )
    assert session.status_code == 201, session.text
    session_id = session.json()["id"]

    commit = client.post(
        f"/jobs/{job_id}/media/upload-sessions/{session_id}/commit",
        headers=_auth_headers(eng, **{"Idempotency-Key": f"media-phase2-{uuid.uuid4().hex}"}),
        json={
            "payloads": [
                {
                    "filename": "site.jpg",
                    "content_base64": "YWJj",
                    "mime_type": "image/jpeg",
                }
            ]
        },
    )
    assert commit.status_code == 200, commit.text
