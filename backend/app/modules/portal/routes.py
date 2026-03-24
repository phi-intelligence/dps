from __future__ import annotations

import json
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.api.deps import require_roles
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.modules.assets.models import Asset
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.compliance.schemas import CertificateOut
from backend.app.modules.contracts.history_service import build_asset_history
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.schemas import JobOut
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.invoicing.schemas import InvoiceOut
from backend.app.modules.invoicing.service import pay_invoice
from backend.app.modules.ppm.models import PpmSchedule
from backend.app.modules.portal.customer_tracking_service import (
    build_customer_job_timeline,
    build_customer_safe_map_payload,
    compute_customer_eta,
    get_customer_job_tracking_state,
)
from backend.app.modules.portal.portal_access_service import (
    can_customer_access_asset,
    can_customer_access_contract,
    can_customer_access_job,
    can_customer_access_site,
    list_portal_sites_for_customer,
    portal_job_ids,
)
from backend.app.services import contract_activation_confirmation_service as acconf
from backend.app.services import portal_customer_scope_service as pcss
from backend.app.services import customer_repricing_proposal_service as crps
from backend.app.services import proposal_acceptance_service as pas
from backend.app.services import repricing_proposal_service as rps
from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry
from backend.app.modules.portal.portal_dashboard_service import build_portal_dashboard
from backend.app.modules.portal.portal_documents_service import (
    get_certificate_for_portal,
    list_asset_documents_for_portal,
    list_unified_portal_documents,
)
from backend.app.modules.documents.schemas import DocumentDownloadLinkIn, DocumentDownloadLinkOut, PortalStoredDocumentOut
from backend.app.modules.documents.service import (
    create_portal_download_link,
    get_portal_stored_document_out,
    resolve_stored_document_for_certificate,
    resolve_stored_document_for_invoice,
    serve_portal_bearer_download,
)
from backend.app.modules.portal.portal_communications_service import (
    get_portal_customer_communication,
    list_portal_customer_communications,
)
from backend.app.modules.portal.portal_invoice_service import build_portal_invoice_detail
from backend.app.modules.portal.schemas import (
    PortalAcceptanceCompleteIn,
    PortalAcceptanceInitiateIn,
    PortalAcceptancePublicOut,
    PortalAcceptanceTokenCompleteOut,
    PortalSecureAcceptanceCompleteIn,
    PortalActivationConfirmationAckIn,
    PortalActivationConfirmationOut,
    PortalActivationConfirmationTimelineEventOut,
    PortalAssetHistoryEntryOut,
    PortalAssetSummaryOut,
    PortalCertificateLiteOut,
    PortalCustomerCommunicationOut,
    PortalDeleteOut,
    PortalDocumentItemOut,
    PortalExportOut,
    PortalInvoiceDetailOut,
    PortalJobSummaryLiteOut,
    PortalJobTrackingOut,
    PortalRepricingLineSummaryOut,
    PortalRepricingProposalOut,
    PortalRepricingProposalRespondIn,
    PortalSiteDetailOut,
    PortalSiteSummaryOut,
    PortalSupportContactOut,
    PortalTimelineEventOut,
)
from backend.app.modules.portal.utils import (
    anonymize_client_customer_for_email,
    get_client_customer,
    list_client_certificates,
    list_client_invoices,
    list_client_jobs,
)
from backend.app.modules.sites.models import Site
from backend.app.modules.sites.schemas import SiteOut


router = APIRouter(prefix="/portal", tags=["portal"])


def _portal_customer_or_404(db: Session, *, email: str):
    customer = get_client_customer(db, email=email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return customer


# --- Public secure-link acceptance (unauthenticated; token is the credential) ---


@router.get("/acceptance/{token}", response_model=PortalAcceptancePublicOut)
def portal_public_acceptance_get(token: str, db: Session = Depends(get_db)) -> PortalAcceptancePublicOut:
    try:
        ctx = pas.describe_secure_link_for_public(db, raw_token=token, mark_viewed=True)
        db.commit()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from None
    if ctx["session_status"] != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return PortalAcceptancePublicOut(
        session_status=ctx["session_status"],
        proposal_reference=ctx["proposal_reference"],
        acceptance_type=ctx["acceptance_type"] or "unknown",
        expires_at=ctx["expires_at"],
    )


@router.post("/acceptance/{token}/complete", response_model=PortalAcceptanceTokenCompleteOut)
def portal_public_acceptance_complete(
    token: str,
    payload: PortalSecureAcceptanceCompleteIn,
    request: Request,
    db: Session = Depends(get_db),
) -> PortalAcceptanceTokenCompleteOut:
    try:
        ctx = pas.describe_secure_link_for_public(db, raw_token=token, mark_viewed=False)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from None
    sess = ctx["session"]
    rec = ctx["record"]
    prop = ctx["proposal"]
    if sess.session_status != "active" or not rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acceptance session is not available",
        )
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    try:
        pas.complete_acceptance(
            db,
            record=rec,
            session=sess,
            actor_user_id=None,
            acceptance_ip=ip,
            acceptance_user_agent=ua,
            signed_name=payload.signed_name,
            signed_title=payload.signed_title,
            signed_email=payload.signed_email,
            accepted_by_contact=payload.accepted_by_contact,
            acceptance_notes=payload.acceptance_notes,
            confirm_binding_acknowledgement=payload.confirm_binding_acknowledgement,
            raw_token=token,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    db.refresh(sess)
    db.refresh(rec)
    return PortalAcceptanceTokenCompleteOut(
        session_status=sess.session_status,
        proposal_reference=prop.proposal_reference,
        immutable_hash=rec.immutable_hash,
    )


def _portal_activation_confirmation_out(conf) -> PortalActivationConfirmationOut:
    raw = json.loads(conf.summary_json) if conf.summary_json else {}
    summary = acconf.portal_safe_summary(raw if isinstance(raw, dict) else {})
    return PortalActivationConfirmationOut(
        id=conf.id,
        contract_id=conf.contract_id,
        confirmation_reference=conf.confirmation_reference,
        status=conf.status,
        effective_date=conf.effective_date,
        released_to_customer_at=conf.released_to_customer_at,
        customer_viewed_at=conf.customer_viewed_at,
        customer_acknowledged_at=conf.customer_acknowledged_at,
        summary=summary,
        stored_document_id=conf.stored_document_id,
        amendment_id=conf.amendment_id,
        contract_version_id=conf.contract_version_id,
        source_proposal_id=conf.source_proposal_id,
    )


def _portal_repricing_proposal_out(db: Session, p, lines) -> PortalRepricingProposalOut:
    expired = p.customer_release_status == "expired" or is_past_customer_expiry(p)
    pdf_ok = bool(p.stored_document_id) and not expired
    summaries = [
        PortalRepricingLineSummaryOut(
            title=ln.title,
            line_type=ln.line_type,
            current_line_total=ln.current_line_total,
            proposed_line_total=float(ln.proposed_line_total),
        )
        for ln in lines
    ]
    return PortalRepricingProposalOut(
        id=p.id,
        contract_id=p.contract_id,
        proposal_reference=p.proposal_reference,
        currency=p.currency,
        current_contract_value=p.current_contract_value,
        proposed_contract_value=p.proposed_contract_value,
        effective_date=p.effective_date,
        validity_end_date=p.validity_end_date,
        customer_expiry_at=p.customer_expiry_at,
        customer_release_status=p.customer_release_status,
        customer_response_status=p.customer_response_status,
        released_to_customer_at=p.released_to_customer_at,
        customer_viewed_at=p.customer_viewed_at,
        customer_responded_at=p.customer_responded_at,
        is_past_validity=expired,
        lines=summaries,
        stored_document_id=p.stored_document_id,
        pdf_downloadable=pdf_ok,
        formal_acceptance_record_id=getattr(p, "formal_acceptance_record_id", None),
    )


def _support() -> PortalSupportContactOut:
    from backend.app.services.runtime_settings_service import get_effective_notifications_settings

    eff = get_effective_notifications_settings(None)
    return PortalSupportContactOut(
        email=str(eff["portal_support_email"]),
        phone=str(eff["portal_support_phone"]),
    )


@router.get("/me/jobs", response_model=list[JobOut])
def client_jobs(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
):
    customer = get_client_customer(db, email=current_user.email)
    return list_client_jobs(db, customer=customer) if customer else []


@router.get("/me/dashboard")
def portal_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> dict:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        return {"profile": "unknown", "summary": {}, "alerts": ["No customer profile linked to this account."]}
    return build_portal_dashboard(db, customer=customer)


@router.get("/me/jobs/{job_id}/tracking", response_model=PortalJobTrackingOut)
def portal_job_tracking(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalJobTrackingOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_job(db, customer=customer, job_id=job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job = db.get(Job, job_id)
    assert job
    if not job.tracking_link_token:
        job.tracking_link_token = secrets.token_urlsafe(24)[:48]
        db.commit()
        db.refresh(job)

    state = get_customer_job_tracking_state(db, job_id=job_id)
    eta = compute_customer_eta(db, job_id=job_id)
    timeline_raw = build_customer_job_timeline(db, job_id=job_id)
    timeline = [PortalTimelineEventOut(**t) for t in timeline_raw]
    map_payload = build_customer_safe_map_payload(db, job=job)

    return PortalJobTrackingOut(
        job_id=job_id,
        customer_tracking_state=state["customer_tracking_state"],
        scheduled_at=state.get("scheduled_at"),
        eta=eta,
        engineer_on_the_way=state["engineer_on_the_way"],
        engineer_on_site=state["engineer_on_site"],
        last_status_update_at=state.get("last_status_update_at"),
        status_timeline=timeline,
        map_payload=map_payload,
        support_contact=_support(),
        tracking_link_token=job.tracking_link_token,
    )


@router.get("/me/jobs/{job_id}/timeline", response_model=list[PortalTimelineEventOut])
def portal_job_timeline(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalTimelineEventOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_job(db, customer=customer, job_id=job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    raw = build_customer_job_timeline(db, job_id=job_id)
    return [PortalTimelineEventOut(**t) for t in raw]


@router.get("/me/sites", response_model=list[PortalSiteSummaryOut])
def portal_list_sites(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalSiteSummaryOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        return []
    sites = list_portal_sites_for_customer(db, customer=customer)
    return [
        PortalSiteSummaryOut(
            id=s.id,
            site_code=s.site_code,
            name=s.name,
            address_line1=s.address_line1,
            city=s.city,
            postcode=s.postcode,
        )
        for s in sites
    ]


@router.get("/me/sites/{site_id}", response_model=SiteOut)
def portal_get_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Site:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_site(db, customer=customer, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


@router.get("/me/sites/{site_id}/detail", response_model=PortalSiteDetailOut)
def portal_site_detail(
    site_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalSiteDetailOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_site(db, customer=customer, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    jobs = (
        db.query(Job)
        .filter(Job.site_id == site_id, Job.customer_id == customer.id)
        .order_by(Job.created_at.desc())
        .limit(80)
        .all()
    )
    open_j = [j for j in jobs if j.status not in ("completed", "closed", "cancelled")]
    recent = jobs[:15]
    assets = db.query(Asset).filter(Asset.site_id == site_id, Asset.customer_id == customer.id).limit(100).all()
    job_ids = [j.id for j in jobs]
    certs: list = []
    if job_ids:
        certs = (
            db.query(Certificate)
            .filter(Certificate.job_id.in_(job_ids))
            .order_by(Certificate.created_at.desc())
            .limit(10)
            .all()
        )

    ppm = (
        db.query(PpmSchedule)
        .filter(PpmSchedule.site_id == site_id, PpmSchedule.active.is_(True))
        .order_by(PpmSchedule.next_due_date.asc())
        .limit(10)
        .all()
    )

    return PortalSiteDetailOut(
        site=PortalSiteSummaryOut(
            id=site.id,
            site_code=site.site_code,
            name=site.name,
            address_line1=site.address_line1,
            city=site.city,
            postcode=site.postcode,
        ),
        open_jobs=[
            PortalJobSummaryLiteOut(id=j.id, status=j.status, address=j.address[:200], scheduled_at=j.scheduled_at, work_type=j.work_type)
            for j in open_j[:20]
        ],
        recent_jobs=[
            PortalJobSummaryLiteOut(id=j.id, status=j.status, address=j.address[:200], scheduled_at=j.scheduled_at, work_type=j.work_type)
            for j in recent
        ],
        assets=[
            PortalAssetSummaryOut(
                id=a.id,
                asset_code=a.asset_code or "",
                asset_type=a.asset_type,
                name=a.name,
                status=a.status,
                site_id=a.site_id,
            )
            for a in assets
        ],
        recent_certificates=[
            PortalCertificateLiteOut(id=c.id, certificate_type=c.certificate_type, status=c.status, created_at=c.created_at, job_id=c.job_id)
            for c in certs
        ],
        upcoming_ppm=[
            {"schedule_id": p.id, "title": p.title, "next_due_date": p.next_due_date.isoformat()} for p in ppm
        ],
    )


@router.get("/me/sites/{site_id}/jobs", response_model=list[PortalJobSummaryLiteOut])
def portal_site_jobs(
    site_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalJobSummaryLiteOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_site(db, customer=customer, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    jobs = (
        db.query(Job)
        .filter(Job.site_id == site_id, Job.customer_id == customer.id)
        .order_by(Job.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        PortalJobSummaryLiteOut(id=j.id, status=j.status, address=j.address[:200], scheduled_at=j.scheduled_at, work_type=j.work_type)
        for j in jobs
    ]


@router.get("/me/sites/{site_id}/assets", response_model=list[PortalAssetSummaryOut])
def portal_site_assets(
    site_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalAssetSummaryOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_site(db, customer=customer, site_id=site_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    assets = db.query(Asset).filter(Asset.site_id == site_id, Asset.customer_id == customer.id).limit(200).all()
    return [
        PortalAssetSummaryOut(
            id=a.id,
            asset_code=a.asset_code or "",
            asset_type=a.asset_type,
            name=a.name,
            status=a.status,
            site_id=a.site_id,
        )
        for a in assets
    ]


@router.get("/me/assets/{asset_id}/history", response_model=list[PortalAssetHistoryEntryOut])
def portal_asset_history(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalAssetHistoryEntryOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer or not can_customer_access_asset(db, customer=customer, asset_id=asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    raw = build_asset_history(db, asset_id=asset_id)
    out: list[PortalAssetHistoryEntryOut] = []
    for e in raw:
        out.append(
            PortalAssetHistoryEntryOut(
                kind=e.get("kind", "note"),
                at=e.get("at", ""),
                title=e.get("summary", "")[:300],
                id=e.get("id"),
            )
        )
    return out


@router.get("/me/assets/{asset_id}/documents", response_model=list[PortalDocumentItemOut])
def portal_asset_documents(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalDocumentItemOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    rows = list_asset_documents_for_portal(db, customer=customer, asset_id=asset_id)
    return [PortalDocumentItemOut(**r) for r in rows]


@router.get("/me/documents", response_model=list[PortalDocumentItemOut])
def portal_documents(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalDocumentItemOut]:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        return []
    rows = list_unified_portal_documents(db, customer=customer)
    return [PortalDocumentItemOut(**r) for r in rows]


@router.get("/me/documents/{document_id}", response_model=PortalStoredDocumentOut)
def portal_get_stored_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalStoredDocumentOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return get_portal_stored_document_out(db, customer=customer, document_id=document_id, request=request)


@router.post("/me/documents/{document_id}/download-link", response_model=DocumentDownloadLinkOut)
def portal_create_document_download_link(
    document_id: str,
    request: Request,
    body: DocumentDownloadLinkIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> DocumentDownloadLinkOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    ttl = body.ttl_seconds if body else None
    return create_portal_download_link(
        db, document_id=document_id, customer=customer, request=request, ttl_seconds=ttl
    )


@router.get("/me/documents/{document_id}/download")
def portal_download_stored_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Response:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    data, content_type, filename = serve_portal_bearer_download(
        db, document_id=document_id, customer=customer, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get("/me/certificates", response_model=list[CertificateOut])
def client_certificates(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[CertificateOut]:
    customer = get_client_customer(db, email=current_user.email)
    return list_client_certificates(db, customer=customer) if customer else []


@router.get("/me/certificates/{certificate_id}", response_model=CertificateOut)
def portal_certificate_detail(
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> CertificateOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    c = get_certificate_for_portal(db, customer=customer, certificate_id=certificate_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return c


@router.get("/me/certificates/{certificate_id}/download")
def portal_download_certificate(
    certificate_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Response:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    c = get_certificate_for_portal(db, customer=customer, certificate_id=certificate_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    sd = resolve_stored_document_for_certificate(db, certificate_id=certificate_id)
    if not sd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate document not available")
    data, content_type, filename = serve_portal_bearer_download(
        db, document_id=sd.id, customer=customer, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get("/me/invoices", response_model=list[InvoiceOut])
def client_invoices(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[InvoiceOut]:
    customer = get_client_customer(db, email=current_user.email)
    return list_client_invoices(db, customer=customer) if customer else []


@router.get("/me/invoices/{invoice_id}", response_model=PortalInvoiceDetailOut)
def portal_invoice_detail(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalInvoiceDetailOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.job_id not in portal_job_ids(db, customer=customer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    payload = build_portal_invoice_detail(db, invoice=inv)
    return PortalInvoiceDetailOut(**payload)


@router.get("/me/invoices/{invoice_id}/download")
def portal_download_invoice(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Response:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.job_id not in portal_job_ids(db, customer=customer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    sd = resolve_stored_document_for_invoice(db, invoice_id=invoice_id)
    if not sd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice document not available")
    data, content_type, filename = serve_portal_bearer_download(
        db, document_id=sd.id, customer=customer, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get("/me/communications", response_model=list[PortalCustomerCommunicationOut])
def portal_list_customer_communications(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalCustomerCommunicationOut]:
    customer = _portal_customer_or_404(db, email=current_user.email)
    return list_portal_customer_communications(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        limit=limit,
    )


@router.get("/me/communications/{communication_id}", response_model=PortalCustomerCommunicationOut)
def portal_get_customer_communication(
    communication_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalCustomerCommunicationOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    row = get_portal_customer_communication(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        communication_id=communication_id,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


@router.get("/me/export", response_model=PortalExportOut)
def client_export_data(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalExportOut:
    customer = get_client_customer(db, email=current_user.email)
    jobs = list_client_jobs(db, customer=customer) if customer else []
    certificates = list_client_certificates(db, customer=customer) if customer else []
    invoices = list_client_invoices(db, customer=customer) if customer else []

    return PortalExportOut(
        customer_id=customer.id if customer else None,
        customer_email=current_user.email,
        jobs=jobs,
        certificates=certificates,
        invoices=invoices,
    )


@router.delete("/me/delete", response_model=PortalDeleteOut)
def client_delete_account(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalDeleteOut:
    import uuid

    anonymize_client_customer_for_email(db, email=current_user.email)

    current_user.is_active = False
    current_user.email = f"deleted_{uuid.uuid4().hex[:16]}@example.invalid"
    db.commit()

    return PortalDeleteOut(deleted=True, detail="Account deleted (anonymized for Phase 4 demo).")


@router.post("/me/invoices/{invoice_id}/pay", response_model=InvoiceOut)
def client_pay_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> InvoiceOut:
    customer = get_client_customer(db, email=current_user.email)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    if invoice.job_id not in portal_job_ids(db, customer=customer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invoice not accessible")

    return pay_invoice(db, invoice_id=invoice_id)


# --- Customer repricing / renewal proposals (released only; contract-scoped auth) ---


@router.get("/me/contracts/{contract_id}/repricing-proposals", response_model=list[PortalRepricingProposalOut])
def portal_list_repricing_proposals_for_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalRepricingProposalOut]:
    customer = _portal_customer_or_404(db, email=current_user.email)
    if not can_customer_access_contract(
        db, customer=customer, contract_id=contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    props = crps.list_released_proposals_for_contract(db, contract_id=contract_id)
    props = pcss.filter_released_proposals_for_customer_portal(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        contract_id=contract_id,
        proposals=props,
    )
    out: list[PortalRepricingProposalOut] = []
    for p in props:
        lines = rps.list_lines(db, proposal_id=p.id)
        out.append(_portal_repricing_proposal_out(db, p, lines))
    return out


@router.get("/me/repricing-proposals/{proposal_id}", response_model=PortalRepricingProposalOut)
def portal_get_repricing_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalRepricingProposalOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    crps.mark_proposal_viewed_by_customer(
        db,
        proposal=prop,
        portal_user_id=current_user.id,
        customer_id=customer.id,
    )
    lines = rps.list_lines(db, proposal_id=prop.id)
    return _portal_repricing_proposal_out(db, prop, lines)


@router.get("/me/repricing-proposals/{proposal_id}/download")
def portal_download_repricing_proposal_pdf(
    proposal_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Response:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    crps.mark_proposal_viewed_by_customer(
        db,
        proposal=prop,
        portal_user_id=current_user.id,
        customer_id=customer.id,
    )
    if not prop.stored_document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not available")
    data, content_type, filename = serve_portal_bearer_download(
        db, document_id=prop.stored_document_id, customer=customer, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get("/me/repricing-proposals/{proposal_id}/timeline")
def portal_repricing_proposal_timeline(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[dict]:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return crps.build_portal_timeline(db, proposal=prop)


@router.post("/me/repricing-proposals/{proposal_id}/respond", response_model=PortalRepricingProposalOut)
def portal_respond_repricing_proposal(
    proposal_id: str,
    payload: PortalRepricingProposalRespondIn = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalRepricingProposalOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        p, _row = crps.record_customer_response(
            db,
            proposal_id=proposal_id,
            portal_user_id=current_user.id,
            customer_id=customer.id,
            response_type=payload.response_type,
            notes=payload.notes,
            contact_reference=payload.contact_reference,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    lines = rps.list_lines(db, proposal_id=p.id)
    return _portal_repricing_proposal_out(db, p, lines)


@router.get("/me/repricing-proposals/{proposal_id}/acceptance")
def portal_get_repricing_proposal_acceptance(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> dict:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    rec, sess = pas.get_active_session_for_portal_proposal(db, proposal_id=proposal_id, customer_id=customer.id)
    if rec and sess:
        pas.mark_acceptance_viewed_if_needed(
            db, record=rec, session=sess, actor_user_id=current_user.id
        )
        db.commit()
    return pas.portal_acceptance_state(db, proposal_id=proposal_id, customer_id=customer.id)


@router.post("/me/repricing-proposals/{proposal_id}/acceptance/initiate")
def portal_initiate_repricing_proposal_acceptance(
    proposal_id: str,
    payload: PortalAcceptanceInitiateIn = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> dict:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        rec, sess = pas.portal_initiate_acceptance(
            db,
            proposal_id=proposal_id,
            portal_user_id=current_user.id,
            customer_id=customer.id,
            acceptance_type=payload.acceptance_type,
        )
        db.commit()
        db.refresh(rec)
        db.refresh(sess)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {
        "acceptance_record_id": rec.id,
        "session_id": sess.id,
        "acceptance_status": rec.acceptance_status,
        "acceptance_type": rec.acceptance_type,
    }


@router.post("/me/repricing-proposals/{proposal_id}/acceptance/complete", response_model=PortalRepricingProposalOut)
def portal_complete_repricing_proposal_acceptance(
    proposal_id: str,
    payload: PortalAcceptanceCompleteIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalRepricingProposalOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    prop = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop or not can_customer_access_contract(
        db, customer=customer, contract_id=prop.contract_id, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not pcss.customer_portal_proposal_allowed(
        db,
        customer=customer,
        portal_login_email=current_user.email,
        proposal_id=proposal_id,
        contract_id=prop.contract_id,
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    rec, sess = pas.get_active_session_for_portal_proposal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not rec or not sess:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active formal acceptance session; call initiate first",
        )
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    signed_email = payload.signed_email or current_user.email
    try:
        pas.complete_acceptance(
            db,
            record=rec,
            session=sess,
            actor_user_id=current_user.id,
            acceptance_ip=ip,
            acceptance_user_agent=ua,
            signed_name=payload.signed_name,
            signed_title=payload.signed_title,
            signed_email=signed_email,
            accepted_by_contact=payload.accepted_by_contact,
            acceptance_notes=payload.acceptance_notes,
            confirm_binding_acknowledgement=payload.confirm_binding_acknowledgement,
            raw_token=None,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    prop_after = crps.get_proposal_for_portal(db, proposal_id=proposal_id, customer_id=customer.id)
    if not prop_after:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    lines = rps.list_lines(db, proposal_id=prop_after.id)
    return _portal_repricing_proposal_out(db, prop_after, lines)


# --- Activation confirmations (released to portal only; distinct from internal activation truth) ---


@router.get(
    "/me/contracts/{contract_id}/activation-confirmations",
    response_model=list[PortalActivationConfirmationOut],
)
def portal_list_activation_confirmations_for_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalActivationConfirmationOut]:
    customer = _portal_customer_or_404(db, email=current_user.email)
    rows = acconf.list_confirmations_for_portal_contract(
        db, customer=customer, contract_id=contract_id, portal_login_email=current_user.email
    )
    return [_portal_activation_confirmation_out(r) for r in rows]


@router.get("/me/activation-confirmations/{confirmation_id}", response_model=PortalActivationConfirmationOut)
def portal_get_activation_confirmation(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalActivationConfirmationOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not acconf.portal_customer_can_access_activation_confirmation(
        db, customer=customer, conf=conf, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    touched = acconf.touch_customer_view_if_needed(
        db,
        confirmation_id=confirmation_id,
        customer=customer,
        actor_user_id=current_user.id,
        portal_login_email=current_user.email,
        commit=True,
    )
    assert touched is not None
    return _portal_activation_confirmation_out(touched)


@router.get("/me/activation-confirmations/{confirmation_id}/download")
def portal_download_activation_confirmation_pdf(
    confirmation_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> Response:
    customer = _portal_customer_or_404(db, email=current_user.email)
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not acconf.portal_customer_can_access_activation_confirmation(
        db, customer=customer, conf=conf, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    touched = acconf.touch_customer_view_if_needed(
        db,
        confirmation_id=confirmation_id,
        customer=customer,
        actor_user_id=current_user.id,
        portal_login_email=current_user.email,
        commit=True,
    )
    if not touched or not touched.stored_document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    data, content_type, filename = serve_portal_bearer_download(
        db, document_id=touched.stored_document_id, customer=customer, request=request
    )
    cd = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": cd},
    )


@router.get(
    "/me/activation-confirmations/{confirmation_id}/timeline",
    response_model=list[PortalActivationConfirmationTimelineEventOut],
)
def portal_activation_confirmation_timeline(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> list[PortalActivationConfirmationTimelineEventOut]:
    customer = _portal_customer_or_404(db, email=current_user.email)
    conf = db.get(ContractActivationConfirmation, confirmation_id)
    if not conf or not acconf.portal_customer_can_access_activation_confirmation(
        db, customer=customer, conf=conf, portal_login_email=current_user.email
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    raw = acconf.build_timeline_for_confirmation(
        db, confirmation_id=confirmation_id, contract_id=conf.contract_id
    )
    return [PortalActivationConfirmationTimelineEventOut(**x) for x in raw]


@router.post("/me/activation-confirmations/{confirmation_id}/acknowledge", response_model=PortalActivationConfirmationOut)
def portal_ack_activation_confirmation(
    confirmation_id: str,
    payload: PortalActivationConfirmationAckIn = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Client")),
) -> PortalActivationConfirmationOut:
    customer = _portal_customer_or_404(db, email=current_user.email)
    try:
        row = acconf.acknowledge_by_customer(
            db,
            confirmation_id=confirmation_id,
            customer=customer,
            portal_user_id=current_user.id,
            acknowledged_by_contact=payload.acknowledged_by_contact,
            acknowledgement_notes=payload.notes,
            portal_login_email=current_user.email,
            commit=True,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from None
    return _portal_activation_confirmation_out(row)
