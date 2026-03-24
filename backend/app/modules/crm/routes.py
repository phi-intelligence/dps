from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.db.session import get_db
from backend.app.modules.crm.schemas import (
    ConvertLeadOut,
    CustomerCreateIn,
    CustomerOut,
    CustomerPatchIn,
    LeadCreateIn,
    LeadOut,
)
from backend.app.modules.crm.service import convert_lead_to_customer, create_lead, list_leads, patch_customer


router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead_endpoint(
    lead_in: LeadCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> LeadOut:
    return create_lead(db, lead_in=lead_in)


@router.get("/leads", response_model=list[LeadOut])
def list_leads_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[LeadOut]:
    return list_leads(db, limit=limit, offset=offset)


@router.post("/leads/{lead_id}/convert", response_model=ConvertLeadOut)
def convert_lead_endpoint(
    lead_id: str,
    customer_in: CustomerCreateIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> ConvertLeadOut:
    try:
        lead, customer = convert_lead_to_customer(db, lead_id=lead_id, customer_in=customer_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ConvertLeadOut(lead=lead, customer=customer)


@router.get("/customers", response_model=list[CustomerOut])
def list_customers_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> list[CustomerOut]:
    # Minimal: listing customers isn't required for the first flow, but it's useful for testing.
    from backend.app.modules.crm.models import Customer

    return db.query(Customer).order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def patch_customer_endpoint(
    customer_id: str,
    body: CustomerPatchIn,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> CustomerOut:
    try:
        row = patch_customer(db, customer_id=customer_id, patch=body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return CustomerOut.model_validate(row)

