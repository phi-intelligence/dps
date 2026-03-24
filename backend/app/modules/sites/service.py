from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.crm.models import Customer
from backend.app.modules.sites.models import Site
from backend.app.modules.sites.schemas import SiteCreateIn, SitePatchIn


def create_site(db: Session, *, payload: SiteCreateIn) -> Site:
    if not db.get(Customer, payload.customer_id):
        raise ValueError("Customer not found")
    site = Site(
        customer_id=payload.customer_id,
        site_code=payload.site_code.strip(),
        name=payload.name.strip(),
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        postcode=payload.postcode,
        country=payload.country,
        latitude=payload.latitude,
        longitude=payload.longitude,
        service_region=payload.service_region,
        access_notes=payload.access_notes,
        billing_notes=payload.billing_notes,
        site_contacts_json=payload.site_contacts_json or "[]",
        active=payload.active,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def list_sites(db: Session, *, customer_id: str | None = None, limit: int = 100, offset: int = 0) -> list[Site]:
    q = db.query(Site).order_by(Site.created_at.desc())
    if customer_id:
        q = q.filter(Site.customer_id == customer_id)
    return q.offset(offset).limit(limit).all()


def get_site(db: Session, *, site_id: str) -> Site | None:
    return db.get(Site, site_id)


def patch_site(db: Session, *, site_id: str, payload: SitePatchIn) -> Site:
    site = db.get(Site, site_id)
    if not site:
        raise ValueError("Site not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(site, k, v)
    db.commit()
    db.refresh(site)
    return site


def site_full_address(site: Site) -> str:
    parts = [site.address_line1]
    if site.address_line2:
        parts.append(site.address_line2)
    if site.city:
        parts.append(site.city)
    if site.postcode:
        parts.append(site.postcode)
    if site.country:
        parts.append(site.country)
    return ", ".join(parts)
