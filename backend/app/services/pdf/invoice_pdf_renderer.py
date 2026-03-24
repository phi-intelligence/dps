"""Deterministic, business-usable invoice PDFs from captured platform data only."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.sites.models import Site


def _utc_fmt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_invoice_pdf(db: Session, *, invoice: Invoice) -> bytes:
    job = db.get(Job, invoice.job_id)
    customer: Customer | None = db.get(Customer, job.customer_id) if job and job.customer_id else None
    site: Site | None = db.get(Site, job.site_id) if job and job.site_id else None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Invoice {invoice.id}",
        pageCompression=0,  # stable, auditable streams; aids integrity checks / tests
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=12, spaceAfter=8)
    small = ParagraphStyle(name="S", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    body = ParagraphStyle(name="B", parent=styles["Normal"], fontSize=10, spaceAfter=6)

    story: list[Any] = []
    story.append(Paragraph(settings.PHI_DPS_COMPANY_NAME.replace("&", "&amp;"), h1))
    story.append(Paragraph(settings.PHI_DPS_COMPANY_TAGLINE.replace("&", "&amp;"), body))
    addr = (settings.PHI_DPS_COMPANY_ADDRESS or "").replace("&", "&amp;")
    if addr:
        story.append(Paragraph(addr.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("<b>Tax invoice</b>", h2))

    cust_name = customer.name if customer else "—"
    story.append(Paragraph(f"<b>Invoice reference:</b> {invoice.id}", body))
    story.append(Paragraph(f"<b>Invoice date:</b> {_utc_fmt(invoice.created_at)}", body))
    story.append(Paragraph(f"<b>Customer:</b> {cust_name.replace('&', '&amp;')}", body))

    if job:
        story.append(Paragraph(f"<b>Job reference:</b> {job.id}", body))
        story.append(
            Paragraph(f"<b>Work address / site context:</b> {job.address.replace('&', '&amp;')}", body)
        )
    else:
        story.append(Paragraph("<b>Job reference:</b> —", body))

    if site:
        parts = [site.name, site.address_line1]
        if site.address_line2:
            parts.append(site.address_line2)
        if site.city:
            parts.append(site.city)
        if site.postcode:
            parts.append(site.postcode)
        story.append(
            Paragraph(
                "<b>Registered site:</b> " + ", ".join(p.replace("&", "&amp;") for p in parts if p),
                body,
            )
        )

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Line items</b>", h2))

    labour = f"{invoice.currency} {invoice.labour_total:.2f}"
    materials = f"{invoice.currency} {invoice.materials_total:.2f}"
    data = [
        ["Description", "Amount"],
        ["Labour (incl. travel where applicable)", labour],
        ["Materials (customer charge)", materials],
        ["", ""],
        ["Subtotal (labour + materials)", f"{invoice.currency} {invoice.grand_total:.2f}"],
    ]
    t = Table(data, colWidths=[10 * cm, 5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -2), 0.25, colors.grey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    pay = invoice.status or "unknown"
    story.append(Paragraph(f"<b>Payment status:</b> {pay}", body))
    if invoice.paid_at:
        story.append(Paragraph(f"<b>Paid at:</b> {_utc_fmt(invoice.paid_at)}", body))

    if invoice.cost_basis_notes:
        notes = invoice.cost_basis_notes.replace("&", "&amp;").replace("\n", "<br/>")
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("<b>Notes / costing context</b>", h2))
        story.append(Paragraph(notes[:8000], body))

    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<i>Document generated at {gen_ts} (system clock).</i>", small))
    story.append(
        Paragraph(
            f"<i>Machine tag: phi-dps-invoice-docid-{invoice.id}</i>",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()
