"""§5.1 commercial follow-up needs-action dashboard aggregation."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from backend.tests.test_contract_scheduled_activation_versions import (
    _admin_token,
    _auth,
    _released_proposal_no_response,
)


def test_dashboard_commercial_follow_up_needs_action_shape_and_esign_reason(client):
    admin = _admin_token(client)
    r0 = client.get("/contracts/dashboard/commercial-follow-up-needs-action", headers=_auth(admin))
    assert r0.status_code == 200, r0.text
    base = r0.json()
    assert set(base.keys()) >= {
        "generated_at",
        "thresholds",
        "proposals",
        "activation_confirmations",
        "draft_customer_comms",
    }
    assert base["thresholds"].get("esign_incomplete_days") == 5
    assert base["thresholds"].get("released_not_viewed_days") == 7
    assert base["thresholds"].get("viewed_not_acknowledged_days") == 7

    contract_id, proposal_id = _released_proposal_no_response(client, admin)
    from backend.app.db.session import SessionLocal
    from backend.app.modules.contracts.models import Contract
    from backend.app.modules.contracts.proposal_acceptance_models import ProposalAcceptanceRecord

    stale = datetime.now(timezone.utc) - timedelta(days=10)
    db = SessionLocal()
    try:
        c = db.get(Contract, contract_id)
        assert c is not None
        db.add(
            ProposalAcceptanceRecord(
                id=str(uuid.uuid4()),
                proposal_id=proposal_id,
                contract_id=contract_id,
                customer_id=c.customer_id,
                source_proposal_reference=None,
                acceptance_status="initiated",
                acceptance_type="provider_esign",
                acceptance_evidence_type="provider_esign",
                acceptance_channel="provider_esign",
                initiated_at=stale,
                created_by_user_id=None,
                provider_name="stub",
                provider_status="sent",
            )
        )
        db.commit()
    finally:
        db.close()

    r1 = client.get("/contracts/dashboard/commercial-follow-up-needs-action", headers=_auth(admin))
    assert r1.status_code == 200, r1.text
    props = r1.json()["proposals"]
    match = [x for x in props if x.get("proposal_id") == proposal_id]
    assert match, props
    assert match[0]["reason_code"] == "provider_esign_incomplete_stale"
    assert match[0].get("acceptance_record_id")
