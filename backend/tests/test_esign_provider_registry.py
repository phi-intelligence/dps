"""§5.16 — additional e-sign provider (echo) and configured fallback when primary is unavailable."""
from __future__ import annotations

from backend.app.services.esign_provider_service import EsignSignatureRequestContext, get_esign_provider
from backend.app.services.esign_providers.echo_esign_provider import EchoEsignProvider


def test_echo_provider_distinct_from_stub():
    echo = EchoEsignProvider()
    assert echo.provider_name() == "echo"
    assert echo.is_configured() is True
    r = echo.create_signature_request(
        EsignSignatureRequestContext(
            proposal_id="p" * 36,
            proposal_reference="PR-1",
            contract_id="c" * 36,
            customer_id="u" * 36,
            signer_email="a@b.com",
            signer_name="A",
            document_title="T",
            callback_reference="cb1",
        )
    )
    assert r.envelope_id.startswith("echo-env-")
    assert "/external-esign/echo/" in r.signing_url


def test_esign_fallback_to_echo_when_docusign_unconfigured(monkeypatch):
    monkeypatch.setenv("PHI_DPS_ESIGN_PROVIDER", "docusign")
    monkeypatch.delenv("PHI_DPS_ESIGN_CLIENT_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_API_KEY", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_USER_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_RSA_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_BASE_URL", raising=False)
    monkeypatch.setenv("PHI_DPS_ESIGN_FALLBACK_PROVIDER", "echo")

    p = get_esign_provider()
    assert isinstance(p, EchoEsignProvider)


def test_esign_no_fallback_returns_unconfigured_primary(monkeypatch):
    monkeypatch.setenv("PHI_DPS_ESIGN_PROVIDER", "docusign")
    monkeypatch.delenv("PHI_DPS_ESIGN_CLIENT_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_API_KEY", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_USER_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_RSA_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_BASE_URL", raising=False)
    monkeypatch.delenv("PHI_DPS_ESIGN_FALLBACK_PROVIDER", raising=False)

    p = get_esign_provider()
    from backend.app.services.esign_providers.docusign_esign_provider import DocusignEsignProvider

    assert isinstance(p, DocusignEsignProvider)
    assert p.is_configured() is False


def test_primary_echo_skips_fallback(monkeypatch):
    monkeypatch.setenv("PHI_DPS_ESIGN_PROVIDER", "echo")
    monkeypatch.setenv("PHI_DPS_ESIGN_FALLBACK_PROVIDER", "stub")
    p = get_esign_provider()
    assert isinstance(p, EchoEsignProvider)
