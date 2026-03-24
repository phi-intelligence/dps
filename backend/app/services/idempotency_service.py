"""
Idempotency helpers for engineer-mobile write paths.

When ``Idempotency-Key`` is present, we store a canonical hash of the request body
together with the successful JSON response. Replays with the same key + same body
return the stored response; replays with the same key + different body return 409.

Limitation (documented): concurrent first-time requests with the same key can still
double-execute before either record is committed. Retries after the first success
are fully covered.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.modules.common.idempotency_models import ApiIdempotencyRecord

_logger = logging.getLogger(__name__)

MAX_IDEMPOTENCY_KEY_LEN = 128


def normalize_idempotency_key(key: str | None) -> str | None:
    if key is None:
        return None
    key = key.strip()
    if not key:
        return None
    if len(key) > MAX_IDEMPOTENCY_KEY_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key too long (max 128)",
        )
    return key


def canonical_request_hash(payload: BaseModel) -> str:
    obj = payload.model_dump(mode="json")
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lookup_cached_json(
    db: Session,
    *,
    user_id: str,
    scope: str,
    idempotency_key: str | None,
    request_hash: str,
) -> tuple[int, dict[str, Any]] | None:
    """
    Returns (http_status, response_dict) when a prior successful response was recorded.
    Raises 409 if the key exists but the body hash differs.
    """
    key = normalize_idempotency_key(idempotency_key)
    if not key:
        return None

    row = (
        db.query(ApiIdempotencyRecord)
        .filter(
            ApiIdempotencyRecord.user_id == user_id,
            ApiIdempotencyRecord.scope == scope,
            ApiIdempotencyRecord.idempotency_key == key,
        )
        .one_or_none()
    )
    if not row:
        return None
    if row.request_hash != request_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key reused with a different request payload",
        )
    return (row.http_status, json.loads(row.response_json))


def save_idempotent_success(
    db: Session,
    *,
    user_id: str,
    scope: str,
    idempotency_key: str | None,
    request_hash: str,
    response_body: dict[str, Any],
    http_status: int = 200,
) -> None:
    key = normalize_idempotency_key(idempotency_key)
    if not key:
        return

    rec = ApiIdempotencyRecord(
        user_id=user_id,
        scope=scope,
        idempotency_key=key,
        request_hash=request_hash,
        http_status=http_status,
        response_json=json.dumps(response_body),
    )
    db.add(rec)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = (
            db.query(ApiIdempotencyRecord)
            .filter(
                ApiIdempotencyRecord.user_id == user_id,
                ApiIdempotencyRecord.scope == scope,
                ApiIdempotencyRecord.idempotency_key == key,
            )
            .one_or_none()
        )
        if not row:
            _logger.warning("Idempotency insert race without follow-up row for scope=%s", scope)
            return
        if row.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency-Key reused with a different request payload",
            ) from None
        # Concurrent completion with same key/hash — safe to ignore duplicate insert.
