from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.modules.crm.customer_communication_preference_models import CustomerCommunicationPreference
from backend.app.modules.crm.models import Customer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def list_preferences_for_customer(db: Session, *, customer_id: str) -> list[CustomerCommunicationPreference]:
    if not db.get(Customer, customer_id):
        raise ValueError("Customer not found")
    return (
        db.query(CustomerCommunicationPreference)
        .filter(CustomerCommunicationPreference.customer_id == customer_id)
        .order_by(CustomerCommunicationPreference.channel, CustomerCommunicationPreference.contact_reference)
        .all()
    )


def create_preference(
    db: Session,
    *,
    customer_id: str,
    channel: str,
    enabled: bool,
    contact_reference: str | None,
    preferred: bool,
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
    timezone_name: str | None,
    notes: str | None,
    commit: bool = True,
) -> CustomerCommunicationPreference:
    if not db.get(Customer, customer_id):
        raise ValueError("Customer not found")
    row = CustomerCommunicationPreference(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        channel=channel,
        enabled=enabled,
        contact_reference=contact_reference,
        preferred=preferred,
        quiet_hours_start=quiet_hours_start,
        quiet_hours_end=quiet_hours_end,
        timezone_name=timezone_name,
        notes=notes,
        updated_at=utc_now(),
    )
    db.add(row)
    try:
        if commit:
            db.commit()
            db.refresh(row)
        else:
            db.flush()
            db.refresh(row)
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Preference already exists for this customer/channel/contact combination") from e
    return row


def disable_email_address_from_provider_event(
    db: Session,
    *,
    customer_id: str,
    email: str,
    audit_note: str,
    commit: bool = True,
) -> CustomerCommunicationPreference | None:
    """
    Disable a specific email address for outbound (per-address preference row).
    Used for provider unsubscribe / spam complaints per product policy.
    """
    if not db.get(Customer, customer_id):
        raise ValueError("Customer not found")
    norm = (email or "").strip().lower()
    if not norm:
        return None
    row = (
        db.query(CustomerCommunicationPreference)
        .filter(
            CustomerCommunicationPreference.customer_id == customer_id,
            CustomerCommunicationPreference.channel == "email",
            CustomerCommunicationPreference.contact_reference == norm,
        )
        .first()
    )
    now = utc_now()
    if row:
        row.enabled = False
        row.notes = (row.notes + "\n" if row.notes else "") + audit_note
        row.updated_at = now
        db.add(row)
    else:
        row = CustomerCommunicationPreference(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            channel="email",
            enabled=False,
            contact_reference=norm,
            preferred=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
            timezone_name=None,
            notes=audit_note,
            updated_at=now,
        )
        db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def patch_preference(
    db: Session,
    *,
    preference_id: str,
    enabled: bool | None,
    contact_reference: str | None,
    preferred: bool | None,
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
    timezone_name: str | None,
    notes: str | None,
    commit: bool = True,
) -> CustomerCommunicationPreference:
    row = db.get(CustomerCommunicationPreference, preference_id)
    if not row:
        raise ValueError("Preference not found")
    if enabled is not None:
        row.enabled = enabled
    if contact_reference is not None:
        row.contact_reference = contact_reference
    if preferred is not None:
        row.preferred = preferred
    if quiet_hours_start is not None:
        row.quiet_hours_start = quiet_hours_start
    if quiet_hours_end is not None:
        row.quiet_hours_end = quiet_hours_end
    if timezone_name is not None:
        row.timezone_name = timezone_name
    if notes is not None:
        row.notes = notes
    row.updated_at = utc_now()
    db.add(row)
    try:
        if commit:
            db.commit()
            db.refresh(row)
        else:
            db.flush()
            db.refresh(row)
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Update violates unique constraint") from e
    return row
