"""
Formal proposal acceptance sessions, immutable completion evidence, and commercial audit hooks.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord, ProposalAcceptanceSession
from backend.app.modules.contracts.review_models import ContractCommercialActionLog, ContractRepricingProposal
from backend.app.services import customer_repricing_proposal_service as crps
from backend.app.services.customer_repricing_proposal_service import audit_actor_user_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def hash_acceptance_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def stable_acceptance_hash(evidence: dict[str, Any]) -> str:
    canonical = _dumps(evidence)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _cancel_active_sessions_for_proposal(
    db: Session,
    *,
    proposal_id: str,
    except_session_id: str | None,
    actor_user_id: str,
    reason: str,
    skip_esign_provider_sessions: bool = False,
) -> None:
    prop = db.get(ContractRepricingProposal, proposal_id)
    if not prop:
        return
    q = db.query(ProposalAcceptanceSession).filter(
        ProposalAcceptanceSession.proposal_id == proposal_id,
        ProposalAcceptanceSession.session_status == "active",
    )
    if skip_esign_provider_sessions:
        q = q.filter(ProposalAcceptanceSession.esign_provider_flow.is_(False))
    if except_session_id:
        q = q.filter(ProposalAcceptanceSession.id != except_session_id)
    for s in q.all():
        s.session_status = "cancelled"
        s.completed_at = utc_now()
        rec = s.acceptance_record_id and db.get(ProposalAcceptanceRecord, s.acceptance_record_id)
        if rec and rec.acceptance_status in ("initiated", "viewed"):
            rec.acceptance_status = "cancelled"
        _log_commercial(
            db,
            contract_id=prop.contract_id,
            review_id=prop.review_id,
            action_type="proposal_acceptance_cancelled",
            summary=f"Proposal acceptance session superseded: {reason}",
            user_id=actor_user_id,
            payload={"proposal_id": proposal_id, "session_id": s.id, "reason": reason},
        )


def _proposal_contract_customer(db: Session, p: ContractRepricingProposal) -> tuple[Contract, str]:
    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")
    return c, c.customer_id


def assert_proposal_eligible_for_acceptance_session(db: Session, *, proposal: ContractRepricingProposal) -> None:
    crps.refresh_customer_expiry_status(db, proposal=proposal, commit=False)
    if proposal.proposal_status in ("superseded", "withdrawn"):
        raise ValueError("Proposal is superseded or withdrawn")
    if proposal.customer_release_status in ("not_released", "ready_for_customer", "withdrawn"):
        raise ValueError("Proposal must be released to the customer before formal acceptance")
    if proposal.customer_release_status == "expired":
        raise ValueError("Proposal has expired; formal acceptance cannot be started")
    if crps.is_past_customer_expiry(proposal):
        raise ValueError("Proposal is past customer validity; formal acceptance cannot be started")
    if proposal.customer_release_status not in ("released", "viewed", "responded"):
        raise ValueError("Invalid customer release state for acceptance")

    crs = proposal.customer_response_status
    if crs in ("rejected", "counter_requested", "needs_follow_up"):
        raise ValueError("Customer response on this proposal prevents formal acceptance")


def _has_completed_formal_acceptance(db: Session, *, proposal_id: str) -> bool:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_status == "completed",
        )
        .first()
        is not None
    )


def create_proposal_acceptance_session(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    acceptance_type: str,
    expires_at: datetime | None = None,
    issue_secure_token: bool = False,
    metadata: dict[str, Any] | None = None,
) -> tuple[ProposalAcceptanceRecord, ProposalAcceptanceSession, str | None]:
    """
    Internal/commercial initiation. Optionally returns a one-time plain token (only when issue_secure_token=True).
    """
    allowed_types = {"portal_acceptance", "token_link_acceptance", "acknowledgement_only"}
    if acceptance_type not in allowed_types:
        raise ValueError(f"acceptance_type must be one of {sorted(allowed_types)}")
    if acceptance_type == "token_link_acceptance" and not issue_secure_token:
        raise ValueError("token_link_acceptance requires a secure token")

    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    assert_proposal_eligible_for_acceptance_session(db, proposal=p)
    if _has_completed_formal_acceptance(db, proposal_id=proposal_id):
        raise ValueError("A completed formal acceptance already exists for this proposal")

    contract, customer_id = _proposal_contract_customer(db, p)

    channel = "secure_link" if issue_secure_token else "internal_assisted"
    now = utc_now()
    exp = expires_at
    if issue_secure_token and exp is None:
        exp = now + timedelta(days=7)

    _cancel_active_sessions_for_proposal(
        db,
        proposal_id=proposal_id,
        except_session_id=None,
        actor_user_id=actor_user_id,
        reason="replaced_by_new_session",
    )

    record = ProposalAcceptanceRecord(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        contract_id=contract.id,
        customer_id=customer_id,
        source_proposal_reference=p.proposal_reference,
        acceptance_status="initiated",
        acceptance_type=acceptance_type,
        initiated_at=now,
        acceptance_channel=channel,
        created_by_user_id=actor_user_id,
    )
    db.add(record)
    db.flush()

    plain_token: str | None = None
    token_hash: str | None = None
    if issue_secure_token:
        plain_token = secrets.token_urlsafe(32)
        token_hash = hash_acceptance_token(plain_token)

    session = ProposalAcceptanceSession(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        acceptance_record_id=record.id,
        session_status="active",
        token_hash=token_hash,
        expires_at=exp,
        created_by_user_id=actor_user_id,
        metadata_json=_dumps(metadata) if metadata else None,
    )
    db.add(session)
    db.flush()

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_acceptance_session_created",
        summary=f"Formal acceptance session created for proposal {p.proposal_reference}",
        user_id=actor_user_id,
        payload={
            "proposal_id": p.id,
            "acceptance_record_id": record.id,
            "session_id": session.id,
            "acceptance_type": acceptance_type,
            "channel": channel,
            "has_secure_token": bool(token_hash),
        },
    )
    return record, session, plain_token


def portal_initiate_acceptance(
    db: Session,
    *,
    proposal_id: str,
    portal_user_id: str,
    customer_id: str,
    acceptance_type: str = "portal_acceptance",
) -> tuple[ProposalAcceptanceRecord, ProposalAcceptanceSession]:
    if acceptance_type not in ("portal_acceptance", "acknowledgement_only"):
        raise ValueError("Invalid acceptance_type for portal initiation")

    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    c = db.get(Contract, p.contract_id)
    if not c or c.customer_id != customer_id:
        raise ValueError("Not authorized for this proposal")

    assert_proposal_eligible_for_acceptance_session(db, proposal=p)
    if _has_completed_formal_acceptance(db, proposal_id=proposal_id):
        raise ValueError("Formal acceptance is already completed for this proposal")

    ex_rec, ex_sess = get_active_session_for_portal_proposal(db, proposal_id=proposal_id, customer_id=customer_id)
    if ex_rec and ex_sess and ex_rec.acceptance_type == acceptance_type:
        return ex_rec, ex_sess

    _cancel_active_sessions_for_proposal(
        db,
        proposal_id=proposal_id,
        except_session_id=None,
        actor_user_id=portal_user_id,
        reason="portal_initiated_new_session",
        skip_esign_provider_sessions=True,
    )

    now = utc_now()
    record = ProposalAcceptanceRecord(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        contract_id=c.id,
        customer_id=customer_id,
        source_proposal_reference=p.proposal_reference,
        acceptance_status="initiated",
        acceptance_type=acceptance_type,
        initiated_at=now,
        acceptance_channel="portal",
        created_by_user_id=portal_user_id,
    )
    db.add(record)
    db.flush()

    session = ProposalAcceptanceSession(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        acceptance_record_id=record.id,
        session_status="active",
        token_hash=None,
        expires_at=None,
        created_by_user_id=portal_user_id,
    )
    db.add(session)
    db.flush()

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_acceptance_session_created",
        summary=f"Customer portal started formal acceptance for {p.proposal_reference}",
        user_id=portal_user_id,
        payload={
            "proposal_id": p.id,
            "acceptance_record_id": record.id,
            "session_id": session.id,
            "acceptance_type": acceptance_type,
            "channel": "portal",
            "customer_id": customer_id,
        },
    )
    return record, session


def _touch_session_access(db: Session, session: ProposalAcceptanceSession) -> None:
    session.last_accessed_at = utc_now()


def mark_acceptance_viewed_if_needed(
    db: Session,
    *,
    record: ProposalAcceptanceRecord,
    session: ProposalAcceptanceSession | None,
    actor_user_id: str,
) -> None:
    if record.acceptance_status != "initiated":
        return
    prop = db.get(ContractRepricingProposal, record.proposal_id)
    record.acceptance_status = "viewed"
    if session:
        _touch_session_access(db, session)
    _log_commercial(
        db,
        contract_id=record.contract_id,
        review_id=prop.review_id if prop else None,
        action_type="proposal_acceptance_viewed",
        summary="Formal acceptance flow viewed",
        user_id=actor_user_id,
        payload={"proposal_id": record.proposal_id, "acceptance_record_id": record.id},
    )


def _expire_session_if_needed(db: Session, session: ProposalAcceptanceSession, *, actor_user_id: str) -> bool:
    if session.session_status != "active":
        return False
    if session.expires_at and utc_now() > _ensure_utc(session.expires_at):
        session.session_status = "expired"
        session.completed_at = utc_now()
        rec = session.acceptance_record_id and db.get(ProposalAcceptanceRecord, session.acceptance_record_id)
        if rec and rec.acceptance_status in ("initiated", "viewed"):
            rec.acceptance_status = "expired"
        prop = db.get(ContractRepricingProposal, session.proposal_id)
        _log_commercial(
            db,
            contract_id=prop.contract_id if prop else "",
            review_id=prop.review_id if prop else None,
            action_type="proposal_acceptance_expired",
            summary="Formal acceptance session expired",
            user_id=actor_user_id,
            payload={"proposal_id": session.proposal_id, "session_id": session.id},
        )
        return True
    return False


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_active_session_for_portal_proposal(
    db: Session, *, proposal_id: str, customer_id: str
) -> tuple[ProposalAcceptanceRecord | None, ProposalAcceptanceSession | None]:
    """Latest active portal session for customer (no token)."""
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return None, None
    c = db.get(Contract, p.contract_id)
    if not c or c.customer_id != customer_id:
        return None, None
    sess = (
        db.query(ProposalAcceptanceSession)
        .filter(
            ProposalAcceptanceSession.proposal_id == proposal_id,
            ProposalAcceptanceSession.session_status == "active",
            ProposalAcceptanceSession.token_hash.is_(None),
            ProposalAcceptanceSession.esign_provider_flow.is_(False),
        )
        .order_by(ProposalAcceptanceSession.created_at.desc())
        .first()
    )
    if not sess or not sess.acceptance_record_id:
        return None, None
    rec = db.get(ProposalAcceptanceRecord, sess.acceptance_record_id)
    if not rec:
        return None, None
    _expire_session_if_needed(db, sess, actor_user_id=audit_actor_user_id(db, proposal=p))
    db.flush()
    if sess.session_status != "active":
        return None, None
    return rec, sess


def resolve_session_by_raw_token(db: Session, *, raw_token: str) -> ProposalAcceptanceSession | None:
    th = hash_acceptance_token(raw_token)
    return db.query(ProposalAcceptanceSession).filter(ProposalAcceptanceSession.token_hash == th).first()


def cancel_acceptance_session(
    db: Session,
    *,
    session_id: str,
    actor_user_id: str,
) -> ProposalAcceptanceSession:
    s = db.get(ProposalAcceptanceSession, session_id)
    if not s:
        raise ValueError("Session not found")
    if s.session_status != "active":
        raise ValueError("Session is not active")
    s.session_status = "cancelled"
    s.completed_at = utc_now()
    if s.acceptance_record_id:
        rec = db.get(ProposalAcceptanceRecord, s.acceptance_record_id)
        if rec and rec.acceptance_status in ("initiated", "viewed"):
            rec.acceptance_status = "cancelled"
    prop = db.get(ContractRepricingProposal, s.proposal_id)
    _log_commercial(
        db,
        contract_id=prop.contract_id if prop else "",
        review_id=prop.review_id if prop else None,
        action_type="proposal_acceptance_cancelled",
        summary="Formal acceptance session cancelled",
        user_id=actor_user_id,
        payload={"proposal_id": s.proposal_id, "session_id": s.id},
    )
    return s


def _build_commercial_snapshot(p: ContractRepricingProposal) -> dict[str, Any]:
    return {
        "proposal_id": p.id,
        "proposal_reference": p.proposal_reference,
        "currency": p.currency,
        "current_contract_value": p.current_contract_value,
        "proposed_contract_value": p.proposed_contract_value,
        "effective_date": p.effective_date.isoformat() if p.effective_date else None,
        "validity_end_date": p.validity_end_date.isoformat() if p.validity_end_date else None,
        "customer_expiry_at": p.customer_expiry_at.isoformat() if p.customer_expiry_at else None,
        "change_summary": _loads(p.change_summary_json) or {},
        "pricing_basis_keys": list((_loads(p.pricing_basis_json) or {}).keys()),
    }


def complete_acceptance(
    db: Session,
    *,
    record: ProposalAcceptanceRecord,
    session: ProposalAcceptanceSession | None,
    actor_user_id: str | None,
    acceptance_ip: str | None,
    acceptance_user_agent: str | None,
    signed_name: str | None,
    signed_title: str | None,
    signed_email: str | None,
    accepted_by_contact: str | None,
    acceptance_notes: str | None,
    confirm_binding_acknowledgement: bool,
    raw_token: str | None = None,
) -> ProposalAcceptanceRecord:
    if record.acceptance_status == "completed":
        raise ValueError("Acceptance is already finalized and cannot be changed")

    if record.acceptance_type == "provider_esign":
        raise ValueError(
            "This acceptance uses a legal e-sign provider; complete it via the provider workflow, not in-product confirmation"
        )

    p = db.get(ContractRepricingProposal, record.proposal_id)
    if not p:
        raise ValueError("Proposal not found")

    effective_actor = actor_user_id or audit_actor_user_id(db, proposal=p)

    if session:
        if session.acceptance_record_id != record.id:
            raise ValueError("Session does not match acceptance record")
        _expire_session_if_needed(db, session, actor_user_id=effective_actor)
        if session.session_status != "active":
            raise ValueError("Acceptance session is not active")
        if session.expires_at and utc_now() > _ensure_utc(session.expires_at):
            raise ValueError("Acceptance session has expired")
        if session.token_hash and raw_token:
            if not hmac.compare_digest(session.token_hash, hash_acceptance_token(raw_token)):
                raise ValueError("Invalid acceptance token")
        elif session.token_hash and not raw_token:
            raise ValueError("Acceptance token required")
        _touch_session_access(db, session)

    crps.refresh_customer_expiry_status(db, proposal=p, commit=False)
    expired = crps.is_past_customer_expiry(p) or p.customer_release_status == "expired"
    if record.acceptance_type in ("portal_acceptance", "token_link_acceptance") and expired:
        raise ValueError("This proposal has expired; formal acceptance cannot be completed")

    if record.acceptance_type in ("portal_acceptance", "token_link_acceptance"):
        if not confirm_binding_acknowledgement:
            raise ValueError("Explicit confirmation is required to complete formal acceptance")
        if not (signed_name or "").strip():
            raise ValueError("signed_name is required for this acceptance type")
        response_type = "accepted"
    else:
        # acknowledgement_only
        response_type = "acknowledged"
        if not confirm_binding_acknowledgement:
            raise ValueError("Explicit acknowledgement is required")

    if p.customer_response_status in ("rejected", "counter_requested", "needs_follow_up"):
        raise ValueError("Existing customer response blocks formal acceptance")

    if actor_user_id is None and record.acceptance_channel == "secure_link":
        if not (signed_email or "").strip():
            raise ValueError("signed_email is required to complete secure-link acceptance")

    mark_acceptance_viewed_if_needed(db, record=record, session=session, actor_user_id=effective_actor)

    now = utc_now()
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "disclosure": (
            "This record captures system-observed customer confirmation; it is not a third-party e-signature certificate."
        ),
        "proposal_commercial_snapshot_at_completion": _build_commercial_snapshot(p),
        "acceptance_type": record.acceptance_type,
        "acceptance_channel": record.acceptance_channel,
        "completed_at": now.isoformat(),
        "accepted_by_contact": accepted_by_contact,
        "signed_name": signed_name,
        "signed_title": signed_title,
        "signed_email": signed_email,
        "acceptance_notes": acceptance_notes,
        "acceptance_ip": acceptance_ip,
        "acceptance_user_agent": acceptance_user_agent,
        "portal_user_id": actor_user_id,
        "completed_without_authenticated_portal_user": actor_user_id is None,
        "customer_id": record.customer_id,
        "confirm_binding_acknowledgement": confirm_binding_acknowledgement,
        "intended_customer_response": response_type,
    }
    ev_type = "acknowledgement_only" if record.acceptance_type == "acknowledgement_only" else "in_product_acceptance"
    evidence["acceptance_evidence_type"] = ev_type

    imm_hash = stable_acceptance_hash(evidence)
    record.acceptance_evidence_type = ev_type
    record.acceptance_status = "completed"
    record.completed_at = now
    record.accepted_by_contact = accepted_by_contact
    record.accepted_by_customer_user_id = actor_user_id
    record.acceptance_ip = acceptance_ip
    record.acceptance_user_agent = acceptance_user_agent
    record.acceptance_notes = acceptance_notes
    record.signed_name = signed_name
    record.signed_title = signed_title
    record.signed_email = signed_email
    record.evidence_json = _dumps(evidence)
    record.immutable_hash = imm_hash

    p.formal_acceptance_record_id = record.id
    p.updated_at = now

    if session:
        session.session_status = "completed"
        session.completed_at = now

    if p.customer_release_status != "responded":
        crps.record_customer_response(
            db,
            proposal_id=p.id,
            portal_user_id=effective_actor,
            customer_id=record.customer_id,
            response_type=response_type,
            notes=acceptance_notes,
            contact_reference=accepted_by_contact or signed_email,
            metadata_json={
                "formal_acceptance_record_id": record.id,
                "formal_acceptance": True,
                "immutable_hash": imm_hash,
                "acting_portal_user_id": effective_actor,
                "authenticated_portal_user_id": actor_user_id,
            },
            commit=False,
        )
    elif p.customer_response_status == "accepted" and response_type == "accepted":
        pass
    elif p.customer_response_status == "accepted" and response_type != "accepted":
        raise ValueError("Proposal already accepted; conflicting formal acceptance type")
    else:
        raise ValueError("Proposal already has a customer response; formal acceptance cannot align")

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_acceptance_completed",
        summary=f"Formal acceptance completed for {p.proposal_reference} ({record.acceptance_type})",
        user_id=effective_actor,
        payload={
            "proposal_id": p.id,
            "acceptance_record_id": record.id,
            "session_id": session.id if session else None,
            "immutable_hash": imm_hash,
            "acceptance_type": record.acceptance_type,
        },
    )

    db.flush()
    return record


def assert_acceptance_record_not_mutated_after_completion(record: ProposalAcceptanceRecord) -> None:
    if record.acceptance_status != "completed":
        return
    if not record.evidence_json or not record.immutable_hash:
        raise AssertionError("Completed record missing evidence")
    evidence = _loads(record.evidence_json)
    if not isinstance(evidence, dict):
        raise AssertionError("Invalid evidence")
    if stable_acceptance_hash(evidence) != record.immutable_hash:
        raise AssertionError("Acceptance evidence hash mismatch — record must remain immutable")


def link_acceptance_to_amendment(
    db: Session,
    *,
    proposal_id: str,
    amendment_id: str,
    actor_user_id: str,
) -> None:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return
    rid = p.formal_acceptance_record_id
    if not rid:
        rec = (
            db.query(ProposalAcceptanceRecord)
            .filter(
                ProposalAcceptanceRecord.proposal_id == proposal_id,
                ProposalAcceptanceRecord.acceptance_status == "completed",
            )
            .order_by(ProposalAcceptanceRecord.completed_at.desc())
            .first()
        )
        if rec:
            rid = rec.id
    if not rid:
        return
    record = db.get(ProposalAcceptanceRecord, rid)
    if not record or record.amendment_id:
        if record and record.amendment_id == amendment_id:
            return
        if not record:
            return
        return
    record.amendment_id = amendment_id
    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_acceptance_linked_to_amendment",
        summary=f"Formal acceptance {record.id[:8]}… linked to amendment",
        user_id=actor_user_id,
        payload={"proposal_id": proposal_id, "acceptance_record_id": record.id, "amendment_id": amendment_id},
    )


def list_acceptance_records_for_proposal(db: Session, *, proposal_id: str) -> list[ProposalAcceptanceRecord]:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(ProposalAcceptanceRecord.proposal_id == proposal_id)
        .order_by(ProposalAcceptanceRecord.created_at.desc())
        .all()
    )


def get_acceptance_record(db: Session, *, acceptance_record_id: str) -> ProposalAcceptanceRecord | None:
    return db.get(ProposalAcceptanceRecord, acceptance_record_id)


def get_acceptance_session(db: Session, *, session_id: str) -> ProposalAcceptanceSession | None:
    return db.get(ProposalAcceptanceSession, session_id)


def record_out_dict(r: ProposalAcceptanceRecord) -> dict[str, Any]:
    return {
        "id": r.id,
        "proposal_id": r.proposal_id,
        "contract_id": r.contract_id,
        "customer_id": r.customer_id,
        "source_proposal_reference": r.source_proposal_reference,
        "acceptance_status": r.acceptance_status,
        "acceptance_type": r.acceptance_type,
        "acceptance_channel": r.acceptance_channel,
        "initiated_at": r.initiated_at.isoformat() if r.initiated_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "accepted_by_contact": r.accepted_by_contact,
        "accepted_by_customer_user_id": r.accepted_by_customer_user_id,
        "acceptance_ip": r.acceptance_ip,
        "acceptance_user_agent": r.acceptance_user_agent,
        "acceptance_notes": r.acceptance_notes,
        "signed_name": r.signed_name,
        "signed_title": r.signed_title,
        "signed_email": r.signed_email,
        "immutable_hash": r.immutable_hash,
        "evidence_json": _loads(r.evidence_json),
        "amendment_id": r.amendment_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "created_by_user_id": r.created_by_user_id,
        "acceptance_evidence_type": getattr(r, "acceptance_evidence_type", None) or "in_product_acceptance",
        "provider_name": getattr(r, "provider_name", None),
        "provider_envelope_id": getattr(r, "provider_envelope_id", None),
        "provider_session_id": getattr(r, "provider_session_id", None),
        "provider_status": getattr(r, "provider_status", None),
        "provider_completed_at": r.provider_completed_at.isoformat() if getattr(r, "provider_completed_at", None) else None,
    }


def session_out_dict(s: ProposalAcceptanceSession, *, include_token_hint: bool = False) -> dict[str, Any]:
    d: dict[str, Any] = {
        "id": s.id,
        "proposal_id": s.proposal_id,
        "acceptance_record_id": s.acceptance_record_id,
        "session_status": s.session_status,
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "created_by_user_id": s.created_by_user_id,
        "last_accessed_at": s.last_accessed_at.isoformat() if s.last_accessed_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "metadata_json": _loads(s.metadata_json),
        "has_secure_token": bool(s.token_hash),
        "esign_provider_flow": getattr(s, "esign_provider_flow", False),
    }
    if include_token_hint:
        d["token_hint"] = "use plain token returned on create only"
    return d


def dashboard_accepted_proposals(db: Session, *, limit: int = 100) -> dict[str, Any]:
    rows = (
        db.query(ProposalAcceptanceRecord)
        .filter(ProposalAcceptanceRecord.acceptance_status == "completed")
        .order_by(ProposalAcceptanceRecord.completed_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        p = db.get(ContractRepricingProposal, r.proposal_id)
        out.append(
            {
                **record_out_dict(r),
                "proposal_reference": p.proposal_reference if p else None,
                "customer_response_status": p.customer_response_status if p else None,
                "has_amendment": bool(r.amendment_id),
            }
        )
    return {"count": len(out), "rows": out}


def dashboard_acceptance_awaiting_activation(db: Session, *, limit: int = 100) -> dict[str, Any]:
    """Completed formal acceptance, customer accepted, no amendment yet."""
    from backend.app.modules.contracts.amendment_models import ContractAmendment

    q = (
        db.query(ProposalAcceptanceRecord)
        .join(ContractRepricingProposal, ContractRepricingProposal.id == ProposalAcceptanceRecord.proposal_id)
        .filter(
            ProposalAcceptanceRecord.acceptance_status == "completed",
            ContractRepricingProposal.customer_response_status == "accepted",
            ContractRepricingProposal.proposal_status.notin_(("superseded", "withdrawn")),
        )
        .order_by(ProposalAcceptanceRecord.completed_at.desc())
        .limit(limit * 2)
    )
    rows = []
    for r in q.all():
        if r.amendment_id:
            continue
        existing = (
            db.query(ContractAmendment)
            .filter(
                ContractAmendment.source_proposal_id == r.proposal_id,
                ContractAmendment.status.notin_(("rejected", "cancelled")),
            )
            .first()
        )
        if existing:
            continue
        p = db.get(ContractRepricingProposal, r.proposal_id)
        rows.append(
            {
                "acceptance_record_id": r.id,
                "proposal_id": r.proposal_id,
                "proposal_reference": p.proposal_reference if p else None,
                "contract_id": r.contract_id,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "immutable_hash": r.immutable_hash,
            }
        )
        if len(rows) >= limit:
            break
    return {"count": len(rows), "rows": rows}


def describe_secure_link_for_public(
    db: Session, *, raw_token: str, mark_viewed: bool = False
) -> dict[str, Any]:
    """
    Resolve a secure acceptance token for unauthenticated portal routes.
    Raises ValueError('not_found') if token is unknown.
    """
    sess = resolve_session_by_raw_token(db, raw_token=raw_token)
    if not sess:
        raise ValueError("not_found")
    prop = db.get(ContractRepricingProposal, sess.proposal_id)
    if not prop:
        raise ValueError("not_found")
    actor = audit_actor_user_id(db, proposal=prop)
    _expire_session_if_needed(db, sess, actor_user_id=actor)
    db.flush()
    rec = sess.acceptance_record_id and db.get(ProposalAcceptanceRecord, sess.acceptance_record_id)
    if sess.session_status == "active" and mark_viewed and rec:
        mark_acceptance_viewed_if_needed(db, record=rec, session=sess, actor_user_id=actor)
        db.flush()
    return {
        "session_status": sess.session_status,
        "proposal_reference": prop.proposal_reference,
        "acceptance_type": rec.acceptance_type if rec else None,
        "expires_at": sess.expires_at,
        "session": sess,
        "record": rec,
        "proposal": prop,
    }


def portal_acceptance_state(
    db: Session, *, proposal_id: str, customer_id: str
) -> dict[str, Any]:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return {"proposal_id": proposal_id, "visible": False}
    c = db.get(Contract, p.contract_id)
    if not c or c.customer_id != customer_id:
        return {"proposal_id": proposal_id, "visible": False}

    completed = (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_status == "completed",
        )
        .order_by(ProposalAcceptanceRecord.completed_at.desc())
        .first()
    )
    rec, sess = get_active_session_for_portal_proposal(db, proposal_id=proposal_id, customer_id=customer_id)

    esign_rec = (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_type == "provider_esign",
        )
        .order_by(ProposalAcceptanceRecord.initiated_at.desc())
        .first()
    )
    esign_public = None
    esign_customer_phase = "none"
    if esign_rec:
        from backend.app.services.proposal_acceptance_esign_service import provider_status_public_dict

        esign_public = provider_status_public_dict(esign_rec)
        if esign_rec.acceptance_status == "completed" and esign_rec.provider_status == "signed":
            esign_customer_phase = "completed"
        elif esign_rec.provider_status in ("declined", "voided", "expired", "failed"):
            esign_customer_phase = "declined_or_expired"
        elif esign_rec.acceptance_status == "cancelled":
            esign_customer_phase = "cancelled"
        else:
            esign_customer_phase = "external_signature_in_progress"

    return {
        "proposal_id": proposal_id,
        "visible": True,
        "formal_acceptance_record_id": p.formal_acceptance_record_id,
        "completed_summary": (
            {
                "acceptance_record_id": completed.id,
                "completed_at": completed.completed_at.isoformat() if completed and completed.completed_at else None,
                "acceptance_type": completed.acceptance_type,
                "acceptance_evidence_type": getattr(completed, "acceptance_evidence_type", None),
                "immutable_hash": completed.immutable_hash,
            }
            if completed
            else None
        ),
        "active_session": session_out_dict(sess) if sess else None,
        "active_record_status": rec.acceptance_status if rec else None,
        "provider_esign": esign_public,
        "provider_esign_customer_phase": esign_customer_phase,
    }
