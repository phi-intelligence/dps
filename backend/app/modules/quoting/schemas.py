from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class QuoteItemIn(BaseModel):
    item_type: str = "labour"  # "labour" | "materials"
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0


class QuoteItemOut(BaseModel):
    id: str
    item_type: str
    description: str
    quantity: float
    unit_price: float
    line_total: float

    class Config:
        from_attributes = True


class QuoteCreateIn(BaseModel):
    customer_id: str | None = None
    currency: str = "GBP"
    notes: str | None = None
    items: list[QuoteItemIn]


class QuoteOut(BaseModel):
    id: str
    customer_id: str | None
    status: str
    currency: str
    notes: str | None

    labour_total: float
    materials_total: float
    grand_total: float

    created_at: datetime
    accepted_at: datetime | None
    items: list[QuoteItemOut]

    class Config:
        from_attributes = True


class QuoteAcceptOut(BaseModel):
    quote: QuoteOut

