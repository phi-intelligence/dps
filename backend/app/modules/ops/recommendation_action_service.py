"""
Recommendation → decision-support workflow: deterministic suggestions, preview, explicit confirm, audit.

No autonomous execution: all meaningful changes require confirmed=True and run only after validation.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.compliance.schemas import CertificateGenerateIn
from backend.app.modules.compliance.service import generate_certificate
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import ContractRepricingReview
from backend.app.modules.dispatch.models import Job
from backend.app.modules.dispatch.recommendation_engine import compute_ranked_dispatch_recommendations
from backend.app.modules.dispatch.service import (
    assign_job,
    mark_job_on_my_way_for_customer,
    set_job_manual_eta_minutes,
)
from backend.app.modules.equipment.service import assign_or_move_equipment
from backend.app.modules.inventory.ledger_service import ensure_default_inventory_locations, get_default_warehouse
from backend.app.modules.inventory.models import StockItem, StockLocation, StockReservation
from backend.app.modules.inventory.service import release_reservation_by_id
from backend.app.modules.auth.models import User
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.ops.models import (
    OperationalRecommendation,
    RecommendationActionDecision,
    RecommendationActionSuggestion,
)
from backend.app.modules.ops import recommendation_action_catalog as catalog
from backend.app.modules.ops import service as ops_service
from backend.app.modules.vehicles.models import VehicleDefect
from backend.app.modules.vehicles.service import resolve_defect
from backend.app.services.authorization_service import (
    assert_rec_action_allowed,
    describe_rec_action_authorization,
)
from backend.app.services.job_costing import persist_job_cost_snapshot
from backend.app.services import low_risk_automation_service as low_risk_automation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(s: str | None) -> dict[str, Any]:
    if not s:
        return {}
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}


def _job_competencies(job: Job) -> list[str]:
    raw = _loads(job.required_competencies_json)
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    return []


def _invoice_hold_reasons(db: Session, inv: Invoice, job: Job | None) -> list[str]:
    if not job:
        return ["Invoice job not found."]
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
    return reasons


def _get_catalog_action(action_type: str) -> catalog.CatalogAction:
    try:
        return catalog.ACTION_DEFINITIONS[action_type]
    except KeyError as e:
        raise ValueError(f"Unknown action_type: {action_type}") from e


def _get_rec(db: Session, recommendation_id: str) -> OperationalRecommendation:
    r = db.get(OperationalRecommendation, recommendation_id)
    if not r:
        raise ValueError("Recommendation not found")
    return r


def ensure_action_suggestions(db: Session, *, recommendation_id: str) -> list[RecommendationActionSuggestion]:
    rec = _get_rec(db, recommendation_id)
    types = catalog.actions_for_recommendation_type(rec.recommendation_type)
    now = utc_now()
    out: list[RecommendationActionSuggestion] = []
    for at in types:
        ca = catalog.ACTION_DEFINITIONS[at]
        row = (
            db.query(RecommendationActionSuggestion)
            .filter(
                RecommendationActionSuggestion.recommendation_id == recommendation_id,
                RecommendationActionSuggestion.action_type == at,
            )
            .one_or_none()
        )
        if row:
            out.append(row)
            continue
        row = RecommendationActionSuggestion(
            id=str(uuid.uuid4()),
            recommendation_id=recommendation_id,
            action_type=at,
            action_label=ca.action_label,
            action_description=ca.action_description,
            action_status="available",
            preview_json=None,
            input_schema_json=_dumps(ca.input_schema),
            requires_confirmation=ca.requires_confirmation,
            requires_override_reason=ca.requires_override_reason,
            risk_level=ca.risk_level,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        out.append(row)
    db.commit()
    for row in out:
        db.refresh(row)
    return out


def _get_suggestion(
    db: Session, *, recommendation_id: str, action_type: str
) -> RecommendationActionSuggestion:
    row = (
        db.query(RecommendationActionSuggestion)
        .filter(
            RecommendationActionSuggestion.recommendation_id == recommendation_id,
            RecommendationActionSuggestion.action_type == action_type,
        )
        .one_or_none()
    )
    if not row:
        raise ValueError("Action suggestion not found for this recommendation (run list/actions to sync).")
    return row


def _log_decision(
    db: Session,
    *,
    recommendation_id: str,
    suggestion_id: str | None,
    decision_type: str,
    user_id: str,
    decision_notes: str | None = None,
    override_reason: str | None = None,
    preview_snapshot: dict[str, Any] | None = None,
    execution_result: dict[str, Any] | None = None,
    execution_status: str | None = None,
) -> RecommendationActionDecision:
    d = RecommendationActionDecision(
        id=str(uuid.uuid4()),
        recommendation_id=recommendation_id,
        action_suggestion_id=suggestion_id,
        decision_type=decision_type,
        decided_by_user_id=user_id,
        decided_at=utc_now(),
        decision_notes=decision_notes,
        override_reason=override_reason,
        preview_snapshot_json=_dumps(preview_snapshot) if preview_snapshot is not None else None,
        execution_result_json=_dumps(execution_result) if execution_result is not None else None,
        execution_status=execution_status,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _base_preview_dict(
    *,
    allowed: bool,
    reason_suggested: str,
    preconditions: list[str],
    affected_entities: list[dict[str, Any]],
    expected_effect: str,
    warnings: list[str],
    ca: catalog.CatalogAction,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "allowed": allowed,
        "reason_suggested": reason_suggested,
        "preconditions": preconditions,
        "affected_entities": affected_entities,
        "expected_effect": expected_effect,
        "warnings": warnings,
        "requires_confirmation": ca.requires_confirmation,
        "requires_override_reason": ca.requires_override_reason,
        "risk_level": ca.risk_level,
        "action_type": ca.action_type,
    }
    if extra:
        body.update(extra)
    return body


def _preview_dispatch_assign_best(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction
) -> dict[str, Any]:
    job_id = rec.related_job_id
    if not job_id:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Dispatch assignment needs a related job.",
            preconditions=["related_job_id must be set on the recommendation."],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    job = db.get(Job, job_id)
    if not job:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Related job not found.",
            preconditions=["Job must exist."],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    comps = _job_competencies(job)
    res = compute_ranked_dispatch_recommendations(
        db, job_id=job_id, limit=5, required_competencies=comps or None, include_stale=True
    )
    warnings: list[str] = []
    if not res.recommendations:
        warnings.append("No ranked candidates returned; check telemetry, competencies, or workload policy.")
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Nearest qualified engineer ranking produced no assignable candidate.",
            preconditions=["At least one qualified engineer with usable operational position."],
            affected_entities=[{"entity_type": "job", "entity_id": job_id}],
            expected_effect="Assign top-ranked engineer to the job.",
            warnings=warnings,
            ca=ca,
            extra={"candidates": [], "scoring_notes": res.scoring_notes},
        )
    top = res.recommendations[0]
    if top.availability_state == "stale_location":
        warnings.append("Top candidate relies on stale telemetry — confirm before notifying the customer.")
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Improves SLA / attendance posture by assigning the best-ranked qualified engineer.",
        preconditions=["Job open for assignment", "Engineer competencies valid"],
        affected_entities=[
            {"entity_type": "job", "entity_id": job_id},
            {"entity_type": "user", "entity_id": top.engineer_id, "role": "engineer"},
        ],
        expected_effect=f"Set assigned_engineer_id to {top.engineer_id} (dispatch intelligence pick).",
        warnings=warnings,
        ca=ca,
        extra={
            "selected_candidate": {
                "engineer_id": top.engineer_id,
                "distance_km": top.distance_km,
                "estimated_travel_minutes": top.estimated_travel_minutes,
                "availability_state": top.availability_state,
            },
            "candidates": [
                {
                    "engineer_id": r.engineer_id,
                    "distance_km": r.distance_km,
                    "estimated_travel_minutes": r.estimated_travel_minutes,
                    "availability_state": r.availability_state,
                }
                for r in res.recommendations[:5]
            ],
            "scoring_notes": res.scoring_notes,
        },
    )


def _preview_dispatch_manual_assign(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    job_id = rec.related_job_id
    eid = (payload or {}).get("engineer_id")
    if not job_id or not eid:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Manual assignment requires related_job_id on the recommendation and engineer_id in payload.",
            preconditions=["related_job_id", "input_payload.engineer_id"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    job = db.get(Job, job_id)
    if not job:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Job not found.",
            preconditions=["Job exists"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Dispatcher-selected assignment overrides ranking suggestions.",
        preconditions=["Engineer passes competency validation at execution time"],
        affected_entities=[
            {"entity_type": "job", "entity_id": job_id},
            {"entity_type": "user", "entity_id": str(eid), "role": "engineer"},
        ],
        expected_effect=f"Assign engineer {eid} to job {job_id}.",
        warnings=["Override reason recommended when diverging from ranked best."],
        ca=ca,
    )


def _preview_manual_eta(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    job_id = rec.related_job_id
    eta = (payload or {}).get("eta_minutes")
    if not job_id or eta is None:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Need related_job_id and eta_minutes.",
            preconditions=["related_job_id", "eta_minutes"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    try:
        eta_i = int(eta)
    except Exception:
        eta_i = -1
    if eta_i <= 0:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="eta_minutes must be a positive integer.",
            preconditions=["eta_minutes > 0"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Sets a manual ETA for customer portal / comms alignment.",
        preconditions=["Job exists"],
        affected_entities=[{"entity_type": "job", "entity_id": job_id}],
        expected_effect=f"Persist manual_eta_minutes={eta_i} on the job.",
        warnings=[],
        ca=ca,
        extra={"eta_minutes": eta_i},
    )


def _preview_on_my_way(db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction) -> dict[str, Any]:
    job_id = rec.related_job_id
    if not job_id:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Customer notification requires related_job_id.",
            preconditions=["related_job_id"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Customer-facing on-my-way signal for portal / comms.",
        preconditions=["Job exists"],
        affected_entities=[{"entity_type": "job", "entity_id": job_id}],
        expected_effect="Set on_my_way timestamps and optional en_route_at (customer-visible).",
        warnings=["This is customer-visible — confirm wording/channel policies externally."],
        ca=ca,
    )


def _stock_item_for_rec(db: Session, rec: OperationalRecommendation) -> StockItem | None:
    if rec.entity_type == "stock_item":
        return db.get(StockItem, rec.entity_id)
    return None


def _preview_inventory_actions(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    item = _stock_item_for_rec(db, rec)
    if not item:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Inventory actions expect entity_type=stock_item with a valid item id.",
            preconditions=["Recommendation linked to stock_item"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    ensure_default_inventory_locations(db)
    wh = get_default_warehouse(db)
    reservations = (
        db.query(StockReservation)
        .filter(
            StockReservation.stock_item_id == item.id,
            StockReservation.status == "reserved",
        )
        .order_by(StockReservation.created_at.desc())
        .limit(10)
        .all()
    )
    shortage = float(item.on_hand_quantity or 0) - float(item.reserved_quantity or 0)
    warnings: list[str] = []
    if shortage >= 0:
        warnings.append("Aggregate on_hand - reserved is no longer negative; verify before transferring or releasing.")
    extra: dict[str, Any] = {
        "sku": item.sku,
        "on_hand": float(item.on_hand_quantity or 0),
        "reserved": float(item.reserved_quantity or 0),
        "default_warehouse_location_id": wh.id,
        "open_reservations": [{"id": r.id, "quantity": r.quantity, "job_id": r.job_id} for r in reservations],
    }
    if ca.action_type == catalog.CREATE_TRANSFER_REQUEST:
        lines = (payload or {}).get("lines")
        if not lines:
            suggest_qty = max(-shortage, float(item.reorder_point_quantity or 1) or 1.0)
            lines = [{"sku": item.sku, "quantity": suggest_qty}]
        extra["proposed_lines"] = lines
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Draft transfer can reposition stock toward demand (no automatic ship).",
            preconditions=["Locations exist", "SKUs valid at execution"],
            affected_entities=[{"entity_type": "stock_item", "entity_id": item.id}],
            expected_effect="Create draft StockTransfer + AutomationRun (auditable).",
            warnings=warnings,
            ca=ca,
            extra=extra,
        )
    if ca.action_type == catalog.CREATE_PURCHASE_ORDER_DRAFT:
        lines = (payload or {}).get("lines")
        if not lines:
            suggest_qty = max(-shortage, float(item.reorder_point_quantity or 1) or 1.0)
            lines = [{"sku": item.sku, "quantity": suggest_qty, "unit_cost": float(item.unit_cost or 0)}]
        supplier = (payload or {}).get("supplier_name") or "TBD Supplier"
        extra["proposed_lines"] = lines
        extra["supplier_name"] = supplier
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Draft PO for procurement review (not issued).",
            preconditions=["SKU exists"],
            affected_entities=[{"entity_type": "stock_item", "entity_id": item.id}],
            expected_effect="Create PurchaseOrder in draft status + AutomationRun (auditable).",
            warnings=warnings,
            ca=ca,
            extra=extra,
        )
    if ca.action_type == catalog.RELEASE_CONFLICTING_RESERVATION:
        rid = (payload or {}).get("reservation_id")
        if not rid and reservations:
            rid = reservations[0].id
            extra["implicit_reservation_id"] = rid
        if not rid:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="No reservation selected; provide reservation_id.",
                preconditions=["reservation_id"],
                affected_entities=[{"entity_type": "stock_item", "entity_id": item.id}],
                expected_effect="No change.",
                warnings=warnings,
                ca=ca,
                extra=extra,
            )
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Releases reserved quantity to ease aggregate shortage (operational).",
            preconditions=["Reservation exists and is active"],
            affected_entities=[
                {"entity_type": "stock_item", "entity_id": item.id},
                {"entity_type": "stock_reservation", "entity_id": str(rid)},
            ],
            expected_effect="Call inventory release_reservation_by_id (ledger-safe).",
            warnings=warnings + ["Impacts promised material — confirm with planner."],
            ca=ca,
            extra=extra | {"reservation_id": str(rid)},
        )
    # mark_for_stock_review
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Creates an InternalFollowUpTask (stock_review) linked to the SKU (AutomationRun audit).",
        preconditions=[],
        affected_entities=[{"entity_type": "stock_item", "entity_id": item.id}],
        expected_effect="Internal follow-up task + automation run (no stock movement).",
        warnings=warnings,
        ca=ca,
        extra=extra,
    )


def _invoice_and_job(db: Session, rec: OperationalRecommendation) -> tuple[Invoice | None, Job | None]:
    inv: Invoice | None = None
    job: Job | None = None
    if rec.related_invoice_id:
        inv = db.get(Invoice, rec.related_invoice_id)
    if rec.related_job_id:
        job = db.get(Job, rec.related_job_id)
    if inv and not job:
        job = db.get(Job, inv.job_id)
    return inv, job


def _preview_invoice_family(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    inv, job = _invoice_and_job(db, rec)
    if ca.action_type == catalog.HOLD_INVOICE:
        if not inv:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Hold requires a related invoice.",
                preconditions=["related_invoice_id"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        reasons = _invoice_hold_reasons(db, inv, job)
        return _base_preview_dict(
            allowed=bool(reasons),
            reason_suggested="Holds release while compliance/costing gaps exist.",
            preconditions=["Blocking reasons still present at execution time"],
            affected_entities=[{"entity_type": "invoice", "entity_id": inv.id}],
            expected_effect="Set invoice.status to held and annotate notes.",
            warnings=[] if reasons else ["No active hold reasons — holding may be unnecessary."],
            ca=ca,
            extra={"hold_reasons": reasons},
        )
    if ca.action_type == catalog.GENERATE_MISSING_CERTIFICATE:
        jid = (job.id if job else None) or rec.related_job_id
        if not jid:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Need a job context to generate a certificate.",
                preconditions=["related_job_id"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Creates compliance certificate shell for the job.",
            preconditions=["Job exists"],
            affected_entities=[{"entity_type": "job", "entity_id": jid}],
            expected_effect="Insert Certificate row (generated).",
            warnings=["May trigger document/customer hooks depending on environment."],
            ca=ca,
            extra={
                "job_id": jid,
                "certificate_type": (payload or {}).get("certificate_type") or "completion",
            },
        )
    if ca.action_type == catalog.REGENERATE_COST_SNAPSHOT:
        jid = (job.id if job else None) or rec.related_job_id
        if not jid:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Need job id to rebuild costing snapshot.",
                preconditions=["related_job_id"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Refreshes persisted job cost snapshot from current inputs.",
            preconditions=["Job exists"],
            affected_entities=[{"entity_type": "job", "entity_id": jid}],
            expected_effect="persist_job_cost_snapshot",
            warnings=[],
            ca=ca,
            extra={"job_id": jid},
        )
    # mark_for_finance_review
    if not inv:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Finance review note needs an invoice.",
            preconditions=["related_invoice_id"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Internal finance follow-up task plus invoice cross-reference note.",
        preconditions=[],
        affected_entities=[{"entity_type": "invoice", "entity_id": inv.id}],
        expected_effect="InternalFollowUpTask (finance_review) + AutomationRun; optional invoice note.",
        warnings=[],
        ca=ca,
    )


def _preview_contract_family(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    cid = rec.related_contract_id or (rec.entity_id if rec.entity_type == "contract" else None)
    if not cid:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Contract action needs related_contract_id (or entity contract).",
            preconditions=["contract id"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    c = db.get(Contract, cid)
    if not c:
        return _base_preview_dict(
            allowed=False,
            reason_suggested="Contract not found.",
            preconditions=["Contract exists"],
            affected_entities=[],
            expected_effect="No change.",
            warnings=[],
            ca=ca,
        )
    note = (payload or {}).get("note") or (payload or {}).get("notes")
    if ca.action_type == catalog.AUTOMATION_CONTRACT_REVIEW_TASK:
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Structured contract review + internal follow-up task (draft-first automation).",
            preconditions=["Contract exists"],
            affected_entities=[{"entity_type": "contract", "entity_id": c.id}],
            expected_effect="ContractReview (deduped if open) + InternalFollowUpTask + AutomationRun.",
            warnings=[],
            ca=ca,
            extra={"contract_id": c.id},
        )
    if ca.action_type == catalog.MARK_FOR_RENEWAL_REVIEW:
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Surfaces renewal planning on the contract record.",
            preconditions=[],
            affected_entities=[{"entity_type": "contract", "entity_id": c.id}],
            expected_effect="Set renewal_review_date if missing (conservative default horizon).",
            warnings=[],
            ca=ca,
        )
    if ca.action_type == catalog.GENERATE_REPRICING_PROPOSAL:
        from backend.app.modules.contracts import contract_review_service as crs

        p = payload or {}
        rr_id = p.get("repricing_review_id")
        rr: ContractRepricingReview | None = None
        if rr_id:
            rr = db.get(ContractRepricingReview, str(rr_id))
            if not rr or rr.contract_id != cid:
                return _base_preview_dict(
                    allowed=False,
                    reason_suggested="repricing_review_id not found or does not belong to this contract.",
                    preconditions=["Valid repricing_review_id for contract"],
                    affected_entities=[],
                    expected_effect="No change.",
                    warnings=[],
                    ca=ca,
                )
        else:
            rr = crs.get_repricing_for_contract(db, contract_id=cid)
        if not rr:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="No repricing review on contract; create structured repricing review first or pass repricing_review_id.",
                preconditions=["ContractRepricingReview exists"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Creates formal ContractRepricingProposal + lines from repricing review (contract pricing unchanged).",
            preconditions=["Repricing review row exists"],
            affected_entities=[
                {"entity_type": "contract", "entity_id": cid},
                {"entity_type": "repricing_review", "entity_id": rr.id},
            ],
            expected_effect="Insert proposal; optional supersede prior open proposals on contract",
            warnings=["Does not email the customer or apply new pricing to the contract."],
            ca=ca,
            extra={
                "contract_id": cid,
                "repricing_review_id": rr.id,
                "supersede_previous": bool(p.get("supersede_previous", False)),
            },
        )
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Commercial review / repricing follow-up captured on contract notes.",
        preconditions=[],
        affected_entities=[{"entity_type": "contract", "entity_id": c.id}],
        expected_effect="Append timestamped note to contract.notes",
        warnings=[],
        ca=ca,
        extra={"note": note or ""},
    )


def _vehicle_defect_context(db: Session, rec: OperationalRecommendation) -> tuple[str | None, str | None]:
    """
    Returns (vehicle_id, defect_id) best-effort from entity payloads / detail_json.
    """
    detail = _loads(rec.detail_json) if rec.detail_json else {}
    vid = detail.get("vehicle_id") or (rec.entity_id if rec.entity_type == "vehicle" else None)
    did = detail.get("defect_id") or (rec.entity_id if rec.entity_type == "vehicle_defect" else None)
    if not did and vid:
        open_d = (
            db.query(VehicleDefect)
            .filter(VehicleDefect.vehicle_id == vid, VehicleDefect.status == "open")
            .order_by(VehicleDefect.reported_at.desc())
            .first()
        )
        if open_d:
            did = open_d.id
    return (str(vid) if vid else None, str(did) if did else None)


def _preview_vehicle_equipment(
    db: Session, rec: OperationalRecommendation, ca: catalog.CatalogAction, payload: dict[str, Any]
) -> dict[str, Any]:
    p = payload or {}
    if ca.action_type == catalog.RESOLVE_DEFECT:
        vid, did = _vehicle_defect_context(db, rec)
        vid = p.get("vehicle_id") or vid
        did = p.get("defect_id") or did
        if not vid or not did:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Resolve defect requires vehicle_id and defect_id (supply in payload or entity detail).",
                preconditions=["vehicle_id", "defect_id"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        d = db.get(VehicleDefect, did)
        if not d or d.vehicle_id != vid:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Defect not found for vehicle.",
                preconditions=["Matching defect"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        return _base_preview_dict(
            allowed=d.status == "open",
            reason_suggested="Closes an open safety/readiness defect after verification.",
            preconditions=["Defect status is open"],
            affected_entities=[
                {"entity_type": "vehicle", "entity_id": vid},
                {"entity_type": "vehicle_defect", "entity_id": did},
            ],
            expected_effect="Mark defect resolved with notes.",
            warnings=["Confirm repair/verification completed in the field."],
            ca=ca,
            extra={"vehicle_id": vid, "defect_id": did, "defect_severity": d.severity},
        )
    if ca.action_type in (catalog.ASSIGN_ALTERNATE_EQUIPMENT, catalog.MOVE_EQUIPMENT):
        from backend.app.modules.equipment.models import FieldEquipment

        eq_id = p.get("equipment_id") or (rec.entity_id if rec.entity_type == "equipment" else None)
        target = p.get("target")
        target_id = p.get("target_id")
        if not eq_id or not target or not target_id:
            return _base_preview_dict(
                allowed=False,
                reason_suggested="Equipment move/assign requires equipment_id, target, target_id in payload.",
                preconditions=["equipment_id", "target", "target_id"],
                affected_entities=[],
                expected_effect="No change.",
                warnings=[],
                ca=ca,
            )
        eq = db.get(FieldEquipment, str(eq_id))
        cal = eq.calibration_status if eq else None
        return _base_preview_dict(
            allowed=True,
            reason_suggested="Repositions field equipment using the equipment service (validated).",
            preconditions=["Equipment exists", "Target id valid for target kind"],
            affected_entities=[{"entity_type": "field_equipment", "entity_id": str(eq_id)}],
            expected_effect="assign_or_move_equipment",
            warnings=["Operational movement — confirm custody and calibration implications."],
            ca=ca,
            extra={
                "equipment_id": str(eq_id),
                "target": str(target),
                "target_id": str(target_id),
                "calibration_status": cal,
            },
        )
    # mark_vehicle_review
    vid = p.get("vehicle_id") or (rec.entity_id if rec.entity_type == "vehicle" else None)
    return _base_preview_dict(
        allowed=True,
        reason_suggested="Internal readiness review flag (audit).",
        preconditions=[],
        affected_entities=[{"entity_type": "vehicle", "entity_id": vid or rec.entity_id}],
        expected_effect="Audit entry only",
        warnings=[],
        ca=ca,
        extra={"vehicle_id": vid},
    )


def _compute_preview(
    db: Session, rec: OperationalRecommendation, action_type: str, input_payload: dict[str, Any] | None
) -> dict[str, Any]:
    ca = _get_catalog_action(action_type)
    payload = input_payload or {}
    if action_type == catalog.ASSIGN_BEST_ENGINEER:
        return _preview_dispatch_assign_best(db, rec, ca)
    if action_type == catalog.MANUAL_ASSIGN_ENGINEER:
        return _preview_dispatch_manual_assign(db, rec, ca, payload)
    if action_type == catalog.SET_MANUAL_ETA:
        return _preview_manual_eta(db, rec, ca, payload)
    if action_type == catalog.SEND_ON_MY_WAY_NOTIFICATION:
        return _preview_on_my_way(db, rec, ca)
    if action_type in (
        catalog.CREATE_TRANSFER_REQUEST,
        catalog.CREATE_PURCHASE_ORDER_DRAFT,
        catalog.RELEASE_CONFLICTING_RESERVATION,
        catalog.MARK_FOR_STOCK_REVIEW,
    ):
        return _preview_inventory_actions(db, rec, ca, payload)
    if action_type in (
        catalog.HOLD_INVOICE,
        catalog.GENERATE_MISSING_CERTIFICATE,
        catalog.REGENERATE_COST_SNAPSHOT,
        catalog.MARK_FOR_FINANCE_REVIEW,
    ):
        return _preview_invoice_family(db, rec, ca, payload)
    if action_type in (
        catalog.AUTOMATION_CONTRACT_REVIEW_TASK,
        catalog.CREATE_CONTRACT_REVIEW_NOTE,
        catalog.MARK_FOR_RENEWAL_REVIEW,
        catalog.MARK_FOR_REPRICING_REVIEW,
        catalog.GENERATE_REPRICING_PROPOSAL,
    ):
        return _preview_contract_family(db, rec, ca, payload)
    if action_type in (
        catalog.RESOLVE_DEFECT,
        catalog.ASSIGN_ALTERNATE_EQUIPMENT,
        catalog.MOVE_EQUIPMENT,
        catalog.MARK_VEHICLE_REVIEW_REQUIRED,
    ):
        return _preview_vehicle_equipment(db, rec, ca, payload)
    raise ValueError(f"Preview not implemented for action_type={action_type}")


def preview_recommendation_action(
    db: Session,
    *,
    recommendation_id: str,
    action_type: str,
    actor_user_id: str,
    input_payload: dict[str, Any] | None = None,
    decision_notes: str | None = None,
) -> dict[str, Any]:
    rec = _get_rec(db, recommendation_id)
    if rec.status in ("resolved", "dismissed"):
        raise ValueError("Recommendation is closed; actions are frozen.")
    ensure_action_suggestions(db, recommendation_id=recommendation_id)
    sug = _get_suggestion(db, recommendation_id=recommendation_id, action_type=action_type)
    if sug.action_status in ("executed", "rejected", "cancelled"):
        raise ValueError(f"Suggestion is terminal ({sug.action_status}).")
    preview = _compute_preview(db, rec, action_type, input_payload)
    actor = db.get(User, actor_user_id)
    if actor:
        preview = {
            **preview,
            "authorization": describe_rec_action_authorization(
                db=db, user=actor, action_type=action_type, preview=preview
            ),
        }
    now = utc_now()
    sug.preview_json = _dumps(preview)
    sug.action_status = "previewed"
    sug.updated_at = now
    db.add(sug)
    db.commit()
    db.refresh(sug)
    _log_decision(
        db,
        recommendation_id=recommendation_id,
        suggestion_id=sug.id,
        decision_type="previewed",
        user_id=actor_user_id,
        decision_notes=decision_notes,
        preview_snapshot=preview,
    )
    return preview


def reject_recommendation_action(
    db: Session,
    *,
    recommendation_id: str,
    action_type: str,
    actor_user_id: str,
    rejection_reason: str,
    decision_notes: str | None = None,
) -> RecommendationActionSuggestion:
    rec = _get_rec(db, recommendation_id)
    if rec.status in ("resolved", "dismissed"):
        raise ValueError("Recommendation is closed.")
    ensure_action_suggestions(db, recommendation_id=recommendation_id)
    sug = _get_suggestion(db, recommendation_id=recommendation_id, action_type=action_type)
    if sug.action_status in ("executed", "rejected"):
        raise ValueError("Suggestion already terminal.")
    now = utc_now()
    sug.action_status = "rejected"
    sug.updated_at = now
    db.add(sug)
    db.commit()
    db.refresh(sug)
    _log_decision(
        db,
        recommendation_id=recommendation_id,
        suggestion_id=sug.id,
        decision_type="rejected",
        user_id=actor_user_id,
        decision_notes=decision_notes,
        override_reason=rejection_reason,
    )
    return sug


def _execute_inner(
    db: Session,
    rec: OperationalRecommendation,
    action_type: str,
    payload: dict[str, Any],
    actor_user_id: str,
) -> dict[str, Any]:
    if action_type == catalog.ASSIGN_BEST_ENGINEER:
        job_id = rec.related_job_id
        if not job_id:
            raise ValueError("Missing related_job_id")
        job = db.get(Job, job_id)
        if not job:
            raise ValueError("Job not found")
        comps = _job_competencies(job)
        res = compute_ranked_dispatch_recommendations(
            db, job_id=job_id, limit=3, required_competencies=comps or None, include_stale=True
        )
        if not res.recommendations:
            raise ValueError("No dispatch candidate available for assignment")
        top_id = res.recommendations[0].engineer_id
        assign_job(db, job_id=job_id, engineer_id=top_id, required_competencies=comps or None)
        return {"assigned_engineer_id": top_id, "job_id": job_id}
    if action_type == catalog.MANUAL_ASSIGN_ENGINEER:
        job_id = rec.related_job_id
        eid = payload.get("engineer_id")
        if not job_id or not eid:
            raise ValueError("job_id context and engineer_id required")
        job = db.get(Job, job_id)
        comps = _job_competencies(job) if job else []
        assign_job(db, job_id=job_id, engineer_id=str(eid), required_competencies=comps or None)
        return {"assigned_engineer_id": str(eid), "job_id": job_id}
    if action_type == catalog.SET_MANUAL_ETA:
        job_id = rec.related_job_id
        eta = int(payload.get("eta_minutes"))
        if not job_id:
            raise ValueError("Missing related_job_id")
        set_job_manual_eta_minutes(db, job_id=job_id, eta_minutes=eta)
        return {"job_id": job_id, "manual_eta_minutes": eta}
    if action_type == catalog.SEND_ON_MY_WAY_NOTIFICATION:
        job_id = rec.related_job_id
        if not job_id:
            raise ValueError("Missing related_job_id")
        mark_job_on_my_way_for_customer(db, job_id=job_id, source="recommendation_action_confirmed")
        return {"job_id": job_id, "on_my_way": True}
    if action_type == catalog.CREATE_TRANSFER_REQUEST:
        run = low_risk_automation.create_transfer_draft_from_recommendation(
            db, rec=rec, actor_user_id=actor_user_id, payload=payload, commit=True
        )
        if run.status == "failed":
            raise ValueError(run.result_summary or "Transfer draft automation failed")
        pl = _loads(run.payload_json)
        return {
            "stock_transfer_id": pl.get("stock_transfer_id") or run.draft_entity_id,
            "automation_run_id": run.id,
            "automation_status": run.status,
            "status": "draft",
        }
    if action_type == catalog.CREATE_PURCHASE_ORDER_DRAFT:
        run = low_risk_automation.create_po_draft_from_recommendation(
            db, rec=rec, actor_user_id=actor_user_id, payload=payload, commit=True
        )
        if run.status == "failed":
            raise ValueError(run.result_summary or "PO draft automation failed")
        pl = _loads(run.payload_json)
        return {
            "purchase_order_id": pl.get("purchase_order_id") or run.draft_entity_id,
            "automation_run_id": run.id,
            "automation_status": run.status,
            "status": "draft",
        }
    if action_type == catalog.RELEASE_CONFLICTING_RESERVATION:
        rid = payload.get("reservation_id")
        if not rid:
            raise ValueError("reservation_id required")
        release_reservation_by_id(db, reservation_id=str(rid), performed_by_user_id=actor_user_id)
        return {"released_reservation_id": str(rid)}
    if action_type == catalog.MARK_FOR_STOCK_REVIEW:
        run = low_risk_automation.create_stock_review_task_from_recommendation(
            db, rec=rec, actor_user_id=actor_user_id, commit=True
        )
        if run.status == "failed":
            raise ValueError(run.result_summary or "Stock review task automation failed")
        pl = _loads(run.payload_json)
        item = _stock_item_for_rec(db, rec)
        return {
            "stock_item_id": item.id if item else None,
            "sku": item.sku if item else None,
            "review_note": payload.get("note"),
            "automation_run_id": run.id,
            "automation_status": run.status,
            "internal_follow_up_task_id": pl.get("task_id"),
        }
    if action_type == catalog.GENERATE_MISSING_CERTIFICATE:
        jid = payload.get("job_id") or rec.related_job_id
        if not jid:
            raise ValueError("job_id required")
        ctype = str(payload.get("certificate_type") or "completion")
        cert = generate_certificate(
            db,
            payload=CertificateGenerateIn(job_id=str(jid), certificate_type=ctype),
            acting_user_id=actor_user_id,
        )
        return {"certificate_id": cert.id, "job_id": str(jid)}
    if action_type == catalog.REGENERATE_COST_SNAPSHOT:
        jid = payload.get("job_id") or rec.related_job_id
        if not jid:
            raise ValueError("job_id required")
        snap = persist_job_cost_snapshot(db, job_id=str(jid), commit=True)
        return {"job_cost_snapshot_id": snap.id, "job_id": str(jid)}
    if action_type == catalog.HOLD_INVOICE:
        inv, job = _invoice_and_job(db, rec)
        if not inv:
            raise ValueError("Invoice required")
        reasons = _invoice_hold_reasons(db, inv, job)
        if not reasons:
            raise ValueError("Invoice hold preconditions no longer apply (nothing to hold for).")
        from backend.app.modules.invoicing.service import hold_invoice

        note = payload.get("hold_note") or "Held via recommendation action"
        inv2 = hold_invoice(
            db,
            invoice_id=inv.id,
            note=note,
            acting_user_id=actor_user_id,
            reason_lines=reasons,
        )
        return {"invoice_id": inv2.id, "status": inv2.status}
    if action_type == catalog.MARK_FOR_FINANCE_REVIEW:
        inv, _job = _invoice_and_job(db, rec)
        if not inv:
            raise ValueError("Invoice required")
        run = low_risk_automation.create_finance_review_task_from_recommendation(
            db, rec=rec, actor_user_id=actor_user_id, commit=True
        )
        if run.status == "failed":
            raise ValueError(run.result_summary or "Finance review task automation failed")
        pl = _loads(run.payload_json)
        note = payload.get("note") or "Finance review requested (recommendation action)"
        if run.status == "draft_created" and pl.get("task_id"):
            prefix = inv.cost_basis_notes or ""
            inv.cost_basis_notes = (prefix + "\n" if prefix else "") + f"[finance_review task={pl.get('task_id')}] {note}"
            db.add(inv)
            db.commit()
            db.refresh(inv)
        return {
            "invoice_id": inv.id,
            "automation_run_id": run.id,
            "automation_status": run.status,
            "internal_follow_up_task_id": pl.get("task_id"),
        }
    if action_type == catalog.AUTOMATION_CONTRACT_REVIEW_TASK:
        run = low_risk_automation.create_contract_review_task_from_recommendation(
            db, rec=rec, actor_user_id=actor_user_id, commit=True
        )
        if run.status == "failed":
            raise ValueError(run.result_summary or "Contract review automation failed")
        pl = _loads(run.payload_json)
        return {
            "automation_run_id": run.id,
            "automation_status": run.status,
            "contract_review_id": pl.get("contract_review_id"),
            "internal_follow_up_task_id": pl.get("task_id"),
        }
    if action_type == catalog.CREATE_CONTRACT_REVIEW_NOTE:
        cid = payload.get("contract_id") or rec.related_contract_id
        if not cid:
            raise ValueError("contract_id required")
        c = db.get(Contract, str(cid))
        if not c:
            raise ValueError("Contract not found")
        note = payload.get("note") or "Contract review (recommendation action)"
        prefix = c.notes or ""
        c.notes = (prefix + "\n" if prefix else "") + f"[rec_review {utc_now().isoformat()}] {note}"
        db.add(c)
        db.commit()
        db.refresh(c)
        return {"contract_id": c.id}
    if action_type == catalog.MARK_FOR_RENEWAL_REVIEW:
        cid = payload.get("contract_id") or rec.related_contract_id
        if not cid:
            raise ValueError("contract_id required")
        c = db.get(Contract, str(cid))
        if not c:
            raise ValueError("Contract not found")
        if c.renewal_review_date is None:
            c.renewal_review_date = utc_now() + timedelta(days=30)
        db.add(c)
        db.commit()
        db.refresh(c)
        return {"contract_id": c.id, "renewal_review_date": c.renewal_review_date.isoformat()}
    if action_type == catalog.MARK_FOR_REPRICING_REVIEW:
        cid = payload.get("contract_id") or rec.related_contract_id
        if not cid:
            raise ValueError("contract_id required")
        c = db.get(Contract, str(cid))
        if not c:
            raise ValueError("Contract not found")
        note = payload.get("note") or "Repricing review requested"
        prefix = c.notes or ""
        c.notes = (prefix + "\n" if prefix else "") + f"[repricing_review {utc_now().isoformat()}] {note}"
        db.add(c)
        db.commit()
        db.refresh(c)
        return {"contract_id": c.id}
    if action_type == catalog.GENERATE_REPRICING_PROPOSAL:
        from backend.app.modules.contracts import contract_review_service as crs
        from backend.app.services import repricing_proposal_service as rps

        cid = (
            payload.get("contract_id")
            or rec.related_contract_id
            or (rec.entity_id if rec.entity_type == "contract" else None)
        )
        if not cid:
            raise ValueError("contract_id required")
        rr_id = payload.get("repricing_review_id")
        if not rr_id:
            rr = crs.get_repricing_for_contract(db, contract_id=str(cid))
            if not rr:
                raise ValueError("No repricing review; create structured repricing review first")
            rr_id = rr.id
        prop = rps.generate_proposal_from_repricing_review(
            db,
            contract_id=str(cid),
            repricing_review_id=str(rr_id),
            generated_by_user_id=actor_user_id,
            currency=str(payload.get("currency") or "GBP"),
            supersede_previous=bool(payload.get("supersede_previous", False)),
        )
        return {
            "contract_id": str(cid),
            "repricing_review_id": prop.repricing_review_id,
            "proposal_id": prop.id,
            "proposal_reference": prop.proposal_reference,
            "proposal_status": prop.proposal_status,
        }
    if action_type == catalog.RESOLVE_DEFECT:
        vid = str(payload.get("vehicle_id") or "")
        did = str(payload.get("defect_id") or "")
        if not vid or not did:
            raise ValueError("vehicle_id and defect_id required")
        notes = payload.get("resolution_notes") or "Resolved via recommendation action"
        row = resolve_defect(
            db,
            vehicle_id=vid,
            defect_id=did,
            resolved_by_user_id=actor_user_id,
            resolution_notes=str(notes),
        )
        return {"vehicle_id": vid, "defect_id": did, "status": row.status}
    if action_type in (catalog.ASSIGN_ALTERNATE_EQUIPMENT, catalog.MOVE_EQUIPMENT):
        eq_id = str(payload.get("equipment_id") or "")
        target = str(payload.get("target") or "")
        target_id = str(payload.get("target_id") or "")
        if not eq_id or not target or not target_id:
            raise ValueError("equipment_id, target, target_id required")
        eq = assign_or_move_equipment(
            db,
            equipment_id=eq_id,
            target=target,
            target_id=target_id,
            performed_by_user_id=actor_user_id,
            notes=payload.get("notes"),
        )
        return {"equipment_id": eq.id, "current_location_type": eq.current_location_type}
    if action_type == catalog.MARK_VEHICLE_REVIEW_REQUIRED:
        return {
            "vehicle_id": payload.get("vehicle_id") or rec.entity_id,
            "flag": "vehicle_review_required",
            "note": payload.get("note"),
        }
    raise ValueError(f"Execution not implemented for {action_type}")


def execute_recommendation_action(
    db: Session,
    *,
    recommendation_id: str,
    action_type: str,
    actor_user_id: str,
    input_payload: dict[str, Any] | None = None,
    confirmed: bool = False,
    decision_notes: str | None = None,
    override_reason: str | None = None,
) -> dict[str, Any]:
    """
    Re-validates preview server-side, records confirm + execute audit rows, and performs the action.
    """
    if not confirmed:
        raise ValueError("Explicit confirmed=true is required to execute recommendation actions.")
    rec = _get_rec(db, recommendation_id)
    if rec.status in ("resolved", "dismissed"):
        raise ValueError("Recommendation is closed.")
    ensure_action_suggestions(db, recommendation_id=recommendation_id)
    sug = _get_suggestion(db, recommendation_id=recommendation_id, action_type=action_type)
    if sug.action_status in ("executed", "rejected", "cancelled"):
        raise ValueError(f"Cannot execute suggestion in status {sug.action_status}")
    ca = _get_catalog_action(action_type)
    if ca.requires_confirmation and not confirmed:
        raise ValueError("Confirmation required for this action.")

    payload = dict(input_payload or {})
    # Merge stored preview hints (e.g. selected candidate) when client omits redundant fields.
    prev = _loads(sug.preview_json)
    if prev.get("selected_candidate") and action_type == catalog.ASSIGN_BEST_ENGINEER:
        payload.setdefault("engineer_id", prev["selected_candidate"].get("engineer_id"))
    if prev.get("job_id") and "job_id" not in payload:
        payload.setdefault("job_id", prev.get("job_id"))
    if prev.get("certificate_type") and "certificate_type" not in payload:
        payload.setdefault("certificate_type", prev.get("certificate_type"))
    if prev.get("proposed_lines") and action_type == catalog.CREATE_PURCHASE_ORDER_DRAFT:
        payload.setdefault("lines", prev.get("proposed_lines"))
    if prev.get("proposed_lines") and action_type == catalog.CREATE_TRANSFER_REQUEST:
        payload.setdefault("lines", prev.get("proposed_lines"))
    if prev.get("reservation_id") and "reservation_id" not in payload:
        payload.setdefault("reservation_id", prev.get("reservation_id"))
    if prev.get("repricing_review_id") and "repricing_review_id" not in payload:
        payload.setdefault("repricing_review_id", prev.get("repricing_review_id"))
    if prev.get("contract_id") and "contract_id" not in payload:
        payload.setdefault("contract_id", prev.get("contract_id"))

    fresh_preview = _compute_preview(db, rec, action_type, payload)
    if not fresh_preview.get("allowed"):
        raise ValueError(fresh_preview.get("reason_suggested") or "Action not allowed after re-validation.")

    actor_user = db.get(User, actor_user_id)
    if not actor_user:
        raise ValueError("Actor user not found")
    assert_rec_action_allowed(db=db, user=actor_user, action_type=action_type, preview=fresh_preview)

    if ca.requires_override_reason and not (override_reason or "").strip():
        raise ValueError("override_reason is required for this action.")

    _log_decision(
        db,
        recommendation_id=recommendation_id,
        suggestion_id=sug.id,
        decision_type="confirmed",
        user_id=actor_user_id,
        decision_notes=decision_notes,
        override_reason=override_reason,
        preview_snapshot=fresh_preview,
    )

    now = utc_now()
    sug.action_status = "confirmed"
    sug.updated_at = now
    db.add(sug)
    db.commit()

    try:
        result = _execute_inner(db, rec, action_type, payload, actor_user_id)
    except Exception as exc:  # noqa: BLE001 — surface clean audit for ops
        sug.action_status = "failed"
        sug.updated_at = utc_now()
        db.add(sug)
        db.commit()
        _log_decision(
            db,
            recommendation_id=recommendation_id,
            suggestion_id=sug.id,
            decision_type="executed",
            user_id=actor_user_id,
            execution_result={"error": str(exc)},
            execution_status="failed",
        )
        raise ValueError(str(exc)) from exc

    sug.action_status = "executed"
    sug.updated_at = utc_now()
    db.add(sug)
    db.commit()

    _log_decision(
        db,
        recommendation_id=recommendation_id,
        suggestion_id=sug.id,
        decision_type="executed",
        user_id=actor_user_id,
        execution_result=result,
        execution_status="success",
    )

    if ca.auto_resolve_on_success and rec.status not in ("resolved", "dismissed"):
        ops_service.resolve_recommendation(
            db,
            recommendation_id=recommendation_id,
            user_id=actor_user_id,
            notes=f"Auto-resolved after successful action {action_type}",
        )

    if action_type in (
        catalog.CREATE_CONTRACT_REVIEW_NOTE,
        catalog.MARK_FOR_RENEWAL_REVIEW,
        catalog.MARK_FOR_REPRICING_REVIEW,
    ):
        from backend.app.modules.contracts import contract_review_service as contract_review_sync

        cid = rec.related_contract_id or (rec.entity_id if rec.entity_type == "contract" else None)
        if cid:
            contract_review_sync.sync_structured_review_after_catalog_action(
                db,
                contract_id=str(cid),
                action_type=action_type,
                performed_by_user_id=actor_user_id,
                recommendation_id=rec.id,
                recommendation_type=rec.recommendation_type,
                recommendation_summary=rec.summary,
            )

    return {"preview": fresh_preview, "execution": result, "suggestion_id": sug.id}


def list_action_suggestions(db: Session, *, recommendation_id: str) -> list[RecommendationActionSuggestion]:
    ensure_action_suggestions(db, recommendation_id=recommendation_id)
    return (
        db.query(RecommendationActionSuggestion)
        .filter(RecommendationActionSuggestion.recommendation_id == recommendation_id)
        .order_by(RecommendationActionSuggestion.action_type.asc())
        .all()
    )


def list_action_history(db: Session, *, recommendation_id: str) -> list[RecommendationActionDecision]:
    return (
        db.query(RecommendationActionDecision)
        .filter(RecommendationActionDecision.recommendation_id == recommendation_id)
        .order_by(RecommendationActionDecision.decided_at.asc())
        .all()
    )


def dashboard_actions_summary(db: Session) -> dict[str, Any]:
    now = utc_now()
    since = now - timedelta(days=7)
    open_recs = (
        db.query(OperationalRecommendation)
        .filter(OperationalRecommendation.status.in_(("open", "acknowledged")))
        .count()
    )
    with_suggestions = (
        db.query(RecommendationActionSuggestion.recommendation_id)
        .filter(RecommendationActionSuggestion.action_status == "available")
        .distinct()
        .count()
    )
    pending = (
        db.query(RecommendationActionSuggestion)
        .filter(RecommendationActionSuggestion.action_status.in_(("previewed", "confirmed")))
        .count()
    )
    recent_decisions = (
        db.query(RecommendationActionDecision).filter(RecommendationActionDecision.decided_at >= since).all()
    )
    rejected = [d for d in recent_decisions if d.decision_type == "rejected"]
    executed_ok = [d for d in recent_decisions if d.decision_type == "executed" and d.execution_status == "success"]
    executed_fail = [d for d in recent_decisions if d.decision_type == "executed" and d.execution_status == "failed"]

    type_counts: dict[str, int] = {}
    for d in recent_decisions:
        if not d.action_suggestion_id:
            continue
        sug = db.get(RecommendationActionSuggestion, d.action_suggestion_id)
        if not sug:
            continue
        type_counts[sug.action_type] = type_counts.get(sug.action_type, 0) + 1

    return {
        "open_recommendations": open_recs,
        "recommendations_with_available_actions": with_suggestions,
        "pending_confirmations": pending,
        "recently_rejected": len(rejected),
        "recently_executed_success": len(executed_ok),
        "failed_executions": len(executed_fail),
        "action_decisions_last_7d_by_type": type_counts,
        "window_start": since.isoformat(),
    }
