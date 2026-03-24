"""
Contract version timeline and transactional amendment activation with versioning.

Manual PATCH updates (`apply_manual_contract_update_with_versioning`) share the same
`ContractVersion` timeline as amendment activations: monotonic `version_number`, a single
open row per contract (`effective_to` null), `source_amendment_id` set only for
`amendment_activation`, and `manual_update` rows for direct edits when tracked fields change.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.modules.automation.models import InternalFollowUpTask
from backend.app.modules.contracts.amendment_models import ContractAmendment
from backend.app.modules.contracts.contract_version_models import ContractActivationRun, ContractVersion
from backend.app.modules.contracts.models import Contract
from backend.app.modules.contracts.review_models import ContractCommercialActionLog
from backend.app.modules.contracts.schemas import ContractPatchIn
from backend.app.services import contract_diff_service as cds
from backend.app.core.config import settings
from backend.app.services.acceptance_policy_service import (
    AcceptancePolicyActivationBlocked,
    blockers_for_activation,
)
from backend.app.services import contract_activation_confirmation_service as acconf


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def contract_state_snapshot(c: Contract) -> dict[str, Any]:
    return {
        "contract_id": c.id,
        "contract_code": c.contract_code,
        "contract_value": c.contract_value,
        "renewal_status": c.renewal_status,
        "renewal_decision": c.renewal_decision,
        "renewal_review_due_at": str(c.renewal_review_due_at) if c.renewal_review_due_at else None,
        "term_end_at": str(c.term_end_at) if c.term_end_at else None,
        "renewal_review_date": str(c.renewal_review_date) if c.renewal_review_date else None,
        "repricing_required": c.repricing_required,
        "account_attention_level": c.account_attention_level,
        "churn_risk_level": c.churn_risk_level,
        "snapshot_at": utc_now().isoformat(),
    }


def next_version_number(db: Session, *, contract_id: str) -> int:
    m = db.query(func.max(ContractVersion.version_number)).filter(ContractVersion.contract_id == contract_id).scalar()
    return int(m or 0) + 1


def get_open_version(db: Session, *, contract_id: str) -> ContractVersion | None:
    return (
        db.query(ContractVersion)
        .filter(ContractVersion.contract_id == contract_id, ContractVersion.effective_to.is_(None))
        .order_by(ContractVersion.version_number.desc())
        .first()
    )


def list_versions_for_contract(
    db: Session, *, contract_id: str, limit: int = 100, offset: int = 0
) -> list[ContractVersion]:
    return (
        db.query(ContractVersion)
        .filter(ContractVersion.contract_id == contract_id)
        .order_by(ContractVersion.version_number.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_version(db: Session, *, version_id: str) -> ContractVersion | None:
    return db.get(ContractVersion, version_id)


def serialize_contract_version(v: ContractVersion, *, include_snapshot: bool = True) -> dict[str, Any]:
    """Build API dict with parsed change summary and optional full snapshot (detail vs list)."""
    p = _loads(v.change_summary_json)
    human = p.get("human_readable_summary") if isinstance(p, dict) else None
    snap: Any = _loads(v.snapshot_json) if include_snapshot else None
    change_summary_out: dict[str, Any] | None = None
    if isinstance(p, dict):
        change_summary_out = dict(p)
        ch = p.get("changes")
        if isinstance(ch, list):
            change_summary_out["changes"] = cds.enrich_changes_for_api([x for x in ch if isinstance(x, dict)])
    return {
        "id": v.id,
        "contract_id": v.contract_id,
        "version_number": v.version_number,
        "source_amendment_id": v.source_amendment_id,
        "version_type": v.version_type,
        "effective_from": v.effective_from,
        "effective_to": v.effective_to,
        "created_at": v.created_at,
        "created_by_user_id": v.created_by_user_id,
        "contract_value": v.contract_value,
        "renewal_status": v.renewal_status,
        "renewal_decision": v.renewal_decision,
        "repricing_required": v.repricing_required,
        "account_attention_level": v.account_attention_level,
        "churn_risk_level": v.churn_risk_level,
        "notes": v.notes,
        "is_active": v.effective_to is None,
        "change_summary": change_summary_out,
        "human_readable_summary": human,
        "snapshot_json": snap if isinstance(snap, dict) else None,
    }


def _next_attempt_number(db: Session, *, amendment_id: str) -> int:
    m = (
        db.query(func.max(ContractActivationRun.attempt_number))
        .filter(ContractActivationRun.amendment_id == amendment_id)
        .scalar()
    )
    return int(m or 0) + 1


def _log_commercial(
    db: Session,
    *,
    contract_id: str,
    review_id: str | None,
    action_type: str,
    summary: str,
    performed_by_user_id: str,
    amendment_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    p = payload or {}
    if amendment_id:
        p["amendment_id"] = amendment_id
    db.add(
        ContractCommercialActionLog(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            review_id=review_id,
            action_type=action_type,
            action_summary=summary,
            performed_by_user_id=performed_by_user_id,
            performed_at=utc_now(),
            payload_json=_dumps(p) if p else None,
        )
    )


def _create_follow_up_for_activation_failure(
    db: Session,
    *,
    amendment: ContractAmendment,
    run: ContractActivationRun,
    summary: str,
) -> None:
    db.add(
        InternalFollowUpTask(
            id=str(uuid.uuid4()),
            task_type="contract_activation_failed",
            title=f"Contract activation failed: {amendment.amendment_reference}",
            summary=summary[:2000],
            status="open",
            priority="high",
            related_entity_type="contract_amendment",
            related_entity_id=amendment.id,
            notes=_dumps({"activation_run_id": run.id, "contract_id": amendment.contract_id}),
        )
    )


def log_commercial_contract_action(
    db: Session,
    *,
    contract_id: str,
    action_type: str,
    summary: str,
    performed_by_user_id: str,
    review_id: str | None = None,
    amendment_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Public wrapper for commercial / audit log rows (manual updates, activations, etc.)."""
    _log_commercial(
        db,
        contract_id=contract_id,
        review_id=review_id,
        action_type=action_type,
        summary=summary,
        performed_by_user_id=performed_by_user_id,
        amendment_id=amendment_id,
        payload=payload,
    )


def execute_amendment_activation(
    db: Session,
    *,
    amendment_id: str,
    actor_user_id: str,
    run_type: str = "manual",
    idempotency_key: str | None = None,
    commit: bool = True,
) -> tuple[ContractAmendment, ContractActivationRun]:
    """
    Idempotent activation: creates ContractActivationRun, applies contract changes,
    creates ContractVersion(s), updates amendment. Single transaction.
    """
    now = utc_now()
    run = ContractActivationRun(
        id=str(uuid.uuid4()),
        amendment_id=amendment_id,
        contract_id="",  # filled after load
        run_type=run_type,
        status="started",
        started_at=now,
        triggered_by_user_id=actor_user_id if run_type == "manual" else actor_user_id,
        attempt_number=_next_attempt_number(db, amendment_id=amendment_id),
        idempotency_key=idempotency_key,
    )

    try:
        a = db.get(ContractAmendment, amendment_id)
        if not a:
            raise ValueError("Amendment not found")

        run.contract_id = a.contract_id
        db.add(run)
        db.flush()

        if run_type == "scheduled":
            _log_commercial(
                db,
                contract_id=a.contract_id,
                review_id=a.source_review_id,
                action_type="activation_scheduled",
                summary=f"Scheduled activation run started for amendment {a.amendment_reference}",
                performed_by_user_id=actor_user_id,
                amendment_id=a.id,
                payload={"activation_run_id": run.id},
            )

        # Idempotent: already activated
        if a.status == "activated":
            run.status = "skipped"
            run.completed_at = utc_now()
            run.result_summary = "Amendment already activated; no duplicate mutation."
            if commit:
                db.commit()
                db.refresh(a)
                db.refresh(run)
            return a, run

        if a.status not in ("approved", "scheduled"):
            raise ValueError(
                f"Cannot activate amendment in status {a.status}; must be approved or scheduled"
            )
        if a.approval_required and not a.approved_at:
            raise ValueError("Amendment requires approval before activation")

        eff = _ensure_utc(a.effective_date)
        if eff and eff > now:
            raise ValueError(
                "Effective date is in the future; activation not permitted until effective date"
            )

        c = db.get(Contract, a.contract_id)
        if not c:
            raise ValueError("Contract not found")

        act_blocks = blockers_for_activation(db, amendment=a)
        if act_blocks:
            run.status = "failed"
            run.completed_at = utc_now()
            run.result_summary = "Blocked by acceptance policy"
            run.error_json = _dumps({"acceptance_policy": act_blocks})
            db.flush()
            _log_commercial(
                db,
                contract_id=a.contract_id,
                review_id=a.source_review_id,
                action_type="proposal_acceptance_policy_blocked_activation",
                summary=f"Activation blocked by acceptance policy: {act_blocks}",
                performed_by_user_id=actor_user_id,
                amendment_id=a.id,
                payload={"activation_run_id": run.id, "reasons": act_blocks},
            )
            if commit:
                db.commit()
                db.refresh(run)
            raise AcceptancePolicyActivationBlocked(
                f"Activation blocked by acceptance policy: {act_blocks}"
            )

        prior_snapshot = _loads(a.prior_contract_snapshot_json) or {}
        activation_ts = now

        # Close any open version window (or create retroactive initial if none)
        open_v = get_open_version(db, contract_id=c.id)
        if open_v is None:
            vn = next_version_number(db, contract_id=c.id)
            initial_snap = contract_state_snapshot(c)
            db.add(
                ContractVersion(
                    id=str(uuid.uuid4()),
                    contract_id=c.id,
                    version_number=vn,
                    source_amendment_id=None,
                    version_type="initial",
                    effective_from=c.created_at if c.created_at else activation_ts,
                    effective_to=activation_ts,
                    created_by_user_id=actor_user_id,
                    contract_value=initial_snap.get("contract_value"),
                    renewal_status=initial_snap.get("renewal_status"),
                    renewal_decision=initial_snap.get("renewal_decision"),
                    repricing_required=initial_snap.get("repricing_required"),
                    account_attention_level=initial_snap.get("account_attention_level"),
                    churn_risk_level=initial_snap.get("churn_risk_level"),
                    snapshot_json=_dumps(initial_snap),
                    change_summary_json=_dumps({"reason": "baseline_before_amendment_activation"}),
                    notes="Auto-created baseline version before first tracked activation.",
                )
            )
            db.flush()
        else:
            open_v.effective_to = activation_ts
            db.flush()

        # Apply mutation to contract
        if a.proposed_contract_value is not None:
            c.contract_value = a.proposed_contract_value
        if a.amendment_type == "repricing":
            c.repricing_required = False
            if c.renewal_status in ("repricing_review", "in_review"):
                c.renewal_status = "renewed"

        resulting_snap = contract_state_snapshot(c)
        resulting = dict(prior_snapshot)
        resulting.update(resulting_snap)
        resulting["amendment_id"] = a.id
        resulting["activated_at"] = activation_ts.isoformat()

        vn_new = next_version_number(db, contract_id=c.id)
        change_summary = {
            "source": "amendment_activation",
            "amendment_reference": a.amendment_reference,
            "prior_contract_value": a.current_contract_value,
            "new_contract_value": a.proposed_contract_value,
        }
        new_version = ContractVersion(
            id=str(uuid.uuid4()),
            contract_id=c.id,
            version_number=vn_new,
            source_amendment_id=a.id,
            version_type="amendment_activation",
            effective_from=activation_ts,
            effective_to=None,
            created_by_user_id=actor_user_id,
            contract_value=c.contract_value,
            renewal_status=c.renewal_status,
            renewal_decision=c.renewal_decision,
            repricing_required=c.repricing_required,
            account_attention_level=c.account_attention_level,
            churn_risk_level=c.churn_risk_level,
            snapshot_json=_dumps(resulting_snap),
            change_summary_json=_dumps(change_summary),
            notes=None,
        )
        db.add(new_version)
        db.flush()

        a.resulting_contract_snapshot_json = _dumps(resulting)
        a.status = "activated"
        a.activated_at = activation_ts
        a.activated_by_user_id = actor_user_id
        a.resulting_contract_version_id = new_version.id

        run.status = "succeeded"
        run.completed_at = utc_now()
        run.result_summary = f"Activated; contract version {new_version.version_number} created."

        log_actor = actor_user_id
        _log_commercial(
            db,
            contract_id=c.id,
            review_id=a.source_review_id,
            action_type="amendment_activated",
            summary=f"Amendment {a.amendment_reference} activated; contract version {new_version.version_number}",
            performed_by_user_id=log_actor,
            amendment_id=a.id,
            payload={
                "contract_version_id": new_version.id,
                "version_number": new_version.version_number,
                "prior_value": a.current_contract_value,
                "new_value": a.proposed_contract_value,
                "activation_run_id": run.id,
            },
        )
        _log_commercial(
            db,
            contract_id=c.id,
            review_id=a.source_review_id,
            action_type="activation_succeeded",
            summary=f"Activation run {run.id} succeeded for amendment {a.amendment_reference}",
            performed_by_user_id=log_actor,
            amendment_id=a.id,
            payload={"activation_run_id": run.id, "contract_version_id": new_version.id},
        )

        if settings.AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE:
            try:
                acconf.create_activation_confirmation_from_amendment(
                    db, amendment_id=a.id, actor_user_id=log_actor, commit=False
                )
            except Exception as ex:
                _log_commercial(
                    db,
                    contract_id=c.id,
                    review_id=a.source_review_id,
                    action_type="activation_confirmation_auto_create_failed",
                    summary=f"Auto-create activation confirmation failed: {str(ex)[:200]}",
                    performed_by_user_id=log_actor,
                    amendment_id=a.id,
                    payload={
                        "activation_run_id": run.id,
                        "error": str(ex)[:500],
                    },
                )

        if commit:
            db.commit()
            db.refresh(a)
            db.refresh(run)
            db.refresh(new_version)
        else:
            db.flush()

        return a, run

    except AcceptancePolicyActivationBlocked as e:
        raise ValueError(str(e)) from e

    except Exception as e:
        db.rollback()
        try:
            a2 = db.get(ContractAmendment, amendment_id)
            if a2:
                run2 = ContractActivationRun(
                    id=str(uuid.uuid4()),
                    amendment_id=amendment_id,
                    contract_id=a2.contract_id,
                    run_type=run_type,
                    status="failed",
                    started_at=now,
                    completed_at=utc_now(),
                    triggered_by_user_id=actor_user_id,
                    attempt_number=_next_attempt_number(db, amendment_id=amendment_id),
                    idempotency_key=idempotency_key,
                    result_summary=str(e)[:2000],
                    error_json=_dumps({"error": str(e), "type": type(e).__name__}),
                )
                db.add(run2)
                db.flush()
                _log_commercial(
                    db,
                    contract_id=a2.contract_id,
                    review_id=a2.source_review_id,
                    action_type="activation_failed",
                    summary=f"Activation failed for amendment {a2.amendment_reference}: {e}",
                    performed_by_user_id=actor_user_id,
                    amendment_id=amendment_id,
                    payload={"activation_run_id": run2.id, "error": str(e)},
                )
                _create_follow_up_for_activation_failure(
                    db, amendment=a2, run=run2, summary=str(e)
                )
                if commit:
                    db.commit()
                    db.refresh(run2)
        except Exception:
            db.rollback()
        raise


def apply_manual_contract_update_with_versioning(
    db: Session,
    *,
    contract_id: str,
    payload: ContractPatchIn,
    actor_user_id: str,
    commit: bool = True,
) -> tuple[Contract, dict[str, Any]]:
    """
    Apply ContractPatchIn to a live contract. When tracked commercial/operational fields change,
    closes the active ContractVersion window and appends version_type=manual_update.

    Precedence / coexistence: same timeline as amendment_activation; source_amendment_id is null.

    Permission checks belong at the HTTP layer; this function assumes the caller is authorized.

    Returns (contract, metadata) where metadata includes version_created, contract_version_id, etc.
    """
    raw = payload.model_dump(exclude_unset=True)
    manual_reason = raw.pop("manual_update_reason", None)

    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")

    if not raw:
        meta: dict[str, Any] = {
            "version_created": False,
            "contract_version_id": None,
            "version_number": None,
            "noop": True,
        }
        return c, meta

    before_snap = cds.contract_snapshot_for_diff(c)
    sim_after = cds.merge_patch_into_snapshot(before_snap, raw)
    diff_preview = cds.diff_contract_snapshots(before_snap, sim_after)

    if not diff_preview["has_meaningful_changes"]:
        log_commercial_contract_action(
            db,
            contract_id=c.id,
            action_type="contract_manual_update_noop",
            summary="Manual contract PATCH applied no tracked field changes; version not created.",
            performed_by_user_id=actor_user_id,
            payload={
                "attempted_fields": list(raw.keys()),
                "manual_update_reason": manual_reason,
            },
        )
        for k, v in raw.items():
            setattr(c, k, v)
        if commit:
            db.commit()
            db.refresh(c)
        else:
            db.flush()
        return c, {
            "version_created": False,
            "contract_version_id": None,
            "version_number": None,
            "noop": True,
        }

    now = utc_now()
    open_v = get_open_version(db, contract_id=c.id)
    if open_v is None:
        vn0 = next_version_number(db, contract_id=c.id)
        db.add(
            ContractVersion(
                id=str(uuid.uuid4()),
                contract_id=c.id,
                version_number=vn0,
                source_amendment_id=None,
                version_type="initial",
                effective_from=c.created_at if c.created_at else now,
                effective_to=now,
                created_by_user_id=actor_user_id,
                contract_value=before_snap.get("contract_value"),
                renewal_status=before_snap.get("renewal_status"),
                renewal_decision=before_snap.get("renewal_decision"),
                repricing_required=before_snap.get("repricing_required"),
                account_attention_level=before_snap.get("account_attention_level"),
                churn_risk_level=before_snap.get("churn_risk_level"),
                snapshot_json=_dumps(before_snap),
                change_summary_json=_dumps({"reason": "baseline_before_manual_update"}),
                notes="Auto-created baseline before first manual versioned update.",
            )
        )
        db.flush()
    else:
        open_v.effective_to = now
        db.flush()

    prior_value = c.contract_value
    for k, v in raw.items():
        setattr(c, k, v)
    db.flush()

    after_snap = cds.contract_snapshot_for_diff(c)
    diff_final = cds.diff_contract_snapshots(before_snap, after_snap)
    vn_new = next_version_number(db, contract_id=c.id)
    summary_obj = cds.build_change_summary_json(
        source="manual_update",
        diff=diff_final,
        actor_user_id=actor_user_id,
        manual_update_reason=manual_reason,
        prior_contract_value=prior_value,
        new_contract_value=c.contract_value,
    )
    new_version = ContractVersion(
        id=str(uuid.uuid4()),
        contract_id=c.id,
        version_number=vn_new,
        source_amendment_id=None,
        version_type="manual_update",
        effective_from=now,
        effective_to=None,
        created_by_user_id=actor_user_id,
        contract_value=c.contract_value,
        renewal_status=c.renewal_status,
        renewal_decision=c.renewal_decision,
        repricing_required=c.repricing_required,
        account_attention_level=c.account_attention_level,
        churn_risk_level=c.churn_risk_level,
        snapshot_json=_dumps(after_snap),
        change_summary_json=_dumps(summary_obj),
        notes=manual_reason,
    )
    db.add(new_version)
    db.flush()

    log_commercial_contract_action(
        db,
        contract_id=c.id,
        action_type="contract_manual_update_version_created",
        summary=f"Manual update; contract version {vn_new}: {summary_obj['human_readable_summary'][:500]}",
        performed_by_user_id=actor_user_id,
        payload={
            "contract_version_id": new_version.id,
            "version_number": vn_new,
            "changed_fields": diff_final["changed_fields"],
            "manual_update_reason": manual_reason,
        },
    )

    if commit:
        db.commit()
        db.refresh(c)
        db.refresh(new_version)
    else:
        db.flush()

    return c, {
        "version_created": True,
        "contract_version_id": new_version.id,
        "version_number": vn_new,
        "noop": False,
    }


def dry_run_activation_preview(
    db: Session,
    *,
    amendment_id: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Describe whether activation would succeed; no mutations."""
    now = now or utc_now()
    a = db.get(ContractAmendment, amendment_id)
    if not a:
        return {"would_activate": False, "reason": "amendment_not_found"}
    if a.status == "activated":
        return {"would_activate": False, "reason": "already_activated", "amendment_id": amendment_id}
    if a.status not in ("approved", "scheduled"):
        return {"would_activate": False, "reason": f"invalid_status:{a.status}"}
    if a.approval_required and not a.approved_at:
        return {"would_activate": False, "reason": "approval_required"}
    eff = _ensure_utc(a.effective_date)
    if eff and eff > now:
        return {"would_activate": False, "reason": "effective_date_in_future", "effective_date": str(eff)}
    return {
        "would_activate": True,
        "amendment_id": amendment_id,
        "contract_id": a.contract_id,
        "effective_date": str(a.effective_date) if a.effective_date else None,
    }
