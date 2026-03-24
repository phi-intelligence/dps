def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase53_scheduled_runner_and_alert_lifecycle(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    # Policy configured for runner intervals and strict SLO breach thresholds.
    policy = client.post(
        "/rollout/policy",
        headers=_auth_headers(admin_token),
        json={
            "low_rating_threshold": 1,
            "error_events_threshold": 1,
            "evaluation_window_hours": 24,
            "ramp_steps": [10, 100],
            "cooldown_minutes": 0,
            "rollback_percent": 0,
            "runner_interval_minutes": 60,
            "auto_pause_enabled": True,
        },
    )
    assert policy.status_code == 200, policy.text

    # Create a planned wave and run scheduled cycle (non-forced) first time -> should run.
    wave = client.post(
        "/rollout/waves",
        headers=_auth_headers(admin_token),
        json={"name": "phase53-wave", "target_role": "Engineer", "rollout_percent": 0},
    )
    assert wave.status_code == 201, wave.text

    cycle_1 = client.post("/rollout/automation/run-cycle", headers=_auth_headers(admin_token))
    assert cycle_1.status_code == 200, cycle_1.text
    assert cycle_1.json()["ran"] is True
    assert cycle_1.json()["tick"] is not None

    # Immediate rerun without force should skip due to runner interval policy.
    cycle_2 = client.post("/rollout/automation/run-cycle", headers=_auth_headers(admin_token))
    assert cycle_2.status_code == 200, cycle_2.text
    assert cycle_2.json()["ran"] is False
    assert cycle_2.json()["skipped_reason"] == "runner-interval-not-reached"

    # Force-run bypasses interval guard.
    cycle_3 = client.post("/rollout/automation/run-cycle?force=true", headers=_auth_headers(admin_token))
    assert cycle_3.status_code == 200, cycle_3.text
    assert cycle_3.json()["ran"] is True

    # Enroll engineer in pilot and emit an error event to trigger health auto-pause alert.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase53", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    err_evt = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "error_unhandled_exception"},
    )
    assert err_evt.status_code == 201, err_evt.text

    eval_res = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
    assert eval_res.status_code == 200, eval_res.text

    alerts = client.get("/rollout/alerts", headers=_auth_headers(admin_token))
    assert alerts.status_code == 200, alerts.text
    alert_list = alerts.json()
    assert len(alert_list) >= 1
    alert_id = alert_list[0]["id"]

    ack = client.post(f"/rollout/alerts/{alert_id}/ack", headers=_auth_headers(admin_token))
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "acknowledged"

