import hashlib
import hmac
import json


def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sign(secret: str, body: str) -> str:
    return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


def test_phase6_webhook_signature_and_idempotency(client):
    admin_token = _login(client, username="admin@example.com", password="admin")

    # Create at least one delivery path by forcing an alert from health evaluation.
    policy = client.post(
        "/rollout/policy",
        headers=_auth_headers(admin_token),
        json={
            "low_rating_threshold": 50,
            "error_events_threshold": 1,
            "evaluation_window_hours": 24,
            "ramp_steps": [10],
            "cooldown_minutes": 0,
            "rollback_percent": 0,
            "runner_interval_minutes": 1,
            "alert_suppression_minutes": 0,
            "notify_email_enabled": True,
            "notify_webhook_enabled": True,
            "notification_max_attempts": 3,
            "notification_backoff_base_seconds": 1,
            "auto_pause_enabled": False,
        },
    )
    assert policy.status_code == 200, policy.text

    body_obj = {"event_type": "delivery.status", "status": "delivered", "metadata": {"provider": "stub"}}
    body = json.dumps(body_obj)
    secret = "dev-webhook-secret"
    sig = _sign(secret, body)

    first = client.post(
        "/rollout/notifications/webhooks/webhook",
        headers={"X-Event-Id": "evt-phase6-001", "X-Signature": sig},
        content=body,
    )
    assert first.status_code == 200, first.text
    assert first.json()["accepted"] is True
    assert first.json()["duplicate"] is False

    # Same event id must be idempotent.
    second = client.post(
        "/rollout/notifications/webhooks/webhook",
        headers={"X-Event-Id": "evt-phase6-001", "X-Signature": sig},
        content=body,
    )
    assert second.status_code == 200, second.text
    assert second.json()["accepted"] is True
    assert second.json()["duplicate"] is True

    # Invalid signature is rejected.
    bad = client.post(
        "/rollout/notifications/webhooks/webhook",
        headers={"X-Event-Id": "evt-phase6-002", "X-Signature": "bad-signature"},
        content=body,
    )
    assert bad.status_code == 200, bad.text
    assert bad.json()["accepted"] is False
    assert bad.json()["duplicate"] is False

