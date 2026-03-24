"""
Contract amendment / activation service.
Turns accepted customer proposals into auditable live contract amendments.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
)
from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.services import acceptance_policy_service as apol
from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _humanize_readiness_blocker(br: str) -> str:
    if "acceptance_policy_blocked" in br:
        return apol.humanize_policy_blocker(br)
    if br == "proposal_not_found":
        return "The repricing proposal was not found."
    if br.startswith("customer_response_status_not_accepted"):
        return "The customer must accept the proposal before creating an amendment."
    if br.startswith("invalid_release_state"):
        return "The proposal is not in a customer-released state suitable for amendment creation."
    if br.startswith("proposal_status_invalid"):
        return "This proposal status does not allow amendment creation (e.g. withdrawn or superseded)."
    if br == "proposal_expired":
        return "The proposal is past its customer response window; renew or re-release before proceeding."
    if br.startswith("amendment_already_exists"):
        return "An amendment already exists for this proposal."
    return br


def _safe_ref_part(s: str) -> str:
    return "".join(c for c in (s or "")[:20] if c.isalnum() or c in "-_") or "X"


def _log_commercial(
    db: Session,
    *,
    contract_id: str,
    review_id: str | None,
    action_type: str,
    summary: str,
    performed_by_user_id: str,
    amendment_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    p = payload or {}
    if amendment_id:
        p["amendment_id"] = amendment_id
    row = ContractCommercialActionLog(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        review_id=review_id,
        action_type=action_type,
        action_summary=summary,
        performed_by_user_id=performed_by_user_id,
        performed_at=utc_now(),
        payload_json=_dumps(p) if p else None,
    )
    db.add(row)


def _contract_snapshot(c: Contract) -> dict[str, Any]:
    """Snapshot of contract fields that can be amended."""
    return {
        "contract_id": c.id,
        "contract_code": c.contract_code,
        "contract_value": c.contract_value,
        "renewal_status": c.renewal_status,
        "renewal_review_due_at": str(c.renewal_review_due_at) if c.renewal_review_due_at else None,
        "term_end_at": str(c.term_end_at) if c.term_end_at else None,
        "renewal_review_date": str(c.renewal_review_date) if c.renewal_review_date else None,
        "repricing_required": c.repricing_required,
        "snapshot_at": utc_now().isoformat(),
    }


def evaluate_proposal_activation_readiness(
    db: Session,
    *,
    proposal_id: str,
) -> dict[str, Any]:
    """
    Evaluate if a proposal is ready for amendment creation and activation.
    Returns: ready, blocking_reasons[], warnings[], required_approval, effective_date_candidate
    """
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        mode = apol.acceptance_policy_mode()
        am_req, act_req = apol.requirement_bullets_for_mode(mode)
        return {
            "ready": False,
            "blocking_reasons": ["proposal_not_found"],
            "blocking_reason_messages": [_humanize_readiness_blocker("proposal_not_found")],
            "warnings": [],
            "required_approval": True,
            "effective_date_candidate": None,
            "proposal_id": proposal_id,
            "acceptance_policy_mode": mode,
            "policy_amendment_requirements": am_req,
            "policy_activation_requirements": act_req,
        }

    blocking: list[str] = []
    warnings: list[str] = []

    if p.customer_response_status != "accepted":
        blocking.append(
            f"customer_response_status_not_accepted: current={p.customer_response_status or 'none'}"
        )

    if p.customer_response_status == "accepted" and not getattr(p, "formal_acceptance_record_id", None):
        warnings.append("no_formal_acceptance_record: customer accepted without structured acceptance evidence")

    if p.customer_release_status in ("not_released", "ready_for_customer", "withdrawn", "expired"):
        blocking.append(f"invalid_release_state: {p.customer_release_status}")

    if p.proposal_status in ("superseded", "withdrawn"):
        blocking.append(f"proposal_status_invalid: {p.proposal_status}")

    if is_past_customer_expiry(p):
        blocking.append("proposal_expired")

    if not p.stored_document_id:
        warnings.append("no_proposal_document: document recommended before activation")

    # Check if amendment already exists for this proposal
    existing = (
        db.query(ContractAmendment)
        .filter(
            ContractAmendment.source_proposal_id == proposal_id,
            ContractAmendment.status.notin_(("rejected", "cancelled")),
        )
        .first()
    )
    if existing:
        blocking.append(f"amendment_already_exists: amendment_id={existing.id}")

    blocking.extend(apol.blockers_for_amendment_creation(db, proposal_id=proposal_id))

    effective_date_candidate = p.effective_date
    if not effective_date_candidate:
        effective_date_candidate = utc_now()

    required_approval = True  # Safe default for repricing amendments

    ready = len(blocking) == 0
    mode = apol.acceptance_policy_mode()
    am_req, act_req = apol.requirement_bullets_for_mode(mode)

    return {
        "ready": ready,
        "blocking_reasons": blocking,
        "blocking_reason_messages": [_humanize_readiness_blocker(b) for b in blocking],
        "warnings": warnings,
        "required_approval": required_approval,
        "effective_date_candidate": effective_date_candidate,
        "proposal_id": proposal_id,
        "acceptance_policy_mode": mode,
        "policy_amendment_requirements": am_req,
        "policy_activation_requirements": act_req,
    }


def create_contract_amendment_from_proposal(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    effective_date: datetime | None = None,
    notes: str | None = None,
) -> ContractAmendment:
    """
    Create amendment record from accepted proposal. Does not mutate contract.
    """
    readiness = evaluate_proposal_activation_readiness(db, proposal_id=proposal_id)
    if not readiness["ready"]:
        p0 = db.get(ContractRepricingProposal, proposal_id)
        if p0:
            for br in readiness["blocking_reasons"]:
                if "acceptance_policy_blocked_amendment" in br:
                    _log_commercial(
                        db,
                        contract_id=p0.contract_id,
                        review_id=p0.review_id,
                        action_type="proposal_acceptance_policy_blocked_amendment",
                        summary=f"Amendment creation blocked by acceptance policy: {br}",
                        performed_by_user_id=actor_user_id,
                        payload={"proposal_id": proposal_id, "reason": br},
                    )
            if any("acceptance_policy_blocked_amendment" in b for b in readiness["blocking_reasons"]):
                db.commit()
        raise ValueError(
            f"Proposal not ready for amendment: {readiness['blocking_reasons']}"
        )

    p = db.get(ContractRepricingProposal, proposal_id)
    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")

    prior_snapshot = _contract_snapshot(c)
    eff_date = effective_date or readiness["effective_date_candidate"]
    if eff_date and eff_date.tzinfo is None:
        eff_date = eff_date.replace(tzinfo=timezone.utc)

    ref = f"AM-{_safe_ref_part(c.contract_code)}-{uuid.uuid4().hex[:10].upper()}"
    approval_required = readiness["required_approval"]

    now = utc_now()
    eff_utc = _ensure_utc(eff_date) if eff_date else None
    if approval_required:
        status = "pending_approval"
    elif eff_utc and eff_utc > now:
        status = "scheduled"
    else:
        status = "approved"  # No approval required, effective now -> ready to activate

    amendment = ContractAmendment(
        id=str(uuid.uuid4()),
        contract_id=c.id,
        source_proposal_id=p.id,
        source_review_id=p.review_id,
        amendment_type="repricing",
        status=status,
        amendment_reference=ref,
        current_contract_value=p.current_contract_value,
        proposed_contract_value=p.proposed_contract_value,
        effective_date=eff_date,
        approval_required=approval_required,
        created_by_user_id=actor_user_id,
        notes=notes,
        pricing_basis_json=p.pricing_basis_json,
        change_summary_json=p.change_summary_json,
        prior_contract_snapshot_json=_dumps(prior_snapshot),
        metadata_json=_dumps({"source": "create_from_proposal", "proposal_id": proposal_id}),
    )
    db.add(amendment)
    db.flush()

    _log_commercial(
        db,
        contract_id=c.id,
        review_id=p.review_id,
        action_type="amendment_created",
        summary=f"Amendment {ref} created from accepted proposal {p.proposal_reference}",
        performed_by_user_id=actor_user_id,
        amendment_id=amendment.id,
        payload={"proposal_id": proposal_id, "status": status},
    )
    from backend.app.services import proposal_acceptance_service as pas

    pas.link_acceptance_to_amendment(
        db,
        proposal_id=proposal_id,
        amendment_id=amendment.id,
        actor_user_id=actor_user_id,
    )
    db.commit()
    db.refresh(amendment)
    return amendment


def submit_for_approval(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str,
) -> ContractAmendment:
    """Mark amendment as submitted for approval (no-op if already pending)."""
    a = db.get(ContractAmendment, amendment_id)
    if not a:
        raise ValueError("Amendment not found")
    if a.status not in ("draft", "scheduled"):
        raise ValueError(f"Cannot submit for approval from status {a.status}")
    a.status = "pending_approval"
    _log_commercial(
        db,
        contract_id=a.contract_id,
        review_id=a.source_review_id,
        action_type="amendment_submitted_for_approval",
        summary=f"Amendment {a.amendment_reference} submitted for approval",
        performed_by_user_id=actor_user_id,
        amendment_id=a.id,
    )
    db.commit()
    db.refresh(a)
    return a


def approve_amendment(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str,
    notes: str | None = None,
) -> ContractAmendment:
    """Approve amendment. Required before activation if approval_required."""
    a = db.get(ContractAmendment, amendment_id)
    if not a:
        raise ValueError("Amendment not found")
    if a.status != "pending_approval":
        raise ValueError(f"Cannot approve amendment in status {a.status}")
    now = utc_now()
    eff = _ensure_utc(a.effective_date)
    a.status = "scheduled" if eff and eff > now else "approved"
    a.approved_at = utc_now()
    a.approved_by_user_id = actor_user_id
    if notes:
        a.notes = (a.notes or "") + f"\n[Approval] {notes}"
    _log_commercial(
        db,
        contract_id=a.contract_id,
        review_id=a.source_review_id,
        action_type="amendment_approved",
        summary=f"Amendment {a.amendment_reference} approved",
        performed_by_user_id=actor_user_id,
        amendment_id=a.id,
    )
    db.commit()
    db.refresh(a)
    return a


def reject_amendment(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str,
    notes: str | None = None,
) -> ContractAmendment:
    """Reject amendment. Contract is never mutated."""
    a = db.get(ContractAmendment, amendment_id)
    if not a:
        raise ValueError("Amendment not found")
    if a.status != "pending_approval":
        raise ValueError(f"Cannot reject amendment in status {a.status}")
    a.status = "rejected"
    if notes:
        a.notes = (a.notes or "") + f"\n[Rejection] {notes}"
    _log_commercial(
        db,
        contract_id=a.contract_id,
        review_id=a.source_review_id,
        action_type="amendment_rejected",
        summary=f"Amendment {a.amendment_reference} rejected",
        performed_by_user_id=actor_user_id,
        amendment_id=a.id,
    )
    db.commit()
    db.refresh(a)
    return a


def activate_contract_amendment(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str,
) -> ContractAmendment:
    """
    Apply approved amendment to live contract. Transactional; creates ContractVersion + ContractActivationRun.
    """
    from backend.app.services.contract_version_service import execute_amendment_activation

    a, _run = execute_amendment_activation(
        db,
        amendment_id=amendment_id,
        actor_user_id=actor_user_id,
        run_type="manual",
        idempotency_key=None,
        commit=True,
    )
    return a


def get_amendment(db: Session, *, amendment_id: str) -> ContractAmendment | None:
    return db.get(ContractAmendment, amendment_id)


def list_amendments(
    db: Session,
    *,
    contract_id: str | None = None,
    status: str | None = None,
    amendment_type: str | None = None,
    source_proposal_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ContractAmendment]:
    q = db.query(ContractAmendment)
    if contract_id:
        q = q.filter(ContractAmendment.contract_id == contract_id)
    if status:
        q = q.filter(ContractAmendment.status == status)
    if amendment_type:
        q = q.filter(ContractAmendment.amendment_type == amendment_type)
    if source_proposal_id:
        q = q.filter(ContractAmendment.source_proposal_id == source_proposal_id)
    return q.order_by(ContractAmendment.created_at.desc()).offset(offset).limit(limit).all()


def dashboard_pending_activations(db: Session) -> dict[str, Any]:
    """Amendments approved/scheduled awaiting activation."""
    approved = (
        db.query(ContractAmendment)
        .filter(ContractAmendment.status.in_(("approved", "scheduled")))
        .order_by(ContractAmendment.effective_date.asc())
        .all()
    )
    return {
        "pending_activations": [
            {
                "amendment_id": a.id,
                "amendment_reference": a.amendment_reference,
                "contract_id": a.contract_id,
                "effective_date": a.effective_date.isoformat() if a.effective_date else None,
                "status": a.status,
                "proposed_contract_value": a.proposed_contract_value,
            }
            for a in approved
        ],
        "count": len(approved),
    }


def dashboard_amendments(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Amendments by status for pipeline views."""
    q = db.query(ContractAmendment)
    if status:
        q = q.filter(ContractAmendment.status == status)
    rows = q.order_by(ContractAmendment.created_at.desc()).limit(limit).all()
    return {
        "amendments": [
            {
                "amendment_id": r.id,
                "amendment_reference": r.amendment_reference,
                "contract_id": r.contract_id,
                "amendment_type": r.amendment_type,
                "status": r.status,
                "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                "activated_at": r.activated_at.isoformat() if r.activated_at else None,
                "source_proposal_id": r.source_proposal_id,
            }
            for r in rows
        ],
        "count": len(rows),
    }


def accepted_proposals_awaiting_activation(
    db: Session,
    *,
    contract_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Proposals accepted by customer but no amendment created yet."""
    q = (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.customer_response_status == "accepted",
            ContractRepricingProposal.proposal_status.notin_(("superseded", "withdrawn")),
            ContractRepricingProposal.customer_release_status.in_(("released", "viewed", "responded")),
        )
    )
    if contract_id:
        q = q.filter(ContractRepricingProposal.contract_id == contract_id)
    proposals = q.order_by(ContractRepricingProposal.customer_responded_at.desc()).limit(limit).all()

    # Exclude those that already have a non-rejected/cancelled amendment
    out = []
    for p in proposals:
        existing = (
            db.query(ContractAmendment)
            .filter(
                ContractAmendment.source_proposal_id == p.id,
                ContractAmendment.status.notin_(("rejected", "cancelled")),
            )
            .first()
        )
        if existing:
            continue
        out.append({
            "proposal_id": p.id,
            "proposal_reference": p.proposal_reference,
            "contract_id": p.contract_id,
            "customer_responded_at": p.customer_responded_at.isoformat() if p.customer_responded_at else None,
        })
    return out
