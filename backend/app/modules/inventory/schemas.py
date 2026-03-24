from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class StockItemCreateIn(BaseModel):
    sku: str
    name: str
    unit_cost: float = 0.0
    on_hand_quantity: float = 0.0
    reorder_point_quantity: float = 0.0
    unit_of_measure: str = "ea"


class StockItemOut(BaseModel):
    id: str
    sku: str
    name: str
    unit_cost: float
    on_hand_quantity: float
    reserved_quantity: float
    reorder_point_quantity: float
    unit_of_measure: str = "ea"
    created_at: datetime

    class Config:
        from_attributes = True


class StockReservationOut(BaseModel):
    id: str
    quote_id: str
    job_id: str | None
    sku: str
    quantity: float
    status: str
    location_id: str | None = None
    stock_item_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class StockLocationOut(BaseModel):
    id: str
    code: str
    name: str
    kind: str
    engineer_user_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VanLocationCreateIn(BaseModel):
    code: str
    name: str
    engineer_user_id: str | None = None


class JobReservePartsIn(BaseModel):
    sku: str
    quantity: float
    location_id: str


class StockTransferLineIn(BaseModel):
    sku: str
    quantity: float


class StockTransferCreateIn(BaseModel):
    from_location_id: str
    to_location_id: str
    lines: list[StockTransferLineIn]


class StockTransferLineOut(BaseModel):
    id: str
    stock_item_id: str
    quantity: float

    class Config:
        from_attributes = True


class PurchaseOrderLineIn(BaseModel):
    sku: str
    quantity: float
    unit_cost: float = 0.0


class PurchaseOrderCreateIn(BaseModel):
    supplier_name: str
    lines: list[PurchaseOrderLineIn]


class PurchaseOrderLineReceiveIn(BaseModel):
    quantity: float
    to_location_id: str | None = None

