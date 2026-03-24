"""Holiday calendars, regional labour rules, timezone-aware costing, profitability, recommendations."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

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
        return db.query(User).filter(User.email == "engineer@example.com").one().id
    finally:
        db.close()


def _clear_eng_profile(db, engineer_id: str) -> None:
    from backend.app.modules.costing.models import LabourRateProfile

    db.query(LabourRateProfile).filter(LabourRateProfile.applies_to_engineer_id == engineer_id).delete()


def _eng_profile(
    db,
    *,
    engineer_id: str,
    base: float = 60.0,
    ot: float | None = 90.0,
    dt: float | None = 120.0,
    ooh: float | None = 45.0,
    ws_utc: int | None = 9 * 60,
    we_utc: int | None = 17 * 60,
    ot_th: int | None = 480,
):
    from backend.app.modules.costing.models import LabourRateProfile

    _clear_eng_profile(db, engineer_id)
    db.add(
        LabourRateProfile(
            name=f"LR-{uuid.uuid4().hex[:6]}",
            active=True,
            base_hourly_rate=base,
            overtime_hourly_rate=ot,
            doubletime_hourly_rate=dt,
            travel_hourly_rate=None,
            out_of_hours_hourly_rate=ooh,
            applies_to_engineer_id=engineer_id,
            default_profile=False,
            work_window_start_minutes_utc=ws_utc,
            work_window_end_minutes_utc=we_utc,
            overtime_threshold_minutes_per_day=ot_th,
            doubletime_threshold_minutes_per_day=None,
            travel_costing_enabled=False,
            weekend_uses_doubletime_rate=False,
        )
    )
    db.commit()


def _approve_all_punches(db, admin_id: str) -> None:
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
        approve_timesheet(db, user_id=p.user_id, date_str=d, approved_by_user_id=admin_id)


def test_public_holiday_uses_holiday_policy_treatment(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import HolidayCalendar, HolidayCalendarDay, LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id, base=60, dt=120, ooh=45)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        cal = HolidayCalendar(
            id=str(uuid.uuid4()),
            name="UK test",
            region_code="UK",
            timezone_name="Europe/London",
            active=True,
        )
        db.add(cal)
        db.flush()
        db.add(
            HolidayCalendarDay(
                id=str(uuid.uuid4()),
                holiday_calendar_id=cal.id,
                calendar_date=date(2026, 1, 1),
                day_type="public_holiday",
                label="NYD",
            )
        )
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        rs = LabourRuleSet(
            id=str(uuid.uuid4()),
            name="RS contract",
            region_code="UK",
            timezone_name="Europe/London",
            active=True,
            applies_to_contract_id=c.id,
            holiday_calendar_id=cal.id,
            holiday_public_policy="doubletime",
            weekend_policy="weekday_window",
            normal_workday_start_minutes=9 * 60,
            normal_workday_end_minutes=17 * 60,
        )
        db.add(rs)
        job = Job(
            customer_id=cust.id,
            contract_id=c.id,
            address="1",
            assigned_engineer_id=engineer_id,
            status="open",
        )
        db.add(job)
        db.flush()
        t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 1, 16, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["doubletime_minutes"] == 240, r
        assert r["regular_minutes"] == 0
        assert r["labour_rules_attribution"]["holiday_applied_any"] is True
    finally:
        db.close()


def test_weekend_policy_doubletime(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        db.add(
            LabourRuleSet(
                id=str(uuid.uuid4()),
                name="WE double",
                region_code="UK",
                timezone_name="Europe/London",
                active=True,
                applies_to_contract_id=c.id,
                weekend_policy="doubletime",
                holiday_public_policy="normal_window",
                holiday_company_policy="normal_window",
            )
        )
        job = Job(customer_id=cust.id, contract_id=c.id, address="1", assigned_engineer_id=engineer_id, status="open")
        db.add(job)
        db.flush()
        # Saturday 6 June 2026 (UTC noon still Saturday in London)
        t0 = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["doubletime_minutes"] == 120
        assert r["labour_rules_attribution"]["weekend_applied_any"] is True
    finally:
        db.close()


def test_special_workday_overrides_weekend_doubletime(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import HolidayCalendar, HolidayCalendarDay, LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id, ot_th=480)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        cal = HolidayCalendar(
            id=str(uuid.uuid4()),
            name="Cal",
            region_code="UK",
            timezone_name="Europe/London",
            active=True,
        )
        db.add(cal)
        db.flush()
        db.add(
            HolidayCalendarDay(
                id=str(uuid.uuid4()),
                holiday_calendar_id=cal.id,
                calendar_date=date(2026, 6, 6),
                day_type="special_workday",
                label="Sat working",
            )
        )
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        db.add(
            LabourRuleSet(
                id=str(uuid.uuid4()),
                name="RS",
                region_code="UK",
                timezone_name="Europe/London",
                active=True,
                applies_to_contract_id=c.id,
                holiday_calendar_id=cal.id,
                weekend_policy="doubletime",
                special_workday_uses_normal_rates=True,
                normal_workday_start_minutes=9 * 60,
                normal_workday_end_minutes=17 * 60,
                holiday_public_policy="normal_window",
            )
        )
        job = Job(customer_id=cust.id, contract_id=c.id, address="1", assigned_engineer_id=engineer_id, status="open")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        r = compute_job_labour_costing(db, job_id=job.id)
        assert r["doubletime_minutes"] == 0, "special workday should not inherit weekend doubletime"
        assert r["regular_minutes"] == 120
    finally:
        db.close()


def test_timezone_segmentation_changes_bucket_allocation(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id, ws_utc=9 * 60, we_utc=17 * 60, ot_th=480)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        # Tokyo 09:00–17:00 local; 2026-06-10 07:00 UTC = 16:00 JST → in local window
        db.add(
            LabourRuleSet(
                id=str(uuid.uuid4()),
                name="Tokyo",
                region_code="JP",
                timezone_name="Asia/Tokyo",
                active=True,
                applies_to_contract_id=c.id,
                normal_workday_start_minutes=9 * 60,
                normal_workday_end_minutes=17 * 60,
                weekend_policy="weekday_window",
                holiday_public_policy="normal_window",
                holiday_company_policy="normal_window",
            )
        )
        job = Job(customer_id=cust.id, contract_id=c.id, address="1", assigned_engineer_id=engineer_id, status="open")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 10, 7, 30, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        r_tokyo = compute_job_labour_costing(db, job_id=job.id)
        assert r_tokyo["out_of_hours_minutes"] == 0
        assert r_tokyo["regular_minutes"] == 30

        # Same punch without rule set: 07:00 UTC is before 09:00 UTC window → OOH
        db.query(LabourRuleSet).filter(LabourRuleSet.applies_to_contract_id == c.id).delete()
        job2 = Job(customer_id=cust.id, address="2", assigned_engineer_id=engineer_id, status="open")
        db.add(job2)
        db.flush()
        db.add(Punch(user_id=engineer_id, job_id=job2.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job2.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        r_legacy = compute_job_labour_costing(db, job_id=job2.id)
        assert r_legacy["out_of_hours_minutes"] == 30
        assert r_legacy["regular_minutes"] == 0
    finally:
        db.close()


def test_missing_labour_rule_emits_warning_not_silent_precision(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.labour_costing_service import compute_job_labour_costing

    db = SessionLocal()
    try:
        _eng_profile(db, engineer_id=engineer_id)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        job = Job(customer_id=cust.id, address="1", assigned_engineer_id=engineer_id, status="open")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        r = compute_job_labour_costing(db, job_id=job.id)
        assert any("no_labour_rule_set_configured" in w for w in r["warnings"])
        assert r["labour_rules_attribution"]["resolution_source"] == "legacy"
        assert r["rules_completeness_status"] == "partial"
    finally:
        db.close()


def test_job_costing_endpoint_exposes_rule_attribution(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch

    rs_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        rs = LabourRuleSet(
            id=rs_id,
            name="API RS",
            region_code="UK",
            timezone_name="Europe/London",
            active=True,
            applies_to_contract_id=c.id,
        )
        db.add(rs)
        job = Job(customer_id=cust.id, contract_id=c.id, address="1", assigned_engineer_id=engineer_id, status="open")
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        jid = job.id
    finally:
        db.close()

    r = client.get(f"/jobs/{jid}/costing", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["labour_rules_attribution"]["labour_rule_set_id"] == rs_id
    assert body["labour_rules_attribution"]["resolution_source"] == "contract"


def test_contract_profitability_labour_rules_summary(client, admin_token, engineer_id):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.crm.models import Customer
    from backend.app.modules.dispatch.models import Job
    from backend.app.modules.labour.models import LabourRuleSet
    from backend.app.modules.time_tracking.models import Punch
    from backend.app.services.contract_profitability_service import build_contract_profitability
    from backend.app.services.job_costing import persist_job_cost_snapshot

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        _eng_profile(db, engineer_id=engineer_id)
        cust = Customer(name="C", email=f"c-{uuid.uuid4().hex[:6]}@example.com")
        db.add(cust)
        db.flush()
        c = Contract(
            customer_id=cust.id,
            name="Co",
            contract_code=f"CC-{uuid.uuid4().hex[:6]}",
            contract_type="full_maintenance",
            term_start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            next_ppm_due_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(c)
        db.flush()
        db.add(
            LabourRuleSet(
                id=str(uuid.uuid4()),
                name="P",
                region_code="UK",
                timezone_name="Europe/London",
                active=True,
                applies_to_contract_id=c.id,
            )
        )
        job = Job(
            customer_id=cust.id,
            contract_id=c.id,
            address="1",
            assigned_engineer_id=engineer_id,
            status="completed",
            resolved_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.flush()
        t0 = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 10, 13, 0, tzinfo=timezone.utc)
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="in", occurred_at=t0, latitude=51.0, longitude=-0.1))
        db.add(Punch(user_id=engineer_id, job_id=job.id, kind="out", occurred_at=t1, latitude=51.0, longitude=-0.1))
        db.commit()
        _approve_all_punches(db, admin.id)
        persist_job_cost_snapshot(db, job_id=job.id, commit=True)
        cid = c.id
    finally:
        db.close()

    db = SessionLocal()
    try:
        perf = build_contract_profitability(db, contract_id=cid, period_window="year_to_date")
        assert "labour_rules" in perf
        assert perf["labour_rules"]["snapshots_without_rule_set_id"] == 0
        assert perf["labour_rules"]["worst_completeness"] in ("clean", "partial")
    finally:
        db.close()


def test_recommendation_holiday_policy_without_calendar(client, admin_token):
    from backend.app.db.session import SessionLocal
    from backend.app.modules.labour.models import LabourRuleSet
    from backend.app.modules.ops.models import OperationalRecommendation
    from backend.app.services import recommendation_engine as rec_engine

    db = SessionLocal()
    try:
        rs = LabourRuleSet(
            id=str(uuid.uuid4()),
            name="Bad cal",
            region_code="X",
            timezone_name="UTC",
            active=True,
            holiday_calendar_id=None,
            holiday_public_policy="doubletime",
        )
        db.add(rs)
        db.commit()
        rec_engine.run_recommendation_scan(db)
        q = (
            db.query(OperationalRecommendation)
            .filter(OperationalRecommendation.recommendation_key == f"labour_rules:holiday_policy_without_calendar:{rs.id}")
            .first()
        )
        assert q is not None
        assert q.status == "open"
    finally:
        db.close()
