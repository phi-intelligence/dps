from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class CustomerCreateIn(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    parent_customer_id: str | None = None


class CustomerOut(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    parent_customer_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerPatchIn(BaseModel):
    """§5.12 — link a customer record under a parent org (optional)."""

    parent_customer_id: str | None = None


class LeadCreateIn(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    property_type: str | None = None
    preferred_time_slots: str | None = None
    issue_description: str | None = None


class LeadOut(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    property_type: str | None = None
    preferred_time_slots: str | None = None
    issue_description: str | None = None
    status: str
    created_at: datetime
    converted_customer_id: str | None = None

    class Config:
        from_attributes = True


class ConvertLeadOut(BaseModel):
    lead: LeadOut
    customer: CustomerOut


class CustomerCommunicationPreferenceCreateIn(BaseModel):
    channel: str = "email"
    enabled: bool = True
    contact_reference: str | None = None
    preferred: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone_name: str | None = None
    notes: str | None = None


class CustomerCommunicationPreferencePatchIn(BaseModel):
    enabled: bool | None = None
    contact_reference: str | None = None
    preferred: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone_name: str | None = None
    notes: str | None = None


class CustomerCommunicationPreferenceOut(BaseModel):
    id: str
    customer_id: str
    channel: str
    enabled: bool
    contact_reference: str | None
    preferred: bool
    quiet_hours_start: str | None
    quiet_hours_end: str | None
    timezone_name: str | None
    notes: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


