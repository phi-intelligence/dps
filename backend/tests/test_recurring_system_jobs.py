"""
Recurring system jobs: runner, scheduling, dry-run, idempotency, APIs, dashboards.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.tests.test_contract_scheduled_activation_versions import (
    _accepted_proposal,
    _admin_token,
    _auth,
    _released_proposal_no_response,
)


@pytest.fixture(autouse=True)
def _clear_recurring_job_runs():
    from backend.app.db.session import SessionLocal
    from backend.app.modules.system.recurring_system_job_models import RecurringSystemJobRun

    db = SessionLocal()
    try:
        db.query(RecurringSystemJobRun).delete()
        db.commit()
    finally:
        db.close()
    yield


def _jobs(client, admin: str) -> list[dict]:
    r = client.get("/system/jobs", headers=_auth(admin))
    assert r.status_code == 200, r.text
    return r.json()


def _freeze_schedules(client, admin: str, *, focus_key: str, focus_past: bool, focus_enabled: bool = True):
    """Push all jobs to far-future next_run; focus job gets past (or far) next_run and enabled flag."""
    far = (datetime.now(timezone.utc) + timedelta(days=400)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    for j in _jobs(client, admin):
        if j["job_key"] == focus_key:
            client.patch(
                f"/system/jobs/{j['id']}",
                headers=_auth(admin),
                json={
                    "enabled": focus_enabled,
                    "next_run_at": past if focus_past else far,
                },
            )
        else:
            client.patch(
                f"/system/jobs/{j['id']}",
                headers=_auth(admin),
                json={"enabled": True, "next_run_at": far},
            )


def _job_id_by_key(client, admin: str, job_key: str) -> str:
    for j in _jobs(client, admin):
        if j["job_key"] == job_key:
            return j["id"]
    raise AssertionError(f"job_key not found: {job_key}")


def test_due_scheduled_amendment_activation_creates_successful_run_record(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert cr.status_code == 201, cr.text
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    _freeze_schedules(
        client,
        admin,
        focus_key="scheduled_contract_amendment_activation",
        focus_past=True,
    )
    due = client.post("/system/jobs/run-due", headers=_auth(admin), json={"limit": 5})
    assert due.status_code == 200, due.text
    runs = due.json()
    assert len(runs) == 1
    assert runs[0]["job_key"] == "scheduled_contract_amendment_activation"
    assert runs[0]["status"] == "succeeded"
    assert runs[0]["dry_run"] is False

    c = client.get(f"/contracts/{contract_id}", headers=_auth(admin))
    assert c.json()["contract_value"] == 45000.0


def test_dry_run_scheduled_activation_reports_candidates_without_mutating(client):
    admin = _admin_token(client)
    _, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.contract_version_models import ContractActivationRun

    db = SessionLocal()
    try:
        before = db.query(ContractActivationRun).filter(ContractActivationRun.amendment_id == aid).count()
    finally:
        db.close()

    jid = _job_id_by_key(client, admin, "scheduled_contract_amendment_activation")
    run = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": True})
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "succeeded"
    assert body["dry_run"] is True
    rj = body.get("result_json") or {}
    assert rj.get("dry_run") is True
    assert rj.get("candidate_count", 0) >= 1

    db = SessionLocal()
    try:
        after = db.query(ContractActivationRun).filter(ContractActivationRun.amendment_id == aid).count()
    finally:
        db.close()
    assert after == before


def test_proposal_follow_up_scan_creates_deduped_outputs_only(client):
    admin = _admin_token(client)
    _, proposal_id = _accepted_proposal(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
    from backend.app.modules.contracts.review_models import ContractRepricingProposal
    from backend.app.services.contract_customer_communication_templates import COMMS_REPRICING_PROPOSAL_REMINDER

    stale = datetime.now(timezone.utc) - timedelta(days=14)
    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, proposal_id)
        assert p is not None
        p.customer_viewed_at = None
        p.customer_response_status = None
        p.released_to_customer_at = stale
        p.customer_release_status = "released"
        db.add(p)
        db.commit()
    finally:
        db.close()

    jid = _job_id_by_key(client, admin, "proposal_follow_up_scan")
    r1 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "succeeded"

    db = SessionLocal()
    try:
        n1 = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.source_entity_type == "repricing_proposal",
                ContractCustomerCommunication.source_entity_id == proposal_id,
                ContractCustomerCommunication.communication_type == COMMS_REPRICING_PROPOSAL_REMINDER,
            )
            .count()
        )
    finally:
        db.close()
    assert n1 == 1

    r2 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r2.status_code == 200, r2.text
    detail = (r2.json().get("result_json") or {}).get("details_sample") or []
    assert any(x.get("result") == "skipped_dup" for x in detail) or r2.json().get("skipped_count", 0) >= 1

    db = SessionLocal()
    try:
        n2 = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.source_entity_type == "repricing_proposal",
                ContractCustomerCommunication.source_entity_id == proposal_id,
                ContractCustomerCommunication.communication_type == COMMS_REPRICING_PROPOSAL_REMINDER,
            )
            .count()
        )
    finally:
        db.close()
    assert n2 == 1


def test_proposal_follow_up_scan_skips_reminder_when_recipient_suppressed(client):
    admin = _admin_token(client)
    _, proposal_id = _accepted_proposal(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.communication_provider_event_models import CommunicationRecipientSuppression
    from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.contracts.review_models import ContractRepricingProposal
    from backend.app.modules.crm.models import Customer
    from backend.app.services.contract_customer_communication_templates import COMMS_REPRICING_PROPOSAL_REMINDER

    stale = datetime.now(timezone.utc) - timedelta(days=14)
    db = SessionLocal()
    try:
        p = db.get(ContractRepricingProposal, proposal_id)
        assert p is not None
        ctr = db.get(Contract, p.contract_id)
        assert ctr is not None
        cust = db.get(Customer, ctr.customer_id)
        assert cust is not None
        cust.email = "suppress-me-followup@example.com"
        db.add(
            CommunicationRecipientSuppression(
                id=str(uuid.uuid4()),
                customer_id=cust.id,
                recipient_email_normalized="suppress-me-followup@example.com",
                kind="hard_bounce",
                active=True,
                requires_manual_review=False,
            )
        )
        p.customer_viewed_at = None
        p.customer_response_status = None
        p.released_to_customer_at = stale
        p.customer_release_status = "released"
        db.add(p)
        db.add(cust)
        db.commit()
    finally:
        db.close()

    jid = _job_id_by_key(client, admin, "proposal_follow_up_scan")
    r1 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r1.status_code == 200, r1.text
    body = r1.json()
    rj = body.get("result_json") or {}
    detail = rj.get("details_sample") or []
    assert any(x.get("result") == "skipped_suppressed" for x in detail) or (body.get("skipped_count") or 0) >= 1

    db = SessionLocal()
    try:
        n = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.source_entity_type == "repricing_proposal",
                ContractCustomerCommunication.source_entity_id == proposal_id,
                ContractCustomerCommunication.communication_type == COMMS_REPRICING_PROPOSAL_REMINDER,
            )
            .count()
        )
    finally:
        db.close()
    assert n == 0


def test_proposal_follow_up_scan_esign_reminder_deduped(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _released_proposal_no_response(client, admin)

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord
    from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
    from backend.app.services.contract_customer_communication_templates import COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER

    stale = datetime.now(timezone.utc) - timedelta(days=14)
    db = SessionLocal()
    try:
        c = db.get(Contract, contract_id)
        assert c is not None
        rec = ProposalAcceptanceRecord(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            contract_id=contract_id,
            customer_id=c.customer_id,
            source_proposal_reference="REF",
            acceptance_status="initiated",
            acceptance_type="provider_esign",
            acceptance_evidence_type="provider_esign",
            acceptance_channel="provider_esign",
            initiated_at=stale,
            created_by_user_id=None,
            provider_name="stub",
            provider_status="sent",
        )
        db.add(rec)
        db.commit()
        rec_id = rec.id
    finally:
        db.close()

    jid = _job_id_by_key(client, admin, "proposal_follow_up_scan")
    r1 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "succeeded"

    db = SessionLocal()
    try:
        n1 = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.source_entity_type == "proposal_acceptance",
                ContractCustomerCommunication.source_entity_id == rec_id,
                ContractCustomerCommunication.communication_type == COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
            )
            .count()
        )
    finally:
        db.close()
    assert n1 == 1

    r2 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r2.status_code == 200, r2.text
    r2_body = r2.json()
    detail = (r2_body.get("result_json") or {}).get("details_sample") or []
    assert any(x.get("action") == "esign_reminder" and x.get("result") == "skipped_dup" for x in detail) or (
        r2_body.get("skipped_count", 0) >= 1
    )

    db = SessionLocal()
    try:
        n2 = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.source_entity_type == "proposal_acceptance",
                ContractCustomerCommunication.source_entity_id == rec_id,
                ContractCustomerCommunication.communication_type == COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
            )
            .count()
        )
    finally:
        db.close()
    assert n2 == 1


def test_activation_confirmation_follow_up_scan_creates_safe_drafts_only(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})
    client.post(f"/contracts/amendments/{aid}/activate", headers=_auth(admin))

    ac = client.post(
        f"/contracts/amendments/{aid}/activation-confirmation",
        headers=_auth(admin),
        json={},
    )
    assert ac.status_code == 201, ac.text
    cid = ac.json()["id"]
    client.post(f"/contracts/activation-confirmations/{cid}/generate-pdf", headers=_auth(admin))
    client.post(f"/contracts/activation-confirmations/{cid}/mark-ready-for-customer", headers=_auth(admin))
    rel = client.post(
        f"/contracts/activation-confirmations/{cid}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    assert rel.status_code == 200, rel.text

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.activation_confirmation_models import ContractActivationConfirmation
    from backend.app.modules.contracts.contract_customer_communication_models import ContractCustomerCommunication
    from backend.app.services.contract_customer_communication_templates import COMMS_ACTIVATION_CONFIRMATION_REMINDER

    stale = datetime.now(timezone.utc) - timedelta(days=14)
    db = SessionLocal()
    try:
        row = db.get(ContractActivationConfirmation, cid)
        assert row is not None
        row.released_to_customer_at = stale
        row.customer_viewed_at = None
        row.status = "released"
        db.add(row)
        db.commit()
    finally:
        db.close()

    jid = _job_id_by_key(client, admin, "activation_confirmation_follow_up_scan")
    run = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "succeeded"

    db = SessionLocal()
    try:
        drafts = (
            db.query(ContractCustomerCommunication)
            .filter(
                ContractCustomerCommunication.contract_id == contract_id,
                ContractCustomerCommunication.source_entity_type == "activation_confirmation",
                ContractCustomerCommunication.source_entity_id == cid,
                ContractCustomerCommunication.communication_type == COMMS_ACTIVATION_CONFIRMATION_REMINDER,
                ContractCustomerCommunication.status == "draft",
            )
            .all()
        )
    finally:
        db.close()
    assert len(drafts) == 1


def test_repeated_recurring_activation_job_idempotent(client):
    admin = _admin_token(client)
    contract_id, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    jid = _job_id_by_key(client, admin, "scheduled_contract_amendment_activation")
    r1 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r1.status_code == 200, r1.text
    r2 = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert r2.status_code == 200, r2.text

    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.contract_version_models import ContractVersion

    db = SessionLocal()
    try:
        n = (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_type == "amendment_activation",
            )
            .count()
        )
    finally:
        db.close()
    assert n == 1


def test_failed_recurring_job_record_and_dashboard_visibility(client, monkeypatch):
    admin = _admin_token(client)
    _, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    def _boom(*_a, **_k):
        raise RuntimeError("forced recurring job failure")

    monkeypatch.setattr(
        "backend.app.services.recurring_job_runner_service.casc.run_due_amendment_activations",
        _boom,
    )

    jid = _job_id_by_key(client, admin, "scheduled_contract_amendment_activation")
    run = client.post(f"/system/jobs/{jid}/run", headers=_auth(admin), json={"dry_run": False})
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "failed"
    err = body.get("error_json") or {}
    assert "forced recurring job failure" in (err.get("message") or "")

    dash = client.get("/system/dashboard/job-failures", headers=_auth(admin))
    assert dash.status_code == 200, dash.text
    failed = dash.json().get("failed_runs") or []
    assert any(x.get("id") == body["id"] for x in failed)

    listed = client.get("/system/job-runs", headers=_auth(admin), params={"run_status": "failed"})
    assert listed.status_code == 200, listed.text
    assert any(x["id"] == body["id"] for x in listed.json())


def test_disabled_recurring_job_not_run_in_run_due(client):
    admin = _admin_token(client)
    _freeze_schedules(
        client,
        admin,
        focus_key="scheduled_contract_amendment_activation",
        focus_past=True,
        focus_enabled=False,
    )
    due = client.post("/system/jobs/run-due", headers=_auth(admin), json={})
    assert due.status_code == 200, due.text
    assert due.json() == []


def test_manual_and_scheduled_trigger_same_execution_path(client):
    admin = _admin_token(client)
    jid_act = _job_id_by_key(client, admin, "scheduled_contract_amendment_activation")
    client.patch(f"/system/jobs/{jid_act}", headers=_auth(admin), json={"enabled": True})

    _, proposal_id = _accepted_proposal(client, admin)
    cr = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    aid = cr.json()["id"]
    if cr.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{aid}/approve", headers=_auth(admin), json={})

    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.services import recurring_job_runner_service as rjr

    db = SessionLocal()
    try:
        uid = db.query(User).filter(User.email == "admin@example.com").one().id
        m = rjr.run_job(
            db,
            job_key="scheduled_contract_amendment_activation",
            dry_run=True,
            actor_user_id=uid,
            trigger_type="manual",
            advance_schedule=False,
            commit=True,
        )
        m_json = m.result_json
        s = rjr.run_job(
            db,
            job_key="scheduled_contract_amendment_activation",
            dry_run=True,
            actor_user_id=uid,
            trigger_type="scheduled",
            advance_schedule=False,
            commit=True,
        )
        s_json = s.result_json
        m_trig, s_trig = m.trigger_type, s.trigger_type
    finally:
        db.close()

    jm = json.loads(m_json) if m_json else {}
    js = json.loads(s_json) if s_json else {}
    assert jm.get("candidate_count") == js.get("candidate_count")
    assert jm.get("dry_run") is True and js.get("dry_run") is True
    assert m_trig == "manual"
    assert s_trig == "scheduled"
