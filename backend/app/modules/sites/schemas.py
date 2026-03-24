from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SiteCreateIn(BaseModel):
    customer_id: str
    site_code: str
    name: str
    address_line1: str
    address_line2: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    service_region: str | None = None
    access_notes: str | None = None
    billing_notes: str | None = None
    site_contacts_json: str = "[]"
    active: bool = True


class SitePatchIn(BaseModel):
    site_code: str | None = None
    name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postcode: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    service_region: str | None = None
    access_notes: str | None = None
    billing_notes: str | None = None
    site_contacts_json: str | None = None
    active: bool | None = None


class SiteOut(BaseModel):
    id: str
    customer_id: str
    site_code: str
    name: str
    address_line1: str
    address_line2: str | None
    city: str | None
    postcode: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    service_region: str | None
    access_notes: str | None
    billing_notes: str | None
    site_contacts_json: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
