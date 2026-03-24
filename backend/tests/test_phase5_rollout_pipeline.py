def _login(client, *, username: str, password: str) -> str:
    res = client.post("/auth/token", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_phase5_pipeline_end_to_end(client):
    admin_token = _login(client, username="admin@example.com", password="admin")
    engineer_token = _login(client, username="engineer@example.com", password="engineer")

    engineer_me = client.get("/auth/me", headers=_auth_headers(engineer_token))
    assert engineer_me.status_code == 200, engineer_me.text
    engineer_id = engineer_me.json()["id"]

    # 1) Pilot enrollment
    enroll = client.post(
        "/rollout/pilot/users",
        headers=_auth_headers(admin_token),
        json={"user_id": engineer_id, "cohort": "pilot-wave-a", "status": "active", "notes": "first batch"},
    )
    assert enroll.status_code == 201, enroll.text
    assert enroll.json()["status"] == "active"

    # 2) Rollout wave creation and progression
    create_wave = client.post(
        "/rollout/waves",
        headers=_auth_headers(admin_token),
        json={"name": "wave-1", "target_role": "Engineer", "rollout_percent": 20},
    )
    assert create_wave.status_code == 201, create_wave.text
    wave_id = create_wave.json()["id"]

    start_wave = client.post(f"/rollout/waves/{wave_id}/start", headers=_auth_headers(admin_token))
    assert start_wave.status_code == 200, start_wave.text
    assert start_wave.json()["status"] == "active"

    complete_wave = client.post(f"/rollout/waves/{wave_id}/complete", headers=_auth_headers(admin_token))
    assert complete_wave.status_code == 200, complete_wave.text
    assert complete_wave.json()["status"] == "completed"

    # 3) Pilot usage and feedback capture
    event = client.post(
        "/rollout/events",
        headers=_auth_headers(engineer_token),
        json={"module": "mobile", "event_name": "job_completed", "metadata": {"source": "pilot"}},
    )
    assert event.status_code == 201, event.text

    feedback = client.post(
        "/rollout/feedback",
        headers=_auth_headers(engineer_token),
        json={"category": "workflow", "rating": 4, "message": "Dispatch flow is smooth"},
    )
    assert feedback.status_code == 201, feedback.text
    feedback_id = feedback.json()["id"]

    # 4) Triage feedback (bugs/refinements loop)
    triage = client.post(
        f"/rollout/feedback/{feedback_id}/triage",
        headers=_auth_headers(admin_token),
        json={"status": "triaged", "triage_notes": "Schedule UX refinement"},
    )
    assert triage.status_code == 200, triage.text
    assert triage.json()["status"] == "triaged"

    # 5) Monitor rollout dashboard metrics
    dashboard = client.get("/rollout/dashboard", headers=_auth_headers(admin_token))
    assert dashboard.status_code == 200, dashboard.text
    body = dashboard.json()
    assert body["pilot_users_total"] >= 1
    assert body["rollout_waves_completed"] >= 1
    assert body["feedback_total"] >= 1
    assert body["usage_events_24h"] >= 1

