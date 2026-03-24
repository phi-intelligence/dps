"""
Low-risk automation: draft artifacts and internal follow-up tasks only.

No silent final financial, customer-facing, or irreversible actions.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.automation.models import AutomationRun, InternalFollowUpTask
from backend.app.modules.contracts import contract_review_service as crs
from backend.app.modules.contracts.review_models import ContractRepricingProposal
from backend.app.modules.dispatch.models import Job
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.inventory.ledger_service import ensure_default_inventory_locations, get_default_warehouse
from backend.app.modules.inventory.models import PurchaseOrder, StockItem, StockTransfer
from backend.app.modules.inventory.service import create_purchase_order, create_stock_transfer
from backend.app.modules.ops.models import OperationalRecommendation
from backend.app.modules.ops import recommendation_action_service as rec_act


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return {}


# --- Constants aligned with recommendation catalog action_type strings ---
AUTOMATION_INVENTORY_TRANSFER_DRAFT = "automation_inventory_transfer_draft"
AUTOMATION_INVENTORY_PO_DRAFT = "automation_inventory_po_draft"
AUTOMATION_STOCK_REVIEW_TASK = "automation_stock_review_task"
AUTOMATION_FINANCE_REVIEW_TASK = "automation_finance_review_task"
AUTOMATION_CONTRACT_REVIEW_TASK = "automation_contract_review_task"

RECOMMENDATION_TYPE_DEFAULT_AUTOMATION: dict[str, str] = {
    "inventory_risk": AUTOMATION_INVENTORY_TRANSFER_DRAFT,
    "stock_shortage_reserved": AUTOMATION_INVENTORY_TRANSFER_DRAFT,
    "parts_reconciliation_block": AUTOMATION_STOCK_REVIEW_TASK,
    "invoice_release_hold": AUTOMATION_FINANCE_REVIEW_TASK,
    "contract_negative_margin": AUTOMATION_CONTRACT_REVIEW_TASK,
    "contract_margin_deterioration": AUTOMATION_CONTRACT_REVIEW_TASK,
    "contract_high_reactive_burden": AUTOMATION_CONTRACT_REVIEW_TASK,
    "contract_repricing_opportunity": AUTOMATION_CONTRACT_REVIEW_TASK,
    "contract_attention": AUTOMATION_CONTRACT_REVIEW_TASK,
}


def _create_run(
    db: Session,
    *,
    automation_type: str,
    trigger_type: str,
    trigger_entity_type: str,
    trigger_entity_id: str,
    source_recommendation_id: str | None,
    source_event_type: str | None,
    performed_by_user_id: str | None,
    created_by_system: bool,
) -> AutomationRun:
    r = AutomationRun(
        id=str(uuid.uuid4()),
        automation_type=automation_type,
        trigger_type=trigger_type,
        trigger_entity_type=trigger_entity_type,
        trigger_entity_id=trigger_entity_id,
        source_recommendation_id=source_recommendation_id,
        source_event_type=source_event_type,
        status="created",
        created_by_system=created_by_system,
        result_summary="",
        payload_json="{}",
        performed_by_user_id=performed_by_user_id,
    )
    db.add(r)
    db.flush()
    return r


def _finish_run(
    db: Session,
    run: AutomationRun,
    *,
    status: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    draft_entity_type: str | None = None,
    draft_entity_id: str | None = None,
) -> AutomationRun:
    run.status = status
    run.result_summary = summary
    run.completed_at = utc_now()
    if payload is not None:
        run.payload_json = _dumps(payload)
    if warnings is not None:
        run.warnings_json = _dumps(warnings)
    run.draft_entity_type = draft_entity_type
    run.draft_entity_id = draft_entity_id
    db.add(run)
    db.flush()
    return run


def _open_proposal_follow_up_by_dedupe_key(
    db: Session, *, proposal_id: str, dedupe_key: str
) -> InternalFollowUpTask | None:
    rows = (
        db.query(InternalFollowUpTask)
        .filter(
            InternalFollowUpTask.related_entity_type == "repricing_proposal",
            InternalFollowUpTask.related_entity_id == proposal_id,
            InternalFollowUpTask.status.in_(("open", "in_progress")),
        )
        .all()
    )
    for t in rows:
        p = _loads(t.payload_json)
        if p.get("dedupe_key") == dedupe_key:
            return t
    return None


def _open_task_match(
    db: Session,
    *,
    task_type: str,
    related_entity_type: str,
    related_entity_id: str,
    source_recommendation_id: str | None = None,
) -> InternalFollowUpTask | None:
    q = (
        db.query(InternalFollowUpTask)
        .filter(
            InternalFollowUpTask.task_type == task_type,
            InternalFollowUpTask.related_entity_type == related_entity_type,
            InternalFollowUpTask.related_entity_id == related_entity_id,
            InternalFollowUpTask.status.in_(("open", "in_progress")),
        )
    )
    if source_recommendation_id is not None:
        q = q.filter(InternalFollowUpTask.source_recommendation_id == source_recommendation_id)
    return q.first()


def _existing_draft_transfer_for_rec(db: Session, recommendation_id: str) -> tuple[AutomationRun, StockTransfer] | None:
    runs = (
        db.query(AutomationRun)
        .filter(
            AutomationRun.source_recommendation_id == recommendation_id,
            AutomationRun.automation_type == AUTOMATION_INVENTORY_TRANSFER_DRAFT,
            AutomationRun.status == "draft_created",
            AutomationRun.draft_entity_type == "stock_transfer",
        )
        .order_by(AutomationRun.created_at.desc())
        .all()
    )
    for run in runs:
        if not run.draft_entity_id:
            continue
        t = db.get(StockTransfer, run.draft_entity_id)
        if t and t.status == "draft":
            return run, t
    return None


def _existing_draft_po_for_rec(db: Session, recommendation_id: str) -> tuple[AutomationRun, PurchaseOrder] | None:
    runs = (
        db.query(AutomationRun)
        .filter(
            AutomationRun.source_recommendation_id == recommendation_id,
            AutomationRun.automation_type == AUTOMATION_INVENTORY_PO_DRAFT,
            AutomationRun.status == "draft_created",
            AutomationRun.draft_entity_type == "purchase_order",
        )
        .order_by(AutomationRun.created_at.desc())
        .all()
    )
    for run in runs:
        if not run.draft_entity_id:
            continue
        po = db.get(PurchaseOrder, run.draft_entity_id)
        if po and po.status == "draft":
            return run, po
    return None


def create_transfer_draft_from_recommendation(
    db: Session,
    *,
    rec: OperationalRecommendation,
    actor_user_id: str,
    payload: dict[str, Any] | None = None,
    commit: bool = True,
) -> AutomationRun:
    run = _create_run(
        db,
        automation_type=AUTOMATION_INVENTORY_TRANSFER_DRAFT,
        trigger_type="recommendation",
        trigger_entity_type="operational_recommendation",
        trigger_entity_id=rec.id,
        source_recommendation_id=rec.id,
        source_event_type=None,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    dup = _existing_draft_transfer_for_rec(db, rec.id)
    if dup:
        _r, t = dup
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Duplicate skipped: draft stock transfer already exists for this recommendation.",
            payload={"existing_stock_transfer_id": t.id, "prior_automation_run_id": _r.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    item = rec_act._stock_item_for_rec(db, rec)  # noqa: SLF001
    if not item:
        _finish_run(db, run, status="failed", summary="No stock_item context on recommendation.")
        if commit:
            db.commit()
        return run
    p = dict(payload or {})
    try:
        ensure_default_inventory_locations(db)
        wh = get_default_warehouse(db)
        from_id = str(p.get("from_location_id") or wh.id)
        to_id = str(p.get("to_location_id") or wh.id)
        lines_raw = p.get("lines")
        if not lines_raw:
            shortage = float(item.on_hand_quantity or 0) - float(item.reserved_quantity or 0)
            suggest_qty = max(-shortage, 1.0)
            lines_raw = [(item.sku, suggest_qty)]
        lines: list[tuple[str, float]] = []
        if isinstance(lines_raw, list):
            for row in lines_raw:
                if isinstance(row, dict) and "sku" in row:
                    lines.append((str(row["sku"]), float(row["quantity"])))
                elif isinstance(row, (list, tuple)) and len(row) >= 2:
                    lines.append((str(row[0]), float(row[1])))
        t = create_stock_transfer(
            db,
            from_location_id=from_id,
            to_location_id=to_id,
            lines=lines,
            requested_by_user_id=actor_user_id,
            commit=False,
        )
        _finish_run(
            db,
            run,
            status="draft_created",
            summary=f"Draft stock transfer {t.id} created.",
            draft_entity_type="stock_transfer",
            draft_entity_id=t.id,
            payload={"stock_transfer_id": t.id},
        )
    except Exception as exc:  # noqa: BLE001
        _finish_run(db, run, status="failed", summary=str(exc), payload={"error": str(exc)})
    if commit:
        db.commit()
        db.refresh(run)
    return run


def create_po_draft_from_recommendation(
    db: Session,
    *,
    rec: OperationalRecommendation,
    actor_user_id: str,
    payload: dict[str, Any] | None = None,
    commit: bool = True,
) -> AutomationRun:
    run = _create_run(
        db,
        automation_type=AUTOMATION_INVENTORY_PO_DRAFT,
        trigger_type="recommendation",
        trigger_entity_type="operational_recommendation",
        trigger_entity_id=rec.id,
        source_recommendation_id=rec.id,
        source_event_type=None,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    dup = _existing_draft_po_for_rec(db, rec.id)
    if dup:
        _r, po = dup
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Duplicate skipped: draft PO already exists for this recommendation.",
            payload={"existing_purchase_order_id": po.id, "prior_automation_run_id": _r.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    item = rec_act._stock_item_for_rec(db, rec)  # noqa: SLF001
    if not item:
        _finish_run(db, run, status="failed", summary="No stock_item context on recommendation.")
        if commit:
            db.commit()
        return run
    p = dict(payload or {})
    try:
        lines_raw = p.get("lines")
        if not lines_raw:
            shortage = float(item.on_hand_quantity or 0) - float(item.reserved_quantity or 0)
            suggest_qty = max(-shortage, 1.0)
            lines_raw = [{"sku": item.sku, "quantity": suggest_qty, "unit_cost": float(item.unit_cost or 0)}]
        supplier = str(p.get("supplier_name") or "Draft Supplier")
        po_lines: list[tuple[str, float, float]] = []
        for row in lines_raw:
            if isinstance(row, dict):
                po_lines.append((str(row["sku"]), float(row["quantity"]), float(row.get("unit_cost") or 0)))
        po = create_purchase_order(
            db, supplier_name=supplier, lines=po_lines, created_by_user_id=actor_user_id, commit=False
        )
        _finish_run(
            db,
            run,
            status="draft_created",
            summary=f"Draft purchase order {po.id} created.",
            draft_entity_type="purchase_order",
            draft_entity_id=po.id,
            payload={"purchase_order_id": po.id},
        )
    except Exception as exc:  # noqa: BLE001
        _finish_run(db, run, status="failed", summary=str(exc), payload={"error": str(exc)})
    if commit:
        db.commit()
        db.refresh(run)
    return run


def create_stock_review_task_from_recommendation(
    db: Session,
    *,
    rec: OperationalRecommendation,
    actor_user_id: str,
    commit: bool = True,
) -> AutomationRun:
    run = _create_run(
        db,
        automation_type=AUTOMATION_STOCK_REVIEW_TASK,
        trigger_type="recommendation",
        trigger_entity_type="operational_recommendation",
        trigger_entity_id=rec.id,
        source_recommendation_id=rec.id,
        source_event_type=None,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    item = rec_act._stock_item_for_rec(db, rec)  # noqa: SLF001
    if not item:
        _finish_run(db, run, status="failed", summary="No stock_item context.")
        if commit:
            db.commit()
        return run

    existing = _open_task_match(
        db,
        task_type="stock_review",
        related_entity_type="stock_item",
        related_entity_id=item.id,
        source_recommendation_id=rec.id,
    )
    if existing:
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Open stock review task already exists.",
            payload={"existing_task_id": existing.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    task = InternalFollowUpTask(
        id=str(uuid.uuid4()),
        task_type="stock_review",
        title=f"Stock review: {item.sku}",
        summary=rec.summary[:2000],
        status="open",
        priority="normal",
        related_entity_type="stock_item",
        related_entity_id=item.id,
        source_recommendation_id=rec.id,
        payload_json=_dumps({"sku": item.sku, "recommendation_type": rec.recommendation_type}),
    )
    db.add(task)
    db.flush()
    _finish_run(
        db,
        run,
        status="draft_created",
        summary=f"Internal follow-up task {task.id} created.",
        draft_entity_type="internal_follow_up_task",
        draft_entity_id=task.id,
        payload={"task_id": task.id},
    )
    if commit:
        db.commit()
        db.refresh(run)
    return run


def create_finance_review_task_from_recommendation(
    db: Session,
    *,
    rec: OperationalRecommendation,
    actor_user_id: str,
    commit: bool = True,
) -> AutomationRun:
    run = _create_run(
        db,
        automation_type=AUTOMATION_FINANCE_REVIEW_TASK,
        trigger_type="recommendation",
        trigger_entity_type="operational_recommendation",
        trigger_entity_id=rec.id,
        source_recommendation_id=rec.id,
        source_event_type=None,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    inv_id = rec.related_invoice_id or (rec.entity_id if rec.entity_type == "invoice" else None)
    if not inv_id:
        _finish_run(db, run, status="failed", summary="No invoice context on recommendation.")
        if commit:
            db.commit()
        return run
    inv = db.get(Invoice, inv_id)
    if not inv:
        _finish_run(db, run, status="failed", summary="Invoice not found.")
        if commit:
            db.commit()
        return run

    existing = _open_task_match(
        db,
        task_type="finance_review",
        related_entity_type="invoice",
        related_entity_id=inv.id,
        source_recommendation_id=rec.id,
    )
    if existing:
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Open finance review task already exists for this recommendation.",
            payload={"existing_task_id": existing.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    task = InternalFollowUpTask(
        id=str(uuid.uuid4()),
        task_type="finance_review",
        title=f"Finance review: invoice {inv.id[:8]}",
        summary=rec.summary[:2000],
        status="open",
        priority="high" if rec.severity in ("critical", "high") else "normal",
        related_entity_type="invoice",
        related_entity_id=inv.id,
        source_recommendation_id=rec.id,
        source_automation_run_id=run.id,
        payload_json=_dumps({"invoice_id": inv.id, "job_id": inv.job_id}),
    )
    db.add(task)
    db.flush()
    _finish_run(
        db,
        run,
        status="draft_created",
        summary=f"Finance review task {task.id} created.",
        draft_entity_type="internal_follow_up_task",
        draft_entity_id=task.id,
        payload={"task_id": task.id},
    )
    if commit:
        db.commit()
        db.refresh(run)
    return run


def create_contract_review_task_from_recommendation(
    db: Session,
    *,
    rec: OperationalRecommendation,
    actor_user_id: str,
    commit: bool = True,
) -> AutomationRun:
    run = _create_run(
        db,
        automation_type=AUTOMATION_CONTRACT_REVIEW_TASK,
        trigger_type="recommendation",
        trigger_entity_type="operational_recommendation",
        trigger_entity_id=rec.id,
        source_recommendation_id=rec.id,
        source_event_type=None,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    cid = rec.related_contract_id or (rec.entity_id if rec.entity_type == "contract" else None)
    if not cid:
        jid = rec.related_job_id
        if jid:
            job = db.get(Job, jid)
            cid = job.contract_id if job else None
    if not cid:
        _finish_run(db, run, status="failed", summary="No contract context on recommendation.")
        if commit:
            db.commit()
        return run

    existing_task = _open_task_match(
        db,
        task_type="contract_review",
        related_entity_type="contract",
        related_entity_id=cid,
        source_recommendation_id=rec.id,
    )
    if existing_task:
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Open contract follow-up task already exists.",
            payload={"existing_task_id": existing_task.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    review, created_new = crs.create_contract_review(
        db,
        contract_id=cid,
        review_type="health_review",
        triggered_by="recommendation",
        triggered_reason=f"{rec.recommendation_type}: {rec.title}",
        summary=rec.summary[:2000],
        performed_by_user_id=actor_user_id,
        source_recommendation_id=rec.id,
        dedupe=True,
    )

    task = InternalFollowUpTask(
        id=str(uuid.uuid4()),
        task_type="contract_review",
        title=f"Contract review follow-up: {rec.title[:120]}",
        summary=rec.summary[:2000],
        status="open",
        priority="high" if rec.severity in ("critical", "high") else "normal",
        related_entity_type="contract",
        related_entity_id=cid,
        source_recommendation_id=rec.id,
        payload_json=_dumps(
            {"contract_review_id": review.id, "contract_review_created": created_new, "recommendation_type": rec.recommendation_type}
        ),
    )
    db.add(task)
    db.flush()
    task.source_automation_run_id = run.id
    db.add(task)
    _finish_run(
        db,
        run,
        status="draft_created",
        summary="Contract review (deduped if existing) + internal follow-up task created.",
        draft_entity_type="contract_review",
        draft_entity_id=review.id,
        payload={"contract_review_id": review.id, "task_id": task.id, "review_created_new": created_new},
    )
    if commit:
        db.commit()
        db.refresh(run)
    return run


def run_automation_for_recommendation(
    db: Session,
    *,
    recommendation_id: str,
    actor_user_id: str,
    automation_type: str | None = None,
    payload: dict[str, Any] | None = None,
    commit: bool = True,
) -> AutomationRun:
    rec = db.get(OperationalRecommendation, recommendation_id)
    if not rec:
        raise ValueError("Recommendation not found")
    at = automation_type or RECOMMENDATION_TYPE_DEFAULT_AUTOMATION.get(rec.recommendation_type)
    if not at:
        raise ValueError(f"No default automation mapping for recommendation_type={rec.recommendation_type}")

    if at == AUTOMATION_INVENTORY_TRANSFER_DRAFT:
        return create_transfer_draft_from_recommendation(db, rec=rec, actor_user_id=actor_user_id, payload=payload, commit=commit)
    if at == AUTOMATION_INVENTORY_PO_DRAFT:
        return create_po_draft_from_recommendation(db, rec=rec, actor_user_id=actor_user_id, payload=payload, commit=commit)
    if at == AUTOMATION_STOCK_REVIEW_TASK:
        return create_stock_review_task_from_recommendation(db, rec=rec, actor_user_id=actor_user_id, commit=commit)
    if at == AUTOMATION_FINANCE_REVIEW_TASK:
        return create_finance_review_task_from_recommendation(db, rec=rec, actor_user_id=actor_user_id, commit=commit)
    if at == AUTOMATION_CONTRACT_REVIEW_TASK:
        return create_contract_review_task_from_recommendation(db, rec=rec, actor_user_id=actor_user_id, commit=commit)
    raise ValueError(f"Unknown automation_type: {at}")


def on_customer_proposal_response(
    db: Session,
    *,
    proposal: ContractRepricingProposal,
    response_type: str,
    actor_user_id: str,
    commit: bool = True,
) -> list[AutomationRun]:
    """Create internal follow-up tasks for commercial proposal outcomes (no outbound comms)."""
    runs: list[AutomationRun] = []
    dedupe_key = f"customer_response:{response_type}"
    if response_type == "rejected":
        tt, title = "customer_follow_up", "Customer rejected repricing proposal"
    elif response_type == "counter_requested":
        tt, title = "repricing_follow_up", "Customer requested a counter on repricing proposal"
    elif response_type in ("needs_follow_up", "acknowledged"):
        tt, title = "customer_follow_up", f"Customer proposal: {response_type.replace('_', ' ')}"
    else:
        return runs

    existing = _open_proposal_follow_up_by_dedupe_key(db, proposal_id=proposal.id, dedupe_key=dedupe_key)
    run = _create_run(
        db,
        automation_type=f"customer_proposal_{response_type}",
        trigger_type="customer_proposal",
        trigger_entity_type="repricing_proposal",
        trigger_entity_id=proposal.id,
        source_recommendation_id=None,
        source_event_type=f"customer_response:{response_type}",
        performed_by_user_id=actor_user_id,
        created_by_system=True,
    )
    if existing:
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Open follow-up task already exists for this proposal.",
            payload={"existing_task_id": existing.id},
        )
        runs.append(run)
        if commit:
            db.commit()
        return runs

    task = InternalFollowUpTask(
        id=str(uuid.uuid4()),
        task_type=tt,
        title=title,
        summary=f"Proposal {proposal.proposal_reference} on contract {proposal.contract_id}.",
        status="open",
        priority="high",
        related_entity_type="repricing_proposal",
        related_entity_id=proposal.id,
        source_recommendation_id=None,
        payload_json=_dumps(
            {"contract_id": proposal.contract_id, "response_type": response_type, "dedupe_key": dedupe_key}
        ),
    )
    db.add(task)
    db.flush()
    task.source_automation_run_id = run.id
    db.add(task)
    _finish_run(
        db,
        run,
        status="draft_created",
        summary=f"Created internal task {task.id}",
        draft_entity_type="internal_follow_up_task",
        draft_entity_id=task.id,
        payload={"task_id": task.id},
    )
    runs.append(run)
    if commit:
        db.commit()
        db.refresh(run)
    return runs


def maybe_create_proposal_viewed_follow_up(
    db: Session,
    *,
    proposal_id: str,
    actor_user_id: str,
    viewed_no_response_days: int = 7,
    kind: str = "viewed_no_response_follow_up",
    commit: bool = True,
) -> AutomationRun | None:
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        raise ValueError("Proposal not found")
    dedupe_key = kind
    if kind == "expired_no_response_follow_up":
        if p.customer_response_status:
            return None
        from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry

        if not is_past_customer_expiry(p) and p.customer_release_status != "expired":
            return None
    else:
        if not p.customer_viewed_at or p.customer_response_status:
            return None
        viewed_at = _as_utc_aware(p.customer_viewed_at)
        delta = utc_now() - viewed_at
        if delta.days < viewed_no_response_days:
            return None

    existing = _open_proposal_follow_up_by_dedupe_key(db, proposal_id=p.id, dedupe_key=dedupe_key)
    run = _create_run(
        db,
        automation_type=kind,
        trigger_type="customer_proposal",
        trigger_entity_type="repricing_proposal",
        trigger_entity_id=p.id,
        source_recommendation_id=None,
        source_event_type=kind,
        performed_by_user_id=actor_user_id,
        created_by_system=False,
    )
    if existing:
        _finish_run(
            db,
            run,
            status="skipped",
            summary="Follow-up task already open.",
            payload={"existing_task_id": existing.id},
        )
        if commit:
            db.commit()
            db.refresh(run)
        return run

    title = (
        "Proposal expired — no customer response"
        if kind == "expired_no_response_follow_up"
        else "Proposal viewed — no customer response"
    )
    summary = (
        f"Proposal {p.proposal_reference} expired without response."
        if kind == "expired_no_response_follow_up"
        else f"Proposal {p.proposal_reference} viewed; no response within policy window."
    )
    task = InternalFollowUpTask(
        id=str(uuid.uuid4()),
        task_type="customer_follow_up",
        title=title,
        summary=summary,
        status="open",
        priority="normal",
        related_entity_type="repricing_proposal",
        related_entity_id=p.id,
        payload_json=_dumps({"contract_id": p.contract_id, "kind": kind, "dedupe_key": dedupe_key}),
    )
    db.add(task)
    db.flush()
    task.source_automation_run_id = run.id
    db.add(task)
    _finish_run(
        db,
        run,
        status="draft_created",
        summary=f"Task {task.id} created",
        draft_entity_type="internal_follow_up_task",
        draft_entity_id=task.id,
        payload={"task_id": task.id},
    )
    if commit:
        db.commit()
        db.refresh(run)
    return run


def list_runs(
    db: Session,
    *,
    status: str | None = None,
    automation_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AutomationRun]:
    q = db.query(AutomationRun).order_by(AutomationRun.created_at.desc())
    if status:
        q = q.filter(AutomationRun.status == status)
    if automation_type:
        q = q.filter(AutomationRun.automation_type == automation_type)
    return q.offset(offset).limit(limit).all()


def get_run(db: Session, *, run_id: str) -> AutomationRun | None:
    return db.get(AutomationRun, run_id)


def dashboard_summary(db: Session, *, limit: int = 50) -> dict[str, Any]:
    rows = db.query(AutomationRun).order_by(AutomationRun.created_at.desc()).limit(limit).all()
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    recent_drafts = [
        {
            "run_id": r.id,
            "automation_type": r.automation_type,
            "draft_entity_type": r.draft_entity_type,
            "draft_entity_id": r.draft_entity_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
        if r.status == "draft_created"
    ][:20]
    skipped = [r for r in rows if r.status == "skipped"][:20]
    return {
        "total_listed": len(rows),
        "by_status": by_status,
        "recent_draft_creations": recent_drafts,
        "recent_skipped": [
            {"run_id": r.id, "summary": r.result_summary, "payload": _loads(r.payload_json)} for r in skipped
        ],
    }


def list_tasks(
    db: Session,
    *,
    status: str | None = None,
    task_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[InternalFollowUpTask]:
    q = db.query(InternalFollowUpTask).order_by(InternalFollowUpTask.created_at.desc())
    if status:
        q = q.filter(InternalFollowUpTask.status == status)
    if task_type:
        q = q.filter(InternalFollowUpTask.task_type == task_type)
    return q.offset(offset).limit(limit).all()


def get_task(db: Session, *, task_id: str) -> InternalFollowUpTask | None:
    return db.get(InternalFollowUpTask, task_id)


def patch_task(
    db: Session,
    *,
    task_id: str,
    status: str | None = None,
    priority: str | None = None,
    assigned_to_user_id: str | None = None,
    due_at: datetime | None = None,
    notes: str | None = None,
    commit: bool = True,
) -> InternalFollowUpTask:
    t = db.get(InternalFollowUpTask, task_id)
    if not t:
        raise ValueError("Task not found")
    if status is not None:
        t.status = status
    if priority is not None:
        t.priority = priority
    if assigned_to_user_id is not None:
        t.assigned_to_user_id = assigned_to_user_id
    if due_at is not None:
        t.due_at = due_at
    if notes is not None:
        t.notes = notes
    db.add(t)
    if commit:
        db.commit()
        db.refresh(t)
    else:
        db.flush()
    return t


def complete_task(
    db: Session,
    *, task_id: str, completed_by_user_id: str, completion_notes: str | None = None, commit: bool = True
) -> InternalFollowUpTask:
    t = db.get(InternalFollowUpTask, task_id)
    if not t:
        raise ValueError("Task not found")
    t.status = "completed"
    t.completed_at = utc_now()
    if completion_notes:
        prefix = t.notes or ""
        t.notes = (prefix + "\n" if prefix else "") + f"[completed by {completed_by_user_id}] {completion_notes}"
    db.add(t)
    if commit:
        db.commit()
        db.refresh(t)
    else:
        db.flush()
    return t


def tasks_dashboard_follow_up(db: Session, *, limit: int = 100) -> dict[str, Any]:
    open_rows = (
        db.query(InternalFollowUpTask)
        .filter(InternalFollowUpTask.status.in_(("open", "in_progress")))
        .order_by(InternalFollowUpTask.created_at.desc())
        .limit(limit)
        .all()
    )
    now = utc_now()
    overdue = [t for t in open_rows if t.due_at and t.due_at < now]
    return {
        "open_count": len(open_rows),
        "overdue_count": len(overdue),
        "overdue_task_ids": [t.id for t in overdue[:50]],
        "rows": [
            {
                "id": t.id,
                "task_type": t.task_type,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "related_entity_type": t.related_entity_type,
                "related_entity_id": t.related_entity_id,
            }
            for t in open_rows
        ],
    }


def tasks_dashboard_commercial(db: Session, *, limit: int = 100) -> dict[str, Any]:
    types = ("contract_review", "repricing_follow_up", "customer_follow_up")
    rows = (
        db.query(InternalFollowUpTask)
        .filter(InternalFollowUpTask.task_type.in_(types))
        .filter(InternalFollowUpTask.status.in_(("open", "in_progress")))
        .order_by(InternalFollowUpTask.priority.desc(), InternalFollowUpTask.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"count": len(rows), "rows": [{"id": t.id, "task_type": t.task_type, "title": t.title} for t in rows]}


def tasks_dashboard_finance(db: Session, *, limit: int = 100) -> dict[str, Any]:
    rows = (
        db.query(InternalFollowUpTask)
        .filter(InternalFollowUpTask.task_type == "finance_review")
        .filter(InternalFollowUpTask.status.in_(("open", "in_progress")))
        .order_by(InternalFollowUpTask.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"count": len(rows), "rows": [{"id": t.id, "title": t.title} for t in rows]}


def automation_run_to_dict(r: AutomationRun) -> dict[str, Any]:
    w = None
    if r.warnings_json:
        parsed = _loads(r.warnings_json)
        w = parsed if isinstance(parsed, list) else None
    return {
        "id": r.id,
        "automation_type": r.automation_type,
        "trigger_type": r.trigger_type,
        "trigger_entity_type": r.trigger_entity_type,
        "trigger_entity_id": r.trigger_entity_id,
        "source_recommendation_id": r.source_recommendation_id,
        "source_event_type": r.source_event_type,
        "status": r.status,
        "created_at": r.created_at,
        "completed_at": r.completed_at,
        "created_by_system": r.created_by_system,
        "result_summary": r.result_summary,
        "payload": _loads(r.payload_json),
        "warnings": w,
        "draft_entity_type": r.draft_entity_type,
        "draft_entity_id": r.draft_entity_id,
        "performed_by_user_id": r.performed_by_user_id,
    }


def task_to_dict(t: InternalFollowUpTask) -> dict[str, Any]:
    return {
        "id": t.id,
        "task_type": t.task_type,
        "title": t.title,
        "summary": t.summary,
        "status": t.status,
        "priority": t.priority,
        "related_entity_type": t.related_entity_type,
        "related_entity_id": t.related_entity_id,
        "source_recommendation_id": t.source_recommendation_id,
        "source_automation_run_id": t.source_automation_run_id,
        "assigned_to_user_id": t.assigned_to_user_id,
        "created_at": t.created_at,
        "due_at": t.due_at,
        "completed_at": t.completed_at,
        "notes": t.notes,
        "payload": _loads(t.payload_json) if t.payload_json else None,
    }
