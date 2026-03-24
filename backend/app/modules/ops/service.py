from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.modules.ops.models import OperationalRecommendation, RecommendationSuppression
from backend.app.modules.ops.schemas import RecommendationOut, RecommendationSummaryOut
from backend.app.services import recommendation_engine as rec_engine


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _apply_snooze_filter(q, *, now: datetime, include_suppressed: bool):
    if include_suppressed:
        return q
    return q.filter(
        or_(
            OperationalRecommendation.suppressed_until.is_(None),
            OperationalRecommendation.suppressed_until < now,
        )
    )


def list_recommendations(
    db: Session,
    *,
    status: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    related_job_id: str | None = None,
    related_contract_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    include_suppressed: bool = False,
) -> list[OperationalRecommendation]:
    now = utc_now()
    q = db.query(OperationalRecommendation).order_by(OperationalRecommendation.created_at.desc())
    q = _apply_snooze_filter(q, now=now, include_suppressed=include_suppressed)
    if status:
        q = q.filter(OperationalRecommendation.status == status)
    if category:
        q = q.filter(OperationalRecommendation.category == category)
    if severity:
        q = q.filter(OperationalRecommendation.severity == severity)
    if entity_type:
        q = q.filter(OperationalRecommendation.entity_type == entity_type)
    if entity_id:
        q = q.filter(OperationalRecommendation.entity_id == entity_id)
    if related_job_id:
        q = q.filter(OperationalRecommendation.related_job_id == related_job_id)
    if related_contract_id:
        q = q.filter(OperationalRecommendation.related_contract_id == related_contract_id)
    return q.offset(offset).limit(limit).all()


def get_recommendation(db: Session, *, recommendation_id: str) -> OperationalRecommendation | None:
    return db.get(OperationalRecommendation, recommendation_id)


def acknowledge_recommendation(
    db: Session, *, recommendation_id: str, user_id: str, notes: str | None = None
) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    if r.status != "open":
        raise ValueError("Only open recommendations can be acknowledged")
    now = utc_now()
    r.status = "acknowledged"
    r.acknowledged_at = now
    r.acknowledged_by_user_id = user_id
    if notes:
        r.resolution_notes = notes
    r.updated_at = now
    db.commit()
    db.refresh(r)
    return r


def resolve_recommendation(
    db: Session, *, recommendation_id: str, user_id: str, notes: str | None = None
) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    if r.status in ("resolved", "dismissed"):
        raise ValueError("Already closed")
    now = utc_now()
    r.status = "resolved"
    r.closed_as = "resolved"
    r.resolved_at = now
    r.acknowledged_by_user_id = r.acknowledged_by_user_id or user_id
    r.resolution_notes = notes or r.resolution_notes
    r.updated_at = now
    db.commit()
    db.refresh(r)
    return r


def dismiss_recommendation(
    db: Session, *, recommendation_id: str, user_id: str, notes: str | None = None
) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    if r.status in ("resolved", "dismissed"):
        raise ValueError("Already closed")
    now = utc_now()
    r.status = "dismissed"
    r.closed_as = "dismissed"
    r.resolved_at = now
    r.acknowledged_by_user_id = r.acknowledged_by_user_id or user_id
    r.resolution_notes = notes or "dismissed"
    r.updated_at = now
    db.commit()
    db.refresh(r)
    return r


def snooze_recommendation(
    db: Session, *, recommendation_id: str, hours: float, notes: str | None = None
) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    if r.status not in ("open", "acknowledged"):
        raise ValueError("Only open or acknowledged recommendations can be snoozed")
    now = utc_now()
    r.suppressed_until = now + timedelta(hours=hours)
    r.suppression_notes = notes
    r.updated_at = now
    db.commit()
    db.refresh(r)
    return r


def reopen_recommendation(
    db: Session, *, recommendation_id: str, user_id: str, notes: str | None = None
) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    if r.status not in ("dismissed", "resolved"):
        raise ValueError("Only closed recommendations can be reopened")
    dup = (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.recommendation_key == r.recommendation_key,
            OperationalRecommendation.status == "open",
            OperationalRecommendation.id != r.id,
        )
        .first()
    )
    if dup:
        raise ValueError("An open recommendation with this key already exists")
    now = utc_now()
    r.status = "open"
    r.closed_as = None
    r.resolved_at = None
    r.acknowledged_at = None
    r.acknowledged_by_user_id = user_id
    extra = f" | reopen: {notes}" if notes else " | reopen"
    r.resolution_notes = (r.resolution_notes or "") + extra
    r.updated_at = now
    db.commit()
    db.refresh(r)
    return r


def create_suppression(
    db: Session,
    *,
    user_id: str | None,
    recommendation_key: str | None,
    category: str | None,
    contract_id: str | None,
    site_id: str | None,
    hours: float,
    notes: str | None,
) -> RecommendationSuppression:
    if not recommendation_key and not category:
        raise ValueError("Provide recommendation_key and/or category")
    now = utc_now()
    s = RecommendationSuppression(
        id=str(uuid.uuid4()),
        recommendation_key=recommendation_key,
        category=category,
        contract_id=contract_id,
        site_id=site_id,
        suppressed_until=now + timedelta(hours=hours),
        notes=notes,
        created_by_user_id=user_id,
        created_at=now,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def list_suppressions(db: Session, *, active_only: bool = True) -> list[RecommendationSuppression]:
    q = db.query(RecommendationSuppression).order_by(RecommendationSuppression.suppressed_until.desc())
    if active_only:
        q = q.filter(RecommendationSuppression.suppressed_until > utc_now())
    return q.limit(200).all()


def delete_suppression(db: Session, *, suppression_id: str) -> None:
    s = db.get(RecommendationSuppression, suppression_id)
    if not s:
        raise ValueError("Suppression not found")
    db.delete(s)
    db.commit()


def run_full_scan(db: Session) -> dict[str, Any]:
    return rec_engine.run_recommendation_scan(db)


def dashboard_summary(db: Session) -> RecommendationSummaryOut:
    now = utc_now()
    q_open = db.query(OperationalRecommendation).filter(OperationalRecommendation.status == "open")
    q_open = _apply_snooze_filter(q_open, now=now, include_suppressed=False)
    open_rows = q_open.all()
    by_sev: dict[str, int] = {}
    by_cat: dict[str, int] = {}
    crit: list[RecommendationOut] = []
    high: list[RecommendationOut] = []
    for r in open_rows:
        by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
        by_cat[r.category] = by_cat.get(r.category, 0) + 1
        if r.severity == "critical":
            crit.append(RecommendationOut.from_orm_row(r))
        elif r.severity == "high":
            high.append(RecommendationOut.from_orm_row(r))

    stale_ack = 0
    cutoff = utc_now() - timedelta(days=3)
    for r in db.query(OperationalRecommendation).filter(OperationalRecommendation.status == "acknowledged").all():
        if r.acknowledged_at and r.acknowledged_at < cutoff:
            stale_ack += 1

    recent_resolved = (
        db.query(OperationalRecommendation)
        .filter(OperationalRecommendation.status == "resolved", OperationalRecommendation.resolved_at.isnot(None))
        .order_by(OperationalRecommendation.resolved_at.desc())
        .limit(15)
        .all()
    )

    return RecommendationSummaryOut(
        open_by_severity=by_sev,
        open_by_category=by_cat,
        critical_open=crit[:20],
        high_open=high[:20],
        stale_acknowledged_count=stale_ack,
        recently_resolved=[RecommendationOut.from_orm_row(x) for x in recent_resolved],
    )


def high_priority_feed(db: Session, *, limit: int = 25) -> list[RecommendationOut]:
    now = utc_now()
    q = db.query(OperationalRecommendation).filter(
        OperationalRecommendation.status == "open", OperationalRecommendation.severity.in_(["critical", "high"])
    )
    q = _apply_snooze_filter(q, now=now, include_suppressed=False)
    rows = q.all()
    sev_rank = {"critical": 0, "high": 1}
    rows = sorted(
        rows,
        key=lambda x: (sev_rank.get(x.severity, 9), -x.created_at.timestamp()),
    )[:limit]
    return [RecommendationOut.from_orm_row(r) for r in rows]


def by_category_feed(db: Session, *, category: str, limit: int = 50) -> list[RecommendationOut]:
    now = utc_now()
    q = db.query(OperationalRecommendation).filter(
        OperationalRecommendation.status == "open", OperationalRecommendation.category == category
    )
    q = _apply_snooze_filter(q, now=now, include_suppressed=False)
    rows = (
        q.order_by(OperationalRecommendation.severity.asc(), OperationalRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [RecommendationOut.from_orm_row(r) for r in rows]
