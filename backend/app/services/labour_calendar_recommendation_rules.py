"""
Recommendations for missing labour rule sets, holiday calendar coverage, region mismatch, and OOH burden.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from backend.app.modules.contracts.models import Contract
from backend.app.modules.dispatch.models import Job
from backend.app.modules.labour.models import LabourRuleSet
from backend.app.modules.costing.models import JobCostSnapshot
from backend.app.services import recommendation_engine as reng
from backend.app.services.labour_rule_resolution_service import resolve_labour_rules_for_job


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def register_labour_calendar_recommendations(
    db: Session, active_keys: set[str], *, now: datetime | None = None
) -> None:
    now = now or utc_now()
    win_start = now - timedelta(days=90)

    # B: Holiday policy without calendar
    for rs in db.query(LabourRuleSet).filter(LabourRuleSet.active.is_(True)).all():
        if rs.holiday_calendar_id is None and (
            rs.holiday_public_policy in ("doubletime", "out_of_hours")
            or rs.holiday_company_policy in ("doubletime", "out_of_hours")
        ):
            key = f"labour_rules:holiday_policy_without_calendar:{rs.id}"
            if key in active_keys:
                continue
            reng._register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="labour_rules_configuration",
                category="labour_rules",
                severity="medium",
                confidence="high",
                title="Labour holiday policy without calendar",
                summary=f"Rule set “{rs.name}” applies holiday cost treatment but has no holiday calendar linked.",
                detail={
                    "rule_set_id": rs.id,
                    "rule_set_name": rs.name,
                    "holiday_public_policy": rs.holiday_public_policy,
                    "holiday_company_policy": rs.holiday_company_policy,
                },
                entity_type="labour_rule_set",
                entity_id=rs.id,
            )

    # A: Active contracts with completed jobs resolving to legacy labour rules only
    for c in db.query(Contract).filter(Contract.status == "active").all():
        jobs = (
            db.query(Job)
            .filter(
                Job.contract_id == c.id,
                Job.status.in_(["completed", "closed"]),
                Job.resolved_at.isnot(None),
                Job.resolved_at >= win_start,
            )
            .limit(5)
            .all()
        )
        if not jobs:
            continue
        all_legacy = True
        for j in jobs:
            r = resolve_labour_rules_for_job(db, j)
            if r.rule_set is not None:
                all_legacy = False
                break
        if not all_legacy:
            continue
        key = f"labour_rules:missing_rule_set:{c.id}"
        reng._register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="labour_rules_configuration",
            category="labour_rules",
            severity="medium",
            confidence="high",
            title="Configure regional labour rules for contract",
            summary=f"Contract {c.contract_code} has recent completed jobs using legacy UTC labour windows (no LabourRuleSet).",
            detail={"contract_id": c.id, "contract_code": c.contract_code},
            entity_type="contract",
            entity_id=c.id,
            related_contract_id=c.id,
        )

    # D: High OOH labour share on snapshots (contract-level)
    for c in db.query(Contract).filter(Contract.status == "active").all():
        rows = (
            db.query(JobCostSnapshot)
            .join(Job, JobCostSnapshot.job_id == Job.id)
            .filter(
                Job.contract_id == c.id,
                JobCostSnapshot.completed_at >= win_start,
            )
            .all()
        )
        if len(rows) < 2:
            continue
        lab = sum(float(s.labour_cost or 0) for s in rows)
        ooh = sum(float(getattr(s, "out_of_hours_labour_cost", 0) or 0) for s in rows)
        if lab > 1e-6 and (ooh / lab) > 0.45:
            key = f"labour_rules:high_ooh_burden:{c.id}"
            reng._register(
                db,
                active_keys=active_keys,
                recommendation_key=key,
                recommendation_type="labour_cost_pattern",
                category="labour_rules",
                severity="low",
                confidence="medium",
                title="Elevated out-of-hours labour cost",
                summary=f"Contract {c.contract_code}: {(ooh/lab)*100:.0f}% of labour cost from out-of-hours in the last 90 days.",
                detail={
                    "contract_id": c.id,
                    "ooh_labour": round(ooh, 2),
                    "total_labour": round(lab, 2),
                    "ratio": round(ooh / lab, 4),
                },
                entity_type="contract",
                entity_id=c.id,
                related_contract_id=c.id,
            )
