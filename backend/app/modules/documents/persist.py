"""Create StoredDocument rows + binaries for generated entities."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.dispatch.models import Job
from backend.app.modules.documents.models import StoredDocument
from backend.app.modules.invoicing.models import Invoice
from backend.app.services import document_storage_service as doc_store
from backend.app.modules.contracts.review_models import ContractRepricingProposal, ContractRepricingProposalLine
from backend.app.services.pdf.certificate_pdf_renderer import render_certificate_pdf
from backend.app.services.pdf.invoice_pdf_renderer import render_invoice_pdf
from backend.app.services.pdf.repricing_proposal_pdf_renderer import render_repricing_proposal_pdf
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.models import Contract
from backend.app.services.pdf.contract_activation_confirmation_pdf_renderer import (
    render_contract_activation_confirmation_pdf,
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _latest_related_document_id(
    db: Session, *, certificate_id: str | None, invoice_id: str | None
) -> str | None:
    q = db.query(StoredDocument)
    if certificate_id:
        q = q.filter(StoredDocument.related_certificate_id == certificate_id)
    elif invoice_id:
        q = q.filter(StoredDocument.related_invoice_id == invoice_id)
    else:
        return None
    prev = q.order_by(StoredDocument.created_at.desc()).first()
    return prev.id if prev else None


def persist_generated_certificate_document(
    db: Session,
    *,
    certificate: Certificate,
    uploaded_by_user_id: str | None,
    commit: bool = True,
) -> StoredDocument | None:
    return _persist_certificate_pdf(
        db,
        certificate=certificate,
        uploaded_by_user_id=uploaded_by_user_id,
        commit=commit,
        force_new=False,
    )


def regenerate_certificate_document(
    db: Session,
    *,
    certificate_id: str,
    uploaded_by_user_id: str | None,
) -> StoredDocument:
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise ValueError("Certificate not found")
    row = _persist_certificate_pdf(
        db,
        certificate=cert,
        uploaded_by_user_id=uploaded_by_user_id,
        commit=True,
        force_new=True,
    )
    assert row is not None
    return row


def _persist_certificate_pdf(
    db: Session,
    *,
    certificate: Certificate,
    uploaded_by_user_id: str | None,
    commit: bool,
    force_new: bool,
) -> StoredDocument | None:
    if not force_new:
        existing = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_certificate_id == certificate.id)
            .order_by(StoredDocument.created_at.desc())
            .first()
        )
        if existing:
            return existing

    prior_id = (
        _latest_related_document_id(db, certificate_id=certificate.id, invoice_id=None)
        if force_new
        else None
    )

    fn = f"certificate-{certificate.id}.pdf"
    key = doc_store.build_storage_key(
        document_type="certificate", document_id=certificate.id, filename_safe=fn
    )
    data = render_certificate_pdf(db, certificate=certificate)
    chk = doc_store.sha256_hex(data)
    doc_store.save_binary(storage_key=key, data=data)

    meta = {
        "renderer": "certificate_pdf_reportlab_v1",
        "certificate_id": certificate.id,
        "generated_at": _iso_now(),
        "regenerated": force_new,
        "prior_stored_document_id": prior_id,
    }
    row = StoredDocument(
        document_type="certificate",
        filename=fn,
        content_type="application/pdf",
        size_bytes=len(data),
        storage_key=key,
        storage_provider=doc_store.get_storage_provider_name(),
        checksum_sha256=chk,
        related_job_id=certificate.job_id,
        related_site_id=certificate.site_id,
        related_asset_id=certificate.asset_id,
        related_contract_id=certificate.contract_id,
        related_certificate_id=certificate.id,
        uploaded_by_user_id=uploaded_by_user_id,
        source_type="generated",
        visibility_scope="customer_safe",
        status="ready",
        metadata_json=json.dumps(meta, separators=(",", ":")),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def persist_generated_invoice_document(
    db: Session,
    *,
    invoice: Invoice,
    uploaded_by_user_id: str | None,
    commit: bool = True,
) -> StoredDocument | None:
    return _persist_invoice_pdf(
        db,
        invoice=invoice,
        uploaded_by_user_id=uploaded_by_user_id,
        commit=commit,
        force_new=False,
    )


def regenerate_invoice_document(
    db: Session,
    *,
    invoice_id: str,
    uploaded_by_user_id: str | None,
) -> StoredDocument:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise ValueError("Invoice not found")
    row = _persist_invoice_pdf(
        db,
        invoice=inv,
        uploaded_by_user_id=uploaded_by_user_id,
        commit=True,
        force_new=True,
    )
    assert row is not None
    return row


def _persist_invoice_pdf(
    db: Session,
    *,
    invoice: Invoice,
    uploaded_by_user_id: str | None,
    commit: bool,
    force_new: bool,
) -> StoredDocument | None:
    if not force_new:
        existing = (
            db.query(StoredDocument)
            .filter(StoredDocument.related_invoice_id == invoice.id)
            .order_by(StoredDocument.created_at.desc())
            .first()
        )
        if existing:
            return existing

    prior_id = (
        _latest_related_document_id(db, certificate_id=None, invoice_id=invoice.id) if force_new else None
    )

    job = db.get(Job, invoice.job_id)
    fn = f"invoice-{invoice.id}.pdf"
    key = doc_store.build_storage_key(document_type="invoice", document_id=invoice.id, filename_safe=fn)
    data = render_invoice_pdf(db, invoice=invoice)
    chk = doc_store.sha256_hex(data)
    doc_store.save_binary(storage_key=key, data=data)

    meta = {
        "renderer": "invoice_pdf_reportlab_v1",
        "invoice_id": invoice.id,
        "generated_at": _iso_now(),
        "regenerated": force_new,
        "prior_stored_document_id": prior_id,
    }
    row = StoredDocument(
        document_type="invoice",
        filename=fn,
        content_type="application/pdf",
        size_bytes=len(data),
        storage_key=key,
        storage_provider=doc_store.get_storage_provider_name(),
        checksum_sha256=chk,
        related_job_id=invoice.job_id,
        related_site_id=job.site_id if job else None,
        related_asset_id=job.asset_id if job else None,
        related_contract_id=job.contract_id if job else None,
        related_invoice_id=invoice.id,
        uploaded_by_user_id=uploaded_by_user_id,
        source_type="generated",
        visibility_scope="customer_safe",
        status="ready",
        metadata_json=json.dumps(meta, separators=(",", ":")),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def persist_repricing_proposal_pdf(
    db: Session,
    *,
    proposal_id: str,
    uploaded_by_user_id: str | None,
    commit: bool = True,
    force_new: bool = True,
) -> StoredDocument:
    prop = db.get(ContractRepricingProposal, proposal_id)
    if not prop:
        raise ValueError("Repricing proposal not found")
    lines = (
        db.query(ContractRepricingProposalLine)
        .filter(ContractRepricingProposalLine.proposal_id == proposal_id)
        .order_by(ContractRepricingProposalLine.sort_order.asc())
        .all()
    )

    prior_id = None
    if force_new and prop.stored_document_id:
        prior_id = prop.stored_document_id

    fn = f"repricing-proposal-{prop.proposal_reference}.pdf".replace("/", "-")
    key = doc_store.build_storage_key(
        document_type="repricing_proposal", document_id=prop.id, filename_safe=fn
    )
    data = render_repricing_proposal_pdf(db, proposal=prop, lines=lines)
    chk = doc_store.sha256_hex(data)
    doc_store.save_binary(storage_key=key, data=data)

    meta = {
        "renderer": "repricing_proposal_pdf_reportlab_v1",
        "proposal_id": prop.id,
        "proposal_reference": prop.proposal_reference,
        "contract_id": prop.contract_id,
        "repricing_review_id": prop.repricing_review_id,
        "generated_at": _iso_now(),
        "prior_stored_document_id": prior_id,
    }
    row = StoredDocument(
        document_type="repricing_proposal",
        filename=fn,
        content_type="application/pdf",
        size_bytes=len(data),
        storage_key=key,
        storage_provider=doc_store.get_storage_provider_name(),
        checksum_sha256=chk,
        related_job_id=None,
        related_site_id=None,
        related_asset_id=None,
        related_contract_id=prop.contract_id,
        related_invoice_id=None,
        uploaded_by_user_id=uploaded_by_user_id,
        source_type="generated",
        visibility_scope="internal_only",
        status="ready",
        metadata_json=json.dumps(meta, separators=(",", ":")),
    )
    db.add(row)
    db.flush()
    prop.stored_document_id = row.id
    db.add(prop)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row


def persist_activation_confirmation_pdf(
    db: Session,
    *,
    confirmation_id: str,
    uploaded_by_user_id: str | None,
    commit: bool = True,
    force_new: bool = False,
) -> StoredDocument:
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf:
        raise ValueError("Activation confirmation not found")

    if not force_new and conf.stored_document_id:
        existing = db.get(StoredDocument, conf.stored_document_id)
        if existing:
            return existing

    prior_id = conf.stored_document_id if force_new else None
    fn = f"activation-confirmation-{conf.confirmation_reference}.pdf".replace("/", "-")
    key = doc_store.build_storage_key(
        document_type="contract_activation_confirmation", document_id=conf.id, filename_safe=fn
    )
    data = render_contract_activation_confirmation_pdf(db, confirmation=conf)
    chk = doc_store.sha256_hex(data)
    doc_store.save_binary(storage_key=key, data=data)

    ctr = db.get(Contract, conf.contract_id)

    meta = {
        "renderer": "contract_activation_confirmation_pdf_reportlab_v1",
        "activation_confirmation_id": conf.id,
        "confirmation_reference": conf.confirmation_reference,
        "contract_id": conf.contract_id,
        "generated_at": _iso_now(),
        "prior_stored_document_id": prior_id,
    }
    row = StoredDocument(
        document_type="contract_activation_confirmation",
        filename=fn,
        content_type="application/pdf",
        size_bytes=len(data),
        storage_key=key,
        storage_provider=doc_store.get_storage_provider_name(),
        checksum_sha256=chk,
        related_job_id=None,
        related_site_id=ctr.site_id if ctr else None,
        related_asset_id=None,
        related_contract_id=conf.contract_id,
        related_invoice_id=None,
        related_certificate_id=None,
        uploaded_by_user_id=uploaded_by_user_id,
        source_type="generated",
        visibility_scope="internal_only",
        status="ready",
        metadata_json=json.dumps(meta, separators=(",", ":")),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
        db.refresh(row)
    return row
