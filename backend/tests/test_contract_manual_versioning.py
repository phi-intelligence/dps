"""
Manual contract PATCH versioning: structured diffs, timeline coherence, audit logs.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from backend.app.db.session import SessionLocal
from backend.app.modules.contracts.contract_version_models import ContractVersion
from backend.app.modules.contracts.review_models import ContractCommercialActionLog


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client) -> str:
    return _login(client, username="admin@example.com", password="admin")


def _ensure_client_user(email: str, password: str) -> None:
    from backend.app.core.security import hash_password
    from backend.app.modules.auth.models import Role, User

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return
        role = db.query(Role).filter(Role.name == "Client").one()
        db.add(User(email=email, hashed_password=hash_password(password), roles=[role]))
        db.commit()
    finally:
        db.close()


def _new_contract(client, admin: str) -> str:
    email = f"mv_{uuid.uuid4().hex[:10]}@example.com"
    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"Contract {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 40000.0,
            "renewal_status": "not_due",
        },
    )
    assert ctr.status_code == 201, ctr.text
    return ctr.json()["id"]


def test_1_manual_patch_meaningful_change_creates_manual_update_version(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    before = (
        SessionLocal()
        .query(ContractVersion)
        .filter(ContractVersion.contract_id == contract_id)
        .count()
    )
    assert before == 0

    r = client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"contract_value": 43000.0, "manual_update_reason": "commercial correction"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["contract_value"] == 43000.0
    assert body["manual_version_created"] is True
    assert body["contract_version_id"]
    assert body["version_number"] >= 1

    db = SessionLocal()
    try:
        manual = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_type == "manual_update",
            )
            .one()
        )
        assert manual.effective_to is None
        assert manual.source_amendment_id is None
    finally:
        db.close()


def test_2_no_meaningful_change_no_extra_version(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"contract_value": 50000.0},
    )
    db = SessionLocal()
    try:
        n_after_first = (
            db.query(ContractVersion).filter(ContractVersion.contract_id == contract_id).count()
        )
    finally:
        db.close()

    r = client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"contract_value": 50000.0, "renewal_status": "not_due"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["manual_version_created"] is False
    assert r.json()["update_noop"] is True

    db = SessionLocal()
    try:
        n_after_second = (
            db.query(ContractVersion).filter(ContractVersion.contract_id == contract_id).count()
        )
        assert n_after_second == n_after_first
    finally:
        db.close()


def test_3_previous_active_version_closed_when_manual_version_created(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    client.patch(f"/contracts/{contract_id}", headers=_auth(admin), json={"contract_value": 51000.0})

    db = SessionLocal()
    try:
        open_rows = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.effective_to.is_(None),
            )
            .all()
        )
        assert len(open_rows) == 1
        first_open_id = open_rows[0].id

        client.patch(f"/contracts/{contract_id}", headers=_auth(admin), json={"contract_value": 52000.0})

        db.expire_all()
        prev = db.get(ContractVersion, first_open_id)
        assert prev is not None
        assert prev.effective_to is not None

        still_open = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.effective_to.is_(None),
            )
            .all()
        )
        assert len(still_open) == 1
        assert still_open[0].id != first_open_id
    finally:
        db.close()


def test_4_manual_version_has_structured_change_summary_json(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"account_attention_level": "high", "contract_value": 60000.0},
    )

    db = SessionLocal()
    try:
        v = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_type == "manual_update",
            )
            .one()
        )
        assert v.change_summary_json
        data = json.loads(v.change_summary_json)
        assert data["source"] == "manual_update"
        assert "contract_value" in data["changed_fields"]
        assert "account_attention_level" in data["changed_fields"]
        assert data["by_category"]["commercial"]
        assert data["human_readable_summary"]
    finally:
        db.close()


def test_5_timeline_shows_amendment_and_manual_coherently(client):
    """Uses repricing → amendment → activate, then manual PATCH; timeline ordered by version_number."""
    admin = _admin_token(client)
    email = f"tl_{uuid.uuid4().hex[:10]}@example.com"
    password = "tl-test"
    _ensure_client_user(email, password)
    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C", "email": email},
    )
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"C {uuid.uuid4().hex[:4]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 40000.0,
        },
    )
    contract_id = ctr.json()["id"]

    from backend.app.modules.ops.models import OperationalRecommendation

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_negative_margin",
                category="contract_attention",
                severity="critical",
                confidence="high",
                title="Margin",
                summary="S",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"m:{contract_id}:{uuid.uuid4().hex[:6]}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.post("/contracts/reviews/from-recommendation", headers=_auth(admin), json={"recommendation_id": rid})
    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    rr_id = rr.json()["id"]
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 45000.0, "current_contract_value": 40000.0},
    )
    pr = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    pid = pr.json()["id"]
    for step in (
        f"/contracts/repricing-proposals/{pid}/generate-pdf",
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ):
        assert client.post(step, headers=_auth(admin)).status_code == 200
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    acc = client.post(
        f"/portal/me/repricing-proposals/{pid}/respond",
        headers=_auth(ctok),
        json={"response_type": "accepted", "notes": "OK"},
    )
    assert acc.status_code == 200
    amd = client.post(
        f"/contracts/repricing-proposals/{pid}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = amd.json()["id"]
    client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))

    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"account_attention_level": "critical"},
    )

    tl = client.get(f"/contracts/{contract_id}/versions", headers=_auth(admin))
    assert tl.status_code == 200
    versions = tl.json()
    types = [x["version_type"] for x in versions]
    assert "amendment_activation" in types
    assert "manual_update" in types
    nums = [x["version_number"] for x in versions]
    assert nums == sorted(nums)
    assert versions[-1]["version_type"] == "manual_update"
    assert versions[-1]["is_active"] is True


def test_6_manual_update_then_amendment_activation_versioning_monotonic(client):
    admin = _admin_token(client)
    email = f"m6_{uuid.uuid4().hex[:10]}@example.com"
    password = "m6-test"
    _ensure_client_user(email, password)
    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "L6", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "C6", "email": email},
    )
    assert conv.status_code == 200, conv.text
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"C6 {uuid.uuid4().hex[:4]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 40000.0,
        },
    )
    contract_id = ctr.json()["id"]
    client.patch(f"/contracts/{contract_id}", headers=_auth(admin), json={"contract_value": 55000.0})

    from backend.app.modules.ops.models import OperationalRecommendation

    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.add(
            OperationalRecommendation(
                id=rid,
                recommendation_type="contract_negative_margin",
                category="contract_attention",
                severity="critical",
                confidence="high",
                title="Margin",
                summary="S",
                detail_json="{}",
                entity_type="contract",
                entity_id=contract_id,
                related_contract_id=contract_id,
                status="open",
                recommendation_key=f"m:{contract_id}:{uuid.uuid4().hex[:6]}",
                source_rule_version="test",
            )
        )
        db.commit()
    finally:
        db.close()

    client.post("/contracts/reviews/from-recommendation", headers=_auth(admin), json={"recommendation_id": rid})
    rr = client.get(f"/contracts/{contract_id}/repricing-review", headers=_auth(admin))
    rr_id = rr.json()["id"]
    client.patch(
        f"/contracts/{contract_id}/repricing-review",
        headers=_auth(admin),
        json={"proposed_contract_value": 58000.0, "current_contract_value": 55000.0},
    )
    pr = client.post(
        f"/contracts/{contract_id}/repricing-proposals",
        headers=_auth(admin),
        json={"repricing_review_id": rr_id},
    )
    pid = pr.json()["id"]
    for step in (
        f"/contracts/repricing-proposals/{pid}/generate-pdf",
        f"/contracts/repricing-proposals/{pid}/mark-internal-review",
        f"/contracts/repricing-proposals/{pid}/approve-internal",
        f"/contracts/repricing-proposals/{pid}/mark-ready-for-customer",
    ):
        assert client.post(step, headers=_auth(admin)).status_code == 200
    client.post(
        f"/contracts/repricing-proposals/{pid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    ctok = _login(client, username=email, password=password)
    assert (
        client.post(
            f"/portal/me/repricing-proposals/{pid}/respond",
            headers=_auth(ctok),
            json={"response_type": "accepted", "notes": "OK"},
        ).status_code
        == 200
    )
    amd = client.post(
        f"/contracts/repricing-proposals/{pid}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    amend_id = amd.json()["id"]
    client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})

    db = SessionLocal()
    try:
        max_before = (
            db.query(ContractVersion)
            .filter(ContractVersion.contract_id == contract_id)
            .with_entities(ContractVersion.version_number)
            .order_by(ContractVersion.version_number.desc())
            .first()
        )
        assert max_before is not None
        top_n = max_before[0]
    finally:
        db.close()

    client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin))

    db = SessionLocal()
    try:
        max_after = (
            db.query(ContractVersion)
            .filter(ContractVersion.contract_id == contract_id)
            .with_entities(ContractVersion.version_number)
            .order_by(ContractVersion.version_number.desc())
            .first()
        )
        assert max_after[0] == top_n + 1
    finally:
        db.close()


def test_7_commercial_audit_log_manual_update(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"contract_value": 70000.0, "manual_update_reason": "billing correction"},
    )

    logs = client.get(f"/contracts/{contract_id}/commercial-actions", headers=_auth(admin))
    assert logs.status_code == 200
    types = {x["action_type"] for x in logs.json()}
    assert "contract_manual_update_version_created" in types


def test_8_version_detail_includes_human_usable_diff_context(client):
    admin = _admin_token(client)
    contract_id = _new_contract(client, admin)
    client.patch(
        f"/contracts/{contract_id}",
        headers=_auth(admin),
        json={"churn_risk_level": "high"},
    )

    db = SessionLocal()
    try:
        v = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_type == "manual_update",
            )
            .one()
        )
        vid = v.id
    finally:
        db.close()

    d = client.get(f"/contracts/versions/{vid}", headers=_auth(admin))
    assert d.status_code == 200
    j = d.json()
    assert j["human_readable_summary"]
    assert j["change_summary"]
    assert j["change_summary"]["source"] == "manual_update"
    ch0 = (j["change_summary"].get("changes") or [{}])[0]
    assert ch0.get("field_label")
    assert ch0.get("category_display")
    assert j["snapshot_json"]
    assert j["snapshot_json"]["contract_id"] == contract_id
