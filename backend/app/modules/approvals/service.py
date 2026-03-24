from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.approvals.models import ApprovalAuditLog, ApprovalRequest
from backend.app.modules.auth.models import User
from backend.app.modules.equipment.service import assign_or_move_equipment
from backend.app.modules.inventory.service import approve_purchase_order
from backend.app.modules.invoicing.service import hold_invoice, release_invoice_from_hold
from backend.app.modules.contracts import contract_review_service as review_service
from backend.app.modules.vehicles.service import resolve_defect
from backend.app.services import authorization_service as authz


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def _append_audit(
    db: Session,
    *,
    approval_id: str,
    event_type: str,
    actor_user_id: str | None,
    notes: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    row = ApprovalAuditLog(
        approval_request_id=approval_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        notes=notes,
        detail_json=json.dumps(detail, separators=(",", ":")) if detail else None,
    )
    db.add(row)
    db.commit()


def create_approval_request(
    db: Session,
    *,
    approval_type: str,
    target_entity_type: str,
    target_entity_id: str,
    reason: str,
    requested_by_user_id: str,
    payload: dict[str, Any] | None = None,
    assigned_to_user_id: str | None = None,
) -> ApprovalRequest:
    authz.approver_permission_for_approval_type(approval_type)  # validate type
    dup = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.approval_type == approval_type,
            ApprovalRequest.target_entity_id == target_entity_id,
            ApprovalRequest.status == "pending",
        )
        .first()
    )
    if dup:
        raise ValueError("A pending approval already exists for this target")

    row = ApprovalRequest(
        approval_type=approval_type,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        requested_by_user_id=requested_by_user_id,
        assigned_to_user_id=assigned_to_user_id,
        status="pending",
        reason=reason,
        payload_json=json.dumps(payload or {}, separators=(",", ":")),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _append_audit(
        db,
        approval_id=row.id,
        event_type="created",
        actor_user_id=requested_by_user_id,
        notes=reason[:500],
        detail={"approval_type": approval_type, "target_entity_id": target_entity_id},
    )
    return row


def list_approval_requests(
    db: Session,
    *,
    status: str | None = None,
    approval_type: str | None = None,
    assigned_to_user_id: str | None = None,
    target_entity_type: str | None = None,
    target_entity_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ApprovalRequest]:
    q = db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
    if status:
        q = q.filter(ApprovalRequest.status == status)
    if approval_type:
        q = q.filter(ApprovalRequest.approval_type == approval_type)
    if assigned_to_user_id:
        q = q.filter(ApprovalRequest.assigned_to_user_id == assigned_to_user_id)
    if target_entity_type:
        q = q.filter(ApprovalRequest.target_entity_type == target_entity_type)
    if target_entity_id:
        q = q.filter(ApprovalRequest.target_entity_id == target_entity_id)
    return q.offset(offset).limit(limit).all()


def get_approval_request(db: Session, *, approval_id: str) -> ApprovalRequest | None:
    return db.get(ApprovalRequest, approval_id)


def _execute_approved_payload(db: Session, req: ApprovalRequest, approver_id: str) -> dict[str, Any]:
    pl = json.loads(req.payload_json or "{}")
    t = req.approval_type

    if t == "invoice_hold":
        iid = str(pl.get("invoice_id") or req.target_entity_id)
        inv = hold_invoice(
            db,
            invoice_id=iid,
            note=str(pl.get("hold_note") or req.reason),
            acting_user_id=approver_id,
            reason_lines=pl.get("reason_lines") if isinstance(pl.get("reason_lines"), list) else None,
        )
        return {"invoice_id": inv.id, "status": inv.status}

    if t == "invoice_release":
        iid = str(pl.get("invoice_id") or req.target_entity_id)
        inv = release_invoice_from_hold(
            db,
            invoice_id=iid,
            note=str(pl.get("release_note") or req.reason),
            acting_user_id=approver_id,
        )
        return {"invoice_id": inv.id, "status": inv.status}

    if t == "purchase_order_approval":
        po = approve_purchase_order(
            db,
            purchase_order_id=req.target_entity_id,
            approved_by_user_id=approver_id,
        )
        return {"purchase_order_id": po.id, "status": po.status}

    if t == "repricing_approval":
        cid = str(pl.get("contract_id") or req.target_entity_id)
        rr = review_service.patch_repricing_review(
            db,
            contract_id=cid,
            performed_by_user_id=approver_id,
            approved=True,
            notes=pl.get("notes"),
        )
        return {"contract_id": cid, "repricing_review_id": rr.id, "approved": True}

    if t == "vehicle_block_override":
        vid = str(pl["vehicle_id"])
        did = str(pl["defect_id"])
        resolve_defect(
            db,
            vehicle_id=vid,
            defect_id=did,
            resolved_by_user_id=approver_id,
            resolution_notes=str(pl.get("resolution_notes") or "Approved vehicle block override"),
        )
        return {"vehicle_id": vid, "defect_id": did, "resolved": True}

    if t == "equipment_block_override":
        eq = assign_or_move_equipment(
            db,
            equipment_id=str(pl["equipment_id"]),
            target=str(pl["target"]),
            target_id=str(pl["target_id"]),
            performed_by_user_id=approver_id,
            notes=str(pl.get("notes") or "Approved equipment calibration override move"),
        )
        return {"equipment_id": eq.id, "current_location_type": eq.current_location_type}

    if t == "customer_notification_override":
        # Placeholder: record intent; real customer comms hooks can subscribe later.
        return {"recorded": True, "override_context": pl}

    if t == "contract_exit_approval":
        # Formalize exit: payload should include review_id + decision; minimal hook.
        return {"recorded": True, "payload": pl}

    raise ValueError(f"No execution handler for approval_type={t}")


def approve_request(
    db: Session,
    *,
    approval_id: str,
    approver: User,
    decision_notes: str | None = None,
) -> ApprovalRequest:
    req = db.get(ApprovalRequest, approval_id)
    if not req:
        raise ValueError("Approval request not found")
    if req.status != "pending":
        raise ValueError(f"Approval is not pending (status={req.status})")

    perm = authz.approver_permission_for_approval_type(req.approval_type)
    if not authz.user_has_permission(approver, perm, db=db):
        raise ValueError(f"Approver lacks permission {perm}")

    if req.assigned_to_user_id and req.assigned_to_user_id != approver.id:
        if "Admin" not in approver.role_names():
            raise ValueError("Approval is assigned to another user")

    now = _utc()
    try:
        result = _execute_approved_payload(db, req, approver.id)
    except Exception as exc:  # noqa: BLE001
        req.status = "cancelled"
        req.decided_at = now
        req.decided_by_user_id = approver.id
        req.decision_notes = (decision_notes or "") + f" | execution_failed: {exc}"
        req.execution_result_json = json.dumps({"error": str(exc)}, separators=(",", ":"))
        db.add(req)
        db.commit()
        _append_audit(
            db,
            approval_id=req.id,
            event_type="approve_failed",
            actor_user_id=approver.id,
            notes=str(exc),
        )
        raise ValueError(str(exc)) from exc

    req.status = "approved"
    req.decided_at = now
    req.decided_by_user_id = approver.id
    req.decision_notes = decision_notes
    req.execution_result_json = json.dumps(result, separators=(",", ":"), default=str)
    db.add(req)
    db.commit()
    db.refresh(req)
    _append_audit(
        db,
        approval_id=req.id,
        event_type="approved",
        actor_user_id=approver.id,
        notes=decision_notes,
        detail=result,
    )
    return req


def reject_request(
    db: Session,
    *,
    approval_id: str,
    approver: User,
    decision_notes: str | None = None,
) -> ApprovalRequest:
    req = db.get(ApprovalRequest, approval_id)
    if not req:
        raise ValueError("Approval request not found")
    if req.status != "pending":
        raise ValueError(f"Approval is not pending (status={req.status})")
    perm = authz.approver_permission_for_approval_type(req.approval_type)
    if not authz.user_has_permission(approver, perm, db=db):
        raise ValueError(f"Approver lacks permission {perm}")

    now = _utc()
    req.status = "rejected"
    req.decided_at = now
    req.decided_by_user_id = approver.id
    req.decision_notes = decision_notes
    db.add(req)
    db.commit()
    db.refresh(req)
    _append_audit(
        db,
        approval_id=req.id,
        event_type="rejected",
        actor_user_id=approver.id,
        notes=decision_notes,
    )
    return req


def dashboard_summary(db: Session, *, current_user_id: str, overdue_hours: float = 72.0) -> dict[str, Any]:
    pending = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").all()
    by_type: dict[str, int] = {}
    overdue = 0
    assigned_me = 0
    cutoff = _utc() - timedelta(hours=overdue_hours)
    for r in pending:
        by_type[r.approval_type] = by_type.get(r.approval_type, 0) + 1
        ca = r.created_at
        if ca.tzinfo is None:
            ca = ca.replace(tzinfo=timezone.utc)
        if ca < cutoff:
            overdue += 1
        if r.assigned_to_user_id == current_user_id:
            assigned_me += 1

    recent_cut = _utc() - timedelta(days=7)
    recently_decided = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.status.in_(("approved", "rejected")),
            ApprovalRequest.decided_at.isnot(None),
            ApprovalRequest.decided_at >= recent_cut,
        )
        .count()
    )

    return {
        "pending_total": len(pending),
        "pending_by_type": by_type,
        "overdue_pending_count": overdue,
        "assigned_to_me_pending": assigned_me,
        "recently_decided": recently_decided,
        "overdue_hours_threshold": overdue_hours,
    }
