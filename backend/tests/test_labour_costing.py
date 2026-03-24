"""Labour rate profiles, segmentation, snapshots, contract profitability, recommendations."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_token(client):
    return _login(client, username="admin@example.com", password="admin")


@pytest.fixture()
def engineer_id(client, admin_token):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == "engineer@example.com").one()
        return u.id
    finally:
        db.close()


def _clear_engineer_profiles(db, engineer_id: str) -> None:
    from backend.app.modules.costing.models import LabourRateProfile

    db.query(LabourRateProfile).filter(LabourRateProfile.applies_to_engineer_id == engineer_id).delete()
    db.commit()


def _approve_timesheets_for_punches(db, *, approver_id: str) -> None:
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.modules.time_tracking.service import approve_timesheet

    seen: set[tuple[str, str]] = set()
    for p in db.query(Punch).all():
        if p.kind != "in":
            continue
        d = p.occurred_at.astimezone(timezone.utc).date().isoformat()
        k = (p.user_id, d)
        if k in seen:
            continue
        seen.add(k)
        approve_timesheet(db, user_id=p.user_id, date_str=d, approved_by_user_id=approver_id)


def _engineer_profile(
    db,
    *,
    engineer_id: str,
    base: float = 60.0,
    overtime_rate: float | None = 90.0,
    travel_rate: float | None = None,
    ooh_rate: float | None = None,
    ws: int | None = None,
    we: int | None = None,
    ot_threshold: int | None = 480,
    dt_threshold: int | None = None,
    travel_enabled: bool = False,
) -> None:
    from backend.app.modules.costing.models import LabourRateProfile

    _clear_engineer_profiles(db, engineer_id)
    db.add(
        LabourRateProfile(
            name=f"UT-{uuid.uuid4().hex[:6]}",
            active=True,
            base_hourly_rate=base,
            overtime_hourly_rate=overtime_rate,
            doubletime_hourly_rate=None,
            travel_hourly_rate=travel_rate,
            out_of_hours_hourly_rate=ooh_rate,
            applies_to_engineer_id=engineer_id,
            default_profile=False,
            work_window_start_minutes_utc=ws,
            work_window_end_minutes_utc=we,
            overtime_threshold_minutes_per_day=ot_threshold,
            doubletime_threshold_minutes_per_day=dt_threshold,
            travel_costing_enabled=travel_enabled,
        )
    )
    db.commit()


def test_regular_hours_labour_total(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(db, engineer_id=engineer_id, base=60.0, ws=None, we=None, ot_threshold=480, travel_enabled=False)
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="created")
        db.add(job)
        db.flush()
        day = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=day,
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=day + timedelta(hours=1),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["regular_minutes"] == 60
        assert r["overtime_minutes"] == 0
        assert abs(r["labour_cost_total"] - 60.0) < 0.1
        assert r["labour_completeness_status"] == "complete"
    finally:
        db.close()


def test_overtime_bucket_over_threshold(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(
            db,
            engineer_id=engineer_id,
            base=60.0,
            overtime_rate=120.0,
            ws=None,
            we=None,
            ot_threshold=60,
            travel_enabled=False,
        )
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="created")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc)
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=t0,
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=t0 + timedelta(hours=3),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["regular_minutes"] == 60
        assert r["overtime_minutes"] == 120
        assert r["overtime_cost"] > r["regular_cost"]
    finally:
        db.close()


def test_travel_time_separate_travel_cost(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(
            db,
            engineer_id=engineer_id,
            base=60.0,
            travel_rate=30.0,
            ws=None,
            we=None,
            ot_threshold=480,
            travel_enabled=True,
        )
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        t0 = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)
        job = Job(
            customer_id=cust.id,
            address="1",
            assigned_engineer_id=engineer_id,
            status="created",
            dispatched_at=t0,
            en_route_at=t0 + timedelta(hours=1),
        )
        db.add(job)
        db.flush()
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=t0 + timedelta(hours=1),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=t0 + timedelta(hours=2),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["travel_minutes"] == 60
        assert abs(r["travel_cost"] - 30.0) < 0.1
    finally:
        db.close()


def test_out_of_hours_bucket(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(
            db,
            engineer_id=engineer_id,
            base=40.0,
            ooh_rate=100.0,
            ws=9 * 60,
            we=17 * 60,
            ot_threshold=480,
            travel_enabled=False,
        )
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="created")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 13, 18, 0, tzinfo=timezone.utc)
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=t0,
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=t0 + timedelta(hours=1),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["out_of_hours_minutes"] == 60
        assert r["out_of_hours_cost"] >= 99.0
    finally:
        db.close()


def test_job_costing_endpoint_labour_breakdown(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(db, engineer_id=engineer_id, base=50.0, ws=None, ot_threshold=480, travel_enabled=False)
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="created")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 14, 11, 0, tzinfo=timezone.utc)
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=t0,
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=t0 + timedelta(minutes=30),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        jid = job.id
    finally:
        db.close()

    r = client.get(f"/jobs/{jid}/costing", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["labour_completeness_status"] == "complete"
    assert body["labour_cost_breakdown"]["regular_minutes"] == 30
    lr = client.get(f"/jobs/{jid}/labour-costing", headers=_auth(admin_token))
    assert lr.status_code == 200
    assert lr.json()["job_id"] == jid


def test_contract_profitability_includes_travel_labour(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job

    db = SessionLocal()
    try:
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        now = datetime.now(timezone.utc)
        c = Contract(
            customer_id=cust.id,
            name="C1",
            contract_code=f"LC-{uuid.uuid4().hex[:4]}",
            contract_type="ppm_plus_reactive",
            term_start_at=now - timedelta(days=60),
            term_end_at=now + timedelta(days=300),
            next_ppm_due_at=now + timedelta(days=30),
        )
        db.add(c)
        db.flush()
        job = Job(
            customer_id=cust.id,
            contract_id=c.id,
            address="1",
            assigned_engineer_id=engineer_id,
            status="completed",
            resolved_at=now - timedelta(days=2),
        )
        db.add(job)
        db.flush()
        db.add(
            JobCostSnapshot(
                job_id=job.id,
                actual_material_cost=0.0,
                labour_cost=100.0,
                travel_cost=25.0,
                labour_seconds=3600,
                labour_hours=1.0,
                labour_overtime_cost=0.0,
                labour_cost_completeness="complete",
                regular_labour_minutes=60,
                regular_labour_cost=100.0,
                completed_at=now - timedelta(days=2),
            )
        )
        db.commit()
        cid = c.id
    finally:
        db.close()

    r = client.get(
        f"/contracts/{cid}/profitability",
        headers=_auth(admin_token),
        params={"period_window": "last_90_days"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["cost"]["travel_labour"] >= 25.0
    assert r.json()["cost"]["labour_completeness"] == "complete"


def test_missing_profile_fallback_and_warnings(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.costing.models import LabourRateProfile
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _clear_engineer_profiles(db, engineer_id)
        prev = {p.id: p.active for p in db.query(LabourRateProfile).all()}
        for p in db.query(LabourRateProfile).all():
            p.active = False
        db.commit()
        try:
            cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
            db.add(cust)
            db.flush()
            job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="created")
            db.add(job)
            db.flush()
            t0 = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)
            db.add(
                Punch(
                    user_id=engineer_id,
                    job_id=job.id,
                    kind="in",
                    occurred_at=t0,
                    latitude=51.0,
                    longitude=-0.1,
                )
            )
            db.add(
                Punch(
                    user_id=engineer_id,
                    job_id=job.id,
                    kind="out",
                    occurred_at=t0 + timedelta(hours=1),
                    latitude=51.0,
                    longitude=-0.1,
                )
            )
            db.commit()
            _approve_timesheets_for_punches(db, approver_id=admin.id)
            r = compute_job_labour_costing(db, job_id=job.id)
            assert r["labour_completeness_status"] == "fallback"
            assert any("no_labour_rate_profile" in w for w in r["warnings"])
        finally:
            for pid, act in prev.items():
                row = db.get(LabourRateProfile, pid)
                if row:
                    row.active = act
            db.commit()
    finally:
        db.close()


def test_excessive_overtime_recommendation(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.costing.models import JobCostSnapshot
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services.labour_recommendation_rules import register_labour_costing_recommendations

    db = SessionLocal()
    try:
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        now = datetime.now(timezone.utc)
        job = Job(
            customer_id=cust.id,
            address="1",
            assigned_engineer_id=engineer_id,
            status="completed",
            resolved_at=now,
        )
        db.add(job)
        db.flush()
        db.add(
            JobCostSnapshot(
                job_id=job.id,
                actual_material_cost=0.0,
                labour_cost=100.0,
                labour_overtime_cost=50.0,
                labour_seconds=7200,
                labour_hours=2.0,
                travel_cost=0.0,
                labour_cost_completeness="complete",
                completed_at=now,
            )
        )
        db.commit()
        jid = job.id
        active: set[str] = set()
        register_labour_costing_recommendations(db, active, now=now)
        db.commit()
        rec = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"labour:excessive-overtime:job:{jid}")
            .first()
        )
        assert rec is not None
        assert rec.category == "labour_costing"
    finally:
        db.close()


def test_snapshot_persists_labour_segmentation(engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.quoting.models import Quote, QuoteItem
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.job_costing import get_job_cost_snapshot, persist_job_cost_snapshot

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _engineer_profile(db, engineer_id=engineer_id, base=60.0, ws=None, ot_threshold=480, travel_enabled=False)
        cust = Customer(name="LC", email=f"lc-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        q = Quote(customer_id=cust.id, currency="GBP", status="accepted", grand_total=1.0, labour_total=1.0)
        db.add(q)
        db.flush()
        db.add(
            QuoteItem(quote_id=q.id, item_type="labour", description="L", quantity=1, unit_price=1, line_total=1)
        )
        job = Job(customer_id=cust.id, quote_id=q.id, address="1", assigned_engineer_id=engineer_id, status="created")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 16, 13, 0, tzinfo=timezone.utc)
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="in",
                occurred_at=t0,
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.add(
            Punch(
                user_id=engineer_id,
                job_id=job.id,
                kind="out",
                occurred_at=t0 + timedelta(hours=2),
                latitude=51.0,
                longitude=-0.1,
            )
        )
        db.commit()
        _approve_timesheets_for_punches(db, approver_id=admin.id)
        jid = job.id
        persist_job_cost_snapshot(db, job_id=jid, commit=True)
        snap = get_job_cost_snapshot(db, job_id=jid)
        assert snap is not None
        assert snap.regular_labour_minutes == 120
        assert float(snap.labour_cost) > 0
    finally:
        db.close()
