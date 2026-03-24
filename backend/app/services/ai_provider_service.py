"""
Internal AI provider abstraction (Gemini REST via httpx).

Rules for future agentic / assisted workflows (enforced by architecture, not optional):
- AI may assist with summarization, drafting, explanation, prioritization suggestions.
- AI must NOT bypass RBAC, approvals, recommendation confirm flows, or low-risk automation
  boundaries. All side effects stay in explicit service code paths guarded by permissions.
- No route should call vendor SDKs directly; use this module (or thin orchestrators above it).
- Secrets live only in Settings / environment — never in the database or API responses.

§5.19 adds bounded text generation behind ``PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED`` + ``GEMINI_*`` + permission.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import httpx


@runtime_checkable
class GeminiLikeClient(Protocol):
    """Placeholder protocol; swap for google-generativeai client when integrated."""

    def generate_content(self, prompt: str, **kwargs: Any) -> Any: ...


class AIProviderService:
    """Injectable facade for future controlled LLM usage."""

    def __init__(self, settings: Any) -> None:
        self._settings = settings

    def is_enabled(self) -> bool:
        return bool(getattr(self._settings, "GEMINI_ENABLED", False)) and bool(
            getattr(self._settings, "GEMINI_API_KEY", "")
        )

    def get_provider_name(self) -> str:
        return "gemini"

    def get_default_model(self) -> str:
        return str(getattr(self._settings, "GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash")

    def build_client(self) -> GeminiLikeClient | None:
        """
        Returns a client handle when enabled and dependencies are available.
        Stub: returns None until an explicit SDK integration is added behind this method.
        """
        if not self.is_enabled():
            return None
        # Intentionally no network/SDK in this slice — prevents accidental invocation.
        return None

    def run_structured_prompt(
        self,
        *,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Future hook for bounded prompts (JSON schema / typed outputs).

        Raises if AI is disabled or not configured — callers must handle gracefully.
        """
        if not self.is_enabled():
            raise RuntimeError("AI provider is disabled or not configured (GEMINI_ENABLED / GEMINI_API_KEY).")
        if self.build_client() is None:
            raise RuntimeError(
                "AI provider is enabled but no client integration is available in this build "
                "(stub — implement build_client with explicit safety review)."
            )
        raise RuntimeError("run_structured_prompt not implemented — foundation only.")


def describe_safe_status(settings: Any) -> dict[str, Any]:
    """Metadata safe for GET /admin/ai/status (no secrets)."""
    key = str(getattr(settings, "GEMINI_API_KEY", "") or "").strip()
    base = str(getattr(settings, "GEMINI_BASE_URL", "") or "").strip()
    drafting = bool(getattr(settings, "AI_ASSISTED_DRAFTING_ENABLED", False))
    gem_on = bool(getattr(settings, "GEMINI_ENABLED", False))
    return {
        "enabled": gem_on,
        "provider_name": "gemini",
        "model": str(getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"),
        "base_url_configured": bool(base),
        "api_key_configured": bool(key),
        "ai_assisted_drafting_feature_flag": drafting,
        "ai_assisted_drafting_ready": drafting and gem_on and bool(key),
    }


def run_text_prompt(
    settings: Any,
    *,
    system_instruction: str,
    user_prompt: str,
    max_output_tokens: int = 512,
) -> str:
    """
    Single-turn text generation for internal drafting helpers (§5.19).
    Requires ``PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED``, ``GEMINI_ENABLED``, and API key.
    """
    if not bool(getattr(settings, "AI_ASSISTED_DRAFTING_ENABLED", False)):
        raise RuntimeError("AI-assisted drafting is disabled (PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED).")
    if not bool(getattr(settings, "GEMINI_ENABLED", False)):
        raise RuntimeError("Gemini is disabled (GEMINI_ENABLED).")
    key = str(getattr(settings, "GEMINI_API_KEY", "") or "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    model = str(getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash").strip()
    if model.startswith("models/"):
        model = model[8:]
    base = str(getattr(settings, "GEMINI_BASE_URL", "") or "").strip() or "https://generativelanguage.googleapis.com"
    url = f"{base.rstrip('/')}/v1beta/models/{model}:generateContent"
    payload: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": max_output_tokens, "temperature": 0.35},
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, params={"key": key}, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError("Gemini returned no candidates")
    parts = (cands[0].get("content") or {}).get("parts") or []
    texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
    if not texts:
        raise RuntimeError("Gemini returned empty text")
    return "\n".join(texts).strip()


def get_ai_provider_service(settings: Any | None = None) -> AIProviderService:
    from backend.app.core.config import settings as default_settings

    return AIProviderService(settings or default_settings)
