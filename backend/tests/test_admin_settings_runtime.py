from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.db.session import SessionLocal
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.modules.auth.admin_settings_models import AdminSettingAuditLog, AdminSettingValue
from backend.app.modules.auth import admin_settings_service as admin_settings
from backend.app.services import runtime_settings_service as runtime_settings


@pytest.fixture(autouse=True)
def _isolate_admin_settings_tables_and_cache():
    # Ensure FK target tables (e.g. users) are registered in metadata.
    from backend.app.modules.auth import models as _auth_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    runtime_settings._cache.clear()  # type: ignore[attr-defined]
    db = SessionLocal()
    try:
        db.query(AdminSettingAuditLog).delete()
        db.query(AdminSettingValue).delete()
        db.commit()
    finally:
        db.close()
    yield
    runtime_settings._cache.clear()  # type: ignore[attr-defined]


def test_upsert_invalid_dispatch_values_raises_validation_error():
    db = SessionLocal()
    try:
        with pytest.raises(ValidationError):
            admin_settings.upsert_domain_settings(
                db,
                domain="dispatch",
                values={"telemetry_fresh_seconds": 1.0},
                actor_user_id=None,
                reason="invalid test",
            )
    finally:
        db.close()


def test_upsert_writes_audit_and_effective_values():
    db = SessionLocal()
    try:
        out = admin_settings.upsert_domain_settings(
            db,
            domain="security",
            values={"access_token_expire_minutes": 180},
            actor_user_id="tester-user-id",
            reason="  policy change  ",
        )
        assert out["effective"]["access_token_expire_minutes"] == 180
        assert out["overrides"]["access_token_expire_minutes"] == 180

        rows = admin_settings.list_domain_audit_logs(db, domain="security", limit=10)
        assert len(rows) == 1
        assert rows[0].setting_key == "security"
        assert rows[0].changed_by_user_id == "tester-user-id"
        assert rows[0].reason == "policy change"
        assert '"access_token_expire_minutes":180' in rows[0].new_value_json
    finally:
        db.close()


def test_runtime_effective_computation_uses_db_overrides():
    db = SessionLocal()
    try:
        admin_settings.upsert_domain_settings(
            db,
            domain="notifications",
            values={
                "communication_enabled": True,
                "communication_email_provider": "sendgrid",
                "communication_sms_provider": "twilio",
                "communication_template_locale": "fr",
                "communication_template_catalog_version": "7",
                "portal_support_email": "ops@example.com",
                "portal_support_phone": "+44 20 1234 5678",
            },
            actor_user_id=None,
            reason=None,
        )
        eff = runtime_settings.get_effective_notifications_settings(db)
        assert eff["communication_enabled"] is True
        assert eff["communication_email_provider"] == "sendgrid"
        assert eff["communication_sms_provider"] == "twilio"
        assert eff["communication_template_locale"] == "fr"
        assert eff["communication_template_catalog_version"] == "7"
        assert eff["portal_support_email"] == "ops@example.com"
    finally:
        db.close()


def test_refresh_runtime_cache_picks_up_latest_security_value():
    db = SessionLocal()
    try:
        admin_settings.upsert_domain_settings(
            db,
            domain="security",
            values={"access_token_expire_minutes": 60},
            actor_user_id=None,
            reason=None,
        )
        # Warm cache with the initial value.
        first = runtime_settings.get_effective_security_settings(db)
        assert first["access_token_expire_minutes"] == 60

        # Update DB value; without refresh, cached value remains visible.
        admin_settings.upsert_domain_settings(
            db,
            domain="security",
            values={"access_token_expire_minutes": 240},
            actor_user_id=None,
            reason=None,
        )
        stale_cached = runtime_settings.get_effective_security_settings(None)
        assert stale_cached["access_token_expire_minutes"] == 60

        runtime_settings.refresh_runtime_settings_cache(db)
        refreshed = runtime_settings.get_effective_security_settings(None)
        assert refreshed["access_token_expire_minutes"] == 240
    finally:
        db.close()


def test_runtime_diagnostics_returns_all_supported_domains():
    db = SessionLocal()
    try:
        admin_settings.upsert_domain_settings(
            db,
            domain="feature_flags",
            values={"ai_assisted_drafting_enabled": True},
            actor_user_id=None,
            reason=None,
        )
        diag = runtime_settings.get_effective_runtime_diagnostics(db)
        assert {"feature_flags", "dispatch", "security", "notifications"} <= set(diag.keys())
        assert diag["feature_flags"]["effective"]["ai_assisted_drafting_enabled"] is True
    finally:
        db.close()
