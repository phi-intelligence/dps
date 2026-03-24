"""
§5.18 — Fetch public or vendor holiday feeds (ICS / JSON) and upsert ``HolidayCalendarDay`` rows.

Admin-triggered only (``CAN_MANAGE_LABOUR_RULES``). No autonomous scheduling.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.app.modules.labour.models import HolidayCalendar
from backend.app.modules.labour.service import upsert_holiday_calendar_days

MAX_FEED_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT_S = 30.0
USER_AGENT = "PHI-DPS-HolidayCalendarImport/1.0"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _unfold_ics(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    acc: list[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and acc:
            acc[-1] += line[1:]
        else:
            acc.append(line)
    return "\n".join(acc)


def _ics_unescape(s: str) -> str:
    return (
        s.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def parse_ics_holiday_days(content: str) -> list[tuple[date, str]]:
    """Parse VEVENT blocks; use first DTSTART (date portion) and SUMMARY per event."""
    text = _unfold_ics(content)
    out: list[tuple[date, str]] = []
    for m in re.finditer(r"(?is)BEGIN:VEVENT\s*(.*?)\s*END:VEVENT", text):
        block = m.group(1)
        dm = re.search(r"^DTSTART(?:[^:\r\n]*):(\d{8})", block, re.MULTILINE)
        if not dm:
            continue
        ymd = dm.group(1)
        try:
            y, mo, d = int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8])
            cal_d = date(y, mo, d)
        except ValueError:
            continue
        sm = re.search(r"^SUMMARY(?:[^:\r\n]*):(.+)$", block, re.MULTILINE | re.IGNORECASE)
        label = "Holiday"
        if sm:
            label = _ics_unescape(sm.group(1).strip()) or "Holiday"
        out.append((cal_d, label))
    return out


def parse_json_holiday_days(content: str) -> list[tuple[date, str, str]]:
    """
    Expect JSON array of objects: ``date`` (ISO YYYY-MM-DD), optional ``label`` / ``name``,
    optional ``day_type`` (default ``public_holiday``).
    """
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("JSON feed must be a top-level array")
    out: list[tuple[date, str, str]] = []
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"JSON feed item {i} must be an object")
        ds = row.get("date")
        if not ds or not isinstance(ds, str):
            raise ValueError(f"JSON feed item {i} missing string 'date'")
        try:
            cal_d = date.fromisoformat(ds.strip()[:10])
        except ValueError as e:
            raise ValueError(f"JSON feed item {i} has invalid date") from e
        label = row.get("label") or row.get("name") or "Holiday"
        if not isinstance(label, str):
            label = str(label)
        day_type = row.get("day_type") or "public_holiday"
        if not isinstance(day_type, str):
            day_type = str(day_type)
        out.append((cal_d, label.strip() or "Holiday", day_type.strip() or "public_holiday"))
    return out


def fetch_feed_body(url: str) -> tuple[str, str | None]:
    """Return (text, content_type). Raises on HTTP / size errors."""
    with httpx.Client(timeout=FETCH_TIMEOUT_S, follow_redirects=True) as client:
        r = client.get(url, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    ct = r.headers.get("content-type")
    if len(r.content) > MAX_FEED_BYTES:
        raise ValueError(f"Feed larger than {MAX_FEED_BYTES} bytes")
    return r.text, ct


def import_holiday_calendar_feed(
    db: Session,
    *,
    calendar_id: str,
    feed_url: str | None = None,
    dry_run: bool = False,
    apply_region_code: str | None = None,
) -> dict[str, Any]:
    cal = db.get(HolidayCalendar, calendar_id)
    if not cal:
        raise ValueError("Calendar not found")
    url = (feed_url or "").strip() or (cal.external_feed_url or "").strip()
    if not url:
        raise ValueError("No feed URL: set external_feed_url on the calendar or pass feed_url")

    fmt = (cal.external_feed_format or "ics").strip().lower()
    if fmt not in ("ics", "json"):
        raise ValueError("Calendar external_feed_format must be ics or json")

    try:
        body, _ct = fetch_feed_body(url)
        if fmt == "ics":
            parsed = parse_ics_holiday_days(body)
            triples = [(d, lab, "public_holiday") for d, lab in parsed]
        else:
            triples = parse_json_holiday_days(body)

        if apply_region_code and apply_region_code.strip():
            cal.region_code = apply_region_code.strip()
            db.commit()
            db.refresh(cal)

        if dry_run:
            cal.last_feed_import_at = _utc_now()
            cal.last_feed_import_status = "dry_run"
            cal.last_feed_import_detail = f"parsed {len(triples)} day(s); no DB day rows written"
            db.commit()
            db.refresh(cal)
            return {
                "calendar_id": cal.id,
                "format_used": fmt,
                "imported_days": len(triples),
                "dry_run": True,
                "status": "ok",
                "detail": cal.last_feed_import_detail,
            }

        n = upsert_holiday_calendar_days(db, calendar_id=calendar_id, days=triples)
        row = db.get(HolidayCalendar, calendar_id)
        if not row:
            raise RuntimeError("Calendar missing after import")
        row.last_feed_import_at = _utc_now()
        row.last_feed_import_status = "ok"
        row.last_feed_import_detail = f"upserted {n} day row(s) from feed"
        db.commit()
        db.refresh(row)
        return {
            "calendar_id": row.id,
            "format_used": fmt,
            "imported_days": n,
            "dry_run": False,
            "status": "ok",
            "detail": row.last_feed_import_detail,
        }
    except Exception as e:
        row = db.get(HolidayCalendar, calendar_id)
        if row:
            row.last_feed_import_at = _utc_now()
            row.last_feed_import_status = "error"
            row.last_feed_import_detail = str(e)[:2000]
            db.commit()
        raise
