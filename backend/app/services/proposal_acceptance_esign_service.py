"""
Provider-backed e-sign sessions for repricing proposals: creation, webhook finalization, cancellation.

In-product acceptance remains in proposal_acceptance_service; this module handles third-party flows only.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.crm.models import Customer
from backend.app.modules.documents.models import StoredDocument
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord, ProposalAcceptanceSession
from backend.app.modules.contracts.review_models import ContractCommercialActionLog, ContractRepricingProposal
from backend.app.services import customer_repricing_proposal_service as crps
from backend.app.services.customer_repricing_proposal_service import audit_actor_user_id
from backend.app.services import document_storage_service as doc_storage
from backend.app.services.esign_provider_service import (
    EsignProviderError,
    EsignSignatureRequestContext,
    NormalizedEsignEvent,
    dumps_safe_metadata,
    esign_integration_enabled,
    get_esign_provider,
    redact_provider_payload_for_storage,
)
from backend.app.services.proposal_acceptance_service import (
    _cancel_active_sessions_for_proposal,
    assert_proposal_eligible_for_acceptance_session,
    stable_acceptance_hash,
    _build_commercial_snapshot,
)


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


def _load_proposal_pdf_for_esign(db: Session, *, proposal: ContractRepricingProposal) -> tuple[bytes, str]:
    if not proposal.stored_document_id:
        raise ValueError("Generate and store a proposal PDF before starting DocuSign e-sign")
    doc = db.get(StoredDocument, proposal.stored_document_id)
    if not doc:
        raise ValueError("Stored proposal document not found")
    ct = (doc.content_type or "").lower()
    if ct and "pdf" not in ct:
        raise ValueError("Proposal document must be a PDF for DocuSign e-sign")
    if not doc_storage.document_exists(storage_key=doc.storage_key):
        raise ValueError("Proposal PDF binary is missing from storage")
    data = doc_storage.stream_document(storage_key=doc.storage_key).read()
    return data, (doc.filename or "proposal.pdf").strip() or "proposal.pdf"


def _resolve_signer_email(db: Session, *, customer_id: str, explicit: str | None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    cust = db.get(Customer, customer_id)
    if cust and cust.email and cust.email.strip():
        return cust.email.strip()
    return None


def _mark_esign_create_failed(
    db: Session,
    *,
    record: ProposalAcceptanceRecord,
    session: ProposalAcceptanceSession,
    proposal: ContractRepricingProposal,
    actor_user_id: str,
    message: str,
) -> None:
    record.provider_status = "failed"
    record.acceptance_status = "cancelled"
    session.session_status = "cancelled"
    session.completed_at = utc_now()
    record.provider_payload_json = dumps_safe_metadata(
        redact_provider_payload_for_storage(
            {
                "create_failed": True,
                "error_summary": message[:500],
            }
        )
    )
    _log_commercial(
        db,
        contract_id=proposal.contract_id,
        review_id=proposal.review_id,
        action_type="proposal_esign_create_failed",
        summary=f"Provider e-sign create failed for {proposal.proposal_reference}: {message[:200]}",
        user_id=actor_user_id,
        payload={"proposal_id": proposal.id, "acceptance_record_id": record.id, "session_id": session.id},
    )


def _has_completed_acceptance(db: Session, *, proposal_id: str) -> bool:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_status == "completed",
        )
        .first()
        is not None
    )


def create_provider_esign_session_for_proposal(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    expires_at: datetime | None = None,
    signer_email: str | None = None,
    signer_name: str | None = None,
) -> dict[str, Any]:
    if not esign_integration_enabled():
        raise ValueError("E-sign integration is disabled (PHI_DPS_ESIGN_ENABLED)")

    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")

    assert_proposal_eligible_for_acceptance_session(db, proposal=p)
    if _has_completed_acceptance(db, proposal_id=proposal_id):
        raise ValueError("A completed acceptance already exists for this proposal")

    from backend.app.modules.contracts.models import Contract

    contract = db.get(Contract, p.contract_id)
    if not contract:
        raise ValueError("Contract not found")

    _cancel_active_sessions_for_proposal(
        db,
        proposal_id=proposal_id,
        except_session_id=None,
        actor_user_id=actor_user_id,
        reason="replaced_by_provider_esign_session",
    )

    now = utc_now()
    exp = expires_at or (now + timedelta(days=14))

    record = ProposalAcceptanceRecord(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        contract_id=contract.id,
        customer_id=contract.customer_id,
        source_proposal_reference=p.proposal_reference,
        acceptance_status="initiated",
        acceptance_type="provider_esign",
        acceptance_evidence_type="provider_esign",
        acceptance_channel="provider_esign",
        initiated_at=now,
        created_by_user_id=actor_user_id,
        provider_name=get_esign_provider().provider_name(),
        provider_status="draft",
    )
    db.add(record)
    db.flush()

    session = ProposalAcceptanceSession(
        id=str(uuid.uuid4()),
        proposal_id=p.id,
        acceptance_record_id=record.id,
        session_status="active",
        expires_at=exp,
        created_by_user_id=actor_user_id,
        esign_provider_flow=True,
        metadata_json=_dumps({"purpose": "provider_esign"}),
    )
    db.add(session)
    db.flush()

    provider = get_esign_provider()
    pdf_bytes: bytes | None = None
    pdf_name: str | None = None
    if provider.provider_name() == "docusign":
        pdf_bytes, pdf_name = _load_proposal_pdf_for_esign(db, proposal=p)

    resolved_email = _resolve_signer_email(db, customer_id=contract.customer_id, explicit=signer_email)
    if provider.provider_name() == "docusign" and not resolved_email:
        raise ValueError(
            "DocuSign requires a signer email; set the customer email or pass signer_email when creating the session"
        )

    ctx = EsignSignatureRequestContext(
        proposal_id=p.id,
        proposal_reference=p.proposal_reference,
        contract_id=contract.id,
        customer_id=contract.customer_id,
        signer_email=resolved_email,
        signer_name=signer_name,
        document_title=f"Repricing proposal {p.proposal_reference}",
        callback_reference=record.id,
        document_pdf_bytes=pdf_bytes,
        document_file_name=pdf_name,
    )
    try:
        result = provider.create_signature_request(ctx)
    except EsignProviderError as e:
        _mark_esign_create_failed(
            db,
            record=record,
            session=session,
            proposal=p,
            actor_user_id=actor_user_id,
            message=str(e),
        )
        db.commit()
        raise ValueError(str(e)) from e

    record.provider_envelope_id = result.envelope_id
    record.provider_session_id = result.provider_session_id
    record.provider_status = "sent"
    record.provider_payload_json = dumps_safe_metadata(
        redact_provider_payload_for_storage(
            {
                "create_result_metadata": result.provider_metadata,
                "signing_url_host_only": _host_only(result.signing_url),
            }
        )
    )

    _log_commercial(
        db,
        contract_id=p.contract_id,
        review_id=p.review_id,
        action_type="proposal_esign_session_created",
        summary=f"Provider e-sign session created for {p.proposal_reference}",
        user_id=actor_user_id,
        payload={
            "proposal_id": p.id,
            "acceptance_record_id": record.id,
            "session_id": session.id,
            "provider": record.provider_name,
            "envelope_id": result.envelope_id,
        },
    )
    db.flush()

    return {
        "acceptance_record_id": record.id,
        "session_id": session.id,
        "signing_url": result.signing_url,
        "provider": record.provider_name,
        "provider_envelope_id": result.envelope_id,
        "expires_at": exp.isoformat(),
    }


def _host_only(url: str) -> str | None:
    from urllib.parse import urlparse

    try:
        u = urlparse(url)
        return u.netloc or None
    except Exception:
        return None


def apply_esign_webhook_event(
    db: Session,
    *,
    event: NormalizedEsignEvent,
    raw_payload_for_audit: dict[str, Any],
) -> dict[str, Any]:
    """Apply a validated, normalized provider event. Caller must verify webhook first."""
    rec = (
        db.query(ProposalAcceptanceRecord)
        .filter(ProposalAcceptanceRecord.provider_envelope_id == event.envelope_id)
        .first()
    )
    if not rec:
        return {"applied": False, "reason": "envelope_not_found"}

    p = db.get(ContractRepricingProposal, rec.proposal_id)
    if not p:
        return {"applied": False, "reason": "proposal_not_found"}

    actor = audit_actor_user_id(db, proposal=p)

    merged = _loads(rec.provider_payload_json) or {}
    webhook_key = f"{event.envelope_id}|{event.status}|{event.safe_payload.get('generatedDateTime')}"
    if webhook_key and merged.get("last_webhook_key") == webhook_key:
        db.flush()
        return {"applied": True, "effect": "duplicate_ignored"}

    if event.status == "signed" and rec.acceptance_status == "completed":
        db.flush()
        return {"applied": True, "effect": "already_completed"}

    if event.status not in ("viewed", "signed", "declined", "voided", "expired", "failed", "sent"):
        db.flush()
        return {"applied": False, "reason": "unhandled_status"}

    safe_audit = redact_provider_payload_for_storage(raw_payload_for_audit)
    merged["last_event"] = event.safe_payload
    merged["audit_events"] = (merged.get("audit_events") or []) + [safe_audit]
    merged["last_webhook_key"] = webhook_key
    rec.provider_payload_json = dumps_safe_metadata(merged)

    if event.status == "viewed":
        rec.provider_status = "viewed"
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type="proposal_esign_viewed",
            summary=f"Provider e-sign viewed for {p.proposal_reference}",
            user_id=actor,
            payload={"proposal_id": p.id, "acceptance_record_id": rec.id, "envelope_id": event.envelope_id},
        )
        db.flush()
        return {"applied": True, "effect": "viewed"}

    if event.status == "signed":
        _finalize_provider_signed(db, record=rec, proposal=p, actor_user_id=actor, event=event)
        db.flush()
        return {"applied": True, "effect": "signed_completed"}

    if event.status in ("declined", "voided", "expired", "failed"):
        rec.provider_status = event.status
        if rec.acceptance_status not in ("completed",):
            rec.acceptance_status = "cancelled"
        sess = (
            db.query(ProposalAcceptanceSession)
            .filter(
                ProposalAcceptanceSession.acceptance_record_id == rec.id,
                ProposalAcceptanceSession.session_status == "active",
            )
            .first()
        )
        if sess:
            sess.session_status = "cancelled"
            sess.completed_at = utc_now()
        action = {
            "declined": "proposal_esign_declined",
            "voided": "proposal_esign_voided",
            "expired": "proposal_esign_expired",
            "failed": "proposal_esign_failed",
        }.get(event.status, "proposal_esign_declined")
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type=action,
            summary=f"Provider e-sign {event.status} for {p.proposal_reference}",
            user_id=actor,
            payload={"proposal_id": p.id, "acceptance_record_id": rec.id, "envelope_id": event.envelope_id},
        )
        db.flush()
        return {"applied": True, "effect": event.status}

    if event.status == "sent":
        rec.provider_status = "sent"
        db.flush()
        return {"applied": True, "effect": "sent_ack"}

    raise RuntimeError("esign webhook: unhandled normalized status after guard")


def _finalize_provider_signed(
    db: Session,
    *,
    record: ProposalAcceptanceRecord,
    proposal: ContractRepricingProposal,
    actor_user_id: str,
    event: NormalizedEsignEvent,
) -> None:
    now = utc_now()
    record.provider_status = "signed"
    record.provider_completed_at = now

    evidence: dict[str, Any] = {
        "schema_version": 2,
        "disclosure": (
            "This acceptance record reflects a third-party e-sign provider completion event ingested by PHI-DPS. "
            "Legal effect depends on your configured provider and jurisdiction; PHI-DPS stores provider correlation "
            "metadata and a redacted event payload for audit."
        ),
        "acceptance_evidence_type": "provider_esign",
        "provider_name": record.provider_name,
        "provider_envelope_id": record.provider_envelope_id,
        "provider_session_id": record.provider_session_id,
        "normalized_event": event.safe_payload,
        "proposal_commercial_snapshot_at_completion": _build_commercial_snapshot(proposal),
        "completed_at": now.isoformat(),
        "customer_id": record.customer_id,
    }
    imm = stable_acceptance_hash(evidence)
    record.acceptance_status = "completed"
    record.completed_at = now
    record.evidence_json = _dumps(evidence)
    record.immutable_hash = imm

    proposal.formal_acceptance_record_id = record.id
    proposal.updated_at = now

    sess = (
        db.query(ProposalAcceptanceSession)
        .filter(
            ProposalAcceptanceSession.acceptance_record_id == record.id,
            ProposalAcceptanceSession.session_status == "active",
        )
        .first()
    )
    if sess:
        sess.session_status = "completed"
        sess.completed_at = now

    if proposal.customer_release_status != "responded":
        crps.record_customer_response(
            db,
            proposal_id=proposal.id,
            portal_user_id=actor_user_id,
            customer_id=record.customer_id,
            response_type="accepted",
            notes="Accepted via legal e-sign provider",
            contact_reference=record.signed_email,
            metadata_json={
                "formal_acceptance_record_id": record.id,
                "formal_acceptance": True,
                "acceptance_evidence_type": "provider_esign",
                "immutable_hash": imm,
                "provider_envelope_id": record.provider_envelope_id,
            },
            commit=False,
        )
    elif proposal.customer_response_status == "accepted":
        pass
    else:
        raise ValueError("Cannot align provider e-sign with existing non-accepted customer response")

    _log_commercial(
        db,
        contract_id=proposal.contract_id,
        review_id=proposal.review_id,
        action_type="proposal_esign_completed",
        summary=f"Provider e-sign completed for {proposal.proposal_reference}",
        user_id=actor_user_id,
        payload={
            "proposal_id": proposal.id,
            "acceptance_record_id": record.id,
            "immutable_hash": imm,
            "provider": record.provider_name,
        },
    )


def cancel_provider_esign_session(
    db: Session,
    *,
    session_id: str,
    actor_user_id: str,
) -> ProposalAcceptanceSession:
    s = db.get(ProposalAcceptanceSession, session_id)
    if not s:
        raise ValueError("Session not found")
    if not s.esign_provider_flow:
        raise ValueError("Session is not a provider e-sign session")
    if s.session_status != "active":
        raise ValueError("Session is not active")

    rec = s.acceptance_record_id and db.get(ProposalAcceptanceRecord, s.acceptance_record_id)
    if not rec or not rec.provider_envelope_id:
        raise ValueError("Acceptance record missing provider envelope")
    if rec.acceptance_status == "completed":
        raise ValueError("Cannot cancel a completed provider e-sign acceptance")

    try:
        get_esign_provider().cancel_signature_request(envelope_id=rec.provider_envelope_id)
    except EsignProviderError as ex:
        p0 = db.get(ContractRepricingProposal, s.proposal_id)
        if p0:
            _log_commercial(
                db,
                contract_id=p0.contract_id,
                review_id=p0.review_id,
                action_type="proposal_esign_remote_void_failed",
                summary=f"Provider void API failed; local session cancelled: {str(ex)[:160]}",
                user_id=actor_user_id,
                payload={"session_id": s.id, "envelope_id": rec.provider_envelope_id},
            )
    rec.provider_status = "voided"
    if rec.acceptance_status in ("initiated", "viewed"):
        rec.acceptance_status = "cancelled"
    s.session_status = "cancelled"
    s.completed_at = utc_now()

    p = db.get(ContractRepricingProposal, s.proposal_id)
    if p:
        _log_commercial(
            db,
            contract_id=p.contract_id,
            review_id=p.review_id,
            action_type="proposal_esign_voided",
            summary=f"Provider e-sign cancelled for {p.proposal_reference}",
            user_id=actor_user_id,
            payload={"proposal_id": p.id, "session_id": s.id, "acceptance_record_id": rec.id},
        )
    return s


def provider_status_public_dict(record: ProposalAcceptanceRecord) -> dict[str, Any]:
    return {
        "acceptance_record_id": record.id,
        "proposal_id": record.proposal_id,
        "provider_name": record.provider_name,
        "provider_status": record.provider_status,
        "provider_envelope_id": record.provider_envelope_id,
        "provider_completed_at": record.provider_completed_at.isoformat() if record.provider_completed_at else None,
        "acceptance_status": record.acceptance_status,
        "acceptance_evidence_type": record.acceptance_evidence_type,
    }


def dashboard_esign_status(db: Session, *, limit: int = 200) -> dict[str, Any]:
    enabled = esign_integration_enabled()
    rows = (
        db.query(ProposalAcceptanceRecord)
        .filter(ProposalAcceptanceRecord.acceptance_type == "provider_esign")
        .order_by(ProposalAcceptanceRecord.initiated_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        p = db.get(ContractRepricingProposal, r.proposal_id)
        summ = provider_status_internal_summary(r)
        out.append(
            {
                **summ,
                "proposal_reference": p.proposal_reference if p else None,
                "contract_id": r.contract_id,
            }
        )
    in_progress = [x for x in out if x["acceptance_status"] not in ("completed", "cancelled") and x["provider_status"] not in ("signed", "declined", "voided", "expired", "failed")]
    declined = [x for x in out if x["provider_status"] in ("declined", "voided", "expired", "failed")]
    signed = [x for x in out if x["provider_status"] == "signed" and x["acceptance_status"] == "completed"]
    return {
        "integration_enabled": enabled,
        "total_tracked": len(out),
        "in_progress": in_progress,
        "signed_completed": signed,
        "declined_or_terminal": declined,
    }


def provider_status_internal_summary(record: ProposalAcceptanceRecord) -> dict[str, Any]:
    """RBAC-internal summary: no raw provider payload bodies (keys only for support)."""
    base = provider_status_public_dict(record)
    keys: list[str] = []
    last_connect_event: str | None = None
    last_webhook_generated_at: str | None = None
    raw = getattr(record, "provider_payload_json", None)
    if raw:
        try:
            o = json.loads(raw)
            if isinstance(o, dict):
                keys = sorted(str(k) for k in o.keys())
                le = o.get("last_event")
                if isinstance(le, dict):
                    ce = le.get("connect_event")
                    if ce is not None:
                        last_connect_event = str(ce)
                    gd = le.get("generatedDateTime")
                    if gd is not None:
                        last_webhook_generated_at = str(gd)
        except Exception:
            keys = []
    return {
        **base,
        "stored_payload_top_level_keys": keys,
        "last_connect_event": last_connect_event,
        "last_webhook_generated_at": last_webhook_generated_at,
    }
