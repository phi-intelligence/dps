"""§5.18 holiday calendar feed import + §5.19 AI-assisted drafting APIs."""
from __future__ import annotations

import json

from backend.tests.test_contract_amendment_activation import _admin_token, _auth
from backend.app.services.holiday_calendar_feed_service import (
    parse_ics_holiday_days,
    parse_json_holiday_days,
)


def test_parse_ics_holiday_days_basic():
    ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;VALUE=DATE:20251225
SUMMARY:Christmas Day
END:VEVENT
BEGIN:VEVENT
DTSTART:20260101
SUMMARY:New Year\\, Ltd
END:VEVENT
END:VCALENDAR
"""
    rows = parse_ics_holiday_days(ics)
    assert len(rows) == 2
    assert rows[0][0].isoformat() == "2025-12-25"
    assert rows[0][1] == "Christmas Day"
    assert rows[1][1] == "New Year, Ltd"


def test_parse_json_holiday_days_basic():
    raw = json.dumps(
        [
            {"date": "2025-07-04", "label": "Independence", "day_type": "public_holiday"},
            {"date": "2025-12-31", "name": "NYE"},
        ]
    )
    rows = parse_json_holiday_days(raw)
    assert len(rows) == 2
    assert rows[0][2] == "public_holiday"
    assert rows[1][1] == "NYE"
    assert rows[1][2] == "public_holiday"


def test_labour_calendar_feed_import_dry_run(client, monkeypatch):
    admin = _admin_token(client)
    cr = client.post(
        "/labour/calendars",
        headers=_auth(admin),
        json={
            "name": "Feed Test Cal",
            "region_code": "GB",
            "timezone_name": "Europe/London",
            "external_feed_format": "ics",
        },
    )
    assert cr.status_code == 201, cr.text
    cal_id = cr.json()["id"]

    ics = (
        "BEGIN:VCALENDAR\nBEGIN:VEVENT\nDTSTART;VALUE=DATE:20300101\n"
        "SUMMARY:Future Day\nEND:VEVENT\nEND:VCALENDAR\n"
    )

    def _fake_fetch(_url: str):
        return (ics, "text/calendar")

    monkeypatch.setattr(
        "backend.app.services.holiday_calendar_feed_service.fetch_feed_body",
        _fake_fetch,
    )

    imp = client.post(
        f"/labour/calendars/{cal_id}/import-feed",
        headers=_auth(admin),
        json={"feed_url": "https://example.invalid/cal.ics", "dry_run": True},
    )
    assert imp.status_code == 200, imp.text
    body = imp.json()
    assert body["dry_run"] is True
    assert body["imported_days"] == 1
    assert body["status"] == "ok"

    days = client.get(f"/labour/calendars/{cal_id}/days", headers=_auth(admin))
    assert days.status_code == 200
    assert days.json() == []


def test_labour_calendar_feed_import_upserts_days(client, monkeypatch):
    admin = _admin_token(client)
    cr = client.post(
        "/labour/calendars",
        headers=_auth(admin),
        json={
            "name": "Feed Upsert Cal",
            "region_code": "GB",
            "timezone_name": "Europe/London",
            "external_feed_format": "ics",
        },
    )
    cal_id = cr.json()["id"]
    ics = (
        "BEGIN:VCALENDAR\nBEGIN:VEVENT\nDTSTART;VALUE=DATE:20300202\n"
        "SUMMARY:Two\nEND:VEVENT\nEND:VCALENDAR\n"
    )
    monkeypatch.setattr(
        "backend.app.services.holiday_calendar_feed_service.fetch_feed_body",
        lambda _u: (ics, "text/calendar"),
    )
    imp = client.post(
        f"/labour/calendars/{cal_id}/import-feed",
        headers=_auth(admin),
        json={"feed_url": "https://example.invalid/x.ics", "dry_run": False},
    )
    assert imp.status_code == 200, imp.text
    assert imp.json()["imported_days"] == 1
    days = client.get(f"/labour/calendars/{cal_id}/days", headers=_auth(admin))
    assert len(days.json()) == 1
    assert days.json()[0]["label"] == "Two"


def test_ai_drafting_503_when_not_configured(client):
    admin = _admin_token(client)
    lr = client.post("/crm/leads", headers=_auth(admin), json={"name": "AI Lead", "status": "new"})
    assert lr.status_code == 201, lr.text
    lid = lr.json()["id"]
    r = client.post(
        "/ai/drafting/assist",
        headers=_auth(admin),
        json={"task": "follow_up_notes", "lead_id": lid},
    )
    assert r.status_code == 503
    assert "AI-assisted drafting" in r.json()["detail"] or "Gemini" in r.json()["detail"]


def test_ai_drafting_200_when_mocked(client, monkeypatch):
    monkeypatch.setenv("PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED", "1")
    monkeypatch.setenv("GEMINI_ENABLED", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-used")

    admin = _admin_token(client)
    lr = client.post("/crm/leads", headers=_auth(admin), json={"name": "AI Lead 2", "status": "new"})
    lid = lr.json()["id"]

    monkeypatch.setattr(
        "backend.app.modules.ai.drafting_routes.ai.run_text_prompt",
        lambda *a, **k: "Internal note: call back Tuesday.",
    )
    r = client.post(
        "/ai/drafting/assist",
        headers=_auth(admin),
        json={"task": "follow_up_notes", "lead_id": lid},
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert "Tuesday" in j["suggested_text"]
    assert j["disclaimer"]


def test_ai_drafting_forbidden_without_permission(client):
    from backend.tests.test_labour_rules_calendars import _login

    tok = _login(client, username="engineer@example.com", password="engineer")
    r = client.post(
        "/ai/drafting/assist",
        headers=_auth(tok),
        json={"task": "follow_up_notes", "lead_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert r.status_code == 403
