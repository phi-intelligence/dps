"""
Deterministic recommendations from labour segmentation / snapshot completeness.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

from backend.app.modules.contracts.models import Contract
from backend.app.modules.costing.models import JobCostSnapshot
from backend.app.modules.dispatch.models import Job


def register_labour_costing_recommendations(db: Session, active_keys: set[str], *, now: datetime) -> None:
    from backend.app.services import recommendation_engine as reng

    _register = reng._register
    now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    window_start = now - timedelta(days=90)

    for job in db.query(Job).filter(Job.status.in_(["completed", "closed"])).all():
        snap = db.query(JobCostSnapshot).filter(JobCostSnapshot.job_id == job.id).first()
        if not snap:
            continue
        ca = _aware(snap.completed_at)
        if ca and ca < window_start:
            continue

        lc = float(snap.labour_cost or 0)
        ot_c = float(snap.labour_overtime_cost or 0)
        dt_c = float(getattr(snap, "doubletime_labour_cost", 0) or 0)
        overtime_total = ot_c + dt_c
        if lc > 80 and overtime_total / max(lc, 1e-6) > 0.35:
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=f"labour:excessive-overtime:job:{job.id}",
                recommendation_type="labour_excessive_overtime",
                category="labour_costing",
                severity="medium",
                confidence="high",
                title="High overtime labour cost vs base work",
                summary=f"Overtime+doubletime ~{(overtime_total/max(lc,1e-6))*100:.0f}% of recorded work labour on snapshot.",
                detail={
                    "reasons": ["overtime_labour_share_elevated"],
                    "current_value": {
                        "labour_cost": lc,
                        "overtime_cost": ot_c,
                        "doubletime_cost": dt_c,
                    },
                    "suggested_action": "Review scheduling, contract hours, and rate profile thresholds.",
                },
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_contract_id=job.contract_id,
            )

        reg_m = int(getattr(snap, "regular_labour_minutes", 0) or 0)
        ooh_m = int(getattr(snap, "out_of_hours_labour_minutes", 0) or 0)
        tot_m = reg_m + int(getattr(snap, "overtime_labour_minutes", 0) or 0)
        tot_m += int(getattr(snap, "doubletime_labour_minutes", 0) or 0) + ooh_m
        if tot_m >= 60 and ooh_m / tot_m > 0.4:
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=f"labour:out-of-hours-burden:job:{job.id}",
                recommendation_type="labour_out_of_hours_burden",
                category="labour_costing",
                severity="medium",
                confidence="high",
                title="Elevated out-of-hours labour share",
                summary=f"~{(ooh_m/tot_m)*100:.0f}% of segmented minutes flagged out-of-hours on snapshot.",
                detail={
                    "reasons": ["out_of_hours_minute_share_high"],
                    "current_value": {"out_of_hours_minutes": ooh_m, "total_segmented_minutes": tot_m},
                    "suggested_action": "Review call-out pricing, SLA windows, and planned maintenance timing.",
                },
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_contract_id=job.contract_id,
            )

        comp = getattr(snap, "labour_cost_completeness", None) or "unavailable"
        if comp in ("partial", "unavailable", "fallback"):
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=f"labour:completeness-gap:job:{job.id}",
                recommendation_type="labour_costing_completeness_gap",
                category="labour_costing",
                severity="low" if comp == "fallback" else "medium",
                confidence="high",
                title="Labour costing completeness gap",
                summary=f"Snapshot labour marked `{comp}` — review punches, approvals, and profile configuration.",
                detail={
                    "reasons": ["labour_costing_not_complete"],
                    "current_value": {"completeness": comp},
                    "suggested_action": "Close timesheet approvals and align LabourRateProfile coverage.",
                },
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_contract_id=job.contract_id,
            )

    for c in db.query(Contract).filter(Contract.status == "active").all():
        snaps = (
            db.query(JobCostSnapshot)
            .join(Job, JobCostSnapshot.job_id == Job.id)
            .filter(Job.contract_id == c.id, JobCostSnapshot.completed_at >= window_start)
            .all()
        )
        if len(snaps) < 2:
            continue
        tw = sum(float(s.travel_cost or 0) for s in snaps)
        lw = sum(float(s.labour_cost or 0) for s in snaps)
        if lw + tw > 250 and tw / max(lw, 1e-6) > 0.25:
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=f"labour:travel-heavy-contract:{c.id}",
                recommendation_type="labour_travel_heavy_contract",
                category="labour_costing",
                severity="medium",
                confidence="medium",
                title="Travel labour eroding contract work labour",
                summary=f"Travel cost ~{(tw/max(lw,1e-6))*100:.0f}% of work labour (last 90d snapshots).",
                detail={
                    "reasons": ["travel_labour_share_elevated"],
                    "current_value": {"travel_labour_cost": round(tw, 2), "work_labour_cost": round(lw, 2)},
                    "suggested_action": "Territory planning, first-fix rate, or mobilisation charges.",
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
            )
