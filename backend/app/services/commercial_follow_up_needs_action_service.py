"""
Commercial "needs action now" aggregation for stalled customer workflows (§5.1).

Uses the same default thresholds as recurring_job_workflow_scans where applicable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
from backend.app.modules.contracts.review_models import ContractRepricingProposal
from backend.app.services.contract_customer_communication_service import OPEN_STATUSES
from backend.app.services.contract_customer_communication_templates import ALL_COMMUNICATION_TYPES
from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _days_between(now: datetime, then: datetime | None) -> int | None:
    t = _as_utc(then)
    if not t:
        return None
    return max(0, (now - t).days)


def _latest_inflight_esign(db: Session, *, proposal_id: str) -> ProposalAcceptanceRecord | None:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_type == "provider_esign",
            ProposalAcceptanceRecord.acceptance_status.notin_(("completed", "cancelled")),
            ProposalAcceptanceRecord.provider_status.in_(("sent", "viewed")),
        )
        .order_by(ProposalAcceptanceRecord.initiated_at.desc())
        .first()
    )


def dashboard_commercial_follow_up_needs_action(
    db: Session,
    *,
    limit_per_section: int = 150,
    released_no_view_days: int = 7,
    viewed_no_response_days: int = 7,
    esign_incomplete_days: int = 5,
    activation_released_not_viewed_days: int = 7,
    activation_viewed_not_acknowledged_days: int = 7,
) -> dict[str, Any]:
    now = utc_now()
    thresholds = {
        "released_no_view_days": released_no_view_days,
        "viewed_no_response_days": viewed_no_response_days,
        "esign_incomplete_days": esign_incomplete_days,
        # Same keys as `activation_confirmation_follow_up_scan` job payload_json:
        "released_not_viewed_days": activation_released_not_viewed_days,
        "viewed_not_acknowledged_days": activation_viewed_not_acknowledged_days,
        # Descriptive aliases (same values) for dashboards and older clients:
        "activation_released_not_viewed_days": activation_released_not_viewed_days,
        "activation_viewed_not_acknowledged_days": activation_viewed_not_acknowledged_days,
    }

    proposals_out: list[dict[str, Any]] = []
    scanned = (
        db.query(ContractRepricingProposal)
        .order_by(ContractRepricingProposal.updated_at.desc())
        .limit(800)
        .all()
    )
    for p in scanned:
        reason: str | None = None
        stale_days: int | None = None
        acceptance_record_id: str | None = None

        if p.customer_response_status in ("rejected", "counter_requested", "needs_follow_up"):
            reason = p.customer_response_status
            stale_days = _days_between(now, p.updated_at)
        elif not p.customer_response_status and (
            is_past_customer_expiry(p) or p.customer_release_status == "expired"
        ):
            reason = "expired_no_response"
            exp = p.customer_expiry_at or p.validity_end_date
            stale_days = _days_between(now, exp) if exp else None
        elif not p.customer_response_status and p.customer_release_status in ("released", "viewed"):
            rec = _latest_inflight_esign(db, proposal_id=p.id)
            if rec:
                ia = _as_utc(rec.initiated_at)
                if ia and (now - ia) >= timedelta(days=esign_incomplete_days):
                    reason = "provider_esign_incomplete_stale"
                    stale_days = (now - ia).days
                    acceptance_record_id = rec.id

        if not reason and (
            p.customer_release_status == "released"
            and p.customer_viewed_at is None
            and not p.customer_response_status
            and p.released_to_customer_at
        ):
            ra = _as_utc(p.released_to_customer_at)
            if ra and (now - ra).days >= released_no_view_days:
                reason = "released_not_viewed_stale"
                stale_days = (now - ra).days

        if not reason and p.customer_viewed_at and not p.customer_response_status:
            va = _as_utc(p.customer_viewed_at)
            if va and (now - va).days >= viewed_no_response_days:
                reason = "viewed_no_response_stale"
                stale_days = (now - va).days

        if reason:
            proposals_out.append(
                {
                    "proposal_id": p.id,
                    "contract_id": p.contract_id,
                    "proposal_reference": p.proposal_reference,
                    "reason_code": reason,
                    "stale_days": stale_days,
                    "acceptance_record_id": acceptance_record_id,
                }
            )
        if len(proposals_out) >= limit_per_section:
            break

    activation_out: list[dict[str, Any]] = []
    for conf in (
        db.query(ContractActivationConfirmation)
        .order_by(ContractActivationConfirmation.created_at.desc())
        .limit(800)
        .all()
    ):
        reason_a: str | None = None
        stale_a: int | None = None
        if conf.status == "released" and conf.customer_viewed_at is None and conf.released_to_customer_at:
            ra = _as_utc(conf.released_to_customer_at)
            if ra and (now - ra).days >= activation_released_not_viewed_days:
                reason_a = "activation_released_not_viewed_stale"
                stale_a = (now - ra).days
        elif conf.status == "viewed" and conf.customer_acknowledged_at is None and conf.customer_viewed_at:
            va = _as_utc(conf.customer_viewed_at)
            if va and (now - va).days >= activation_viewed_not_acknowledged_days:
                reason_a = "activation_viewed_not_acknowledged_stale"
                stale_a = (now - va).days
        if reason_a:
            activation_out.append(
                {
                    "confirmation_id": conf.id,
                    "contract_id": conf.contract_id,
                    "confirmation_reference": conf.confirmation_reference,
                    "reason_code": reason_a,
                    "stale_days": stale_a,
                }
            )
        if len(activation_out) >= limit_per_section:
            break

    comm_types = tuple(ALL_COMMUNICATION_TYPES)
    drafts_out: list[dict[str, Any]] = []
    for row in (
        db.query(ContractCustomerCommunication)
        .filter(
            ContractCustomerCommunication.status.in_(OPEN_STATUSES),
            ContractCustomerCommunication.communication_type.in_(comm_types),
        )
        .order_by(ContractCustomerCommunication.created_at.desc())
        .limit(limit_per_section)
        .all()
    ):
        drafts_out.append(
            {
                "communication_id": row.id,
                "contract_id": row.contract_id,
                "communication_type": row.communication_type,
                "status": row.status,
                "source_entity_type": row.source_entity_type,
                "source_entity_id": row.source_entity_id,
                "stale_days": _days_between(now, row.created_at),
            }
        )

    return {
        "generated_at": now.isoformat(),
        "thresholds": thresholds,
        "proposals": proposals_out,
        "activation_confirmations": activation_out,
        "draft_customer_comms": drafts_out,
    }
