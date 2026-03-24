from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.sla.models import SlaPolicy
from backend.app.modules.sla.schemas import SlaPolicyCreateIn, SlaPolicyPatchIn


def create_sla_policy(db: Session, *, payload: SlaPolicyCreateIn) -> SlaPolicy:
    p = SlaPolicy(
        name=payload.name.strip(),
        priority=payload.priority.strip(),
        response_target_minutes=payload.response_target_minutes,
        attendance_target_minutes=payload.attendance_target_minutes,
        resolution_target_minutes=payload.resolution_target_minutes,
        service_window_json=payload.service_window_json or "{}",
        warning_threshold_percent_json=payload.warning_threshold_percent_json or "{}",
        escalation_notes=payload.escalation_notes,
        active=payload.active,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def list_sla_policies(db: Session, *, active_only: bool = False) -> list[SlaPolicy]:
    q = db.query(SlaPolicy).order_by(SlaPolicy.priority.asc(), SlaPolicy.name.asc())
    if active_only:
        q = q.filter(SlaPolicy.active.is_(True))
    return q.all()


def get_sla_policy(db: Session, *, policy_id: str) -> SlaPolicy | None:
    return db.get(SlaPolicy, policy_id)


def patch_sla_policy(db: Session, *, policy_id: str, payload: SlaPolicyPatchIn) -> SlaPolicy:
    p = db.get(SlaPolicy, policy_id)
    if not p:
        raise ValueError("SLA policy not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p
