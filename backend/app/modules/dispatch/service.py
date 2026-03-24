from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.contracts.commercial_context import apply_reactive_commercial_context
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.models import (
    JobFormRequirement,
    JobFormSubmission,
    JobMediaRequirement,
    JobPartsUsageRequirement,
    JobSignatureRequirement,
)
from backend.app.modules.dispatch.schemas import (
    EngineerRecommendationOut,
    JobCompletionRequirementsBundleOut,
    JobCreateIn,
    JobFormRequirementOut,
    JobMediaRequirementOut,
    JobPartsUsageRequirementOut,
    JobRecommendationOut,
    JobSignatureRequirementOut,
)
from backend.app.modules.dispatch.recommendation_engine import compute_ranked_dispatch_recommendations
from backend.app.modules.quoting.schemas import QuoteItemIn, QuoteCreateIn
from backend.app.modules.quoting.service import accept_quote, create_quote


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_job(db: Session, *, payload: JobCreateIn) -> Job:
    if not payload.customer_id and not payload.quote_id:
        raise ValueError("Either customer_id or quote_id must be provided")

    req_json = json.dumps(payload.required_competencies) if payload.required_competencies is not None else "[]"
    job = Job(
        customer_id=payload.customer_id,
        quote_id=payload.quote_id,
        contract_id=payload.contract_id,
        site_id=payload.site_id,
        asset_id=payload.asset_id,
        address=payload.address,
        scheduled_at=payload.scheduled_at,
        status="created",
        work_type=payload.work_type or "reactive",
        site_latitude=payload.site_latitude,
        site_longitude=payload.site_longitude,
        address_geocoded_latitude=payload.address_geocoded_latitude,
        address_geocoded_longitude=payload.address_geocoded_longitude,
        material_policy=payload.material_policy,
        dispatch_priority=payload.dispatch_priority,
        required_competencies_json=req_json,
    )
    if payload.site_id or payload.asset_id or payload.contract_id:
        apply_reactive_commercial_context(
            db,
            job=job,
            site_id=payload.site_id,
            asset_id=payload.asset_id,
            contract_id=payload.contract_id,
        )
    db.add(job)
    db.commit()
    db.refresh(job)

    if job.quote_id:
        try:
            from backend.app.modules.portal.communication_hooks import log_quote_accepted

            log_quote_accepted(db, job_id=job.id, quote_id=job.quote_id)
        except Exception:
            pass

    return job


def list_jobs(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    assigned_engineer_id: str | None = None,
) -> list[Job]:
    """
    List jobs. When ``assigned_engineer_id`` is set, only jobs assigned to that engineer are returned
    (used by the engineer mobile app).
    """
    q = db.query(Job)
    if assigned_engineer_id is not None:
        q = q.filter(Job.assigned_engineer_id == assigned_engineer_id)
    jobs = (
        q.order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Best-effort SLA risk fields for UI (doc: contract SLA engine + breach risk).
    # Keep it lightweight by computing on-demand for the returned page only.
    try:
        from backend.app.modules.contracts.service import compute_sla_breach_risk

        for job in jobs:
            if not job.contract_id:
                setattr(job, "sla_risk_state", None)
                setattr(job, "sla_target_completion_at", None)
                continue

            risk = compute_sla_breach_risk(db, job_id=job.id)
            setattr(job, "sla_risk_state", risk.get("risk_state"))
            setattr(job, "sla_target_completion_at", risk.get("target_completion_at"))
    except Exception:
        # SLA computation should never break core list jobs.
        for job in jobs:
            setattr(job, "sla_risk_state", None)
            setattr(job, "sla_target_completion_at", None)

    return jobs


def try_finalize_job_completion_if_possible(
    db: Session,
    *,
    job_id: str,
    completed_status: str = "completed",
    blocked_status: str = "completion_blocked_forms",
) -> Job:
    """
    Minimal job completion gate (Phase 3.1):
    - if no requirements exist for the job, job is moved to `completed`
    - otherwise the job is completed only if every requirement has `satisfied_at`
    """

    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    form_requirements = db.query(JobFormRequirement).filter(JobFormRequirement.job_id == job_id).all()
    signature_requirements = db.query(JobSignatureRequirement).filter(JobSignatureRequirement.job_id == job_id).all()
    media_requirements = db.query(JobMediaRequirement).filter(JobMediaRequirement.job_id == job_id).all()
    parts_requirements = db.query(JobPartsUsageRequirement).filter(JobPartsUsageRequirement.job_id == job_id).all()

    policy = getattr(job, "material_policy", "materials_optional")
    requirements = [*form_requirements, *signature_requirements, *media_requirements]
    if policy != "no_materials_expected":
        requirements.extend(parts_requirements)

    from backend.app.modules.inventory.service import parts_usage_blocks_strict_completion

    def _apply_inventory_gate() -> None:
        if parts_usage_blocks_strict_completion(db, job_id=job_id):
            job.status = "completion_blocked_inventory"
        else:
            job.status = completed_status

    if not requirements:
        _apply_inventory_gate()
    else:
        all_satisfied = all(r.satisfied_at is not None for r in requirements)
        if not all_satisfied:
            job.status = blocked_status
        else:
            _apply_inventory_gate()

    # Freeze costing at completion (standard cost + usage truth) before commit.
    if job.status == completed_status:
        try:
            from backend.app.services.job_costing import persist_job_cost_snapshot

            persist_job_cost_snapshot(db, job_id=job_id, commit=False)
        except Exception:
            # Costing must not block operational completion.
            pass

    db.commit()
    db.refresh(job)
    return job


def list_job_completion_requirements_bundle(db: Session, *, job_id: str) -> JobCompletionRequirementsBundleOut:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    forms = db.query(JobFormRequirement).filter(JobFormRequirement.job_id == job_id).all()
    signatures = db.query(JobSignatureRequirement).filter(JobSignatureRequirement.job_id == job_id).all()
    media = db.query(JobMediaRequirement).filter(JobMediaRequirement.job_id == job_id).all()
    parts = db.query(JobPartsUsageRequirement).filter(JobPartsUsageRequirement.job_id == job_id).all()

    policy = getattr(job, "material_policy", "materials_optional") or "materials_optional"

    return JobCompletionRequirementsBundleOut(
        job_id=job_id,
        material_policy=policy,
        form_requirements=[JobFormRequirementOut.model_validate(r) for r in forms],
        signature_requirements=[JobSignatureRequirementOut.model_validate(r) for r in signatures],
        media_requirements=[JobMediaRequirementOut.model_validate(r) for r in media],
        parts_requirements=[JobPartsUsageRequirementOut.model_validate(r) for r in parts],
    )


def validate_job_form_submission_required_keys(
    *,
    required_keys_json: str,
    data: dict[str, object],
) -> tuple[bool, list[str]]:
    required_keys = []
    try:
        required_keys = json.loads(required_keys_json or "[]")
    except Exception:
        required_keys = []

    missing: list[str] = []
    for k in required_keys:
        v = data.get(k)
        if v is None:
            missing.append(k)
            continue
        if isinstance(v, str) and not v.strip():
            missing.append(k)

    return (len(missing) == 0), missing


def create_follow_on_jobs_from_defects(
    db: Session,
    *,
    source_job_id: str,
    defects: list[str],
    labour_unit_price: float = 100.0,
) -> list[str]:
    """
    Minimal Phase 3.3 implementation:
    - create a separate accepted quote per defect (labour-only)
    - create a follow-up job linked to that quote
    """

    source_job = db.get(Job, source_job_id)
    if not source_job:
        raise ValueError("Source job not found")

    if not source_job.customer_id:
        raise ValueError("Source job has no customer_id")

    created_job_ids: list[str] = []
    for defect in defects:
        defect_clean = (defect or "").strip()
        if not defect_clean:
            continue

        follow_quote = create_quote(
            db,
            payload=QuoteCreateIn(
                customer_id=source_job.customer_id,
                currency="GBP",
                notes=f"Follow-on from job {source_job_id}: {defect_clean}",
                items=[
                    QuoteItemIn(item_type="labour", description=defect_clean, quantity=1.0, unit_price=labour_unit_price)
                ],
            ),
        )
        accept_quote(db, quote_id=follow_quote.id)

        follow_job = create_job(
            db,
            payload=JobCreateIn(
                customer_id=source_job.customer_id,
                quote_id=follow_quote.id,
                address=source_job.address,
                scheduled_at=None,
                site_id=source_job.site_id,
                asset_id=source_job.asset_id,
                contract_id=source_job.contract_id,
                work_type="reactive",
            ),
        )
        created_job_ids.append(follow_job.id)

    return created_job_ids


def assign_job(
    db: Session,
    *,
    job_id: str,
    engineer_id: str,
    required_competencies: list[str] | None = None,
) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    if required_competencies:
        # Enforce that the engineer has non-expired qualifications for each required competency.
        from backend.app.modules.competence.service import validate_engineer_competencies

        validate_engineer_competencies(
            db,
            engineer_id=engineer_id,
            required_competencies=required_competencies,
        )

    job.assigned_engineer_id = engineer_id
    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, *, job_id: str, status: str) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    job.status = status
    if status == "completed" and job.resolved_at is None:
        job.resolved_at = utc_now()
    db.commit()
    db.refresh(job)
    return job


def recommend_engineers_for_job(
    db: Session,
    *,
    job_id: str,
    required_competencies: list[str] | None = None,
    limit: int = 3,
    max_vehicle_age_seconds: int = 60 * 15,
) -> JobRecommendationOut:
    """
    Backward-compatible wrapper around dispatch intelligence.

    Uses the same ranking engine as /dispatch/jobs/{id}/recommendations but returns the legacy shape.
    Includes stale telemetry candidates (similar to the historical 15-minute observation window).
    """
    del max_vehicle_age_seconds  # superseded by freshness tiers; kept for API compatibility

    result = compute_ranked_dispatch_recommendations(
        db,
        job_id=job_id,
        limit=limit,
        required_competencies=required_competencies,
        include_stale=True,
    )

    recommendations: list[EngineerRecommendationOut] = []
    for r in result.recommendations:
        recommendations.append(
            EngineerRecommendationOut(
                engineer_id=r.engineer_id,
                distance_m=float(r.distance_km * 1000.0),
                eta_minutes=r.estimated_travel_minutes,
                latitude=r.operational_latitude,
                longitude=r.operational_longitude,
                last_seen_at=r.last_occurred_at or utc_now(),
            )
        )

    return JobRecommendationOut(job_id=job_id, recommendations=recommendations)


def mark_job_on_my_way_for_customer(
    db: Session,
    *,
    job_id: str,
    source: str = "dispatcher_manual",
    set_en_route: bool = True,
) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    now = utc_now()
    job.on_my_way_sent_at = now
    job.customer_notified_at = now
    if set_en_route and not job.en_route_at:
        job.en_route_at = now
    from backend.app.modules.portal.communication_hooks import log_engineer_on_the_way

    log_engineer_on_the_way(db, job_id=job_id, source=source, commit=False)
    db.commit()
    db.refresh(job)
    return job


def set_job_manual_eta_minutes(db: Session, *, job_id: str, eta_minutes: int | None) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    job.manual_eta_minutes = eta_minutes
    job.manual_eta_set_at = utc_now() if eta_minutes is not None else None
    db.commit()
    db.refresh(job)
    return job

