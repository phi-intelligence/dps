def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_rollout_guard_by_wave_and_auto_pause(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    dispatcher_token = _login(client, username="dispatcher@example.com", password="dispatcher")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    # Dispatcher is initially not in pilot and should be blocked.
    guard_before = client.get("/rollout/guard/me", headers=_auth_headers(dispatcher_token))
    assert guard_before.status_code == 200, guard_before.text
    assert guard_before.json()["allowed"] is False

    event_blocked = client.post(
        "/rollout/events",
        headers=_auth_headers(dispatcher_token),
        json={"module": "dispatch", "event_name": "view_board"},
    )
    assert event_blocked.status_code == 403, event_blocked.text

    # Create role-based wave and activate it at 100% rollout.
    wave = client.post(
        "/rollout/waves",
        headers=_auth_headers(admin_token),
        json={"name": "phase51-dispatcher-wave", "target_role": "Dispatcher", "rollout_percent": 100},
    )
    assert wave.status_code == 201, wave.text
    wave_id = wave.json()["id"]

    wave_start = client.post(f"/rollout/waves/{wave_id}/start", headers=_auth_headers(admin_token))
    assert wave_start.status_code == 200, wave_start.text
    assert wave_start.json()["status"] == "active"

    # Guard now allows dispatcher due to active role wave.
    guard_after = client.get("/rollout/guard/me", headers=_auth_headers(dispatcher_token))
    assert guard_after.status_code == 200, guard_after.text
    assert guard_after.json()["allowed"] is True

    event_allowed = client.post(
        "/rollout/events",
        headers=_auth_headers(dispatcher_token),
        json={"module": "dispatch", "event_name": "view_board"},
    )
    assert event_allowed.status_code == 201, event_allowed.text

    # Configure strict policy so one bad signal triggers auto-pause.
    policy = client.post(
        "/rollout/policy",
        headers=_auth_headers(admin_token),
        json={
            "low_rating_threshold": 1,
            "error_events_threshold": 1,
            "evaluation_window_hours": 24,
            "auto_pause_enabled": True,
        },
    )
    assert policy.status_code == 200, policy.text

    # Enroll engineer into pilot and generate low-rating feedback + error event.
    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]

    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "phase51", "status": "active"},
    )
    assert enroll.status_code == 201, enroll.text

    bad_feedback = client.post(
        "/rollout/feedback",
        headers=_auth_headers(engineer_token),
        json={"category": "reliability", "rating": 1, "message": "App failed during dispatch"},
    )
    assert bad_feedback.status_code == 201, bad_feedback.text

    error_event = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "error_sync_timeout"},
    )
    assert error_event.status_code == 201, error_event.text

    evaluate = client.post("/rollout/health/evaluate", headers=_auth_headers(admin_token))
    assert evaluate.status_code == 200, evaluate.text
    eval_body = evaluate.json()
    assert eval_body["paused_waves_now"] >= 1

    # Dashboard should reflect paused wave count.
    dashboard = client.get("/rollout/dashboard", headers=_auth_headers(admin_token))
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["rollout_waves_paused"] >= 1

