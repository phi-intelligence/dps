"""
Generate and lifecycle-manage formal repricing proposals (CPQ-style) from repricing reviews.

Does not mutate Contract commercial fields. Deterministic, auditable generation rules.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ContractRepricingProposalLine,
    ContractRepricingReview,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


REASON_LINE_MAP: dict[str, tuple[str, str]] = {
    "margin_pressure": ("burden_adjustment", "Margin / cost pressure adjustment"),
    "contract_margin_deterioration": ("burden_adjustment", "Margin deterioration vs prior period"),
    "reactive_burden": ("reactive_allowance", "Reactive workload allowance"),
    "contract_high_reactive_burden": ("reactive_allowance", "High reactive service burden"),
    "contract_negative_margin": ("base_contract_value", "Contract value correction (negative margin signal)"),
    "contract_repricing_opportunity": ("miscellaneous", "Commercial repricing opportunity"),
    "recommendation_action": ("miscellaneous", "Follow-up from operational recommendation"),
    "test": ("miscellaneous", "Test / manual reason"),
}


def _safe_ref_part(code: str) -> str:
    x = re.sub(r"[^A-Za-z0-9]+", "-", code).strip("-").upper()
    return (x[:16] or "CTR")[:16]


def _log_action(
    db: Session,
    *,
    contract_id: str,
    review_id: str | None,
    action_type: str,
    summary: str,
    user_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    db.add(
        ContractCommercialActionLog(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            review_id=review_id,
            action_type=action_type,
            action_summary=summary,
            performed_by_user_id=user_id,
            performed_at=utc_now(),
            payload_json=_dumps(payload) if payload else None,
        )
    )


def supersede_prior_proposals(
    db: Session, *, contract_id: str, new_proposal_id: str, user_id: str
) -> int:
    q = (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.contract_id == contract_id,
            ContractRepricingProposal.id != new_proposal_id,
            ContractRepricingProposal.proposal_status.notin_(["superseded", "withdrawn"]),
        )
        .all()
    )
    n = 0
    for p in q:
        p.proposal_status = "superseded"
        p.superseded_by_proposal_id = new_proposal_id
        p.updated_at = utc_now()
        n += 1
    if n:
        _log_action(
            db,
            contract_id=contract_id,
            review_id=None,
            action_type="repricing_proposal_superseded",
            summary=f"Superseded {n} prior proposal(s) by new proposal {new_proposal_id}",
            user_id=user_id,
            payload={"new_proposal_id": new_proposal_id, "count": n},
        )
    return n


def generate_proposal_from_repricing_review(
    db: Session,
    *,
    contract_id: str,
    repricing_review_id: str,
    generated_by_user_id: str,
    currency: str = "GBP",
    supersede_previous: bool = False,
    commit: bool = True,
) -> ContractRepricingProposal:
    contract = db.get(Contract, contract_id)
    rr = db.get(ContractRepricingReview, repricing_review_id)
    if not contract or not rr:
        raise ValueError("Contract or repricing review not found")
    if rr.contract_id != contract_id:
        raise ValueError("Repricing review does not belong to contract")

    codes: list[str] = []
    raw_codes = _loads(rr.repricing_reason_codes_json)
    if isinstance(raw_codes, list):
        codes = [str(x) for x in raw_codes]

    current = rr.current_contract_value
    if current is None:
        current = contract.contract_value
    proposed = rr.proposed_contract_value

    modes: list[str] = []
    warnings: list[str] = []
    line_specs: list[dict[str, Any]] = []

    margin_summary = _loads(rr.margin_summary_json) if rr.margin_summary_json else None
    burden_summary = _loads(rr.burden_summary_json) if rr.burden_summary_json else None

    if proposed is not None:
        modes.append("direct_proposed_value")
        cur_f = float(current) if current is not None else None
        prop_f = float(proposed)
        var_amt = (prop_f - cur_f) if cur_f is not None else None
        var_pct = None
        if cur_f is not None and abs(cur_f) > 1e-9 and var_amt is not None:
            var_pct = round((var_amt / cur_f) * 100.0, 4)
        line_specs.append(
            {
                "line_type": "base_contract_value",
                "code": "BASE",
                "title": "Annual / contract value (proposed)",
                "description": "Primary contract value change derived from repricing review proposed_contract_value.",
                "quantity": 1.0,
                "unit": "contract",
                "current_unit_price": cur_f,
                "proposed_unit_price": prop_f,
                "current_line_total": cur_f,
                "proposed_line_total": prop_f,
                "variance_amount": var_amt,
                "variance_percent": var_pct,
                "justification_json": _dumps({"source": "repricing_review", "field": "proposed_contract_value"}),
                "sort_order": 0,
            }
        )
    else:
        if codes:
            modes.append("reason_code_draft")
            warnings.append("no_explicit_proposed_value:structured_draft_requires_commercial_confirmation")
            for i, code in enumerate(codes):
                lt, title = REASON_LINE_MAP.get(code, ("miscellaneous", f"Adjustment: {code}"))
                line_specs.append(
                    {
                        "line_type": lt,
                        "code": code,
                        "title": title,
                        "description": f"Draft line from repricing reason code `{code}` — confirm pricing before customer release.",
                        "quantity": 1.0,
                        "unit": "ea",
                        "current_unit_price": float(current) if current is not None else None,
                        "proposed_unit_price": None,
                        "current_line_total": float(current) if current is not None and i == 0 else None,
                        "proposed_line_total": 0.0,
                        "variance_amount": None,
                        "variance_percent": None,
                        "justification_json": _dumps({"source": "reason_code", "code": code}),
                        "sort_order": i,
                    }
                )
        if margin_summary or burden_summary:
            modes.append("burden_backed_justification")
            line_specs.append(
                {
                    "line_type": "burden_adjustment",
                    "code": "BURDEN_SUMMARY",
                    "title": "Margin / burden signals (non-quantified)",
                    "description": "Profitability and burden summaries attached for internal review; no automatic price computed.",
                    "quantity": 1.0,
                    "unit": "ea",
                    "current_unit_price": None,
                    "proposed_unit_price": None,
                    "current_line_total": None,
                    "proposed_line_total": 0.0,
                    "variance_amount": None,
                    "variance_percent": None,
                    "justification_json": _dumps(
                        {"margin_summary": margin_summary or {}, "burden_summary": burden_summary or {}}
                    ),
                    "sort_order": len(line_specs),
                }
            )

    if not line_specs:
        modes.append("incomplete_basis")
        warnings.append("no_proposed_value_no_reason_codes:minimal_placeholder_line")
        line_specs.append(
            {
                "line_type": "miscellaneous",
                "code": "INCOMPLETE",
                "title": "Incomplete repricing basis",
                "description": "Add proposed contract value or reason codes on the repricing review, then regenerate if needed.",
                "quantity": 1.0,
                "unit": "ea",
                "current_line_total": float(current) if current is not None else None,
                "proposed_line_total": float(current) if current is not None else 0.0,
                "variance_amount": 0.0,
                "variance_percent": None,
                "justification_json": _dumps({"source": "system", "warning": "incomplete"}),
                "sort_order": 0,
            }
        )

    prop_status = "draft" if (proposed is None and warnings) else "generated"

    ref = f"RPP-{_safe_ref_part(contract.contract_code)}-{uuid.uuid4().hex[:10].upper()}"

    basis: dict[str, Any] = {
        "repricing_review_id": rr.id,
        "contract_id": contract_id,
        "generation_modes": modes,
        "warnings": warnings,
        "currency": currency,
    }
    change_summary: dict[str, Any] = {
        "headline": "Repricing commercial proposal generated from structured review inputs.",
        "modes": modes,
        "warnings": warnings,
        "line_count": len(line_specs),
    }

    pid = str(uuid.uuid4())
    prop = ContractRepricingProposal(
        id=pid,
        contract_id=contract_id,
        repricing_review_id=rr.id,
        review_id=rr.review_id,
        proposal_status=prop_status,
        proposal_reference=ref,
        currency=currency,
        current_contract_value=float(current) if current is not None else None,
        proposed_contract_value=float(proposed) if proposed is not None else None,
        generated_at=utc_now(),
        generated_by_user_id=generated_by_user_id,
        pricing_basis_json=_dumps(basis),
        change_summary_json=_dumps(change_summary),
    )
    db.add(prop)
    db.flush()

    for spec in line_specs:
        db.add(
            ContractRepricingProposalLine(
                id=str(uuid.uuid4()),
                proposal_id=pid,
                line_type=spec["line_type"],
                code=spec.get("code"),
                title=spec["title"],
                description=spec.get("description"),
                quantity=float(spec["quantity"]),
                unit=spec.get("unit") or "ea",
                current_unit_price=spec.get("current_unit_price"),
                proposed_unit_price=spec.get("proposed_unit_price"),
                current_line_total=spec.get("current_line_total"),
                proposed_line_total=float(spec["proposed_line_total"]),
                variance_amount=spec.get("variance_amount"),
                variance_percent=spec.get("variance_percent"),
                justification_json=spec.get("justification_json"),
                sort_order=int(spec.get("sort_order") or 0),
            )
        )

    if supersede_previous:
        supersede_prior_proposals(db, contract_id=contract_id, new_proposal_id=pid, user_id=generated_by_user_id)

    _log_action(
        db,
        contract_id=contract_id,
        review_id=rr.review_id,
        action_type="repricing_proposal_generated",
        summary=f"Repricing proposal {ref} generated ({prop_status})",
        user_id=generated_by_user_id,
        payload={"proposal_id": pid, "repricing_review_id": rr.id, "modes": modes},
    )

    if commit:
        db.commit()
        db.refresh(prop)
    else:
        db.flush()
        db.refresh(prop)
    return prop


def list_proposals_for_contract(db: Session, *, contract_id: str) -> list[ContractRepricingProposal]:
    return (
        db.query(ContractRepricingProposal)
        .filter(ContractRepricingProposal.contract_id == contract_id)
        .order_by(ContractRepricingProposal.created_at.desc())
        .all()
    )


def get_proposal(db: Session, *, proposal_id: str) -> ContractRepricingProposal | None:
    return db.get(ContractRepricingProposal, proposal_id)


def list_lines(db: Session, *, proposal_id: str) -> list[ContractRepricingProposalLine]:
    return (
        db.query(ContractRepricingProposalLine)
        .filter(ContractRepricingProposalLine.proposal_id == proposal_id)
        .order_by(ContractRepricingProposalLine.sort_order.asc(), ContractRepricingProposalLine.created_at.asc())
        .all()
    )


def latest_proposal_for_repricing_review(
    db: Session, *, repricing_review_id: str
) -> ContractRepricingProposal | None:
    return (
        db.query(ContractRepricingProposal)
        .filter(ContractRepricingProposal.repricing_review_id == repricing_review_id)
        .order_by(ContractRepricingProposal.created_at.desc())
        .first()
    )


def patch_proposal(
    db: Session,
    *,
    proposal_id: str,
    user_id: str,
    notes: str | None = None,
    effective_date: datetime | None = None,
    validity_end_date: datetime | None = None,
    metadata_json: dict[str, Any] | None = None,
    commit: bool = True,
) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status in ("superseded", "withdrawn", "ready_for_customer"):
        raise ValueError("Proposal cannot be edited in current status")
    if p.customer_release_status not in ("not_released", "ready_for_customer"):
        raise ValueError("Proposal cannot be edited after customer-facing release")
    if notes is not None:
        p.notes = notes
    if effective_date is not None:
        p.effective_date = effective_date
    if validity_end_date is not None:
        p.validity_end_date = validity_end_date
    if metadata_json is not None:
        p.metadata_json = _dumps(metadata_json)
    p.updated_at = utc_now()
    _log_action(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="repricing_proposal_patched",
        summary=f"Proposal {p.proposal_reference} updated",
        user_id=user_id,
        payload={"proposal_id": proposal_id},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
    return p


def mark_internal_review(db: Session, *, proposal_id: str, user_id: str, commit: bool = True) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status not in ("draft", "generated"):
        raise ValueError("Invalid transition to internal_review")
    p.proposal_status = "internal_review"
    p.updated_at = utc_now()
    _log_action(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="repricing_proposal_internal_review",
        summary=f"Proposal {p.proposal_reference} marked for internal review",
        user_id=user_id,
        payload={"proposal_id": proposal_id},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
    return p


def approve_internal(db: Session, *, proposal_id: str, user_id: str, commit: bool = True) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status != "internal_review":
        raise ValueError("Proposal must be in internal_review to approve internally")
    p.proposal_status = "approved_internal"
    p.approved_at = utc_now()
    p.approved_by_user_id = user_id
    p.updated_at = utc_now()
    _log_action(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="repricing_proposal_approved_internal",
        summary=f"Proposal {p.proposal_reference} approved internally",
        user_id=user_id,
        payload={"proposal_id": proposal_id},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
    return p


def mark_ready_for_customer(db: Session, *, proposal_id: str, user_id: str, commit: bool = True) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status != "approved_internal":
        raise ValueError("Proposal must be approved_internal before ready_for_customer")
    p.proposal_status = "ready_for_customer"
    p.ready_for_customer_at = utc_now()
    p.updated_at = utc_now()
    if p.customer_release_status == "not_released":
        p.customer_release_status = "ready_for_customer"
    _log_action(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="repricing_proposal_ready_for_customer",
        summary=f"Proposal {p.proposal_reference} marked ready for customer release (not sent automatically)",
        user_id=user_id,
        payload={"proposal_id": proposal_id},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
    return p


def withdraw_proposal(db: Session, *, proposal_id: str, user_id: str, commit: bool = True) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status in ("superseded", "withdrawn"):
        raise ValueError("Proposal already closed")
    if p.proposal_status == "ready_for_customer":
        raise ValueError("Withdraw not allowed after ready_for_customer; use superseding workflow")
    p.proposal_status = "withdrawn"
    p.updated_at = utc_now()
    _log_action(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="repricing_proposal_withdrawn",
        summary=f"Proposal {p.proposal_reference} withdrawn",
        user_id=user_id,
        payload={"proposal_id": proposal_id},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
    return p


def attach_stored_document(db: Session, *, proposal_id: str, document_id: str, commit: bool = True) -> None:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    p.stored_document_id = document_id
    p.updated_at = utc_now()
    if commit:
        db.commit()
    else:
        db.flush()


def dashboard_repricing_proposals(db: Session, *, limit: int = 200) -> dict[str, Any]:
    rows = db.query(ContractRepricingProposal).order_by(ContractRepricingProposal.updated_at.desc()).limit(limit).all()
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.proposal_status] = by_status.get(r.proposal_status, 0) + 1
    return {
        "total_listed": len(rows),
        "by_status": by_status,
        "rows": [
            {
                "proposal_id": r.id,
                "proposal_reference": r.proposal_reference,
                "contract_id": r.contract_id,
                "repricing_review_id": r.repricing_review_id,
                "proposal_status": r.proposal_status,
                "current_contract_value": r.current_contract_value,
                "proposed_contract_value": r.proposed_contract_value,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "stored_document_id": r.stored_document_id,
            }
            for r in rows
        ],
    }


def dashboard_repricing_readiness(db: Session, *, limit: int = 200) -> dict[str, Any]:
    """
    Approved repricing reviews lacking a non-superseded / non-withdrawn proposal.
    """
    from backend.app.modules.contracts.review_models import ContractRepricingReview

    approved = (
        db.query(ContractRepricingReview)
        .filter(ContractRepricingReview.approved.is_(True))
        .order_by(ContractRepricingReview.updated_at.desc())
        .limit(limit)
        .all()
    )
    missing: list[dict[str, Any]] = []
    for rr in approved:
        viable = (
            db.query(ContractRepricingProposal)
            .filter(
                ContractRepricingProposal.repricing_review_id == rr.id,
                ContractRepricingProposal.proposal_status.notin_(["superseded", "withdrawn"]),
            )
            .count()
        )
        latest = latest_proposal_for_repricing_review(db, repricing_review_id=rr.id)
        if viable == 0:
            missing.append(
                {
                    "contract_id": rr.contract_id,
                    "repricing_review_id": rr.id,
                    "approved": True,
                    "needs_proposal": True,
                    "latest_proposal_id": latest.id if latest else None,
                    "latest_proposal_status": latest.proposal_status if latest else None,
                }
            )
    return {
        "approved_repricing_reviews_checked": len(approved),
        "missing_proposal_count": len(missing),
        "rows": missing,
    }
