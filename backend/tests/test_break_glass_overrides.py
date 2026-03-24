"""§5.14 break-glass overrides: audited reasons, comms suppression, vehicle defects, equipment assign."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from backend.app.db.session import SessionLocal
from backend.app.modules.system.break_glass_models import BreakGlassOverrideAudit
from backend.app.services.communication_recipient_suppression_service import upsert_suppression
from backend.tests.test_contract_amendment_activation import _admin_token, _auth, _proposal_ready_for_customer_release
from backend.tests.test_contract_customer_communications import _comms_for_proposal
from backend.tests.test_equipment_readiness import _default_wh_id, _eng_user


def _engineer_and_vehicle(client, admin_tok: str) -> tuple[str, str]:
    from backend.app.core.security import hash_password
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "Engineer").one()
        email = f"bg_eng_{uuid.uuid4().hex[:6]}@example.com"
        u = User(email=email, hashed_password=hash_password("bg123"), roles=[role])
        db.add(u)
        db.commit()
        db.refresh(u)
        eid = u.id
    finally:
        db.close()
    vid = f"v-bg-{uuid.uuid4().hex[:6]}"
    b = client.post(
        "/dispatch/vehicle-bindings",
        headers=_auth(admin_tok),
        json={"engineer_id": eid, "vehicle_id": vid},
    )
    assert b.status_code == 200, b.text
    return eid, vid


def test_break_glass_comm_suppression_send_retry_and_audit(client):
    admin = _admin_token(client)
    contract_id, proposal_id, email = _proposal_ready_for_customer_release(client, admin)
    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    rows = _comms_for_proposal(client, admin, proposal_id)
    cid = next(r["id"] for r in rows if r["communication_type"] == "repricing_proposal_released")
    assert client.post(f"/contracts/communications/{cid}/mark-ready", headers=_auth(admin)).status_code == 200

    cre = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert cre.status_code == 200, cre.text
    customer_id = cre.json()["customer_id"]

    db = SessionLocal()
    try:
        upsert_suppression(
            db,
            customer_id=customer_id,
            recipient_email=email,
            kind="complaint",
            requires_manual_review=False,
            provider_event_id=None,
            notes="test suppression",
            commit=True,
        )
    finally:
        db.close()

    s = client.post(f"/contracts/communications/{cid}/send", headers=_auth(admin))
    assert s.status_code == 200, s.text
    assert s.json()["status"] == "failed"

    bad = client.post(
        f"/contracts/communications/{cid}/retry-send",
        headers=_auth(admin),
        json={"break_glass_override_suppression": True, "break_glass_reason": "too short"},
    )
    assert bad.status_code == 400, bad.text

    ok = client.post(
        f"/contracts/communications/{cid}/retry-send",
        headers=_auth(admin),
        json={
            "break_glass_override_suppression": True,
            "break_glass_reason": "Customer explicitly requested the repricing pack by phone; documented in CRM.",
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "sent"

    db = SessionLocal()
    try:
        n = (
            db.query(BreakGlassOverrideAudit)
            .filter(
                BreakGlassOverrideAudit.target_id == cid,
                BreakGlassOverrideAudit.override_kind == "communication_suppression",
            )
            .count()
        )
        assert n >= 1
    finally:
        db.close()


def test_critical_defect_resolve_requires_long_notes_and_audits(client):
    admin = _admin_token(client)
    _eid, vid = _engineer_and_vehicle(client, admin)
    d = client.post(
        f"/vehicles/{vid}/defects",
        headers=_auth(admin),
        json={
            "defect_type": "safety",
            "severity": "critical",
            "title": "Test defect",
            "description": "For break-glass audit test",
        },
    )
    assert d.status_code == 201, d.text
    defect_id = d.json()["id"]

    short = client.post(
        f"/vehicles/{vid}/defects/{defect_id}/resolve",
        headers=_auth(admin),
        json={"resolution_notes": "fixed"},
    )
    assert short.status_code == 400, short.text

    good = client.post(
        f"/vehicles/{vid}/defects/{defect_id}/resolve",
        headers=_auth(admin),
        json={
            "resolution_notes": "Replaced brake sensor after workshop inspection; vehicle cleared for controlled use.",
        },
    )
    assert good.status_code == 200, good.text
    assert good.json()["status"] == "resolved"

    db = SessionLocal()
    try:
        n = (
            db.query(BreakGlassOverrideAudit)
            .filter(
                BreakGlassOverrideAudit.target_id == defect_id,
                BreakGlassOverrideAudit.override_kind == "vehicle_critical_defect_resolve",
            )
            .count()
        )
        assert n == 1
    finally:
        db.close()


def test_expired_calibration_assign_requires_notes_and_audits(client):
    admin = _admin_token(client)
    _e_email, _pw, eid = _eng_user()
    wh_id = _default_wh_id()
    code = f"BG-{uuid.uuid4().hex[:6]}"
    cr = client.post(
        "/equipment",
        headers=_auth(admin),
        json={
            "equipment_code": code,
            "name": "Break-glass cal test",
            "equipment_type": "combustion_analyser",
            "category": "test_gear",
            "status": "available",
            "current_location_type": "warehouse",
            "current_location_id": wh_id,
            "calibration_required": True,
            "calibration_due_date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        },
    )
    assert cr.status_code == 201, cr.text
    eq_id = cr.json()["id"]

    missing = client.post(
        f"/equipment/{eq_id}/assign",
        headers=_auth(admin),
        json={"target": "engineer", "target_id": eid},
    )
    assert missing.status_code == 400, missing.text

    ok = client.post(
        f"/equipment/{eq_id}/assign",
        headers=_auth(admin),
        json={
            "target": "engineer",
            "target_id": eid,
            "notes": "Temporary loan for same-day job; customer accepts calibrated backup tomorrow.",
        },
    )
    assert ok.status_code == 200, ok.text

    db = SessionLocal()
    try:
        n = (
            db.query(BreakGlassOverrideAudit)
            .filter(
                BreakGlassOverrideAudit.target_id == eq_id,
                BreakGlassOverrideAudit.override_kind == "equipment_expired_calibration_assign",
            )
            .count()
        )
        assert n == 1
    finally:
        db.close()
