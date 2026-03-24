from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.crm.models import Customer, Lead
from backend.app.modules.crm.schemas import CustomerCreateIn, CustomerPatchIn, LeadCreateIn


def create_lead(db: Session, *, lead_in: LeadCreateIn) -> Lead:
    lead = Lead(
        name=lead_in.name,
        email=lead_in.email,
        phone=lead_in.phone,
        property_type=lead_in.property_type,
        preferred_time_slots=lead_in.preferred_time_slots,
        issue_description=lead_in.issue_description,
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def list_leads(db: Session, *, limit: int = 50, offset: int = 0) -> list[Lead]:
    return db.query(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()


def convert_lead_to_customer(
    db: Session,
    *,
    lead_id: str,
    customer_in: CustomerCreateIn,
) -> tuple[Lead, Customer]:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise ValueError("Lead not found")
    if lead.converted_customer_id:
        raise ValueError("Lead already converted")

    # customers.email is UNIQUE, so if this lead converts to an email that already exists,
    # reuse the existing customer instead of creating a duplicate row.
    if customer_in.email:
        customer = db.query(Customer).filter(Customer.email == customer_in.email).one_or_none()
    else:
        customer = None

    if not customer:
        customer = Customer(
            name=customer_in.name,
            email=customer_in.email,
            phone=customer_in.phone,
            address=customer_in.address,
        )
        db.add(customer)
        db.flush()  # ensures customer.id exists before linking

    lead.converted_customer_id = customer.id
    lead.status = "converted"
    db.commit()
    db.refresh(lead)
    db.refresh(customer)
    return lead, customer


def patch_customer(db: Session, *, customer_id: str, patch: CustomerPatchIn) -> Customer:
    row = db.get(Customer, customer_id)
    if not row:
        raise ValueError("Customer not found")
    data = patch.model_dump(exclude_unset=True)
    if "parent_customer_id" in data:
        pid = data["parent_customer_id"]
        if pid is None or pid == "":
            row.parent_customer_id = None
        else:
            if pid == customer_id:
                raise ValueError("parent_customer_id cannot equal customer id")
            if not db.get(Customer, pid):
                raise ValueError("parent_customer_id not found")
            row.parent_customer_id = pid
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

