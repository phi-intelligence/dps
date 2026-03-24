from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.competence.models import Qualification
from backend.app.modules.competence.schemas import QualificationCreateIn


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_qualification(db: Session, *, payload: QualificationCreateIn) -> Qualification:
    qual = Qualification(
        engineer_user_id=payload.engineer_user_id,
        competency=payload.competency,
        issued_at=payload.issued_at,
        expires_at=payload.expires_at,
        document_ref=payload.document_ref,
        status="active",
    )
    db.add(qual)
    db.commit()
    db.refresh(qual)
    return qual


def list_qualifications_for_engineer(db: Session, *, engineer_user_id: str, limit: int = 50, offset: int = 0) -> list[Qualification]:
    return (
        db.query(Qualification)
        .filter(Qualification.engineer_user_id == engineer_user_id)
        .order_by(Qualification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def validate_engineer_competencies(
    db: Session,
    *,
    engineer_id: str,
    required_competencies: list[str],
) -> None:
    now = utc_now()
    missing: list[str] = []
    for comp in required_competencies:
        ok = (
            db.query(Qualification)
            .filter(Qualification.engineer_user_id == engineer_id, Qualification.competency == comp, Qualification.status == "active")
            .all()
        )
        def _to_utc_aware(dt: datetime) -> datetime:
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

        has_valid = any(
            (q.expires_at is None)
            or (_to_utc_aware(q.expires_at) >= now)  # type: ignore[arg-type]
            for q in ok
        )
        if not has_valid:
            missing.append(comp)
    if missing:
        raise ValueError(f"Engineer missing/expired competencies: {', '.join(missing)}")

