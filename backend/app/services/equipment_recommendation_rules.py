"""
Operational recommendations for field equipment readiness (ops scan).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.dispatch.models import Job
from backend.app.modules.equipment.models import FieldEquipment, JobEquipmentRequirement
from backend.app.services.equipment_readiness_service import (
    compute_calibration_status,
    evaluate_job_equipment_readiness,
    utc_now,
)
from backend.app.services.recommendation_engine import _register


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def register_equipment_recommendations(db: Session, active_keys: set[str], *, now: datetime | None = None) -> None:
    now = now or utc_now()
    window = int(getattr(settings, "PHI_DPS_EQUIPMENT_CALIBRATION_DUE_SOON_DAYS", 30))
    tomorrow_start = (_aware(now) or now).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # Rule A: mandatory equipment missing / blocked for active assigned job
    for job in (
        db.query(Job)
        .filter(
            Job.status.not_in(["completed", "closed", "cancelled"]),
            Job.assigned_engineer_id.isnot(None),
        )
        .all()
    ):
        if not db.query(JobEquipmentRequirement).filter(JobEquipmentRequirement.job_id == job.id).first():
            continue
        ev = evaluate_job_equipment_readiness(db, job_id=job.id, for_engineer_id=job.assigned_engineer_id, now=now)
        if ev.readiness_status == "blocked":
            key = f"equipment:required-missing:job:{job.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="equipment_required_missing",
                category="equipment_readiness",
                severity="high",
                confidence="high",
                title=f"Job missing required field equipment",
                summary="Assigned engineer does not satisfy mandatory equipment/calibration requirements.",
                detail={
                    "reasons": ev.blocking_flags + ev.warnings[:8],
                    "missing": ev.missing_required_equipment,
                    "expired": ev.expired_required_equipment,
                    "suggested_action": "Reassign equipment, swap engineer, or adjust job requirements.",
                },
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_engineer_id=job.assigned_engineer_id,
            )
        elif ev.readiness_status == "warning":
            key = f"equipment:warning:job:{job.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="equipment_readiness_warning",
                category="equipment_readiness",
                severity="medium",
                confidence="medium",
                title=f"Equipment readiness warning on job",
                summary="Calibration due soon or optional gaps detected for assigned engineer.",
                detail={"reasons": ev.warnings, "due_soon": ev.due_soon_equipment},
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_engineer_id=job.assigned_engineer_id,
            )

        # Rule B: compliance-sensitive job with calibration failure
        if bool(getattr(job, "compliance_required", False)) and ev.expired_required_equipment:
            key = f"equipment:cal-expired-compliance:job:{job.id}"
            _register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="equipment_calibration_compliance_risk",
                category="equipment_compliance",
                severity="critical",
                confidence="high",
                title="Compliance job — calibrated equipment invalid",
                summary="Compliance-sensitive work has expired or invalid calibration on required device(s).",
                detail={
                    "reasons": [x.get("reason") for x in ev.expired_required_equipment],
                    "items": ev.expired_required_equipment,
                    "suggested_action": "Do not proceed until valid calibration or substitute equipment is confirmed.",
                },
                entity_type="job",
                entity_id=job.id,
                related_job_id=job.id,
                related_engineer_id=job.assigned_engineer_id,
            )

    # Rule C: calibration due soon on equipment assigned to engineer with heavy workload tomorrow
    for eq in db.query(FieldEquipment).filter(FieldEquipment.assigned_engineer_id.isnot(None)).all():
        if not eq.calibration_required:
            continue
        st = compute_calibration_status(eq, now=now)
        if st != "due_soon":
            continue
        eid = eq.assigned_engineer_id
        assert eid
        cnt = (
            db.query(Job)
            .filter(
                Job.assigned_engineer_id == eid,
                Job.scheduled_at.isnot(None),
                Job.scheduled_at >= tomorrow_start,
                Job.scheduled_at < tomorrow_end,
                Job.status.not_in(["completed", "closed", "cancelled"]),
            )
            .count()
        )
        if cnt < 3:
            continue
        key = f"equipment:due-soon-heavy-day:eq:{eq.id}:eng:{eid}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="equipment_calibration_due_heavy_schedule",
            category="equipment_readiness",
            severity="medium",
            confidence="medium",
            title=f"Calibration due soon on busy schedule: {eq.equipment_code}",
            summary=f"Device calibration due within {window}d while engineer has {cnt} jobs scheduled tomorrow.",
            detail={
                "equipment_id": eq.id,
                "engineer_id": eid,
                "jobs_tomorrow": cnt,
                "calibration_due_date": eq.calibration_due_date.isoformat() if eq.calibration_due_date else None,
            },
            entity_type="equipment",
            entity_id=eq.id,
            related_engineer_id=eid,
        )

    # Rule D: out_of_service equipment still referenced by a job requirement
    for req in db.query(JobEquipmentRequirement).filter(JobEquipmentRequirement.specific_equipment_id.isnot(None)).all():
        eq = db.get(FieldEquipment, req.specific_equipment_id or "")
        if not eq or eq.status != "out_of_service":
            continue
        job = db.get(Job, req.job_id)
        if not job or job.status in ("completed", "closed", "cancelled"):
            continue
        key = f"equipment:oos-referenced:req:{req.id}:eq:{eq.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="equipment_out_of_service_referenced",
            category="equipment_readiness",
            severity="high",
            confidence="high",
            title=f"Out-of-service equipment still required: {eq.equipment_code}",
            summary="A job requirement points at equipment marked out of service.",
            detail={
                "job_id": req.job_id,
                "requirement_id": req.id,
                "equipment_id": eq.id,
                "suggested_action": "Update requirement, repair equipment, or substitute asset.",
            },
            entity_type="equipment",
            entity_id=eq.id,
            related_job_id=req.job_id,
        )

    # Rule E: tomorrow's jobs — engineer/van readiness gap
    for job in (
        db.query(Job)
        .filter(
            Job.scheduled_at.isnot(None),
            Job.scheduled_at >= tomorrow_start,
            Job.scheduled_at < tomorrow_end,
            Job.status.not_in(["completed", "closed", "cancelled"]),
            Job.assigned_engineer_id.isnot(None),
        )
        .all()
    ):
        if not db.query(JobEquipmentRequirement).filter(JobEquipmentRequirement.job_id == job.id).first():
            continue
        ev = evaluate_job_equipment_readiness(
            db, job_id=job.id, for_engineer_id=job.assigned_engineer_id, now=now
        )
        if ev.readiness_status == "ready":
            continue
        key = f"equipment:tomorrow-gap:job:{job.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="equipment_tomorrow_schedule_gap",
            category="equipment_readiness",
            severity="high" if ev.readiness_status == "blocked" else "medium",
            confidence="high",
            title="Tomorrow's job — equipment readiness gap",
            summary=f"Scheduled job has equipment readiness state: {ev.readiness_status}.",
            detail={
                "readiness": ev.to_dict(),
                "suggested_action": "Pre-stage tools tonight or reassign coverage.",
            },
            entity_type="job",
            entity_id=job.id,
            related_job_id=job.id,
            related_engineer_id=job.assigned_engineer_id,
        )
