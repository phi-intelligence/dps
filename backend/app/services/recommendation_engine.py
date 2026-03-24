"""
Deterministic operational recommendation scan engine.

Produces/upgrades OperationalRecommendation rows with stable ``recommendation_key`` dedupe
while rows are **open**. Full product narrative: ``PHI_DPS_Gap_Analysis_and_Target_Workflows.md``
§5.14 *Recommendation lifecycle — current vs future product rules*.

**Implemented lifecycle (see also** ``recommendation_lifecycle.py`` **and config** ``PHI_DPS_OPS_REC_*`` **)**
- **Reopen / cooldown:** New open rows are not created for a ``recommendation_key`` until cooldown
  elapses after the last **dismissed** / **resolved** / **auto_resolved** close, unless severity
  increases or ``source_rule_version`` changed. **Manual** ``POST .../reopen`` bypasses cooldown.
- **Per-row snooze:** ``suppressed_until`` hides items from default list/dashboard counts; scans can
  still refresh the row.
- **Scope suppressions:** Table ``recommendation_suppressions`` (exact key or category+optional
  contract/site) blocks **new** rows while active; existing **open** rows are still updated and
  kept in ``active_keys`` so auto-resolve does not drop them.
- **Occurrence escalation:** Rolling window fire count bumps severity one step (configurable).

Explainability: ``detail.lifecycle`` carries reopen/cooldown/escalation notes where relevant.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.assets.models import Asset
from backend.app.modules.compliance.models import Certificate
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.sla_clock_service import aggregate_contract_sla_performance, compute_job_sla_status
from backend.app.modules.costing.models import JobCostSnapshot
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.recommendation_engine import compute_ranked_dispatch_recommendations
from backend.app.modules.dispatch.position_resolver_service import resolve_operational_position_for_engineer
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.inventory.models import StockItem, StockReservation
from backend.app.modules.inventory.service import parts_usage_blocks_strict_completion
from backend.app.modules.ops.models import OperationalRecommendation
from backend.app.modules.ppm.models import PpmSchedule
from backend.app.modules.competence.models import Qualification
from backend.app.services.job_costing import get_job_cost_snapshot
from backend.app.services import recommendation_lifecycle as rec_lc


RULE_ENGINE_VERSION = getattr(settings, "PHI_DPS_OPS_RECOMMENDATION_RULE_VERSION", "2025.03.v1")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _detail(**kwargs: Any) -> str:
    return json.dumps(kwargs, default=str)


def _register(
    db: Session,
    *,
    active_keys: set[str],
    recommendation_key: str,
    recommendation_type: str,
    category: str,
    severity: str,
    confidence: str,
    title: str,
    summary: str,
    detail: dict[str, Any],
    entity_type: str,
    entity_id: str,
    related_job_id: str | None = None,
    related_engineer_id: str | None = None,
    related_site_id: str | None = None,
    related_asset_id: str | None = None,
    related_contract_id: str | None = None,
    related_invoice_id: str | None = None,
) -> OperationalRecommendation | None:
    now = utc_now()
    open_row = (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.recommendation_key == recommendation_key,
            OperationalRecommendation.status == "open",
        )
        .first()
    )

    if rec_lc.active_global_suppression_applies(
        db,
        recommendation_key=recommendation_key,
        category=category,
        related_contract_id=related_contract_id,
        related_site_id=related_site_id,
        now=now,
    ):
        if not open_row:
            return None

    sev, esc_extra = rec_lc.apply_occurrence_escalation(
        db, recommendation_key=recommendation_key, base_severity=severity, now=now
    )
    detail_merged = rec_lc.merge_lifecycle_into_detail(detail, esc_extra)

    if open_row:
        active_keys.add(recommendation_key)
        rec_lc.record_occurrence(db, recommendation_key=recommendation_key, now=now)
        open_row.recommendation_type = recommendation_type
        open_row.category = category
        open_row.severity = sev
        open_row.confidence = confidence
        open_row.title = title
        open_row.summary = summary
        open_row.detail_json = _detail(**detail_merged)
        open_row.entity_type = entity_type
        open_row.entity_id = entity_id
        open_row.related_job_id = related_job_id
        open_row.related_engineer_id = related_engineer_id
        open_row.related_site_id = related_site_id
        open_row.related_asset_id = related_asset_id
        open_row.related_contract_id = related_contract_id
        open_row.related_invoice_id = related_invoice_id
        open_row.source_rule_version = RULE_ENGINE_VERSION
        open_row.updated_at = now
        return open_row

    blocked, cool_detail = rec_lc.cooldown_blocks_new_open(
        db,
        recommendation_key=recommendation_key,
        new_severity=sev,
        current_rule_version=RULE_ENGINE_VERSION,
        now=now,
    )
    if blocked:
        return None
    if cool_detail:
        detail_merged = rec_lc.merge_lifecycle_into_detail(detail_merged, cool_detail)

    active_keys.add(recommendation_key)
    rec_lc.record_occurrence(db, recommendation_key=recommendation_key, now=now)

    row = OperationalRecommendation(
        recommendation_type=recommendation_type,
        category=category,
        severity=sev,
        confidence=confidence,
        title=title,
        summary=summary,
        detail_json=_detail(**detail_merged),
        entity_type=entity_type,
        entity_id=entity_id,
        related_job_id=related_job_id,
        related_engineer_id=related_engineer_id,
        related_site_id=related_site_id,
        related_asset_id=related_asset_id,
        related_contract_id=related_contract_id,
        related_invoice_id=related_invoice_id,
        status="open",
        recommendation_key=recommendation_key,
        source_rule_version=RULE_ENGINE_VERSION,
        closed_as=None,
        suppressed_until=None,
        suppression_notes=None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    return row


def auto_resolve_stale_open(db: Session, *, active_keys: set[str]) -> int:
    """Resolve open recommendations no longer produced by this scan."""
    n = 0
    now = utc_now()
    for r in (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.status == "open",
            OperationalRecommendation.source_rule_version == RULE_ENGINE_VERSION,
        )
        .all()
    ):
        if r.recommendation_key not in active_keys:
            r.status = "resolved"
            r.closed_as = "auto_resolved"
            r.resolved_at = now
            r.resolution_notes = "auto: condition cleared by recommendation scan"
            r.updated_at = now
            n += 1
    return n


def auto_resolve_stale_for_job(db: Session, *, job_id: str, active_keys: set[str]) -> int:
    n = 0
    now = utc_now()
    for r in (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.related_job_id == job_id,
            OperationalRecommendation.status == "open",
            OperationalRecommendation.source_rule_version == RULE_ENGINE_VERSION,
        )
        .all()
    ):
        if r.recommendation_key not in active_keys:
            r.status = "resolved"
            r.closed_as = "auto_resolved"
            r.resolved_at = now
            r.resolution_notes = "auto: job-scoped scan — condition cleared"
            r.updated_at = now
            n += 1
    return n


def _active_jobs_q(db: Session):
    return db.query(Job).filter(Job.status.not_in(["completed", "closed", "cancelled"]))


def rule_sla_eta_risk(db: Session, job: Job, active_keys: set[str], *, now: datetime) -> None:
    st = compute_job_sla_status(db, job_id=job.id, now=now)
    if st.get("sla_status_summary") == "no_sla_context":
        return
    targets_breached = st.get("response_breached") or st.get("attendance_breached") or st.get("resolution_breached")
    imminent = st.get("warning_state") not in (None, "none")
    if not targets_breached and not imminent:
        return
    sev = "critical" if targets_breached else "high"
    key = f"sla-risk:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="sla_breach_risk",
        category="sla_risk",
        severity=sev,
        confidence="high",
        title=f"SLA risk on job {job.id[:8]}…",
        summary=st.get("sla_status_summary", "sla concern"),
        detail={
            "reasons": [
                f"response_breached={st.get('response_breached')}",
                f"attendance_breached={st.get('attendance_breached')}",
                f"resolution_breached={st.get('resolution_breached')}",
                f"warning_state={st.get('warning_state')}",
            ],
            "current_value": {
                "response_minutes": st.get("response_time_minutes"),
                "attendance_minutes": st.get("attendance_time_minutes"),
                "resolution_minutes": st.get("resolution_time_minutes"),
            },
            "suggested_action": "Reassign, expedite travel, or reset customer expectations with an update.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
        related_engineer_id=job.assigned_engineer_id,
        related_contract_id=job.contract_id,
        related_site_id=job.site_id,
    )


def rule_stale_telemetry(db: Session, job: Job, active_keys: set[str], *, now: datetime) -> None:
    if not job.assigned_engineer_id:
        return
    op = resolve_operational_position_for_engineer(db, engineer_id=job.assigned_engineer_id, now=now)
    if not op or op.freshness_status != "stale":
        return
    key = f"dispatch:stale-telemetry:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="stale_telemetry_active_job",
        category="dispatch_risk",
        severity="high",
        confidence="high",
        title="Stale live telemetry for assigned engineer",
        summary="Assigned engineer position data is stale while the job is still active.",
        detail={
            "reasons": ["Engineer telemetry classified as stale during active assignment."],
            "suggested_action": "Ping engineer app, confirm device, or dispatch alternative tracking.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
        related_engineer_id=job.assigned_engineer_id,
    )


def rule_no_qualified_dispatch_candidate(db: Session, job: Job, active_keys: set[str]) -> None:
    try:
        res = compute_ranked_dispatch_recommendations(db, job_id=job.id, limit=5, include_stale=False)
    except Exception:
        return
    matched = [r for r in res.recommendations if r.competency_match]
    urgent = (job.sla_priority or "").lower() in ("emergency", "urgent") or job.dispatch_priority >= 8
    if matched or not urgent:
        return
    key = f"dispatch:no-qualified-candidate:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="no_qualified_dispatch_candidate",
        category="dispatch_risk",
        severity="critical",
        confidence="medium",
        title="No qualified dispatch candidate (fresh telemetry)",
        summary="High-priority job has no competency-matched engineer with acceptable telemetry freshness.",
        detail={
            "reasons": ["Ranked recommendations returned zero competency matches with include_stale=false."],
            "suggested_action": "Relax geography, add cover engineer, or adjust required competencies.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
    )


def rule_engineer_overload(db: Session, active_keys: set[str]) -> None:
    rows = (
        db.query(Job.assigned_engineer_id, func.count(Job.id))
        .filter(Job.assigned_engineer_id.isnot(None), Job.status.not_in(["completed", "closed", "cancelled"]))
        .group_by(Job.assigned_engineer_id)
        .all()
    )
    if not rows:
        return
    counts = {eid: int(c) for eid, c in rows if eid}
    if not counts:
        return
    mx = max(counts.values())
    avg = sum(counts.values()) / max(len(counts), 1)
    if mx < 5 or mx < avg * 1.8:
        return
    hot = next(eid for eid, c in counts.items() if c == mx)
    key = f"dispatch:engineer-overload:{hot}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="engineer_overload",
        category="dispatch_risk",
        severity="medium",
        confidence="medium",
        title="Engineer workload imbalance",
        summary=f"Engineer {hot[:8]}… carries {mx} active jobs vs team average {avg:.1f}.",
        detail={
            "reasons": ["Active assignment count exceeds peer average materially."],
            "current_value": {"active_jobs": mx, "peer_average": round(avg, 2)},
            "suggested_action": "Consider rebalancing open jobs to peers with capacity.",
        },
        entity_type="engineer",
        entity_id=hot,
        related_engineer_id=hot,
    )


def rule_parts_reconciliation_block(db: Session, job: Job, active_keys: set[str]) -> None:
    try:
        if not parts_usage_blocks_strict_completion(db, job_id=job.id):
            return
    except Exception:
        return
    key = f"inventory:parts-reconciliation-block:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="parts_reconciliation_block",
        category="inventory_risk",
        severity="high",
        confidence="high",
        title="Parts usage blocked for completion",
        summary="Strict parts reconciliation or unreconciled usage is blocking job completion.",
        detail={
            "reasons": ["parts_usage_blocks_strict_completion returned true."],
            "suggested_action": "Review parts submission, approve reconciliation, or adjust policy.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
    )


def rule_low_stock_reserved(db: Session, active_keys: set[str]) -> None:
    for item in db.query(StockItem).all():
        avail = float(item.on_hand_quantity or 0) - float(item.reserved_quantity or 0)
        if item.reserved_quantity <= 0:
            continue
        if avail >= 0:
            continue
        key = f"inventory:shortage:item:{item.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="stock_shortage_reserved",
            category="inventory_risk",
            severity="critical",
            confidence="high",
            title=f"Stock shortage: {item.sku}",
            summary="Reserved demand exceeds effective available quantity for this SKU.",
            detail={
                "reasons": ["on_hand - reserved < 0 at aggregate level."],
                "current_value": {
                    "on_hand": item.on_hand_quantity,
                    "reserved": item.reserved_quantity,
                    "sku": item.sku,
                },
                "suggested_action": "Replenish warehouse or release/adjust reservations.",
            },
            entity_type="stock_item",
            entity_id=item.id,
        )


def rule_cost_variance(db: Session, job: Job, active_keys: set[str]) -> None:
    if job.status not in ("completed", "closed"):
        return
    snap = get_job_cost_snapshot(db, job_id=job.id)
    if not snap:
        return
    est = float(snap.estimated_material_cost or 0)
    act = float(snap.actual_material_cost or 0)
    if est <= 1e-6:
        return
    pct = (act - est) / est * 100.0
    if pct < 25:
        return
    key = f"costing:material-variance:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="material_cost_variance",
        category="costing_variance",
        severity="high" if pct < 60 else "critical",
        confidence="high",
        title="Material cost variance vs estimate",
        summary=f"Actual material cost {act:.2f} vs estimated {est:.2f} ({pct:+.1f}%).",
        detail={
            "reasons": ["Snapshot actual materially exceeds estimated material cost."],
            "current_value": {"actual": act, "estimated": est, "variance_pct": round(pct, 2)},
            "suggested_action": "Review usage, pricing, and quote alignment before next similar job.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
        related_contract_id=job.contract_id,
    )


def rule_invoice_hold(db: Session, inv: Invoice, active_keys: set[str]) -> None:
    job = db.get(Job, inv.job_id)
    if not job:
        return
    reasons: list[str] = []
    if job.status in ("completed", "closed") and not inv.job_cost_snapshot_id:
        reasons.append("Invoice lacks costing snapshot link while job is completed.")
    if job.status in ("completed", "closed"):
        cert = (
            db.query(Certificate)
            .filter(Certificate.job_id == job.id, Certificate.status.in_(["generated", "signed"]))
            .first()
        )
        if not cert:
            reasons.append("No compliance certificate on file for completed job.")
    if not reasons:
        return
    key = f"invoice:hold:{inv.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="invoice_release_hold",
        category="invoice_hold",
        severity="high",
        confidence="medium",
        title=f"Invoice {inv.id[:8]}… should be held / reviewed",
        summary="; ".join(reasons),
        detail={"reasons": reasons, "suggested_action": "Attach snapshot, complete compliance, or document waiver."},
        entity_type="invoice",
        entity_id=inv.id,
        related_invoice_id=inv.id,
        related_job_id=job.id,
        related_contract_id=job.contract_id,
    )


def rule_low_margin(db: Session, job: Job, active_keys: set[str]) -> None:
    if job.status not in ("completed", "closed"):
        return
    snap = get_job_cost_snapshot(db, job_id=job.id)
    if not snap:
        return
    inv = db.query(Invoice).filter(Invoice.job_id == job.id).order_by(Invoice.created_at.desc()).first()
    if not inv:
        return
    sell = float(inv.grand_total or 0)
    cost = (
        float(snap.actual_material_cost or 0)
        + float(snap.labour_cost or 0)
        + float(getattr(snap, "travel_cost", 0) or 0)
    )
    if sell <= 0:
        return
    margin_pct = (sell - cost) / sell * 100.0
    if margin_pct > 5:
        return
    key = f"costing:low-margin:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="low_margin_job",
        category="costing_variance",
        severity="critical" if margin_pct < 0 else "high",
        confidence="medium",
        title="Low or negative margin on completed work",
        summary=f"Indicative margin ~{margin_pct:.1f}% on snapshot billable vs actual.",
        detail={
            "reasons": ["Billable totals vs actual costs imply thin/negative margin."],
            "current_value": {"margin_pct": round(margin_pct, 2), "sell": sell, "cost": cost},
            "suggested_action": "Review pricing, leakage, and contract profitability.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
        related_contract_id=job.contract_id,
        related_invoice_id=inv.id,
    )


def rule_completion_compliance_gap(db: Session, job: Job, active_keys: set[str]) -> None:
    if job.status != "completed" or not job.compliance_required:
        return
    cert = db.query(Certificate).filter(Certificate.job_id == job.id).first()
    if cert:
        return
    key = f"compliance:missing-cert:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="completion_compliance_gap",
        category="compliance_blocker",
        severity="high",
        confidence="high",
        title="Completed job missing compliance record",
        summary="Job flagged compliance_required but no certificate exists.",
        detail={"reasons": ["Operational completion without certificate."], "suggested_action": "Generate or attach certificate."},
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
        related_site_id=job.site_id,
        related_asset_id=job.asset_id,
    )


def rule_qualification_expiry(db: Session, active_keys: set[str], *, now: datetime) -> None:
    horizon = now + timedelta(days=30)
    for q in db.query(Qualification).filter(Qualification.status == "active", Qualification.expires_at.isnot(None)).all():
        if _aware(q.expires_at) > horizon:
            continue
        upcoming = (
            _active_jobs_q(db)
            .filter(Job.assigned_engineer_id == q.engineer_user_id)
            .count()
        )
        if upcoming == 0:
            continue
        key = f"compliance:qual-expiry:{q.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="qualification_expiring",
            category="compliance_blocker",
            severity="medium",
            confidence="high",
            title=f"Qualification expiring: {q.competency}",
            summary=f"Engineer competency expires {q.expires_at.date()} with active assignments.",
            detail={
                "reasons": ["Qualification expires within 30 days with open jobs."],
                "suggested_action": "Schedule renewal training / evidence upload.",
            },
            entity_type="qualification",
            entity_id=q.id,
            related_engineer_id=q.engineer_user_id,
        )


def rule_asset_service_overdue(db: Session, active_keys: set[str], *, now: datetime) -> None:
    for a in db.query(Asset).filter(Asset.next_service_date.isnot(None)).all():
        if _aware(a.next_service_date) > _aware(now):
            continue
        key = f"asset:service-overdue:{a.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="asset_service_overdue",
            category="asset_attention",
            severity="medium",
            confidence="high",
            title=f"Asset service overdue: {a.name}",
            summary="next_service_date is in the past.",
            detail={"reasons": ["Planned maintenance date elapsed."], "suggested_action": "Schedule PPM or reactive visit."},
            entity_type="asset",
            entity_id=a.id,
            related_asset_id=a.id,
            related_site_id=a.site_id,
        )


def rule_contract_expiry(db: Session, active_keys: set[str], *, now: datetime) -> None:
    window_days = int(getattr(settings, "PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS", "90"))
    for c in db.query(Contract).filter(Contract.status == "active").all():
        if not c.term_end_at:
            continue
        if _aware(c.term_end_at) > _aware(now) + timedelta(days=window_days):
            continue
        key = f"contract:expiry:{c.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="contract_nearing_expiry",
            category="contract_attention",
            severity="high",
            confidence="high",
            title=f"Contract nearing expiry: {c.contract_code}",
            summary=f"Term ends {c.term_end_at.date().isoformat()}",
            detail={
                "reasons": [f"Within {window_days}d renewal window."],
                "suggested_action": "Start renewal / commercial review.",
            },
            entity_type="contract",
            entity_id=c.id,
            related_contract_id=c.id,
        )


def rule_contract_repeated_sla(db: Session, c: Contract, active_keys: set[str]) -> None:
    perf = aggregate_contract_sla_performance(db, contract_id=c.id)
    bc = int(perf.get("breached_job_count") or 0)
    if bc < 3:
        return
    key = f"contract:sla-breaches:{c.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="contract_repeated_sla_breaches",
        category="contract_attention",
        severity="high",
        confidence="medium",
        title=f"Repeated SLA issues on contract {c.contract_code}",
        summary=f"{bc} jobs show SLA breach signals under this contract.",
        detail={
            "reasons": ["Aggregate SLA performance shows multiple breached jobs."],
            "current_value": {"breached_job_count": bc},
            "suggested_action": "Service review, capacity, or SLA policy alignment.",
        },
        entity_type="contract",
        entity_id=c.id,
        related_contract_id=c.id,
    )


def rule_high_reactive_volume(db: Session, c: Contract, active_keys: set[str], *, now: datetime) -> None:
    since = now - timedelta(days=30)
    n = (
        db.query(Job)
        .filter(
            Job.contract_id == c.id,
            Job.work_type == "reactive",
            Job.created_at >= since,
        )
        .count()
    )
    if n < 10:
        return
    key = f"contract:reactive-volume:{c.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="high_reactive_volume",
        category="contract_attention",
        severity="medium",
        confidence="medium",
        title="High reactive volume on contract (30d)",
        summary=f"{n} reactive jobs logged in rolling 30 days.",
        detail={"reasons": ["Reactive demand spike may erode PPM value."], "current_value": {"reactive_jobs_30d": n}},
        entity_type="contract",
        entity_id=c.id,
        related_contract_id=c.id,
    )


def register_ppm_overdue_if_needed(db: Session, sch: PpmSchedule, active_keys: set[str], *, now: datetime) -> None:
    if not sch.active or _aware(sch.next_due_date) >= _aware(now):
        return
    key = f"contract:ppm-overdue:{sch.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="ppm_schedule_overdue",
        category="contract_attention",
        severity="high",
        confidence="high",
        title=f"Overdue PPM schedule: {sch.title}",
        summary=f"Next due {sch.next_due_date.isoformat()} is past.",
        detail={"reasons": ["Active PPM schedule past next_due_date."], "suggested_action": "Run generation or reschedule."},
        entity_type="ppm_schedule",
        entity_id=sch.id,
        related_contract_id=sch.contract_id,
        related_site_id=sch.site_id,
        related_asset_id=sch.asset_id,
    )


def rule_ppm_overdue_scan_all(db: Session, active_keys: set[str], *, now: datetime) -> None:
    for sch in db.query(PpmSchedule).filter(PpmSchedule.active.is_(True)).all():
        register_ppm_overdue_if_needed(db, sch, active_keys, now=now)


def rule_customer_on_my_way_gap(db: Session, job: Job, active_keys: set[str], *, now: datetime) -> None:
    if not job.en_route_at and not job.on_my_way_sent_at:
        return
    if job.customer_notified_at:
        return
    ref = job.en_route_at or job.on_my_way_sent_at
    if not ref or (_aware(now) - _aware(ref)).total_seconds() < 15 * 60:
        return
    key = f"cx:on-my-way-notify:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="customer_on_my_way_not_notified",
        category="customer_experience_risk",
        severity="medium",
        confidence="medium",
        title="Customer may not have on-the-way confirmation",
        summary="Job is en route / on-my-way but customer_notified_at is still empty after threshold.",
        detail={"reasons": [">15m since en_route/on_my_way without customer_notified_at."], "suggested_action": "Send portal/SMS update."},
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
    )


def rule_low_eta_confidence_imminent(db: Session, job: Job, active_keys: set[str], *, now: datetime) -> None:
    if job.status in ("completed", "closed", "cancelled"):
        return
    if not job.scheduled_at:
        return
    if (_aware(job.scheduled_at) - _aware(now)).total_seconds() > 2 * 3600:
        return
    from backend.app.modules.dispatch.operational_tracking_service import compute_internal_job_eta

    eta = compute_internal_job_eta(db, job_id=job.id, now=now)
    conf = (eta.get("eta_confidence") or "").lower()
    src = (eta.get("eta_source") or "").lower()
    if conf not in ("low", "unavailable") and src != "unavailable":
        return
    key = f"cx:low-eta-confidence:job:{job.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="low_eta_confidence_imminent_visit",
        category="customer_experience_risk",
        severity="medium",
        confidence="high",
        title="Weak ETA signal before imminent visit",
        summary="Visit scheduled within 2h but ETA confidence is low/unavailable.",
        detail={
            "reasons": ["Poor telemetry or missing schedule/manual override near visit window."],
            "suggested_action": "Confirm engineer position or set manual ETA for customer comms.",
        },
        entity_type="job",
        entity_id=job.id,
        related_job_id=job.id,
    )


def rule_overdue_invoice_cx(db: Session, inv: Invoice, active_keys: set[str], *, now: datetime) -> None:
    if inv.status == "paid" or inv.paid_at:
        return
    if (_aware(now) - _aware(inv.created_at)).days < 30:
        return
    job = db.get(Job, inv.job_id)
    if job and job.status not in ("completed", "closed"):
        return
    key = f"cx:overdue-invoice:{inv.id}"
    _register(
        db,
        active_keys=active_keys,
        recommendation_key=key,
        recommendation_type="overdue_invoice_followup",
        category="customer_experience_risk",
        severity="medium",
        confidence="high",
        title=f"Overdue invoice {inv.id[:8]}…",
        summary="Unpaid invoice >30d after recent completed work context.",
        detail={"reasons": ["Cash collection / customer follow-up risk."], "suggested_action": "Collections outreach or portal nudge."},
        entity_type="invoice",
        entity_id=inv.id,
        related_invoice_id=inv.id,
        related_job_id=inv.job_id,
    )


def scan_job_recommendations(db: Session, *, job_id: str, now: datetime | None = None) -> int:
    now = now or utc_now()
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    active_keys: set[str] = set()
    rule_sla_eta_risk(db, job, active_keys, now=now)
    rule_stale_telemetry(db, job, active_keys, now=now)
    rule_no_qualified_dispatch_candidate(db, job, active_keys)
    rule_parts_reconciliation_block(db, job, active_keys)
    rule_cost_variance(db, job, active_keys)
    rule_low_margin(db, job, active_keys)
    rule_completion_compliance_gap(db, job, active_keys)
    rule_customer_on_my_way_gap(db, job, active_keys, now=now)
    rule_low_eta_confidence_imminent(db, job, active_keys, now=now)
    auto_resolve_stale_for_job(db, job_id=job_id, active_keys=active_keys)
    db.commit()
    return len(active_keys)


def scan_contract_recommendations(db: Session, *, contract_id: str, now: datetime | None = None) -> int:
    now = now or utc_now()
    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")
    active_keys: set[str] = set()
    window_days = int(getattr(settings, "PHI_DPS_CONTRACT_RENEWAL_SCAN_DAYS", "90"))
    if c.status == "active" and c.term_end_at and _aware(c.term_end_at) <= _aware(now) + timedelta(days=window_days):
        key = f"contract:expiry:{c.id}"
        _register(
            db,
            active_keys=active_keys,
            recommendation_key=key,
            recommendation_type="contract_nearing_expiry",
            category="contract_attention",
            severity="high",
            confidence="high",
            title=f"Contract nearing expiry: {c.contract_code}",
            summary=f"Term ends {c.term_end_at.date().isoformat()}",
            detail={
                "reasons": [f"Within {window_days}d renewal window."],
                "suggested_action": "Start renewal / commercial review.",
            },
            entity_type="contract",
            entity_id=c.id,
            related_contract_id=c.id,
        )
    rule_contract_repeated_sla(db, c, active_keys)
    rule_high_reactive_volume(db, c, active_keys, now=now)
    for sch in db.query(PpmSchedule).filter(PpmSchedule.contract_id == contract_id, PpmSchedule.active.is_(True)).all():
        register_ppm_overdue_if_needed(db, sch, active_keys, now=now)

    for r in (
        db.query(OperationalRecommendation)
        .filter(
            OperationalRecommendation.related_contract_id == contract_id,
            OperationalRecommendation.status == "open",
            OperationalRecommendation.source_rule_version == RULE_ENGINE_VERSION,
        )
        .all()
    ):
        if r.recommendation_key not in active_keys:
            r.status = "resolved"
            r.closed_as = "auto_resolved"
            r.resolved_at = now
            r.resolution_notes = "auto: contract scan — condition cleared"
            r.updated_at = now

    db.commit()
    return len(active_keys)


def scan_inventory_recommendations(db: Session) -> int:
    active_keys: set[str] = set()
    rule_low_stock_reserved(db, active_keys)
    db.commit()
    return len(active_keys)


def scan_asset_recommendations(db: Session, now: datetime | None = None) -> int:
    now = now or utc_now()
    active_keys: set[str] = set()
    rule_asset_service_overdue(db, active_keys, now=now)
    db.commit()
    return len(active_keys)


def run_recommendation_scan(
    db: Session, *, now: datetime | None = None, commit: bool = True
) -> dict[str, Any]:
    now = now or utc_now()
    rec_lc.prune_stale_occurrence_events(db)
    active_keys: set[str] = set()

    for job in _active_jobs_q(db).all():
        rule_sla_eta_risk(db, job, active_keys, now=now)
        rule_stale_telemetry(db, job, active_keys, now=now)
        rule_no_qualified_dispatch_candidate(db, job, active_keys)
        rule_parts_reconciliation_block(db, job, active_keys)
        rule_customer_on_my_way_gap(db, job, active_keys, now=now)
        rule_low_eta_confidence_imminent(db, job, active_keys, now=now)

    for job in db.query(Job).filter(Job.status.in_(["completed", "closed"])).all():
        rule_cost_variance(db, job, active_keys)
        rule_low_margin(db, job, active_keys)
        rule_completion_compliance_gap(db, job, active_keys)

    rule_engineer_overload(db, active_keys)
    rule_low_stock_reserved(db, active_keys)
    rule_qualification_expiry(db, active_keys, now=now)
    rule_asset_service_overdue(db, active_keys, now=now)
    rule_contract_expiry(db, active_keys, now=now)
    rule_ppm_overdue_scan_all(db, active_keys, now=now)

    for c in db.query(Contract).filter(Contract.status == "active").all():
        rule_contract_repeated_sla(db, c, active_keys)
        rule_high_reactive_volume(db, c, active_keys, now=now)

    for inv in db.query(Invoice).all():
        rule_invoice_hold(db, inv, active_keys)
        rule_overdue_invoice_cx(db, inv, active_keys, now=now)

    from backend.app.services.labour_recommendation_rules import register_labour_costing_recommendations

    register_labour_costing_recommendations(db, active_keys, now=now)

    from backend.app.services.contract_commercial_recommendations import register_contract_commercial_recommendations

    register_contract_commercial_recommendations(db, active_keys, now=now)

    from backend.app.services.equipment_recommendation_rules import register_equipment_recommendations

    register_equipment_recommendations(db, active_keys, now=now)

    from backend.app.services.vehicle_inspection_recommendation_rules import register_vehicle_inspection_recommendations

    register_vehicle_inspection_recommendations(db, active_keys, now=now)

    from backend.app.services.labour_calendar_recommendation_rules import register_labour_calendar_recommendations

    register_labour_calendar_recommendations(db, active_keys, now=now)

    resolved = auto_resolve_stale_open(db, active_keys=active_keys)
    if commit:
        db.commit()
    return {"keys_active": len(active_keys), "auto_resolved": resolved}
