"""
Field equipment readiness, calibration, movement history, dashboards, and ops recommendations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


def _token(client, username: str, password: str) -> str:
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


def _eng_user() -> tuple[str, str, str]:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    email = f"eq_eng_{uuid.uuid4().hex[:6]}@example.com"
    password = "engpass"
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        u = User(email=email, hashed_password=hash_password(password), roles=[role])
        db.add(u)
        db.commit()
        db.refresh(u)
        return email, password, u.id
    finally:
        db.close()


def _job_and_customer(client, admin: str) -> tuple[str, str]:
    lead = client.post(
        "/crm/leads",
        headers=_h(admin),
        json={"name": f"E {uuid.uuid4().hex[:6]}", "email": f"e_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201, lead.text
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_h(admin),
        json={"name": "ECust", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200, conv.text
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": cid, "address": "Equipment readiness st", "required_competencies": ["gas"]},
    )
    assert job.status_code == 201, job.text
    return cid, job.json()["id"]


@pytest.fixture
def admin_tok(client):
    return _token(client, "admin@example.com", "admin")


def test_job_blocked_when_expired_calibrated_equipment_only(admin_tok, client):
    _, job_id = _job_and_customer(client, admin_tok)
    _e_email, _, eid = _eng_user()
    client.post(
        f"/jobs/{job_id}/assign",
        headers=_h(admin_tok),
        json={"engineer_id": eid},
    )
    wh_id = _default_wh_id()
    code = f"AN-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_h(admin_tok),
        json={
            "equipment_code": code,
            "name": "Combustion analyser",
            "equipment_type": "combustion_analyser",
            "category": "test_gear",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
            "calibration_required": True,
            "calibration_due_date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        },
    )
    assert cr.status_code == 201, cr.text
    eq_id = cr.json()["id"]
    client.post(
        f"/equipment/{eq_id}/assign",
        headers=_h(admin_tok),
        json={
            "target": "engineer",
            "target_id": eid,
            "notes": "Test assign despite expired calibration for readiness check.",
        },
    )
    client.post(
        f"/jobs/{job_id}/equipment-requirements",
        headers=_h(admin_tok),
        json={
            "equipment_type": "combustion_analyser",
            "category": "test_gear",
            "calibration_required": True,
            "mandatory": True,
            "quantity": 1,
        },
    )
    r = client.get(f"/jobs/{job_id}/equipment-readiness", headers=_h(admin_tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["readiness_status"] == "blocked"
    assert body["expired_required_equipment"] or body["blocking_flags"]


def test_job_ready_when_valid_calibrated_equipment_assigned(admin_tok, client):
    _, job_id = _job_and_customer(client, admin_tok)
    _e_email, _, eid = _eng_user()
    client.post(f"/jobs/{job_id}/assign", headers=_h(admin_tok), json={"engineer_id": eid})
    wh_id = _default_wh_id()
    code = f"AN2-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_h(admin_tok),
        json={
            "equipment_code": code,
            "name": "Combustion analyser 2",
            "equipment_type": "combustion_analyser",
            "category": "test_gear",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
            "calibration_required": True,
            "calibration_due_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        },
    )
    assert cr.status_code == 201, cr.text
    eq_id = cr.json()["id"]
    client.post(
        f"/equipment/{eq_id}/assign",
        headers=_h(admin_tok),
        json={"target": "engineer", "target_id": eid},
    )
    client.post(
        f"/jobs/{job_id}/equipment-requirements",
        headers=_h(admin_tok),
        json={
            "equipment_type": "combustion_analyser",
            "calibration_required": True,
            "mandatory": True,
            "quantity": 1,
        },
    )
    r = client.get(f"/jobs/{job_id}/equipment-readiness", headers=_h(admin_tok))
    assert r.status_code == 200, r.text
    assert r.json()["readiness_status"] == "ready"
    assert r.json()["assigned_matching_equipment"]


def test_equipment_movement_history_append_only(admin_tok, client):
    wh_id = _default_wh_id()
    code = f"MV-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_h(admin_tok),
        json={
            "equipment_code": code,
            "name": "Movable",
            "equipment_type": "meter",
            "category": "electrical",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
        },
    )
    eq_id = cr.json()["id"]
    _a, _b, eid = _eng_user()
    client.post(
        f"/equipment/{eq_id}/move",
        headers=_h(admin_tok),
        json={"target": "engineer", "target_id": eid, "notes": "first"},
    )
    client.post(
        f"/equipment/{eq_id}/move",
        headers=_h(admin_tok),
        json={"target": "warehouse", "target_id": wh_id, "notes": "second"},
    )
    hist = client.get(f"/equipment/{eq_id}/movements", headers=_h(admin_tok))
    assert hist.status_code == 200, hist.text
    types = [x["movement_type"] for x in hist.json()]
    assert "assign_engineer" in types or "move_warehouse" in types
    assert len(hist.json()) >= 2


def test_calibration_record_updates_equipment_due_status(admin_tok, client):
    wh_id = _default_wh_id()
    code = f"CAL-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_h(admin_tok),
        json={
            "equipment_code": code,
            "name": "Cal tool",
            "equipment_type": "pressure_kit",
            "category": "pressure",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
            "calibration_required": True,
            "calibration_due_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        },
    )
    eq_id = cr.json()["id"]
    pr = client.post(
        f"/equipment/{eq_id}/calibration-records",
        headers=_h(admin_tok),
        json={
            "performed_at": datetime.now(timezone.utc).isoformat(),
            "next_due_date": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            "notes": "lab cert",
        },
    )
    assert pr.status_code == 201, pr.text
    g = client.get(f"/equipment/{eq_id}", headers=_h(admin_tok))
    assert g.status_code == 200, g.text
    assert g.json()["calibration_status"] in ("valid", "due_soon")
    assert g.json()["calibration_due_date"] is not None


def test_dashboards_reflect_counts(admin_tok, client):
    r1 = client.get("/equipment/dashboard/readiness", headers=_h(admin_tok))
    r2 = client.get("/equipment/dashboard/calibration", headers=_h(admin_tok))
    r3 = client.get("/equipment/dashboard/attention", headers=_h(admin_tok))
    assert r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 200
    assert "available_count" in r1.json()
    assert "calibration_expired" in r2.json()
    assert "expired_calibration_count" in r3.json()


def test_ops_scan_creates_equipment_recommendation(admin_tok, client):
    _, job_id = _job_and_customer(client, admin_tok)
    _e_email, _, eid = _eng_user()
    client.post(f"/jobs/{job_id}/assign", headers=_h(admin_tok), json={"engineer_id": eid})
    client.post(
        f"/jobs/{job_id}/equipment-requirements",
        headers=_h(admin_tok),
        json={
            "equipment_type": "nonexistent_type_xyz",
            "mandatory": True,
            "quantity": 1,
        },
    )
    rs = client.post("/ops/recommendations/run-scan", headers=_h(admin_tok))
    assert rs.status_code == 200, rs.text
    lst = client.get("/ops/recommendations?category=equipment_readiness", headers=_h(admin_tok))
    assert lst.status_code == 200, lst.text
    keys = [x["recommendation_key"] for x in lst.json()]
    assert any("equipment" in k for k in keys)


def test_job_equipment_readiness_endpoint_breakdown(admin_tok, client):
    _, job_id = _job_and_customer(client, admin_tok)
    r = client.get(f"/jobs/{job_id}/equipment-readiness", headers=_h(admin_tok))
    assert r.status_code == 200, r.text
    b = r.json()
    for k in (
        "readiness_status",
        "missing_required_equipment",
        "expired_required_equipment",
        "due_soon_equipment",
        "assigned_matching_equipment",
        "warnings",
        "blocking_flags",
    ):
        assert k in b


def test_equipment_operations_do_not_touch_inventory_ledger(admin_tok, client):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.models import InventoryLedgerEntry

    db = SessionLocal()
    try:
        before = db.query(InventoryLedgerEntry).count()
    finally:
        db.close()

    wh_id = _default_wh_id()
    code = f"INV-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_h(admin_tok),
        json={
            "equipment_code": code,
            "name": "Not stock",
            "equipment_type": "tool",
            "category": "hand",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
        },
    )
    assert cr.status_code == 201, cr.text
    eq_id = cr.json()["id"]
    client.post(
        f"/equipment/{eq_id}/calibration-records",
        headers=_h(admin_tok),
        json={
            "performed_at": datetime.now(timezone.utc).isoformat(),
            "next_due_date": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
        },
    )

    db = SessionLocal()
    try:
        after = db.query(InventoryLedgerEntry).count()
    finally:
        db.close()
    assert after == before


def _default_wh_id() -> str:
    from backend.app.db.session import SessionLocal
    from backend.app.modules.inventory.models import StockLocation

    db = SessionLocal()
    try:
        loc = db.query(StockLocation).filter(StockLocation.code == "DEFAULT_WH").one()
        return loc.id
    finally:
        db.close()
