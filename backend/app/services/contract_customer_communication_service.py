"""
Contract-scoped customer communication workflow: generation, approval-safe send, audit.

Outbound email uses provider abstraction; delivery attempts are first-class rows.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
from backend.app.modules.contracts.review_models import ContractCommercialActionLog, ContractRepricingProposal
from backend.app.modules.crm.customer_communication_preference_models import CustomerCommunicationPreference
from backend.app.modules.crm.models import Customer
from backend.app.services import contract_customer_communication_templates as tpl
from backend.app.services.communication_channel_routing_service import effective_channel_for_communication_type
from backend.app.services.communication_template_registry import resolve_communication_locale_for_contract
from backend.app.services.communication_recipient_suppression_service import is_outbound_blocked
from backend.app.services.customer_communication_recipient_service import resolve_customer_communication_recipients
from backend.app.services.outbound_communication_provider import (
    OutboundEmailMessage,
    dumps_response_payload,
    get_email_provider,
)
from backend.app.services.outbound_sms_provider import (
    OutboundSmsMessage,
    dumps_sms_response_payload,
    get_sms_provider,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _e164_for_sms(to_compact: str | None) -> str:
    """Best-effort E.164 for Twilio-style providers when customer data omits leading +."""
    if not to_compact:
        return ""
    t = to_compact.strip()
    if t.startswith("+"):
        return t
    if t.isdigit() and len(t) >= 10:
        return f"+{t}"
    return t


def _as_utc_aware(dt: datetime | None) -> datetime | None:
    """SQLite can surface naive datetimes; normalize for comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


OPEN_STATUSES = ("draft", "ready_to_send")


def _audit_actor_fallback(db: Session) -> str:
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
    user_id: str | None,
    payload: dict[str, Any] | None = None,
) -> None:
    uid = user_id or _audit_actor_fallback(db)
    p = dict(payload or {})
    db.add(
        ContractCommercialActionLog(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            review_id=review_id,
            action_type=action_type,
            action_summary=summary,
            performed_by_user_id=uid,
            performed_at=utc_now(),
            payload_json=_dumps(p) if p else None,
        )
    )


def log_communication_provider_audit(
    db: Session,
    *,
    contract_id: str,
    action_type: str,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Commercial audit for provider webhooks (no interactive user — uses system fallback actor)."""
    _log_commercial(
        db,
        contract_id=contract_id,
        review_id=None,
        action_type=action_type,
        summary=summary,
        user_id=None,
        payload=payload,
    )


def find_open_duplicate(
    db: Session,
    *,
    contract_id: str,
    communication_type: str,
    source_entity_type: str,
    source_entity_id: str,
) -> ContractCustomerCommunication | None:
    return (
        db.query(ContractCustomerCommunication)
        .filter(
            ContractCustomerCommunication.contract_id == contract_id,
            ContractCustomerCommunication.communication_type == communication_type,
            ContractCustomerCommunication.source_entity_type == source_entity_type,
            ContractCustomerCommunication.source_entity_id == source_entity_id,
            ContractCustomerCommunication.status.in_(OPEN_STATUSES),
        )
        .order_by(ContractCustomerCommunication.created_at.desc())
        .first()
    )


def _persist_communication(
    db: Session,
    *,
    row: ContractCustomerCommunication,
    contract_id: str,
    review_id: str | None,
    actor_user_id: str | None,
    event: str,
    summary: str,
    commit: bool,
) -> ContractCustomerCommunication:
    db.add(row)
    _log_commercial(
        db,
        contract_id=contract_id,
        review_id=review_id,
        action_type=event,
        summary=summary,
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id, "communication_type": row.communication_type},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def create_draft_for_repricing_proposal_release(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.customer_release_status != "released":
        raise ValueError("Proposal must be released to customer before creating release communication")
    dup = find_open_duplicate(
        db,
        contract_id=p.contract_id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_RELEASED,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
    )
    if dup:
        return dup

    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    cust_name = cust.name if cust else "Customer"
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_repricing_proposal_released(
        proposal_reference=p.proposal_reference,
        contract_name=c.name,
        contract_code=c.contract_code,
        customer_name=cust_name,
        currency=p.currency,
        current_value=p.current_contract_value,
        proposed_value=p.proposed_contract_value,
        validity_end=p.validity_end_date,
        customer_expiry=p.customer_expiry_at or p.validity_end_date,
        proposal_id=p.id,
        stored_document_id=p.stored_document_id,
        locale=loc,
    )
    meta = {
        "customer_safe_summary": r.customer_safe_summary,
        "link_hints": r.link_hints,
        "template_version": tpl.template_key_for_type(tpl.COMMS_REPRICING_PROPOSAL_RELEASED, locale=loc),
    }
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=p.contract_id,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_RELEASED,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_REPRICING_PROPOSAL_RELEASED),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_REPRICING_PROPOSAL_RELEASED, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_REPRICING_PROPOSAL_RELEASED),
        metadata_json=_dumps(meta),
        stored_document_id=p.stored_document_id,
        source_proposal_id=p.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=p.contract_id,
        review_id=p.review_id,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft communication {row.communication_type} for proposal {p.proposal_reference}",
        commit=commit,
    )


def create_draft_for_repricing_proposal_reminder(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.customer_release_status not in ("released", "viewed"):
        raise ValueError("Proposal must be released or viewed for a reminder communication")
    dup = find_open_duplicate(
        db,
        contract_id=p.contract_id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_REMINDER,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
    )
    if dup:
        return dup
    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_repricing_proposal_reminder(
        proposal_reference=p.proposal_reference,
        contract_code=c.contract_code,
        customer_name=cust.name if cust else "Customer",
        customer_expiry=p.customer_expiry_at or p.validity_end_date,
        proposal_id=p.id,
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=p.contract_id,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_REMINDER,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_REPRICING_PROPOSAL_REMINDER),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_REPRICING_PROPOSAL_REMINDER, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_REPRICING_PROPOSAL_REMINDER),
        metadata_json=_dumps(meta),
        stored_document_id=p.stored_document_id,
        source_proposal_id=p.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=p.contract_id,
        review_id=p.review_id,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft reminder communication for proposal {p.proposal_reference}",
        commit=commit,
    )


def create_draft_for_repricing_proposal_esign_reminder(
    db: Session,
    *,
    acceptance_record_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    rec = db.get(ProposalAcceptanceRecord, acceptance_record_id)
    if not rec or rec.acceptance_type != "provider_esign":
        raise ValueError("Provider e-sign acceptance record not found")
    p = db.get(ContractRepricingProposal, rec.proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    if p.contract_id != rec.contract_id:
        raise ValueError("Acceptance record does not match proposal contract")

    dup = find_open_duplicate(
        db,
        contract_id=p.contract_id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
        source_entity_type="proposal_acceptance",
        source_entity_id=rec.id,
    )
    if dup:
        return dup

    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_repricing_proposal_esign_reminder(
        proposal_reference=p.proposal_reference,
        contract_code=c.contract_code,
        customer_name=cust.name if cust else "Customer",
        proposal_id=p.id,
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints, "acceptance_record_id": rec.id}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=p.contract_id,
        source_entity_type="proposal_acceptance",
        source_entity_id=rec.id,
        communication_type=tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER),
        metadata_json=_dumps(meta),
        stored_document_id=p.stored_document_id,
        source_proposal_id=p.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=p.contract_id,
        review_id=p.review_id,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft e-sign reminder for proposal {p.proposal_reference}",
        commit=commit,
    )


def create_draft_for_customer_response_follow_up(
    db: Session,
    *,
    proposal_id: str,
    response_type: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    if response_type == "rejected":
        ctype = tpl.COMMS_REPRICING_PROPOSAL_REJECTED_FOLLOW_UP
    elif response_type == "counter_requested":
        ctype = tpl.COMMS_REPRICING_PROPOSAL_COUNTER_REQUESTED_FOLLOW_UP
    else:
        raise ValueError("response_type must be rejected or counter_requested")

    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    dup = find_open_duplicate(
        db,
        contract_id=p.contract_id,
        communication_type=ctype,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
    )
    if dup:
        return dup
    c = db.get(Contract, p.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    if response_type == "rejected":
        r = tpl.render_repricing_rejected_follow_up(
            proposal_reference=p.proposal_reference,
            contract_code=c.contract_code,
            customer_name=cust.name if cust else "Customer",
            proposal_id=p.id,
            locale=loc,
        )
    else:
        r = tpl.render_repricing_counter_follow_up(
            proposal_reference=p.proposal_reference,
            contract_code=c.contract_code,
            customer_name=cust.name if cust else "Customer",
            proposal_id=p.id,
            locale=loc,
        )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints, "response_type": response_type}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=p.contract_id,
        source_entity_type="repricing_proposal",
        source_entity_id=p.id,
        communication_type=ctype,
        status="draft",
        channel=effective_channel_for_communication_type(ctype),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(ctype, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(ctype),
        metadata_json=_dumps(meta),
        stored_document_id=p.stored_document_id,
        source_proposal_id=p.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=p.contract_id,
        review_id=p.review_id,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft follow-up ({response_type}) for proposal {p.proposal_reference}",
        commit=commit,
    )


def create_draft_for_activation_confirmation_release(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status not in ("released", "viewed", "acknowledged"):
        raise ValueError("Confirmation must be released to customer portal before creating release communication")

    dup = find_open_duplicate(
        db,
        contract_id=conf.contract_id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_RELEASED,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
    )
    if dup:
        return dup

    c = db.get(Contract, conf.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_activation_confirmation_released(
        confirmation_reference=conf.confirmation_reference,
        contract_name=c.name,
        contract_code=c.contract_code,
        customer_name=cust.name if cust else "Customer",
        effective_date=conf.effective_date,
        confirmation_id=conf.id,
        stored_document_id=conf.stored_document_id,
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=conf.contract_id,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_RELEASED,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_ACTIVATION_CONFIRMATION_RELEASED),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_ACTIVATION_CONFIRMATION_RELEASED, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_ACTIVATION_CONFIRMATION_RELEASED),
        metadata_json=_dumps(meta),
        stored_document_id=conf.stored_document_id,
        source_activation_confirmation_id=conf.id,
        source_proposal_id=conf.source_proposal_id,
        source_amendment_id=conf.amendment_id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=conf.contract_id,
        review_id=None,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft activation confirmation communication {conf.confirmation_reference}",
        commit=commit,
    )


def create_draft_for_activation_confirmation_reminder(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status not in ("released", "viewed", "acknowledged"):
        raise ValueError("Invalid confirmation state for reminder")

    dup = find_open_duplicate(
        db,
        contract_id=conf.contract_id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
    )
    if dup:
        return dup

    c = db.get(Contract, conf.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_activation_confirmation_reminder(
        confirmation_reference=conf.confirmation_reference,
        contract_code=c.contract_code,
        customer_name=cust.name if cust else "Customer",
        confirmation_id=conf.id,
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=conf.contract_id,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER),
        metadata_json=_dumps(meta),
        stored_document_id=conf.stored_document_id,
        source_activation_confirmation_id=conf.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=conf.contract_id,
        review_id=None,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft activation reminder for {conf.confirmation_reference}",
        commit=commit,
    )


def create_draft_for_activation_acknowledgement_follow_up(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status not in ("released", "viewed", "acknowledged"):
        raise ValueError("Invalid confirmation state for acknowledgement follow-up")

    dup = find_open_duplicate(
        db,
        contract_id=conf.contract_id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
    )
    if dup:
        return dup

    c = db.get(Contract, conf.contract_id)
    if not c:
        raise ValueError("Contract not found")
    cust = db.get(Customer, c.customer_id)
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_activation_ack_follow_up(
        confirmation_reference=conf.confirmation_reference,
        contract_code=c.contract_code,
        customer_name=cust.name if cust else "Customer",
        confirmation_id=conf.id,
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "link_hints": r.link_hints}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=conf.contract_id,
        source_entity_type="activation_confirmation",
        source_entity_id=conf.id,
        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP,
        status="draft",
        channel=effective_channel_for_communication_type(tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP),
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP),
        metadata_json=_dumps(meta),
        stored_document_id=conf.stored_document_id,
        source_activation_confirmation_id=conf.id,
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=conf.contract_id,
        review_id=None,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary=f"Draft acknowledgement follow-up for {conf.confirmation_reference}",
        commit=commit,
    )


def create_draft_contract_follow_up_notice(
    db: Session,
    *,
    contract_id: str,
    internal_note: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")
    loc = resolve_communication_locale_for_contract(c)
    r = tpl.render_contract_follow_up_notice(
        contract_name=c.name,
        contract_code=c.contract_code,
        internal_note=internal_note.strip()[:8000],
        locale=loc,
    )
    meta = {"customer_safe_summary": r.customer_safe_summary, "internal": True}
    row = ContractCustomerCommunication(
        id=str(uuid.uuid4()),
        contract_id=c.id,
        source_entity_type="contract",
        source_entity_id=c.id,
        communication_type=tpl.COMMS_CONTRACT_FOLLOW_UP_NOTICE,
        status="draft",
        channel=tpl.CHANNEL_INTERNAL_DRAFT,
        subject=r.subject,
        body_text=r.body_text,
        body_html=r.body_html,
        template_key=tpl.template_key_for_type(tpl.COMMS_CONTRACT_FOLLOW_UP_NOTICE, locale=loc),
        recipient_customer_id=c.customer_id,
        created_by_user_id=actor_user_id,
        requires_approval=tpl.type_requires_approval(tpl.COMMS_CONTRACT_FOLLOW_UP_NOTICE),
        metadata_json=_dumps(meta),
    )
    return _persist_communication(
        db,
        row=row,
        contract_id=c.id,
        review_id=None,
        actor_user_id=actor_user_id,
        event="contract_customer_communication_created",
        summary="Draft internal contract follow-up notice",
        commit=commit,
    )


def mark_ready_to_send(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    if row.status != "draft":
        raise ValueError("Only draft communications can be marked ready")
    row.status = "ready_to_send"
    row.ready_at = utc_now()
    db.add(row)
    _log_commercial(
        db,
        contract_id=row.contract_id,
        review_id=None,
        action_type="contract_customer_communication_ready",
        summary=f"Communication {row.id} marked ready to send",
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def approve_for_send(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    if not row.requires_approval:
        raise ValueError("This communication does not require approval")
    if row.status != "ready_to_send":
        raise ValueError("Only ready_to_send communications can be approved")
    row.approved_at = utc_now()
    row.approved_by_user_id = actor_user_id
    db.add(row)
    _log_commercial(
        db,
        contract_id=row.contract_id,
        review_id=None,
        action_type="contract_customer_communication_approved",
        summary=f"Communication {row.id} approved for send",
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def _next_delivery_attempt_number(db: Session, communication_id: str) -> int:
    mx = (
        db.query(func.max(ContractCustomerCommunicationDelivery.attempt_number))
        .filter(ContractCustomerCommunicationDelivery.communication_id == communication_id)
        .scalar()
    )
    return int(mx or 0) + 1


def _execute_outbound_delivery(
    db: Session,
    row: ContractCustomerCommunication,
    actor_user_id: str | None,
    *,
    allow_retry_from_failed: bool,
    commit: bool,
    break_glass_override_suppression: bool = False,
    break_glass_reason: str | None = None,
) -> ContractCustomerCommunication:
    if row.status == "cancelled":
        raise ValueError("Cancelled communications cannot be sent")
    if allow_retry_from_failed:
        if row.status != "failed":
            raise ValueError("Only failed communications can be retried")
    elif row.status != "ready_to_send":
        raise ValueError("Communication must be ready_to_send before send")
    if row.requires_approval and not row.approved_at:
        raise ValueError("Communication requires approval before send")

    attempt_n = _next_delivery_attempt_number(db, row.id)
    delivery = ContractCustomerCommunicationDelivery(
        id=str(uuid.uuid4()),
        communication_id=row.id,
        channel=row.channel,
        provider_name="pending",
        attempt_number=attempt_n,
        status="started",
        started_at=utc_now(),
    )
    db.add(delivery)
    db.flush()

    def _fail_commercial(msg: str, payload: dict[str, Any] | None = None) -> None:
        p = {"contract_customer_communication_id": row.id, "delivery_id": delivery.id}
        if payload:
            p.update(payload)
        _log_commercial(
            db,
            contract_id=row.contract_id,
            review_id=None,
            action_type="contract_customer_communication_failed",
            summary=f"Communication {row.id} failed: {msg[:200]}",
            user_id=actor_user_id,
            payload=p,
        )

    def _sent_commercial(summary: str, payload_extra: dict[str, Any] | None = None) -> None:
        p = {
            "contract_customer_communication_id": row.id,
            "channel": row.channel,
            "delivery_id": delivery.id,
        }
        if payload_extra:
            p.update(payload_extra)
        _log_commercial(
            db,
            contract_id=row.contract_id,
            review_id=None,
            action_type="contract_customer_communication_sent",
            summary=summary,
            user_id=actor_user_id,
            payload=p,
        )

    try:
        if row.channel == "email":
            res = resolve_customer_communication_recipients(db, communication=row)
            prov = get_email_provider()
            delivery.provider_name = prov.provider_name()
            if not res.allowed:
                delivery.status = "failed"
                delivery.completed_at = utc_now()
                delivery.error_code = "recipient_blocked"
                delivery.error_message = res.block_reason
                delivery.response_payload_json = _dumps({"resolution": res.resolution_notes})
                row.status = "failed"
                row.failed_at = utc_now()
                row.sent_at = None
                row.error_json = _dumps({"message": res.block_reason})
                meta = _loads(row.metadata_json) or {}
                if res.quiet_hours_warning:
                    w = list(meta.get("outbound_warnings") or [])
                    w.append(res.quiet_hours_warning)
                    meta["outbound_warnings"] = w
                row.metadata_json = _dumps(meta)
                _fail_commercial(res.block_reason or "recipient blocked")
            else:
                delivery.recipient_address = res.recipient_email
                cust_for_suppress = row.recipient_customer_id
                if not cust_for_suppress:
                    ctr0 = db.get(Contract, row.contract_id)
                    if ctr0:
                        cust_for_suppress = ctr0.customer_id
                blocked, block_detail = (False, None)
                if cust_for_suppress and res.recipient_email:
                    blocked, block_detail = is_outbound_blocked(
                        db,
                        customer_id=cust_for_suppress,
                        recipient_email=res.recipient_email,
                    )
                bypass_suppression = False
                if blocked:
                    if break_glass_override_suppression and (break_glass_reason or "").strip():
                        from backend.app.services import authorization_policy as pol
                        from backend.app.services import authorization_service as authz
                        from backend.app.services.break_glass_audit_service import record_break_glass_override

                        u = db.get(User, actor_user_id) if actor_user_id else None
                        if u and authz.user_has_permission(
                            u, pol.CAN_BREAK_GLASS_COMMUNICATION_SUPPRESSION, db=db
                        ):
                            try:
                                record_break_glass_override(
                                    db,
                                    actor_user_id=actor_user_id,
                                    override_kind="communication_suppression",
                                    target_type="contract_customer_communication",
                                    target_id=row.id,
                                    reason=break_glass_reason or "",
                                    metadata={
                                        "contract_id": row.contract_id,
                                        "customer_id": cust_for_suppress,
                                        "recipient_email": res.recipient_email,
                                        "suppression_detail": block_detail,
                                    },
                                    commit=False,
                                )
                                bypass_suppression = True
                            except ValueError as e:
                                raise ValueError(str(e)) from e
                        else:
                            raise ValueError(
                                "Break-glass send requires can_break_glass_communication_suppression permission."
                            )
                    if not bypass_suppression:
                        if break_glass_override_suppression:
                            raise ValueError(
                                "Recipient suppressed: set break_glass_reason (≥12 characters) together with "
                                "break_glass_override_suppression, and use an account with break-glass permission."
                            )
                        delivery.status = "failed"
                        delivery.completed_at = utc_now()
                        delivery.error_code = "recipient_suppressed"
                        delivery.error_message = block_detail
                        delivery.response_payload_json = _dumps({"suppression": True})
                        row.status = "failed"
                        row.failed_at = utc_now()
                        row.sent_at = None
                        row.error_json = _dumps({"message": block_detail})
                        _fail_commercial(block_detail or "recipient suppressed", {"suppression": True})

                if (not blocked) or bypass_suppression:
                    meta = _loads(row.metadata_json) or {}
                    if bypass_suppression:
                        bg = list(meta.get("break_glass_events") or [])
                        bg.append(
                            {
                                "kind": "communication_suppression",
                                "at": utc_now().isoformat(),
                            }
                        )
                        meta["break_glass_events"] = bg
                    if res.quiet_hours_warning:
                        w = list(meta.get("outbound_warnings") or [])
                        w.append(res.quiet_hours_warning)
                        meta["outbound_warnings"] = w
                    row.metadata_json = _dumps(meta)
                    msg = OutboundEmailMessage(
                        to_address=res.recipient_email or "",
                        subject=row.subject or "",
                        body_text=row.body_text,
                        body_html=row.body_html,
                    )
                    result = prov.send_email(msg)
                    delivery.completed_at = utc_now()
                    merged_raw = {**result.raw_response, **result.normalize_for_storage()}
                    if not result.ok:
                        delivery.status = "failed"
                        delivery.error_code = result.error_code or "send_failed"
                        delivery.error_message = result.error_message
                        delivery.response_payload_json = dumps_response_payload(merged_raw)
                        row.status = "failed"
                        row.failed_at = utc_now()
                        row.sent_at = None
                        row.error_json = _dumps(
                            {"message": result.error_message, "code": result.error_code}
                        )
                        _fail_commercial(result.error_message or "send failed")
                    else:
                        delivery.status = "sent"
                        delivery.provider_message_id = result.provider_message_id
                        delivery.response_payload_json = dumps_response_payload(merged_raw)
                        row.status = "sent"
                        row.sent_at = utc_now()
                        row.failed_at = None
                        row.error_json = None
                        meta = _loads(row.metadata_json) or {}
                        meta["delivery"] = {
                            "provider": prov.provider_name(),
                            "last_delivery_id": delivery.id,
                            "provider_message_id": result.provider_message_id,
                        }
                        row.metadata_json = _dumps(meta)
                        _sent_commercial(
                            f"Communication {row.id} sent via {prov.provider_name()}",
                            {"provider": prov.provider_name()},
                        )

        elif row.channel == "sms":
            res = resolve_customer_communication_recipients(db, communication=row)
            prov = get_sms_provider()
            delivery.provider_name = prov.provider_name()
            if not res.allowed:
                delivery.status = "failed"
                delivery.completed_at = utc_now()
                delivery.error_code = "recipient_blocked"
                delivery.error_message = res.block_reason
                delivery.response_payload_json = _dumps({"resolution": res.resolution_notes})
                row.status = "failed"
                row.failed_at = utc_now()
                row.sent_at = None
                row.error_json = _dumps({"message": res.block_reason})
                meta = _loads(row.metadata_json) or {}
                if res.quiet_hours_warning:
                    w = list(meta.get("outbound_warnings") or [])
                    w.append(res.quiet_hours_warning)
                    meta["outbound_warnings"] = w
                row.metadata_json = _dumps(meta)
                _fail_commercial(res.block_reason or "recipient blocked")
            else:
                phone = _e164_for_sms(res.recipient_phone)
                if not phone:
                    delivery.status = "failed"
                    delivery.completed_at = utc_now()
                    delivery.error_code = "no_recipient"
                    delivery.error_message = "No valid SMS destination"
                    row.status = "failed"
                    row.failed_at = utc_now()
                    row.sent_at = None
                    row.error_json = _dumps({"message": "No valid SMS destination"})
                    _fail_commercial("No valid SMS destination")
                else:
                    delivery.recipient_address = phone
                    meta = _loads(row.metadata_json) or {}
                    if res.quiet_hours_warning:
                        w = list(meta.get("outbound_warnings") or [])
                        w.append(res.quiet_hours_warning)
                        meta["outbound_warnings"] = w
                    row.metadata_json = _dumps(meta)
                    body_out = (row.body_text or "").strip() or (row.subject or "Notice").strip()
                    if len(body_out) > 1600:
                        body_out = body_out[:1597] + "..."
                    smsg = OutboundSmsMessage(to_e164=phone, body=body_out)
                    result = prov.send_sms(smsg)
                    delivery.completed_at = utc_now()
                    merged_raw = {**result.raw_response, **result.normalize_for_storage()}
                    if not result.ok:
                        delivery.status = "failed"
                        delivery.error_code = result.error_code or "send_failed"
                        delivery.error_message = result.error_message
                        delivery.response_payload_json = dumps_sms_response_payload(merged_raw)
                        row.status = "failed"
                        row.failed_at = utc_now()
                        row.sent_at = None
                        row.error_json = _dumps(
                            {"message": result.error_message, "code": result.error_code}
                        )
                        _fail_commercial(result.error_message or "send failed")
                    else:
                        delivery.status = "sent"
                        delivery.provider_message_id = result.provider_message_id
                        delivery.response_payload_json = dumps_sms_response_payload(merged_raw)
                        row.status = "sent"
                        row.sent_at = utc_now()
                        row.failed_at = None
                        row.error_json = None
                        meta = _loads(row.metadata_json) or {}
                        meta["delivery"] = {
                            "provider": prov.provider_name(),
                            "last_delivery_id": delivery.id,
                            "provider_message_id": result.provider_message_id,
                        }
                        row.metadata_json = _dumps(meta)
                        _sent_commercial(
                            f"Communication {row.id} sent via {prov.provider_name()} (SMS)",
                            {"provider": prov.provider_name(), "channel": "sms"},
                        )

        elif row.channel in ("internal_draft", "portal_notice"):
            delivery.provider_name = "workflow_internal"
            delivery.status = "sent"
            delivery.completed_at = utc_now()
            delivery.response_payload_json = _dumps({"workflow_internal": True, "channel": row.channel})
            row.status = "sent"
            row.sent_at = utc_now()
            row.failed_at = None
            row.error_json = None
            meta = _loads(row.metadata_json) or {}
            meta["delivery"] = {"provider": "workflow_internal", "last_delivery_id": delivery.id}
            row.metadata_json = _dumps(meta)
            _sent_commercial(
                f"Communication {row.id} recorded (internal / non-SMTP channel)",
                {"provider": "workflow_internal"},
            )
        else:
            delivery.provider_name = "none"
            delivery.status = "failed"
            delivery.completed_at = utc_now()
            delivery.error_code = "unsupported_channel"
            em = f"Channel {row.channel} has no outbound adapter"
            delivery.error_message = em
            delivery.response_payload_json = _dumps({"channel": row.channel})
            row.status = "failed"
            row.failed_at = utc_now()
            row.sent_at = None
            row.error_json = _dumps({"message": em})
            _fail_commercial(em)
    finally:
        db.add(delivery)
        db.add(row)

    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def send_communication(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    commit: bool = True,
    break_glass_override_suppression: bool = False,
    break_glass_reason: str | None = None,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    return _execute_outbound_delivery(
        db,
        row,
        actor_user_id,
        allow_retry_from_failed=False,
        commit=commit,
        break_glass_override_suppression=break_glass_override_suppression,
        break_glass_reason=break_glass_reason,
    )


def retry_send_communication(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    commit: bool = True,
    break_glass_override_suppression: bool = False,
    break_glass_reason: str | None = None,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    if row.status == "cancelled":
        raise ValueError("Cancelled communications cannot be retried")
    _log_commercial(
        db,
        contract_id=row.contract_id,
        review_id=None,
        action_type="contract_customer_communication_retry_send",
        summary=f"Retry send requested for communication {row.id}",
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id},
    )
    return _execute_outbound_delivery(
        db,
        row,
        actor_user_id,
        allow_retry_from_failed=True,
        commit=commit,
        break_glass_override_suppression=break_glass_override_suppression,
        break_glass_reason=break_glass_reason,
    )


def cancel_communication(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    reason: str | None = None,
    commit: bool = True,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    if row.status in ("sent", "cancelled"):
        raise ValueError("Cannot cancel a sent or already cancelled communication")
    row.status = "cancelled"
    row.cancelled_at = utc_now()
    m = _loads(row.metadata_json) or {}
    if reason:
        m["cancel_reason"] = reason[:2000]
    row.metadata_json = _dumps(m)
    db.add(row)
    _log_commercial(
        db,
        contract_id=row.contract_id,
        review_id=None,
        action_type="contract_customer_communication_cancelled",
        summary=f"Communication {row.id} cancelled",
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id, "reason": reason},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def mark_failed(
    db: Session,
    *,
    communication_id: str,
    actor_user_id: str | None,
    error_message: str,
    commit: bool = True,
) -> ContractCustomerCommunication:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise ValueError("Communication not found")
    if row.status != "ready_to_send":
        raise ValueError("Only ready_to_send can be marked failed (after delivery attempt)")
    row.status = "failed"
    row.failed_at = utc_now()
    row.error_json = _dumps({"message": error_message[:4000]})
    db.add(row)
    _log_commercial(
        db,
        contract_id=row.contract_id,
        review_id=None,
        action_type="contract_customer_communication_failed",
        summary=f"Communication {row.id} failed: {error_message[:200]}",
        user_id=actor_user_id,
        payload={"contract_customer_communication_id": row.id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def list_communications(
    db: Session,
    *,
    contract_id: str | None = None,
    status: str | None = None,
    communication_type: str | None = None,
    source_entity_type: str | None = None,
    source_entity_id: str | None = None,
    channel: str | None = None,
    requires_approval: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ContractCustomerCommunication]:
    q = db.query(ContractCustomerCommunication).order_by(ContractCustomerCommunication.created_at.desc())
    if contract_id:
        q = q.filter(ContractCustomerCommunication.contract_id == contract_id)
    if status:
        q = q.filter(ContractCustomerCommunication.status == status)
    if communication_type:
        q = q.filter(ContractCustomerCommunication.communication_type == communication_type)
    if source_entity_type:
        q = q.filter(ContractCustomerCommunication.source_entity_type == source_entity_type)
    if source_entity_id:
        q = q.filter(ContractCustomerCommunication.source_entity_id == source_entity_id)
    if channel:
        q = q.filter(ContractCustomerCommunication.channel == channel)
    if requires_approval is not None:
        q = q.filter(ContractCustomerCommunication.requires_approval.is_(requires_approval))
    return q.offset(offset).limit(limit).all()


def dashboard_customer_communications(db: Session) -> dict[str, Any]:
    rows = db.query(ContractCustomerCommunication).all()
    buckets: dict[str, int] = {
        "draft": 0,
        "ready_to_send": 0,
        "sent": 0,
        "failed": 0,
        "cancelled": 0,
    }
    pending_approval = 0
    for r in rows:
        if r.status in buckets:
            buckets[r.status] += 1
        if r.requires_approval and r.status == "ready_to_send" and not r.approved_at:
            pending_approval += 1
    return {
        "by_status": buckets,
        "pending_approval_ready": pending_approval,
        "total": len(rows),
    }


def dashboard_customer_communications_follow_up(db: Session) -> dict[str, Any]:
    """Heuristic pipeline hints — not automated sends."""
    now = utc_now()
    horizon = now - timedelta(days=7)

    proposals = (
        db.query(ContractRepricingProposal)
        .filter(
            ContractRepricingProposal.customer_release_status.in_(("released", "viewed")),
            ContractRepricingProposal.customer_response_status.is_(None),
        )
        .all()
    )
    proposal_reminder_candidates: list[str] = []
    for p in proposals:
        ra = _as_utc_aware(p.released_to_customer_at)
        if ra is not None and ra < horizon:
            proposal_reminder_candidates.append(p.id)

    confs = (
        db.query(ContractActivationConfirmation)
        .filter(
            ContractActivationConfirmation.status == "released",
            ContractActivationConfirmation.customer_viewed_at.is_(None),
        )
        .all()
    )
    activation_view_reminder_candidates: list[str] = []
    for c in confs:
        ra = _as_utc_aware(c.released_to_customer_at)
        if ra is not None and ra < horizon:
            activation_view_reminder_candidates.append(c.id)

    viewed_unacked = (
        db.query(ContractActivationConfirmation)
        .filter(
            ContractActivationConfirmation.status == "viewed",
            ContractActivationConfirmation.customer_acknowledged_at.is_(None),
        )
        .all()
    )

    return {
        "repricing_proposal_reminder_candidates": proposal_reminder_candidates,
        "activation_confirmation_view_reminder_candidates": activation_view_reminder_candidates,
        "activation_confirmation_ack_candidates": [c.id for c in viewed_unacked],
    }


def list_deliveries_for_communication(
    db: Session, *, communication_id: str
) -> list[ContractCustomerCommunicationDelivery]:
    return (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.communication_id == communication_id)
        .order_by(ContractCustomerCommunicationDelivery.attempt_number.asc())
        .all()
    )


def dashboard_customer_communications_delivery(db: Session) -> dict[str, Any]:
    now = utc_now()
    since = now - timedelta(hours=24)
    del_rows = db.query(ContractCustomerCommunicationDelivery).all()
    by_d_status: dict[str, int] = {}
    for d in del_rows:
        by_d_status[d.status] = by_d_status.get(d.status, 0) + 1

    comms = db.query(ContractCustomerCommunication).all()
    ready = sum(1 for c in comms if c.status == "ready_to_send")
    failed_c = sum(1 for c in comms if c.status == "failed")
    sent_recent = 0
    for c in comms:
        if c.status != "sent" or not c.sent_at:
            continue
        st = _as_utc_aware(c.sent_at)
        if st is not None and st >= since:
            sent_recent += 1

    retryable = [c.id for c in comms if c.status == "failed" and c.cancelled_at is None]

    pending_approval = sum(
        1
        for c in comms
        if c.requires_approval and c.status == "ready_to_send" and not c.approved_at
    )

    return {
        "delivery_attempts_by_status": by_d_status,
        "communications_ready_to_send": ready,
        "communications_failed": failed_c,
        "communications_sent_last_24h": sent_recent,
        "retryable_failed_communication_ids": retryable,
        "pending_approval_ready_to_send": pending_approval,
        "total_delivery_attempts": len(del_rows),
    }


def dashboard_customer_communications_failures(db: Session) -> dict[str, Any]:
    failed_deliveries = (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.status == "failed")
        .order_by(ContractCustomerCommunicationDelivery.started_at.desc())
        .limit(100)
        .all()
    )
    failed_comms = (
        db.query(ContractCustomerCommunication)
        .filter(ContractCustomerCommunication.status == "failed")
        .order_by(ContractCustomerCommunication.failed_at.desc())
        .limit(100)
        .all()
    )

    disabled_global = (
        db.query(CustomerCommunicationPreference)
        .filter(
            CustomerCommunicationPreference.channel == "email",
            CustomerCommunicationPreference.contact_reference.is_(None),
            CustomerCommunicationPreference.enabled.is_(False),
        )
        .all()
    )

    return {
        "failed_communication_ids": [c.id for c in failed_comms],
        "failed_communication_count": db.query(ContractCustomerCommunication)
        .filter(ContractCustomerCommunication.status == "failed")
        .count(),
        "failed_delivery_attempt_count": db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.status == "failed")
        .count(),
        "recent_failed_delivery_ids": [d.id for d in failed_deliveries[:20]],
        "customers_with_global_email_disabled": [p.customer_id for p in disabled_global],
    }
