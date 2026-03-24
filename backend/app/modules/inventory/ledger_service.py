"""
Ledger-first inventory: every movement writes an immutable InventoryLedgerEntry
and updates StockBalance in the same DB transaction.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.inventory.models import (
    InventoryLedgerEntry,
    StockBalance,
    StockItem,
    StockLocation,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_default_warehouse(db: Session) -> StockLocation:
    loc = db.query(StockLocation).filter(StockLocation.code == "DEFAULT_WH").one_or_none()
    if not loc:
        raise RuntimeError("DEFAULT_WH location missing; run ensure_default_inventory_locations()")
    return loc


def ensure_default_inventory_locations(db: Session) -> StockLocation:
    loc = db.query(StockLocation).filter(StockLocation.code == "DEFAULT_WH").one_or_none()
    if loc:
        return loc
    loc = StockLocation(
        code="DEFAULT_WH",
        name="Default warehouse",
        kind="warehouse",
        engineer_user_id=None,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def sync_legacy_stock_items_to_default_warehouse(db: Session) -> None:
    """
    One-time style sync: if StockBalance rows are missing for items that only exist on legacy
    StockItem aggregate columns, seed DEFAULT_WH balances (no ledger rows — bootstrap only).
    """
    from backend.app.modules.inventory.models import StockBalance, StockItem

    wh = ensure_default_inventory_locations(db)
    for item in db.query(StockItem).all():
        exists = (
            db.query(StockBalance)
            .filter(StockBalance.stock_item_id == item.id, StockBalance.location_id == wh.id)
            .one_or_none()
        )
        if exists:
            continue
        on_h = float(item.on_hand_quantity)
        res = float(item.reserved_quantity)
        if on_h <= 0 and res <= 0:
            continue
        bal = StockBalance(
            id=str(uuid.uuid4()),
            location_id=wh.id,
            stock_item_id=item.id,
            on_hand=max(on_h, res),
            reserved=min(res, max(on_h, res)),
        )
        db.add(bal)
    db.commit()


def get_or_create_balance(db: Session, *, location_id: str, stock_item_id: str) -> StockBalance:
    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.location_id == location_id,
            StockBalance.stock_item_id == stock_item_id,
        )
        .one_or_none()
    )
    if bal:
        return bal
    bal = StockBalance(
        id=str(uuid.uuid4()),
        location_id=location_id,
        stock_item_id=stock_item_id,
        on_hand=0.0,
        reserved=0.0,
    )
    db.add(bal)
    db.flush()
    return bal


def sync_stock_item_aggregates(db: Session, *, stock_item_id: str) -> None:
    """Denormalize sums onto StockItem for legacy APIs / tests."""
    rows = db.query(StockBalance).filter(StockBalance.stock_item_id == stock_item_id).all()
    total_on = sum(float(r.on_hand) for r in rows)
    total_res = sum(float(r.reserved) for r in rows)
    item = db.get(StockItem, stock_item_id)
    if item:
        item.on_hand_quantity = total_on
        item.reserved_quantity = total_res


def _check_invariants(*, on_hand: float, reserved: float) -> None:
    if reserved < -1e-9 or on_hand < -1e-9:
        raise ValueError("Stock balance would go negative")
    if reserved > on_hand + 1e-6:
        raise ValueError("Reserved quantity cannot exceed on-hand at location")


def append_ledger(
    db: Session,
    *,
    entry_type: str,
    stock_item_id: str,
    location_id: str,
    delta_on_hand: float,
    delta_reserved: float,
    quote_id: str | None = None,
    job_id: str | None = None,
    stock_reservation_id: str | None = None,
    stock_transfer_id: str | None = None,
    transfer_line_id: str | None = None,
    purchase_order_line_id: str | None = None,
    performed_by_user_id: str | None = None,
    note: str | None = None,
    ref_json: str | None = None,
) -> InventoryLedgerEntry:
    bal = get_or_create_balance(db, location_id=location_id, stock_item_id=stock_item_id)
    new_on = float(bal.on_hand) + float(delta_on_hand)
    new_res = float(bal.reserved) + float(delta_reserved)
    _check_invariants(on_hand=new_on, reserved=new_res)

    # When reserving, we need enough available before reservation.
    if entry_type == "reservation" and float(delta_reserved) > 0:
        available_before = float(bal.on_hand) - float(bal.reserved)
        if available_before + 1e-9 < float(delta_reserved):
            raise ValueError("Insufficient available stock for reservation")

    entry = InventoryLedgerEntry(
        entry_type=entry_type,
        stock_item_id=stock_item_id,
        location_id=location_id,
        delta_on_hand=float(delta_on_hand),
        delta_reserved=float(delta_reserved),
        quote_id=quote_id,
        job_id=job_id,
        stock_reservation_id=stock_reservation_id,
        stock_transfer_id=stock_transfer_id,
        transfer_line_id=transfer_line_id,
        purchase_order_line_id=purchase_order_line_id,
        performed_by_user_id=performed_by_user_id,
        note=note,
        ref_json=ref_json,
    )
    bal.on_hand = new_on
    bal.reserved = new_res
    db.add(entry)
    db.flush()
    sync_stock_item_aggregates(db, stock_item_id=stock_item_id)
    return entry


def available_at_location(db: Session, *, location_id: str, stock_item_id: str) -> float:
    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.location_id == location_id,
            StockBalance.stock_item_id == stock_item_id,
        )
        .one_or_none()
    )
    if not bal:
        return 0.0
    return max(0.0, float(bal.on_hand) - float(bal.reserved))
