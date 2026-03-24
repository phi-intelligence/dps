from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class InvoiceGenerateIn(BaseModel):
    job_id: str


class InvoiceHoldIn(BaseModel):
    note: str


class InvoiceReleaseHoldIn(BaseModel):
    note: str = "Release hold"


class InvoiceOut(BaseModel):
    id: str
    job_id: str
    currency: str
    status: str
    labour_total: float
    materials_total: float
    grand_total: float
    job_cost_snapshot_id: str | None = None
    materials_actual_cost: float | None = None
    cost_basis_notes: str | None = None
    paid_at: datetime | None
    created_at: datetime
    finance_reviewed_at: datetime | None = None
    finance_reviewed_by_user_id: str | None = None

    class Config:
        from_attributes = True


class InvoiceFinanceReviewNoteIn(BaseModel):
    note: str | None = None

