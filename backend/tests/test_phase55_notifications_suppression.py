def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase55_alert_suppression_and_notification_retry(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    # Enable notifier channels and suppression window.
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
            "alert_suppression_minutes": 60,
            "notify_email_enabled": True,
            "notify_webhook_enabled": True,
            "auto_pause_enabled": False,
        },
    )
    assert policy.status_code == 200, policy.text

    # Ensure engineer can submit events.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase55", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    # Repeated failing events trigger same alert code with suppression dedup.
    for _ in range(2):
        evt = client.post(
            "/rollout/events",
            headers=_auth_headers(engineer_token),
            json={"module": "mobile", "event_name": "error_FAIL_NOTIFY"},
        )
        assert evt.status_code == 201, evt.text
        ev = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
        assert ev.status_code == 200, ev.text

    alerts = client.get("/rollout/alerts", headers=_auth_headers(admin_token))
    assert alerts.status_code == 200, alerts.text
    fail_alerts = [a for a in alerts.json() if a["code"] in {"SLO_THRESHOLD_BREACH", "AUTO_PAUSE_TRIGGERED"}]
    assert len(fail_alerts) >= 1
    assert any(int(a["dedup_count"]) >= 1 for a in fail_alerts)

    deliveries = client.get("/rollout/notifications/deliveries", headers=_auth_headers(admin_token))
    assert deliveries.status_code == 200, deliveries.text
    rows = deliveries.json()
    assert len(rows) >= 1

    failed = next((d for d in rows if d["status"] == "failed"), None)
    if failed is not None:
        retry = client.post(
            f"/rollout/notifications/deliveries/{failed['id']}/retry",
            headers=_auth_headers(admin_token),
        )
        assert retry.status_code == 200, retry.text
        assert int(retry.json()["attempts"]) >= int(failed["attempts"]) + 1

