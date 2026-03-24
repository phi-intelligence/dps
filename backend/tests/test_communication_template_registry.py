"""§5.17 — template registry, versioned keys, contract locale → French copy."""
from __future__ import annotations

from backend.app.core import config
from backend.app.db.session import SessionLocal
from backend.app.modules.contracts.models import Contract
from backend.app.services.communication_template_registry import (
    build_template_key,
    list_communication_template_registry,
    normalize_locale,
    resolve_communication_locale_for_contract,
)
from backend.app.services import contract_customer_communication_templates as tpl
from backend.tests.test_contract_amendment_activation import _admin_token, _auth, _proposal_ready_for_customer_release


def test_normalize_locale():
    assert normalize_locale("FR-fr") == "fr"
    assert normalize_locale("en-GB") == "en"
    assert normalize_locale(None) == "en"


def test_build_template_key_includes_catalog_and_locale():
    assert build_template_key("repricing_proposal_released", locale="en").startswith("phi_dps/cv")
    assert "/en/repricing_proposal_released" in build_template_key("repricing_proposal_released", locale="en")


def test_list_registry_contains_all_types():
    rows = list_communication_template_registry()
    types = {r["communication_type"] for r in rows}
    assert tpl.COMMS_REPRICING_PROPOSAL_RELEASED in types
    assert all("supported_locales" in r for r in rows)


def test_system_registry_endpoint(client):
    admin = _admin_token(client)
    r = client.get("/system/communication-template-registry", headers=_auth(admin))
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
    assert any(x.get("communication_type") == tpl.COMMS_REPRICING_PROPOSAL_RELEASED for x in r.json())


def test_french_comm_when_contract_locale_fr(client, monkeypatch):
    monkeypatch.setattr(config.settings, "COMMUNICATION_TEMPLATE_LOCALE", "en", raising=False)
    admin = _admin_token(client)
    contract_id, proposal_id, _email = _proposal_ready_for_customer_release(client, admin)
    db = SessionLocal()
    try:
        c = db.get(Contract, contract_id)
        assert c is not None
        c.communication_locale = "fr"
        db.add(c)
        db.commit()
        db.refresh(c)
        assert resolve_communication_locale_for_contract(c) == "fr"
    finally:
        db.close()

    client.post(
        f"/contracts/repricing-proposals/{proposal_id}/release-to-customer",
        headers=_auth(admin),
        json={},
    )
    lst = client.get(
        "/contracts/communications",
        headers=_auth(admin),
        params={"source_entity_type": "repricing_proposal", "source_entity_id": proposal_id},
    )
    assert lst.status_code == 200
    hit = next(x for x in lst.json() if x["communication_type"] == "repricing_proposal_released")
    assert hit["template_key"].startswith("phi_dps/cv")
    assert "/fr/" in hit["template_key"]
    assert "Bonjour" in (hit.get("body_text") or "")
