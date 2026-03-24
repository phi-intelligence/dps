"""Certificate PDFs from captured truth only (no invented readings)."""
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
from backend.app.modules.assets.models import Asset
from backend.app.modules.auth.models import User
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job, JobFormSubmission
from backend.app.modules.sites.models import Site


def _utc_fmt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _short_json_value(val: object, max_len: int = 120) -> str:
    if val is None:
        return "—"
    if isinstance(val, (dict, list)):
        s = json.dumps(val, ensure_ascii=False, sort_keys=True)
    else:
        s = str(val)
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def render_certificate_pdf(db: Session, *, certificate: Certificate) -> bytes:
    job = db.get(Job, certificate.job_id)
    customer: Customer | None = db.get(Customer, job.customer_id) if job and job.customer_id else None
    site: Site | None = db.get(Site, certificate.site_id) if certificate.site_id else None
    asset: Asset | None = db.get(Asset, certificate.asset_id) if certificate.asset_id else None
    engineer: User | None = (
        db.get(User, certificate.engineer_user_id) if certificate.engineer_user_id else None
    )

    submissions = (
        db.query(JobFormSubmission)
        .filter(JobFormSubmission.job_id == certificate.job_id)
        .order_by(JobFormSubmission.submitted_at.asc())
        .all()
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Certificate {certificate.id}",
        pageCompression=0,
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
    story.append(Paragraph("<b>Compliance certificate</b>", h2))

    story.append(Paragraph(f"<b>Certificate identifier:</b> {certificate.id}", body))
    story.append(Paragraph(f"<b>Certificate type:</b> {certificate.certificate_type}", body))
    story.append(Paragraph(f"<b>Status:</b> {certificate.status}", body))
    story.append(Paragraph(f"<b>Issue date:</b> {_utc_fmt(certificate.created_at)}", body))

    if job:
        story.append(Paragraph(f"<b>Job reference:</b> {job.id}", body))
        story.append(
            Paragraph(f"<b>Work address:</b> {job.address.replace('&', '&amp;')}", body)
        )
    else:
        story.append(Paragraph("<b>Job reference:</b> —", body))

    cust_name = customer.name if customer else "—"
    story.append(Paragraph(f"<b>Customer:</b> {cust_name.replace('&', '&amp;')}", body))

    if site:
        line = ", ".join(
            x.replace("&", "&amp;")
            for x in [site.name, site.address_line1, site.postcode or ""]  # type: ignore[union-attr]
            if x
        )
        story.append(Paragraph(f"<b>Site:</b> {line}", body))
    else:
        story.append(Paragraph("<b>Site:</b> Not linked on certificate record", body))

    if asset:
        story.append(
            Paragraph(
                f"<b>Asset:</b> {asset.name.replace('&', '&amp;')} ({asset.asset_type}) "
                f"— code {asset.asset_code or 'n/a'}",
                body,
            )
        )
    else:
        story.append(Paragraph("<b>Asset:</b> Not linked on certificate record", body))

    if certificate.contract_id:
        story.append(Paragraph(f"<b>Contract reference:</b> {certificate.contract_id}", body))

    if engineer:
        story.append(
            Paragraph(
                f"<b>Responsible engineer (assigned):</b> {engineer.email.replace('&', '&amp;')}",
                body,
            )
        )
    else:
        story.append(Paragraph("<b>Responsible engineer (assigned):</b> —", body))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Signatures</b>", h2))
    story.append(
        Paragraph(
            f"Engineer signed (recorded in system): <b>{'yes' if certificate.signed_by_engineer else 'no'}</b>",
            body,
        )
    )
    story.append(
        Paragraph(
            f"Customer signed (recorded in system): <b>{'yes' if certificate.signed_by_client else 'no'}</b>",
            body,
        )
    )
    story.append(
        Paragraph(
            "<i>Physical signature capture, if used, is stored separately; placeholders apply until integrated.</i>",
            small,
        )
    )

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>Captured field data (job forms)</b>", h2))
    if not submissions:
        story.append(
            Paragraph(
                "No job form submissions were present at PDF generation time.",
                body,
            )
        )
    else:
        for sub in submissions:
            story.append(
                Paragraph(
                    f"<b>Form:</b> {sub.form_key} &nbsp; <b>Submitted:</b> {_utc_fmt(sub.submitted_at)}",
                    body,
                )
            )
            try:
                payload = json.loads(sub.data_json or "{}")
            except json.JSONDecodeError:
                payload = {"_raw": sub.data_json[:500] if sub.data_json else ""}
            if not isinstance(payload, dict):
                story.append(Paragraph(_short_json_value(payload), body))
                continue
            rows = [["Field", "Value"]]
            for k in sorted(payload.keys(), key=lambda x: str(x).lower())[:40]:
                rows.append([str(k), _short_json_value(payload[k])])
            if len(payload) > 40:
                rows.append(["…", f"{len(payload) - 40} additional keys omitted"])
            tbl = Table(rows, colWidths=[4.5 * cm, 10.5 * cm])
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ]
                )
            )
            story.append(tbl)
            story.append(Spacer(1, 0.15 * cm))

    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"<i>Document generated at {gen_ts} (system clock).</i>", small))
    story.append(
        Paragraph(
            f"<i>Machine tag: phi-dps-certificate-docid-{certificate.id}</i>",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()
