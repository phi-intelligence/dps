"""Formal repricing / commercial proposal PDF (internal-ready; not auto-sent to customers)."""
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
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import ContractRepricingProposal, ContractRepricingProposalLine
from backend.app.modules.crm.models import Customer


def _utc_fmt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _esc(s: str | None) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


def render_repricing_proposal_pdf(
    db: Session, *, proposal: ContractRepricingProposal, lines: list[ContractRepricingProposalLine]
) -> bytes:
    contract = db.get(Contract, proposal.contract_id)
    customer: Customer | None = db.get(Customer, contract.customer_id) if contract else None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Repricing proposal {proposal.proposal_reference}",
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    small = ParagraphStyle(name="S", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    body = ParagraphStyle(name="B", parent=styles["Normal"], fontSize=10, spaceAfter=6)

    story: list[Any] = []
    story.append(Paragraph(_esc(settings.PHI_DPS_COMPANY_NAME), h1))
    story.append(Paragraph(_esc(settings.PHI_DPS_COMPANY_TAGLINE or ""), body))
    addr = (settings.PHI_DPS_COMPANY_ADDRESS or "").replace("&", "&amp;")
    if addr:
        story.append(Paragraph(addr.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("<b>Commercial repricing proposal</b>", h2))
    story.append(Paragraph(f"<b>Status:</b> {_esc(proposal.proposal_status)}", body))
    story.append(Paragraph(f"<b>Proposal reference:</b> {_esc(proposal.proposal_reference)}", body))
    story.append(Paragraph(f"<b>Generated:</b> {_utc_fmt(proposal.generated_at)}", body))
    story.append(Spacer(1, 0.2 * cm))

    if contract:
        story.append(Paragraph(f"<b>Contract:</b> {_esc(contract.name)} ({_esc(contract.contract_code)})", body))
    if customer:
        story.append(Paragraph(f"<b>Customer:</b> {_esc(customer.name)}", body))
    story.append(Paragraph(f"<b>Repricing review id:</b> {_esc(proposal.repricing_review_id)}", body))
    story.append(Spacer(1, 0.3 * cm))

    cur = proposal.current_contract_value
    prop = proposal.proposed_contract_value
    story.append(Paragraph("<b>Current vs proposed (summary)</b>", h2))
    story.append(
        Paragraph(
            f"<b>Current contract value (basis):</b> {proposal.currency} {cur:.2f}" if cur is not None else "<b>Current contract value:</b> —",
            body,
        )
    )
    story.append(
        Paragraph(
            f"<b>Proposed contract value:</b> {proposal.currency} {prop:.2f}" if prop is not None else "<b>Proposed contract value:</b> — (see lines / internal review)",
            body,
        )
    )

    try:
        ch = json.loads(proposal.change_summary_json or "{}")
        if isinstance(ch, dict) and ch.get("warnings"):
            w = ", ".join(str(x) for x in ch["warnings"])
            story.append(Paragraph(f"<b>Basis warnings:</b> {_esc(w)}", body))
    except json.JSONDecodeError:
        pass

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Proposal lines</b>", h2))

    data: list[list[str]] = [
        ["Type", "Title", "Qty", "Unit", "Current", "Proposed", "Variance"],
    ]
    for ln in sorted(lines, key=lambda x: (x.sort_order, x.created_at)):
        data.append(
            [
                _esc(ln.line_type)[:24],
                _esc(ln.title)[:40],
                f"{ln.quantity:g}",
                _esc(ln.unit),
                f"{proposal.currency} {ln.current_line_total:.2f}" if ln.current_line_total is not None else "—",
                f"{proposal.currency} {ln.proposed_line_total:.2f}",
                f"{proposal.currency} {ln.variance_amount:.2f}" if ln.variance_amount is not None else "—",
            ]
        )
    t = Table(data, colWidths=[2.6 * cm, 4.2 * cm, 1.2 * cm, 1.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "<i>This document is for internal commercial use unless explicitly marked ready for customer. "
            "It does not amend the live contract until a separate acceptance process is completed.</i>",
            small,
        )
    )
    doc.build(story)
    return buf.getvalue()
