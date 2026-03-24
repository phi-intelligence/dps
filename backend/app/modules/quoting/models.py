from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Links to CRM Customer (later we can add versioning/snapshots).
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(64), default="draft", index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    labour_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    materials_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["QuoteItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotes.id"), index=True, nullable=False)

    item_type: Mapped[str] = mapped_column(String(32), default="labour", index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    line_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="items")

