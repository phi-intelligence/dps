"""
Configurable acceptance policy for repricing amendments and contract activation.

Policy is env-driven (PHI_DPS_ACCEPTANCE_POLICY_MODE) — explicit and centralized.
"""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
from backend.app.modules.contracts.review_models import ContractRepricingProposal


class AcceptancePolicyActivationBlocked(ValueError):
    """Activation was blocked by acceptance policy after persisting audit/run state."""


def acceptance_policy_mode() -> str:
    raw = (os.getenv("PHI_DPS_ACCEPTANCE_POLICY_MODE", "warn_only") or "warn_only").strip().lower()
    allowed = {
        "warn_only",
        "require_formal_acceptance_for_amendment",
        "require_formal_acceptance_for_activation",
        "require_provider_esign_for_activation",
        "require_provider_esign_for_amendment_and_activation",
    }
    return raw if raw in allowed else "warn_only"


def acceptance_policy_matrix() -> list[dict[str, Any]]:
    """
    Static review matrix: what each PHI_DPS_ACCEPTANCE_POLICY_MODE means for amendment vs activation.
    Used by dashboards and API consumers; keep in sync with blockers_for_*.
    """
    return [
        {
            "mode": "warn_only",
            "label": "Warn only",
            "blocks_amendment_on": [],
            "blocks_activation_on": [],
            "customer_evidence": (
                "Portal (or captured) customer response is enough to proceed; formal acceptance and "
                "provider e-sign are optional unless you adopt them operationally."
            ),
            "notes": "Dashboards may show non-blocking hints when formal or provider e-sign is absent.",
        },
        {
            "mode": "require_formal_acceptance_for_amendment",
            "label": "Formal acceptance before amendment",
            "blocks_amendment_on": [
                "Missing any completed ProposalAcceptanceRecord (portal, secure link, or acknowledgement flow)."
            ],
            "blocks_activation_on": [],
            "customer_evidence": (
                "Amendment creation requires a completed in-product formal acceptance record on the proposal."
            ),
            "notes": "Activation is not additionally gated by formal acceptance in this mode.",
        },
        {
            "mode": "require_formal_acceptance_for_activation",
            "label": "Formal acceptance before activation",
            "blocks_amendment_on": [],
            "blocks_activation_on": [
                "Missing any completed ProposalAcceptanceRecord for the source proposal before activation runs."
            ],
            "customer_evidence": "Amendment can be drafted, but contract version cutover requires formal acceptance completed.",
            "notes": "Pairs with operational review before go-live.",
        },
        {
            "mode": "require_provider_esign_for_activation",
            "label": "Provider e-sign before activation",
            "blocks_amendment_on": [],
            "blocks_activation_on": [
                "Missing completed third-party e-sign (provider_esign evidence) on the source proposal."
            ],
            "customer_evidence": "Legal e-sign completion must be ingested via the configured provider before activation.",
            "notes": "Use when activation must not run without an external signature artifact.",
        },
        {
            "mode": "require_provider_esign_for_amendment_and_activation",
            "label": "Provider e-sign before amendment and activation",
            "blocks_amendment_on": [
                "Missing completed third-party e-sign (provider_esign evidence) on the proposal."
            ],
            "blocks_activation_on": [
                "Missing completed third-party e-sign (provider_esign evidence) on the source proposal."
            ],
            "customer_evidence": "Both amendment creation and activation require provider e-sign completion.",
            "notes": "Strictest commercial/legal posture in the built-in policy set.",
        },
    ]


def humanize_policy_blocker(code: str) -> str:
    """Turn machine blocker tokens into short operator-facing sentences."""
    c = (code or "").strip()
    if not c:
        return ""
    if "acceptance_policy_blocked_amendment: require_formal_acceptance_for_amendment" in c:
        return (
            "Amendment creation is blocked: policy requires a completed formal acceptance record "
            "(in-product acceptance session), not only a portal 'accepted' response."
        )
    if "acceptance_policy_blocked_amendment: require_provider_esign_for_amendment_and_activation" in c:
        return (
            "Amendment creation is blocked: policy requires a completed legal e-sign from the configured provider."
        )
    if "acceptance_policy_blocked_activation: require_formal_acceptance_for_activation" in c:
        return (
            "Activation is blocked: policy requires a completed formal acceptance record on the source proposal."
        )
    if "acceptance_policy_blocked_activation: require_provider_esign_for_activation" in c:
        return "Activation is blocked: policy requires completed provider e-sign on the source proposal."
    if "acceptance_policy_blocked_activation: require_provider_esign_for_amendment_and_activation" in c:
        return "Activation is blocked: policy requires completed provider e-sign on the source proposal."
    return c


def requirement_bullets_for_mode(mode: str) -> tuple[list[str], list[str]]:
    """(requirements_to_create_amendment, requirements_to_run_activation) as human lines."""
    m = (mode or "warn_only").strip().lower()
    simple = "Customer must have accepted the proposal (response captured as accepted)."
    formal = "A completed formal acceptance record must exist on the proposal (in-product flow)."
    esign = "A completed provider e-sign acceptance record must exist on the proposal."
    if m == "warn_only":
        return ([simple], [simple, "Amendment approved (if required) and effective date due or past."])
    if m == "require_formal_acceptance_for_amendment":
        return ([simple, formal], [simple, "Amendment approved (if required) and effective date due or past."])
    if m == "require_formal_acceptance_for_activation":
        return ([simple], [simple, formal, "Amendment approved (if required) and effective date due or past."])
    if m == "require_provider_esign_for_activation":
        return ([simple], [simple, esign, "Amendment approved (if required) and effective date due or past."])
    if m == "require_provider_esign_for_amendment_and_activation":
        return ([simple, esign], [simple, esign, "Amendment approved (if required) and effective date due or past."])
    return ([simple], [simple, "Amendment approved (if required) and effective date due or past."])


def has_completed_any_acceptance_record(db: Session, *, proposal_id: str) -> bool:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_status == "completed",
        )
        .first()
        is not None
    )


def has_completed_provider_esign(db: Session, *, proposal_id: str) -> bool:
    return (
        db.query(ProposalAcceptanceRecord)
        .filter(
            ProposalAcceptanceRecord.proposal_id == proposal_id,
            ProposalAcceptanceRecord.acceptance_status == "completed",
            ProposalAcceptanceRecord.acceptance_evidence_type == "provider_esign",
            ProposalAcceptanceRecord.provider_status == "signed",
        )
        .first()
        is not None
    )


def policy_warnings_for_proposal_readiness(db: Session, *, proposal_id: str) -> list[str]:
    """Non-blocking hints for readiness dashboards (warn_only and others)."""
    out: list[str] = []
    mode = acceptance_policy_mode()
    p = db.get(ContractRepricingProposal, proposal_id)
    if not p:
        return out
    if mode != "warn_only":
        return out
    if p.customer_response_status == "accepted" and not has_completed_any_acceptance_record(db, proposal_id=proposal_id):
        out.append("acceptance_policy_hint: legacy_or_informal_acceptance_only")
    if p.customer_response_status == "accepted" and not has_completed_provider_esign(db, proposal_id=proposal_id):
        out.append("acceptance_policy_hint: no_provider_esign_completed")
    return out


def blockers_for_amendment_creation(db: Session, *, proposal_id: str) -> list[str]:
    mode = acceptance_policy_mode()
    if mode == "warn_only":
        return []
    block: list[str] = []
    if mode in ("require_formal_acceptance_for_amendment",):
        if not has_completed_any_acceptance_record(db, proposal_id=proposal_id):
            block.append("acceptance_policy_blocked_amendment: require_formal_acceptance_for_amendment")
    if mode == "require_provider_esign_for_amendment_and_activation":
        if not has_completed_provider_esign(db, proposal_id=proposal_id):
            block.append("acceptance_policy_blocked_amendment: require_provider_esign_for_amendment_and_activation")
    return block


def blockers_for_activation(db: Session, *, amendment: ContractAmendment) -> list[str]:
    mode = acceptance_policy_mode()
    if mode == "warn_only":
        return []
    pid = amendment.source_proposal_id
    if not pid:
        return []
    block: list[str] = []
    if mode in (
        "require_formal_acceptance_for_activation",
        "require_formal_acceptance_for_amendment",
    ):
        # Activation-time formal requirement (explicit mode for activation path only + shared strictness)
        if mode == "require_formal_acceptance_for_activation":
            if not has_completed_any_acceptance_record(db, proposal_id=pid):
                block.append("acceptance_policy_blocked_activation: require_formal_acceptance_for_activation")
    if mode == "require_provider_esign_for_activation":
        if not has_completed_provider_esign(db, proposal_id=pid):
            block.append("acceptance_policy_blocked_activation: require_provider_esign_for_activation")
    if mode == "require_provider_esign_for_amendment_and_activation":
        if not has_completed_provider_esign(db, proposal_id=pid):
            block.append("acceptance_policy_blocked_activation: require_provider_esign_for_amendment_and_activation")
    return block


def evaluate_policy_blockers_summary(db: Session, *, limit_proposals: int = 200) -> dict[str, Any]:
    """Dashboard: proposals/amendments currently blocked by acceptance policy."""
    mode = acceptance_policy_mode()
    proposals = (
        db.query(ContractRepricingProposal)
        .filter(ContractRepricingProposal.customer_response_status == "accepted")
        .order_by(ContractRepricingProposal.updated_at.desc())
        .limit(limit_proposals)
        .all()
    )
    amend_blocked: list[dict[str, Any]] = []
    for p in proposals:
        reasons = blockers_for_amendment_creation(db, proposal_id=p.id)
        if reasons:
            amend_blocked.append(
                {
                    "proposal_id": p.id,
                    "proposal_reference": p.proposal_reference,
                    "contract_id": p.contract_id,
                    "reasons": reasons,
                    "reason_messages": [humanize_policy_blocker(r) for r in reasons],
                }
            )

    act_blocked: list[dict[str, Any]] = []
    amendments = (
        db.query(ContractAmendment)
        .filter(ContractAmendment.status.in_(("approved", "scheduled")))
        .order_by(ContractAmendment.created_at.desc())
        .limit(limit_proposals)
        .all()
    )
    for a in amendments:
        reasons = blockers_for_activation(db, amendment=a)
        if reasons:
            act_blocked.append(
                {
                    "amendment_id": a.id,
                    "amendment_reference": a.amendment_reference,
                    "contract_id": a.contract_id,
                    "source_proposal_id": a.source_proposal_id,
                    "reasons": reasons,
                    "reason_messages": [humanize_policy_blocker(r) for r in reasons],
                }
            )

    am_req, act_req = requirement_bullets_for_mode(mode)

    return {
        "acceptance_policy_mode": mode,
        "policy_matrix": acceptance_policy_matrix(),
        "active_mode_explainer": next(
            (row for row in acceptance_policy_matrix() if row["mode"] == mode),
            {
                "mode": mode,
                "label": mode,
                "customer_evidence": "",
                "notes": "Unknown or legacy mode; server falls back to warn_only-style behavior.",
            },
        ),
        "requirements_for_amendment": am_req,
        "requirements_for_activation": act_req,
        "evidence_types_explainer": (
            "Simple response: portal (or API) has recorded customer_response_status (e.g. accepted). "
            "Formal acceptance: at least one ProposalAcceptanceRecord with acceptance_status=completed from an "
            "in-product acceptance flow. Provider e-sign: a completed record with acceptance_evidence_type=provider_esign "
            "and provider_status=signed."
        ),
        "config_env_var": "PHI_DPS_ACCEPTANCE_POLICY_MODE",
        "amendment_creation_blocked": amend_blocked,
        "activation_blocked": act_blocked,
        "counts": {
            "amendment_creation_blocked": len(amend_blocked),
            "activation_blocked": len(act_blocked),
        },
    }
