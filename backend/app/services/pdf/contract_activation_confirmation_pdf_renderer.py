"""Customer-safe contract activation confirmation PDF (no internal margin / profitability signals)."""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_fmt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _esc(s: str | None) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def render_contract_activation_confirmation_pdf(
    db: Session, *, confirmation: ContractActivationConfirmation
) -> bytes:
    contract = db.get(Contract, confirmation.contract_id)
    customer: Customer | None = db.get(Customer, contract.customer_id) if contract else None
    summary = _loads(confirmation.summary_json) or {}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Activation confirmation {confirmation.confirmation_reference}",
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    body = ParagraphStyle(name="B", parent=styles["Normal"], fontSize=10, spaceAfter=6)
    small = ParagraphStyle(name="S", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story: list[Any] = []
    story.append(Paragraph(_esc(settings.PHI_DPS_COMPANY_NAME), h1))
    if settings.PHI_DPS_COMPANY_TAGLINE:
        story.append(Paragraph(_esc(settings.PHI_DPS_COMPANY_TAGLINE), body))
    addr = (settings.PHI_DPS_COMPANY_ADDRESS or "").replace("&", "&amp;")
    if addr:
        story.append(Paragraph(addr.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("<b>Contract activation confirmation</b>", h2))
    story.append(Paragraph(f"<b>Confirmation reference:</b> {_esc(confirmation.confirmation_reference)}", body))
    story.append(Paragraph(f"<b>Generated:</b> {_utc_fmt(utc_now())}", body))
    story.append(Spacer(1, 0.2 * cm))

    if contract:
        story.append(Paragraph(f"<b>Contract:</b> {_esc(contract.name)} ({_esc(contract.contract_code)})", body))
    if customer:
        story.append(Paragraph(f"<b>Customer:</b> {_esc(customer.name)}", body))
    story.append(Paragraph(f"<b>Effective date:</b> {_utc_fmt(confirmation.effective_date)}", body))
    story.append(Paragraph(f"<b>Activated (internal record):</b> {_utc_fmt(confirmation.activated_at)}", body))
    story.append(Spacer(1, 0.3 * cm))

    headline = summary.get("headline") if isinstance(summary, dict) else None
    if headline:
        story.append(Paragraph(_esc(str(headline)), h2))
    lines = summary.get("body_lines") if isinstance(summary, dict) else None
    if isinstance(lines, list):
        for ln in lines:
            story.append(Paragraph(f"• {_esc(str(ln))}", body))
    else:
        story.append(Paragraph("Your contract has been updated as agreed.", body))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Commercial summary (customer view)</b>", h2))
    prior = summary.get("prior_contract_value") if isinstance(summary, dict) else None
    newv = summary.get("new_contract_value") if isinstance(summary, dict) else None
    rows = [["Item", "Before activation", "After activation"]]
    if prior is not None and newv is not None:
        rows.append(["Contract value (basis agreed with you)", f"{prior:,.2f}", f"{newv:,.2f}"])
    else:
        rows.append(["Contract value", "As per prior agreement", "As per your approved change"])
    t = Table(rows, colWidths=[6 * cm, 4.5 * cm, 4.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "This document confirms that the commercial change referenced above is now reflected in your live contract. "
            "It is not a new offer unless separately issued.",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()
