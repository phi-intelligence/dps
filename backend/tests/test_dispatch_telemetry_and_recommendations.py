"""
Dispatch intelligence: telemetry state, recommendations, assign-best audit, material policy hooks.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_engineer_user(email: str, password: str) -> str:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        u = User(email=email, hashed_password=hash_password(password), roles=[role])
        db.add(u)
        db.commit()
        db.refresh(u)
        return u.id
    finally:
        db.close()


def _customer_and_job(client, admin_token: str) -> tuple[str, str]:
    lead = client.post(
        "/crm/leads",
        headers=_auth(admin_token),
        json={"name": f"L {uuid.uuid4().hex[:6]}", "email": f"c_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert lead.status_code == 201, lead.text
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin_token),
        json={"name": "C", "email": lead.json()["email"]},
    )
    assert conv.status_code == 200, conv.text
    cid = conv.json()["customer"]["id"]
    job = client.post(
        "/jobs",
        headers=_auth(admin_token),
        json={
            "customer_id": cid,
            "address": "1 Dispatch Way",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "required_competencies": ["gas"],
        },
    )
    assert job.status_code == 201, job.text
    return cid, job.json()["id"]


def _add_qual(client, admin_token: str, engineer_id: str, competency: str, expires_at: datetime | None) -> None:
    res = client.post(
        "/competence/qualifications",
        headers=_auth(admin_token),
        json={
            "engineer_user_id": engineer_id,
            "competency": competency,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
    )
    assert res.status_code == 201, res.text


@pytest.fixture(autouse=True)
def _dispatch_test_isolation():
    """Prevent stacked qualifications / telemetry / active jobs from affecting ranking across tests."""
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.competence.models import Qualification
    from backend.app.modules.dispatch.models import DispatchDecisionLog, Job
    from backend.app.modules.tracking.models import (
        EngineerLatestLocation,
        EngineerTelemetryEvent,
        VehicleLatestLocation,
        VehicleTelemetryEvent,
    )

    db = SessionLocal()
    try:
        db.query(DispatchDecisionLog).delete()
        db.query(EngineerTelemetryEvent).delete()
        db.query(VehicleTelemetryEvent).delete()
        db.query(EngineerLatestLocation).delete()
        db.query(VehicleLatestLocation).delete()
        db.query(Qualification).delete()
        for u in db.query(User).all():
            u.assigned_vehicle_id = None
        for j in db.query(Job).all():
            j.assigned_engineer_id = None
            j.status = "completed"
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def admin_token(client):
    return _login(client, username="admin@example.com", password="admin")


@pytest.fixture()
def eng1_token(client):
    return _login(client, username="engineer@example.com", password="engineer")


@pytest.fixture()
def eng1_id(client, eng1_token):
    r = client.get("/auth/me", headers=_auth(eng1_token))
    assert r.status_code == 200
    return r.json()["id"]


def test_two_qualified_engineers_nearer_ranked_first(client, admin_token, eng1_token, eng1_id):
    e2_email = f"e2_{uuid.uuid4().hex[:8]}@example.com"
    e2_id = _create_engineer_user(e2_email, "pw")
    e2_token = _login(client, username=e2_email, password="pw")

    _add_qual(client, admin_token, eng1_id, "gas", None)
    _add_qual(client, admin_token, e2_id, "gas", None)

    _, job_id = _customer_and_job(client, admin_token)

    now = datetime.now(timezone.utc)
    # Engineer 1 nearer to site (51.5, -0.12)
    r1 = client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )
    assert r1.status_code == 200, r1.text
    r2 = client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e2_token),
        json={"latitude": 52.0, "longitude": -0.5, "occurred_at": now.isoformat()},
    )
    assert r2.status_code == 200, r2.text

    rec = client.get(
        f"/dispatch/jobs/{job_id}/recommendations",
        headers=_auth(admin_token),
        params={"required_competencies": "gas", "include_stale": "true"},
    )
    assert rec.status_code == 200, rec.text
    data = rec.json()["recommendations"]
    assert len(data) >= 2
    assert data[0]["engineer_id"] == eng1_id


def test_expired_competency_engineer_not_preferred(client, admin_token, eng1_token, eng1_id):
    e2_email = f"e2_{uuid.uuid4().hex[:8]}@example.com"
    e2_id = _create_engineer_user(e2_email, "pw")
    e2_token = _login(client, username=e2_email, password="pw")

    past = datetime.now(timezone.utc) - timedelta(days=1)
    _add_qual(client, admin_token, eng1_id, "gas", past)
    _add_qual(client, admin_token, e2_id, "gas", None)

    _, job_id = _customer_and_job(client, admin_token)
    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e2_token),
        json={"latitude": 52.0, "longitude": -0.5, "occurred_at": now.isoformat()},
    )

    rec = client.get(
        f"/dispatch/jobs/{job_id}/recommendations",
        headers=_auth(admin_token),
        params={"required_competencies": "gas"},
    )
    assert rec.status_code == 200, rec.text
    ids = [r["engineer_id"] for r in rec.json()["recommendations"]]
    assert eng1_id not in ids
    assert ids[0] == e2_id


def test_stale_telemetry_excluded_by_default(client, admin_token, eng1_token, eng1_id):
    e2_email = f"e2_{uuid.uuid4().hex[:8]}@example.com"
    e2_id = _create_engineer_user(e2_email, "pw")
    e2_token = _login(client, username=e2_email, password="pw")

    _add_qual(client, admin_token, eng1_id, "gas", None)
    _add_qual(client, admin_token, e2_id, "gas", None)

    _, job_id = _customer_and_job(client, admin_token)
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=400)
    fresh_time = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": stale_time.isoformat()},
    )
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e2_token),
        json={"latitude": 52.0, "longitude": -0.5, "occurred_at": fresh_time.isoformat()},
    )

    rec = client.get(
        f"/dispatch/jobs/{job_id}/recommendations",
        headers=_auth(admin_token),
        params={"required_competencies": "gas", "include_stale": "false"},
    )
    assert rec.status_code == 200, rec.text
    ids = [r["engineer_id"] for r in rec.json()["recommendations"]]
    assert eng1_id not in ids
    assert e2_id in ids


def test_engineer_on_active_job_excluded(client, admin_token, eng1_token, eng1_id):
    e2_email = f"e2_{uuid.uuid4().hex[:8]}@example.com"
    e2_id = _create_engineer_user(e2_email, "pw")
    e2_token = _login(client, username=e2_email, password="pw")

    _add_qual(client, admin_token, eng1_id, "gas", None)
    _add_qual(client, admin_token, e2_id, "gas", None)

    cid, job_target = _customer_and_job(client, admin_token)
    _, job_busy = _customer_and_job(client, admin_token)

    client.post(
        f"/jobs/{job_busy}/assign",
        headers=_auth(admin_token),
        json={"engineer_id": eng1_id},
    )
    client.post(
        f"/jobs/{job_busy}/status",
        headers=_auth(admin_token),
        json={"status": "in_progress"},
    )

    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e2_token),
        json={"latitude": 52.0, "longitude": -0.5, "occurred_at": now.isoformat()},
    )

    rec = client.get(
        f"/dispatch/jobs/{job_target}/recommendations",
        headers=_auth(admin_token),
        params={"required_competencies": "gas", "include_stale": "true"},
    )
    assert rec.status_code == 200, rec.text
    ids = [r["engineer_id"] for r in rec.json()["recommendations"]]
    assert eng1_id not in ids
    assert ids[0] == e2_id


def test_engineer_telemetry_endpoint_updates_latest_state(client, eng1_token, eng1_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.tracking.models import EngineerLatestLocation

    when = datetime.now(timezone.utc)
    r = client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.9, "longitude": -0.2, "occurred_at": when.isoformat(), "accuracy": 12.0},
    )
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        row = db.get(EngineerLatestLocation, eng1_id)
        assert row is not None
        assert abs(row.last_latitude - 51.9) < 1e-6
        assert abs(row.last_longitude - (-0.2)) < 1e-6
        assert row.last_accuracy_m == 12.0
    finally:
        db.close()


def test_operational_resolver_prefers_fresher_source(client, admin_token, eng1_token, eng1_id):
    _add_qual(client, admin_token, eng1_id, "gas", None)
    _, job_id = _customer_and_job(client, admin_token)

    van_id = f"VAN-{uuid.uuid4().hex[:6]}"
    client.post(
        "/dispatch/vehicle-bindings",
        headers=_auth(admin_token),
        json={"engineer_id": eng1_id, "vehicle_id": van_id},
    )

    older = datetime.now(timezone.utc) - timedelta(minutes=5)
    newer = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.0, "longitude": -0.2, "occurred_at": older.isoformat()},
    )
    client.post(
        "/tracking/telemetry/vehicle",
        headers=_auth(eng1_token),
        json={
            "vehicle_id": van_id,
            "latitude": 51.8,
            "longitude": -0.15,
            "occurred_at": newer.isoformat(),
        },
    )

    rec = client.get(
        f"/dispatch/jobs/{job_id}/recommendations",
        headers=_auth(admin_token),
        params={"required_competencies": "gas"},
    )
    assert rec.status_code == 200, rec.text
    top = rec.json()["recommendations"][0]
    assert top["engineer_id"] == eng1_id
    assert top["operational_source"] == "vehicle"
    assert abs(top["operational_latitude"] - 51.8) < 1e-4


def test_assign_best_writes_dispatch_decision_log(client, admin_token, eng1_token, eng1_id):
    e2_email = f"e2_{uuid.uuid4().hex[:8]}@example.com"
    e2_id = _create_engineer_user(e2_email, "pw")
    e2_token = _login(client, username=e2_email, password="pw")

    _add_qual(client, admin_token, eng1_id, "gas", None)
    _add_qual(client, admin_token, e2_id, "gas", None)

    _, job_id = _customer_and_job(client, admin_token)
    now = datetime.now(timezone.utc)
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(eng1_token),
        json={"latitude": 51.501, "longitude": -0.1201, "occurred_at": now.isoformat()},
    )
    client.post(
        "/tracking/telemetry/engineer",
        headers=_auth(e2_token),
        json={"latitude": 52.0, "longitude": -0.5, "occurred_at": now.isoformat()},
    )

    res = client.post(
        f"/dispatch/jobs/{job_id}/assign-best",
        headers=_auth(admin_token),
        json={"notes": "auto test"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["selected_engineer_id"] == eng1_id
    assert "competency_match" in " ".join(body["explanation_reasons"])

    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import DispatchDecisionLog

    db = SessionLocal()
    try:
        logs = db.query(DispatchDecisionLog).filter(DispatchDecisionLog.job_id == job_id).all()
        assert len(logs) == 1
        assert logs[0].decision_type == "auto_assign"
        assert logs[0].chosen_engineer_id == eng1_id
        ranked = json.loads(logs[0].ranked_candidates_json)
        assert isinstance(ranked, list)
        assert len(ranked) >= 1
    finally:
        db.close()


def test_manual_assign_still_works(client, admin_token, eng1_token, eng1_id):
    _add_qual(client, admin_token, eng1_id, "gas", None)
    _, job_id = _customer_and_job(client, admin_token)
    r = client.post(
        f"/jobs/{job_id}/assign",
        headers=_auth(admin_token),
        json={"engineer_id": eng1_id, "required_competencies": ["gas"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["assigned_engineer_id"] == eng1_id


def test_engineer_job_list_includes_only_assigned_jobs(client, admin_token, eng1_token, eng1_id):
    """Mobile app uses GET /jobs as engineer — must see assigned work only (not 403)."""
    _, job_id = _customer_and_job(client, admin_token)
    r_eng = client.get("/jobs?limit=50", headers=_auth(eng1_token))
    assert r_eng.status_code == 200, r_eng.text
    assert job_id not in {j["id"] for j in r_eng.json()}

    assign = client.post(
        f"/jobs/{job_id}/assign",
        headers=_auth(admin_token),
        json={"engineer_id": eng1_id},
    )
    assert assign.status_code == 200, assign.text

    r_eng2 = client.get("/jobs?limit=50", headers=_auth(eng1_token))
    assert r_eng2.status_code == 200
    assert job_id in {j["id"] for j in r_eng2.json()}


def test_no_materials_expected_skips_strict_parts_block(client, admin_token, monkeypatch):
    from backend.app.core import config

    monkeypatch.setattr(config.settings, "STRICT_PARTS_RECONCILIATION", True)

    from backend.app.modules.inventory.service import parts_usage_blocks_strict_completion
    from backend.app.db.session import SessionLocal
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        job = Job(
            customer_id=None,
            quote_id=None,
            address="addr",
            status="created",
            material_policy="no_materials_expected",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        assert parts_usage_blocks_strict_completion(db, job_id=job.id) is False
    finally:
        db.close()
