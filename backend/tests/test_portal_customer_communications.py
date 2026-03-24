"""Portal customer outbound communications history (scoped, customer-safe)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _ensure_client_user(email: str, password: str) -> None:
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
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


def test_portal_lists_sent_communications_only(client):
    admin = _login(client, username="admin@example.com", password="admin")
    email = f"pcm_{uuid.uuid4().hex[:10]}@example.com"
    password = "pcm-test"
    _ensure_client_user(email, password)

    lead = client.post("/crm/leads", headers=_auth(admin), json={"name": "PCM", "email": email})
    assert lead.status_code == 201
    conv = client.post(
        f"/crm/leads/{lead.json()['id']}/convert",
        headers=_auth(admin),
        json={"name": "PCM Co", "email": email},
    )
    assert conv.status_code == 200
    cid = conv.json()["customer"]["id"]
    now = datetime.now(timezone.utc)
    ctr = client.post(
        "/contracts",
        headers=_auth(admin),
        json={
            "customer_id": cid,
            "name": f"C {uuid.uuid4().hex[:6]}",
            "term_start_at": now.isoformat(),
            "next_ppm_due_at": now.isoformat(),
            "contract_value": 1000.0,
        },
    )
    assert ctr.status_code == 201
    contract_id = ctr.json()["id"]

    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        sent_id = str(uuid.uuid4())
        draft_id = str(uuid.uuid4())
        db.add(
            ContractCustomerCommunication(
                id=sent_id,
                contract_id=contract_id,
                source_entity_type="contract",
                source_entity_id=contract_id,
                communication_type="customer_notification",
                status="sent",
                channel="email",
                subject="Your service update",
                body_text="We will attend on Tuesday. " * 20,
                sent_at=now,
                recipient_customer_id=cid,
            )
        )
        db.add(
            ContractCustomerCommunication(
                id=draft_id,
                contract_id=contract_id,
                source_entity_type="contract",
                source_entity_id=contract_id,
                communication_type="customer_notification",
                status="draft",
                channel="email",
                subject="Internal draft",
                body_text="Secret",
            )
        )
        db.commit()
    finally:
        db.close()

    ctok = _login(client, username=email, password=password)
    lst = client.get("/portal/me/communications", headers=_auth(ctok))
    assert lst.status_code == 200, lst.text
    rows = lst.json()
    ids = {r["id"] for r in rows}
    assert sent_id in ids
    assert draft_id not in ids
    hit = next(r for r in rows if r["id"] == sent_id)
    assert hit["status"] == "sent"
    assert hit["subject"] == "Your service update"
    assert hit["body_preview"]
    assert "Tuesday" in hit["body_preview"]

    one = client.get(f"/portal/me/communications/{sent_id}", headers=_auth(ctok))
    assert one.status_code == 200
    assert one.json()["id"] == sent_id
