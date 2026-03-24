"""
Customer-facing repricing / renewal proposal workflow: release, portal visibility, responses, audit.

Does not mutate Contract commercial fields.

Expiry policy (explicit):
- Effective expiry timestamp = customer_expiry_at if set, else validity_end_date on the proposal.
- After expiry, POST /portal/me/repricing-proposals/{id}/respond allows only response_type=acknowledged;
  accepted/rejected/counter/needs_follow_up return 400 with a clear message.
- PDF download is blocked when expired (metadata/detail remain visible for transparency).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.auth.models import User
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
from backend.app.modules.contracts.review_models import (
    ContractCommercialActionLog,
    ContractRepricingProposal,
    ProposalCustomerResponse,
)
from backend.app.modules.documents.models import StoredDocument
from backend.app.services import low_risk_automation_service as low_risk_automation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def audit_actor_user_id(db: Session, *, proposal: ContractRepricingProposal | None = None) -> str:
    """Fallback user id for system-side audit rows (FK to users)."""
    if proposal and proposal.released_by_user_id:
        return proposal.released_by_user_id
    u = db.query(User).filter(User.email == "admin@example.com").first()
    if u:
        return u.id
    u2 = db.query(User).first()
    if not u2:
        raise RuntimeError("No user available for commercial audit log")
    return u2.id


def _log_commercial(
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


def effective_customer_expiry_at(p: ContractRepricingProposal) -> datetime | None:
    """Prefer explicit customer_expiry_at; fall back to commercial validity_end_date."""
    return p.customer_expiry_at or p.validity_end_date


def is_past_customer_expiry(p: ContractRepricingProposal, *, now: datetime | None = None) -> bool:
    exp = effective_customer_expiry_at(p)
    if not exp:
        return False
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    n = now or utc_now()
    return n > exp


def refresh_customer_expiry_status(
    db: Session, *, proposal: ContractRepricingProposal, commit: bool = False
) -> ContractRepricingProposal:
    """
    If proposal was released to customer but unanswered and past expiry, set customer_release_status=expired.
    """
    if proposal.customer_release_status in ("not_released", "ready_for_customer", "withdrawn", "responded", "expired"):
        return proposal
    if proposal.customer_response_status:
        return proposal
    if proposal.customer_release_status not in ("released", "viewed"):
        return proposal
    if not is_past_customer_expiry(proposal):
        return proposal
    proposal.customer_release_status = "expired"
    proposal.updated_at = utc_now()
    _log_commercial(
        db,
        contract_id=proposal.contract_id,
        review_id=proposal.review_id,
        action_type="proposal_expired",
        summary=f"Customer proposal {proposal.proposal_reference} expired without response",
        user_id=audit_actor_user_id(db, proposal=proposal),
        payload={"proposal_id": proposal.id},
    )
    if commit:
        db.commit()
        db.refresh(proposal)
    else:
        db.flush()
    return proposal


def release_proposal_to_customer(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    release_notes: str | None = None,
    customer_expiry_at: datetime | None = None,
    commit: bool = True,
) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.proposal_status not in ("approved_internal", "ready_for_customer"):
        raise ValueError("Proposal must be approved_internal or ready_for_customer before customer release")
    if p.proposal_status in ("superseded", "withdrawn"):
        raise ValueError("Invalid internal proposal status for release")
    if not p.stored_document_id:
        raise ValueError("Proposal PDF must be generated before customer release")
    if p.customer_release_status == "responded":
        raise ValueError("Cannot re-release after customer response; create a new proposal")
    if p.customer_release_status == "released":
        return p

    doc = db.get(StoredDocument, p.stored_document_id)
    if not doc or doc.document_type != "repricing_proposal":
        raise ValueError("Stored proposal document missing or invalid")

    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")

    doc.visibility_scope = "customer_repricing_proposal"
    doc.related_contract_id = p.contract_id
    if c.site_id:
        doc.related_site_id = c.site_id
    db.add(doc)

    p.customer_release_status = "released"
    p.released_to_customer_at = utc_now()
    p.released_by_user_id = actor_user_id
    p.portal_visibility_scope = "contract_customer"
    if customer_expiry_at is not None:
        p.customer_expiry_at = customer_expiry_at
    p.updated_at = utc_now()

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_released_to_customer",
        summary=f"Repricing proposal {p.proposal_reference} released to customer portal",
        user_id=actor_user_id,
        payload={
            "proposal_id": p.id,
            "stored_document_id": p.stored_document_id,
            "release_notes": release_notes,
        },
    )
    from backend.app.services import contract_customer_communication_service as cccs

    cccs.create_draft_for_repricing_proposal_release(
        db, proposal_id=p.id, actor_user_id=actor_user_id, commit=False
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
        db.refresh(p)
    return p


def withdraw_customer_proposal(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    reason: str | None = None,
    commit: bool = True,
) -> ContractRepricingProposal:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.customer_release_status in ("not_released", "withdrawn"):
        raise ValueError("Proposal is not in a customer-released state")

    if p.stored_document_id:
        doc = db.get(StoredDocument, p.stored_document_id)
        if doc and doc.document_type == "repricing_proposal":
            doc.visibility_scope = "internal_only"
            db.add(doc)

    p.customer_release_status = "withdrawn"
    p.updated_at = utc_now()
    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_withdrawn",
        summary=f"Customer access withdrawn for proposal {p.proposal_reference}",
        user_id=actor_user_id,
        payload={"proposal_id": p.id, "reason": reason},
    )
    if commit:
        db.commit()
        db.refresh(p)
    else:
        db.flush()
        db.refresh(p)
    return p


def mark_proposal_viewed_by_customer(
    db: Session,
    *,
    proposal: ContractRepricingProposal,
    portal_user_id: str,
    customer_id: str,
    commit: bool = True,
) -> ContractRepricingProposal:
    refresh_customer_expiry_status(db, proposal=proposal, commit=False)
    if proposal.customer_release_status not in ("released", "viewed", "expired", "responded"):
        return proposal

    log_view = False
    if proposal.customer_release_status == "released":
        proposal.customer_viewed_at = utc_now()
        proposal.customer_release_status = "viewed"
        proposal.updated_at = utc_now()
        log_view = True
    elif not proposal.customer_viewed_at and proposal.customer_release_status in ("viewed", "expired"):
        proposal.customer_viewed_at = utc_now()
        proposal.updated_at = utc_now()
        log_view = True

    if log_view:
        _log_commercial(
            db,
            contract_id=proposal.contract_id,
            review_id=proposal.review_id,
            action_type="proposal_viewed_by_customer",
            summary=f"Customer viewed repricing proposal {proposal.proposal_reference}",
            user_id=portal_user_id,
            payload={"proposal_id": proposal.id, "customer_id": customer_id},
        )
    if commit:
        db.commit()
        db.refresh(proposal)
    else:
        db.flush()
    return proposal


def record_customer_response(
    db: Session,
    *,
    proposal_id: str,
    portal_user_id: str,
    customer_id: str,
    response_type: str,
    notes: str | None = None,
    contact_reference: str | None = None,
    metadata_json: dict[str, Any] | None = None,
    commit: bool = True,
) -> tuple[ContractRepricingProposal, ProposalCustomerResponse]:
    allowed = {"accepted", "rejected", "counter_requested", "needs_follow_up", "acknowledged"}
    if response_type not in allowed:
        raise ValueError(f"Invalid response_type; expected one of {sorted(allowed)}")

    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")

    c = db.get(Contract, p.contract_id)
    if not c or c.customer_id != customer_id:
        raise ValueError("Not authorized for this contract")

    refresh_customer_expiry_status(db, proposal=p, commit=False)

    if p.customer_release_status not in ("released", "viewed", "expired"):
        raise ValueError("Proposal is not available for response")

    expired = is_past_customer_expiry(p) or p.customer_release_status == "expired"
    if expired and response_type != "acknowledged":
        raise ValueError(
            "This proposal has expired; only an acknowledgement can be recorded. "
            "Please contact your account manager for next steps."
        )

    row = ProposalCustomerResponse(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        response_type=response_type,
        responded_at=utc_now(),
        responded_by_customer_id=customer_id,
        notes=notes,
        contact_reference=contact_reference,
        metadata_json=_dumps(metadata_json) if metadata_json else None,
    )
    db.add(row)

    p.customer_response_status = response_type
    p.customer_responded_at = row.responded_at
    p.customer_response_notes = notes
    p.customer_response_by_contact = contact_reference
    p.customer_release_status = "responded"
    p.updated_at = utc_now()

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_response_recorded",
        summary=f"Customer {response_type} on proposal {p.proposal_reference}",
        user_id=portal_user_id,
        payload={
            "proposal_id": p.id,
            "response_type": response_type,
            "response_id": row.id,
            "customer_id": customer_id,
        },
    )

    if response_type == "rejected":
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type="follow_up_required",
            summary=f"Commercial follow-up: customer rejected proposal {p.proposal_reference}",
            user_id=portal_user_id,
            payload={"proposal_id": p.id, "reason": "customer_rejected", "customer_id": customer_id},
        )
    elif response_type == "counter_requested":
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type="follow_up_required",
            summary=f"Commercial follow-up: customer counter-request on {p.proposal_reference}",
            user_id=portal_user_id,
            payload={"proposal_id": p.id, "reason": "counter_requested", "customer_id": customer_id},
        )
    elif response_type == "needs_follow_up":
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type="follow_up_required",
            summary=f"Customer requested follow-up on {p.proposal_reference}",
            user_id=portal_user_id,
            payload={"proposal_id": p.id, "reason": "needs_follow_up", "customer_id": customer_id},
        )

    if response_type in ("rejected", "counter_requested"):
        from backend.app.services import contract_customer_communication_service as cccs

        cccs.create_draft_for_customer_response_follow_up(
            db,
            proposal_id=p.id,
            response_type=response_type,
            actor_user_id=portal_user_id,
            commit=False,
        )

    if response_type in ("rejected", "counter_requested", "needs_follow_up", "acknowledged"):
        low_risk_automation.on_customer_proposal_response(
            db,
            proposal=p,
            response_type=response_type,
            actor_user_id=portal_user_id,
            commit=False,
        )

    if commit:
        db.commit()
        db.refresh(p)
        db.refresh(row)
    else:
        db.flush()

    return p, row


def list_released_proposals_for_contract(
    db: Session, *, contract_id: str
) -> list[ContractRepricingProposal]:
    return (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.contract_id == contract_id,
            ContractRepricingProposal.customer_release_status.in_(
                ("released", "viewed", "responded", "expired")
            ),
            ContractRepricingProposal.proposal_status.notin_(("superseded", "withdrawn")),
        )
        .order_by(ContractRepricingProposal.updated_at.desc())
        .all()
    )


def get_proposal_for_portal(
    db: Session, *, proposal_id: str, customer_id: str
) -> ContractRepricingProposal | None:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return None
    c = db.get(Contract, p.contract_id)
    if not c or c.customer_id != customer_id:
        return None
    refresh_customer_expiry_status(db, proposal=p, commit=True)
    if p.customer_release_status not in ("released", "viewed", "responded", "expired"):
        return None
    if p.proposal_status in ("superseded", "withdrawn"):
        return None
    return p


def build_portal_timeline(db: Session, *, proposal: ContractRepricingProposal) -> list[dict[str, Any]]:
    """Customer-safe ordered milestones (no internal margin data)."""
    events: list[tuple[datetime, str, str]] = []
    if proposal.approved_at:
        events.append((proposal.approved_at, "internally_approved", "Proposal approved internally"))
    if proposal.ready_for_customer_at:
        events.append(
            (proposal.ready_for_customer_at, "ready_for_share", "Marked ready for customer release")
        )
    if proposal.released_to_customer_at:
        events.append((proposal.released_to_customer_at, "released", "Released to your portal"))
    if proposal.customer_viewed_at:
        events.append((proposal.customer_viewed_at, "viewed", "Viewed in portal"))
    if proposal.customer_responded_at and proposal.customer_response_status:
        events.append(
            (
                proposal.customer_responded_at,
                "responded",
                f"Your response: {proposal.customer_response_status.replace('_', ' ')}",
            )
        )
    if proposal.customer_release_status == "expired":
        exp = effective_customer_expiry_at(proposal)
        events.append(
            (
                exp or proposal.updated_at,
                "expired",
                "Proposal validity ended",
            )
        )
    if proposal.customer_release_status == "withdrawn":
        events.append((proposal.updated_at, "withdrawn", "Proposal withdrawn from portal"))

    for rec in (
        db.query(ProposalAcceptanceRecord)
        .filter(ProposalAcceptanceRecord.proposal_id == proposal.id)
        .order_by(ProposalAcceptanceRecord.initiated_at.asc())
        .all()
    ):
        events.append(
            (
                rec.initiated_at,
                "formal_acceptance_started",
                "Formal acceptance process started",
            )
        )
        if rec.acceptance_status == "completed" and rec.completed_at:
            events.append(
                (
                    rec.completed_at,
                    "formal_acceptance_completed",
                    "Formal acceptance recorded",
                )
            )

    events.sort(key=lambda x: x[0])
    return [
        {"at": t.isoformat(), "event_type": et, "label": lbl}
        for t, et, lbl in events
    ]


def build_internal_proposal_timeline(db: Session, *, proposal_id: str) -> list[dict[str, Any]]:
    """Commercial timeline: commercial action log + customer responses."""
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return []
    out: list[dict[str, Any]] = []

    logs = (
        db.query(ContractCommercialActionLog)
        .filter(ContractCommercialActionLog.contract_id == p.contract_id)
        .order_by(ContractCommercialActionLog.performed_at.asc())
        .all()
    )
    interesting = {
        "repricing_proposal_generated",
        "repricing_proposal_internal_review",
        "repricing_proposal_approved_internal",
        "repricing_proposal_ready_for_customer",
        "proposal_released_to_customer",
        "proposal_viewed_by_customer",
        "proposal_response_recorded",
        "proposal_withdrawn",
        "proposal_expired",
        "follow_up_required",
        "proposal_acceptance_session_created",
        "proposal_acceptance_viewed",
        "proposal_acceptance_completed",
        "proposal_acceptance_expired",
        "proposal_acceptance_cancelled",
        "proposal_acceptance_linked_to_amendment",
    }
    for lg in logs:
        if lg.action_type not in interesting:
            continue
        try:
            pj = json.loads(lg.payload_json) if lg.payload_json else {}
        except json.JSONDecodeError:
            pj = {}
        if pj.get("proposal_id") != proposal_id:
            continue
        out.append(
            {
                "at": lg.performed_at.isoformat(),
                "source": "commercial_log",
                "action_type": lg.action_type,
                "summary": lg.action_summary,
                "performed_by_user_id": lg.performed_by_user_id,
            }
        )

    for r in (
        db.query(ProposalCustomerResponse)
        .filter(ProposalCustomerResponse.proposal_id == proposal_id)
        .order_by(ProposalCustomerResponse.responded_at.asc())
        .all()
    ):
        out.append(
            {
                "at": r.responded_at.isoformat(),
                "source": "customer_response",
                "action_type": r.response_type,
                "summary": f"Customer response: {r.response_type}",
                "customer_id": r.responded_by_customer_id,
            }
        )

    out.sort(key=lambda x: x["at"])
    return out


def dashboard_customer_proposals(
    db: Session,
    *,
    customer_release_status: str | None = None,
    customer_response_status: str | None = None,
    contract_id: str | None = None,
    expiring_within_days: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    q = db.query(ContractRepricingProposal).filter(
        ContractRepricingProposal.customer_release_status.notin_(["not_released"])
    )
    if contract_id:
        q = q.filter(ContractRepricingProposal.contract_id == contract_id)
    if customer_release_status:
        q = q.filter(ContractRepricingProposal.customer_release_status == customer_release_status)
    if customer_response_status:
        q = q.filter(ContractRepricingProposal.customer_response_status == customer_response_status)

    rows = q.order_by(ContractRepricingProposal.updated_at.desc()).limit(limit).all()
    now = utc_now()
    enriched = []
    for r in rows:
        exp = effective_customer_expiry_at(r)
        days_left = None
        if exp:
            days_left = (exp - now).days
        enriched.append(
            {
                "proposal_id": r.id,
                "proposal_reference": r.proposal_reference,
                "contract_id": r.contract_id,
                "proposal_status": r.proposal_status,
                "customer_release_status": r.customer_release_status,
                "customer_response_status": r.customer_response_status,
                "released_to_customer_at": r.released_to_customer_at.isoformat()
                if r.released_to_customer_at
                else None,
                "customer_viewed_at": r.customer_viewed_at.isoformat() if r.customer_viewed_at else None,
                "customer_responded_at": r.customer_responded_at.isoformat()
                if r.customer_responded_at
                else None,
                "customer_expiry_at": exp.isoformat() if exp else None,
                "days_until_expiry": days_left,
                "stored_document_id": r.stored_document_id,
            }
        )

    if expiring_within_days is not None:
        enriched = [
            e
            for e in enriched
            if e["days_until_expiry"] is not None
            and 0 <= e["days_until_expiry"] <= expiring_within_days
            and e["customer_response_status"] is None
        ]

    by_rel: dict[str, int] = {}
    for e in enriched:
        k = e["customer_release_status"]
        by_rel[k] = by_rel.get(k, 0) + 1

    return {"total": len(enriched), "by_customer_release_status": by_rel, "rows": enriched}


def dashboard_customer_proposal_follow_up(db: Session, *, limit: int = 100) -> dict[str, Any]:
    """Commercial queue: viewed but no response, rejected, counter, needs_follow_up, expired unanswered."""
    rows = (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.customer_release_status.in_(
                ("released", "viewed", "expired", "responded")
            )
        )
        .order_by(ContractRepricingProposal.updated_at.desc())
        .limit(500)
        .all()
    )
    follow: list[dict[str, Any]] = []
    for p in rows:
        has_resp = bool(p.customer_response_status)
        vis = p.customer_release_status
        past_exp = is_past_customer_expiry(p)
        if has_resp and p.customer_response_status in ("rejected", "counter_requested", "needs_follow_up"):
            follow.append(
                {
                    "proposal_id": p.id,
                    "contract_id": p.contract_id,
                    "reason": p.customer_response_status,
                    "priority": "high",
                    "proposal_reference": p.proposal_reference,
                }
            )
        elif not has_resp and past_exp and vis in ("released", "viewed", "expired"):
            follow.append(
                {
                    "proposal_id": p.id,
                    "contract_id": p.contract_id,
                    "reason": "expired_no_response",
                    "priority": "high",
                    "proposal_reference": p.proposal_reference,
                }
            )
        elif vis == "viewed" and not has_resp:
            follow.append(
                {
                    "proposal_id": p.id,
                    "contract_id": p.contract_id,
                    "reason": "viewed_no_response",
                    "priority": "normal",
                    "proposal_reference": p.proposal_reference,
                }
            )

    return {"count": len(follow[:limit]), "rows": follow[:limit]}


def resolve_proposal_stored_document_for_portal(
    db: Session, *, proposal: ContractRepricingProposal
) -> StoredDocument | None:
    if not proposal.stored_document_id:
        return None
    doc = db.get(StoredDocument, proposal.stored_document_id)
    if not doc or doc.document_type != "repricing_proposal":
        return None
    return doc
