"""
Structured, business-relevant contract diffs for versioning and audit timelines.

Compares prior vs resulting contract snapshots (dicts), not raw ORM rows.

Policy:
- Only keys in ``MEANINGFUL_TRACKED_FIELDS`` can create a new ``manual_update`` version.
- JSON service fields are normalized (sorted keys) before comparison.
- Wider context for storage lives in ``contract_snapshot_for_diff`` / version ``snapshot_json``.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Final

# Fields that trigger a new manual_update version when changed via PATCH.
MEANINGFUL_TRACKED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "contract_value",
        "renewal_status",
        "renewal_decision",
        "repricing_required",
        "account_attention_level",
        "churn_risk_level",
        "term_start_at",
        "term_end_at",
        "renewal_review_date",
        "renewal_review_due_at",
        "billing_frequency",
        "contract_type",
        "status",
        "name",
        "contract_code",
        "site_id",
        "service_inclusions_json",
        "exclusions_json",
        "covered_assets_mode",
        "covered_asset_ids_json",
        "default_sla_policy_id",
        "ppm_interval_days",
        "next_ppm_due_at",
        "sla_response_minutes",
        "sla_attendance_minutes",
        "sla_completion_minutes",
        "notes",
    }
)

CATEGORY_DISPLAY_NAMES: Final[dict[str, str]] = {
    "commercial": "Commercial & renewal",
    "term": "Contract term",
    "operational": "Operational status",
    "identity": "Identity & reference",
    "scope": "Site & scope",
    "service_scope": "Service scope",
    "sla": "SLA",
    "ppm": "PPM schedule",
    "notes": "Notes",
    "other": "Other",
}


FIELD_DISPLAY_LABELS: Final[dict[str, str]] = {
    "contract_value": "Contract value",
    "renewal_status": "Renewal status",
    "renewal_decision": "Renewal decision",
    "repricing_required": "Repricing required",
    "account_attention_level": "Account attention level",
    "churn_risk_level": "Churn risk level",
    "term_start_at": "Term start",
    "term_end_at": "Term end",
    "renewal_review_date": "Renewal review date",
    "renewal_review_due_at": "Renewal review due",
    "billing_frequency": "Billing frequency",
    "contract_type": "Contract type",
    "status": "Operational status",
    "name": "Contract name",
    "contract_code": "Contract code",
    "site_id": "Site",
    "service_inclusions_json": "Service inclusions",
    "exclusions_json": "Exclusions",
    "covered_assets_mode": "Covered assets mode",
    "covered_asset_ids_json": "Covered assets",
    "default_sla_policy_id": "Default SLA policy",
    "ppm_interval_days": "PPM interval (days)",
    "next_ppm_due_at": "Next PPM due",
    "sla_response_minutes": "SLA response (minutes)",
    "sla_attendance_minutes": "SLA attendance (minutes)",
    "sla_completion_minutes": "SLA completion (minutes)",
    "notes": "Notes",
}


FIELD_CATEGORIES: Final[dict[str, str]] = {
    "contract_value": "commercial",
    "renewal_status": "commercial",
    "renewal_decision": "commercial",
    "repricing_required": "commercial",
    "account_attention_level": "commercial",
    "churn_risk_level": "commercial",
    "renewal_review_date": "commercial",
    "renewal_review_due_at": "commercial",
    "billing_frequency": "commercial",
    "term_start_at": "term",
    "term_end_at": "term",
    "contract_type": "commercial",
    "status": "operational",
    "name": "identity",
    "contract_code": "identity",
    "site_id": "scope",
    "service_inclusions_json": "service_scope",
    "exclusions_json": "service_scope",
    "covered_assets_mode": "service_scope",
    "covered_asset_ids_json": "service_scope",
    "default_sla_policy_id": "sla",
    "ppm_interval_days": "ppm",
    "next_ppm_due_at": "ppm",
    "sla_response_minutes": "sla",
    "sla_attendance_minutes": "sla",
    "sla_completion_minutes": "sla",
    "notes": "notes",
}


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    return dt.astimezone(timezone.utc).isoformat()


def _normalize_json_text(s: str | None) -> str | None:
    if s is None:
        return None
    try:
        return json.dumps(json.loads(s), sort_keys=True, default=str)
    except Exception:
        return s


def contract_snapshot_for_diff(c: Any) -> dict[str, Any]:
    """Full business snapshot from a Contract ORM instance (stable keys for diff + storage)."""
    return {
        "contract_id": c.id,
        "customer_id": c.customer_id,
        "site_id": c.site_id,
        "name": c.name,
        "contract_code": c.contract_code,
        "contract_type": c.contract_type,
        "status": c.status,
        "term_start_at": _iso(c.term_start_at),
        "term_end_at": _iso(c.term_end_at),
        "renewal_review_date": _iso(c.renewal_review_date),
        "billing_frequency": c.billing_frequency,
        "contract_value": c.contract_value,
        "covered_assets_mode": c.covered_assets_mode,
        "covered_asset_ids_json": _normalize_json_text(c.covered_asset_ids_json),
        "service_inclusions_json": _normalize_json_text(c.service_inclusions_json),
        "exclusions_json": _normalize_json_text(c.exclusions_json),
        "notes": c.notes,
        "default_sla_policy_id": c.default_sla_policy_id,
        "ppm_interval_days": c.ppm_interval_days,
        "next_ppm_due_at": _iso(c.next_ppm_due_at),
        "sla_response_minutes": c.sla_response_minutes,
        "sla_attendance_minutes": c.sla_attendance_minutes,
        "sla_completion_minutes": c.sla_completion_minutes,
        "renewal_status": c.renewal_status,
        "renewal_review_due_at": _iso(c.renewal_review_due_at),
        "renewal_review_last_opened_at": _iso(c.renewal_review_last_opened_at),
        "renewal_decision": c.renewal_decision,
        "repricing_required": c.repricing_required,
        "account_attention_level": c.account_attention_level,
        "churn_risk_level": c.churn_risk_level,
        "communication_locale": getattr(c, "communication_locale", None),
    }


def _values_equal(field: str, a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if type(a) is bool or type(b) is bool:
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) or isinstance(b, float):
            return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-9)
        return int(a) == int(b)
    return a == b


def merge_patch_into_snapshot(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Simulate applying ContractPatchIn fields onto a snapshot (values already JSON-normalized where needed)."""
    out = dict(base)
    for k, v in patch.items():
        if k == "manual_update_reason":
            continue
        if k not in out:
            continue
        if k in {
            "term_start_at",
            "term_end_at",
            "renewal_review_date",
            "next_ppm_due_at",
            "renewal_review_due_at",
            "renewal_review_last_opened_at",
        }:
            if v is None:
                out[k] = None
            elif isinstance(v, datetime):
                out[k] = _iso(v)
            else:
                out[k] = v
        elif k in {"service_inclusions_json", "exclusions_json", "covered_asset_ids_json"}:
            if v is None:
                out[k] = None
            elif isinstance(v, str):
                out[k] = _normalize_json_text(v)
            else:
                out[k] = v
        else:
            out[k] = v
    return out


def diff_contract_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """
    Produce structured diff for versioning and APIs.

    Returns:
      has_meaningful_changes, changed_fields, changes[], by_category{}, human_readable_summary, human_readable_lines
    """
    changed_fields: list[str] = []
    changes: list[dict[str, Any]] = []
    by_category: dict[str, list[str]] = {}

    for field in sorted(MEANINGFUL_TRACKED_FIELDS):
        b = before.get(field)
        a = after.get(field)
        if _values_equal(field, b, a):
            continue
        changed_fields.append(field)
        cat = FIELD_CATEGORIES.get(field, "other")
        by_category.setdefault(cat, []).append(field)
        changes.append(
            {
                "field": field,
                "category": cat,
                "before": b,
                "after": a,
            }
        )

    lines: list[str] = []
    for ch in changes:
        label = ch["field"].replace("_", " ")
        lines.append(f"{label}: {ch['before']!r} → {ch['after']!r}")

    summary = "; ".join(lines[:12])
    if len(lines) > 12:
        summary += f" … (+{len(lines) - 12} more)"

    return {
        "has_meaningful_changes": len(changed_fields) > 0,
        "changed_fields": changed_fields,
        "changes": changes,
        "by_category": by_category,
        "human_readable_lines": lines,
        "human_readable_summary": summary or "No tracked fields changed.",
    }


def display_name_for_category(category: str) -> str:
    return CATEGORY_DISPLAY_NAMES.get(category or "other", category or "Other")


def display_label_for_field(field: str) -> str:
    f = (field or "").strip()
    if not f:
        return "Field"
    return FIELD_DISPLAY_LABELS.get(f, f.replace("_", " ").title())


def enrich_changes_for_api(changes: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Attach human category and field labels for contract version / diff APIs (§5.5)."""
    if not changes:
        return []
    out: list[dict[str, Any]] = []
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        row = dict(ch)
        cat = str(row.get("category") or "other")
        row["category_display"] = display_name_for_category(cat)
        row["field_label"] = display_label_for_field(str(row.get("field") or ""))
        out.append(row)
    return out


def build_change_summary_json(
    *,
    source: str,
    diff: dict[str, Any],
    actor_user_id: str | None,
    manual_update_reason: str | None,
    prior_contract_value: Any,
    new_contract_value: Any,
) -> dict[str, Any]:
    """Structured payload stored on ContractVersion.change_summary_json."""
    return {
        "source": source,
        "changed_fields": diff["changed_fields"],
        "changes": diff["changes"],
        "by_category": diff["by_category"],
        "human_readable_summary": diff["human_readable_summary"],
        "human_readable_lines": diff["human_readable_lines"],
        "actor_user_id": actor_user_id,
        "manual_update_reason": manual_update_reason,
        "contract_value_before": prior_contract_value,
        "contract_value_after": new_contract_value,
    }
