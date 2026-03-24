from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.auth.models import User
from backend.app.modules.dispatch.availability_service import (
    compute_engineer_availability,
    compute_engineer_workload_band,
    count_active_assigned_jobs,
    engineer_has_valid_competencies,
)
from backend.app.modules.dispatch.dispatch_point_service import resolve_job_dispatch_point
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.tracking.service import haversine_m
from backend.app.modules.tracking.telemetry_state_service import telemetry_freshness_seconds
from backend.app.services.runtime_settings_service import get_effective_dispatch_settings, get_effective_feature_flags
from backend.app.services.equipment_readiness_service import evaluate_job_equipment_readiness
from backend.app.services.vehicle_readiness_service import evaluate_vehicle_readiness


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _job_required_competencies(job: Job) -> list[str]:
    try:
        raw = json.loads(job.required_competencies_json or "[]")
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
    except Exception:
        pass
    return []


@dataclass
class DispatchRecommendationRow:
    engineer_id: str
    distance_km: float
    estimated_travel_minutes: float
    availability_state: str
    telemetry_freshness_seconds: float | None
    competency_match: bool
    active_job_count: int
    recommendation_score: float
    recommendation_reasons: list[str] = field(default_factory=list)
    operational_latitude: float = 0.0
    operational_longitude: float = 0.0
    operational_source: str = "phone"
    last_occurred_at: datetime | None = None
    equipment_readiness_status: str | None = None
    equipment_readiness_reasons: list[str] = field(default_factory=list)
    vehicle_readiness_status: str | None = None
    vehicle_readiness_reasons: list[str] = field(default_factory=list)

    def to_audit_dict(self) -> dict[str, Any]:
        d = asdict(self)
        loa = d.get("last_occurred_at")
        if isinstance(loa, datetime):
            d["last_occurred_at"] = loa.isoformat()
        return d


@dataclass
class DispatchRecommendationResult:
    job_id: str
    dispatch_point_source: str
    recommendations: list[DispatchRecommendationRow]
    scoring_notes: dict[str, Any]


def compute_ranked_dispatch_recommendations(
    db: Session,
    *,
    job_id: str,
    limit: int = 10,
    required_competencies: list[str] | None = None,
    include_stale: bool | None = None,
    now: datetime | None = None,
) -> DispatchRecommendationResult:
    """
    Competency-aware, telemetry-aware ranked dispatch recommendations.
    Scoring stays here — not in HTTP handlers.
    """
    now = now or utc_now()
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    dp = resolve_job_dispatch_point(db, job_id=job_id)
    merged_required = [c for c in (required_competencies or []) if c]
    if not merged_required:
        merged_required = _job_required_competencies(job)

    ff = get_effective_feature_flags(db)
    ds = get_effective_dispatch_settings(db)
    if include_stale is None:
        include_stale = bool(ff["dispatch_recommend_stale"])

    users = db.query(User).all()
    engineer_ids = [u.id for u in users if "Engineer" in set(u.role_names())]

    avg_speed = float(ds["avg_vehicle_speed_mps"])
    priority_boost = float(job.dispatch_priority or 0) * 2.0

    rows: list[DispatchRecommendationRow] = []
    for eid in engineer_ids:
        reasons: list[str] = []

        comp_ok, comp_detail = engineer_has_valid_competencies(
            db, engineer_id=eid, required_competencies=merged_required, now=now
        )
        if not comp_ok:
            continue
        reasons.append("competency_match")
        if merged_required:
            reasons.append(f"competencies:{','.join(merged_required)}")

        op = resolve_operational_position_for_engineer(db, engineer_id=eid, now=now)
        if not op:
            continue

        if op.freshness_status == "stale" and not include_stale:
            continue

        workload = compute_engineer_workload_band(db, engineer_id=eid)
        if workload in ("on_job", "busy"):
            continue

        fresh_s = telemetry_freshness_seconds(occurred_at=op.occurred_at, now=now)
        availability_state = compute_engineer_availability(
            db,
            engineer_id=eid,
            required_competencies=merged_required,
            now=now,
        )
        # If we allowed stale via include_stale, availability may still say stale_location — normalise row state.
        if include_stale and op.freshness_status == "stale":
            availability_state = "stale_location"
            reasons.append("telemetry_stale_included_by_policy")

        distance_m = haversine_m(
            lat1=op.latitude,
            lon1=op.longitude,
            lat2=dp.latitude,
            lon2=dp.longitude,
        )
        distance_km = distance_m / 1000.0
        travel_minutes = float(distance_m / max(avg_speed, 0.1) / 60.0)

        active_count = count_active_assigned_jobs(db, engineer_id=eid)

        score = (
            1000.0
            + priority_boost
            - distance_km * 80.0
            - travel_minutes * 1.5
            - active_count * 25.0
        )

        if op.freshness_status == "aging":
            score -= 15.0
            reasons.append("telemetry_aging_penalty")
        if op.freshness_status == "stale":
            score -= 200.0
            reasons.append("telemetry_stale_penalty")

        if workload == "travelling":
            score -= 10.0
            reasons.append("workload_travelling_penalty")

        reasons.append(f"distance_km:{round(distance_km, 3)}")
        reasons.append(f"operational_source:{op.source}")
        reasons.append(f"telemetry_freshness:{op.freshness_status}")
        reasons.append(f"dispatch_point_source:{dp.source}")
        reasons.append(f"active_jobs:{active_count}")

        eq_status: str | None = None
        eq_reasons: list[str] = []
        try:
            ev = evaluate_job_equipment_readiness(db, job_id=job_id, for_engineer_id=eid, now=now)
            eq_status = ev.readiness_status
            eq_reasons = list(ev.blocking_flags) + ev.warnings[:6]
            if ev.readiness_status == "blocked":
                score -= 150.0
                reasons.append("equipment_readiness_blocked")
            elif ev.readiness_status == "warning":
                score -= 40.0
                reasons.append("equipment_readiness_warning")
        except Exception:
            pass

        urow = db.get(User, eid)
        vid = (urow.assigned_vehicle_id or "").strip() if urow else ""
        vr_status: str | None = None
        vr_reasons: list[str] = []
        if vid:
            vr = evaluate_vehicle_readiness(db, vehicle_id=vid, now=now)
            vr_status = vr.readiness_status
            vr_reasons = (vr.reasons + vr.warnings + vr.blocking_flags)[:8]
            if vr.readiness_status == "blocked":
                reasons.append("vehicle_readiness_blocked_excluded")
                continue
            if vr.readiness_status == "warning":
                score -= 35.0
                reasons.append("vehicle_readiness_warning")

        rows.append(
            DispatchRecommendationRow(
                engineer_id=eid,
                distance_km=round(distance_km, 6),
                estimated_travel_minutes=round(travel_minutes, 3),
                availability_state=availability_state,
                telemetry_freshness_seconds=round(fresh_s, 3),
                competency_match=True,
                active_job_count=active_count,
                recommendation_score=round(score, 4),
                recommendation_reasons=reasons,
                operational_latitude=op.latitude,
                operational_longitude=op.longitude,
                operational_source=op.source,
                last_occurred_at=op.occurred_at,
                equipment_readiness_status=eq_status,
                equipment_readiness_reasons=eq_reasons,
                vehicle_readiness_status=vr_status,
                vehicle_readiness_reasons=vr_reasons,
            )
        )

    rows.sort(key=lambda r: r.recommendation_score, reverse=True)
    safe_limit = max(1, min(max(limit, 1), 50))

    meta = {
        "job_dispatch_priority": job.dispatch_priority,
        "include_stale": include_stale,
        "required_competencies": merged_required,
        "avg_speed_mps": avg_speed,
        "candidate_count_pre_limit": len(rows),
    }

    return DispatchRecommendationResult(
        job_id=job_id,
        dispatch_point_source=dp.source,
        recommendations=rows[:safe_limit],
        scoring_notes=meta,
    )
