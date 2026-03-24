from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.ops.schemas import (
    DashboardActionsSummaryOut,
    RecommendationActionConfirmIn,
    RecommendationActionDecisionOut,
    RecommendationActionExecuteOut,
    RecommendationActionIn,
    RecommendationActionPreviewIn,
    RecommendationActionPreviewOut,
    RecommendationActionRejectIn,
    RecommendationActionSuggestionOut,
    RecommendationByCategoryOut,
    RecommendationHighPriorityOut,
    RecommendationOut,
    RecommendationRunScanOut,
    RecommendationSnoozeIn,
    RecommendationSummaryOut,
    RecommendationSuppressionCreateIn,
    RecommendationSuppressionOut,
)
from backend.app.modules.approvals import service as approval_service
from backend.app.modules.approvals.schemas import ApprovalsDashboardSummaryOut
from backend.app.modules.ops import recommendation_action_service as rec_action_service
from backend.app.modules.ops import service as ops_service
from backend.app.services import recommendation_engine as rec_engine


router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/recommendations", response_model=list[RecommendationOut])
def list_recommendations_endpoint(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    related_job_id: str | None = Query(default=None),
    related_contract_id: str | None = Query(default=None),
    include_suppressed: bool = Query(default=False),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RecommendationOut]:
    rows = ops_service.list_recommendations(
        db,
        status=status,
        category=category,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        related_job_id=related_job_id,
        related_contract_id=related_contract_id,
        limit=limit,
        offset=offset,
        include_suppressed=include_suppressed,
    )
    return [RecommendationOut.from_orm_row(r) for r in rows]


@router.post("/recommendations/run-scan", response_model=RecommendationRunScanOut)
def run_scan_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationRunScanOut:
    out = ops_service.run_full_scan(db)
    return RecommendationRunScanOut(keys_active=out["keys_active"], auto_resolved=out["auto_resolved"])


@router.post("/recommendations/scan-job/{job_id}", response_model=dict)
def scan_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    try:
        n = rec_engine.scan_job_recommendations(db, job_id=job_id)
        return {"job_id": job_id, "keys_active": n}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/recommendations/scan-contract/{contract_id}", response_model=dict)
def scan_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    try:
        n = rec_engine.scan_contract_recommendations(db, contract_id=contract_id)
        return {"contract_id": contract_id, "keys_active": n}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/recommendations/scan-inventory", response_model=dict)
def scan_inventory_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    n = rec_engine.scan_inventory_recommendations(db)
    return {"keys_active": n}


@router.post("/recommendations/scan-assets", response_model=dict)
def scan_assets_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict:
    n = rec_engine.scan_asset_recommendations(db)
    return {"keys_active": n}


@router.post("/recommendations/suppressions", response_model=RecommendationSuppressionOut, status_code=status.HTTP_201_CREATED)
def create_suppression_endpoint(
    payload: RecommendationSuppressionCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationSuppressionOut:
    try:
        s = ops_service.create_suppression(
            db,
            user_id=current_user.id,
            recommendation_key=payload.recommendation_key,
            category=payload.category,
            contract_id=payload.contract_id,
            site_id=payload.site_id,
            hours=payload.hours,
            notes=payload.notes,
        )
        return RecommendationSuppressionOut.model_validate(s)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/recommendations/suppressions", response_model=list[RecommendationSuppressionOut])
def list_suppressions_endpoint(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RecommendationSuppressionOut]:
    rows = ops_service.list_suppressions(db, active_only=active_only)
    return [RecommendationSuppressionOut.model_validate(r) for r in rows]


@router.delete("/recommendations/suppressions/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suppression_endpoint(
    suppression_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> None:
    try:
        ops_service.delete_suppression(db, suppression_id=suppression_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationOut)
def get_recommendation_endpoint(
    recommendation_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    r = ops_service.get_recommendation(db, recommendation_id=recommendation_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return RecommendationOut.from_orm_row(r)


@router.post("/recommendations/{recommendation_id}/acknowledge", response_model=RecommendationOut)
def acknowledge_endpoint(
    recommendation_id: str,
    payload: RecommendationActionIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    try:
        r = ops_service.acknowledge_recommendation(
            db,
            recommendation_id=recommendation_id,
            user_id=current_user.id,
            notes=(payload.notes if payload else None),
        )
        return RecommendationOut.from_orm_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/recommendations/{recommendation_id}/resolve", response_model=RecommendationOut)
def resolve_endpoint(
    recommendation_id: str,
    payload: RecommendationActionIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    try:
        r = ops_service.resolve_recommendation(
            db,
            recommendation_id=recommendation_id,
            user_id=current_user.id,
            notes=(payload.notes if payload else None),
        )
        return RecommendationOut.from_orm_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/recommendations/{recommendation_id}/dismiss", response_model=RecommendationOut)
def dismiss_endpoint(
    recommendation_id: str,
    payload: RecommendationActionIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    try:
        r = ops_service.dismiss_recommendation(
            db,
            recommendation_id=recommendation_id,
            user_id=current_user.id,
            notes=(payload.notes if payload else None),
        )
        return RecommendationOut.from_orm_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/recommendations/{recommendation_id}/reopen", response_model=RecommendationOut)
def reopen_endpoint(
    recommendation_id: str,
    payload: RecommendationActionIn | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    try:
        r = ops_service.reopen_recommendation(
            db,
            recommendation_id=recommendation_id,
            user_id=current_user.id,
            notes=(payload.notes if payload else None),
        )
        return RecommendationOut.from_orm_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/recommendations/{recommendation_id}/snooze", response_model=RecommendationOut)
def snooze_endpoint(
    recommendation_id: str,
    payload: RecommendationSnoozeIn,
    db: Session = Depends(get_db),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationOut:
    try:
        r = ops_service.snooze_recommendation(
            db,
            recommendation_id=recommendation_id,
            hours=payload.hours,
            notes=payload.notes,
        )
        return RecommendationOut.from_orm_row(r)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/dashboard/recommendations/summary", response_model=RecommendationSummaryOut)
def dashboard_summary_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationSummaryOut:
    return ops_service.dashboard_summary(db)


@router.get("/dashboard/recommendations/high-priority", response_model=RecommendationHighPriorityOut)
def dashboard_high_priority_endpoint(
    limit: int = Query(default=25, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationHighPriorityOut:
    return RecommendationHighPriorityOut(items=ops_service.high_priority_feed(db, limit=limit))


@router.get("/dashboard/recommendations/by-category", response_model=RecommendationByCategoryOut)
def dashboard_by_category_endpoint(
    category: str = Query(..., min_length=3),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationByCategoryOut:
    return RecommendationByCategoryOut(
        category=category,
        items=ops_service.by_category_feed(db, category=category, limit=limit),
    )


@router.get(
    "/recommendations/{recommendation_id}/actions",
    response_model=list[RecommendationActionSuggestionOut],
)
def list_recommendation_actions_endpoint(
    recommendation_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RecommendationActionSuggestionOut]:
    rows = rec_action_service.list_action_suggestions(db, recommendation_id=recommendation_id)
    return [RecommendationActionSuggestionOut.from_row(r) for r in rows]


@router.post(
    "/recommendations/{recommendation_id}/actions/preview",
    response_model=RecommendationActionPreviewOut,
)
def preview_recommendation_action_endpoint(
    recommendation_id: str,
    payload: RecommendationActionPreviewIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationActionPreviewOut:
    try:
        prev = rec_action_service.preview_recommendation_action(
            db,
            recommendation_id=recommendation_id,
            action_type=payload.action_type,
            actor_user_id=current_user.id,
            input_payload=payload.input_payload,
            decision_notes=payload.decision_notes,
        )
        return RecommendationActionPreviewOut(preview=prev)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/recommendations/{recommendation_id}/actions/confirm",
    response_model=RecommendationActionExecuteOut,
)
def confirm_recommendation_action_endpoint(
    recommendation_id: str,
    payload: RecommendationActionConfirmIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationActionExecuteOut:
    try:
        out = rec_action_service.execute_recommendation_action(
            db,
            recommendation_id=recommendation_id,
            action_type=payload.action_type,
            actor_user_id=current_user.id,
            input_payload=payload.input_payload,
            confirmed=payload.confirmed,
            decision_notes=payload.decision_notes,
            override_reason=payload.override_reason,
        )
        return RecommendationActionExecuteOut(**out)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/recommendations/{recommendation_id}/actions/reject", status_code=status.HTTP_200_OK)
def reject_recommendation_action_endpoint(
    recommendation_id: str,
    payload: RecommendationActionRejectIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Dispatcher")),
) -> RecommendationActionSuggestionOut:
    try:
        row = rec_action_service.reject_recommendation_action(
            db,
            recommendation_id=recommendation_id,
            action_type=payload.action_type,
            actor_user_id=current_user.id,
            rejection_reason=payload.rejection_reason,
            decision_notes=payload.decision_notes,
        )
        return RecommendationActionSuggestionOut.from_row(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/recommendations/{recommendation_id}/actions/history",
    response_model=list[RecommendationActionDecisionOut],
)
def recommendation_action_history_endpoint(
    recommendation_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[RecommendationActionDecisionOut]:
    rows = rec_action_service.list_action_history(db, recommendation_id=recommendation_id)
    return [RecommendationActionDecisionOut.from_row(r) for r in rows]


@router.get("/dashboard/actions/summary", response_model=DashboardActionsSummaryOut)
def dashboard_actions_summary_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> DashboardActionsSummaryOut:
    raw = rec_action_service.dashboard_actions_summary(db)
    return DashboardActionsSummaryOut(**raw)


@router.get("/dashboard/pending-approvals", response_model=ApprovalsDashboardSummaryOut)
def ops_pending_approvals_dashboard_endpoint(
    overdue_hours: float = Query(default=72.0, ge=1.0, le=720.0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _roles=Depends(require_roles("Admin", "Finance", "Commercial", "Ops_Manager", "Dispatcher")),
) -> ApprovalsDashboardSummaryOut:
    raw = approval_service.dashboard_summary(
        db, current_user_id=current_user.id, overdue_hours=overdue_hours
    )
    return ApprovalsDashboardSummaryOut(**raw)
