from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.services.authorization_policy import (
    CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND,
    CAN_APPROVE_REPRICING,
    CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION,
    CAN_DECIDE_CONTRACT_REVIEW,
    CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION,
    CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
)
from backend.app.services.authorization_service import require_permission_http
from backend.app.services import scoped_access_service as scoped_access
from backend.app.modules.contracts.operational_views import (
    contract_jobs_summary,
    contract_ppm_summary,
    contracts_attention_dashboard,
)
from backend.app.modules.contracts import contract_review_service as review_service
from backend.app.modules.contracts.schemas import (
    AmendmentApproveIn,
    AmendmentCreateFromProposalIn,
    AmendmentOut,
    AmendmentPatchIn,
    ActivationConfirmationNotesIn,
    ActivationConfirmationOut,
    ActivationConfirmationTimelineEventOut,
    ActivationConfirmationWithdrawIn,
    ContractCustomerCommunicationDeliveryOut,
    ContractCustomerCommunicationOut,
    ContractFollowUpNoticeIn,
    CustomerCommunicationCancelIn,
    CustomerCommunicationFailedIn,
    CustomerCommunicationSendIn,
    RepricingCustomerResponseFollowUpIn,
    AcceptancePolicyMatrixOut,
    AcceptancePolicyMatrixRowOut,
    AmendmentReadinessOut,
    AmendmentRejectIn,
    ContractActivationRunOut,
    ContractVersionOut,
    RunScheduledActivationsIn,
    CommunicationProviderEventOut,
    CommercialActionLogOut,
    CommercialFollowUpNeedsActionOut,
    ContractCreateIn,
    ContractOut,
    ContractManualUpdateOut,
    ContractPatchIn,
    ContractReviewCreateIn,
    ContractReviewDecisionIn,
    ContractReviewOut,
    ContractReviewPatchIn,
    CustomerProposalReleaseIn,
    CustomerProposalWithdrawIn,
    ProposalAcceptanceProviderStatusOut,
    ProposalAcceptanceRecordOut,
    ProposalAcceptanceSessionCreateIn,
    ProposalAcceptanceSessionCreateOut,
    ProposalAcceptanceSessionOut,
    ProviderEsignSessionCreateIn,
    ProviderEsignSessionCreateOut,
    RepricingProposalCreateIn,
    RepricingProposalOut,
    RepricingProposalPatchIn,
    RepricingReviewCreateIn,
    RepricingReviewOut,
    RepricingReviewPatchIn,
    ReviewFromRecommendationIn,
    SlaBreachRiskOut,
)
from backend.app.modules.contracts.service import (
    compute_sla_breach_risk,
    create_contract,
    generate_due_ppm_jobs_for_contract,
    get_contract,
    list_contracts,
)
from backend.app.modules.contracts.sla_clock_service import aggregate_contract_sla_performance
from backend.app.services import contract_profitability_service as contract_intel
from backend.app.services import commercial_follow_up_needs_action_service as cfna
from backend.app.services import customer_repricing_proposal_service as crps
from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts import amendment_service as ams
from backend.app.services import contract_activation_confirmation_service as acconf
from backend.app.services import communication_provider_event_service as comm_prov_events
from backend.app.services import communication_recipient_suppression_service as comm_hygiene
from backend.app.services import contract_customer_communication_service as ccc_svc
from backend.app.services import contract_activation_scheduler_service as casc
from backend.app.services import contract_version_readable_service as cvread
from backend.app.services import contract_version_service as cvs
from backend.app.services.contract_version_service import execute_amendment_activation
from backend.app.services import acceptance_policy_service as apol
from backend.app.services import proposal_acceptance_esign_service as paes
from backend.app.services import proposal_acceptance_service as pas
from backend.app.services import repricing_proposal_service as rps
from backend.app.modules.documents.persist import persist_repricing_proposal_pdf
from backend.app.modules.documents.schemas import StoredDocumentOut
from backend.app.modules.documents.service import stored_document_out_from_row

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _repricing_review_out_with_latest(db: Session, rr) -> RepricingReviewOut:
    out = RepricingReviewOut.from_row(rr)
    lp = rps.latest_proposal_for_repricing_review(db, repricing_review_id=rr.id)
    if lp:
        return out.model_copy(
            update={
                "latest_proposal_id": lp.id,
                "latest_proposal_reference": lp.proposal_reference,
                "latest_proposal_status": lp.proposal_status,
            }
        )
    return out


def require_commercial_ready_user(user: User = Depends(get_current_user)) -> User:
    if not set(user.role_names()) & {"Admin", "Commercial"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Commercial required")
    return user


def require_repricing_internal_approve_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if "Admin" in user.role_names():
        return user
    require_permission_http(user, CAN_APPROVE_REPRICING, db=db)
    return user


@router.post("", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
def create_contract_endpoint(
    payload: ContractCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> ContractOut:
    try:
        return create_contract(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/attention")
def contracts_attention_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    return contracts_attention_dashboard(db)


@router.get("", response_model=list[ContractOut])
def list_contracts_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> list[ContractOut]:
    rows = list_contracts(db)
    rows = scoped_access.filter_contracts_for_internal_user(db, current_user, rows)
    return rows


@router.get("/dashboard/profitability")
def contracts_dashboard_profitability_endpoint(
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    return contract_intel.dashboard_profitability(db, period_window=period_window, limit=limit)


@router.get("/dashboard/renewals")
def contracts_dashboard_renewals_endpoint(
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    return contract_intel.dashboard_renewals(db, period_window=period_window, limit=limit)


@router.get("/dashboard/attention-summary")
def contracts_dashboard_attention_summary_endpoint(
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    limit: int = Query(default=30, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    return contract_intel.dashboard_attention_summary(db, period_window=period_window, limit=limit)


@router.post("/performance/run-snapshot")
def contracts_run_performance_snapshot_endpoint(
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    contract_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    if contract_id:
        if not get_contract(db, contract_id=contract_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        row = contract_intel.persist_performance_snapshot(db, contract_id=contract_id, period_window=period_window)
        return {"snapshot_id": row.id, "contract_id": contract_id}
    return contract_intel.run_snapshots_all_active(db, period_window=period_window)


# --- Static paths must be registered before /{contract_id} (avoid "reviews" parsed as id) ---


@router.get("/dashboard/review-pipeline")
def contracts_dashboard_review_pipeline_endpoint(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_to_user_id: str | None = Query(default=None),
    review_type: str | None = Query(default=None),
    due_within_days: int | None = Query(default=None, le=365),
    unassigned_only: bool = Query(default=False),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    core = review_service.dashboard_review_pipeline(
        db,
        status=status,
        priority=priority,
        assigned_to_user_id=assigned_to_user_id,
        review_type=review_type,
        due_within_days=due_within_days,
        unassigned_only=unassigned_only,
        limit=limit,
    )
    core["recently_completed"] = review_service.list_recent_completed_reviews(db, limit=20)
    return core


@router.get("/dashboard/repricing")
def contracts_dashboard_repricing_endpoint(
    approved: bool | None = Query(default=None),
    customer_risk_level: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    return review_service.dashboard_repricing(
        db, approved=approved, customer_risk_level=customer_risk_level, limit=limit
    )


_REPRICING_PROPOSAL_ROLES = ("Admin", "Dispatcher", "Commercial", "Finance")


def _proposal_out(db: Session, p) -> RepricingProposalOut:
    return RepricingProposalOut.from_row(p, lines=rps.list_lines(db, proposal_id=p.id))


def _get_repricing_proposal_or_404(db: Session, proposal_id: str):
    p = rps.get_proposal(db, proposal_id=proposal_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return p


@router.get("/dashboard/repricing-proposals")
def contracts_dashboard_repricing_proposals_endpoint(
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return rps.dashboard_repricing_proposals(db, limit=limit)


@router.get("/dashboard/repricing-readiness")
def contracts_dashboard_repricing_readiness_endpoint(
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return rps.dashboard_repricing_readiness(db, limit=limit)


@router.get("/repricing-proposals/{proposal_id}", response_model=RepricingProposalOut)
def get_repricing_proposal_global_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> RepricingProposalOut:
    p = _get_repricing_proposal_or_404(db, proposal_id)
    return _proposal_out(db, p)


@router.patch("/repricing-proposals/{proposal_id}", response_model=RepricingProposalOut)
def patch_repricing_proposal_global_endpoint(
    proposal_id: str,
    payload: RepricingProposalPatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    data = payload.model_dump(exclude_unset=True)
    try:
        p = rps.patch_proposal(db, proposal_id=proposal_id, user_id=current_user.id, **data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.post("/repricing-proposals/{proposal_id}/generate-pdf", response_model=StoredDocumentOut)
def generate_repricing_proposal_pdf_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> StoredDocumentOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        row = persist_repricing_proposal_pdf(
            db, proposal_id=proposal_id, uploaded_by_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return stored_document_out_from_row(row)


@router.post("/repricing-proposals/{proposal_id}/mark-internal-review", response_model=RepricingProposalOut)
def mark_repricing_proposal_internal_review_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        p = rps.mark_internal_review(db, proposal_id=proposal_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.post("/repricing-proposals/{proposal_id}/approve-internal", response_model=RepricingProposalOut)
def approve_repricing_proposal_internal_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        p = rps.approve_internal(db, proposal_id=proposal_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.post("/repricing-proposals/{proposal_id}/mark-ready-for-customer", response_model=RepricingProposalOut)
def mark_repricing_proposal_ready_for_customer_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        p = rps.mark_ready_for_customer(db, proposal_id=proposal_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.post("/repricing-proposals/{proposal_id}/release-to-customer", response_model=RepricingProposalOut)
def release_repricing_proposal_to_customer_endpoint(
    proposal_id: str,
    payload: CustomerProposalReleaseIn = CustomerProposalReleaseIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        p = crps.release_proposal_to_customer(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            release_notes=payload.release_notes,
            customer_expiry_at=payload.customer_expiry_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.post("/repricing-proposals/{proposal_id}/withdraw-customer-release", response_model=RepricingProposalOut)
def withdraw_repricing_proposal_customer_release_endpoint(
    proposal_id: str,
    payload: CustomerProposalWithdrawIn = CustomerProposalWithdrawIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> RepricingProposalOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        p = crps.withdraw_customer_proposal(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            reason=payload.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.get("/repricing-proposals/{proposal_id}/timeline")
def internal_repricing_proposal_timeline_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[dict]:
    _get_repricing_proposal_or_404(db, proposal_id)
    return crps.build_internal_proposal_timeline(db, proposal_id=proposal_id)


@router.get(
    "/repricing-proposals/{proposal_id}/acceptance-records",
    response_model=list[ProposalAcceptanceRecordOut],
)
def list_proposal_acceptance_records_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[ProposalAcceptanceRecordOut]:
    _get_repricing_proposal_or_404(db, proposal_id)
    rows = pas.list_acceptance_records_for_proposal(db, proposal_id=proposal_id)
    return [ProposalAcceptanceRecordOut.from_row(r) for r in rows]


@router.get(
    "/acceptance-records/{acceptance_record_id}",
    response_model=ProposalAcceptanceRecordOut,
)
def get_acceptance_record_endpoint(
    acceptance_record_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ProposalAcceptanceRecordOut:
    r = pas.get_acceptance_record(db, acceptance_record_id=acceptance_record_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceptance record not found")
    return ProposalAcceptanceRecordOut.from_row(r)


@router.get(
    "/acceptance-sessions/{session_id}",
    response_model=ProposalAcceptanceSessionOut,
)
def get_acceptance_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ProposalAcceptanceSessionOut:
    s = pas.get_acceptance_session(db, session_id=session_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceptance session not found")
    return ProposalAcceptanceSessionOut.from_row(s)


@router.post(
    "/repricing-proposals/{proposal_id}/acceptance-sessions",
    response_model=ProposalAcceptanceSessionCreateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_proposal_acceptance_session_endpoint(
    proposal_id: str,
    payload: ProposalAcceptanceSessionCreateIn = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> ProposalAcceptanceSessionCreateOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        rec, sess, tok = pas.create_proposal_acceptance_session(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            acceptance_type=payload.acceptance_type,
            expires_at=payload.expires_at,
            issue_secure_token=payload.issue_secure_token,
            metadata=payload.metadata_json,
        )
        db.commit()
        db.refresh(rec)
        db.refresh(sess)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ProposalAcceptanceSessionCreateOut(
        acceptance_record=ProposalAcceptanceRecordOut.from_row(rec),
        session=ProposalAcceptanceSessionOut.from_row(sess),
        plain_token=tok,
    )


@router.post(
    "/acceptance-sessions/{session_id}/cancel",
    response_model=ProposalAcceptanceSessionOut,
)
def cancel_proposal_acceptance_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> ProposalAcceptanceSessionOut:
    try:
        s = pas.cancel_acceptance_session(db, session_id=session_id, actor_user_id=current_user.id)
        db.commit()
        db.refresh(s)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ProposalAcceptanceSessionOut.from_row(s)


@router.post(
    "/repricing-proposals/{proposal_id}/esign-sessions",
    response_model=ProviderEsignSessionCreateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_proposal_provider_esign_session_endpoint(
    proposal_id: str,
    payload: ProviderEsignSessionCreateIn = Body(default_factory=ProviderEsignSessionCreateIn),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> ProviderEsignSessionCreateOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        out = paes.create_provider_esign_session_for_proposal(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            expires_at=payload.expires_at,
            signer_email=payload.signer_email,
            signer_name=payload.signer_name,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ProviderEsignSessionCreateOut.model_validate(out)


@router.get(
    "/acceptance-records/{acceptance_record_id}/provider-status",
    response_model=ProposalAcceptanceProviderStatusOut,
)
def get_acceptance_record_provider_status_endpoint(
    acceptance_record_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ProposalAcceptanceProviderStatusOut:
    r = pas.get_acceptance_record(db, acceptance_record_id=acceptance_record_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceptance record not found")
    if r.acceptance_type != "provider_esign":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acceptance record is not a provider e-sign flow",
        )
    return ProposalAcceptanceProviderStatusOut.model_validate(paes.provider_status_internal_summary(r))


@router.post(
    "/acceptance-sessions/{session_id}/cancel-esign",
    response_model=ProposalAcceptanceSessionOut,
)
def cancel_provider_esign_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> ProposalAcceptanceSessionOut:
    try:
        s = paes.cancel_provider_esign_session(
            db, session_id=session_id, actor_user_id=current_user.id
        )
        db.commit()
        db.refresh(s)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ProposalAcceptanceSessionOut.from_row(s)


@router.get("/dashboard/esign-status")
def contracts_dashboard_esign_status_endpoint(
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return paes.dashboard_esign_status(db, limit=limit)


@router.get(
    "/dashboard/commercial-follow-up-needs-action",
    response_model=CommercialFollowUpNeedsActionOut,
)
def contracts_dashboard_commercial_follow_up_needs_action_endpoint(
    limit_per_section: int = Query(default=150, le=300),
    released_no_view_days: int = Query(default=7, ge=0, le=365),
    viewed_no_response_days: int = Query(default=7, ge=0, le=365),
    esign_incomplete_days: int = Query(default=5, ge=0, le=365),
    activation_released_not_viewed_days: int = Query(default=7, ge=0, le=365),
    activation_viewed_not_acknowledged_days: int = Query(default=7, ge=0, le=365),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> CommercialFollowUpNeedsActionOut:
    raw = cfna.dashboard_commercial_follow_up_needs_action(
        db,
        limit_per_section=limit_per_section,
        released_no_view_days=released_no_view_days,
        viewed_no_response_days=viewed_no_response_days,
        esign_incomplete_days=esign_incomplete_days,
        activation_released_not_viewed_days=activation_released_not_viewed_days,
        activation_viewed_not_acknowledged_days=activation_viewed_not_acknowledged_days,
    )
    return CommercialFollowUpNeedsActionOut.model_validate(raw)


@router.get("/dashboard/acceptance-policy-blockers")
def contracts_dashboard_acceptance_policy_blockers_endpoint(
    limit_proposals: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return apol.evaluate_policy_blockers_summary(db, limit_proposals=limit_proposals)


@router.get(
    "/dashboard/acceptance-policy-matrix",
    response_model=AcceptancePolicyMatrixOut,
)
def contracts_dashboard_acceptance_policy_matrix_endpoint(
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> AcceptancePolicyMatrixOut:
    mode = apol.acceptance_policy_mode()
    rows = [AcceptancePolicyMatrixRowOut.model_validate(r) for r in apol.acceptance_policy_matrix()]
    return AcceptancePolicyMatrixOut(current_mode=mode, rows=rows)


@router.get("/dashboard/accepted-proposals")
def contracts_dashboard_accepted_proposals_endpoint(
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return pas.dashboard_accepted_proposals(db, limit=limit)


@router.get("/dashboard/acceptance-awaiting-activation")
def contracts_dashboard_acceptance_awaiting_activation_endpoint(
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return pas.dashboard_acceptance_awaiting_activation(db, limit=limit)


@router.get("/dashboard/customer-proposals")
def contracts_dashboard_customer_proposals_endpoint(
    customer_release_status: str | None = Query(default=None),
    customer_response_status: str | None = Query(default=None),
    contract_id: str | None = Query(default=None),
    expiring_within_days: int | None = Query(default=None, le=365),
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return crps.dashboard_customer_proposals(
        db,
        customer_release_status=customer_release_status,
        customer_response_status=customer_response_status,
        contract_id=contract_id,
        expiring_within_days=expiring_within_days,
        limit=limit,
    )


@router.get("/dashboard/customer-proposal-follow-up")
def contracts_dashboard_customer_proposal_follow_up_endpoint(
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return crps.dashboard_customer_proposal_follow_up(db, limit=limit)


# --- Contract Amendment / Activation ---


@router.get("/repricing-proposals/{proposal_id}/activation-readiness", response_model=AmendmentReadinessOut)
def proposal_activation_readiness_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> AmendmentReadinessOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    return AmendmentReadinessOut.model_validate(ams.evaluate_proposal_activation_readiness(db, proposal_id=proposal_id))


@router.post(
    "/repricing-proposals/{proposal_id}/create-amendment",
    response_model=AmendmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_amendment_from_proposal_endpoint(
    proposal_id: str,
    payload: AmendmentCreateFromProposalIn = AmendmentCreateFromProposalIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> AmendmentOut:
    _get_repricing_proposal_or_404(db, proposal_id)
    try:
        a = ams.create_contract_amendment_from_proposal(
            db,
            proposal_id=proposal_id,
            actor_user_id=current_user.id,
            effective_date=payload.effective_date,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


def _activation_run_out(r) -> ContractActivationRunOut:
    import json

    ej = None
    if r.error_json:
        try:
            ej = json.loads(r.error_json)
            if not isinstance(ej, dict):
                ej = None
        except Exception:
            ej = None
    return ContractActivationRunOut(
        id=r.id,
        amendment_id=r.amendment_id,
        contract_id=r.contract_id,
        run_type=r.run_type,
        status=r.status,
        started_at=r.started_at,
        completed_at=r.completed_at,
        triggered_by_user_id=r.triggered_by_user_id,
        attempt_number=r.attempt_number,
        result_summary=r.result_summary,
        error_json=ej,
        idempotency_key=r.idempotency_key,
        notes=r.notes,
    )


@router.post("/amendments/run-scheduled-activations")
def run_scheduled_activations_endpoint(
    payload: RunScheduledActivationsIn = RunScheduledActivationsIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> dict:
    return casc.run_due_amendment_activations(
        db,
        now=None,
        limit=payload.limit,
        dry_run=payload.dry_run,
        actor_user_id=current_user.id,
    )


@router.get("/amendments/activation-runs", response_model=list[ContractActivationRunOut])
def list_activation_runs_endpoint(
    amendment_id: str | None = Query(default=None),
    contract_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[ContractActivationRunOut]:
    rows = casc.list_activation_runs(
        db,
        amendment_id=amendment_id,
        contract_id=contract_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_activation_run_out(r) for r in rows]


@router.get("/amendments/activation-runs/{run_id}", response_model=ContractActivationRunOut)
def get_activation_run_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ContractActivationRunOut:
    r = casc.get_activation_run(db, run_id=run_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activation run not found")
    return _activation_run_out(r)


@router.get("/amendments", response_model=list[AmendmentOut])
def list_amendments_endpoint(
    contract_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    amendment_type: str | None = Query(default=None),
    source_proposal_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[AmendmentOut]:
    rows = ams.list_amendments(
        db,
        contract_id=contract_id,
        status=status,
        amendment_type=amendment_type,
        source_proposal_id=source_proposal_id,
        limit=limit,
        offset=offset,
    )
    return [AmendmentOut.model_validate(r) for r in rows]


@router.get("/amendments/{amendment_id}", response_model=AmendmentOut)
def get_amendment_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> AmendmentOut:
    a = ams.get_amendment(db, amendment_id=amendment_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amendment not found")
    return AmendmentOut.model_validate(a)


@router.patch("/amendments/{amendment_id}", response_model=AmendmentOut)
def patch_amendment_endpoint(
    amendment_id: str,
    payload: AmendmentPatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commercial_ready_user),
) -> AmendmentOut:
    a = ams.get_amendment(db, amendment_id=amendment_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amendment not found")
    if a.status not in ("draft", "pending_approval", "scheduled", "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot patch amendment in status {a.status}",
        )
    if payload.notes is not None:
        a.notes = payload.notes
    db.commit()
    db.refresh(a)
    return AmendmentOut.model_validate(a)


@router.post("/amendments/{amendment_id}/submit-for-approval", response_model=AmendmentOut)
def submit_amendment_for_approval_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> AmendmentOut:
    try:
        a = ams.submit_for_approval(db, amendment_id=amendment_id, actor_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


@router.post("/amendments/{amendment_id}/approve", response_model=AmendmentOut)
def approve_amendment_endpoint(
    amendment_id: str,
    payload: AmendmentApproveIn = AmendmentApproveIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> AmendmentOut:
    try:
        a = ams.approve_amendment(
            db,
            amendment_id=amendment_id,
            actor_user_id=current_user.id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


@router.post("/amendments/{amendment_id}/reject", response_model=AmendmentOut)
def reject_amendment_endpoint(
    amendment_id: str,
    payload: AmendmentRejectIn = AmendmentRejectIn(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> AmendmentOut:
    try:
        a = ams.reject_amendment(
            db,
            amendment_id=amendment_id,
            actor_user_id=current_user.id,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


@router.post("/amendments/{amendment_id}/activate", response_model=AmendmentOut)
def activate_amendment_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> AmendmentOut:
    try:
        a = ams.activate_contract_amendment(
            db,
            amendment_id=amendment_id,
            actor_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


@router.post("/amendments/{amendment_id}/dry-run-activation")
def dry_run_amendment_activation_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return cvs.dry_run_activation_preview(db, amendment_id=amendment_id)


@router.post("/amendments/{amendment_id}/retry-activation", response_model=AmendmentOut)
def retry_amendment_activation_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_repricing_internal_approve_user),
) -> AmendmentOut:
    """Re-attempt activation (idempotent if already activated)."""
    try:
        a, _r = execute_amendment_activation(
            db,
            amendment_id=amendment_id,
            actor_user_id=current_user.id,
            run_type="manual",
            idempotency_key=None,
            commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AmendmentOut.model_validate(a)


@router.get("/dashboard/amendments")
def contracts_dashboard_amendments_endpoint(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return ams.dashboard_amendments(db, status=status, limit=limit)


@router.get("/dashboard/pending-activations")
def contracts_dashboard_pending_activations_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return ams.dashboard_pending_activations(db)


@router.get("/dashboard/accepted-proposals-awaiting-activation")
def contracts_dashboard_accepted_proposals_awaiting_activation_endpoint(
    contract_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[dict]:
    return ams.accepted_proposals_awaiting_activation(db, contract_id=contract_id, limit=limit)


@router.get("/dashboard/activations-due")
def contracts_dashboard_activations_due_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_activations_due(db)


@router.get("/dashboard/activation-failures")
def contracts_dashboard_activation_failures_endpoint(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_activation_failures(db, limit=limit)


@router.get("/dashboard/future-activations")
def contracts_dashboard_future_activations_endpoint(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_future_activations(db, limit=limit)


@router.get("/dashboard/version-history-summary")
def contracts_dashboard_version_history_summary_endpoint(
    limit: int = Query(default=30, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_version_history_summary(db, limit=limit)


@router.get("/dashboard/recent-contract-version-activity")
def contracts_dashboard_recent_contract_version_activity_endpoint(
    limit: int = Query(default=40, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return {"rows": cvread.recent_version_activity(db, limit=limit)}


@router.get("/dashboard/recently-updated-contracts")
def contracts_dashboard_recently_updated_contracts_endpoint(
    limit: int = Query(default=40, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_recently_updated_contracts(db, limit=limit)


@router.get("/dashboard/recently-activated-amendments")
def contracts_dashboard_recently_activated_amendments_endpoint(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return casc.dashboard_recently_activated_amendments(db, limit=limit)


@router.post(
    "/amendments/{amendment_id}/activation-confirmation",
    response_model=ActivationConfirmationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activation_confirmation_from_amendment_endpoint(
    amendment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    try:
        row = acconf.create_activation_confirmation_from_amendment(
            db, amendment_id=amendment_id, actor_user_id=current_user.id, commit=True
        )
        return ActivationConfirmationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/activation-confirmations", response_model=list[ActivationConfirmationOut])
def list_activation_confirmations_endpoint(
    contract_id: str | None = Query(default=None),
    amendment_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[ActivationConfirmationOut]:
    rows = acconf.list_confirmations_internal(
        db, contract_id=contract_id, amendment_id=amendment_id, status=status, limit=limit, offset=offset
    )
    return [ActivationConfirmationOut.model_validate(r) for r in rows]


@router.get("/activation-confirmations/{confirmation_id}", response_model=ActivationConfirmationOut)
def get_activation_confirmation_endpoint(
    confirmation_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    row = db.get(ContractActivationConfirmation, confirmation_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return ActivationConfirmationOut.model_validate(row)


@router.post("/activation-confirmations/{confirmation_id}/generate-pdf", response_model=ActivationConfirmationOut)
def generate_activation_confirmation_pdf_endpoint(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    try:
        row = acconf.generate_activation_confirmation_pdf(
            db, confirmation_id=confirmation_id, actor_user_id=current_user.id, commit=True
        )
        return ActivationConfirmationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/activation-confirmations/{confirmation_id}/mark-ready-for-customer", response_model=ActivationConfirmationOut)
def mark_activation_confirmation_ready_endpoint(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    try:
        row = acconf.mark_ready_for_customer(
            db, confirmation_id=confirmation_id, actor_user_id=current_user.id, commit=True
        )
        return ActivationConfirmationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/activation-confirmations/{confirmation_id}/release-to-customer", response_model=ActivationConfirmationOut)
def release_activation_confirmation_endpoint(
    confirmation_id: str,
    payload: ActivationConfirmationNotesIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    try:
        row = acconf.release_activation_confirmation_to_customer(
            db,
            confirmation_id=confirmation_id,
            actor_user_id=current_user.id,
            notes=payload.notes if payload else None,
            commit=True,
        )
        return ActivationConfirmationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/activation-confirmations/{confirmation_id}/withdraw-customer-release", response_model=ActivationConfirmationOut)
def withdraw_activation_confirmation_endpoint(
    confirmation_id: str,
    payload: ActivationConfirmationWithdrawIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ActivationConfirmationOut:
    try:
        row = acconf.withdraw_activation_confirmation_from_customer(
            db,
            confirmation_id=confirmation_id,
            actor_user_id=current_user.id,
            reason=payload.reason if payload else None,
            commit=True,
        )
        return ActivationConfirmationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/activation-confirmations")
def contracts_dashboard_activation_confirmations_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return acconf.dashboard_activation_confirmations(db)


@router.get("/dashboard/activations-awaiting-customer-confirmation")
def contracts_dashboard_activations_awaiting_customer_confirmation_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return acconf.dashboard_activations_awaiting_customer_confirmation(db)


@router.get("/dashboard/activation-confirmations-follow-up")
def contracts_dashboard_activation_confirmations_follow_up_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return acconf.dashboard_activation_confirmations_follow_up(db)


@router.get("/dashboard/activation-customer-lifecycle")
def contracts_dashboard_activation_customer_lifecycle_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    return acconf.dashboard_activation_customer_lifecycle(db)


def _require_view_customer_comms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION, db=db)
    return current_user


def _require_create_customer_comms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION, db=db)
    return current_user


def _require_send_customer_comms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION, db=db)
    return current_user


def _require_approve_customer_comms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND, db=db)
    return current_user


@router.get("/communications", response_model=list[ContractCustomerCommunicationOut])
def list_contract_customer_communications_endpoint(
    contract_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    communication_type: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    requires_approval: bool | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> list[ContractCustomerCommunicationOut]:
    rows = ccc_svc.list_communications(
        db,
        contract_id=contract_id,
        status=status,
        communication_type=communication_type,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        channel=channel,
        requires_approval=requires_approval,
        limit=limit,
        offset=offset,
    )
    return [ContractCustomerCommunicationOut.model_validate(r) for r in rows]


@router.get("/communications/{communication_id}", response_model=ContractCustomerCommunicationOut)
def get_contract_customer_communication_endpoint(
    communication_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> ContractCustomerCommunicationOut:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return ContractCustomerCommunicationOut.model_validate(row)


@router.post(
    "/communications/drafts/repricing-proposals/{proposal_id}/reminder",
    response_model=ContractCustomerCommunicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_repricing_reminder_communication_draft_endpoint(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.create_draft_for_repricing_proposal_reminder(
            db, proposal_id=proposal_id, actor_user_id=current_user.id, commit=True
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/communications/drafts/repricing-proposals/{proposal_id}/customer-response-follow-up",
    response_model=ContractCustomerCommunicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_repricing_response_follow_up_draft_endpoint(
    proposal_id: str,
    payload: RepricingCustomerResponseFollowUpIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.create_draft_for_customer_response_follow_up(
            db,
            proposal_id=proposal_id,
            response_type=payload.response_type,
            actor_user_id=current_user.id,
            commit=True,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/communications/drafts/activation-confirmations/{confirmation_id}/reminder",
    response_model=ContractCustomerCommunicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activation_reminder_communication_draft_endpoint(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.create_draft_for_activation_confirmation_reminder(
            db, confirmation_id=confirmation_id, actor_user_id=current_user.id, commit=True
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/communications/drafts/activation-confirmations/{confirmation_id}/acknowledgement-follow-up",
    response_model=ContractCustomerCommunicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activation_ack_follow_up_draft_endpoint(
    confirmation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.create_draft_for_activation_acknowledgement_follow_up(
            db, confirmation_id=confirmation_id, actor_user_id=current_user.id, commit=True
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/communications/drafts/contracts/{contract_id}/follow-up-notice",
    response_model=ContractCustomerCommunicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_contract_follow_up_notice_draft_endpoint(
    contract_id: str,
    payload: ContractFollowUpNoticeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.create_draft_contract_follow_up_notice(
            db,
            contract_id=contract_id,
            internal_note=payload.internal_note,
            actor_user_id=current_user.id,
            commit=True,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/communications/{communication_id}/mark-ready", response_model=ContractCustomerCommunicationOut)
def mark_customer_communication_ready_endpoint(
    communication_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.mark_ready_to_send(
            db, communication_id=communication_id, actor_user_id=current_user.id, commit=True
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/communications/{communication_id}/approve", response_model=ContractCustomerCommunicationOut)
def approve_customer_communication_endpoint(
    communication_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_approve_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.approve_for_send(
            db, communication_id=communication_id, actor_user_id=current_user.id, commit=True
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/communications/{communication_id}/send", response_model=ContractCustomerCommunicationOut)
def send_customer_communication_endpoint(
    communication_id: str,
    payload: CustomerCommunicationSendIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_send_customer_comms),
) -> ContractCustomerCommunicationOut:
    p = payload or CustomerCommunicationSendIn()
    try:
        row = ccc_svc.send_communication(
            db,
            communication_id=communication_id,
            actor_user_id=current_user.id,
            commit=True,
            break_glass_override_suppression=p.break_glass_override_suppression,
            break_glass_reason=p.break_glass_reason,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/communications/{communication_id}/cancel", response_model=ContractCustomerCommunicationOut)
def cancel_customer_communication_endpoint(
    communication_id: str,
    payload: CustomerCommunicationCancelIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_create_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.cancel_communication(
            db,
            communication_id=communication_id,
            actor_user_id=current_user.id,
            reason=payload.reason if payload else None,
            commit=True,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/communications/{communication_id}/mark-failed", response_model=ContractCustomerCommunicationOut)
def mark_customer_communication_failed_endpoint(
    communication_id: str,
    payload: CustomerCommunicationFailedIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_send_customer_comms),
) -> ContractCustomerCommunicationOut:
    try:
        row = ccc_svc.mark_failed(
            db,
            communication_id=communication_id,
            error_message=payload.error_message,
            actor_user_id=current_user.id,
            commit=True,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/communications/{communication_id}/deliveries",
    response_model=list[ContractCustomerCommunicationDeliveryOut],
)
def list_customer_communication_deliveries_endpoint(
    communication_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> list[ContractCustomerCommunicationDeliveryOut]:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    dels = ccc_svc.list_deliveries_for_communication(db, communication_id=communication_id)
    return [ContractCustomerCommunicationDeliveryOut.model_validate(d) for d in dels]


@router.get(
    "/communications/{communication_id}/provider-events",
    response_model=list[CommunicationProviderEventOut],
)
def list_communication_provider_events_endpoint(
    communication_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> list[CommunicationProviderEventOut]:
    row = db.get(ContractCustomerCommunication, communication_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    events = comm_prov_events.list_events_for_communication(db, communication_id=communication_id)
    return [CommunicationProviderEventOut.model_validate(e) for e in events]


@router.post("/communications/{communication_id}/retry-send", response_model=ContractCustomerCommunicationOut)
def retry_customer_communication_send_endpoint(
    communication_id: str,
    payload: CustomerCommunicationSendIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_send_customer_comms),
) -> ContractCustomerCommunicationOut:
    p = payload or CustomerCommunicationSendIn()
    try:
        row = ccc_svc.retry_send_communication(
            db,
            communication_id=communication_id,
            actor_user_id=current_user.id,
            commit=True,
            break_glass_override_suppression=p.break_glass_override_suppression,
            break_glass_reason=p.break_glass_reason,
        )
        return ContractCustomerCommunicationOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/customer-communications")
def contracts_dashboard_customer_communications_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return ccc_svc.dashboard_customer_communications(db)


@router.get("/dashboard/customer-communications-follow-up")
def contracts_dashboard_customer_communications_follow_up_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return ccc_svc.dashboard_customer_communications_follow_up(db)


@router.get("/dashboard/customer-communications-delivery")
def contracts_dashboard_customer_communications_delivery_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return ccc_svc.dashboard_customer_communications_delivery(db)


@router.get("/dashboard/customer-communications-failures")
def contracts_dashboard_customer_communications_failures_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return ccc_svc.dashboard_customer_communications_failures(db)


@router.get("/dashboard/customer-communications-hygiene")
def contracts_dashboard_customer_communications_hygiene_endpoint(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return comm_hygiene.dashboard_hygiene_summary(db, limit=limit)


@router.get("/dashboard/customer-communications-provider-events")
def contracts_dashboard_customer_communications_provider_events_endpoint(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_customer_comms),
) -> dict:
    return comm_hygiene.dashboard_provider_events(db, limit=limit)


@router.get("/dashboard/renewal-pipeline")
def contracts_dashboard_renewal_pipeline_endpoint(
    renewal_status: str | None = Query(default=None),
    churn_risk_level: str | None = Query(default=None),
    attention_level: str | None = Query(default=None),
    due_within_days: int | None = Query(default=None, le=730),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    return review_service.dashboard_renewal_pipeline(
        db,
        renewal_status=renewal_status,
        churn_risk_level=churn_risk_level,
        attention_level=attention_level,
        due_within_days=due_within_days,
        limit=limit,
    )


@router.post("/reviews/from-recommendation", response_model=ContractReviewOut, status_code=status.HTTP_201_CREATED)
def create_review_from_recommendation_endpoint(
    payload: ReviewFromRecommendationIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> ContractReviewOut:
    try:
        row, _created = review_service.create_review_from_recommendation(
            db,
            recommendation_id=payload.recommendation_id,
            performed_by_user_id=current_user.id,
            review_type=payload.review_type,
        )
        return ContractReviewOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/reviews", response_model=list[ContractReviewOut])
def list_contract_reviews_global_endpoint(
    status: str | None = Query(default=None),
    review_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_to_user_id: str | None = Query(default=None),
    contract_id: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[ContractReviewOut]:
    rows = review_service.list_reviews_global(
        db,
        status=status,
        review_type=review_type,
        priority=priority,
        assigned_to_user_id=assigned_to_user_id,
        contract_id=contract_id,
        limit=limit,
        offset=offset,
    )
    return [ContractReviewOut.from_row(r) for r in rows]


@router.get("/reviews/{review_id}", response_model=ContractReviewOut)
def get_contract_review_endpoint(
    review_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> ContractReviewOut:
    r = review_service.get_review(db, review_id=review_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return ContractReviewOut.from_row(r)


@router.patch("/reviews/{review_id}", response_model=ContractReviewOut)
def patch_contract_review_endpoint(
    review_id: str,
    payload: ContractReviewPatchIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> ContractReviewOut:
    try:
        r = review_service.patch_review(
            db,
            review_id=review_id,
            performed_by_user_id=current_user.id,
            **payload.model_dump(exclude_unset=True),
        )
        return ContractReviewOut.from_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/reviews/{review_id}/decision", response_model=ContractReviewOut)
def contract_review_decision_endpoint(
    review_id: str,
    payload: ContractReviewDecisionIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Commercial")),
) -> ContractReviewOut:
    require_permission_http(current_user, CAN_DECIDE_CONTRACT_REVIEW, db=db)
    try:
        r = review_service.record_review_decision(
            db,
            review_id=review_id,
            decision=payload.decision,
            performed_by_user_id=current_user.id,
            notes=payload.notes,
        )
        return ContractReviewOut.from_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/versions/{version_id}", response_model=ContractVersionOut)
def get_contract_version_global_endpoint(
    version_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> ContractVersionOut:
    v = cvs.get_version(db, version_id=version_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return ContractVersionOut.model_validate(cvs.serialize_contract_version(v, include_snapshot=True))


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> ContractOut:
    c = get_contract(db, contract_id=contract_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if not scoped_access.user_can_access_internal_entity(
        db, current_user, entity_type="contract", entity_id=contract_id, required_scope="view"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return c


@router.get("/{contract_id}/versions", response_model=list[ContractVersionOut])
def list_contract_versions_endpoint(
    contract_id: str,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[ContractVersionOut]:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rows = cvs.list_versions_for_contract(db, contract_id=contract_id, limit=limit, offset=offset)
    return [
        ContractVersionOut.model_validate(cvs.serialize_contract_version(r, include_snapshot=False))
        for r in rows
    ]


@router.get("/{contract_id}/versions/active-summary")
def contract_active_open_version_summary_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        return cvread.active_open_version_summary(db, contract_id=contract_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{contract_id}/versions/{version_id}/readable-change")
def contract_version_readable_change_endpoint(
    contract_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        return cvread.readable_change_for_version(db, contract_id=contract_id, version_id=version_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{contract_id}", response_model=ContractManualUpdateOut)
def patch_contract_endpoint(
    contract_id: str,
    payload: ContractPatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Dispatcher")),
) -> ContractManualUpdateOut:
    c = get_contract(db, contract_id=contract_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if not scoped_access.user_can_access_internal_entity(
        db,
        current_user,
        entity_type="contract",
        entity_id=contract_id,
        required_scope="manage",
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        c2, meta = cvs.apply_manual_contract_update_with_versioning(
            db,
            contract_id=contract_id,
            payload=payload,
            actor_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    base = ContractOut.model_validate(c2, from_attributes=True)
    return ContractManualUpdateOut(
        **base.model_dump(),
        manual_version_created=meta["version_created"],
        contract_version_id=meta["contract_version_id"],
        version_number=meta["version_number"],
        update_noop=meta["noop"],
    )


@router.post("/{contract_id}/reviews", response_model=ContractReviewOut, status_code=status.HTTP_201_CREATED)
def create_contract_review_endpoint(
    contract_id: str,
    payload: ContractReviewCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> ContractReviewOut:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        row, _created = review_service.create_contract_review(
            db,
            contract_id=contract_id,
            review_type=payload.review_type,
            triggered_by=payload.triggered_by,
            triggered_reason=payload.triggered_reason,
            summary=payload.summary,
            performed_by_user_id=current_user.id,
            priority=payload.priority,
            due_at=payload.due_at,
            notes=payload.notes,
            metadata=payload.metadata,
            source_recommendation_id=payload.source_recommendation_id,
            assigned_to_user_id=payload.assigned_to_user_id,
        )
        return ContractReviewOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{contract_id}/reviews", response_model=list[ContractReviewOut])
def list_contract_reviews_for_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[ContractReviewOut]:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rows = review_service.list_reviews_for_contract(db, contract_id=contract_id)
    return [ContractReviewOut.from_row(r) for r in rows]


@router.post("/{contract_id}/reviews/suggest-from-signals")
def suggest_contract_reviews_from_signals_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    applied = review_service.apply_signal_rules_for_contract(
        db,
        contract_id=contract_id,
        performed_by_user_id=current_user.id,
        period_window=period_window,
    )
    return {"contract_id": contract_id, "applied": applied}


@router.post("/{contract_id}/repricing-review", response_model=RepricingReviewOut, status_code=status.HTTP_201_CREATED)
def create_repricing_review_endpoint(
    contract_id: str,
    payload: RepricingReviewCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RepricingReviewOut:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rr, _rev, _cp = review_service.get_or_create_repricing_review(
        db,
        contract_id=contract_id,
        performed_by_user_id=current_user.id,
        current_contract_value=payload.current_contract_value,
        proposed_contract_value=payload.proposed_contract_value,
        repricing_reason_codes=payload.repricing_reason_codes,
        margin_summary=payload.margin_summary,
        burden_summary=payload.burden_summary,
        recommendation_basis=payload.recommendation_basis,
        customer_risk_level=payload.customer_risk_level,
        notes=payload.notes,
    )
    return _repricing_review_out_with_latest(db, rr)


@router.get("/{contract_id}/repricing-review", response_model=RepricingReviewOut | None)
def get_repricing_review_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RepricingReviewOut | None:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rr = review_service.get_repricing_for_contract(db, contract_id=contract_id)
    return _repricing_review_out_with_latest(db, rr) if rr else None


@router.patch("/{contract_id}/repricing-review", response_model=RepricingReviewOut)
def patch_repricing_review_endpoint(
    contract_id: str,
    payload: RepricingReviewPatchIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher", "Finance", "Commercial")),
) -> RepricingReviewOut:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("approved") is True:
        require_permission_http(current_user, CAN_APPROVE_REPRICING, db=db)
    try:
        rr = review_service.patch_repricing_review(
            db,
            contract_id=contract_id,
            performed_by_user_id=current_user.id,
            **data,
        )
        return _repricing_review_out_with_latest(db, rr)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{contract_id}/repricing-proposals",
    response_model=RepricingProposalOut,
    status_code=status.HTTP_201_CREATED,
)
def create_repricing_proposal_endpoint(
    contract_id: str,
    payload: RepricingProposalCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _roles=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> RepricingProposalOut:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    try:
        p = rps.generate_proposal_from_repricing_review(
            db,
            contract_id=contract_id,
            repricing_review_id=payload.repricing_review_id,
            generated_by_user_id=current_user.id,
            currency=payload.currency,
            supersede_previous=payload.supersede_previous,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _proposal_out(db, p)


@router.get("/{contract_id}/repricing-proposals", response_model=list[RepricingProposalOut])
def list_repricing_proposals_for_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles(*_REPRICING_PROPOSAL_ROLES)),
) -> list[RepricingProposalOut]:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    props = rps.list_proposals_for_contract(db, contract_id=contract_id)
    return [_proposal_out(db, p) for p in props]


@router.get("/{contract_id}/commercial-actions", response_model=list[CommercialActionLogOut])
def list_commercial_actions_endpoint(
    contract_id: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[CommercialActionLogOut]:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rows = review_service.list_commercial_actions(db, contract_id=contract_id, limit=limit)
    return [CommercialActionLogOut.from_row(r) for r in rows]


@router.get("/{contract_id}/jobs")
def contract_jobs_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract_jobs_summary(db, contract_id=contract_id)


@router.get("/{contract_id}/ppm")
def contract_ppm_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract_ppm_summary(db, contract_id=contract_id)


@router.get("/{contract_id}/sla-performance")
def contract_sla_performance_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return aggregate_contract_sla_performance(db, contract_id=contract_id)


@router.get("/{contract_id}/labour-summary")
def contract_labour_summary_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    try:
        return contract_intel.contract_labour_summary(db, contract_id=contract_id, period_window=period_window)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{contract_id}/performance")
def contract_performance_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    try:
        return contract_intel.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{contract_id}/profitability")
def contract_profitability_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    p = contract_intel.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    return {
        "contract_id": p["contract_id"],
        "period_window": p["period_window"],
        "revenue": p["revenue"],
        "cost": p["cost"],
        "margin": p["margin"],
        "warnings": p["warnings"],
        "calculation_basis": p["calculation_basis"],
        "data_completeness": p["data_completeness"],
    }


@router.get("/{contract_id}/renewal-intelligence")
def contract_renewal_intelligence_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    p = contract_intel.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    return {
        "contract_id": p["contract_id"],
        "period_window": p["period_window"],
        "renewal": p["renewal"],
        "health": p["health"],
        "operational_signals": {
            "overdue_ppm_count": p["operational"]["overdue_ppm_count"],
            "sla_breach_count": p["operational"]["sla_breach_count_jobs_in_period"],
            "open_recommendation_count": p["operational"]["open_recommendation_count"],
        },
        "warnings": p["warnings"],
    }


@router.get("/{contract_id}/sites/performance")
def contract_sites_performance_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    p = contract_intel.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    return {
        "contract_id": contract_id,
        "period_window": period_window,
        "site_burden": p["site_burden"],
        "warnings": p["warnings"],
    }


@router.get("/{contract_id}/assets/burden")
def contract_assets_burden_endpoint(
    contract_id: str,
    period_window: str = Query(default=contract_intel.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if period_window not in contract_intel.PERIOD_WINDOWS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period_window")
    p = contract_intel.build_contract_profitability(db, contract_id=contract_id, period_window=period_window)
    return {
        "contract_id": contract_id,
        "period_window": period_window,
        "asset_burden": p["asset_burden"],
        "warnings": p["warnings"],
    }


@router.get("/{contract_id}/performance/snapshots")
def contract_performance_snapshots_list_endpoint(
    contract_id: str,
    period_window: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[dict]:
    if not get_contract(db, contract_id=contract_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    rows = contract_intel.list_snapshots(db, contract_id=contract_id, period_window=period_window, limit=limit)
    return [contract_intel.snapshot_to_api_dict(r) for r in rows]


@router.post("/{contract_id}/ppm/generate-due", status_code=status.HTTP_200_OK)
def generate_ppm_due_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
    now: datetime | None = Query(default=None),
) -> dict[str, object]:
    try:
        job_ids = generate_due_ppm_jobs_for_contract(db, contract_id=contract_id, now=now)
        return {"created_job_ids": job_ids}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/jobs/{job_id}/sla/risk", response_model=SlaBreachRiskOut)
def sla_risk_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
    now: datetime | None = Query(default=None),
) -> SlaBreachRiskOut:
    risk = compute_sla_breach_risk(db, job_id=job_id, now=now)
    return SlaBreachRiskOut.model_validate(risk)

