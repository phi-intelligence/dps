def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase52_progressive_ramp_and_rollback(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    # Configure rapid automation settings for test.
    policy = client.post(
        "/rollout/policy",
        headers=_auth_headers(admin_token),
        json={
            "low_rating_threshold": 1,
            "error_events_threshold": 99,
            "evaluation_window_hours": 24,
            "ramp_steps": [10, 25, 50],
            "cooldown_minutes": 0,
            "rollback_percent": 5,
            "auto_pause_enabled": True,
        },
    )
    assert policy.status_code == 200, policy.text

    # Create planned wave for Engineers.
    wave = client.post(
        "/rollout/waves",
        headers=_auth_headers(admin_token),
        json={"name": "phase52-engineer-wave", "target_role": "Engineer", "rollout_percent": 0},
    )
    assert wave.status_code == 201, wave.text
    wave_id = wave.json()["id"]

    # Tick 1: planned -> active at first step.
    tick1 = client.post("/rollout/automation/tick", headers=_auth_headers(admin_token))
    assert tick1.status_code == 200, tick1.text
    assert tick1.json()["waves_started"] >= 1

    # Tick 2: active ramps to next step.
    tick2 = client.post("/rollout/automation/tick", headers=_auth_headers(admin_token))
    assert tick2.status_code == 200, tick2.text
    assert tick2.json()["waves_ramped"] >= 1

    # Engineer should now be allowed by rollout guard and can post usage event.
    guard = client.get("/rollout/guard/me", headers=_auth_headers(engineer_token))
    assert guard.status_code == 200, guard.text
    assert guard.json()["allowed"] is True

    event = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "feature_used"},
    )
    assert event.status_code == 201, event.text

    # Create low-rating feedback to trigger rollback+pause.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase52", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    bad_feedback = client.post(
        "/rollout/feedback",
        headers=_auth_headers(engineer_token),
        json={"category": "reliability", "rating": 1, "message": "Found a blocker"},
    )
    assert bad_feedback.status_code == 201, bad_feedback.text

    eval_res = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
    assert eval_res.status_code == 200, eval_res.text
    assert eval_res.json()["paused_waves_now"] >= 1

    # Confirm paused count via dashboard.
    dashboard = client.get("/rollout/dashboard", headers=_auth_headers(admin_token))
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["rollout_waves_paused"] >= 1

    # Wave should be paused and rollback percentage should be applied.
    waves = client.get("/rollout/waves", headers=_auth_headers(admin_token))
    assert waves.status_code == 200, waves.text
    target = next((w for w in waves.json() if w["id"] == wave_id), None)
    assert target is not None
    assert target["status"] == "paused"
    assert int(target["rollout_percent"]) == 5

