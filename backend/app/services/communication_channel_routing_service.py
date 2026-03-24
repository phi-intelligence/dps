"""
§5.15 — optional per-communication-type channel overrides (env JSON) layered on template defaults.
"""
from __future__ import annotations

import json
from typing import Any

from backend.app.core.config import settings
from backend.app.services import contract_customer_communication_templates as tpl

_VALID = frozenset({"email", "sms", "portal_notice", "internal_draft"})


def _type_channel_map() -> dict[str, str]:
    raw = settings.COMMUNICATION_TYPE_CHANNEL_MAP_JSON
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(obj, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(k, str) and isinstance(v, str) and v.strip().lower() in _VALID:
            out[k.strip()] = v.strip().lower()
    return out


def effective_channel_for_communication_type(communication_type: str) -> str:
    m = _type_channel_map()
    hit = m.get(communication_type)
    if hit:
        return hit
    return tpl.type_default_channel(communication_type)
