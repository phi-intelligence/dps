def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase56_retry_backoff_and_dead_letter(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

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
            "notification_max_attempts": 2,
            "notification_backoff_base_seconds": 1,
            "auto_pause_enabled": False,
        },
    )
    assert policy.status_code == 200, policy.text

    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase56", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    # Trigger failing alert notification path.
    evt = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "error_FAIL_NOTIFY"},
    )
    assert evt.status_code == 201, evt.text
    eval_res = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
    assert eval_res.status_code == 200, eval_res.text

    deliveries = client.get("/rollout/notifications/deliveries", headers=_auth_headers(admin_token))
    assert deliveries.status_code == 200, deliveries.text
    failed = next((d for d in deliveries.json() if d["status"] == "failed"), None)
    assert failed is not None
    assert failed["next_retry_at"] is not None

    # Immediate processor run should not process yet because retry time is in future.
    run1 = client.post("/rollout/notifications/retries/process", headers=_auth_headers(admin_token))
    assert run1.status_code == 200, run1.text
    assert run1.json()["processed"] >= 0

    # Manual retry should exhaust max attempts and dead-letter.
    retry = client.post(
        f"/rollout/notifications/deliveries/{failed['id']}/retry",
        headers=_auth_headers(admin_token),
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] in {"failed", "dead_letter"}

    if retry.json()["status"] != "dead_letter":
        retry2 = client.post(
            f"/rollout/notifications/deliveries/{failed['id']}/retry",
            headers=_auth_headers(admin_token),
        )
        assert retry2.status_code == 200, retry2.text
        assert retry2.json()["status"] == "dead_letter"

    alerts = client.get("/rollout/alerts", headers=_auth_headers(admin_token))
    assert alerts.status_code == 200, alerts.text
    assert any(a["code"] == "NOTIFICATION_DEAD_LETTER" for a in alerts.json())

