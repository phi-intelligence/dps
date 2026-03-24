from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.modules.quoting.models import Quote, QuoteItem
from backend.app.modules.quoting.schemas import QuoteCreateIn


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_quote_totals(*, items: list[QuoteItem]) -> tuple[float, float, float]:
    labour_total = 0.0
    materials_total = 0.0

    for it in items:
        if it.item_type == "labour":
            labour_total += it.line_total
        elif it.item_type == "materials":
            materials_total += it.line_total
        else:
            # Default to labour to avoid blocking flows for unknown types.
            labour_total += it.line_total

    grand_total = labour_total + materials_total
    return labour_total, materials_total, grand_total


def create_quote(db: Session, *, payload: QuoteCreateIn) -> Quote:
    items: list[QuoteItem] = []
    for item_in in payload.items:
        line_total = float(item_in.quantity) * float(item_in.unit_price)
        items.append(
            QuoteItem(
                item_type=item_in.item_type,
                description=item_in.description,
                quantity=item_in.quantity,
                unit_price=item_in.unit_price,
                line_total=line_total,
            )
        )

    labour_total, materials_total, grand_total = compute_quote_totals(items=items)

    quote = Quote(
        customer_id=payload.customer_id,
        status="draft",
        currency=payload.currency,
        notes=payload.notes,
        labour_total=labour_total,
        materials_total=materials_total,
        grand_total=grand_total,
        items=items,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def accept_quote(db: Session, *, quote_id: str) -> Quote:
    quote = db.get(Quote, quote_id)
    if not quote:
        raise ValueError("Quote not found")

    quote.status = "accepted"
    quote.accepted_at = utc_now()

    # Phase 3 integration: if the quote includes material line-items,
    # reserve parts in inventory for the accepted quote.
    from backend.app.modules.inventory.service import reserve_parts_for_quote

    reserve_parts_for_quote(db, quote_id=quote_id, job_id=None, commit=False)

    db.commit()
    db.refresh(quote)
    return quote


def list_quotes(db: Session, *, limit: int = 50, offset: int = 0) -> list[Quote]:
    return (
        db.query(Quote)
        .order_by(Quote.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

