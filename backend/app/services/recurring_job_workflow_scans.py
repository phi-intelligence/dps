"""
Safe recurring scans: draft communications + internal tasks only (no silent final actions).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
from backend.app.modules.contracts.review_models import ContractRepricingProposal
from backend.app.modules.crm.models import Customer
from backend.app.services import contract_customer_communication_service as ccc_svc
from backend.app.services.communication_recipient_suppression_service import is_outbound_blocked
from backend.app.services import contract_customer_communication_templates as tpl
from backend.app.services.contract_customer_communication_service import find_open_duplicate
from backend.app.services import low_risk_automation_service as lra
from backend.app.services.low_risk_automation_service import RECOMMENDATION_TYPE_DEFAULT_AUTOMATION
from backend.app.modules.ops.models import OperationalRecommendation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _loads_payload(s: str | None) -> dict[str, Any]:
    if not s:
        return {}
    try:
        o = json.loads(s)
        return o if isinstance(o, dict) else {}
    except json.JSONDecodeError:
        return {}


def _outbound_suppressed_for_contract(db: Session, *, contract_id: str) -> bool:
    """Skip drafting customer email reminders when CRM primary email is actively suppressed (§5.1)."""
    c = db.get(Contract, contract_id)
    if not c or not c.customer_id:
        return False
    cust = db.get(Customer, c.customer_id)
    email = (cust.email or "").strip() if cust else ""
    if not email:
        return False
    blocked, _ = is_outbound_blocked(db, customer_id=c.customer_id, recipient_email=email)
    return bool(blocked)


def run_proposal_follow_up_scan(
    db: Session,
    *,
    dry_run: bool,
    actor_user_id: str | None,
    payload_json: str | None,
) -> dict[str, Any]:
    cfg = _loads_payload(payload_json)
    released_no_view_days = int(cfg.get("released_no_view_days", 7))
    viewed_no_response_days = int(cfg.get("viewed_no_response_days", 7))
    esign_incomplete_days = int(cfg.get("esign_incomplete_days", 5))
    now = utc_now()

    created = skipped = failed = 0
    details: list[dict[str, Any]] = []

    proposals = db.query(ContractRepricingProposal).all()
    for p in proposals:
        try:
            # Provider e-sign in progress (sent/viewed) but stale — draft reminder per acceptance record
            if p.customer_release_status in ("released", "viewed") and not p.customer_response_status:
                rec = (
                    db.query(ProposalAcceptanceRecord)
                    .filter(
                        ProposalAcceptanceRecord.proposal_id == p.id,
                        ProposalAcceptanceRecord.acceptance_type == "provider_esign",
                        ProposalAcceptanceRecord.acceptance_status.notin_(("completed", "cancelled")),
                        ProposalAcceptanceRecord.provider_status.in_(("sent", "viewed")),
                    )
                    .order_by(ProposalAcceptanceRecord.initiated_at.desc())
                    .first()
                )
                if rec:
                    ia = _as_utc(rec.initiated_at)
                    if ia and (now - ia) >= timedelta(days=esign_incomplete_days):
                        dup = find_open_duplicate(
                            db,
                            contract_id=p.contract_id,
                            communication_type=tpl.COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
                            source_entity_type="proposal_acceptance",
                            source_entity_id=rec.id,
                        )
                        if dup:
                            skipped += 1
                            details.append(
                                {"proposal_id": p.id, "action": "esign_reminder", "result": "skipped_dup"}
                            )
                            continue
                        if _outbound_suppressed_for_contract(db, contract_id=p.contract_id):
                            skipped += 1
                            details.append(
                                {"proposal_id": p.id, "action": "esign_reminder", "result": "skipped_suppressed"}
                            )
                            continue
                        if dry_run:
                            created += 1
                            details.append(
                                {"proposal_id": p.id, "action": "esign_reminder", "result": "would_create"}
                            )
                        else:
                            ccc_svc.create_draft_for_repricing_proposal_esign_reminder(
                                db,
                                acceptance_record_id=rec.id,
                                actor_user_id=actor_user_id,
                                commit=False,
                            )
                            created += 1
                            details.append(
                                {"proposal_id": p.id, "action": "esign_reminder", "result": "created"}
                            )
                        continue

            # Reminder: released but never viewed, stale (suppress if customer already responded)
            if (
                p.customer_release_status == "released"
                and p.customer_viewed_at is None
                and p.released_to_customer_at
                and not p.customer_response_status
            ):
                ra = _as_utc(p.released_to_customer_at)
                if ra and (now - ra) >= timedelta(days=released_no_view_days):
                    dup = find_open_duplicate(
                        db,
                        contract_id=p.contract_id,
                        communication_type=tpl.COMMS_REPRICING_PROPOSAL_REMINDER,
                        source_entity_type="repricing_proposal",
                        source_entity_id=p.id,
                    )
                    if dup:
                        skipped += 1
                        details.append({"proposal_id": p.id, "action": "reminder", "result": "skipped_dup"})
                        continue
                    if _outbound_suppressed_for_contract(db, contract_id=p.contract_id):
                        skipped += 1
                        details.append({"proposal_id": p.id, "action": "reminder", "result": "skipped_suppressed"})
                        continue
                    if dry_run:
                        created += 1
                        details.append({"proposal_id": p.id, "action": "reminder", "result": "would_create"})
                    else:
                        ccc_svc.create_draft_for_repricing_proposal_reminder(
                            db, proposal_id=p.id, actor_user_id=actor_user_id, commit=False
                        )
                        created += 1
                        details.append({"proposal_id": p.id, "action": "reminder", "result": "created"})
                    continue

            # Viewed, no response (internal task)
            if p.customer_viewed_at and not p.customer_response_status:
                va = _as_utc(p.customer_viewed_at)
                if va and (now - va) >= timedelta(days=viewed_no_response_days):
                    if dry_run:
                        existing = lra._open_proposal_follow_up_by_dedupe_key(
                            db, proposal_id=p.id, dedupe_key="viewed_no_response_follow_up"
                        )
                        if existing:
                            skipped += 1
                            details.append({"proposal_id": p.id, "action": "viewed_task", "result": "skipped_dup"})
                        else:
                            created += 1
                            details.append({"proposal_id": p.id, "action": "viewed_task", "result": "would_create"})
                    else:
                        run = lra.maybe_create_proposal_viewed_follow_up(
                            db,
                            proposal_id=p.id,
                            actor_user_id=actor_user_id or "",
                            viewed_no_response_days=0,
                            kind="viewed_no_response_follow_up",
                            commit=False,
                        )
                        if not run:
                            skipped += 1
                        elif run.status == "skipped":
                            skipped += 1
                            details.append({"proposal_id": p.id, "action": "viewed_task", "result": "skipped"})
                        else:
                            created += 1
                            details.append({"proposal_id": p.id, "action": "viewed_task", "result": "created"})
                    continue

            # Expired / past customer expiry without response
            from backend.app.services.customer_repricing_proposal_service import is_past_customer_expiry

            if not p.customer_response_status and (
                is_past_customer_expiry(p) or p.customer_release_status == "expired"
            ):
                if dry_run:
                    existing = lra._open_proposal_follow_up_by_dedupe_key(
                        db, proposal_id=p.id, dedupe_key="expired_no_response_follow_up"
                    )
                    if existing:
                        skipped += 1
                        details.append({"proposal_id": p.id, "action": "expired_task", "result": "skipped_dup"})
                    else:
                        created += 1
                        details.append({"proposal_id": p.id, "action": "expired_task", "result": "would_create"})
                else:
                    run = lra.maybe_create_proposal_viewed_follow_up(
                        db,
                        proposal_id=p.id,
                        actor_user_id=actor_user_id or "",
                        kind="expired_no_response_follow_up",
                        commit=False,
                    )
                    if not run:
                        skipped += 1
                    elif run.status == "skipped":
                        skipped += 1
                    else:
                        created += 1
                        details.append({"proposal_id": p.id, "action": "expired_task", "result": "created"})
        except Exception as e:
            failed += 1
            details.append({"proposal_id": p.id, "error": str(e)[:500]})

    if not dry_run:
        db.commit()

    return {
        "dry_run": dry_run,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "details_sample": details[:50],
    }


def run_activation_confirmation_follow_up_scan(
    db: Session,
    *,
    dry_run: bool,
    actor_user_id: str | None,
    payload_json: str | None,
) -> dict[str, Any]:
    cfg = _loads_payload(payload_json)
    released_stale_days = int(cfg.get("released_not_viewed_days", 7))
    viewed_stale_days = int(cfg.get("viewed_not_acknowledged_days", 7))
    now = utc_now()

    created = skipped = failed = 0
    details: list[dict[str, Any]] = []

    for conf in db.query(ContractActivationConfirmation).all():
        try:
            if conf.status == "released" and conf.customer_viewed_at is None and conf.released_to_customer_at:
                ra = _as_utc(conf.released_to_customer_at)
                if ra and (now - ra) >= timedelta(days=released_stale_days):
                    dup = find_open_duplicate(
                        db,
                        contract_id=conf.contract_id,
                        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_REMINDER,
                        source_entity_type="activation_confirmation",
                        source_entity_id=conf.id,
                    )
                    if dup:
                        skipped += 1
                        continue
                    if _outbound_suppressed_for_contract(db, contract_id=conf.contract_id):
                        skipped += 1
                        details.append(
                            {"confirmation_id": conf.id, "action": "reminder", "result": "skipped_suppressed"}
                        )
                        continue
                    if dry_run:
                        created += 1
                        details.append({"confirmation_id": conf.id, "action": "reminder", "result": "would_create"})
                    else:
                        ccc_svc.create_draft_for_activation_confirmation_reminder(
                            db, confirmation_id=conf.id, actor_user_id=actor_user_id, commit=False
                        )
                        created += 1
                    continue

            if conf.status == "viewed" and conf.customer_acknowledged_at is None and conf.customer_viewed_at:
                va = _as_utc(conf.customer_viewed_at)
                if va and (now - va) >= timedelta(days=viewed_stale_days):
                    dup = find_open_duplicate(
                        db,
                        contract_id=conf.contract_id,
                        communication_type=tpl.COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP,
                        source_entity_type="activation_confirmation",
                        source_entity_id=conf.id,
                    )
                    if dup:
                        skipped += 1
                        continue
                    if _outbound_suppressed_for_contract(db, contract_id=conf.contract_id):
                        skipped += 1
                        details.append(
                            {"confirmation_id": conf.id, "action": "ack_follow_up", "result": "skipped_suppressed"}
                        )
                        continue
                    if dry_run:
                        created += 1
                        details.append({"confirmation_id": conf.id, "action": "ack_follow_up", "result": "would_create"})
                    else:
                        ccc_svc.create_draft_for_activation_acknowledgement_follow_up(
                            db, confirmation_id=conf.id, actor_user_id=actor_user_id, commit=False
                        )
                        created += 1
        except Exception as e:
            failed += 1
            details.append({"confirmation_id": conf.id, "error": str(e)[:500]})

    if not dry_run:
        db.commit()

    return {
        "dry_run": dry_run,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "details_sample": details[:50],
    }


def run_low_risk_automation_scan(
    db: Session,
    *,
    dry_run: bool,
    actor_user_id: str,
    payload_json: str | None,
) -> dict[str, Any]:
    cfg = _loads_payload(payload_json)
    limit = int(cfg.get("recommendation_limit", 40))
    created = skipped = failed = 0
    q = (
        db.query(OperationalRecommendation)
        .filter(OperationalRecommendation.status == "open")
        .order_by(OperationalRecommendation.created_at.asc())
        .limit(limit)
    )
    for rec in q.all():
        if rec.recommendation_type not in RECOMMENDATION_TYPE_DEFAULT_AUTOMATION:
            skipped += 1
            continue
        try:
            if dry_run:
                # Would automation run skip? Delegate to run with commit=False then rollback entire txn at runner.
                lra.run_automation_for_recommendation(
                    db,
                    recommendation_id=rec.id,
                    actor_user_id=actor_user_id,
                    commit=False,
                )
                created += 1
            else:
                lra.run_automation_for_recommendation(
                    db,
                    recommendation_id=rec.id,
                    actor_user_id=actor_user_id,
                    commit=False,
                )
                created += 1
        except Exception:
            failed += 1
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return {"dry_run": dry_run, "processed": created + skipped + failed, "created_runs": created, "skipped": skipped, "failed": failed}


def run_equipment_vehicle_attention_scan(
    db: Session,
    *,
    dry_run: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    from backend.app.services.equipment_recommendation_rules import register_equipment_recommendations
    from backend.app.services.recommendation_engine import auto_resolve_stale_open
    from backend.app.services.vehicle_inspection_recommendation_rules import (
        register_vehicle_inspection_recommendations,
    )

    now = now or utc_now()
    active_keys: set[str] = set()
    register_equipment_recommendations(db, active_keys, now=now)
    register_vehicle_inspection_recommendations(db, active_keys, now=now)
    keys = len(active_keys)
    if dry_run:
        db.rollback()
        return {"dry_run": True, "keys_active": keys, "auto_resolved": 0}
    resolved = auto_resolve_stale_open(db, active_keys=active_keys)
    db.commit()
    return {"dry_run": False, "keys_active": keys, "auto_resolved": resolved}
