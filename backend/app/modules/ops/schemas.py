from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RecommendationOut(BaseModel):
    id: str
    recommendation_type: str
    category: str
    severity: str
    confidence: str
    title: str
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)
    entity_type: str
    entity_id: str
    related_job_id: str | None
    related_engineer_id: str | None
    related_site_id: str | None
    related_asset_id: str | None
    related_contract_id: str | None
    related_invoice_id: str | None
    status: str
    recommendation_key: str
    source_rule_version: str
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    acknowledged_by_user_id: str | None
    resolution_notes: str | None
    closed_as: str | None = None
    suppressed_until: datetime | None = None
    suppression_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_row(cls, r: Any) -> RecommendationOut:
        try:
            detail = json.loads(r.detail_json or "{}")
            if not isinstance(detail, dict):
                detail = {}
        except Exception:
            detail = {}
        return cls(
            id=r.id,
            recommendation_type=r.recommendation_type,
            category=r.category,
            severity=r.severity,
            confidence=r.confidence,
            title=r.title,
            summary=r.summary,
            detail=detail,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            related_job_id=r.related_job_id,
            related_engineer_id=r.related_engineer_id,
            related_site_id=r.related_site_id,
            related_asset_id=r.related_asset_id,
            related_contract_id=r.related_contract_id,
            related_invoice_id=r.related_invoice_id,
            status=r.status,
            recommendation_key=r.recommendation_key,
            source_rule_version=r.source_rule_version,
            acknowledged_at=r.acknowledged_at,
            resolved_at=r.resolved_at,
            acknowledged_by_user_id=r.acknowledged_by_user_id,
            resolution_notes=r.resolution_notes,
            closed_as=getattr(r, "closed_as", None),
            suppressed_until=getattr(r, "suppressed_until", None),
            suppression_notes=getattr(r, "suppression_notes", None),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )


class RecommendationRunScanOut(BaseModel):
    keys_active: int
    auto_resolved: int


class RecommendationActionIn(BaseModel):
    notes: str | None = None


class RecommendationSnoozeIn(BaseModel):
    hours: float = Field(default=24, ge=0.25, le=720)
    notes: str | None = None


class RecommendationSuppressionCreateIn(BaseModel):
    """At least one of recommendation_key or category must be set."""

    recommendation_key: str | None = None
    category: str | None = None
    contract_id: str | None = None
    site_id: str | None = None
    hours: float = Field(default=24, ge=0.25, le=720 * 4)
    notes: str | None = None


class RecommendationSuppressionOut(BaseModel):
    id: str
    recommendation_key: str | None
    category: str | None
    contract_id: str | None
    site_id: str | None
    suppressed_until: datetime
    notes: str | None
    created_by_user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationSummaryOut(BaseModel):
    open_by_severity: dict[str, int]
    open_by_category: dict[str, int]
    critical_open: list[RecommendationOut]
    high_open: list[RecommendationOut]
    stale_acknowledged_count: int
    recently_resolved: list[RecommendationOut]


class RecommendationHighPriorityOut(BaseModel):
    items: list[RecommendationOut]


class RecommendationByCategoryOut(BaseModel):
    category: str
    items: list[RecommendationOut]


class RecommendationActionSuggestionOut(BaseModel):
    id: str
    recommendation_id: str
    action_type: str
    action_label: str
    action_description: str
    action_status: str
    preview_json: dict[str, Any] | None = None
    input_schema_json: dict[str, Any] | None = None
    requires_confirmation: bool
    requires_override_reason: bool
    risk_level: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row: Any) -> RecommendationActionSuggestionOut:
        pj = None
        if row.preview_json:
            try:
                pj = json.loads(row.preview_json)
                if not isinstance(pj, dict):
                    pj = None
            except Exception:
                pj = None
        ij = None
        if row.input_schema_json:
            try:
                ij = json.loads(row.input_schema_json)
                if not isinstance(ij, dict):
                    ij = None
            except Exception:
                ij = None
        return cls(
            id=row.id,
            recommendation_id=row.recommendation_id,
            action_type=row.action_type,
            action_label=row.action_label,
            action_description=row.action_description,
            action_status=row.action_status,
            preview_json=pj,
            input_schema_json=ij,
            requires_confirmation=row.requires_confirmation,
            requires_override_reason=row.requires_override_reason,
            risk_level=row.risk_level,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class RecommendationActionPreviewIn(BaseModel):
    action_type: str = Field(..., min_length=3)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    decision_notes: str | None = None


class RecommendationActionConfirmIn(BaseModel):
    action_type: str = Field(..., min_length=3)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    decision_notes: str | None = None
    override_reason: str | None = None


class RecommendationActionRejectIn(BaseModel):
    action_type: str = Field(..., min_length=3)
    rejection_reason: str = Field(..., min_length=3)
    decision_notes: str | None = None


class RecommendationActionDecisionOut(BaseModel):
    id: str
    recommendation_id: str
    action_suggestion_id: str | None
    decision_type: str
    decided_by_user_id: str
    decided_at: datetime
    decision_notes: str | None
    override_reason: str | None
    preview_snapshot_json: dict[str, Any] | None = None
    execution_result_json: dict[str, Any] | None = None
    execution_status: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_row(cls, row: Any) -> RecommendationActionDecisionOut:
        def _pj(raw: str | None) -> dict[str, Any] | None:
            if not raw:
                return None
            try:
                o = json.loads(raw)
                return o if isinstance(o, dict) else None
            except Exception:
                return None

        return cls(
            id=row.id,
            recommendation_id=row.recommendation_id,
            action_suggestion_id=row.action_suggestion_id,
            decision_type=row.decision_type,
            decided_by_user_id=row.decided_by_user_id,
            decided_at=row.decided_at,
            decision_notes=row.decision_notes,
            override_reason=row.override_reason,
            preview_snapshot_json=_pj(row.preview_snapshot_json),
            execution_result_json=_pj(row.execution_result_json),
            execution_status=row.execution_status,
        )


class RecommendationActionPreviewOut(BaseModel):
    preview: dict[str, Any]


class RecommendationActionExecuteOut(BaseModel):
    preview: dict[str, Any]
    execution: dict[str, Any]
    suggestion_id: str


class DashboardActionsSummaryOut(BaseModel):
    open_recommendations: int
    recommendations_with_available_actions: int
    pending_confirmations: int
    recently_rejected: int
    recently_executed_success: int
    failed_executions: int
    action_decisions_last_7d_by_type: dict[str, int]
    window_start: str
