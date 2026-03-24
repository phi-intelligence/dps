from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.dispatch.models import Job, JobPartUsageLine, JobPartsUsageSubmission
from backend.app.modules.inventory.ledger_service import (
    append_ledger,
    available_at_location,
    ensure_default_inventory_locations,
    get_default_warehouse,
)
from backend.app.modules.inventory.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
    StockItem,
    StockLocation,
    StockReservation,
    StockTransaction,
    StockTransfer,
    StockTransferLine,
)
from backend.app.modules.inventory.schemas import StockItemCreateIn
from backend.app.modules.quoting.models import Quote, QuoteItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _mirror_legacy_tx(
    db: Session,
    *,
    transaction_type: str,
    sku: str,
    quantity: float,
    quote_id: str | None = None,
    job_id: str | None = None,
    note: str | None = None,
) -> None:
    db.add(
        StockTransaction(
            transaction_type=transaction_type,
            sku=sku,
            quantity=quantity,
            quote_id=quote_id,
            job_id=job_id,
            note=note,
        )
    )


def create_stock_item(db: Session, *, payload: StockItemCreateIn) -> StockItem:
    ensure_default_inventory_locations(db)
    wh = get_default_warehouse(db)

    item = StockItem(
        sku=payload.sku,
        name=payload.name,
        unit_of_measure=payload.unit_of_measure,
        unit_cost=payload.unit_cost,
        on_hand_quantity=0.0,
        reserved_quantity=0.0,
        reorder_point_quantity=payload.reorder_point_quantity,
    )
    db.add(item)
    db.flush()

    qty = float(payload.on_hand_quantity)
    if qty > 0:
        append_ledger(
            db,
            entry_type="receipt",
            stock_item_id=item.id,
            location_id=wh.id,
            delta_on_hand=qty,
            delta_reserved=0.0,
            note="Initial stock on item create",
        )
        _mirror_legacy_tx(
            db,
            transaction_type="receipt",
            sku=item.sku,
            quantity=qty,
            note="Initial stock (ledger)",
        )

    db.commit()
    db.refresh(item)
    return item


def list_stock_items(db: Session, *, limit: int = 50, offset: int = 0) -> list[StockItem]:
    return db.query(StockItem).order_by(StockItem.created_at.desc()).offset(offset).limit(limit).all()


def search_stock_items_for_engineer(
    db: Session,
    *,
    query: str | None = None,
    limit: int = 20,
) -> list[StockItem]:
    """
    Lightweight SKU/name lookup for engineer parts entry.
    """
    q = db.query(StockItem)
    needle = (query or "").strip()
    if needle:
        like = f"%{needle}%"
        q = q.filter((StockItem.sku.ilike(like)) | (StockItem.name.ilike(like)))
    return q.order_by(StockItem.sku.asc()).limit(max(1, min(limit, 100))).all()


def list_locations(db: Session) -> list[StockLocation]:
    return db.query(StockLocation).order_by(StockLocation.code.asc()).all()


def create_van_location(db: Session, *, code: str, name: str, engineer_user_id: str | None) -> StockLocation:
    loc = StockLocation(code=code, name=name, kind="van", engineer_user_id=engineer_user_id)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def reserve_parts_for_quote(
    db: Session,
    *,
    quote_id: str,
    job_id: str | None = None,
    commit: bool = True,
    location_id: str | None = None,
    performed_by_user_id: str | None = None,
) -> list[str]:
    """
    Reserve materials for an accepted quote at a stock location (default warehouse).
    """
    ensure_default_inventory_locations(db)
    wh = get_default_warehouse(db)
    loc_id = location_id or wh.id

    quote = db.get(Quote, quote_id)
    if not quote:
        raise ValueError("Quote not found")

    materials_items: list[QuoteItem] = [it for it in quote.items if it.item_type == "materials"]
    if not materials_items:
        return []

    created_reservation_ids: list[str] = []

    for it in materials_items:
        sku = it.description
        if not sku:
            raise ValueError("Materials quote items must have a description (SKU) set")

        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        if not item:
            raise ValueError(f"No stock item for SKU: {sku}")

        required_qty = float(it.quantity)

        append_ledger(
            db,
            entry_type="reservation",
            stock_item_id=item.id,
            location_id=loc_id,
            delta_on_hand=0.0,
            delta_reserved=required_qty,
            quote_id=quote_id,
            job_id=job_id,
            performed_by_user_id=performed_by_user_id,
            note="Reserved from accepted quote",
        )
        _mirror_legacy_tx(
            db,
            transaction_type="reserve",
            sku=sku,
            quantity=required_qty,
            quote_id=quote_id,
            job_id=job_id,
            note="Reserved from accepted quote",
        )

        reservation = StockReservation(
            quote_id=quote_id,
            job_id=job_id,
            sku=sku,
            quantity=required_qty,
            status="reserved",
            location_id=loc_id,
            stock_item_id=item.id,
        )
        db.add(reservation)
        db.flush()
        created_reservation_ids.append(reservation.id)

    if commit:
        db.commit()
    return created_reservation_ids


def reserve_parts_for_job(
    db: Session,
    *,
    job_id: str,
    sku: str,
    quantity: float,
    location_id: str,
    performed_by_user_id: str | None = None,
) -> str:
    """Explicit reservation against a job (and its quote if present)."""
    job = db.get(Job, job_id)
    if not job:
        raise ValueError("Job not found")
    if not job.quote_id:
        raise ValueError("Job has no quote_id to attach reservation")

    item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
    if not item:
        raise ValueError(f"No stock item for SKU: {sku}")

    append_ledger(
        db,
        entry_type="reservation",
        stock_item_id=item.id,
        location_id=location_id,
        delta_on_hand=0.0,
        delta_reserved=float(quantity),
        quote_id=job.quote_id,
        job_id=job_id,
        performed_by_user_id=performed_by_user_id,
        note="Manual job reservation",
    )
    _mirror_legacy_tx(
        db,
        transaction_type="reserve",
        sku=sku,
        quantity=float(quantity),
        quote_id=job.quote_id,
        job_id=job_id,
        note="Manual job reservation",
    )
    r = StockReservation(
        quote_id=job.quote_id,
        job_id=job_id,
        sku=sku,
        quantity=float(quantity),
        status="reserved",
        location_id=location_id,
        stock_item_id=item.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r.id


def release_reservation_by_id(db: Session, *, reservation_id: str, performed_by_user_id: str | None = None) -> None:
    r = db.get(StockReservation, reservation_id)
    if not r or r.status != "reserved":
        return
    if not r.stock_item_id or not r.location_id:
        raise ValueError("Reservation missing ledger linkage")
    qty = float(r.quantity)
    append_ledger(
        db,
        entry_type="release",
        stock_item_id=r.stock_item_id,
        location_id=r.location_id,
        delta_on_hand=0.0,
        delta_reserved=-qty,
        quote_id=r.quote_id,
        job_id=r.job_id,
        stock_reservation_id=r.id,
        performed_by_user_id=performed_by_user_id,
        note="Released reservation",
    )
    _mirror_legacy_tx(
        db,
        transaction_type="release",
        sku=r.sku,
        quantity=qty,
        quote_id=r.quote_id,
        job_id=r.job_id,
        note="Released reservation",
    )
    r.status = "released"
    db.commit()


def list_reservations_for_job_quote(db: Session, *, quote_id: str, job_id: str | None = None) -> list[StockReservation]:
    q = db.query(StockReservation).filter(StockReservation.quote_id == quote_id, StockReservation.status == "reserved")
    if job_id:
        q = q.filter((StockReservation.job_id == job_id) | (StockReservation.job_id.is_(None)))
    return q.all()


def consume_parts_for_quote(
    db: Session,
    *,
    quote_id: str,
    job_id: str,
    commit: bool = True,
    performed_by_user_id: str | None = None,
) -> list[str]:
    """
    On job completion: consume actual usage if captured, else consume full reservations.
    Releases unused reserved quantity. Writes ledger + updates reservation rows.
    """
    processed: list[str] = finalize_reservations_for_job_completion(
        db,
        quote_id=quote_id,
        job_id=job_id,
        performed_by_user_id=performed_by_user_id,
        commit=False,
    )
    if commit:
        db.commit()
    return processed


def finalize_reservations_for_job_completion(
    db: Session,
    *,
    quote_id: str,
    job_id: str,
    performed_by_user_id: str | None = None,
    commit: bool = True,
) -> list[str]:
    reservations = (
        db.query(StockReservation)
        .filter(StockReservation.quote_id == quote_id, StockReservation.status == "reserved")
        .order_by(StockReservation.created_at.asc())
        .all()
    )
    if not reservations:
        return []

    usage_rows = db.query(JobPartUsageLine).filter(JobPartUsageLine.job_id == job_id).all()
    usage_map: dict[tuple[str, str], float] = defaultdict(float)
    for row in usage_rows:
        usage_map[(row.stock_item_id, row.location_id)] += float(row.quantity)

    if not usage_rows:
        return _legacy_consume_all_reservations(
            db,
            reservations=reservations,
            quote_id=quote_id,
            job_id=job_id,
            performed_by_user_id=performed_by_user_id,
            commit=commit,
        )

    touched: list[str] = []
    by_key: dict[tuple[str, str], list[StockReservation]] = defaultdict(list)
    for r in reservations:
        if not r.stock_item_id or not r.location_id:
            ensure_default_inventory_locations(db)
            wh = get_default_warehouse(db)
            item = db.query(StockItem).filter(StockItem.sku == r.sku).one_or_none()
            if not item:
                continue
            r.stock_item_id = item.id
            r.location_id = wh.id
            db.flush()
        by_key[(r.stock_item_id, r.location_id)].append(r)

    for (item_id, loc_id), rows in by_key.items():
        used_total = float(usage_map.get((item_id, loc_id), 0.0))
        reserved_total = sum(float(x.quantity) for x in rows)
        release_total = max(0.0, reserved_total - used_total)
        consume_from_reserved = min(used_total, reserved_total)
        over_total = max(0.0, used_total - reserved_total)
        sku = rows[0].sku if rows else ""

        if release_total > 0:
            append_ledger(
                db,
                entry_type="release",
                stock_item_id=item_id,
                location_id=loc_id,
                delta_on_hand=0.0,
                delta_reserved=-release_total,
                quote_id=quote_id,
                job_id=job_id,
                stock_reservation_id=rows[0].id,
                performed_by_user_id=performed_by_user_id,
                note="Release unused reservation aggregate on job completion",
            )
            _mirror_legacy_tx(
                db,
                transaction_type="release",
                sku=sku,
                quantity=release_total,
                quote_id=quote_id,
                job_id=job_id,
                note="Release unused reservation",
            )

        if consume_from_reserved > 0:
            append_ledger(
                db,
                entry_type="consumption",
                stock_item_id=item_id,
                location_id=loc_id,
                delta_on_hand=-consume_from_reserved,
                delta_reserved=-consume_from_reserved,
                quote_id=quote_id,
                job_id=job_id,
                stock_reservation_id=rows[0].id,
                performed_by_user_id=performed_by_user_id,
                note="Consume reserved stock aggregate on job completion",
            )
            _mirror_legacy_tx(
                db,
                transaction_type="consume",
                sku=sku,
                quantity=consume_from_reserved,
                quote_id=quote_id,
                job_id=job_id,
                note="Consume reserved stock",
            )

        if over_total > 0:
            item = db.get(StockItem, item_id)
            sku2 = item.sku if item else sku
            free = available_at_location(db, location_id=loc_id, stock_item_id=item_id)
            if free + 1e-9 < over_total:
                raise ValueError(f"Insufficient unreserved stock for over-consumption SKU {sku2}")
            append_ledger(
                db,
                entry_type="consumption_unreserved",
                stock_item_id=item_id,
                location_id=loc_id,
                delta_on_hand=-over_total,
                delta_reserved=0.0,
                quote_id=quote_id,
                job_id=job_id,
                performed_by_user_id=performed_by_user_id,
                note="Consume beyond reservation (reconciled usage)",
            )
            _mirror_legacy_tx(
                db,
                transaction_type="consume",
                sku=sku2,
                quantity=over_total,
                quote_id=quote_id,
                job_id=job_id,
                note="Consume unreserved (overuse)",
            )

        for r in rows:
            r.status = "consumed"
            r.job_id = job_id
            touched.append(r.id)
        db.flush()

    if commit:
        db.commit()
    return touched


def _legacy_consume_all_reservations(
    db: Session,
    *,
    reservations: list[StockReservation],
    quote_id: str,
    job_id: str,
    performed_by_user_id: str | None,
    commit: bool,
) -> list[str]:
    touched: list[str] = []
    for r in reservations:
        if not r.stock_item_id or not r.location_id:
            ensure_default_inventory_locations(db)
            wh = get_default_warehouse(db)
            item = db.query(StockItem).filter(StockItem.sku == r.sku).one_or_none()
            if not item:
                continue
            r.stock_item_id = item.id
            r.location_id = wh.id
            db.flush()
        qty = float(r.quantity)
        append_ledger(
            db,
            entry_type="consumption",
            stock_item_id=r.stock_item_id,
            location_id=r.location_id,
            delta_on_hand=-qty,
            delta_reserved=-qty,
            quote_id=quote_id,
            job_id=job_id,
            stock_reservation_id=r.id,
            performed_by_user_id=performed_by_user_id,
            note="Consumed on job completion (legacy full reservation)",
        )
        _mirror_legacy_tx(
            db,
            transaction_type="consume",
            sku=r.sku,
            quantity=qty,
            quote_id=quote_id,
            job_id=job_id,
            note="Consumed on job completion",
        )
        r.status = "consumed"
        r.job_id = job_id
        touched.append(r.id)
    if commit:
        db.commit()
    return touched


def quote_material_skus(db: Session, *, quote_id: str) -> set[str]:
    quote = db.get(Quote, quote_id)
    if not quote:
        return set()
    return {it.description for it in quote.items if it.item_type == "materials" and it.description}


def reconcile_parts_usage_submission(
    db: Session,
    *,
    job: Job,
    submission: JobPartsUsageSubmission,
    raw_items: list[dict[str, Any]],
) -> None:
    """
    Create JobPartUsageLine rows with match_status for reconciliation / completion gating.
    """
    ensure_default_inventory_locations(db)
    wh = get_default_warehouse(db)
    quote_skus = quote_material_skus(db, quote_id=job.quote_id) if job.quote_id else set()

    res_map: dict[tuple[str, str], float] = defaultdict(float)
    if job.quote_id:
        for r in (
            db.query(StockReservation)
            .filter(
                StockReservation.quote_id == job.quote_id,
                StockReservation.status == "reserved",
            )
            .all()
        ):
            if r.stock_item_id and r.location_id:
                res_map[(r.stock_item_id, r.location_id)] += float(r.quantity)

    for raw in raw_items:
        sku = str(raw.get("sku") or raw.get("SKU") or raw.get("description") or "").strip()
        if not sku:
            continue
        qty = float(raw.get("quantity") or raw.get("qty") or 0)
        if qty <= 0:
            continue
        loc_id = str(raw.get("location_id") or "").strip() or wh.id

        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        if not item:
            raise ValueError(f"Unknown SKU in parts usage: {sku}")

        reserved_here = float(res_map.get((item.id, loc_id), 0.0))
        free = available_at_location(db, location_id=loc_id, stock_item_id=item.id)

        if job.quote_id and sku not in quote_skus:
            status = "unreserved"
            note = "SKU not on quote materials"
        elif qty <= reserved_here + 1e-9:
            status = "matched"
            note = None
        else:
            extra = qty - reserved_here
            if free + 1e-9 >= extra:
                status = "overused"
                note = f"Used {extra} beyond reservation; covered by available stock"
            else:
                status = "unavailable"
                note = f"Need {extra} beyond reservation but only {free} available"

        db.add(
            JobPartUsageLine(
                job_id=job.id,
                submission_id=submission.id,
                stock_item_id=item.id,
                location_id=loc_id,
                quantity=qty,
                match_status=status,
                reserved_available_for_sku=reserved_here,
                note=note,
            )
        )
    db.flush()


# --- Start-4e / 4f operational flows ---


def material_shortage_preview_for_quote(db: Session, *, quote_id: str) -> list[dict[str, Any]]:
    """Planner view: materials on quote vs available at default warehouse."""
    ensure_default_inventory_locations(db)
    wh = get_default_warehouse(db)
    quote = db.get(Quote, quote_id)
    if not quote:
        raise ValueError("Quote not found")
    out: list[dict[str, Any]] = []
    for it in quote.items:
        if it.item_type != "materials":
            continue
        sku = (it.description or "").strip()
        if not sku:
            continue
        req = float(it.quantity)
        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        if not item:
            out.append({"sku": sku, "required": req, "available": 0.0, "short": req, "reason": "no_stock_item"})
            continue
        av = available_at_location(db, location_id=wh.id, stock_item_id=item.id)
        if av + 1e-9 < req:
            out.append({"sku": sku, "required": req, "available": av, "short": max(0.0, req - av), "reason": "below_available"})
    return out


def low_stock_items(db: Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in db.query(StockItem).order_by(StockItem.sku.asc()).all():
        if float(i.reorder_point_quantity) <= 0:
            continue
        if float(i.on_hand_quantity) <= float(i.reorder_point_quantity):
            rows.append(
                {
                    "sku": i.sku,
                    "name": i.name,
                    "on_hand_total": float(i.on_hand_quantity),
                    "reorder_point": float(i.reorder_point_quantity),
                }
            )
    return rows


def unreconciled_parts_usage_lines(db: Session) -> list[JobPartUsageLine]:
    return (
        db.query(JobPartUsageLine)
        .filter(
            JobPartUsageLine.match_status.in_(["overused", "unreserved", "unavailable", "shortage"]),
        )
        .order_by(JobPartUsageLine.created_at.desc())
        .limit(200)
        .all()
    )


def suggest_purchase_requests_for_low_stock(db: Session) -> list[str]:
    created: list[str] = []
    for row in low_stock_items(db):
        item = db.query(StockItem).filter(StockItem.sku == row["sku"]).one_or_none()
        if not item:
            continue
        suggested_qty = max(float(item.reorder_point_quantity) * 2 - float(item.on_hand_quantity), 0.0)
        if suggested_qty <= 0:
            continue
        pr = PurchaseRequest(
            stock_item_id=item.id,
            quantity=suggested_qty,
            reason="Below reorder point (auto-suggest)",
            status="suggested",
        )
        db.add(pr)
        db.flush()
        created.append(pr.id)
    db.commit()
    return created


def create_purchase_order(
    db: Session,
    *,
    supplier_name: str,
    lines: list[tuple[str, float, float]],
    created_by_user_id: str | None = None,
    commit: bool = True,
) -> PurchaseOrder:
    po = PurchaseOrder(supplier_name=supplier_name, status="draft", created_by_user_id=created_by_user_id)
    db.add(po)
    db.flush()
    for sku, qty, unit_cost in lines:
        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        if not item:
            raise ValueError(f"Unknown SKU: {sku}")
        db.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                stock_item_id=item.id,
                quantity_ordered=float(qty),
                quantity_received=0.0,
                unit_cost=float(unit_cost),
            )
        )
    if commit:
        db.commit()
        db.refresh(po)
    else:
        db.flush()
    return po


def approve_purchase_order(
    db: Session,
    *,
    purchase_order_id: str,
    approved_by_user_id: str | None = None,
) -> PurchaseOrder:
    po = db.get(PurchaseOrder, purchase_order_id)
    if not po:
        raise ValueError("Purchase order not found")
    if po.status not in ("draft",):
        raise ValueError(f"PO cannot be approved from status {po.status}")
    po.status = "approved"
    db.add(po)
    db.commit()
    db.refresh(po)
    _ = approved_by_user_id
    return po


def receive_purchase_order_line(
    db: Session,
    *,
    line_id: str,
    quantity: float,
    to_location_id: str | None = None,
    performed_by_user_id: str | None = None,
) -> PurchaseOrderLine:
    line = db.get(PurchaseOrderLine, line_id)
    if not line:
        raise ValueError("PO line not found")
    po = db.get(PurchaseOrder, line.purchase_order_id)
    if not po:
        raise ValueError("PO not found")
    if po.status not in ("approved", "partially_received", "received"):
        raise ValueError("Purchase order must be approved before receiving lines")

    ensure_default_inventory_locations(db)
    loc_id = to_location_id or get_default_warehouse(db).id
    q = float(quantity)
    if q <= 0:
        raise ValueError("quantity must be positive")

    append_ledger(
        db,
        entry_type="receipt",
        stock_item_id=line.stock_item_id,
        location_id=loc_id,
        delta_on_hand=q,
        delta_reserved=0.0,
        purchase_order_line_id=line.id,
        performed_by_user_id=performed_by_user_id,
        note=f"PO receipt {po.id[:8]}",
    )
    item = db.get(StockItem, line.stock_item_id)
    if item:
        _mirror_legacy_tx(
            db,
            transaction_type="receipt",
            sku=item.sku,
            quantity=q,
            note="PO receipt",
        )

    line.quantity_received = float(line.quantity_received) + q
    all_lines = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).all()
    if all(float(x.quantity_received) + 1e-9 >= float(x.quantity_ordered) for x in all_lines):
        po.status = "received"
    elif any(float(x.quantity_received) > 0 for x in all_lines):
        po.status = "partially_received"
    db.commit()
    db.refresh(line)
    return line


def create_stock_transfer(
    db: Session,
    *,
    from_location_id: str,
    to_location_id: str,
    lines: list[tuple[str, float]],
    requested_by_user_id: str | None = None,
    commit: bool = True,
) -> StockTransfer:
    t = StockTransfer(
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        status="draft",
        requested_by_user_id=requested_by_user_id,
    )
    db.add(t)
    db.flush()
    for sku, qty in lines:
        item = db.query(StockItem).filter(StockItem.sku == sku).one_or_none()
        if not item:
            raise ValueError(f"Unknown SKU: {sku}")
        db.add(
            StockTransferLine(
                stock_transfer_id=t.id,
                stock_item_id=item.id,
                quantity=float(qty),
            )
        )
    if commit:
        db.commit()
        db.refresh(t)
    else:
        db.flush()
    return t


def approve_and_ship_stock_transfer(
    db: Session,
    *,
    transfer_id: str,
    approved_by_user_id: str | None = None,
) -> StockTransfer:
    t = db.get(StockTransfer, transfer_id)
    if not t:
        raise ValueError("Transfer not found")
    if t.status != "draft":
        raise ValueError("Transfer not in draft state")

    lines = db.query(StockTransferLine).filter(StockTransferLine.stock_transfer_id == t.id).all()
    for ln in lines:
        qty = float(ln.quantity)
        append_ledger(
            db,
            entry_type="transfer_out",
            stock_item_id=ln.stock_item_id,
            location_id=t.from_location_id,
            delta_on_hand=-qty,
            delta_reserved=0.0,
            stock_transfer_id=t.id,
            transfer_line_id=ln.id,
            performed_by_user_id=approved_by_user_id,
            note="Transfer ship from source",
        )
        item = db.get(StockItem, ln.stock_item_id)
        if item:
            _mirror_legacy_tx(
                db,
                transaction_type="transfer_out",
                sku=item.sku,
                quantity=qty,
                note=f"Transfer {t.id[:8]}",
            )

    t.status = "in_transit"
    t.approved_by_user_id = approved_by_user_id
    db.commit()
    db.refresh(t)
    return t


def receive_stock_transfer(
    db: Session,
    *,
    transfer_id: str,
    performed_by_user_id: str | None = None,
) -> StockTransfer:
    t = db.get(StockTransfer, transfer_id)
    if not t:
        raise ValueError("Transfer not found")
    if t.status != "in_transit":
        raise ValueError("Transfer not in transit")

    lines = db.query(StockTransferLine).filter(StockTransferLine.stock_transfer_id == t.id).all()
    for ln in lines:
        qty = float(ln.quantity)
        append_ledger(
            db,
            entry_type="transfer_in",
            stock_item_id=ln.stock_item_id,
            location_id=t.to_location_id,
            delta_on_hand=qty,
            delta_reserved=0.0,
            stock_transfer_id=t.id,
            transfer_line_id=ln.id,
            performed_by_user_id=performed_by_user_id,
            note="Transfer receive at destination",
        )
        item = db.get(StockItem, ln.stock_item_id)
        if item:
            _mirror_legacy_tx(
                db,
                transaction_type="transfer_in",
                sku=item.sku,
                quantity=qty,
                note=f"Transfer {t.id[:8]}",
            )

    t.status = "received"
    db.commit()
    db.refresh(t)
    return t


def parts_usage_blocks_strict_completion(db: Session, *, job_id: str) -> bool:
    from backend.app.services.runtime_settings_service import get_effective_feature_flags
    from backend.app.modules.dispatch.models import JobPartsReconciliationApproval

    ff = get_effective_feature_flags(db)
    if not bool(ff.get("strict_parts_reconciliation", False)):
        return False

    job = db.get(Job, job_id)
    if job:
        policy = getattr(job, "material_policy", None) or "materials_optional"
        if policy == "no_materials_expected":
            return False
        if policy == "materials_optional":
            has_lines = (
                db.query(JobPartUsageLine).filter(JobPartUsageLine.job_id == job_id).first() is not None
            )
            if not has_lines:
                return False

    if db.query(JobPartsReconciliationApproval).filter(JobPartsReconciliationApproval.job_id == job_id).first():
        return False
    bad = (
        db.query(JobPartUsageLine)
        .filter(
            JobPartUsageLine.job_id == job_id,
            JobPartUsageLine.match_status.in_(["overused", "unreserved", "unavailable", "shortage"]),
        )
        .first()
    )
    return bad is not None
