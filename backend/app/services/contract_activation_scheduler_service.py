"""
Scheduled / batch processing for due contract amendments (idempotent).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.contract_version_models import ContractActivationRun
from backend.app.modules.contracts.models import Contract
from backend.app.services.contract_version_service import _ensure_utc, execute_amendment_activation, utc_now


def find_due_amendments(db: Session, *, now: datetime | None = None) -> list[ContractAmendment]:
    """Amendments approved/scheduled with effective_date <= now, not yet activated."""
    now = now or utc_now()
    now_utc = _ensure_utc(now) or now
    rows = (
        db.query(ContractAmendment)
        .filter(ContractAmendment.status.in_(("approved", "scheduled")))
        .order_by(ContractAmendment.effective_date.asc())
        .all()
    )
    out: list[ContractAmendment] = []
    for a in rows:
        if a.approval_required and not a.approved_at:
            continue
        eff = _ensure_utc(a.effective_date)
        if eff is not None and eff <= now_utc:
            out.append(a)
    return out


def run_due_amendment_activations(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    actor_user_id: str,
) -> dict[str, Any]:
    """
    Activate all due amendments. Idempotent per amendment.
    If dry_run, returns candidate list only (no mutations).
    """
    now = now or utc_now()
    due = find_due_amendments(db, now=now)
    if limit is not None:
        due = due[:limit]

    if dry_run:
        return {
            "dry_run": True,
            "now": now.isoformat(),
            "candidate_count": len(due),
            "candidates": [
                {
                    "amendment_id": a.id,
                    "amendment_reference": a.amendment_reference,
                    "contract_id": a.contract_id,
                    "effective_date": a.effective_date.isoformat() if a.effective_date else None,
                }
                for a in due
            ],
        }

    results: list[dict[str, Any]] = []
    for a in due:
        key = f"scheduled:{a.id}"
        try:
            _am, run = execute_amendment_activation(
                db,
                amendment_id=a.id,
                actor_user_id=actor_user_id,
                run_type="scheduled",
                idempotency_key=key,
                commit=True,
            )
            results.append(
                {
                    "amendment_id": a.id,
                    "run_id": run.id,
                    "status": run.status,
                    "result_summary": run.result_summary,
                }
            )
        except Exception as e:
            results.append(
                {
                    "amendment_id": a.id,
                    "status": "error",
                    "error": str(e),
                }
            )

    return {
        "dry_run": False,
        "now": now.isoformat(),
        "processed": len(results),
        "results": results,
    }


def activate_scheduled_amendment(
    db: Session,
    *,
    amendment_id: str,
    now: datetime | None = None,
    actor_user_id: str,
) -> tuple[Any, ContractActivationRun]:
    """Single-amendment scheduled-style activation (same rules as batch)."""
    now = now or utc_now()
    due = find_due_amendments(db, now=now)
    ids = {x.id for x in due}
    if amendment_id not in ids:
        raise ValueError("Amendment is not due for scheduled activation")
    return execute_amendment_activation(
        db,
        amendment_id=amendment_id,
        actor_user_id=actor_user_id,
        run_type="scheduled",
        idempotency_key=f"scheduled:{amendment_id}",
        commit=True,
    )


def list_activation_runs(
    db: Session,
    *,
    amendment_id: str | None = None,
    contract_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ContractActivationRun]:
    q = db.query(ContractActivationRun)
    if amendment_id:
        q = q.filter(ContractActivationRun.amendment_id == amendment_id)
    if contract_id:
        q = q.filter(ContractActivationRun.contract_id == contract_id)
    if status:
        q = q.filter(ContractActivationRun.status == status)
    return q.order_by(ContractActivationRun.started_at.desc()).offset(offset).limit(limit).all()


def get_activation_run(db: Session, *, run_id: str) -> ContractActivationRun | None:
    return db.get(ContractActivationRun, run_id)


def dashboard_activations_due(db: Session, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    due = find_due_amendments(db, now=now)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    overdue = [a for a in due if _ensure_utc(a.effective_date) and _ensure_utc(a.effective_date) < today_start]
    due_today = [a for a in due if a not in overdue]
    return {
        "now": now.isoformat(),
        "due_today_count": len(due_today),
        "overdue_count": len(overdue),
        "due_today": [
            {
                "amendment_id": a.id,
                "contract_id": a.contract_id,
                "effective_date": a.effective_date.isoformat() if a.effective_date else None,
            }
            for a in due_today
        ],
        "overdue": [
            {
                "amendment_id": a.id,
                "contract_id": a.contract_id,
                "effective_date": a.effective_date.isoformat() if a.effective_date else None,
            }
            for a in overdue
        ],
    }


def dashboard_activation_failures(db: Session, *, limit: int = 50) -> dict[str, Any]:
    rows = (
        db.query(ContractActivationRun)
        .filter(ContractActivationRun.status == "failed")
        .order_by(ContractActivationRun.completed_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "failures": [
            {
                "run_id": r.id,
                "amendment_id": r.amendment_id,
                "contract_id": r.contract_id,
                "attempt_number": r.attempt_number,
                "result_summary": r.result_summary,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ],
        "count": len(rows),
    }


def dashboard_future_activations(db: Session, *, now: datetime | None = None, limit: int = 50) -> dict[str, Any]:
    now = now or utc_now()
    now_utc = _ensure_utc(now) or now
    rows = (
        db.query(ContractAmendment)
        .filter(
            ContractAmendment.status.in_(("approved", "scheduled")),
        )
        .order_by(ContractAmendment.effective_date.asc())
        .limit(limit * 2)
        .all()
    )
    future = []
    for a in rows:
        eff = _ensure_utc(a.effective_date)
        if eff and eff > now_utc and (not a.approval_required or a.approved_at):
            future.append(a)
        if len(future) >= limit:
            break
    return {
        "count": len(future),
        "items": [
            {
                "amendment_id": a.id,
                "contract_id": a.contract_id,
                "effective_date": a.effective_date.isoformat() if a.effective_date else None,
                "status": a.status,
            }
            for a in future
        ],
    }


def dashboard_version_history_summary(db: Session, *, limit: int = 30) -> dict[str, Any]:
    from backend.app.modules.contracts.contract_version_models import ContractVersion

    recent = (
        db.query(ContractVersion)
        .order_by(ContractVersion.created_at.desc())
        .limit(limit)
        .all()
    )

    def _human_summary(v: ContractVersion) -> str | None:
        if not v.change_summary_json:
            return None
        try:
            p = json.loads(v.change_summary_json)
            if isinstance(p, dict):
                return p.get("human_readable_summary")
        except Exception:
            return None
        return None

    by_type: dict[str, int] = {}
    for v in recent:
        by_type[v.version_type] = by_type.get(v.version_type, 0) + 1

    c_ids = {v.contract_id for v in recent}
    code_by_cid: dict[str, str | None] = {}
    if c_ids:
        for c in db.query(Contract).filter(Contract.id.in_(c_ids)).all():
            code_by_cid[c.id] = c.contract_code

    return {
        "recent_versions": [
            {
                "version_id": v.id,
                "contract_id": v.contract_id,
                "contract_code": code_by_cid.get(v.contract_id),
                "version_number": v.version_number,
                "version_type": v.version_type,
                "source_amendment_id": v.source_amendment_id,
                "effective_from": v.effective_from.isoformat() if v.effective_from else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "is_active": v.effective_to is None,
                "human_readable_summary": _human_summary(v),
            }
            for v in recent
        ],
        "count": len(recent),
        "recent_versions_by_type_counts": by_type,
    }


def dashboard_recently_updated_contracts(db: Session, *, limit: int = 40) -> dict[str, Any]:
    """Surface recent manual and amendment-driven version churn for commercial ops."""
    from backend.app.modules.contracts.contract_version_models import ContractVersion

    q = (
        db.query(ContractVersion)
        .filter(
            ContractVersion.version_type.in_(("manual_update", "amendment_activation", "initial"))
        )
        .order_by(ContractVersion.created_at.desc())
        .limit(limit)
        .all()
    )

    def _snippet(v: ContractVersion) -> str | None:
        if not v.change_summary_json:
            return None
        try:
            p = json.loads(v.change_summary_json)
            if isinstance(p, dict):
                s = p.get("human_readable_summary")
                if isinstance(s, str) and len(s) > 240:
                    return s[:237] + "..."
                return s
        except Exception:
            return None
        return None

    return {
        "items": [
            {
                "version_id": v.id,
                "contract_id": v.contract_id,
                "version_number": v.version_number,
                "version_type": v.version_type,
                "source_amendment_id": v.source_amendment_id,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "is_active": v.effective_to is None,
                "contract_value": v.contract_value,
                "summary_snippet": _snippet(v),
            }
            for v in q
        ],
        "count": len(q),
    }


def dashboard_recently_activated_amendments(db: Session, *, limit: int = 20) -> dict[str, Any]:
    rows = (
        db.query(ContractAmendment)
        .filter(ContractAmendment.status == "activated")
        .order_by(ContractAmendment.activated_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "amendment_id": a.id,
                "contract_id": a.contract_id,
                "activated_at": a.activated_at.isoformat() if a.activated_at else None,
                "resulting_contract_version_id": a.resulting_contract_version_id,
            }
            for a in rows
        ],
        "count": len(rows),
    }
