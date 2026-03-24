from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StockLocation(Base):
    """
    Physical or logical stock location: warehouse, van, inbound, quarantine, etc.
    """

    __tablename__ = "stock_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # warehouse | van | supplier_inbound | quarantine | damaged
    kind: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    engineer_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockItem(Base):
    __tablename__ = "stock_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(16), default="ea", nullable=False)

    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Denormalized aggregates across all locations (kept in sync by ledger operations).
    on_hand_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    reorder_point_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockBalance(Base):
    """
    Per-location balance. Source of truth together with InventoryLedgerEntry.
    Invariant: 0 <= reserved <= on_hand (at each location).
    """

    __tablename__ = "stock_balances"

    __table_args__ = (UniqueConstraint("location_id", "stock_item_id", name="uq_stock_balance_loc_item"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), index=True, nullable=False)
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)

    on_hand: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class InventoryLedgerEntry(Base):
    """
    Immutable inventory movement audit trail.
    """

    __tablename__ = "inventory_ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    entry_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), index=True, nullable=False)

    delta_on_hand: Mapped[float] = mapped_column(Float, nullable=False)
    delta_reserved: Mapped[float] = mapped_column(Float, nullable=False)

    quote_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    stock_reservation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    stock_transfer_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    transfer_line_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    purchase_order_line_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ref_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    quote_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    sku: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stock_locations.id"), nullable=True, index=True)
    stock_item_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stock_items.id"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(16), default="reserved", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockTransaction(Base):
    """
    Legacy mirror table (optional); kept for backward compatibility with older reporting.
    """

    __tablename__ = "stock_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    transaction_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    quote_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), index=True, nullable=False)
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_received: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), index=True, nullable=False)
    to_location_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_locations.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    requested_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class StockTransferLine(Base):
    __tablename__ = "stock_transfer_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_transfer_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_transfers.id"), index=True, nullable=False)
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PurchaseRequest(Base):
    """Suggested procurement from shortage / below reorder (ops queue)."""

    __tablename__ = "purchase_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("stock_items.id"), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="suggested", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
