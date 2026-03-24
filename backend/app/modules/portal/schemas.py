from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.modules.compliance.schemas import CertificateOut
from backend.app.modules.dispatch.schemas import JobOut
from backend.app.modules.invoicing.schemas import InvoiceOut


class PortalExportOut(BaseModel):
    customer_id: str | None
    customer_email: str | None

    jobs: list[JobOut] = []
    certificates: list[CertificateOut] = []
    invoices: list[InvoiceOut] = []


class PortalDeleteOut(BaseModel):
    deleted: bool
    detail: str
    meta: dict[str, Any] = {}


class PortalSupportContactOut(BaseModel):
    email: str
    phone: str


class PortalTimelineEventOut(BaseModel):
    at: str
    milestone: str
    title: str


class PortalJobTrackingOut(BaseModel):
    job_id: str
    customer_tracking_state: str
    scheduled_at: str | None
    eta: dict[str, Any]
    engineer_on_the_way: bool
    engineer_on_site: bool
    last_status_update_at: str | None
    status_timeline: list[PortalTimelineEventOut]
    map_payload: dict[str, Any] | None = None
    support_contact: PortalSupportContactOut
    tracking_link_token: str | None = None


class PortalSiteSummaryOut(BaseModel):
    id: str
    site_code: str
    name: str
    address_line1: str
    city: str | None
    postcode: str | None


class PortalAssetSummaryOut(BaseModel):
    id: str
    asset_code: str
    asset_type: str
    name: str
    status: str
    site_id: str | None


class PortalDocumentItemOut(BaseModel):
    document_type: str
    id: str
    title: str
    related_job_id: str | None
    related_site_id: str | None
    related_asset_id: str | None
    issue_date: datetime
    status: str
    retrieval_path: str
    # When set, authorized binary delivery uses /portal/me/documents/{stored_document_id}/download
    stored_document_id: str | None = None


class PortalJobSummaryLiteOut(BaseModel):
    id: str
    status: str
    address: str
    scheduled_at: datetime | None
    work_type: str


class PortalCertificateLiteOut(BaseModel):
    id: str
    certificate_type: str
    status: str
    created_at: datetime
    job_id: str


class PortalSiteDetailOut(BaseModel):
    site: PortalSiteSummaryOut
    open_jobs: list[PortalJobSummaryLiteOut]
    recent_jobs: list[PortalJobSummaryLiteOut]
    assets: list[PortalAssetSummaryOut]
    recent_certificates: list[PortalCertificateLiteOut]
    upcoming_ppm: list[dict[str, Any]]


class PortalAssetHistoryEntryOut(BaseModel):
    kind: str
    at: str
    title: str
    id: str | None = None


class PortalInvoiceDetailOut(BaseModel):
    invoice: dict[str, Any]
    service_context: dict[str, Any]
    retrieval: dict[str, Any]


class PortalRepricingLineSummaryOut(BaseModel):
    """Customer-safe line summary (no internal justification payloads)."""

    title: str
    line_type: str
    current_line_total: float | None = None
    proposed_line_total: float


class PortalRepricingProposalOut(BaseModel):
    """Released repricing / renewal proposal for portal (no internal approval or margin basis)."""

    id: str
    contract_id: str
    proposal_reference: str
    currency: str
    current_contract_value: float | None = None
    proposed_contract_value: float | None = None
    effective_date: datetime | None = None
    validity_end_date: datetime | None = None
    customer_expiry_at: datetime | None = None
    customer_release_status: str
    customer_response_status: str | None = None
    released_to_customer_at: datetime | None = None
    customer_viewed_at: datetime | None = None
    customer_responded_at: datetime | None = None
    is_past_validity: bool = False
    lines: list[PortalRepricingLineSummaryOut] = Field(default_factory=list)
    stored_document_id: str | None = None
    pdf_downloadable: bool = False
    formal_acceptance_record_id: str | None = None


class PortalRepricingProposalRespondIn(BaseModel):
    response_type: str
    notes: str | None = None
    contact_reference: str | None = None


class PortalAcceptanceInitiateIn(BaseModel):
    """Defaults to commercial acceptance; use acknowledgement_only for expiry-safe acknowledgement flows."""

    acceptance_type: Literal["portal_acceptance", "acknowledgement_only"] = "portal_acceptance"


class PortalAcceptanceCompleteIn(BaseModel):
    signed_name: str | None = None
    signed_title: str | None = None
    signed_email: str | None = None
    accepted_by_contact: str | None = None
    acceptance_notes: str | None = None
    confirm_binding_acknowledgement: bool = False


class PortalSecureAcceptanceCompleteIn(PortalAcceptanceCompleteIn):
    """Completes tokenized session; token is in URL path, not body."""

    pass


class PortalAcceptancePublicOut(BaseModel):
    """Minimal customer-safe payload for secure-link acceptance page."""

    session_status: str
    proposal_reference: str
    acceptance_type: str
    expires_at: datetime | None = None
    disclosure: str = (
        "This is an in-product acceptance record (not a third-party e-signature). "
        "By continuing you confirm the details you submit are accurate."
    )


class PortalAcceptanceTokenCompleteOut(BaseModel):
    session_status: str
    proposal_reference: str
    immutable_hash: str | None = None


class PortalActivationConfirmationOut(BaseModel):
    """Customer-safe activation confirmation (no internal commercial ops fields)."""

    id: str
    contract_id: str
    confirmation_reference: str
    status: str
    effective_date: datetime
    released_to_customer_at: datetime | None
    customer_viewed_at: datetime | None
    customer_acknowledged_at: datetime | None
    summary: dict[str, Any] = Field(default_factory=dict)
    stored_document_id: str | None
    amendment_id: str
    contract_version_id: str | None
    source_proposal_id: str | None


class PortalActivationConfirmationTimelineEventOut(BaseModel):
    at: str | None
    event_type: str
    summary: str


class PortalActivationConfirmationAckIn(BaseModel):
    acknowledged_by_contact: str
    notes: str | None = None


class PortalCustomerCommunicationOut(BaseModel):
    """Customer-safe outbound comms history (no internal drafts, no raw provider payloads)."""

    id: str
    contract_id: str
    source_entity_type: str
    communication_type: str
    channel: str
    status: str
    subject: str | None
    created_at: datetime
    sent_at: datetime | None
    failed_at: datetime | None
    cancelled_at: datetime | None
    body_preview: str | None = None
    recipient_masked: str | None = None
    last_delivery_status: str | None = None
    last_delivery_completed_at: datetime | None = None
