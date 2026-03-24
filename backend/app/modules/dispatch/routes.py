from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
import json
from datetime import datetime, timedelta, timezone

from backend.app.api.deps import require_roles
from backend.app.db.session import get_db
from backend.app.modules.dispatch.schemas import (
    JobAssignIn,
    JobCompletionRequirementsBundleOut,
    JobCreateIn,
    JobOut,
    JobEngineerAcceptIn,
    JobFormRequirementOut,
    JobFormRequirementSetIn,
    JobFormSubmitIn,
    JobFormSubmissionOut,
    JobMediaRequirementSetIn,
    JobMediaCapabilitiesOut,
    JobMediaSubmitIn,
    JobMediaUploadSessionCommitIn,
    JobMediaUploadSessionCreateIn,
    JobMediaUploadSessionOut,
    JobMediaRequirementOut,
    JobPartsUsageRequirementSetIn,
    JobPartsUsageRequirementOut,
    JobPartsUsageSubmitIn,
    JobSignatureRequirementOut,
    JobSignatureRequirementSetIn,
    JobSignatureSubmitIn,
    JobRecommendationOut,
    FollowOnCreatedOut,
    FollowOnFromDefectsIn,
    JobActivityEventOut,
    JobActivityNoteCreateIn,
    JobStatusUpdateIn,
)
from backend.app.modules.dispatch.service import (
    assign_job,
    create_job,
    create_follow_on_jobs_from_defects,
    list_job_completion_requirements_bundle,
    list_jobs,
    recommend_engineers_for_job,
    try_finalize_job_completion_if_possible,
    update_job_status,
    validate_job_form_submission_required_keys,
)
from backend.app.services.equipment_readiness_service import evaluate_job_equipment_readiness
from backend.app.modules.costing.schemas import JobCostingSummaryOut, JobLabourCostingOut
from backend.app.modules.contracts.schemas import JobSlaStatusOut
from backend.app.modules.contracts.sla_clock_service import compute_job_sla_status
from backend.app.modules.equipment.schemas import (
    EquipmentReadinessResultOut,
    JobEquipmentRequirementCreateIn,
    JobEquipmentRequirementOut,
)
from backend.app.modules.equipment.service import add_job_requirement, list_job_requirements
from backend.app.modules.dispatch.models import (
    Job,
    JobFormRequirement,
    JobFormSubmission,
    JobMediaRequirement,
    JobMediaSubmission,
    JobMediaUploadSession,
    JobPartsUsageRequirement,
    JobPartsUsageSubmission,
    JobPartsReconciliationApproval,
    JobSignatureRequirement,
    JobSignatureSubmission,
    JobActivityEvent,
)
from backend.app.services.runtime_settings_service import get_effective_feature_flags
from backend.app.modules.time_tracking.models import Punch
from backend.app.modules.dispatch.engineer_mobile_constants import ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES
from backend.app.modules.dispatch.engineer_replay_guards import (
    TERMINAL_JOB_STATUSES_FOR_ACCEPT,
    engineer_accept_is_replay_noop,
    find_duplicate_form_submission,
    find_duplicate_parts_submission,
    find_duplicate_signature_submission,
)
from backend.app.services.idempotency_service import (
    canonical_request_hash,
    lookup_cached_json,
    save_idempotent_success,
)


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _enforce_engineer_job_access_or_403(*, job: Job, current_user) -> None:
    roles = set(current_user.role_names())
    if "Engineer" in roles:
        if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")


def _media_phase2_enabled(db: Session) -> bool:
    flags = get_effective_feature_flags(db)
    return bool(flags.get("engineer_media_phase2_enabled", False))


def _submit_media_common(
    *,
    db: Session,
    job_id: str,
    media_type: str,
    payloads: list[dict[str, object]],
    current_user,
) -> JobMediaRequirement:
    payload = JobMediaSubmitIn(media_type=media_type, payloads=payloads)
    payload_bytes = len(json.dumps(payload.model_dump(mode="json"), separators=(",", ":")).encode("utf-8"))
    if payload_bytes > ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Media JSON payload exceeds {ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES} bytes; "
                "reduce photo count or resolution."
            ),
        )

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    for p in payloads:
        db.add(
            JobMediaSubmission(
                job_id=job_id,
                media_type=media_type,
                payload_json=json.dumps(p),
                submitted_by_user_id=current_user.id,
            )
        )

    requirement = db.query(JobMediaRequirement).filter(JobMediaRequirement.job_id == job_id).one_or_none()
    if requirement and media_type == "photo":
        photo_count = (
            db.query(JobMediaSubmission)
            .filter(JobMediaSubmission.job_id == job_id, JobMediaSubmission.media_type == "photo")
            .count()
        )
        if photo_count >= requirement.required_photo_count:
            requirement.satisfied_at = datetime.now(timezone.utc)

    db.commit()

    try:
        finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)
        if finalized.status == "completed" and finalized.quote_id:
            from backend.app.modules.inventory.service import consume_parts_for_quote

            consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)
            db.commit()
    except Exception:
        pass

    if not requirement:
        requirement = JobMediaRequirement(
            job_id=job_id,
            required_photo_count=len(payloads),
            satisfied_at=datetime.now(timezone.utc),
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)

    return requirement


@router.get("/media/capabilities", response_model=JobMediaCapabilitiesOut)
def get_media_capabilities_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Engineer")),
) -> JobMediaCapabilitiesOut:
    phase2 = _media_phase2_enabled(db)
    return JobMediaCapabilitiesOut(
        phase2_enabled=phase2,
        mode="upload_session_commit" if phase2 else "legacy_json",
        max_json_payload_bytes=ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES,
        legacy_json_enabled=True,
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job_endpoint(
    payload: JobCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobOut:
    try:
        return create_job(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[JobOut])
def list_jobs_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> list[JobOut]:
    roles = set(current_user.role_names())
    if roles.intersection({"Admin", "Dispatcher"}):
        return list_jobs(db, limit=limit, offset=offset)
    # Engineer-only callers: assigned work only (mobile field app).
    return list_jobs(
        db,
        limit=limit,
        offset=offset,
        assigned_engineer_id=current_user.id,
    )


@router.get("/{job_id}/costing", response_model=JobCostingSummaryOut)
def get_job_costing_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobCostingSummaryOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    from backend.app.services.job_costing import get_job_costing_for_api

    try:
        payload = get_job_costing_for_api(db, job_id=job_id, prefer_snapshot=True)
        return JobCostingSummaryOut(**payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{job_id}/labour-costing", response_model=JobLabourCostingOut)
def get_job_labour_costing_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobLabourCostingOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    from backend.app.services.job_costing import get_job_labour_costing_for_api

    try:
        payload = get_job_labour_costing_for_api(db, job_id=job_id, prefer_snapshot=True)
        return JobLabourCostingOut(**payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{job_id}/sla", response_model=JobSlaStatusOut)
def get_job_sla_clock_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
    now: datetime | None = Query(default=None),
) -> JobSlaStatusOut:
    try:
        raw = compute_job_sla_status(db, job_id=job_id, now=now)
        return JobSlaStatusOut.model_validate(raw)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{job_id}/assign", response_model=JobOut)
def assign_job_endpoint(
    job_id: str,
    payload: JobAssignIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobOut:
    try:
        return assign_job(
            db,
            job_id=job_id,
            engineer_id=payload.engineer_id,
            required_competencies=payload.required_competencies,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{job_id}/accept", response_model=JobOut)
def engineer_accept_job_endpoint(
    job_id: str,
    payload: JobEngineerAcceptIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobOut:
    scope = f"POST:/jobs/{job_id}/accept"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobOut.model_validate(cached[1])

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status in TERMINAL_JOB_STATUSES_FOR_ACCEPT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be accepted in its current state",
        )

    # If assigned already, only allow the same engineer to re-accept.
    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    if engineer_accept_is_replay_noop(job, engineer_user_id=current_user.id):
        out = JobOut.model_validate(job)
        save_idempotent_success(
            db,
            user_id=current_user.id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=rhash,
            response_body=out.model_dump(mode="json"),
        )
        return out

    try:
        assign_job(
            db,
            job_id=job_id,
            engineer_id=current_user.id,
            required_competencies=payload.required_competencies,
        )
        updated = update_job_status(db, job_id=job_id, status="accepted")
        out = JobOut.model_validate(updated)
        save_idempotent_success(
            db,
            user_id=current_user.id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=rhash,
            response_body=out.model_dump(mode="json"),
        )
        return out
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{job_id}/status", response_model=JobOut)
def update_job_status_endpoint(
    job_id: str,
    payload: JobStatusUpdateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobOut:
    try:
        return update_job_status(db, job_id=job_id, status=payload.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{job_id}/recommend", response_model=JobRecommendationOut)
def recommend_job_engineers_endpoint(
    job_id: str,
    required_competencies: str | None = Query(
        default=None,
        description="Comma-separated list of required competencies to filter qualified engineers.",
    ),
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobRecommendationOut:
    required_list = [c.strip() for c in (required_competencies or "").split(",") if c.strip()] or None
    try:
        return recommend_engineers_for_job(
            db,
            job_id=job_id,
            required_competencies=required_list,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{job_id}/forms/{form_key}/requirements", response_model=JobFormRequirementOut)
def set_job_form_requirements_endpoint(
    job_id: str,
    form_key: str,
    payload: JobFormRequirementSetIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobFormRequirementOut:
    existing = (
        db.query(JobFormRequirement)
        .filter(JobFormRequirement.job_id == job_id, JobFormRequirement.form_key == form_key)
        .one_or_none()
    )
    if not db.get(Job, job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    required_keys_json = json.dumps(payload.required_keys)

    if existing:
        existing.required_keys_json = required_keys_json
        existing.satisfied_at = datetime.now(timezone.utc) if len(payload.required_keys) == 0 else None
        db.commit()
        db.refresh(existing)
        return JobFormRequirementOut.model_validate(existing)

    req = JobFormRequirement(
        job_id=job_id,
        form_key=form_key,
        required_keys_json=required_keys_json,
        satisfied_at=datetime.now(timezone.utc) if len(payload.required_keys) == 0 else None,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return JobFormRequirementOut.model_validate(req)


@router.post("/{job_id}/forms/{form_key}/submit", response_model=JobFormSubmissionOut)
def submit_job_form_endpoint(
    job_id: str,
    form_key: str,
    payload: JobFormSubmitIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobFormSubmissionOut:
    scope = f"POST:/jobs/{job_id}/forms/{form_key}/submit"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobFormSubmissionOut.model_validate(cached[1])

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    dup = find_duplicate_form_submission(db, job_id=job_id, form_key=form_key, data=payload.data)
    if dup:
        out = JobFormSubmissionOut.model_validate(dup)
        save_idempotent_success(
            db,
            user_id=current_user.id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=rhash,
            response_body=out.model_dump(mode="json"),
        )
        return out

    requirement = (
        db.query(JobFormRequirement)
        .filter(JobFormRequirement.job_id == job_id, JobFormRequirement.form_key == form_key)
        .one_or_none()
    )

    if requirement:
        ok, missing = validate_job_form_submission_required_keys(
            required_keys_json=requirement.required_keys_json,
            data=payload.data,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"missing_required_keys": missing},
            )

    submission = JobFormSubmission(
        job_id=job_id,
        form_key=form_key,
        data_json=json.dumps(payload.data),
        submitted_by_user_id=current_user.id,
    )
    db.add(submission)

    if requirement:
        requirement.satisfied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(submission)

    # After submission, if all requirements are satisfied, allow job completion.
    try:
        finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)
        if finalized.status == "completed" and finalized.quote_id:
            from backend.app.modules.inventory.service import consume_parts_for_quote

            consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)
            db.commit()
    except Exception:
        pass

    out = JobFormSubmissionOut.model_validate(submission)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/{job_id}/completion/signature/require", response_model=JobSignatureRequirementOut)
def set_signature_requirement_endpoint(
    job_id: str,
    payload: JobSignatureRequirementSetIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobSignatureRequirementOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.query(JobSignatureRequirement).filter(JobSignatureRequirement.job_id == job_id).one_or_none()
    required = bool(payload.required)
    if existing:
        existing.satisfied_at = datetime.now(timezone.utc) if not required else None
        db.commit()
        db.refresh(existing)
        return JobSignatureRequirementOut.model_validate(existing)

    req = JobSignatureRequirement(
        job_id=job_id,
        satisfied_at=None if required else datetime.now(timezone.utc),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return JobSignatureRequirementOut.model_validate(req)


@router.post("/{job_id}/completion/media/require", response_model=JobMediaRequirementOut)
def set_media_requirement_endpoint(
    job_id: str,
    payload: JobMediaRequirementSetIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobMediaRequirementOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.query(JobMediaRequirement).filter(JobMediaRequirement.job_id == job_id).one_or_none()
    required_photo_count = int(payload.required_photo_count)
    satisfied_at = datetime.now(timezone.utc) if required_photo_count <= 0 else None

    if existing:
        existing.required_photo_count = required_photo_count
        existing.satisfied_at = satisfied_at
        db.commit()
        db.refresh(existing)
        return JobMediaRequirementOut.model_validate(existing)

    req = JobMediaRequirement(
        job_id=job_id,
        required_photo_count=required_photo_count,
        satisfied_at=satisfied_at,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return JobMediaRequirementOut.model_validate(req)


@router.post("/{job_id}/completion/parts-usage/require", response_model=JobPartsUsageRequirementOut)
def set_parts_usage_requirement_endpoint(
    job_id: str,
    payload: JobPartsUsageRequirementSetIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobPartsUsageRequirementOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.query(JobPartsUsageRequirement).filter(JobPartsUsageRequirement.job_id == job_id).one_or_none()
    required_parts_items_count = int(payload.required_parts_items_count)
    satisfied_at = datetime.now(timezone.utc) if required_parts_items_count <= 0 else None

    if existing:
        existing.required_parts_items_count = required_parts_items_count
        existing.satisfied_at = satisfied_at
        db.commit()
        db.refresh(existing)
        return JobPartsUsageRequirementOut.model_validate(existing)

    req = JobPartsUsageRequirement(
        job_id=job_id,
        required_parts_items_count=required_parts_items_count,
        satisfied_at=satisfied_at,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return JobPartsUsageRequirementOut.model_validate(req)


@router.post("/{job_id}/signature", response_model=JobSignatureRequirementOut)
def submit_job_signature_endpoint(
    job_id: str,
    payload: JobSignatureSubmitIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobSignatureRequirementOut:
    scope = f"POST:/jobs/{job_id}/signature"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobSignatureRequirementOut.model_validate(cached[1])

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    dup_sig = find_duplicate_signature_submission(
        db,
        job_id=job_id,
        engineer_user_id=current_user.id,
        signature=payload.signature,
    )
    if dup_sig:
        requirement = db.query(JobSignatureRequirement).filter(JobSignatureRequirement.job_id == job_id).one_or_none()
        if not requirement:
            requirement = JobSignatureRequirement(job_id=job_id, satisfied_at=datetime.now(timezone.utc))
            db.add(requirement)
            db.commit()
            db.refresh(requirement)
        out = JobSignatureRequirementOut.model_validate(requirement)
        save_idempotent_success(
            db,
            user_id=current_user.id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=rhash,
            response_body=out.model_dump(mode="json"),
        )
        return out

    # Persist signature capture for audit.
    submission = JobSignatureSubmission(
        job_id=job_id,
        signed_by_user_id=current_user.id,
        signature_json=json.dumps(payload.signature),
    )
    db.add(submission)

    requirement = db.query(JobSignatureRequirement).filter(JobSignatureRequirement.job_id == job_id).one_or_none()
    if requirement:
        requirement.satisfied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(submission)

    try:
        finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)
        if finalized.status == "completed" and finalized.quote_id:
            from backend.app.modules.inventory.service import consume_parts_for_quote

            consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)
            db.commit()
    except Exception:
        pass

    # If no requirement existed yet, return a "satisfied" placeholder by creating one lazily.
    if not requirement:
        requirement = JobSignatureRequirement(job_id=job_id, satisfied_at=datetime.now(timezone.utc))
        db.add(requirement)
        db.commit()
        db.refresh(requirement)

    out = JobSignatureRequirementOut.model_validate(requirement)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/{job_id}/media", response_model=JobMediaRequirementOut)
def submit_job_media_endpoint(
    job_id: str,
    payload: JobMediaSubmitIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobMediaRequirementOut:
    scope = f"POST:/jobs/{job_id}/media"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobMediaRequirementOut.model_validate(cached[1])

    requirement = _submit_media_common(
        db=db,
        job_id=job_id,
        media_type=payload.media_type,
        payloads=payload.payloads,
        current_user=current_user,
    )
    out = JobMediaRequirementOut.model_validate(requirement)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/{job_id}/media/upload-sessions", response_model=JobMediaUploadSessionOut, status_code=status.HTTP_201_CREATED)
def create_job_media_upload_session_endpoint(
    job_id: str,
    payload: JobMediaUploadSessionCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
) -> JobMediaUploadSessionOut:
    if not _media_phase2_enabled(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media phase 2 not enabled")
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    session = JobMediaUploadSession(
        job_id=job_id,
        created_by_user_id=current_user.id,
        media_type=payload.media_type,
        status="open",
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return JobMediaUploadSessionOut(
        id=session.id,
        job_id=session.job_id,
        media_type=session.media_type,
        status=session.status,
        upload_mode="upload_session_commit",
        expires_at=session.expires_at,
        created_at=session.created_at,
    )


@router.post("/{job_id}/media/upload-sessions/{session_id}/commit", response_model=JobMediaRequirementOut)
def commit_job_media_upload_session_endpoint(
    job_id: str,
    session_id: str,
    payload: JobMediaUploadSessionCommitIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobMediaRequirementOut:
    if not _media_phase2_enabled(db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media phase 2 not enabled")
    session = db.get(JobMediaUploadSession, session_id)
    if not session or session.job_id != job_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    if session.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Upload session belongs to another user")
    now = datetime.now(timezone.utc)
    if session.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload session not open")
    if session.expires_at < now:
        session.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload session expired")

    scope = f"POST:/jobs/{job_id}/media/upload-sessions/{session_id}/commit"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobMediaRequirementOut.model_validate(cached[1])

    requirement = _submit_media_common(
        db=db,
        job_id=job_id,
        media_type=session.media_type,
        payloads=payload.payloads,
        current_user=current_user,
    )
    session.status = "committed"
    session.committed_at = datetime.now(timezone.utc)
    db.commit()
    out = JobMediaRequirementOut.model_validate(requirement)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/{job_id}/parts-usage", response_model=JobPartsUsageRequirementOut)
def submit_job_parts_usage_endpoint(
    job_id: str,
    payload: JobPartsUsageSubmitIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobPartsUsageRequirementOut:
    scope = f"POST:/jobs/{job_id}/parts-usage"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobPartsUsageRequirementOut.model_validate(cached[1])

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    dup_parts = find_duplicate_parts_submission(
        db,
        job_id=job_id,
        engineer_user_id=current_user.id,
        items=payload.items,
    )
    if dup_parts:
        requirement = db.query(JobPartsUsageRequirement).filter(JobPartsUsageRequirement.job_id == job_id).one_or_none()
        if not requirement:
            requirement = JobPartsUsageRequirement(
                job_id=job_id,
                required_parts_items_count=len(payload.items),
                satisfied_at=datetime.now(timezone.utc),
            )
            db.add(requirement)
            db.commit()
            db.refresh(requirement)
        out = JobPartsUsageRequirementOut.model_validate(requirement)
        save_idempotent_success(
            db,
            user_id=current_user.id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=rhash,
            response_body=out.model_dump(mode="json"),
        )
        return out

    submission = JobPartsUsageSubmission(
        job_id=job_id,
        payload_json=json.dumps(payload.items),
        submitted_by_user_id=current_user.id,
    )
    db.add(submission)
    db.flush()

    try:
        from backend.app.modules.inventory.service import reconcile_parts_usage_submission

        reconcile_parts_usage_submission(db, job=job, submission=submission, raw_items=payload.items)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    requirement = db.query(JobPartsUsageRequirement).filter(JobPartsUsageRequirement.job_id == job_id).one_or_none()
    if requirement:
        required_count = requirement.required_parts_items_count
        # Approximation: total items across all submissions.
        total_items = 0
        for s in db.query(JobPartsUsageSubmission).filter(JobPartsUsageSubmission.job_id == job_id).all():
            try:
                decoded = json.loads(s.payload_json or "[]")
                if isinstance(decoded, list):
                    total_items += len(decoded)
            except Exception:
                continue

        if total_items >= required_count:
            requirement.satisfied_at = datetime.now(timezone.utc)

    db.commit()

    try:
        finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)
        if finalized.status == "completed" and finalized.quote_id:
            from backend.app.modules.inventory.service import consume_parts_for_quote

            consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)
            db.commit()
    except Exception:
        pass

    if not requirement:
        requirement = JobPartsUsageRequirement(
            job_id=job_id,
            required_parts_items_count=len(payload.items),
            satisfied_at=datetime.now(timezone.utc),
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)

    out = JobPartsUsageRequirementOut.model_validate(requirement)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
    )
    return out


@router.post("/{job_id}/parts-reconciliation/approve", status_code=status.HTTP_200_OK)
def approve_job_parts_reconciliation_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.query(JobPartsReconciliationApproval).filter(JobPartsReconciliationApproval.job_id == job_id).first()
    if not existing:
        db.add(
            JobPartsReconciliationApproval(
                job_id=job_id,
                approved_by_user_id=current_user.id,
            )
        )
        db.commit()

    finalized = try_finalize_job_completion_if_possible(db, job_id=job_id)
    if finalized.status == "completed" and finalized.quote_id:
        from backend.app.modules.inventory.service import consume_parts_for_quote

        consume_parts_for_quote(db, quote_id=finalized.quote_id, job_id=job_id, commit=False)
        db.commit()

    return {"status": finalized.status}


@router.post("/{job_id}/follow-on/from-defects", response_model=FollowOnCreatedOut)
def create_follow_on_from_defects_endpoint(
    job_id: str,
    payload: FollowOnFromDefectsIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
) -> FollowOnCreatedOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.assigned_engineer_id and job.assigned_engineer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job assigned to another engineer")

    created_job_ids = create_follow_on_jobs_from_defects(
        db,
        source_job_id=job_id,
        defects=payload.defects,
    )

    return FollowOnCreatedOut(source_job_id=job_id, created_job_ids=created_job_ids)


@router.get("/{job_id}/completion-requirements", response_model=JobCompletionRequirementsBundleOut)
def get_job_completion_requirements_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> JobCompletionRequirementsBundleOut:
    try:
        return list_job_completion_requirements_bundle(db, job_id=job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{job_id}/equipment-readiness", response_model=EquipmentReadinessResultOut)
def job_equipment_readiness_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> EquipmentReadinessResultOut:
    try:
        ev = evaluate_job_equipment_readiness(db, job_id=job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return EquipmentReadinessResultOut(**ev.to_dict())


@router.post(
    "/{job_id}/equipment-requirements",
    response_model=JobEquipmentRequirementOut,
    status_code=status.HTTP_201_CREATED,
)
def add_job_equipment_requirement_endpoint(
    job_id: str,
    payload: JobEquipmentRequirementCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> JobEquipmentRequirementOut:
    try:
        return add_job_requirement(db, job_id=job_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{job_id}/equipment-requirements", response_model=list[JobEquipmentRequirementOut])
def list_job_equipment_requirements_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> list[JobEquipmentRequirementOut]:
    if not db.get(Job, job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return list_job_requirements(db, job_id=job_id)


@router.get("/{job_id}", response_model=JobOut)
def get_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> JobOut:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("/{job_id}/activity", response_model=list[JobActivityEventOut])
def list_job_activity_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Engineer")),
) -> list[JobActivityEventOut]:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    _enforce_engineer_job_access_or_403(job=job, current_user=current_user)
    note_rows = (
        db.query(JobActivityEvent)
        .filter(JobActivityEvent.job_id == job_id)
        .order_by(JobActivityEvent.created_at.asc())
        .all()
    )
    events: list[JobActivityEventOut] = [JobActivityEventOut.model_validate(r) for r in note_rows]

    # Typed timeline expansion from existing job-domain records (safe read-only projection).
    form_rows = (
        db.query(JobFormSubmission)
        .filter(JobFormSubmission.job_id == job_id)
        .order_by(JobFormSubmission.submitted_at.asc())
        .all()
    )
    for row in form_rows:
        events.append(
            JobActivityEventOut(
                id=f"form:{row.id}",
                job_id=job_id,
                author_user_id=row.submitted_by_user_id,
                activity_type="form_submission",
                source="job_form",
                body=f"Submitted form '{row.form_key}'.",
                created_at=row.submitted_at,
            )
        )

    signature_rows = (
        db.query(JobSignatureSubmission)
        .filter(JobSignatureSubmission.job_id == job_id)
        .order_by(JobSignatureSubmission.submitted_at.asc())
        .all()
    )
    for row in signature_rows:
        events.append(
            JobActivityEventOut(
                id=f"signature:{row.id}",
                job_id=job_id,
                author_user_id=row.signed_by_user_id,
                activity_type="signature_submission",
                source="job_signature",
                body="Captured engineer signature.",
                created_at=row.submitted_at,
            )
        )

    media_rows = (
        db.query(JobMediaSubmission)
        .filter(JobMediaSubmission.job_id == job_id)
        .order_by(JobMediaSubmission.submitted_at.asc())
        .all()
    )
    for row in media_rows:
        events.append(
            JobActivityEventOut(
                id=f"media:{row.id}",
                job_id=job_id,
                author_user_id=row.submitted_by_user_id,
                activity_type="media_submission",
                source="job_media",
                body=f"Uploaded {row.media_type} evidence.",
                created_at=row.submitted_at,
            )
        )

    parts_rows = (
        db.query(JobPartsUsageSubmission)
        .filter(JobPartsUsageSubmission.job_id == job_id)
        .order_by(JobPartsUsageSubmission.submitted_at.asc())
        .all()
    )
    for row in parts_rows:
        events.append(
            JobActivityEventOut(
                id=f"parts:{row.id}",
                job_id=job_id,
                author_user_id=row.submitted_by_user_id,
                activity_type="parts_submission",
                source="job_parts",
                body="Submitted parts usage.",
                created_at=row.submitted_at,
            )
        )

    punch_rows = (
        db.query(Punch)
        .filter(Punch.job_id == job_id)
        .order_by(Punch.occurred_at.asc())
        .all()
    )
    for row in punch_rows:
        events.append(
            JobActivityEventOut(
                id=f"punch:{row.id}",
                job_id=job_id,
                author_user_id=row.user_id,
                activity_type="punch",
                source="time_tracking",
                body=f"Recorded punch {row.kind}.",
                created_at=row.occurred_at,
            )
        )

    events.sort(key=lambda e: e.created_at)
    return events


@router.post("/{job_id}/notes", response_model=JobActivityEventOut, status_code=status.HTTP_201_CREATED)
def create_job_note_endpoint(
    job_id: str,
    payload: JobActivityNoteCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Engineer")),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> JobActivityEventOut:
    scope = f"POST:/jobs/{job_id}/notes"
    rhash = canonical_request_hash(payload)
    cached = lookup_cached_json(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
    )
    if cached:
        return JobActivityEventOut.model_validate(cached[1])

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    _enforce_engineer_job_access_or_403(job=job, current_user=current_user)

    body = (payload.body or "").strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note body is required")
    if len(body) > 4000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note body too long (max 4000)")

    ev = JobActivityEvent(
        job_id=job_id,
        author_user_id=current_user.id,
        activity_type="note",
        source=(payload.source or "engineer_note").strip() or "engineer_note",
        body=body,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    out = JobActivityEventOut.model_validate(ev)
    save_idempotent_success(
        db,
        user_id=current_user.id,
        scope=scope,
        idempotency_key=idempotency_key,
        request_hash=rhash,
        response_body=out.model_dump(mode="json"),
        http_status=status.HTTP_201_CREATED,
    )
    return out

