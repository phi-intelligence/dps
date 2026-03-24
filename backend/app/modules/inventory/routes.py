from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.services.authorization_policy import CAN_APPROVE_PURCHASE_ORDER, CAN_CREATE_PURCHASE_ORDER
from backend.app.services.authorization_service import require_permission_http
from backend.app.modules.inventory.schemas import (
    JobReservePartsIn,
    PurchaseOrderCreateIn,
    PurchaseOrderLineReceiveIn,
    StockItemCreateIn,
    StockItemOut,
    StockLocationOut,
    StockReservationOut,
    StockTransferCreateIn,
    VanLocationCreateIn,
)
from backend.app.modules.auth.models import User
from backend.app.modules.inventory.service import (
    approve_and_ship_stock_transfer,
    approve_purchase_order,
    create_purchase_order,
    create_stock_item,
    create_stock_transfer,
    create_van_location,
    list_locations,
    search_stock_items_for_engineer,
    list_reservations_for_job_quote,
    list_stock_items,
    low_stock_items,
    material_shortage_preview_for_quote,
    receive_purchase_order_line,
    receive_stock_transfer,
    release_reservation_by_id,
    reserve_parts_for_job,
    suggest_purchase_requests_for_low_stock,
    unreconciled_parts_usage_lines,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/items", response_model=StockItemOut, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(
    payload: StockItemCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> StockItemOut:
    return create_stock_item(db, payload=payload)


@router.get("/items", response_model=list[StockItemOut])
def list_items_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[StockItemOut]:
    return list_stock_items(db, limit=limit, offset=offset)


@router.get("/engineer/items/search", response_model=list[StockItemOut])
def engineer_search_items_endpoint(
    q: str | None = Query(default=None, description="SKU or name contains"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Engineer")),
) -> list[StockItemOut]:
    return search_stock_items_for_engineer(db, query=q, limit=limit)


@router.get("/locations", response_model=list[StockLocationOut])
def list_locations_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[StockLocationOut]:
    return list_locations(db)


@router.post("/locations/van", response_model=StockLocationOut, status_code=status.HTTP_201_CREATED)
def create_van_location_endpoint(
    payload: VanLocationCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> StockLocationOut:
    return create_van_location(
        db,
        code=payload.code,
        name=payload.name,
        engineer_user_id=payload.engineer_user_id,
    )


@router.get("/quotes/{quote_id}/material-shortage-preview")
def material_shortage_preview_endpoint(
    quote_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[dict[str, Any]]:
    try:
        return material_shortage_preview_for_quote(db, quote_id=quote_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/reservations", response_model=list[StockReservationOut])
def list_reservations_endpoint(
    quote_id: str | None = Query(default=None),
    job_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[StockReservationOut]:
    if not quote_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quote_id is required")
    return list_reservations_for_job_quote(db, quote_id=quote_id, job_id=job_id)


@router.post("/reservations/{reservation_id}/release", status_code=status.HTTP_200_OK)
def release_reservation_endpoint(
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    try:
        release_reservation_by_id(db, reservation_id=reservation_id, performed_by_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"status": "released"}


@router.post("/jobs/{job_id}/reserve-parts", status_code=status.HTTP_201_CREATED)
def reserve_parts_for_job_endpoint(
    job_id: str,
    payload: JobReservePartsIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    try:
        rid = reserve_parts_for_job(
            db,
            job_id=job_id,
            sku=payload.sku,
            quantity=payload.quantity,
            location_id=payload.location_id,
            performed_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"reservation_id": rid}


@router.get("/dashboard/low-stock")
def low_stock_dashboard_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[dict[str, Any]]:
    return low_stock_items(db)


@router.get("/dashboard/unreconciled-parts-usage")
def unreconciled_parts_dashboard_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[dict[str, Any]]:
    lines = unreconciled_parts_usage_lines(db)
    return [
        {
            "id": ln.id,
            "job_id": ln.job_id,
            "stock_item_id": ln.stock_item_id,
            "location_id": ln.location_id,
            "quantity": ln.quantity,
            "match_status": ln.match_status,
            "note": ln.note,
            "created_at": ln.created_at.isoformat(),
        }
        for ln in lines
    ]


@router.post("/purchase-requests/suggest-from-low-stock")
def suggest_purchase_requests_endpoint(
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, list[str]]:
    ids = suggest_purchase_requests_for_low_stock(db)
    return {"created_request_ids": ids}


@router.post("/transfers", status_code=status.HTTP_201_CREATED)
def create_transfer_endpoint(
    payload: StockTransferCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    lines = [(ln.sku, ln.quantity) for ln in payload.lines]
    try:
        t = create_stock_transfer(
            db,
            from_location_id=payload.from_location_id,
            to_location_id=payload.to_location_id,
            lines=lines,
            requested_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"transfer_id": t.id, "status": t.status}


@router.post("/transfers/{transfer_id}/ship", status_code=status.HTTP_200_OK)
def ship_transfer_endpoint(
    transfer_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    try:
        t = approve_and_ship_stock_transfer(db, transfer_id=transfer_id, approved_by_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"transfer_id": t.id, "status": t.status}


@router.post("/transfers/{transfer_id}/receive", status_code=status.HTTP_200_OK)
def receive_transfer_endpoint(
    transfer_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher")),
) -> dict[str, str]:
    try:
        t = receive_stock_transfer(db, transfer_id=transfer_id, performed_by_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"transfer_id": t.id, "status": t.status}


@router.post("/purchase-orders", status_code=status.HTTP_201_CREATED)
def create_po_endpoint(
    payload: PurchaseOrderCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    require_permission_http(current_user, CAN_CREATE_PURCHASE_ORDER, db=db)
    lines = [(ln.sku, ln.quantity, ln.unit_cost) for ln in payload.lines]
    try:
        po = create_purchase_order(
            db,
            supplier_name=payload.supplier_name,
            lines=lines,
            created_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"purchase_order_id": po.id, "status": po.status}


@router.post("/purchase-orders/{purchase_order_id}/approve", status_code=status.HTTP_200_OK)
def approve_po_endpoint(
    purchase_order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Finance", "Ops_Manager")),
) -> dict[str, str]:
    require_permission_http(current_user, CAN_APPROVE_PURCHASE_ORDER, db=db)
    try:
        po = approve_purchase_order(
            db, purchase_order_id=purchase_order_id, approved_by_user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"purchase_order_id": po.id, "status": po.status}


@router.post("/purchase-orders/lines/{line_id}/receive", status_code=status.HTTP_200_OK)
def receive_po_line_endpoint(
    line_id: str,
    payload: PurchaseOrderLineReceiveIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("Admin", "Dispatcher", "Finance", "Ops_Manager")),
) -> dict[str, Any]:
    try:
        line = receive_purchase_order_line(
            db,
            line_id=line_id,
            quantity=payload.quantity,
            to_location_id=payload.to_location_id,
            performed_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {
        "line_id": line.id,
        "quantity_received": line.quantity_received,
        "quantity_ordered": line.quantity_ordered,
    }
