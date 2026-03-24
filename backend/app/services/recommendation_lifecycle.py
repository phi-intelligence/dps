"""
Recommendation lifecycle: cooldowns after close, reopen rules, scope suppressions,
occurrence-based severity escalation. Used by recommendation_engine._register.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.ops.models import (
    OperationalRecommendation,
    RecommendationOccurrenceEvent,
    RecommendationSuppression,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


SEVERITY_RANK: dict[str, int] = {"low": 1, "medium": 2, "high": 3, "critical": 4}
SEVERITY_ORDER: list[str] = ["low", "medium", "high", "critical"]


def severity_rank(sev: str) -> int:
    return SEVERITY_RANK.get((sev or "").lower(), 0)


def bump_severity(sev: str) -> str:
    s = (sev or "medium").lower()
    try:
        i = SEVERITY_ORDER.index(s)
    except ValueError:
        i = 1
    return SEVERITY_ORDER[min(i + 1, len(SEVERITY_ORDER) - 1)]


def _dismiss_cooldown_hours() -> float:
    return float(getattr(settings, "PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS", 24.0))


def _resolve_cooldown_hours() -> float:
    return float(getattr(settings, "PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS", 6.0))


def _escalation_window_hours() -> float:
    return float(getattr(settings, "PHI_DPS_OPS_REC_ESCALATION_WINDOW_HOURS", 168.0))


def _escalation_min_fires() -> int:
    return int(getattr(settings, "PHI_DPS_OPS_REC_ESCALATION_MIN_FIRES", 5))


def _escalation_enabled() -> bool:
    return getattr(settings, "PHI_DPS_OPS_REC_ESCALATION_ENABLED", True)


def prune_stale_occurrence_events(db: Session, *, older_than_hours: float | None = None) -> int:
    """Delete occurrence events outside retention (default: 2× escalation window)."""
    h = older_than_hours or (_escalation_window_hours() * 2)
    cutoff = utc_now() - timedelta(hours=h)
    n = db.query(RecommendationOccurrenceEvent).filter(RecommendationOccurrenceEvent.recorded_at < cutoff).delete()
    return int(n or 0)


def count_occurrences_in_window(db: Session, *, recommendation_key: str, now: datetime) -> int:
    since = now - timedelta(hours=_escalation_window_hours())
    return (
        db.query(RecommendationOccurrenceEvent)
        .filter(
            RecommendationOccurrenceEvent.recommendation_key == recommendation_key,
            RecommendationOccurrenceEvent.recorded_at >= since,
        )
        .count()
    )


def record_occurrence(db: Session, *, recommendation_key: str, now: datetime) -> None:
    import uuid

    db.add(
        RecommendationOccurrenceEvent(
            id=str(uuid.uuid4()),
            recommendation_key=recommendation_key,
            recorded_at=now,
        )
    )


def apply_occurrence_escalation(
    db: Session, *, recommendation_key: str, base_severity: str, now: datetime
) -> tuple[str, dict[str, Any]]:
    """If enough fires in rolling window, bump severity one step. Returns (severity, lifecycle_detail)."""
    extra: dict[str, Any] = {}
    if not _escalation_enabled():
        return base_severity, extra
    n = count_occurrences_in_window(db, recommendation_key=recommendation_key, now=now)
    min_f = _escalation_min_fires()
    # This emission is the (n+1)th after we record; bump when we're at or past the K-th fire.
    if n >= min_f - 1 and min_f > 0:
        bumped = bump_severity(base_severity)
        if bumped != base_severity:
            extra["occurrence_escalation"] = {
                "prior_fires_in_window": n,
                "window_hours": _escalation_window_hours(),
                "min_fires": min_f,
                "base_severity": base_severity,
                "escalated_to": bumped,
            }
            return bumped, extra
    return base_severity, extra


def last_closed_recommendation(db: Session, *, recommendation_key: str) -> OperationalRecommendation | None:
    return (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.recommendation_key == recommendation_key,
            OperationalRecommendation.status.in_(["dismissed", "resolved"]),
            OperationalRecommendation.resolved_at.isnot(None),
        )
        .order_by(OperationalRecommendation.resolved_at.desc())
        .first()
    )


def cooldown_blocks_new_open(
    db: Session,
    *,
    recommendation_key: str,
    new_severity: str,
    current_rule_version: str,
    now: datetime,
) -> tuple[bool, dict[str, Any]]:
    """
    After dismiss/resolve, block creating a new open row for a cooldown unless:
    - new severity is strictly higher than last closed severity, or
    - rule version changed since last close.
    Returns (blocked, explain_detail).
    """
    last = last_closed_recommendation(db, recommendation_key=recommendation_key)
    if not last:
        return False, {}
    if (last.source_rule_version or "") != (current_rule_version or ""):
        return False, {"reopen": "rule_version_changed", "previous_version": last.source_rule_version}
    if severity_rank(new_severity) > severity_rank(last.severity):
        return False, {"reopen": "severity_increased", "previous_severity": last.severity}

    closed_as = last.closed_as or "resolved"
    hours = _dismiss_cooldown_hours() if closed_as == "dismissed" else _resolve_cooldown_hours()
    if hours <= 0:
        return False, {}

    end = last.resolved_at
    if end is None:
        return False, {}
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    until = end + timedelta(hours=hours)
    if _aware(now) < until:
        return True, {
            "cooldown_blocked": True,
            "closed_as": closed_as,
            "cooldown_hours": hours,
            "cooldown_until": until.isoformat(),
            "last_closed_at": end.isoformat(),
        }
    return False, {"reopen": "cooldown_elapsed"}


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def active_global_suppression_applies(
    db: Session,
    *,
    recommendation_key: str,
    category: str,
    related_contract_id: str | None,
    related_site_id: str | None,
    now: datetime,
) -> bool:
    rows = (
        db.query(RecommendationSuppression)
        .filter(RecommendationSuppression.suppressed_until > now)
        .all()
    )
    for s in rows:
        if s.recommendation_key and s.recommendation_key == recommendation_key:
            return True
        if s.category and s.category == category:
            if s.contract_id and s.contract_id != related_contract_id:
                continue
            if s.site_id and s.site_id != related_site_id:
                continue
            return True
    return False


def merge_lifecycle_into_detail(detail: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    out = dict(detail)
    if lifecycle:
        lc = dict(out.get("lifecycle") or {})
        lc.update(lifecycle)
        out["lifecycle"] = lc
    return out
