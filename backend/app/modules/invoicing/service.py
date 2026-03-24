from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.compliance.models import Certificate
from backend.app.modules.invoicing.models import Invoice
from backend.app.modules.dispatch.models import Job
from backend.app.modules.quoting.models import Quote
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _legacy_quote_materials_sell_total(db: Session, *, job: Job) -> float:
    """Customer-facing materials total from quote (sell) when no usage-based billable computed."""
    if not job.quote_id:
        return 0.0
    quote = db.get(Quote, job.quote_id)
    if not quote:
        return 0.0
    return round(sum(float(it.line_total) for it in quote.items if it.item_type == "materials"), 2)


def build_invoice_cost_basis(db: Session, *, job_id: str) -> dict[str, Any]:
    """
    Preferred path: use JobCostSnapshot (frozen at completion) for materials charge + actual cost.
    Fallback: live job costing summary; if no actual usage qty, legacy quote materials sell totals.

    - materials_total on invoice = customer materials charge (actual qty × quote unit sell when possible).
    - materials_actual_cost = standard cost sum from costing (margin-side).
    """
    from backend.app.services.job_costing import compute_job_costing_summary_dict, get_job_cost_snapshot

    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    notes: list[str] = []
    snap = get_job_cost_snapshot(db, job_id=job_id)

    if snap:
        labour_total = round(float(snap.labour_cost or 0) + float(getattr(snap, "travel_cost", 0) or 0), 2)
        warnings = json.loads(snap.warnings_json or "[]")
        lw = json.loads(getattr(snap, "labour_cost_warnings_json", None) or "[]")
        warnings = list(warnings) + [f"labour:{x}" for x in lw]
        materials_actual = round(float(snap.actual_material_cost), 2)
        mat_customer = round(float(snap.materials_billable_total), 2)
        if mat_customer <= 0 and float(snap.actual_material_qty) > 1e-6:
            mat_customer = _legacy_quote_materials_sell_total(db, job=job)
            notes.append("materials_charge_fallback_quote_line_totals")
        elif mat_customer <= 0:
            mat_customer = _legacy_quote_materials_sell_total(db, job=job)
        return {
            "labour_total": labour_total,
            "materials_total": mat_customer,
            "materials_actual_cost": materials_actual,
            "job_cost_snapshot_id": snap.id,
            "warnings": warnings,
            "notes": "; ".join(notes) if notes else None,
        }

    live = compute_job_costing_summary_dict(db, job_id=job_id)
    warnings = list(live.get("costing_warnings", []))
    labour_total = round(
        float(live.get("labour_cost") or 0) + float(live.get("travel_cost") or 0),
        2,
    )
    materials_actual = round(float(live["actual_material_cost"]), 2)
    act_qty = float(live["actual_material_qty"])
    if act_qty > 1e-6:
        mat_customer = round(float(live["materials_billable_from_actual"]), 2)
        if mat_customer <= 0:
            mat_customer = _legacy_quote_materials_sell_total(db, job=job)
            notes.append("materials_charge_fallback_quote_line_totals")
    else:
        mat_customer = _legacy_quote_materials_sell_total(db, job=job)

    return {
        "labour_total": labour_total,
        "materials_total": mat_customer,
        "materials_actual_cost": materials_actual,
        "job_cost_snapshot_id": None,
        "warnings": warnings,
        "notes": "; ".join(notes) if notes else None,
    }


def generate_invoice(db: Session, *, job_id: str, acting_user_id: str | None = None) -> Invoice:
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")

    # Phase 1/2 release-gate hardening:
    # Don't allow invoice release unless the job is completed and compliance exists.
    # (Doc: Step 10 "Invoice release should be blocked if job incomplete / compliance missing".)
    if job.status != "completed":
        raise ValueError("Job status incomplete")

    compliance_exists = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id, Certificate.status.in_(["generated", "signed"]))
        .first()
    )
    if not compliance_exists:
        raise ValueError("Compliance missing")

    basis = build_invoice_cost_basis(db, job_id=job_id)
    grand_total = round(float(basis["labour_total"]) + float(basis["materials_total"]), 2)

    note = basis.get("notes")
    if basis.get("warnings"):
        w = "; ".join(str(x) for x in basis["warnings"][:8])
        note = (note + " | " if note else "") + f"costing_warnings:{w}"

    invoice = Invoice(
        job_id=job_id,
        currency="GBP",
        status="unpaid",
        labour_total=float(basis["labour_total"]),
        materials_total=float(basis["materials_total"]),
        grand_total=grand_total,
        job_cost_snapshot_id=basis.get("job_cost_snapshot_id"),
        materials_actual_cost=basis.get("materials_actual_cost"),
        cost_basis_notes=note[:4000] if note else None,
    )
    db.add(invoice)
    db.flush()
    db.refresh(invoice)
    from backend.app.modules.documents.persist import persist_generated_invoice_document

    persist_generated_invoice_document(
        db, invoice=invoice, uploaded_by_user_id=acting_user_id, commit=False
    )
    db.commit()
    db.refresh(invoice)
    return invoice


def list_invoices(
    db: Session,
    *,
    job_id: str | None = None,
    status: str | None = None,
    finance_reviewed: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Invoice]:
    q = db.query(Invoice).order_by(Invoice.created_at.desc())
    if job_id:
        q = q.filter(Invoice.job_id == job_id)
    if status:
        q = q.filter(Invoice.status == status)
    if finance_reviewed is True:
        q = q.filter(Invoice.finance_reviewed_at.isnot(None))
    if finance_reviewed is False:
        q = q.filter(Invoice.finance_reviewed_at.is_(None))
    return q.offset(offset).limit(limit).all()


def _invoice_export_row(i: Invoice) -> dict[str, Any]:
    return {
        "invoice_id": i.id,
        "job_id": i.job_id,
        "status": i.status,
        "grand_total": i.grand_total,
        "currency": i.currency,
        "labour_total": i.labour_total,
        "materials_total": i.materials_total,
        "materials_actual_cost": i.materials_actual_cost,
        "job_cost_snapshot_id": i.job_cost_snapshot_id,
        "paid_at": i.paid_at.isoformat() if i.paid_at else None,
        "finance_reviewed_at": i.finance_reviewed_at.isoformat() if i.finance_reviewed_at else None,
    }


def invoice_export_rows(
    db: Session,
    *,
    limit: int = 500,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Stable column set for CSV / external finance tools (§5.4 export consistency)."""
    cap = min(max(limit, 1), 2000)
    q = db.query(Invoice).order_by(Invoice.created_at.desc())
    if status:
        q = q.filter(Invoice.status == status)
    return [_invoice_export_row(i) for i in q.limit(cap).all()]


def invoice_reconciliation_summary(db: Session) -> dict[str, Any]:
    """AR-style buckets and paid velocity for finance ops (§5.4)."""
    now = utc_now()
    unpaid = db.query(Invoice).filter(Invoice.status == "unpaid").all()
    held = db.query(Invoice).filter(Invoice.status == "held").all()
    paid_recent = (
        db.query(Invoice)
        .filter(Invoice.status == "paid", Invoice.paid_at.isnot(None), Invoice.paid_at >= now - timedelta(days=30))
        .count()
    )

    def _age_days(inv: Invoice) -> int:
        ca = inv.created_at
        if ca.tzinfo is None:
            ca = ca.replace(tzinfo=timezone.utc)
        return max(0, (now - ca.astimezone(timezone.utc)).days)

    buckets = {"0_7_days": 0, "8_30_days": 0, "31_plus_days": 0}
    for inv in unpaid + held:
        d = _age_days(inv)
        if d <= 7:
            buckets["0_7_days"] += 1
        elif d <= 30:
            buckets["8_30_days"] += 1
        else:
            buckets["31_plus_days"] += 1

    outstanding = round(sum(float(i.grand_total) for i in unpaid) + sum(float(i.grand_total) for i in held), 2)

    return {
        "as_of": now.isoformat(),
        "counts": {
            "unpaid": len(unpaid),
            "held": len(held),
            "paid_last_30_days": int(paid_recent),
        },
        "open_invoice_age_buckets": buckets,
        "outstanding_grand_total_open": outstanding,
        "currencies_note": "Totals assume a single currency per deployment; mixed-currency sums are approximate.",
    }


def hold_invoice(
    db: Session,
    *,
    invoice_id: str,
    note: str,
    acting_user_id: str | None = None,
    reason_lines: list[str] | None = None,
) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise ValueError("Invoice not found")
    if inv.status == "paid":
        raise ValueError("Cannot hold a paid invoice")
    if inv.status == "held":
        raise ValueError("Invoice already held")
    parts = [note.strip()]
    if reason_lines:
        parts.append("; ".join(str(x) for x in reason_lines))
    text = " | ".join(p for p in parts if p)
    inv.status = "held"
    prefix = inv.cost_basis_notes or ""
    inv.cost_basis_notes = (prefix + "\n" if prefix else "") + f"[hold] {text}"
    db.add(inv)
    db.commit()
    db.refresh(inv)
    _ = acting_user_id  # reserved for future audit row
    return inv


def release_invoice_from_hold(
    db: Session,
    *,
    invoice_id: str,
    note: str,
    acting_user_id: str | None = None,
) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise ValueError("Invoice not found")
    if inv.status != "held":
        raise ValueError("Invoice is not on hold")
    inv.status = "unpaid"
    prefix = inv.cost_basis_notes or ""
    inv.cost_basis_notes = (prefix + "\n" if prefix else "") + f"[release_hold] {note.strip()}"
    db.add(inv)
    db.commit()
    db.refresh(inv)
    _ = acting_user_id
    return inv


def pay_invoice(db: Session, *, invoice_id: str) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")
    if invoice.status == "held":
        raise ValueError("Cannot pay a held invoice — release hold first")
    if invoice.status == "paid":
        return invoice
    invoice.status = "paid"
    invoice.paid_at = utc_now()
    db.commit()
    db.refresh(invoice)
    try:
        from backend.app.modules.portal.communication_hooks import emit_customer_comms_event

        emit_customer_comms_event(
            db,
            job_id=invoice.job_id,
            event_type="payment_received",
            payload={"invoice_id": invoice.id},
        )
    except Exception:
        pass
    return invoice


def mark_invoice_finance_reviewed(
    db: Session,
    *,
    invoice_id: str,
    acting_user_id: str,
    note: str | None = None,
) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise ValueError("Invoice not found")
    if inv.status == "paid":
        raise ValueError("Cannot mark finance review on a paid invoice")
    inv.finance_reviewed_at = utc_now()
    inv.finance_reviewed_by_user_id = acting_user_id
    if note and note.strip():
        prefix = inv.cost_basis_notes or ""
        inv.cost_basis_notes = (prefix + "\n" if prefix else "") + f"[finance_review] {note.strip()}"
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def clear_invoice_finance_review(
    db: Session,
    *,
    invoice_id: str,
    note: str | None = None,
) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise ValueError("Invoice not found")
    if inv.status == "paid":
        raise ValueError("Cannot clear finance review on a paid invoice")
    inv.finance_reviewed_at = None
    inv.finance_reviewed_by_user_id = None
    if note and note.strip():
        prefix = inv.cost_basis_notes or ""
        inv.cost_basis_notes = (prefix + "\n" if prefix else "") + f"[finance_review_cleared] {note.strip()}"
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def finance_operations_dashboard(db: Session, *, limit_queue: int = 100) -> dict[str, Any]:
    """
    Finance-facing queue: held invoices, unpaid awaiting review, costing-warning flags (§5.4).
    """
    from sqlalchemy import func

    status_counts: dict[str, int] = {}
    for st in ("unpaid", "held", "paid"):
        n = db.query(func.count(Invoice.id)).filter(Invoice.status == st).scalar()
        status_counts[st] = int(n or 0)

    held_rows = (
        db.query(Invoice).filter(Invoice.status == "held").order_by(Invoice.created_at.desc()).limit(50).all()
    )
    unpaid_no_review = (
        db.query(Invoice)
        .filter(Invoice.status == "unpaid", Invoice.finance_reviewed_at.is_(None))
        .order_by(Invoice.created_at.desc())
        .limit(limit_queue)
        .all()
    )
    unpaid_reviewed = (
        db.query(Invoice)
        .filter(Invoice.status == "unpaid", Invoice.finance_reviewed_at.isnot(None))
        .order_by(Invoice.finance_reviewed_at.desc())
        .limit(50)
        .all()
    )

    def _row(i: Invoice) -> dict[str, Any]:
        notes = i.cost_basis_notes or ""
        return {
            "invoice_id": i.id,
            "job_id": i.job_id,
            "status": i.status,
            "grand_total": i.grand_total,
            "currency": i.currency,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "finance_reviewed_at": i.finance_reviewed_at.isoformat() if i.finance_reviewed_at else None,
            "finance_reviewed_by_user_id": i.finance_reviewed_by_user_id,
            "has_costing_warnings": "costing_warnings:" in notes,
            "on_hold": i.status == "held",
        }

    return {
        "status_counts": status_counts,
        "held_invoices": [_row(i) for i in held_rows],
        "unpaid_awaiting_finance_review": [_row(i) for i in unpaid_no_review],
        "unpaid_finance_reviewed_ready_to_collect": [_row(i) for i in unpaid_reviewed],
        "export_column_definitions": [
            {"key": "invoice_id", "description": "Internal invoice UUID"},
            {"key": "job_id", "description": "Linked job UUID"},
            {"key": "status", "description": "unpaid | held | paid"},
            {"key": "grand_total", "description": "Customer grand total"},
            {"key": "currency", "description": "ISO currency code"},
            {"key": "labour_total", "description": "Labour + travel charge component"},
            {"key": "materials_total", "description": "Customer materials charge"},
            {"key": "materials_actual_cost", "description": "Internal cost basis (margin side)"},
            {"key": "job_cost_snapshot_id", "description": "Frozen costing snapshot when present"},
            {"key": "paid_at", "description": "Payment timestamp when paid"},
            {"key": "finance_reviewed_at", "description": "Finance sign-off timestamp"},
        ],
        "credit_notes_and_adjustments": {
            "status": "external_system",
            "in_app_supported": False,
            "message": (
                "Credit notes and formal accounting adjustments are issued in your finance system (Xero, Sage, QuickBooks, "
                "etc.). Export invoice rows from PHI-DPS for reconciliation; operational invoices here remain the field "
                "billing source of truth."
            ),
            "export_hint": "GET /invoicing/invoices/export-rows",
        },
    }
