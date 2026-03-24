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


@pytest.fixture(scope="module")
def portal_client_auth():
    """
    Dedicated portal user (avoids shared dev client@example.com mutated by other e2e tests).
    """
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    email = "portal_eta_client@example.com"
    password = "portaltest"
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == email).first():
            role = db.query(Role).filter(Role.name == "Client").one()
            db.add(
                User(
                    email=email,
                    hashed_password=hash_password(password),
                    roles=[role],
                )
            )
            db.commit()
        if not db.query(Customer).filter(Customer.email == email).first():
            db.add(Customer(name="Portal ETA Client", email=email))
            db.commit()
        cust = db.query(Customer).filter(Customer.email == email).one()
        return {"email": email, "password": password, "customer_id": cust.id}
    finally:
        db.close()


@pytest.fixture
def portal_customer_record(portal_client_auth):
    return portal_client_auth["customer_id"]


def _client_user_token(client, portal_client_auth) -> str:
    return _token(client, portal_client_auth["email"], portal_client_auth["password"])


def test_portal_customer_can_view_own_job_tracking(client, portal_customer_record, portal_client_auth):
    admin = _token(client, "admin@example.com", "admin")
    cust_tok = _client_user_token(client, portal_client_auth)

    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": portal_customer_record, "address": "1 Test Street"},
    )
    assert job_r.status_code == 201, job_r.text
    job_id = job_r.json()["id"]

    tr = client.get(f"/portal/me/jobs/{job_id}/tracking", headers=_h(cust_tok))
    assert tr.status_code == 200, tr.text
    body = tr.json()
    assert body["job_id"] == job_id
    assert "customer_tracking_state" in body
    assert "eta" in body


def test_portal_cannot_view_other_customer_job_tracking(client, portal_customer_record, portal_client_auth):
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    db = SessionLocal()
    try:
        other_c = Customer(name="Other Co", email=f"other-{uuid.uuid4().hex[:6]}@example.com")
        db.add(other_c)
        db.commit()
        db.refresh(other_c)
        other_id = other_c.id

        role = db.query(Role).filter(Role.name == "Client").one()
        u2 = User(
            email=f"client2-{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("secret"),
            roles=[role],
        )
        db.add(u2)
        db.commit()
        db.refresh(u2)
        u2_email = u2.email
    finally:
        db.close()

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": other_id, "address": "Secret site"},
    )
    assert job_r.status_code == 201, job_r.text
    job_id = job_r.json()["id"]

    cust_tok = _client_user_token(client, portal_client_auth)
    tr = client.get(f"/portal/me/jobs/{job_id}/tracking", headers=_h(cust_tok))
    assert tr.status_code == 404

    # client2 can never hit portal for wrong customer — same 404 for isolation
    t2 = _token(client, u2_email, "secret")
    tr2 = client.get(f"/portal/me/jobs/{job_id}/tracking", headers=_h(t2))
    assert tr2.status_code == 404


def test_internal_eta_live_tracking_when_fresh_telemetry(client, portal_customer_record):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        eid = eng.id
    finally:
        db.close()

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={
            "customer_id": portal_customer_record,
            "address": "Geo job",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
        },
    )
    job_id = job_r.json()["id"]

    gf = client.post(
        f"/tracking/geofences/{job_id}",
        headers=_h(admin),
        json={"latitude": 51.5, "longitude": -0.12, "radius_m": 200},
    )
    assert gf.status_code in (200, 201), gf.text

    client.post(
        f"/jobs/{job_id}/assign",
        headers=_h(admin),
        json={"engineer_id": eid},
    )

    tel = client.post(
        "/tracking/telemetry",
        headers=_h(admin),
        json={
            "vehicle_id": eid,
            "latitude": 51.501,
            "longitude": -0.121,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert tel.status_code == 200, tel.text

    eta_r = client.get(f"/dispatch/jobs/{job_id}/eta", headers=_h(admin))
    assert eta_r.status_code == 200, eta_r.text
    eta = eta_r.json()
    assert eta["eta_source"] == "live_tracking"
    assert eta["eta_confidence"] in ("high", "medium")
    assert eta["eta_minutes"] is not None


def test_eta_falls_back_to_schedule_when_telemetry_stale(client, portal_customer_record):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.tracking.telemetry_state_service import append_engineer_phone_telemetry

    db = SessionLocal()
    try:
        eng = db.query(User).filter(User.email == "engineer@example.com").one()
        eid = eng.id
        stale_time = datetime.now(timezone.utc) - timedelta(hours=2)
        append_engineer_phone_telemetry(
            db,
            engineer_id=eid,
            latitude=51.6,
            longitude=-0.2,
            occurred_at=stale_time,
        )
        db.commit()
    finally:
        db.close()

    admin = _token(client, "admin@example.com", "admin")
    sched = datetime.now(timezone.utc) + timedelta(hours=1)
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={
            "customer_id": portal_customer_record,
            "address": "Scheduled fallback",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
            "scheduled_at": sched.isoformat(),
        },
    )
    job_id = job_r.json()["id"]

    client.post(
        f"/tracking/geofences/{job_id}",
        headers=_h(admin),
        json={"latitude": 51.5, "longitude": -0.12, "radius_m": 200},
    )
    client.post(
        f"/jobs/{job_id}/assign",
        headers=_h(admin),
        json={"engineer_id": eid},
    )

    eta_r = client.get(f"/dispatch/jobs/{job_id}/eta", headers=_h(admin))
    assert eta_r.status_code == 200, eta_r.text
    assert eta_r.json()["eta_source"] == "schedule_window"


def test_commercial_portal_site_asset_access(client, portal_customer_record, portal_client_auth):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.portal.models import PortalSiteAccess

    admin = _token(client, "admin@example.com", "admin")
    try:
        db = SessionLocal()
        try:
            cust = db.get(Customer, portal_customer_record)
            cust.portal_profile = "commercial"
            db.commit()
        finally:
            db.close()

        site_a = client.post(
            "/sites",
            headers=_h(admin),
            json={
                "customer_id": portal_customer_record,
                "site_code": f"A-{uuid.uuid4().hex[:4]}",
                "name": "Site A",
                "address_line1": "A road",
            },
        ).json()["id"]
        site_b = client.post(
            "/sites",
            headers=_h(admin),
            json={
                "customer_id": portal_customer_record,
                "site_code": f"B-{uuid.uuid4().hex[:4]}",
                "name": "Site B",
                "address_line1": "B road",
            },
        ).json()["id"]

        db = SessionLocal()
        try:
            db.add(PortalSiteAccess(customer_id=portal_customer_record, site_id=site_a))
            db.commit()
        finally:
            db.close()

        client.post(
            "/jobs",
            headers=_h(admin),
            json={"customer_id": portal_customer_record, "address": "On A", "site_id": site_a},
        )
        client.post(
            "/jobs",
            headers=_h(admin),
            json={"customer_id": portal_customer_record, "address": "On B", "site_id": site_b},
        )

        ctok = _client_user_token(client, portal_client_auth)
        jobs = client.get("/portal/me/jobs", headers=_h(ctok)).json()
        assert len(jobs) == 1
        assert jobs[0]["site_id"] == site_a

        assets = client.post(
            "/assets",
            headers=_h(admin),
            json={
                "customer_id": portal_customer_record,
                "site_id": site_a,
                "asset_type": "boiler",
                "name": "Boiler A",
                "location_address": "A road",
            },
        )
        assert assets.status_code == 201, assets.text
        aid = assets.json()["id"]

        hist = client.get(f"/portal/me/assets/{aid}/history", headers=_h(ctok))
        assert hist.status_code == 200, hist.text
    finally:
        db = SessionLocal()
        try:
            db.query(PortalSiteAccess).filter(PortalSiteAccess.customer_id == portal_customer_record).delete()
            cust = db.get(Customer, portal_customer_record)
            if cust:
                cust.portal_profile = "residential"
            db.commit()
        finally:
            db.close()


def test_portal_timeline_has_milestones(client, portal_customer_record, portal_client_auth):
    admin = _token(client, "admin@example.com", "admin")
    cust_tok = _client_user_token(client, portal_client_auth)

    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": portal_customer_record, "address": "Timeline job"},
    )
    job_id = job_r.json()["id"]

    tl = client.get(f"/portal/me/jobs/{job_id}/timeline", headers=_h(cust_tok))
    assert tl.status_code == 200, tl.text
    titles = [x["title"] for x in tl.json()]
    assert any("received" in t.lower() for t in titles)


def test_portal_documents_only_authorized(client, portal_customer_record, portal_client_auth):
    from backend.app.core.security import hash_password
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import Role, User
    from backend.app.modules.crm.models import Customer

    shared_email = f"doc-{uuid.uuid4().hex[:6]}@example.com"
    db = SessionLocal()
    try:
        other_c = Customer(name="Doc Other", email=shared_email)
        db.add(other_c)
        db.commit()
        db.refresh(other_c)
        oid = other_c.id
        role = db.query(Role).filter(Role.name == "Client").one()
        u2 = User(
            email=shared_email,
            hashed_password=hash_password("secret"),
            roles=[role],
        )
        db.add(u2)
        db.commit()
        u2e = u2.email
    finally:
        db.close()

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": oid, "address": "Other doc job"},
    )
    job_id = job_r.json()["id"]
    cert_r = client.post(
        "/compliance/certificates/generate",
        headers=_h(admin),
        json={"job_id": job_id, "certificate_type": "gas"},
    )
    cert_id = cert_r.json()["id"]

    t1 = _client_user_token(client, portal_client_auth)
    assert client.get(f"/portal/me/certificates/{cert_id}", headers=_h(t1)).status_code == 404

    t2 = _token(client, u2e, "secret")
    assert client.get(f"/portal/me/certificates/{cert_id}", headers=_h(t2)).status_code == 200


def test_portal_invoice_detail_links_job_and_site(client, portal_customer_record, portal_client_auth):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.invoicing.models import Invoice

    admin = _token(client, "admin@example.com", "admin")
    site_id = client.post(
        "/sites",
        headers=_h(admin),
        json={
            "customer_id": portal_customer_record,
            "site_code": f"I-{uuid.uuid4().hex[:4]}",
            "name": "Invoice Site",
            "address_line1": "Inv lane",
        },
    ).json()["id"]

    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={
            "customer_id": portal_customer_record,
            "address": "Work at site",
            "site_id": site_id,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    job_id = job_r.json()["id"]

    db = SessionLocal()
    try:
        inv = Invoice(
            job_id=job_id,
            currency="GBP",
            status="unpaid",
            labour_total=100.0,
            materials_total=20.0,
            grand_total=120.0,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        inv_id = inv.id
    finally:
        db.close()

    ctok = _client_user_token(client, portal_client_auth)
    detail = client.get(f"/portal/me/invoices/{inv_id}", headers=_h(ctok))
    assert detail.status_code == 200, detail.text
    ctx = detail.json()["service_context"]
    assert ctx["site_id"] == site_id
    assert ctx["site_name"] == "Invoice Site"
    assert ctx["job_address"]


def test_internal_dispatch_tracking_full_context(client, portal_customer_record):
    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={"customer_id": portal_customer_record, "address": "Track me"},
    )
    job_id = job_r.json()["id"]

    tr = client.get(f"/dispatch/jobs/{job_id}/tracking", headers=_h(admin))
    assert tr.status_code == 200, tr.text
    body = tr.json()
    assert body["job_id"] == job_id
    assert "internal_status" in body
    assert "eta" in body
    assert "internal_timeline_events" in body
    assert isinstance(body["internal_timeline_events"], list)


def test_internal_and_customer_eta_share_service_layer(client, portal_customer_record, portal_client_auth):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        eid = db.query(User).filter(User.email == "engineer@example.com").one().id
    finally:
        db.close()

    admin = _token(client, "admin@example.com", "admin")
    job_r = client.post(
        "/jobs",
        headers=_h(admin),
        json={
            "customer_id": portal_customer_record,
            "address": "Shared eta",
            "site_latitude": 51.5,
            "site_longitude": -0.12,
        },
    )
    job_id = job_r.json()["id"]
    client.post(
        f"/tracking/geofences/{job_id}",
        headers=_h(admin),
        json={"latitude": 51.5, "longitude": -0.12, "radius_m": 200},
    )
    client.post(
        f"/jobs/{job_id}/assign",
        headers=_h(admin),
        json={"engineer_id": eid},
    )
    client.post(
        "/tracking/telemetry",
        headers=_h(admin),
        json={
            "vehicle_id": eid,
            "latitude": 51.501,
            "longitude": -0.121,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    internal = client.get(f"/dispatch/jobs/{job_id}/eta", headers=_h(admin)).json()
    ctok = _client_user_token(client, portal_client_auth)
    portal_tr = client.get(f"/portal/me/jobs/{job_id}/tracking", headers=_h(ctok)).json()
    cust_eta = portal_tr["eta"]

    assert internal["eta_source"] == cust_eta["eta_source"] == "live_tracking"
    assert abs((internal["eta_minutes"] or 0) - (cust_eta["eta_minutes"] or 0)) < 1e-6
