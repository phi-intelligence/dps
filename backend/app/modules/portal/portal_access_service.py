from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.assets.models import Asset
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer
from backend.app.modules.dispatch.models import Job
from backend.app.modules.portal.models import PortalSiteAccess
from backend.app.services import portal_customer_scope_service as customer_scope


def portal_restricted_site_ids(db: Session, *, customer_id: str) -> list[str] | None:
    """
    None = no site restriction (all jobs for customer).
    If any portal_site_access rows exist, only jobs at those sites are visible (FM/commercial scoping).
    """
    rows = db.query(PortalSiteAccess).filter(PortalSiteAccess.customer_id == customer_id).all()
    if not rows:
        return None
    return [r.site_id for r in rows]


def portal_jobs_base_query(db: Session, *, customer: Customer):
    q = db.query(Job).filter(Job.customer_id == customer.id)
    site_ids = portal_restricted_site_ids(db, customer_id=customer.id)
    if site_ids is not None:
        q = q.filter(Job.site_id.in_(site_ids))
    return q


def portal_job_ids(db: Session, *, customer: Customer) -> set[str]:
    return {j.id for j in portal_jobs_base_query(db, customer=customer).all()}


def can_customer_access_job(db: Session, *, customer: Customer | None, job_id: str) -> bool:
    if not customer:
        return False
    job = db.get(Job, job_id)
    if not job or job.customer_id != customer.id:
        return False
    site_ids = portal_restricted_site_ids(db, customer_id=customer.id)
    if site_ids is None:
        return True
    return job.site_id is None or job.site_id in site_ids


def list_portal_sites_for_customer(db: Session, *, customer: Customer):
    from backend.app.modules.sites.models import Site

    q = db.query(Site).filter(Site.customer_id == customer.id, Site.active.is_(True))
    site_ids = portal_restricted_site_ids(db, customer_id=customer.id)
    if site_ids is not None:
        q = q.filter(Site.id.in_(site_ids))
    return q.order_by(Site.name.asc()).all()


def can_customer_access_site(
    db: Session, *, customer: Customer, site_id: str, portal_login_email: str | None = None
) -> bool:
    from backend.app.modules.sites.models import Site

    site = db.get(Site, site_id)
    if not site or site.customer_id != customer.id:
        return False
    em = (portal_login_email or customer.email or "").strip().lower()
    if em and not customer_scope.customer_portal_site_allowed(
        db, customer=customer, portal_login_email=em, site_id=site_id
    ):
        return False
    allowed = portal_restricted_site_ids(db, customer_id=customer.id)
    if allowed is None:
        return True
    return site_id in allowed


def can_customer_access_contract(
    db: Session, *, customer: Customer, contract_id: str, portal_login_email: str | None = None
) -> bool:
    c = db.get(Contract, contract_id)
    if not c or c.customer_id != customer.id:
        return False
    em = (portal_login_email or customer.email or "").strip().lower()
    if em and customer_scope.customer_portal_group_scope_active(
        db, customer_id=customer.id, portal_login_email=em
    ):
        if not customer_scope.customer_portal_contract_allowed(
            db, customer=customer, portal_login_email=em, contract_id=contract_id
        ):
            return False
    site_ids = portal_restricted_site_ids(db, customer_id=customer.id)
    if site_ids is None:
        return True
    if c.site_id is None:
        return True
    return c.site_id in site_ids


def can_customer_access_asset(db: Session, *, customer: Customer, asset_id: str) -> bool:
    asset = db.get(Asset, asset_id)
    if not asset or asset.customer_id != customer.id:
        return False
    if not asset.site_id:
        return True
    return can_customer_access_site(db, customer=customer, site_id=asset.site_id)
