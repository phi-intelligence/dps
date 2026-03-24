"""
Lightweight Wave 7 checks that do not import ``backend.app.main`` (avoids heavy PDF/PIL
import chain in constrained CI / dev environments).
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from backend.app.modules.dispatch.engineer_replay_guards import (
    engineer_accept_is_replay_noop,
    normalized_json_for_dedup,
)
from fastapi import HTTPException

from backend.app.services.idempotency_service import (
    canonical_request_hash,
    normalize_idempotency_key,
)


class _SamplePayload(BaseModel):
    job_id: str
    latitude: float
    longitude: float


def test_canonical_request_hash_stable_for_equivalent_payloads():
    a = _SamplePayload(job_id="j1", latitude=1.0, longitude=2.0)
    b = _SamplePayload(job_id="j1", latitude=1.0, longitude=2.0)
    assert canonical_request_hash(a) == canonical_request_hash(b)


def test_canonical_request_hash_differs_for_different_payloads():
    a = _SamplePayload(job_id="j1", latitude=1.0, longitude=2.0)
    b = _SamplePayload(job_id="j1", latitude=1.1, longitude=2.0)
    assert canonical_request_hash(a) != canonical_request_hash(b)


def test_normalize_idempotency_key_rejects_overlength_key():
    long_key = "x" * 129
    with pytest.raises(HTTPException) as exc:
        normalize_idempotency_key(long_key)
    assert exc.value.status_code == 400
    assert "128" in (exc.value.detail or "")


def test_normalize_idempotency_key_strips_and_empty_becomes_none():
    assert normalize_idempotency_key("  abc  ") == "abc"
    assert normalize_idempotency_key("") is None
    assert normalize_idempotency_key("   ") is None
    assert normalize_idempotency_key(None) is None


def test_normalized_json_for_dedup_order_independent():
    assert normalized_json_for_dedup({"b": 1, "a": 2}) == normalized_json_for_dedup({"a": 2, "b": 1})


def test_engineer_accept_replay_noop_requires_status_and_assignment():
    from types import SimpleNamespace

    job_ok = SimpleNamespace(assigned_engineer_id="u1", status="accepted")
    assert engineer_accept_is_replay_noop(job_ok, engineer_user_id="u1") is True

    job_wrong = SimpleNamespace(assigned_engineer_id="u2", status="accepted")
    assert engineer_accept_is_replay_noop(job_wrong, engineer_user_id="u1") is False
