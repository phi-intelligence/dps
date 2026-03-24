"""Daily vehicle inspection / H&S pre-use checks and readiness."""
from __future__ import annotations

import uuid

import pytest


def _token(client, username: str, password: str) -> str:
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


def _engineer_id() -> str:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        email = f"vins_{uuid.uuid4().hex[:6]}@example.com"
        u = User(email=email, hashed_password=hash_password("vins123"), roles=[role])
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id
    finally:
        db.close()


@pytest.fixture
def admin_tok(client):
    return _token(client, "admin@example.com", "admin")


def test_passed_inspection_keeps_vehicle_ready(admin_tok, client):
    eng = _engineer_id()
    vid = f"v-ready-{uuid.uuid4().hex[:6]}"
    b = client.post(
        "/dispatch/vehicle-bindings",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "vehicle_id": vid},
    )
    assert b.status_code == 200, b.text

    ins = client.post(
        f"/vehicles/{vid}/inspections",
        headers=_h(admin_tok),
        json={
            "engineer_id": eng,
            "overall_status": "passed",
            "odometer": 12000.5,
            "latitude": 51.5,
            "longitude": -0.12,
            "items": [
                {"item_code": "tyres", "item_label": "Tyres", "result": "pass"},
                {"item_code": "lights", "item_label": "Lights", "result": "pass"},
            ],
        },
    )
    assert ins.status_code == 201, ins.text

    from backend.app.db.session import SessionLocal
    from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness

    db = SessionLocal()
    try:
        r = evaluate_vehicle_readiness(db, vehicle_id=vid)
        assert r.readiness_status == "ready"
    finally:
        db.close()


def test_failed_critical_inspection_blocks_vehicle(admin_tok, client):
    eng = _engineer_id()
    vid = f"v-fc-{uuid.uuid4().hex[:6]}"
    client.post(
        "/dispatch/vehicle-bindings",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "vehicle_id": vid},
    )
    ins = client.post(
        f"/vehicles/{vid}/inspections",
        headers=_h(admin_tok),
        json={
            "engineer_id": eng,
            "overall_status": "failed_critical",
            "items": [{"item_code": "brakes", "item_label": "Brakes", "result": "fail", "fail_criticality": "critical"}],
        },
    )
    assert ins.status_code == 201, ins.text

    from backend.app.db.session import SessionLocal
    from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness

    db = SessionLocal()
    try:
        r = evaluate_vehicle_readiness(db, vehicle_id=vid)
        assert r.readiness_status == "blocked"
        assert "failed_critical_inspection" in r.blocking_flags
    finally:
        db.close()


def test_unresolved_critical_defect_blocks_vehicle(admin_tok, client):
    eng = _engineer_id()
    vid = f"v-def-{uuid.uuid4().hex[:6]}"
    client.post(
        "/dispatch/vehicle-bindings",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "vehicle_id": vid},
    )
    d = client.post(
        f"/vehicles/{vid}/defects",
        headers=_h(admin_tok),
        json={
            "defect_type": "safety",
            "severity": "critical",
            "title": "Brake warning lamp",
            "description": "Lamp on during drive",
        },
    )
    assert d.status_code == 201, d.text

    from backend.app.db.session import SessionLocal
    from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness

    db = SessionLocal()
    try:
        r = evaluate_vehicle_readiness(db, vehicle_id=vid)
        assert r.readiness_status == "blocked"
        assert "unresolved_critical_defect" in r.blocking_flags
    finally:
        db.close()


def test_no_inspection_today_warning_and_recommendation(admin_tok, client):
    eng = _engineer_id()
    vid = f"v-noi-{uuid.uuid4().hex[:6]}"
    client.post(
        "/dispatch/vehicle-bindings",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "vehicle_id": vid},
    )

    from backend.app.db.session import SessionLocal
    from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness

    db = SessionLocal()
    try:
        r = evaluate_vehicle_readiness(db, vehicle_id=vid)
        assert r.readiness_status == "warning"
        assert "no_inspection_today" in r.reasons
    finally:
        db.close()

    client.post("/ops/recommendations/run-scan", headers=_h(admin_tok))
    lst = client.get("/ops/recommendations?category=vehicle_readiness", headers=_h(admin_tok))
    assert lst.status_code == 200, lst.text
    keys = " ".join(x["recommendation_key"] for x in lst.json())
    assert vid in keys or "no-inspection-today" in keys


def test_latest_inspection_and_history_retrieval(admin_tok, client):
    eng = _engineer_id()
    vid = f"v-hist-{uuid.uuid4().hex[:6]}"
    client.post(
        "/dispatch/vehicle-bindings",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "vehicle_id": vid},
    )
    r1 = client.post(
        f"/vehicles/{vid}/inspections",
        headers=_h(admin_tok),
        json={"engineer_id": eng, "overall_status": "passed", "items": []},
    )
    assert r1.status_code == 201, r1.text
    latest = client.get(f"/vehicles/{vid}/inspections/latest", headers=_h(admin_tok))
    assert latest.status_code == 200, latest.text
    assert latest.json()["vehicle_id"] == vid
    hist = client.get(f"/vehicles/{vid}/inspections", headers=_h(admin_tok))
    assert hist.status_code == 200, hist.text
    assert len(hist.json()) >= 1
