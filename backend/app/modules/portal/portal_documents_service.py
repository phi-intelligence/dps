from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.crm.models import Customer
from backend.app.modules.documents.models import StoredDocument
from backend.app.modules.documents.service import portal_customer_may_see_metadata
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.portal.portal_access_service import can_customer_access_asset, portal_job_ids


def _latest_stored_certificate_map(db: Session, cert_ids: list[str]) -> dict[str, str]:
    if not cert_ids:
        return {}
    rows = (
        db.query(StoredDocument)
        .filter(StoredDocument.related_certificate_id.in_(cert_ids))
        .order_by(StoredDocument.created_at.desc())
        .all()
    )
    out: dict[str, str] = {}
    for r in rows:
        cid = r.related_certificate_id
        if cid and cid not in out:
            out[cid] = r.id
    return out


def _latest_stored_invoice_map(db: Session, inv_ids: list[str]) -> dict[str, str]:
    if not inv_ids:
        return {}
    rows = (
        db.query(StoredDocument)
        .filter(StoredDocument.related_invoice_id.in_(inv_ids))
        .order_by(StoredDocument.created_at.desc())
        .all()
    )
    out: dict[str, str] = {}
    for r in rows:
        iid = r.related_invoice_id
        if iid and iid not in out:
            out[iid] = r.id
    return out


def list_unified_portal_documents(db: Session, *, customer: Customer) -> list[dict[str, Any]]:
    job_ids = portal_job_ids(db, customer=customer)
    items: list[dict[str, Any]] = []

    if not job_ids:
        return []

    certs = (
        db.query(Certificate).filter(Certificate.job_id.in_(job_ids)).order_by(Certificate.created_at.desc()).all()
    )
    cert_map = _latest_stored_certificate_map(db, [c.id for c in certs])
    for c in certs:
        items.append(
            {
                "document_type": "certificate",
                "id": c.id,
                "title": f"{c.certificate_type.upper()} certificate",
                "related_job_id": c.job_id,
                "related_site_id": c.site_id,
                "related_asset_id": c.asset_id,
                "issue_date": c.created_at,
                "status": c.status,
                "retrieval_path": f"/portal/me/certificates/{c.id}",
                "stored_document_id": cert_map.get(c.id),
            }
        )

    invs = db.query(Invoice).filter(Invoice.job_id.in_(job_ids)).order_by(Invoice.created_at.desc()).all()
    inv_map = _latest_stored_invoice_map(db, [i.id for i in invs])
    for inv in invs:
        items.append(
            {
                "document_type": "invoice",
                "id": inv.id,
                "title": f"Invoice {inv.id[:8]}… ({inv.currency} {inv.grand_total:.2f})",
                "related_job_id": inv.job_id,
                "related_site_id": None,
                "related_asset_id": None,
                "issue_date": inv.created_at,
                "status": inv.status,
                "retrieval_path": f"/portal/me/invoices/{inv.id}",
                "stored_document_id": inv_map.get(inv.id),
            }
        )

    # Standalone stored documents (reports, future packs) — exclude cert/invoice rows already surfaced above.
    for d in (
        db.query(StoredDocument)
        .filter(StoredDocument.related_job_id.in_(job_ids))
        .order_by(StoredDocument.created_at.desc())
        .all()
    ):
        if d.visibility_scope == "internal_only":
            continue
        if not portal_customer_may_see_metadata(db, customer=customer, doc=d):
            continue
        if d.related_certificate_id or d.related_invoice_id:
            continue
        items.append(
            {
                "document_type": d.document_type,
                "id": d.id,
                "title": d.filename,
                "related_job_id": d.related_job_id,
                "related_site_id": d.related_site_id,
                "related_asset_id": d.related_asset_id,
                "issue_date": d.created_at,
                "status": d.status,
                "retrieval_path": f"/portal/me/documents/{d.id}",
                "stored_document_id": d.id,
            }
        )

    items.sort(key=lambda x: x["issue_date"], reverse=True)
    return items


def list_asset_documents_for_portal(db: Session, *, customer: Customer, asset_id: str) -> list[dict[str, Any]]:
    if not can_customer_access_asset(db, customer=customer, asset_id=asset_id):
        return []
    rows = (
        db.query(Certificate)
        .filter(Certificate.asset_id == asset_id)
        .order_by(Certificate.created_at.desc())
        .all()
    )
    cert_map = _latest_stored_certificate_map(db, [c.id for c in rows])
    return [
        {
            "document_type": "certificate",
            "id": c.id,
            "title": f"{c.certificate_type.upper()} certificate",
            "related_job_id": c.job_id,
            "related_site_id": c.site_id,
            "related_asset_id": c.asset_id,
            "issue_date": c.created_at,
            "status": c.status,
            "retrieval_path": f"/portal/me/certificates/{c.id}",
            "stored_document_id": cert_map.get(c.id),
        }
        for c in rows
    ]


def get_certificate_for_portal(
    db: Session, *, customer: Customer, certificate_id: str
) -> Certificate | None:
    job_ids = portal_job_ids(db, customer=customer)
    c = db.get(Certificate, certificate_id)
    if not c or c.job_id not in job_ids:
        return None
    return c
