"""Phase 2 (finance + contract readability) and Phase 3 (health + ops diagnostics) smoke tests."""
from __future__ import annotations

from backend.tests.test_contract_amendment_activation import (
    _accepted_proposal,
    _admin_token,
    _auth,
)


def test_health_and_ready_endpoints(client):
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json().get("status") == "ok"
    r2 = client.get("/health/ready")
    assert r2.status_code == 200
    assert r2.json().get("database") == "ok"


def test_system_operations_diagnostics_endpoint(client):
    admin = _admin_token(client)
    r = client.get("/system/dashboard/operations-diagnostics", headers=_auth(admin))
    assert r.status_code == 200, r.text
    j = r.json()
    assert "recurring_job_failures" in j
    assert "contract_activation_failures" in j
    assert "customer_communication_delivery_failures" in j
    assert "communication_provider_webhook_failures" in j
    assert "rollout_notification_delivery_failures" in j
    assert "rollout_webhook_invalid_signatures" in j
    assert "counts" in j
    assert "communication_provider_webhook_failures_shown" in j["counts"]


def test_system_integration_status_and_blockers_overview(client):
    admin = _admin_token(client)
    ri = client.get("/system/integration-status", headers=_auth(admin))
    assert ri.status_code == 200, ri.text
    si = ri.json()
    assert si.get("database_reachable") is True
    assert "communication" in si and "esign" in si
    assert "ai" in si and "assisted_drafting_ready" in si["ai"]
    assert "labour" in si and si["labour"].get("holiday_calendar_feed_import_enabled") is True
    rb = client.get("/system/dashboard/operations-blockers-overview", headers=_auth(admin))
    assert rb.status_code == 200, rb.text
    assert "commercial_follow_up" in rb.json()
    assert "finance_status_counts" in rb.json()


def test_finance_queue_dashboard_and_finance_review(client):
    admin = _admin_token(client)
    r0 = client.get("/invoicing/dashboard/finance-queue", headers=_auth(admin))
    assert r0.status_code == 200, r0.text
    body = r0.json()
    assert "status_counts" in body
    assert "export_column_definitions" in body
    cn = body.get("credit_notes_and_adjustments", {})
    assert cn.get("status") == "external_system"
    assert cn.get("in_app_supported") is False
    rec = client.get("/invoicing/dashboard/reconciliation-summary", headers=_auth(admin))
    assert rec.status_code == 200, rec.text
    assert "counts" in rec.json() and "open_invoice_age_buckets" in rec.json()
    ex = client.get("/invoicing/invoices/export-rows?limit=10", headers=_auth(admin))
    assert ex.status_code == 200, ex.text
    assert isinstance(ex.json(), list)


def test_contract_version_activity_and_readable_change(client):
    admin = _admin_token(client)
    contract_id, proposal_id, _ = _accepted_proposal(client, admin)
    create = client.post(
        f"/contracts/repricing-proposals/{proposal_id}/create-amendment",
        headers=_auth(admin),
        json={},
    )
    assert create.status_code == 201, create.text
    amend_id = create.json()["id"]
    if create.json()["status"] == "pending_approval":
        client.post(f"/contracts/amendments/{amend_id}/approve", headers=_auth(admin), json={})
    assert client.post(f"/contracts/amendments/{amend_id}/activate", headers=_auth(admin)).status_code == 200

    act = client.get("/contracts/dashboard/recent-contract-version-activity", headers=_auth(admin))
    assert act.status_code == 200, act.text
    rows = act.json().get("rows") or []
    ours = [r for r in rows if r.get("contract_id") == contract_id]
    assert ours, rows
    vid = ours[0]["version_id"]
    cid = ours[0]["contract_id"]

    vh = client.get("/contracts/dashboard/version-history-summary?limit=20", headers=_auth(admin))
    assert vh.status_code == 200, vh.text
    vh_rows = vh.json().get("recent_versions") or []
    vh_ours = [r for r in vh_rows if r.get("contract_id") == contract_id]
    assert vh_ours, vh_rows
    assert "contract_code" in vh_ours[0]
    rd = client.get(
        f"/contracts/{cid}/versions/{vid}/readable-change",
        headers=_auth(admin),
    )
    assert rd.status_code == 200, rd.text
    rj = rd.json()
    assert "headline" in rj
    assert "by_category" in rj
    # Amendment-driven versions may store narrative summary without per-field `changes[]`;
    # field labels are covered in test_8_version_detail_includes_human_usable_diff_context (manual PATCH).
    for ch in rj.get("changes") or []:
        assert ch.get("field_label")

    life = client.get("/contracts/dashboard/activation-customer-lifecycle", headers=_auth(admin))
    assert life.status_code == 200, life.text
    lj = life.json()
    assert "by_status" in lj and "follow_up_counts" in lj

    av = client.get(f"/contracts/{cid}/versions/active-summary", headers=_auth(admin))
    assert av.status_code == 200, av.text
    assert av.json().get("contract_id") == cid
    assert "open_version" in av.json()
