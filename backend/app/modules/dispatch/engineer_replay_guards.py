"""
Practical replay / duplicate protections for engineer mobile write paths (Wave 7).

These are additive guards; server-side idempotency (``Idempotency-Key``) remains the
primary replay contract.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.app.modules.dispatch.models import (
    Job,
    JobFormSubmission,
    JobPartsUsageSubmission,
    JobSignatureSubmission,
)

# Jobs that cannot transition via engineer accept.
TERMINAL_JOB_STATUSES_FOR_ACCEPT = frozenset({"completed", "cancelled"})

# Engineer has already progressed past raw dispatch; accept replay should not mutate.
POST_ACCEPT_ENGINEER_STATUSES = frozenset({"accepted", "on_site", "en_route", "completion_pending_forms"})


def normalized_json_for_dedup(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def engineer_accept_is_replay_noop(job: Job, *, engineer_user_id: str) -> bool:
    return bool(
        job.assigned_engineer_id == engineer_user_id and job.status in POST_ACCEPT_ENGINEER_STATUSES
    )


def find_duplicate_form_submission(
    db: Session,
    *,
    job_id: str,
    form_key: str,
    data: dict,
) -> JobFormSubmission | None:
    want = normalized_json_for_dedup(data)
    rows = (
        db.query(JobFormSubmission)
        .filter(JobFormSubmission.job_id == job_id, JobFormSubmission.form_key == form_key)
        .order_by(JobFormSubmission.created_at.desc())
        .limit(5)
        .all()
    )
    for row in rows:
        try:
            got = normalized_json_for_dedup(json.loads(row.data_json or "{}"))
        except Exception:
            continue
        if got == want:
            return row
    return None


def find_duplicate_signature_submission(
    db: Session,
    *,
    job_id: str,
    engineer_user_id: str,
    signature: dict,
) -> JobSignatureSubmission | None:
    want = normalized_json_for_dedup(signature)
    rows = (
        db.query(JobSignatureSubmission)
        .filter(JobSignatureSubmission.job_id == job_id, JobSignatureSubmission.signed_by_user_id == engineer_user_id)
        .order_by(JobSignatureSubmission.submitted_at.desc())
        .limit(5)
        .all()
    )
    for row in rows:
        try:
            got = normalized_json_for_dedup(json.loads(row.signature_json or "{}"))
        except Exception:
            continue
        if got == want:
            return row
    return None


def find_duplicate_parts_submission(
    db: Session,
    *,
    job_id: str,
    engineer_user_id: str,
    items: list[dict],
) -> JobPartsUsageSubmission | None:
    want = normalized_json_for_dedup({"items": items})
    rows = (
        db.query(JobPartsUsageSubmission)
        .filter(
            JobPartsUsageSubmission.job_id == job_id,
            JobPartsUsageSubmission.submitted_by_user_id == engineer_user_id,
        )
        .order_by(JobPartsUsageSubmission.submitted_at.desc())
        .limit(5)
        .all()
    )
    for row in rows:
        try:
            raw = json.loads(row.payload_json or "[]")
            got = normalized_json_for_dedup({"items": raw if isinstance(raw, list) else []})
        except Exception:
            continue
        if got == want:
            return row
    return None
