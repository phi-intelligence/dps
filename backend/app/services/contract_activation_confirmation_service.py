"""
Customer activation confirmation: internal activation truth vs customer-communicable release workflow.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import ContractCommercialActionLog
from backend.app.modules.crm.models import Customer
from backend.app.modules.documents.models import StoredDocument
from backend.app.modules.portal.portal_access_service import can_customer_access_contract, can_customer_access_site


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


_TERMINAL_CONFIRMATION_STATUSES = frozenset({"withdrawn", "superseded"})


def _log_commercial(
    db: Session,
    *,
    contract_id: str,
    review_id: str | None,
    action_type: str,
    summary: str,
    performed_by_user_id: str | None,
    payload: dict[str, Any] | None = None,
) -> None:
    p = dict(payload or {})
    db.add(
        ContractCommercialActionLog(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            review_id=review_id,
            action_type=action_type,
            action_summary=summary,
            performed_by_user_id=performed_by_user_id,
            performed_at=utc_now(),
            payload_json=_dumps(p) if p else None,
        )
    )


def _safe_ref_part(code: str) -> str:
    x = re.sub(r"[^A-Za-z0-9]+", "-", code).strip("-").upper()
    return (x[:12] or "CTR")[:12]


def _customer_safe_summary_from_amendment(a: ContractAmendment) -> dict[str, Any]:
    raw = _loads(a.change_summary_json) or {}
    prior_v = a.current_contract_value
    new_v = a.proposed_contract_value
    lines: list[str] = []
    if prior_v is not None and new_v is not None and prior_v != new_v:
        lines.append("Your contract commercial value has been updated to reflect the agreed change.")
    elif new_v is not None:
        lines.append("Your contract commercial terms have been updated.")
    else:
        lines.append("Your contract has been updated following the approved commercial change.")
    if isinstance(raw, dict):
        ref = raw.get("amendment_reference")
        if ref:
            lines.append(f"Reference: {ref}")
    return {
        "headline": "Contract change is now live",
        "body_lines": lines,
        "amendment_reference": a.amendment_reference,
        "amendment_type": a.amendment_type,
        "prior_contract_value": prior_v,
        "new_contract_value": new_v,
        "effective_date": a.effective_date.isoformat() if a.effective_date else None,
    }


def portal_safe_summary(summary: dict[str, Any] | None) -> dict[str, Any]:
    """Strip any keys that must not appear in customer API responses."""
    if not summary or not isinstance(summary, dict):
        return {}
    allowed = {
        "headline",
        "body_lines",
        "amendment_reference",
        "amendment_type",
        "prior_contract_value",
        "new_contract_value",
        "effective_date",
    }
    return {k: summary[k] for k in allowed if k in summary}


def get_active_confirmation_for_amendment(db: Session, *, amendment_id: str) -> ContractActivationConfirmation | None:
    return (
        db.query(ContractActivationConfirmation)
        .filter(
            ContractActivationConfirmation.amendment_id == amendment_id,
            ContractActivationConfirmation.status.notin_(_TERMINAL_CONFIRMATION_STATUSES),
        )
        .order_by(ContractActivationConfirmation.created_at.desc())
        .first()
    )


def create_activation_confirmation_from_amendment(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    existing = get_active_confirmation_for_amendment(db, amendment_id=amendment_id)
    if existing:
        return existing

    a = db.get(ContractAmendment, amendment_id)
    if not a:
        raise ValueError("Amendment not found")
    if a.status != "activated":
        raise ValueError("Amendment must be activated before creating a customer activation confirmation")
    c = db.get(Contract, a.contract_id)
    if not c:
        raise ValueError("Contract not found")

    ref = f"CAC-{_safe_ref_part(c.contract_code)}-{uuid.uuid4().hex[:8].upper()}"
    summary = _customer_safe_summary_from_amendment(a)
    row = ContractActivationConfirmation(
        id=str(uuid.uuid4()),
        contract_id=a.contract_id,
        amendment_id=a.id,
        contract_version_id=a.resulting_contract_version_id,
        source_proposal_id=a.source_proposal_id,
        status="pending_generation",
        confirmation_reference=ref,
        effective_date=a.effective_date,
        activated_at=a.activated_at or utc_now(),
        summary_json=_dumps(summary),
        notes=None,
        created_by_user_id=actor_user_id,
    )
    db.add(row)
    _log_commercial(
        db,
        contract_id=a.contract_id,
        review_id=a.source_review_id,
        action_type="activation_confirmation_created",
        summary=f"Activation confirmation {ref} created (pending PDF generation)",
        performed_by_user_id=actor_user_id,
        payload={"activation_confirmation_id": row.id, "amendment_id": a.id},
    )
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def generate_activation_confirmation_pdf(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    from backend.app.modules.documents.persist import persist_activation_confirmation_pdf

    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status != "pending_generation":
        raise ValueError("PDF can only be generated while confirmation is pending_generation")

    doc = persist_activation_confirmation_pdf(
        db, confirmation_id=confirmation_id, uploaded_by_user_id=actor_user_id, commit=False
    )
    conf.stored_document_id = doc.id
    conf.confirmation_generated_at = utc_now()
    conf.status = "generated"
    db.add(conf)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_pdf_generated",
        summary=f"PDF generated for activation confirmation {conf.confirmation_reference}",
        performed_by_user_id=actor_user_id,
        payload={
            "activation_confirmation_id": conf.id,
            "stored_document_id": doc.id,
        },
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def mark_ready_for_customer(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status != "generated":
        raise ValueError("Only generated confirmations can be marked ready for customer")
    conf.status = "ready_for_customer"
    db.add(conf)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_ready_for_customer",
        summary=f"Activation confirmation {conf.confirmation_reference} marked ready for customer release",
        performed_by_user_id=actor_user_id,
        payload={"activation_confirmation_id": conf.id},
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def release_activation_confirmation_to_customer(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    notes: str | None = None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status not in ("generated", "ready_for_customer"):
        raise ValueError("Only generated or ready_for_customer confirmations can be released")
    if not conf.stored_document_id:
        raise ValueError("Confirmation has no stored document; generate PDF first")

    doc = db.get(StoredDocument, conf.stored_document_id)
    if not doc:
        raise ValueError("Stored document not found")

    now = utc_now()
    conf.status = "released"
    conf.released_to_customer_at = now
    conf.released_by_user_id = actor_user_id
    conf.portal_visibility_scope = "contract_customer_portal"
    doc.visibility_scope = "customer_activation_confirmation"
    if notes:
        conf.notes = (conf.notes + "\n" if conf.notes else "") + f"[release] {notes}"

    db.add(conf)
    db.add(doc)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_released",
        summary=f"Activation confirmation {conf.confirmation_reference} released to customer portal",
        performed_by_user_id=actor_user_id,
        payload={"activation_confirmation_id": conf.id, "stored_document_id": doc.id, "notes": notes},
    )
    from backend.app.services import contract_customer_communication_service as cccs

    cccs.create_draft_for_activation_confirmation_release(
        db, confirmation_id=conf.id, actor_user_id=actor_user_id, commit=False
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def withdraw_activation_confirmation_from_customer(
    db: Session,
    *,
    confirmation_id: str,
    actor_user_id: str | None,
    reason: str | None = None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")
    if conf.status not in ("released", "viewed", "acknowledged"):
        raise ValueError("Only released, viewed, or acknowledged confirmations can be withdrawn from the portal")

    if conf.stored_document_id:
        doc = db.get(StoredDocument, conf.stored_document_id)
        if doc:
            doc.visibility_scope = "internal_only"
            db.add(doc)

    conf.status = "withdrawn"
    conf.portal_visibility_scope = None
    if reason:
        conf.notes = (conf.notes + "\n" if conf.notes else "") + f"[withdraw] {reason}"

    db.add(conf)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_withdrawn",
        summary=f"Activation confirmation {conf.confirmation_reference} withdrawn from customer portal",
        performed_by_user_id=actor_user_id,
        payload={"activation_confirmation_id": conf.id, "reason": reason},
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def portal_customer_can_access_activation_confirmation(
    db: Session,
    *,
    customer: Customer,
    conf: ContractActivationConfirmation,
    portal_login_email: str | None = None,
) -> bool:
    if conf.status not in ("released", "viewed", "acknowledged"):
        return False
    if conf.portal_visibility_scope != "contract_customer_portal":
        return False
    em = portal_login_email
    if not can_customer_access_contract(
        db, customer=customer, contract_id=conf.contract_id, portal_login_email=em
    ):
        return False
    c = db.get(Contract, conf.contract_id)
    if c and c.site_id:
        if not can_customer_access_site(db, customer=customer, site_id=c.site_id, portal_login_email=em):
            return False
    from backend.app.services import portal_customer_scope_service as _pcs

    pem = (portal_login_email or customer.email or "").strip().lower()
    if pem and _pcs.customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=pem):
        if not _pcs.customer_portal_activation_confirmation_allowed(
            db,
            customer=customer,
            portal_login_email=pem,
            confirmation_id=conf.id,
            contract_id=conf.contract_id,
        ):
            return False
    return True


def touch_customer_view_if_needed(
    db: Session,
    *,
    confirmation_id: str,
    customer: Customer,
    actor_user_id: str,
    portal_login_email: str | None = None,
    commit: bool = True,
) -> ContractActivationConfirmation | None:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not portal_customer_can_access_activation_confirmation(
        db, customer=customer, conf=conf, portal_login_email=portal_login_email
    ):
        return None
    if conf.customer_viewed_at is not None:
        return conf
    if conf.status == "released":
        conf.status = "viewed"
    conf.customer_viewed_at = utc_now()
    db.add(conf)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_viewed",
        summary=f"Customer viewed activation confirmation {conf.confirmation_reference}",
        performed_by_user_id=actor_user_id,
        payload={"activation_confirmation_id": conf.id, "customer_id": customer.id},
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def acknowledge_by_customer(
    db: Session,
    *,
    confirmation_id: str,
    customer: Customer,
    portal_user_id: str,
    acknowledged_by_contact: str,
    acknowledgement_notes: str | None = None,
    portal_login_email: str | None = None,
    commit: bool = True,
) -> ContractActivationConfirmation:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not portal_customer_can_access_activation_confirmation(
        db, customer=customer, conf=conf, portal_login_email=portal_login_email
    ):
        raise ValueError("Confirmation not available")
    if conf.status not in ("released", "viewed", "acknowledged"):
        raise ValueError("Confirmation cannot be acknowledged in its current state")
    if conf.status == "acknowledged" and conf.customer_acknowledged_at:
        return conf

    now = utc_now()
    if conf.customer_viewed_at is None:
        conf.customer_viewed_at = now
        if conf.status == "released":
            conf.status = "viewed"
    conf.status = "acknowledged"
    conf.customer_acknowledged_at = now
    conf.customer_acknowledged_by_contact = acknowledged_by_contact.strip()[:255]
    conf.customer_acknowledgement_notes = (acknowledgement_notes or "").strip()[:4000] or None
    db.add(conf)
    _log_commercial(
        db,
        contract_id=conf.contract_id,
        review_id=None,
        action_type="activation_confirmation_acknowledged",
        summary=f"Customer acknowledged activation confirmation {conf.confirmation_reference}",
        performed_by_user_id=portal_user_id,
        payload={
            "activation_confirmation_id": conf.id,
            "customer_id": customer.id,
            "acknowledged_by_contact": conf.customer_acknowledged_by_contact,
        },
    )
    if commit:
        db.commit()
        db.refresh(conf)
    else:
        db.flush()
        db.refresh(conf)
    return conf


def list_confirmations_internal(
    db: Session,
    *,
    contract_id: str | None = None,
    amendment_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ContractActivationConfirmation]:
    q = db.query(ContractActivationConfirmation).order_by(ContractActivationConfirmation.created_at.desc())
    if contract_id:
        q = q.filter(ContractActivationConfirmation.contract_id == contract_id)
    if amendment_id:
        q = q.filter(ContractActivationConfirmation.amendment_id == amendment_id)
    if status:
        q = q.filter(ContractActivationConfirmation.status == status)
    return q.offset(offset).limit(limit).all()


def list_confirmations_for_portal_contract(
    db: Session, *, customer: Customer, contract_id: str, portal_login_email: str | None = None
) -> list[ContractActivationConfirmation]:
    if not can_customer_access_contract(
        db, customer=customer, contract_id=contract_id, portal_login_email=portal_login_email
    ):
        return []
    rows = (
        db.query(ContractActivationConfirmation)
        .filter(ContractActivationConfirmation.contract_id == contract_id)
        .order_by(ContractActivationConfirmation.created_at.desc())
        .all()
    )
    return [
        r
        for r in rows
        if portal_customer_can_access_activation_confirmation(
            db, customer=customer, conf=r, portal_login_email=portal_login_email
        )
    ]


def build_timeline_for_confirmation(
    db: Session, *, confirmation_id: str, contract_id: str
) -> list[dict[str, Any]]:
    rows = (
        db.query(ContractCommercialActionLog)
        .filter(ContractCommercialActionLog.contract_id == contract_id)
        .order_by(ContractCommercialActionLog.performed_at.asc())
        .all()
    )
    out: list[dict[str, Any]] = []
    wanted = {
        "activation_confirmation_created",
        "activation_confirmation_pdf_generated",
        "activation_confirmation_ready_for_customer",
        "activation_confirmation_released",
        "activation_confirmation_viewed",
        "activation_confirmation_acknowledged",
        "activation_confirmation_withdrawn",
    }
    for r in rows:
        if r.action_type not in wanted:
            continue
        p = _loads(r.payload_json) or {}
        if p.get("activation_confirmation_id") != confirmation_id:
            continue
        out.append(
            {
                "at": r.performed_at.isoformat() if r.performed_at else None,
                "event_type": r.action_type,
                "summary": r.action_summary,
            }
        )
    return out


def dashboard_activation_confirmations(db: Session) -> dict[str, Any]:
    q = db.query(ContractActivationConfirmation)
    rows = q.all()
    buckets = {
        "pending_generation": 0,
        "generated": 0,
        "ready_for_customer": 0,
        "released": 0,
        "viewed": 0,
        "acknowledged": 0,
        "withdrawn": 0,
        "superseded": 0,
    }
    for r in rows:
        if r.status in buckets:
            buckets[r.status] += 1
    return {"by_status": buckets, "total": len(rows)}


def dashboard_activations_awaiting_customer_confirmation(db: Session) -> dict[str, Any]:
    open_release = (
        db.query(ContractActivationConfirmation)
        .filter(ContractActivationConfirmation.status.in_(("generated", "ready_for_customer")))
        .order_by(ContractActivationConfirmation.created_at.asc())
        .all()
    )
    return {
        "generated_unreleased": [
            {
                "id": r.id,
                "confirmation_reference": r.confirmation_reference,
                "contract_id": r.contract_id,
                "amendment_id": r.amendment_id,
                "status": r.status,
            }
            for r in open_release
        ],
        "count": len(open_release),
    }


def dashboard_activation_customer_lifecycle(db: Session) -> dict[str, Any]:
    """
    Single view for §5.3 exit: internal + customer-facing activation confirmation state.
    Composes existing dashboard helpers without duplicating query logic.
    """
    fu = dashboard_activation_confirmations_follow_up(db)
    return {
        "by_status": dashboard_activation_confirmations(db),
        "awaiting_release_or_generation": dashboard_activations_awaiting_customer_confirmation(db),
        "follow_up_counts": {
            "released_not_viewed": len(fu["released_not_viewed"]),
            "viewed_not_acknowledged": len(fu["viewed_not_acknowledged"]),
            "withdrawn_confirmations": len(fu["withdrawn_confirmations"]),
            "activated_without_open_confirmation": len(fu["activated_without_open_confirmation"]),
        },
        "follow_up_samples": {
            "released_not_viewed_ids": fu["released_not_viewed"][:25],
            "viewed_not_acknowledged_ids": fu["viewed_not_acknowledged"][:25],
            "activated_without_open_confirmation": fu["activated_without_open_confirmation"][:25],
        },
    }


def dashboard_activation_confirmations_follow_up(db: Session) -> dict[str, Any]:
    released_unviewed = (
        db.query(ContractActivationConfirmation)
        .filter(
            ContractActivationConfirmation.status == "released",
            ContractActivationConfirmation.customer_viewed_at.is_(None),
        )
        .all()
    )
    viewed_unacked = (
        db.query(ContractActivationConfirmation)
        .filter(
            ContractActivationConfirmation.status == "viewed",
            ContractActivationConfirmation.customer_acknowledged_at.is_(None),
        )
        .all()
    )
    withdrawn = (
        db.query(ContractActivationConfirmation).filter(ContractActivationConfirmation.status == "withdrawn").all()
    )
    # Activated amendments with no non-terminal confirmation
    amendments = db.query(ContractAmendment).filter(ContractAmendment.status == "activated").all()
    missing: list[dict[str, str]] = []
    for a in amendments:
        has_open = (
            db.query(ContractActivationConfirmation)
            .filter(
                ContractActivationConfirmation.amendment_id == a.id,
                ContractActivationConfirmation.status.notin_(_TERMINAL_CONFIRMATION_STATUSES),
            )
            .first()
        )
        if not has_open:
            missing.append({"amendment_id": a.id, "contract_id": a.contract_id, "amendment_reference": a.amendment_reference})
    return {
        "released_not_viewed": [c.id for c in released_unviewed],
        "viewed_not_acknowledged": [c.id for c in viewed_unacked],
        "withdrawn_confirmations": [c.id for c in withdrawn],
        "activated_without_open_confirmation": missing,
    }


def resolve_stored_document_for_activation_confirmation(
    db: Session, *, confirmation_id: str
) -> StoredDocument | None:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not conf.stored_document_id:
        return None
    return db.get(StoredDocument, conf.stored_document_id)
