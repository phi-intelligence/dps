def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase54_scheduler_once_and_alert_digest(client):
    from backend.app.modules.rollout.scheduler import run_rollout_cycle_once

    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    # Configure strict thresholds and a wave to ensure alerts are generated.
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
            "runner_interval_minutes": 1,
            "auto_pause_enabled": True,
        },
    )
    assert policy.status_code == 200, policy.text

    wave = client.post(
        "/rollout/waves",
        headers=_auth_headers(admin_token),
        json={"name": "phase54-wave", "target_role": "Engineer", "rollout_percent": 0},
    )
    assert wave.status_code == 201, wave.text

    # One-shot scheduler helper should run a full cycle.
    cycle = run_rollout_cycle_once(force=True)
    assert cycle["ran"] is True

    # Enroll engineer and create an error event to trigger alert generation.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase54", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    err_evt = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "error_phase54"},
    )
    assert err_evt.status_code == 201, err_evt.text

    eval_res = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
    assert eval_res.status_code == 200, eval_res.text

    digest = client.get("/rollout/alerts/digest", headers=_auth_headers(admin_token))
    assert digest.status_code == 200, digest.text
    body = digest.json()
    assert body["total_alerts"] >= 1
    assert body["open_alerts"] >= 1
    assert body["alerts_last_24h"] >= 1

