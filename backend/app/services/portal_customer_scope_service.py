"""
Customer portal visibility via CustomerAccessGroup + CustomerGroupEntityAccess.

When a portal login email is an active member of a group that has active entity scope rows,
visibility is restricted to the union of those entities (plus legacy PortalSiteAccess rules).

If the member's groups have no entity scope rows, behaviour matches legacy portal only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.modules.auth.org_access_models import (
    CustomerAccessGroup,
    CustomerAccessGroupMembership,
    CustomerGroupEntityAccess,
)
from backend.app.modules.contracts.models import Contract
from backend.app.modules.crm.models import Customer


def _member_group_ids_for_portal(
    db: Session, *, customer_id: str, portal_login_email: str
) -> list[str]:
    em = portal_login_email.strip().lower()
    rows = (
        db.query(CustomerAccessGroupMembership.customer_access_group_id)
        .join(
            CustomerAccessGroup,
            CustomerAccessGroup.id == CustomerAccessGroupMembership.customer_access_group_id,
        )
        .filter(
            CustomerAccessGroup.customer_id == customer_id,
            CustomerAccessGroup.active.is_(True),
            CustomerAccessGroupMembership.portal_login_email == em,
            CustomerAccessGroupMembership.active.is_(True),
        )
        .all()
    )
    return [r[0] for r in rows]


def customer_portal_group_scope_active(
    db: Session, *, customer_id: str, portal_login_email: str
) -> bool:
    gids = _member_group_ids_for_portal(db, customer_id=customer_id, portal_login_email=portal_login_email)
    if not gids:
        return False
    hit = (
        db.query(CustomerGroupEntityAccess.id)
        .filter(
            CustomerGroupEntityAccess.customer_access_group_id.in_(gids),
            CustomerGroupEntityAccess.active.is_(True),
        )
        .first()
    )
    return hit is not None


def _collect_customer_portal_scope_sets(
    db: Session, *, customer_id: str, portal_login_email: str
) -> tuple[set[str], set[str], set[str], set[str]]:
    """contract_ids, site_ids, proposal_ids, activation_confirmation_ids"""
    gids = _member_group_ids_for_portal(db, customer_id=customer_id, portal_login_email=portal_login_email)
    contract_ids: set[str] = set()
    site_ids: set[str] = set()
    proposal_ids: set[str] = set()
    ac_ids: set[str] = set()
    if not gids:
        return contract_ids, site_ids, proposal_ids, ac_ids
    rows = (
        db.query(CustomerGroupEntityAccess.entity_type, CustomerGroupEntityAccess.entity_id)
        .filter(
            CustomerGroupEntityAccess.customer_access_group_id.in_(gids),
            CustomerGroupEntityAccess.active.is_(True),
        )
        .all()
    )
    for et, eid in rows:
        if et == "contract":
            contract_ids.add(eid)
        elif et == "site":
            site_ids.add(eid)
        elif et == "proposal":
            proposal_ids.add(eid)
        elif et == "activation_confirmation":
            ac_ids.add(eid)
    return contract_ids, site_ids, proposal_ids, ac_ids


def customer_portal_site_allowed(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    site_id: str,
) -> bool:
    if not customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=portal_login_email):
        return True
    cids, sids, _, _ = _collect_customer_portal_scope_sets(
        db, customer_id=customer.id, portal_login_email=portal_login_email
    )
    if site_id in sids:
        return True
    for cid in cids:
        c = db.get(Contract, cid)
        if c and c.customer_id == customer.id and c.site_id == site_id:
            return True
    return False


def customer_portal_contract_allowed(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    contract_id: str,
) -> bool:
    if not customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=portal_login_email):
        return True
    c = db.get(Contract, contract_id)
    if not c or c.customer_id != customer.id:
        return False
    cids, sids, pids, _ = _collect_customer_portal_scope_sets(
        db, customer_id=customer.id, portal_login_email=portal_login_email
    )
    if contract_id in cids:
        return True
    if c.site_id and c.site_id in sids:
        return True
    if pids:
        from backend.app.modules.contracts.review_models import ContractRepricingProposal

        hit = (
            db.query(ContractRepricingProposal.id)
            .filter(
                ContractRepricingProposal.contract_id == contract_id,
                ContractRepricingProposal.id.in_(pids),
            )
            .limit(1)
            .first()
        )
        if hit:
            return True
    return False


def customer_portal_proposal_allowed(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    proposal_id: str,
    contract_id: str,
) -> bool:
    if not customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=portal_login_email):
        return True
    _, _, pids, _ = _collect_customer_portal_scope_sets(
        db, customer_id=customer.id, portal_login_email=portal_login_email
    )
    if proposal_id in pids:
        return True
    return customer_portal_contract_allowed(
        db, customer=customer, portal_login_email=portal_login_email, contract_id=contract_id
    )


def customer_portal_activation_confirmation_allowed(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    confirmation_id: str,
    contract_id: str,
) -> bool:
    if not customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=portal_login_email):
        return True
    _, _, _, aids = _collect_customer_portal_scope_sets(
        db, customer_id=customer.id, portal_login_email=portal_login_email
    )
    if confirmation_id in aids:
        return True
    return customer_portal_contract_allowed(
        db, customer=customer, portal_login_email=portal_login_email, contract_id=contract_id
    )


def filter_released_proposals_for_customer_portal(
    db: Session,
    *,
    customer: Customer,
    portal_login_email: str,
    contract_id: str,
    proposals: list,
) -> list:
    if not customer_portal_group_scope_active(db, customer_id=customer.id, portal_login_email=portal_login_email):
        return proposals
    cids, sids, pids, _ = _collect_customer_portal_scope_sets(
        db, customer_id=customer.id, portal_login_email=portal_login_email
    )
    if contract_id in cids:
        return proposals
    c = db.get(Contract, contract_id)
    if c and c.site_id and c.site_id in sids:
        return proposals
    return [p for p in proposals if p.id in pids]
