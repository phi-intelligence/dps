"""
Human-readable contract version change summaries for admins (§5.5).

Uses stored change_summary_json; does not re-diff full snapshots by default.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.contracts.contract_version_models import ContractVersion
from backend.app.modules.contracts.models import Contract
from backend.app.services.contract_diff_service import display_name_for_category, enrich_changes_for_api
from backend.app.services import contract_version_service as cvs


def _loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def readable_change_for_version(
    db: Session,
    *,
    contract_id: str,
    version_id: str,
) -> dict[str, Any]:
    v = db.get(ContractVersion, version_id)
    if not v or v.contract_id != contract_id:
        raise ValueError("Version not found for this contract")
    c = db.get(Contract, contract_id)
    raw = _loads(v.change_summary_json) or {}
    if not isinstance(raw, dict):
        raw = {}

    changes = raw.get("changes") if isinstance(raw.get("changes"), list) else []
    by_cat = raw.get("by_category") if isinstance(raw.get("by_category"), dict) else {}
    enriched = enrich_changes_for_api([x for x in changes if isinstance(x, dict)])

    by_category_display: list[dict[str, Any]] = []
    for cat, fields in sorted(by_cat.items(), key=lambda x: x[0]):
        by_category_display.append(
            {
                "category": cat,
                "category_display": display_name_for_category(str(cat)),
                "fields": list(fields) if isinstance(fields, list) else [],
            }
        )

    headline = str(raw.get("human_readable_summary") or "").strip() or "No structured change summary stored."
    lines = raw.get("human_readable_lines")
    if not isinstance(lines, list):
        lines = [headline] if headline else []

    version_headline = {
        "initial": "Baseline or pre-history version window",
        "amendment_activation": "Contract updated from an approved amendment activation",
        "manual_update": "Contract updated from a manual administrative change",
    }.get(v.version_type, f"Version type: {v.version_type}")

    return {
        "contract_id": contract_id,
        "contract_code": c.contract_code if c else None,
        "version_id": v.id,
        "version_number": v.version_number,
        "version_type": v.version_type,
        "version_type_explanation": version_headline,
        "effective_from": v.effective_from.isoformat() if v.effective_from else None,
        "effective_to": v.effective_to.isoformat() if v.effective_to else None,
        "source_amendment_id": v.source_amendment_id,
        "headline": headline,
        "human_readable_lines": lines,
        "changes": enriched,
        "by_category": by_category_display,
        "manual_update_reason": raw.get("manual_update_reason"),
        "change_source": raw.get("source"),
        "contract_value_before": raw.get("contract_value_before"),
        "contract_value_after": raw.get("contract_value_after"),
    }


def active_open_version_summary(db: Session, *, contract_id: str) -> dict[str, Any]:
    """Current open version (effective_to IS NULL) with a one-line readable summary (§5.5)."""
    c = db.get(Contract, contract_id)
    if not c:
        raise ValueError("Contract not found")
    v = cvs.get_open_version(db, contract_id=contract_id)
    if not v:
        return {
            "contract_id": contract_id,
            "contract_code": c.contract_code,
            "open_version": None,
            "message": "No open contract version row (check versioning data).",
        }
    raw = _loads(v.change_summary_json) or {}
    summary = raw.get("human_readable_summary") if isinstance(raw, dict) else None
    return {
        "contract_id": contract_id,
        "contract_code": c.contract_code,
        "open_version": {
            "version_id": v.id,
            "version_number": v.version_number,
            "version_type": v.version_type,
            "effective_from": v.effective_from.isoformat() if v.effective_from else None,
            "one_line_summary": (str(summary or "").strip()[:500]) or None,
            "source_amendment_id": v.source_amendment_id,
        },
    }


def recent_version_activity(
    db: Session,
    *,
    limit: int = 40,
) -> list[dict[str, Any]]:
    rows = (
        db.query(ContractVersion)
        .order_by(ContractVersion.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    out: list[dict[str, Any]] = []
    for v in rows:
        c = db.get(Contract, v.contract_id)
        raw = _loads(v.change_summary_json) or {}
        summary = raw.get("human_readable_summary") if isinstance(raw, dict) else None
        out.append(
            {
                "contract_id": v.contract_id,
                "contract_code": c.contract_code if c else None,
                "version_id": v.id,
                "version_number": v.version_number,
                "version_type": v.version_type,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "one_line_summary": (summary or "")[:500] or None,
            }
        )
    return out
