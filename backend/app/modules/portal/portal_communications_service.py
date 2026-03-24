"""Portal-scoped, customer-safe views of contract outbound communications."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.contracts.contract_customer_communication_delivery_models import (
    ContractCustomerCommunicationDelivery,
)
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer
from backend.app.modules.portal.portal_access_service import can_customer_access_contract
from backend.app.modules.portal.schemas import PortalCustomerCommunicationOut

_PORTAL_VISIBLE_STATUSES = ("sent", "failed", "cancelled")


def _mask_recipient(addr: str | None) -> str | None:
    if not addr or "@" not in addr:
        if addr and len(addr) > 6:
            return f"{addr[:3]}…"
        return addr
    local, _, domain = addr.partition("@")
    local = local.strip()
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[:2]}***@{domain}"


def _truncate_preview(text: str | None, max_chars: int) -> str | None:
    if not text:
        return None
    t = text.strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"


def _last_delivery(db: Session, *, communication_id: str) -> ContractCustomerCommunicationDelivery | None:
    return (
        db.query(ContractCustomerCommunicationDelivery)
        .filter(ContractCustomerCommunicationDelivery.communication_id == communication_id)
        .order_by(ContractCustomerCommunicationDelivery.started_at.desc())
        .first()
    )


def _row_to_out(
    db: Session,
    row: ContractCustomerCommunication,
    *,
    preview_chars: int,
) -> PortalCustomerCommunicationOut:
    delivery = _last_delivery(db, communication_id=row.id)
    recipient_src = delivery.recipient_address if delivery else row.recipient_contact_reference
    preview = None
    if row.status == "sent":
        preview = _truncate_preview(row.body_text, preview_chars) or _truncate_preview(row.subject, preview_chars)

    return PortalCustomerCommunicationOut(
        id=row.id,
        contract_id=row.contract_id,
        source_entity_type=row.source_entity_type,
        communication_type=row.communication_type,
        channel=row.channel,
        status=row.status,
        subject=row.subject,
        created_at=row.created_at,
        sent_at=row.sent_at,
        failed_at=row.failed_at,
        cancelled_at=row.cancelled_at,
        body_preview=preview,
        recipient_masked=_mask_recipient(recipient_src),
        last_delivery_status=delivery.status if delivery else None,
        last_delivery_completed_at=delivery.completed_at if delivery else None,
    )


def list_portal_customer_communications(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    limit: int = 30,
    preview_chars: int = 400,
) -> list[PortalCustomerCommunicationOut]:
    """Newest first; respects contract + portal group / site scoping."""
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    fetch = min(limit * 5, 500)
    rows = (
        db.query(ContractCustomerCommunication)
        .join(Contract, Contract.id == ContractCustomerCommunication.contract_id)
        .filter(Contract.customer_id == customer.id)
        .filter(ContractCustomerCommunication.status.in_(_PORTAL_VISIBLE_STATUSES))
        .order_by(ContractCustomerCommunication.created_at.desc())
        .limit(fetch)
        .all()
    )

    out: list[PortalCustomerCommunicationOut] = []
    for row in rows:
        if not can_customer_access_contract(
            db,
            customer=customer,
            contract_id=row.contract_id,
            portal_login_email=portal_login_email,
        ):
            continue
        out.append(_row_to_out(db, row, preview_chars=preview_chars))
        if len(out) >= limit:
            break
    return out


def get_portal_customer_communication(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    communication_id: str,
    preview_chars: int = 2000,
) -> PortalCustomerCommunicationOut | None:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row or row.status not in _PORTAL_VISIBLE_STATUSES:
        return None
    c = db.get(Contract, row.contract_id)
    if not c or c.customer_id != customer.id:
        return None
    if not can_customer_access_contract(
        db,
        customer=customer,
        contract_id=row.contract_id,
        portal_login_email=portal_login_email,
    ):
        return None
    return _row_to_out(db, row, preview_chars=preview_chars)
