from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import json

from pydantic import BaseModel, Field, field_validator


class ContractCreateIn(BaseModel):
    customer_id: str
    site_id: str | None = None
    name: str
    contract_code: str | None = None
    contract_type: str = "ppm_plus_reactive"
    status: str = "active"
    term_start_at: datetime
    term_end_at: datetime | None = None
    renewal_review_date: datetime | None = None
    billing_frequency: str | None = None
    contract_value: float | None = None
    covered_assets_mode: str = "all_assets"
    covered_asset_ids_json: str = "[]"
    service_inclusions_json: str = "[]"
    exclusions_json: str = "[]"
    notes: str | None = None
    default_sla_policy_id: str | None = None

    ppm_interval_days: int = 90
    next_ppm_due_at: datetime

    sla_response_minutes: int = 60
    sla_attendance_minutes: int = 240
    sla_completion_minutes: int = 720
    communication_locale: str | None = Field(
        default=None,
        max_length=16,
        description="Locale for generated customer communications (e.g. en, fr). Falls back to global default when unset.",
    )


class ContractPatchIn(BaseModel):
    """PATCH body for contracts. `manual_update_reason` is audit-only and not stored on Contract columns."""

    site_id: str | None = None
    name: str | None = None
    contract_code: str | None = None
    contract_type: str | None = None
    status: str | None = None
    term_start_at: datetime | None = None
    term_end_at: datetime | None = None
    renewal_review_date: datetime | None = None
    billing_frequency: str | None = None
    contract_value: float | None = None
    covered_assets_mode: str | None = None
    covered_asset_ids_json: str | None = None
    service_inclusions_json: str | None = None
    exclusions_json: str | None = None
    notes: str | None = None
    default_sla_policy_id: str | None = None
    ppm_interval_days: int | None = None
    next_ppm_due_at: datetime | None = None
    sla_response_minutes: int | None = None
    sla_attendance_minutes: int | None = None
    sla_completion_minutes: int | None = None
    renewal_status: str | None = None
    renewal_review_due_at: datetime | None = None
    renewal_review_last_opened_at: datetime | None = None
    renewal_decision: str | None = None
    repricing_required: bool | None = None
    account_attention_level: str | None = None
    churn_risk_level: str | None = None
    manual_update_reason: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional reason for this edit (stored on ContractVersion.notes and commercial audit).",
    )


class ContractOut(BaseModel):
    id: str
    customer_id: str
    site_id: str | None
    name: str
    contract_code: str
    contract_type: str
    status: str
    term_start_at: datetime
    term_end_at: datetime | None
    renewal_review_date: datetime | None
    billing_frequency: str | None
    contract_value: float | None
    covered_assets_mode: str
    covered_asset_ids_json: str
    service_inclusions_json: str
    exclusions_json: str
    notes: str | None
    default_sla_policy_id: str | None
    ppm_interval_days: int
    next_ppm_due_at: datetime
    sla_response_minutes: int
    sla_attendance_minutes: int
    sla_completion_minutes: int
    created_at: datetime
    renewal_status: str = "not_due"
    renewal_review_due_at: datetime | None = None
    renewal_review_last_opened_at: datetime | None = None
    renewal_decision: str | None = None
    repricing_required: bool = False
    account_attention_level: str = "normal"
    churn_risk_level: str | None = None
    communication_locale: str | None = None

    model_config = {"from_attributes": True}


class ContractManualUpdateOut(ContractOut):
    """PATCH response including optional manual versioning metadata."""

    manual_version_created: bool = False
    contract_version_id: str | None = None
    version_number: int | None = None
    update_noop: bool = False


class SlaBreachRiskOut(BaseModel):
    job_id: str
    contract_id: str | None
    risk_state: Literal["on_track", "at_risk", "breached"]
    target_completion_at: datetime | None
    computed_at: datetime


class JobSlaStatusOut(BaseModel):
    job_id: str
    response_time_minutes: float | None
    attendance_time_minutes: float | None
    resolution_time_minutes: float | None
    response_breached: bool
    attendance_breached: bool
    resolution_breached: bool
    warning_state: str
    sla_status_summary: str
    computed_at: datetime


# --- Commercial review workflow ---


class ContractReviewCreateIn(BaseModel):
    review_type: Literal["renewal", "repricing", "health_review", "risk_review"]
    triggered_reason: str = Field(..., min_length=3)
    summary: str = Field(..., min_length=3)
    priority: str = "normal"
    due_at: datetime | None = None
    notes: str | None = None
    assigned_to_user_id: str | None = None
    triggered_by: str = "manual"
    metadata: dict[str, Any] | None = None
    source_recommendation_id: str | None = None


class ContractReviewPatchIn(BaseModel):
    status: str | None = None
    assigned_to_user_id: str | None = None
    priority: str | None = None
    due_at: datetime | None = None
    notes: str | None = None
    summary: str | None = None


class ContractReviewDecisionIn(BaseModel):
    decision: Literal[
        "renew_as_is",
        "renew_with_repricing",
        "monitor",
        "escalate",
        "exit_contract",
        "defer",
    ]
    notes: str | None = None


class ContractReviewOut(BaseModel):
    id: str
    contract_id: str
    review_type: str
    status: str
    triggered_by: str
    triggered_reason: str
    opened_at: datetime
    due_at: datetime | None
    assigned_to_user_id: str | None
    priority: str
    summary: str
    notes: str | None
    decision: str | None
    decided_at: datetime | None
    decided_by_user_id: str | None
    metadata_json: dict[str, Any] | None = None
    source_recommendation_id: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, r: Any) -> ContractReviewOut:
        import json

        meta = None
        if r.metadata_json:
            try:
                meta = json.loads(r.metadata_json)
                if not isinstance(meta, dict):
                    meta = None
            except Exception:
                meta = None
        return cls(
            id=r.id,
            contract_id=r.contract_id,
            review_type=r.review_type,
            status=r.status,
            triggered_by=r.triggered_by,
            triggered_reason=r.triggered_reason,
            opened_at=r.opened_at,
            due_at=r.due_at,
            assigned_to_user_id=r.assigned_to_user_id,
            priority=r.priority,
            summary=r.summary,
            notes=r.notes,
            decision=r.decision,
            decided_at=r.decided_at,
            decided_by_user_id=r.decided_by_user_id,
            metadata_json=meta,
            source_recommendation_id=r.source_recommendation_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )


class ReviewFromRecommendationIn(BaseModel):
    recommendation_id: str = Field(..., min_length=8)
    review_type: str | None = None


class RepricingReviewCreateIn(BaseModel):
    current_contract_value: float | None = None
    proposed_contract_value: float | None = None
    repricing_reason_codes: list[str] = Field(default_factory=list)
    margin_summary: dict[str, Any] | None = None
    burden_summary: dict[str, Any] | None = None
    recommendation_basis: dict[str, Any] | None = None
    customer_risk_level: str = "medium"
    notes: str | None = None


class RepricingReviewPatchIn(BaseModel):
    proposed_contract_value: float | None = None
    current_contract_value: float | None = None
    repricing_reason_codes: list[str] | None = None
    margin_summary: dict[str, Any] | None = None
    burden_summary: dict[str, Any] | None = None
    recommendation_basis: dict[str, Any] | None = None
    customer_risk_level: str | None = None
    notes: str | None = None
    approved: bool | None = None


class RepricingReviewOut(BaseModel):
    id: str
    contract_id: str
    review_id: str
    current_contract_value: float | None
    proposed_contract_value: float | None
    repricing_reason_codes: list[str]
    margin_summary: dict[str, Any] | None = None
    burden_summary: dict[str, Any] | None = None
    recommendation_basis: dict[str, Any] | None = None
    customer_risk_level: str
    approved: bool | None
    approved_at: datetime | None
    approved_by_user_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    latest_proposal_id: str | None = None
    latest_proposal_reference: str | None = None
    latest_proposal_status: str | None = None

    @classmethod
    def from_row(cls, r: Any) -> RepricingReviewOut:
        import json

        codes: list[str] = []
        if r.repricing_reason_codes_json:
            try:
                raw = json.loads(r.repricing_reason_codes_json)
                if isinstance(raw, list):
                    codes = [str(x) for x in raw]
            except Exception:
                codes = []

        def _pj(s: str | None) -> dict[str, Any] | None:
            if not s:
                return None
            try:
                o = json.loads(s)
                return o if isinstance(o, dict) else None
            except Exception:
                return None

        return cls(
            id=r.id,
            contract_id=r.contract_id,
            review_id=r.review_id,
            current_contract_value=r.current_contract_value,
            proposed_contract_value=r.proposed_contract_value,
            repricing_reason_codes=codes,
            margin_summary=_pj(r.margin_summary_json),
            burden_summary=_pj(r.burden_summary_json),
            recommendation_basis=_pj(r.recommendation_basis_json),
            customer_risk_level=r.customer_risk_level,
            approved=r.approved,
            approved_at=r.approved_at,
            approved_by_user_id=r.approved_by_user_id,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at,
            latest_proposal_id=None,
            latest_proposal_reference=None,
            latest_proposal_status=None,
        )


class RepricingProposalLineOut(BaseModel):
    id: str
    proposal_id: str
    line_type: str
    code: str | None
    title: str
    description: str | None
    quantity: float
    unit: str
    current_unit_price: float | None
    proposed_unit_price: float | None
    current_line_total: float | None
    proposed_line_total: float
    variance_amount: float | None
    variance_percent: float | None
    justification_json: dict[str, Any] | None = None
    sort_order: int
    created_at: datetime

    @classmethod
    def from_row(cls, ln: Any) -> RepricingProposalLineOut:
        import json

        jj = None
        if ln.justification_json:
            try:
                o = json.loads(ln.justification_json)
                jj = o if isinstance(o, dict) else None
            except Exception:
                jj = None
        return cls(
            id=ln.id,
            proposal_id=ln.proposal_id,
            line_type=ln.line_type,
            code=ln.code,
            title=ln.title,
            description=ln.description,
            quantity=float(ln.quantity),
            unit=ln.unit,
            current_unit_price=ln.current_unit_price,
            proposed_unit_price=ln.proposed_unit_price,
            current_line_total=ln.current_line_total,
            proposed_line_total=float(ln.proposed_line_total),
            variance_amount=ln.variance_amount,
            variance_percent=ln.variance_percent,
            justification_json=jj,
            sort_order=int(ln.sort_order),
            created_at=ln.created_at,
        )


class RepricingProposalOut(BaseModel):
    id: str
    contract_id: str
    repricing_review_id: str
    review_id: str | None
    proposal_status: str
    proposal_reference: str
    currency: str
    current_contract_value: float | None
    proposed_contract_value: float | None
    effective_date: datetime | None
    validity_end_date: datetime | None
    generated_at: datetime
    generated_by_user_id: str | None
    approved_at: datetime | None
    approved_by_user_id: str | None
    ready_for_customer_at: datetime | None
    superseded_by_proposal_id: str | None
    notes: str | None
    pricing_basis: dict[str, Any] = Field(default_factory=dict)
    change_summary: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] | None = None
    stored_document_id: str | None = None
    customer_release_status: str = "not_released"
    released_to_customer_at: datetime | None = None
    released_by_user_id: str | None = None
    customer_viewed_at: datetime | None = None
    customer_responded_at: datetime | None = None
    customer_response_status: str | None = None
    customer_response_notes: str | None = None
    customer_response_by_contact: str | None = None
    customer_expiry_at: datetime | None = None
    portal_visibility_scope: str | None = None
    formal_acceptance_record_id: str | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[RepricingProposalLineOut] = Field(default_factory=list)

    @classmethod
    def from_row(cls, p: Any, *, lines: list[Any] | None = None) -> RepricingProposalOut:
        import json

        def _pj(s: str | None) -> dict[str, Any]:
            if not s:
                return {}
            try:
                o = json.loads(s)
                return o if isinstance(o, dict) else {}
            except Exception:
                return {}

        meta = None
        if p.metadata_json:
            try:
                m = json.loads(p.metadata_json)
                meta = m if isinstance(m, dict) else None
            except Exception:
                meta = None
        return cls(
            id=p.id,
            contract_id=p.contract_id,
            repricing_review_id=p.repricing_review_id,
            review_id=p.review_id,
            proposal_status=p.proposal_status,
            proposal_reference=p.proposal_reference,
            currency=p.currency,
            current_contract_value=p.current_contract_value,
            proposed_contract_value=p.proposed_contract_value,
            effective_date=p.effective_date,
            validity_end_date=p.validity_end_date,
            generated_at=p.generated_at,
            generated_by_user_id=p.generated_by_user_id,
            approved_at=p.approved_at,
            approved_by_user_id=p.approved_by_user_id,
            ready_for_customer_at=p.ready_for_customer_at,
            superseded_by_proposal_id=p.superseded_by_proposal_id,
            notes=p.notes,
            pricing_basis=_pj(p.pricing_basis_json),
            change_summary=_pj(p.change_summary_json),
            metadata_json=meta,
            stored_document_id=p.stored_document_id,
            customer_release_status=getattr(p, "customer_release_status", None) or "not_released",
            released_to_customer_at=getattr(p, "released_to_customer_at", None),
            released_by_user_id=getattr(p, "released_by_user_id", None),
            customer_viewed_at=getattr(p, "customer_viewed_at", None),
            customer_responded_at=getattr(p, "customer_responded_at", None),
            customer_response_status=getattr(p, "customer_response_status", None),
            customer_response_notes=getattr(p, "customer_response_notes", None),
            customer_response_by_contact=getattr(p, "customer_response_by_contact", None),
            customer_expiry_at=getattr(p, "customer_expiry_at", None),
            portal_visibility_scope=getattr(p, "portal_visibility_scope", None),
            formal_acceptance_record_id=getattr(p, "formal_acceptance_record_id", None),
            created_at=p.created_at,
            updated_at=p.updated_at,
            lines=[RepricingProposalLineOut.from_row(x) for x in (lines or [])],
        )


class CustomerProposalReleaseIn(BaseModel):
    release_notes: str | None = None
    customer_expiry_at: datetime | None = None


class CustomerProposalWithdrawIn(BaseModel):
    reason: str | None = None


class RepricingProposalCreateIn(BaseModel):
    repricing_review_id: str
    supersede_previous: bool = False
    currency: str = "GBP"


class RepricingProposalPatchIn(BaseModel):
    notes: str | None = None
    effective_date: datetime | None = None
    validity_end_date: datetime | None = None
    metadata_json: dict[str, Any] | None = None


class CommercialActionLogOut(BaseModel):
    id: str
    contract_id: str
    review_id: str | None
    action_type: str
    action_summary: str
    performed_by_user_id: str
    performed_at: datetime
    notes: str | None
    payload_json: dict[str, Any] | None = None

    @classmethod
    def from_row(cls, r: Any) -> CommercialActionLogOut:
        import json

        pj = None
        if r.payload_json:
            try:
                pj = json.loads(r.payload_json)
                if not isinstance(pj, dict):
                    pj = None
            except Exception:
                pj = None
        return cls(
            id=r.id,
            contract_id=r.contract_id,
            review_id=r.review_id,
            action_type=r.action_type,
            action_summary=r.action_summary,
            performed_by_user_id=r.performed_by_user_id,
            performed_at=r.performed_at,
            notes=r.notes,
            payload_json=pj,
        )


# --- Contract Amendment / Activation ---


class AmendmentCreateFromProposalIn(BaseModel):
    effective_date: datetime | None = None
    notes: str | None = None


class AmendmentPatchIn(BaseModel):
    notes: str | None = None


class AmendmentApproveIn(BaseModel):
    notes: str | None = None


class AmendmentRejectIn(BaseModel):
    notes: str | None = None


class AmendmentOut(BaseModel):
    id: str
    contract_id: str
    source_proposal_id: str | None
    source_review_id: str | None
    amendment_type: str
    status: str
    amendment_reference: str
    current_contract_value: float | None
    proposed_contract_value: float | None
    effective_date: datetime
    activated_at: datetime | None
    activated_by_user_id: str | None
    approved_at: datetime | None
    approved_by_user_id: str | None
    approval_required: bool
    created_at: datetime
    created_by_user_id: str | None
    notes: str | None
    resulting_contract_version_id: str | None = None

    model_config = {"from_attributes": True}


class ContractVersionOut(BaseModel):
    id: str
    contract_id: str
    version_number: int
    source_amendment_id: str | None
    version_type: str
    effective_from: datetime
    effective_to: datetime | None
    created_at: datetime
    created_by_user_id: str | None
    contract_value: float | None
    renewal_status: str | None
    renewal_decision: str | None
    repricing_required: bool | None
    account_attention_level: str | None
    churn_risk_level: str | None
    notes: str | None = None
    is_active: bool = False
    change_summary: dict[str, Any] | None = None
    human_readable_summary: str | None = None
    snapshot_json: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class ContractActivationRunOut(BaseModel):
    id: str
    amendment_id: str
    contract_id: str
    run_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    triggered_by_user_id: str | None
    attempt_number: int
    result_summary: str | None
    error_json: dict[str, Any] | None = None
    idempotency_key: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class RunScheduledActivationsIn(BaseModel):
    dry_run: bool = False
    limit: int | None = None


class AmendmentReadinessOut(BaseModel):
    ready: bool
    blocking_reasons: list[str]
    blocking_reason_messages: list[str] = Field(default_factory=list)
    warnings: list[str]
    required_approval: bool
    effective_date_candidate: datetime | None
    proposal_id: str | None = None
    acceptance_policy_mode: str = "warn_only"
    policy_amendment_requirements: list[str] = Field(default_factory=list)
    policy_activation_requirements: list[str] = Field(default_factory=list)


class AcceptancePolicyMatrixRowOut(BaseModel):
    mode: str
    label: str
    blocks_amendment_on: list[str]
    blocks_activation_on: list[str]
    customer_evidence: str
    notes: str | None = None


class AcceptancePolicyMatrixOut(BaseModel):
    current_mode: str
    rows: list[AcceptancePolicyMatrixRowOut]


class ActivationConfirmationOut(BaseModel):
    id: str
    contract_id: str
    amendment_id: str
    contract_version_id: str | None
    source_proposal_id: str | None
    status: str
    confirmation_reference: str
    effective_date: datetime
    activated_at: datetime
    confirmation_generated_at: datetime | None
    released_to_customer_at: datetime | None
    released_by_user_id: str | None
    customer_viewed_at: datetime | None
    customer_acknowledged_at: datetime | None
    customer_acknowledged_by_contact: str | None
    customer_acknowledgement_notes: str | None
    portal_visibility_scope: str | None
    stored_document_id: str | None
    summary_json: dict[str, Any] | None = None
    notes: str | None
    created_at: datetime
    created_by_user_id: str | None

    model_config = {"from_attributes": True}

    @field_validator("summary_json", mode="before")
    @classmethod
    def _parse_summary_json(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                out = json.loads(v)
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class ActivationConfirmationNotesIn(BaseModel):
    notes: str | None = None


class ActivationConfirmationWithdrawIn(BaseModel):
    reason: str | None = None


class ActivationConfirmationTimelineEventOut(BaseModel):
    at: str | None
    event_type: str
    summary: str


class ContractCustomerCommunicationOut(BaseModel):
    id: str
    contract_id: str
    source_entity_type: str
    source_entity_id: str
    communication_type: str
    status: str
    channel: str
    subject: str | None
    body_text: str | None
    body_html: str | None
    template_key: str | None
    recipient_customer_id: str | None
    recipient_contact_reference: str | None
    created_at: datetime
    created_by_user_id: str | None
    ready_at: datetime | None
    sent_at: datetime | None
    failed_at: datetime | None
    cancelled_at: datetime | None
    approved_at: datetime | None
    approved_by_user_id: str | None
    requires_approval: bool
    error_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    stored_document_id: str | None
    source_proposal_id: str | None
    source_amendment_id: str | None
    source_activation_confirmation_id: str | None

    model_config = {"from_attributes": True}

    @field_validator("error_json", "metadata_json", mode="before")
    @classmethod
    def _parse_json_dict(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                out = json.loads(v)
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class CustomerCommunicationCancelIn(BaseModel):
    reason: str | None = None


class CustomerCommunicationSendIn(BaseModel):
    """§5.14 optional break-glass send despite recipient suppression."""

    break_glass_override_suppression: bool = False
    break_glass_reason: str | None = None


class CustomerCommunicationFailedIn(BaseModel):
    error_message: str


class ContractCustomerCommunicationDeliveryOut(BaseModel):
    id: str
    communication_id: str
    channel: str
    provider_name: str
    provider_message_id: str | None
    attempt_number: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    recipient_address: str | None
    error_code: str | None
    error_message: str | None
    response_payload_json: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @field_validator("response_payload_json", mode="before")
    @classmethod
    def _parse_response_json(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                o = json.loads(v)
                return o if isinstance(o, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class CommunicationProviderEventOut(BaseModel):
    id: str
    provider_name: str
    event_type: str
    provider_message_id: str | None
    communication_id: str | None
    delivery_id: str | None
    recipient_address: str | None
    occurred_at: datetime | None
    received_at: datetime
    status: str
    normalized_status: str | None
    processing_status: str
    error_message: str | None
    external_event_id: str | None = None
    processing_result_json: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @field_validator("processing_result_json", mode="before")
    @classmethod
    def _parse_processing_json(cls, v: Any) -> dict[str, Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                o = json.loads(v)
                return o if isinstance(o, dict) else None
            except json.JSONDecodeError:
                return None
        return None


class RepricingCustomerResponseFollowUpIn(BaseModel):
    response_type: Literal["rejected", "counter_requested"]


class ContractFollowUpNoticeIn(BaseModel):
    internal_note: str


class ProposalAcceptanceRecordOut(BaseModel):
    """Internal view of formal acceptance (includes evidence for audit)."""

    id: str
    proposal_id: str
    contract_id: str
    customer_id: str
    source_proposal_reference: str | None = None
    acceptance_status: str
    acceptance_type: str
    acceptance_channel: str
    initiated_at: datetime | None = None
    completed_at: datetime | None = None
    accepted_by_contact: str | None = None
    accepted_by_customer_user_id: str | None = None
    acceptance_ip: str | None = None
    acceptance_user_agent: str | None = None
    acceptance_notes: str | None = None
    signed_name: str | None = None
    signed_title: str | None = None
    signed_email: str | None = None
    immutable_hash: str | None = None
    evidence_json: dict[str, Any] | None = None
    amendment_id: str | None = None
    created_at: datetime | None = None
    created_by_user_id: str | None = None
    acceptance_evidence_type: Literal["in_product_acceptance", "provider_esign", "acknowledgement_only"] | str = (
        "in_product_acceptance"
    )
    provider_name: str | None = None
    provider_envelope_id: str | None = None
    provider_session_id: str | None = None
    provider_status: str | None = None
    provider_completed_at: datetime | None = None

    @classmethod
    def from_row(cls, r: Any) -> ProposalAcceptanceRecordOut:
        ev: dict[str, Any] | None = None
        if r.evidence_json:
            try:
                o = json.loads(r.evidence_json)
                ev = o if isinstance(o, dict) else None
            except Exception:
                ev = None
        return cls(
            id=r.id,
            proposal_id=r.proposal_id,
            contract_id=r.contract_id,
            customer_id=r.customer_id,
            source_proposal_reference=r.source_proposal_reference,
            acceptance_status=r.acceptance_status,
            acceptance_type=r.acceptance_type,
            acceptance_channel=r.acceptance_channel,
            initiated_at=r.initiated_at,
            completed_at=r.completed_at,
            accepted_by_contact=r.accepted_by_contact,
            accepted_by_customer_user_id=r.accepted_by_customer_user_id,
            acceptance_ip=r.acceptance_ip,
            acceptance_user_agent=r.acceptance_user_agent,
            acceptance_notes=r.acceptance_notes,
            signed_name=r.signed_name,
            signed_title=r.signed_title,
            signed_email=r.signed_email,
            immutable_hash=r.immutable_hash,
            evidence_json=ev,
            amendment_id=r.amendment_id,
            created_at=r.created_at,
            created_by_user_id=r.created_by_user_id,
            acceptance_evidence_type=getattr(r, "acceptance_evidence_type", None) or "in_product_acceptance",
            provider_name=getattr(r, "provider_name", None),
            provider_envelope_id=getattr(r, "provider_envelope_id", None),
            provider_session_id=getattr(r, "provider_session_id", None),
            provider_status=getattr(r, "provider_status", None),
            provider_completed_at=getattr(r, "provider_completed_at", None),
        )


class ProposalAcceptanceSessionOut(BaseModel):
    id: str
    proposal_id: str
    acceptance_record_id: str | None = None
    session_status: str
    expires_at: datetime | None = None
    created_at: datetime | None = None
    created_by_user_id: str | None = None
    last_accessed_at: datetime | None = None
    completed_at: datetime | None = None
    has_secure_token: bool = False
    metadata_json: dict[str, Any] | None = None
    esign_provider_flow: bool = False

    @classmethod
    def from_row(cls, s: Any) -> ProposalAcceptanceSessionOut:
        meta: dict[str, Any] | None = None
        if s.metadata_json:
            try:
                o = json.loads(s.metadata_json)
                meta = o if isinstance(o, dict) else None
            except Exception:
                meta = None
        return cls(
            id=s.id,
            proposal_id=s.proposal_id,
            acceptance_record_id=s.acceptance_record_id,
            session_status=s.session_status,
            expires_at=s.expires_at,
            created_at=s.created_at,
            created_by_user_id=s.created_by_user_id,
            last_accessed_at=s.last_accessed_at,
            completed_at=s.completed_at,
            has_secure_token=bool(s.token_hash),
            metadata_json=meta,
            esign_provider_flow=bool(getattr(s, "esign_provider_flow", False)),
        )


class ProposalAcceptanceProviderStatusOut(BaseModel):
    """Internal support view: correlation IDs and lifecycle — not raw provider secrets/payloads."""

    acceptance_record_id: str
    proposal_id: str
    provider_name: str | None = None
    provider_status: str | None = None
    provider_envelope_id: str | None = None
    provider_completed_at: datetime | None = None
    acceptance_status: str
    acceptance_evidence_type: str | None = None
    stored_payload_top_level_keys: list[str] = Field(default_factory=list)
    last_connect_event: str | None = None
    last_webhook_generated_at: str | None = None


class ProviderEsignSessionCreateIn(BaseModel):
    expires_at: datetime | None = None
    signer_email: str | None = None
    signer_name: str | None = None


class ProviderEsignSessionCreateOut(BaseModel):
    acceptance_record_id: str
    session_id: str
    signing_url: str
    provider: str
    provider_envelope_id: str
    expires_at: str


class CommercialFollowUpProposalRowOut(BaseModel):
    proposal_id: str
    contract_id: str
    proposal_reference: str | None = None
    reason_code: str
    stale_days: int | None = None
    acceptance_record_id: str | None = None


class CommercialFollowUpActivationRowOut(BaseModel):
    confirmation_id: str
    contract_id: str
    confirmation_reference: str | None = None
    reason_code: str
    stale_days: int | None = None


class CommercialFollowUpDraftCommRowOut(BaseModel):
    communication_id: str
    contract_id: str
    communication_type: str
    status: str
    source_entity_type: str
    source_entity_id: str
    stale_days: int | None = None


class CommercialFollowUpNeedsActionOut(BaseModel):
    generated_at: str
    thresholds: dict[str, int]
    proposals: list[CommercialFollowUpProposalRowOut]
    activation_confirmations: list[CommercialFollowUpActivationRowOut]
    draft_customer_comms: list[CommercialFollowUpDraftCommRowOut]


class ProposalAcceptanceSessionCreateIn(BaseModel):
    acceptance_type: Literal["portal_acceptance", "token_link_acceptance", "acknowledgement_only"]
    expires_at: datetime | None = None
    issue_secure_token: bool = False
    metadata_json: dict[str, Any] | None = None


class ProposalAcceptanceSessionCreateOut(BaseModel):
    acceptance_record: ProposalAcceptanceRecordOut
    session: ProposalAcceptanceSessionOut
    plain_token: str | None = Field(
        default=None,
        description="Returned once when a secure token is issued; never stored server-side.",
    )
