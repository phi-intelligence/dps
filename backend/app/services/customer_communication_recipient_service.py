"""
Resolve outbound recipients and evaluate customer communication preferences.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.customer_communication_preference_models import CustomerCommunicationPreference
from backend.app.modules.crm.models import Customer


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _compact_phone_digits(s: str) -> str:
    t = (s or "").strip()
    t = re.sub(r"[\s().-]", "", t)
    if t.startswith("+"):
        return "+" + "".join(c for c in t[1:] if c.isdigit())
    return "".join(c for c in t if c.isdigit())


def _valid_sms_number(s: str) -> bool:
    c = _compact_phone_digits(s)
    if c.startswith("+"):
        d = c[1:]
        return 8 <= len(d) <= 15 and d.isdigit()
    return 10 <= len(c) <= 15 and c.isdigit()


def _parse_hhmm(s: str | None) -> tuple[int, int] | None:
    if not s or s.count(":") != 1:
        return None
    a, b = s.split(":", 1)
    try:
        h, m = int(a), int(b)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except ValueError:
        return None
    return None


def _minutes_since_midnight(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _quiet_hours_warning_for_prefs(
    prefs: list[CustomerCommunicationPreference], now_utc: datetime, *, channel: str
) -> str | None:
    """Best-effort quiet-hours hint; does not block send in this slice."""
    for pr in prefs:
        if pr.channel != channel:
            continue
        if not pr.quiet_hours_start or not pr.quiet_hours_end:
            continue
        sh = _parse_hhmm(pr.quiet_hours_start)
        eh = _parse_hhmm(pr.quiet_hours_end)
        if not sh or not eh:
            continue
        tz_name = pr.timezone_name or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        local = now_utc.astimezone(tz)
        cur = _minutes_since_midnight(local)
        qs = sh[0] * 60 + sh[1]
        qe = eh[0] * 60 + eh[1]
        in_window = cur >= qs and cur <= qe if qs <= qe else cur >= qs or cur <= qe
        if in_window:
            return (
                f"Quiet hours active for customer ({pr.quiet_hours_start}-{pr.quiet_hours_end} {tz_name}); "
                "send proceeded per policy."
            )
    return None


@dataclass
class RecipientResolution:
    allowed: bool
    recipient_email: str | None = None
    recipient_phone: str | None = None
    block_reason: str | None = None
    quiet_hours_warning: str | None = None
    resolution_notes: dict[str, Any] | None = None


def resolve_customer_communication_recipients(
    db: Session,
    *,
    communication: ContractCustomerCommunication,
    now_utc: datetime | None = None,
) -> RecipientResolution:
    """
    Determine To address for email or SMS and whether preferences allow send.

    Email rules:
    - Global email disabled (row channel=email, contact_reference NULL, enabled=False) → block.
    - Explicit recipient_contact_reference on communication → use if valid email (unless globally disabled).
    - Else preferred preference row (preferred=True, enabled, contact_reference set) → that address.
    - Else customer.email from CRM.

    SMS rules: same shape using channel=sms preferences and customer.phone.
    """
    now = now_utc or datetime.now(timezone.utc)
    notes: dict[str, Any] = {}

    ch = (communication.channel or "").strip().lower()
    if ch not in ("email", "sms"):
        return RecipientResolution(
            allowed=False,
            block_reason="Recipient resolution applies to email and sms channels only",
            resolution_notes=notes,
        )

    cust_id = communication.recipient_customer_id
    if not cust_id:
        ctr = db.get(Contract, communication.contract_id)
        if ctr:
            cust_id = ctr.customer_id
    if not cust_id:
        return RecipientResolution(
            allowed=False,
            recipient_email=None,
            block_reason="No customer context for communication",
            resolution_notes=notes,
        )

    customer = db.get(Customer, cust_id)
    if not customer:
        return RecipientResolution(
            allowed=False,
            recipient_email=None,
            block_reason="Customer not found",
            resolution_notes=notes,
        )

    prefs = (
        db.query(CustomerCommunicationPreference)
        .filter(
            CustomerCommunicationPreference.customer_id == cust_id,
            CustomerCommunicationPreference.channel == ch,
        )
        .all()
    )

    global_disabled = any(p.contact_reference is None and not p.enabled for p in prefs)
    if global_disabled:
        return RecipientResolution(
            allowed=False,
            block_reason=(
                "Customer email channel disabled by communication preference"
                if ch == "email"
                else "Customer SMS channel disabled by communication preference"
            ),
            resolution_notes={**notes, "preference": f"global_{ch}_disabled"},
        )

    quiet_warn = _quiet_hours_warning_for_prefs(prefs, now, channel=ch)

    explicit = (communication.recipient_contact_reference or "").strip()
    if explicit:
        if ch == "email":
            if not _EMAIL_RE.match(explicit):
                return RecipientResolution(
                    allowed=False,
                    block_reason="recipient_contact_reference is not a valid email address",
                    resolution_notes=notes,
                )
            per_addr_off = any(
                p.contact_reference and p.contact_reference.lower() == explicit.lower() and not p.enabled
                for p in prefs
            )
            if per_addr_off:
                return RecipientResolution(
                    allowed=False,
                    block_reason="Target address disabled by customer communication preference",
                    resolution_notes={**notes, "address": explicit},
                )
            return RecipientResolution(
                allowed=True,
                recipient_email=explicit,
                quiet_hours_warning=quiet_warn,
                resolution_notes={**notes, "source": "communication.recipient_contact_reference"},
            )
        if not _valid_sms_number(explicit):
            return RecipientResolution(
                allowed=False,
                block_reason="recipient_contact_reference is not a valid phone number for SMS",
                resolution_notes=notes,
            )
        per_addr_off = any(
            p.contact_reference
            and _compact_phone_digits(p.contact_reference) == _compact_phone_digits(explicit)
            and not p.enabled
            for p in prefs
        )
        if per_addr_off:
            return RecipientResolution(
                allowed=False,
                block_reason="Target number disabled by customer communication preference",
                resolution_notes={**notes, "address": explicit},
            )
        return RecipientResolution(
            allowed=True,
            recipient_phone=_compact_phone_digits(explicit),
            quiet_hours_warning=quiet_warn,
            resolution_notes={**notes, "source": "communication.recipient_contact_reference"},
        )

    preferred_rows = [p for p in prefs if p.preferred and p.enabled and p.contact_reference]
    if preferred_rows:
        addr = preferred_rows[0].contact_reference.strip()
        if ch == "email":
            if _EMAIL_RE.match(addr):
                return RecipientResolution(
                    allowed=True,
                    recipient_email=addr,
                    quiet_hours_warning=quiet_warn,
                    resolution_notes={**notes, "source": "preference.preferred"},
                )
            return RecipientResolution(
                allowed=False,
                block_reason="Preferred communication preference has invalid email",
                resolution_notes=notes,
            )
        if _valid_sms_number(addr):
            return RecipientResolution(
                allowed=True,
                recipient_phone=_compact_phone_digits(addr),
                quiet_hours_warning=quiet_warn,
                resolution_notes={**notes, "source": "preference.preferred"},
            )
        return RecipientResolution(
            allowed=False,
            block_reason="Preferred communication preference has invalid phone number",
            resolution_notes=notes,
        )

    if ch == "email":
        default_email = (customer.email or "").strip()
        if not default_email:
            return RecipientResolution(
                allowed=False,
                block_reason="Customer has no email and no explicit recipient",
                resolution_notes=notes,
            )
        if not _EMAIL_RE.match(default_email):
            return RecipientResolution(
                allowed=False,
                block_reason="Customer email on file is not a valid address",
                resolution_notes=notes,
            )

        return RecipientResolution(
            allowed=True,
            recipient_email=default_email,
            quiet_hours_warning=quiet_warn,
            resolution_notes={**notes, "source": "customer.email"},
        )

    default_phone = (customer.phone or "").strip()
    if not default_phone or not _valid_sms_number(default_phone):
        return RecipientResolution(
            allowed=False,
            block_reason="Customer has no usable phone and no explicit SMS recipient",
            resolution_notes=notes,
        )

    return RecipientResolution(
        allowed=True,
        recipient_phone=_compact_phone_digits(default_phone),
        quiet_hours_warning=quiet_warn,
        resolution_notes={**notes, "source": "customer.phone"},
    )
