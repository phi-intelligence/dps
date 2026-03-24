"""
Structured renewal / repricing / commercial review workflow (service layer).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingReview,
    ContractReview,
)
from backend.app.modules.ops.models import OperationalRecommendation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


TERMINAL_REVIEW_STATUSES = frozenset({"completed", "cancelled"})

OPEN_REVIEW_STATUSES = frozenset(
    {"open", "in_review", "waiting_input", "ready_for_decision"}
)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _touch_review(r: ContractReview) -> None:
    r.updated_at = utc_now()


def _touch_repricing(r: ContractRepricingReview) -> None:
    r.updated_at = utc_now()


def log_commercial_action(
    db: Session,
    *,
    contract_id: str,
    review_id: str | None,
    action_type: str,
    action_summary: str,
    performed_by_user_id: str,
    notes: str | None = None,
    payload: dict[str, Any] | None = None,
) -> ContractCommercialActionLog:
    row = ContractCommercialActionLog(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        review_id=review_id,
        action_type=action_type,
        action_summary=action_summary,
        performed_by_user_id=performed_by_user_id,
        performed_at=utc_now(),
        notes=notes,
        payload_json=_dumps(payload) if payload is not None else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def find_open_review(db: Session, *, contract_id: str, review_type: str) -> ContractReview | None:
    return (
        db.query(ContractReview)
        .filter(
            ContractReview.contract_id == contract_id,
            ContractReview.review_type == review_type,
            ContractReview.status.not_in(TERMINAL_REVIEW_STATUSES),
        )
        .order_by(ContractReview.opened_at.desc())
        .first()
    )


def create_contract_review(
    db: Session,
    *,
    contract_id: str,
    review_type: str,
    triggered_by: str,
    triggered_reason: str,
    summary: str,
    performed_by_user_id: str,
    priority: str = "normal",
    due_at: datetime | None = None,
    notes: str | None = None,
    metadata: dict[str, Any] | None = None,
    source_recommendation_id: str | None = None,
    assigned_to_user_id: str | None = None,
    status: str = "open",
    dedupe: bool = True,
) -> tuple[ContractReview, bool]:
    """
    Returns (review, created_new). If dedupe and an open review of same type exists, returns it with created_new=False.
    """
    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")

    if dedupe:
        existing = find_open_review(db, contract_id=contract_id, review_type=review_type)
        if existing:
            log_commercial_action(
                db,
                contract_id=contract_id,
                review_id=existing.id,
                action_type="review_deduped",
                action_summary=f"Open {review_type} review already exists; no duplicate created.",
                performed_by_user_id=performed_by_user_id,
                payload={"existing_review_id": existing.id},
            )
            return existing, False

    now = utc_now()
    row = ContractReview(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        review_type=review_type,
        status=status,
        triggered_by=triggered_by,
        triggered_reason=triggered_reason,
        opened_at=now,
        due_at=due_at,
        assigned_to_user_id=assigned_to_user_id,
        priority=priority,
        summary=summary,
        notes=notes,
        metadata_json=_dumps(metadata) if metadata else None,
        source_recommendation_id=source_recommendation_id,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()

    # Align contract renewal visibility
    c.renewal_review_last_opened_at = now
    if review_type == "renewal":
        c.renewal_status = "in_review"
    elif review_type == "repricing":
        c.renewal_status = "repricing_review"
        c.repricing_required = True
    elif review_type == "risk_review":
        c.account_attention_level = "high"
        if c.renewal_status in ("not_due", "due_soon"):
            c.renewal_status = "at_risk"
    elif review_type == "health_review":
        c.renewal_status = "in_review"

    db.add(c)
    db.commit()
    db.refresh(row)

    log_commercial_action(
        db,
        contract_id=contract_id,
        review_id=row.id,
        action_type="review_opened",
        action_summary=f"Opened {review_type} review: {summary[:200]}",
        performed_by_user_id=performed_by_user_id,
        payload={"review_type": review_type, "triggered_by": triggered_by},
    )
    return row, True


def list_reviews_for_contract(db: Session, *, contract_id: str) -> list[ContractReview]:
    return (
        db.query(ContractReview)
        .filter(ContractReview.contract_id == contract_id)
        .order_by(ContractReview.opened_at.desc())
        .all()
    )


def list_reviews_global(
    db: Session,
    *,
    status: str | None = None,
    review_type: str | None = None,
    priority: str | None = None,
    assigned_to_user_id: str | None = None,
    contract_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ContractReview]:
    q = db.query(ContractReview).order_by(ContractReview.due_at.asc().nullslast(), ContractReview.opened_at.desc())
    if status:
        q = q.filter(ContractReview.status == status)
    if review_type:
        q = q.filter(ContractReview.review_type == review_type)
    if priority:
        q = q.filter(ContractReview.priority == priority)
    if assigned_to_user_id:
        q = q.filter(ContractReview.assigned_to_user_id == assigned_to_user_id)
    if contract_id:
        q = q.filter(ContractReview.contract_id == contract_id)
    return q.offset(offset).limit(limit).all()


def get_review(db: Session, *, review_id: str) -> ContractReview | None:
    return db.get(ContractReview, review_id)


def patch_review(
    db: Session,
    *,
    review_id: str,
    performed_by_user_id: str,
    status: str | None = None,
    assigned_to_user_id: str | None = None,
    priority: str | None = None,
    due_at: datetime | None = None,
    notes: str | None = None,
    summary: str | None = None,
) -> ContractReview:
    r = db.get(ContractReview, review_id)
    if not r:
        raise ValueError("Review not found")
    if status is not None:
        old = r.status
        r.status = status
        log_commercial_action(
            db,
            contract_id=r.contract_id,
            review_id=r.id,
            action_type="review_status_changed",
            action_summary=f"Status {old} → {status}",
            performed_by_user_id=performed_by_user_id,
        )
    if assigned_to_user_id is not None:
        r.assigned_to_user_id = assigned_to_user_id
        log_commercial_action(
            db,
            contract_id=r.contract_id,
            review_id=r.id,
            action_type="account_manager_assigned",
            action_summary="Review owner updated",
            performed_by_user_id=performed_by_user_id,
            payload={"assigned_to_user_id": assigned_to_user_id},
        )
    if priority is not None:
        r.priority = priority
    if due_at is not None:
        r.due_at = due_at
    if notes is not None:
        r.notes = notes
        log_commercial_action(
            db,
            contract_id=r.contract_id,
            review_id=r.id,
            action_type="commercial_note",
            action_summary="Notes updated on review",
            performed_by_user_id=performed_by_user_id,
        )
    if summary is not None:
        r.summary = summary
    _touch_review(r)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _apply_decision_to_contract(contract: Contract, decision: str) -> None:
    contract.renewal_decision = decision
    if decision == "renew_as_is":
        contract.renewal_status = "ready_to_renew"
        contract.repricing_required = False
    elif decision == "renew_with_repricing":
        contract.renewal_status = "repricing_review"
        contract.repricing_required = True
    elif decision == "monitor":
        contract.renewal_status = "at_risk"
        contract.churn_risk_level = contract.churn_risk_level or "medium"
        contract.account_attention_level = "high"
    elif decision == "escalate":
        contract.account_attention_level = "critical"
        contract.renewal_status = "in_review"
    elif decision == "exit_contract":
        contract.renewal_status = "exit_pending"
        contract.churn_risk_level = "high"
    elif decision == "defer":
        contract.renewal_status = "not_due"
        contract.renewal_review_due_at = utc_now() + timedelta(days=90)


def record_review_decision(
    db: Session,
    *,
    review_id: str,
    decision: str,
    performed_by_user_id: str,
    notes: str | None = None,
) -> ContractReview:
    r = db.get(ContractReview, review_id)
    if not r:
        raise ValueError("Review not found")
    if r.status in TERMINAL_REVIEW_STATUSES:
        raise ValueError("Review already closed")

    now = utc_now()
    r.decision = decision
    r.decided_at = now
    r.decided_by_user_id = performed_by_user_id
    r.status = "completed"
    if notes:
        r.notes = (r.notes + "\n" if r.notes else "") + f"[decision] {notes}"
    _touch_review(r)

    c = db.get(Contract, r.contract_id)
    if c:
        _apply_decision_to_contract(c, decision)
        db.add(c)

    db.add(r)
    db.commit()
    db.refresh(r)

    log_commercial_action(
        db,
        contract_id=r.contract_id,
        review_id=r.id,
        action_type="decision_recorded",
        action_summary=f"Decision: {decision}",
        performed_by_user_id=performed_by_user_id,
        notes=notes,
        payload={"decision": decision},
    )
    return r


def get_or_create_repricing_review(
    db: Session,
    *,
    contract_id: str,
    performed_by_user_id: str,
    current_contract_value: float | None = None,
    proposed_contract_value: float | None = None,
    repricing_reason_codes: list[str] | None = None,
    margin_summary: dict[str, Any] | None = None,
    burden_summary: dict[str, Any] | None = None,
    recommendation_basis: dict[str, Any] | None = None,
    customer_risk_level: str = "medium",
    notes: str | None = None,
) -> tuple[ContractRepricingReview, ContractReview, bool]:
    """
    Ensures an open repricing review exists and returns (repricing_row, parent_review, created_new_parent).
    """
    open_rev = find_open_review(db, contract_id=contract_id, review_type="repricing")
    created_parent = False
    if not open_rev:
        open_rev, created_parent = create_contract_review(
            db,
            contract_id=contract_id,
            review_type="repricing",
            triggered_by="manual",
            triggered_reason="Repricing review opened",
            summary="Repricing review",
            performed_by_user_id=performed_by_user_id,
            priority="high",
        )
        # create_contract_review commits; refresh
        open_rev = db.get(ContractReview, open_rev.id)

    rr = (
        db.query(ContractRepricingReview)
        .filter(ContractRepricingReview.review_id == open_rev.id)
        .order_by(ContractRepricingReview.created_at.desc())
        .first()
    )
    if rr:
        return rr, open_rev, created_parent

    now = utc_now()
    rr = ContractRepricingReview(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        review_id=open_rev.id,
        current_contract_value=current_contract_value,
        proposed_contract_value=proposed_contract_value,
        repricing_reason_codes_json=_dumps(repricing_reason_codes or []),
        margin_summary_json=_dumps(margin_summary) if margin_summary else None,
        burden_summary_json=_dumps(burden_summary) if burden_summary else None,
        recommendation_basis_json=_dumps(recommendation_basis) if recommendation_basis else None,
        customer_risk_level=customer_risk_level,
        notes=notes,
        created_at=now,
        updated_at=now,
    )
    db.add(rr)
    db.commit()
    db.refresh(rr)

    log_commercial_action(
        db,
        contract_id=contract_id,
        review_id=open_rev.id,
        action_type="repricing_flagged",
        action_summary="Repricing review record created",
        performed_by_user_id=performed_by_user_id,
    )
    return rr, open_rev, created_parent


def get_repricing_for_contract(db: Session, *, contract_id: str) -> ContractRepricingReview | None:
    open_rev = find_open_review(db, contract_id=contract_id, review_type="repricing")
    if not open_rev:
        return None
    return (
        db.query(ContractRepricingReview)
        .filter(ContractRepricingReview.review_id == open_rev.id)
        .order_by(ContractRepricingReview.created_at.desc())
        .first()
    )


def patch_repricing_review(
    db: Session,
    *,
    contract_id: str,
    performed_by_user_id: str,
    proposed_contract_value: float | None = None,
    current_contract_value: float | None = None,
    repricing_reason_codes: list[str] | None = None,
    margin_summary: dict[str, Any] | None = None,
    burden_summary: dict[str, Any] | None = None,
    recommendation_basis: dict[str, Any] | None = None,
    customer_risk_level: str | None = None,
    notes: str | None = None,
    approved: bool | None = None,
) -> ContractRepricingReview:
    rr = get_repricing_for_contract(db, contract_id=contract_id)
    if not rr:
        raise ValueError("No active repricing review for contract")

    if proposed_contract_value is not None:
        rr.proposed_contract_value = proposed_contract_value
    if current_contract_value is not None:
        rr.current_contract_value = current_contract_value
    if repricing_reason_codes is not None:
        rr.repricing_reason_codes_json = _dumps(repricing_reason_codes)
    if margin_summary is not None:
        rr.margin_summary_json = _dumps(margin_summary)
    if burden_summary is not None:
        rr.burden_summary_json = _dumps(burden_summary)
    if recommendation_basis is not None:
        rr.recommendation_basis_json = _dumps(recommendation_basis)
    if customer_risk_level is not None:
        rr.customer_risk_level = customer_risk_level
    if notes is not None:
        rr.notes = notes
    if approved is not None:
        rr.approved = approved
        if approved:
            rr.approved_at = utc_now()
            rr.approved_by_user_id = performed_by_user_id
        else:
            rr.approved_at = None
            rr.approved_by_user_id = None

    _touch_repricing(rr)
    db.add(rr)
    db.commit()
    db.refresh(rr)

    log_commercial_action(
        db,
        contract_id=contract_id,
        review_id=rr.review_id,
        action_type="repricing_updated",
        action_summary="Repricing review fields updated",
        performed_by_user_id=performed_by_user_id,
    )
    return rr


# --- Recommendation & signal integration ---

RECOMMENDATION_TYPE_TO_REVIEW: dict[str, tuple[str, str]] = {
    "contract_renewal_risk": ("renewal", "Renewal risk signal from operational intelligence"),
    "contract_nearing_expiry": ("renewal", "Contract approaching end / renewal review date"),
    "contract_negative_margin": ("repricing", "Negative or unsustainable margin signal"),
    "contract_margin_deterioration": ("repricing", "Margin deterioration vs prior period"),
    "contract_repricing_opportunity": ("repricing", "Commercial repricing opportunity"),
    "contract_repeated_sla_breaches": ("risk_review", "Repeated SLA breaches on contract"),
    "contract_high_reactive_burden": ("health_review", "High reactive workload vs plan"),
    "contract_site_cost_hotspot": ("health_review", "Site-level cost / workload hotspot"),
    "contract_asset_reactive_hotspot": ("health_review", "Asset-level reactive hotspot"),
}


def create_review_from_recommendation(
    db: Session,
    *,
    recommendation_id: str,
    performed_by_user_id: str,
    review_type: str | None = None,
) -> tuple[ContractReview, bool]:
    rec = db.get(OperationalRecommendation, recommendation_id)
    if not rec:
        raise ValueError("Recommendation not found")
    cid = rec.related_contract_id or (rec.entity_id if rec.entity_type == "contract" else None)
    if not cid:
        raise ValueError("Recommendation has no linked contract")

    mapped = RECOMMENDATION_TYPE_TO_REVIEW.get(rec.recommendation_type)
    rtype = review_type or (mapped[0] if mapped else None)
    if not rtype:
        raise ValueError(f"No review mapping for recommendation_type={rec.recommendation_type}")

    reason = mapped[1] if mapped else rec.summary
    summary = f"{rec.title}: {rec.summary}"[:2000]

    row, created = create_contract_review(
        db,
        contract_id=cid,
        review_type=rtype,
        triggered_by="recommendation",
        triggered_reason=reason,
        summary=summary,
        performed_by_user_id=performed_by_user_id,
        priority="high" if rec.severity in ("critical", "high") else "normal",
        source_recommendation_id=rec.id,
        metadata={"recommendation_type": rec.recommendation_type, "recommendation_key": rec.recommendation_key},
    )
    if rtype == "repricing":
        get_or_create_repricing_review(
            db,
            contract_id=cid,
            performed_by_user_id=performed_by_user_id,
            repricing_reason_codes=[rec.recommendation_type],
            recommendation_basis={
                "recommendation_type": rec.recommendation_type,
                "recommendation_id": rec.id,
            },
            notes="Linked from operational recommendation",
        )
    return row, created


def apply_signal_rules_for_contract(
    db: Session,
    *,
    contract_id: str,
    performed_by_user_id: str,
    period_window: str = "90d",
) -> list[dict[str, Any]]:
    """
    Controlled rules: uses profitability payload to suggest structured reviews (deduped).
    """
    from backend.app.services import contract_profitability_service as cps

    out: list[dict[str, Any]] = []
    try:
        p = cps.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    except ValueError:
        return out

    margin = p.get("margin") or {}
    margin_pct = margin.get("gross_percent")
    margin_pct_f = float(margin_pct) if margin_pct is not None else None
    renewal = p.get("renewal") or {}
    health = p.get("health") or {}
    renewal_risk = str(renewal.get("renewal_risk_level") or "").lower()

    # Negative margin → repricing
    if margin_pct_f is not None and margin_pct_f < 0:
        _, created = create_contract_review(
            db,
            contract_id=contract_id,
            review_type="repricing",
            triggered_by="profitability_signal",
            triggered_reason="Negative margin in profitability window",
            summary=f"Margin ~{margin_pct_f:.1f}% — repricing review suggested",
            performed_by_user_id=performed_by_user_id,
            priority="critical",
            metadata={"gross_percent": margin_pct_f, "period_window": period_window},
            dedupe=True,
        )
        out.append({"rule": "negative_margin", "review_type": "repricing", "created": created})

    # Renewal risk from intelligence payload
    if renewal_risk in ("high", "critical") or renewal.get("renewal_status") in ("at_risk", "review_required"):
        _, created = create_contract_review(
            db,
            contract_id=contract_id,
            review_type="renewal",
            triggered_by="profitability_signal",
            triggered_reason="Renewal / churn risk elevated",
            summary="Renewal risk elevated from profitability renewal intelligence",
            performed_by_user_id=performed_by_user_id,
            priority="high",
            metadata={"renewal_risk_level": renewal_risk, "renewal": renewal},
            dedupe=True,
        )
        out.append({"rule": "renewal_risk", "review_type": "renewal", "created": created})

    op = p.get("operational") or {}
    if int(op.get("sla_breach_count_jobs_in_period") or 0) >= 3:
        _, created = create_contract_review(
            db,
            contract_id=contract_id,
            review_type="risk_review",
            triggered_by="rules_engine",
            triggered_reason="Multiple SLA breaches in period",
            summary=f"SLA breaches in period: {op.get('sla_breach_count_jobs_in_period')}",
            performed_by_user_id=performed_by_user_id,
            priority="high",
            metadata={"operational": op},
            dedupe=True,
        )
        out.append({"rule": "sla_breaches", "review_type": "risk_review", "created": created})

    jobs = p.get("jobs") or {}
    rj = float(jobs.get("reactive_created_in_period") or 0)
    pj = float(jobs.get("planned_created_in_period") or 0)
    reactive_ratio = rj / max(rj + pj, 1)
    if reactive_ratio >= 0.55:
        _, created = create_contract_review(
            db,
            contract_id=contract_id,
            review_type="health_review",
            triggered_by="rules_engine",
            triggered_reason="High reactive job mix",
            summary=f"Reactive job ratio ~{reactive_ratio:.0%}",
            performed_by_user_id=performed_by_user_id,
            metadata={"health": health},
            dedupe=True,
        )
        out.append({"rule": "reactive_burden", "review_type": "health_review", "created": created})

    return out


def sync_structured_review_after_catalog_action(
    db: Session,
    *,
    contract_id: str,
    action_type: str,
    performed_by_user_id: str,
    recommendation_id: str | None,
    recommendation_type: str | None,
    recommendation_summary: str | None,
) -> None:
    """Called after confirmed recommendation actions that should open structured reviews."""
    summary_base = (recommendation_summary or "Commercial follow-up from recommendation action")[:1500]
    meta = {"recommendation_id": recommendation_id, "action_type": action_type}

    if action_type == "mark_for_renewal_review":
        create_contract_review(
            db,
            contract_id=contract_id,
            review_type="renewal",
            triggered_by="recommendation",
            triggered_reason="User confirmed mark-for-renewal-review action",
            summary=summary_base,
            performed_by_user_id=performed_by_user_id,
            source_recommendation_id=recommendation_id,
            metadata=meta,
            dedupe=True,
        )
    elif action_type == "mark_for_repricing_review":
        create_contract_review(
            db,
            contract_id=contract_id,
            review_type="repricing",
            triggered_by="recommendation",
            triggered_reason="User confirmed mark-for-repricing-review action",
            summary=summary_base,
            performed_by_user_id=performed_by_user_id,
            priority="high",
            source_recommendation_id=recommendation_id,
            metadata=meta,
            dedupe=True,
        )
        get_or_create_repricing_review(
            db,
            contract_id=contract_id,
            performed_by_user_id=performed_by_user_id,
            repricing_reason_codes=["recommendation_action"],
            recommendation_basis={"recommendation_type": recommendation_type},
            notes="Opened from recommendation action",
        )
    elif action_type == "create_contract_review_note":
        create_contract_review(
            db,
            contract_id=contract_id,
            review_type="health_review",
            triggered_by="recommendation",
            triggered_reason="Structured health review from contract review note action",
            summary=summary_base,
            performed_by_user_id=performed_by_user_id,
            source_recommendation_id=recommendation_id,
            metadata=meta,
            dedupe=True,
        )


# --- Dashboards ---

def _review_row_to_pipeline_dict(db: Session, r: ContractReview) -> dict[str, Any]:
    c = db.get(Contract, r.contract_id)
    return {
        "review_id": r.id,
        "contract_id": r.contract_id,
        "contract_code": c.contract_code if c else None,
        "contract_name": c.name if c else None,
        "review_type": r.review_type,
        "status": r.status,
        "priority": r.priority,
        "due_at": r.due_at.isoformat() if r.due_at else None,
        "assigned_to_user_id": r.assigned_to_user_id,
        "opened_at": r.opened_at.isoformat(),
        "summary": r.summary,
        "decision": r.decision,
    }


def dashboard_review_pipeline(
    db: Session,
    *,
    status: str | None = None,
    priority: str | None = None,
    assigned_to_user_id: str | None = None,
    review_type: str | None = None,
    due_within_days: int | None = None,
    unassigned_only: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    q = db.query(ContractReview)
    if status:
        q = q.filter(ContractReview.status == status)
    else:
        q = q.filter(ContractReview.status.in_(OPEN_REVIEW_STATUSES))
    if priority:
        q = q.filter(ContractReview.priority == priority)
    if assigned_to_user_id:
        q = q.filter(ContractReview.assigned_to_user_id == assigned_to_user_id)
    if review_type:
        q = q.filter(ContractReview.review_type == review_type)
    if unassigned_only:
        q = q.filter(ContractReview.assigned_to_user_id.is_(None))
    if due_within_days is not None:
        until = utc_now() + timedelta(days=due_within_days)
        q = q.filter(
            and_(
                ContractReview.due_at.isnot(None),
                ContractReview.due_at <= until,
            )
        )
    rows = q.order_by(ContractReview.due_at.asc().nullslast(), ContractReview.priority.desc()).limit(limit).all()
    return {
        "count": len(rows),
        "items": [_review_row_to_pipeline_dict(db, r) for r in rows],
    }


def dashboard_repricing(
    db: Session,
    *,
    approved: bool | None = None,
    customer_risk_level: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    q = (
        db.query(ContractRepricingReview, ContractReview)
        .join(ContractReview, ContractRepricingReview.review_id == ContractReview.id)
        .filter(ContractReview.status.in_(OPEN_REVIEW_STATUSES))
    )
    if approved is not None:
        q = q.filter(ContractRepricingReview.approved == approved)
    if customer_risk_level:
        q = q.filter(ContractRepricingReview.customer_risk_level == customer_risk_level)
    q = q.order_by(ContractRepricingReview.updated_at.desc()).limit(limit)
    items = []
    for rr, rev in q.all():
        c = db.get(Contract, rr.contract_id)
        items.append(
            {
                "repricing_id": rr.id,
                "review_id": rr.review_id,
                "contract_id": rr.contract_id,
                "contract_code": c.contract_code if c else None,
                "current_contract_value": rr.current_contract_value,
                "proposed_contract_value": rr.proposed_contract_value,
                "repricing_reason_codes": _loads(rr.repricing_reason_codes_json) or [],
                "customer_risk_level": rr.customer_risk_level,
                "approved": rr.approved,
                "review_status": rev.status,
                "assigned_to_user_id": rev.assigned_to_user_id,
            }
        )
    return {"count": len(items), "items": items}


def dashboard_renewal_pipeline(
    db: Session,
    *,
    renewal_status: str | None = None,
    churn_risk_level: str | None = None,
    attention_level: str | None = None,
    due_within_days: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    q = db.query(Contract).filter(Contract.status == "active")
    if renewal_status:
        q = q.filter(Contract.renewal_status == renewal_status)
    else:
        q = q.filter(
            Contract.renewal_status.in_(
                ("due_soon", "in_review", "repricing_review", "at_risk", "ready_to_renew", "exit_pending")
            )
        )
    if churn_risk_level:
        q = q.filter(Contract.churn_risk_level == churn_risk_level)
    if attention_level:
        q = q.filter(Contract.account_attention_level == attention_level)
    if due_within_days is not None:
        until = utc_now() + timedelta(days=due_within_days)
        q = q.filter(
            or_(
                and_(Contract.renewal_review_due_at.isnot(None), Contract.renewal_review_due_at <= until),
                and_(Contract.renewal_review_date.isnot(None), Contract.renewal_review_date <= until),
            )
        )
    rows = q.order_by(Contract.renewal_review_due_at.asc().nullslast(), Contract.renewal_review_date.asc().nullslast()).limit(limit).all()
    items = []
    for c in rows:
        items.append(
            {
                "contract_id": c.id,
                "contract_code": c.contract_code,
                "name": c.name,
                "renewal_status": c.renewal_status,
                "renewal_review_due_at": c.renewal_review_due_at.isoformat() if c.renewal_review_due_at else None,
                "renewal_review_date": c.renewal_review_date.isoformat() if c.renewal_review_date else None,
                "renewal_decision": c.renewal_decision,
                "repricing_required": c.repricing_required,
                "account_attention_level": c.account_attention_level,
                "churn_risk_level": c.churn_risk_level,
                "contract_value": c.contract_value,
            }
        )
    return {"count": len(items), "items": items}


def list_commercial_actions(
    db: Session, *, contract_id: str, limit: int = 50
) -> list[ContractCommercialActionLog]:
    return (
        db.query(ContractCommercialActionLog)
        .filter(ContractCommercialActionLog.contract_id == contract_id)
        .order_by(ContractCommercialActionLog.performed_at.desc())
        .limit(limit)
        .all()
    )


def list_recent_completed_reviews(db: Session, *, limit: int = 25) -> list[dict[str, Any]]:
    rows = (
        db.query(ContractReview)
        .filter(ContractReview.status == "completed")
        .order_by(ContractReview.decided_at.desc().nullslast(), ContractReview.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [_review_row_to_pipeline_dict(db, r) | {"decided_at": r.decided_at.isoformat() if r.decided_at else None} for r in rows]
