"""
High-level "what needs attention" counts across commercial, finance, and job failures (§5.7).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.services import acceptance_policy_service as aps
from backend.app.services import commercial_follow_up_needs_action_service as cfna
from backend.app.services import operations_diagnostics_service as ops_diag
from backend.app.modules.invoicing.service import finance_operations_dashboard


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def operations_blockers_overview(db: Session, *, limit_each: int = 5) -> dict[str, Any]:
    cf = cfna.dashboard_commercial_follow_up_needs_action(db, limit_per_section=200)
    fin = finance_operations_dashboard(db, limit_queue=50)
    diag = ops_diag.operations_diagnostics_summary(db, limit_each=min(max(limit_each, 1), 50))

    return {
        "generated_at": utc_now().isoformat(),
        "acceptance_policy_mode": aps.acceptance_policy_mode(),
        "commercial_follow_up": {
            "proposal_rows": len(cf.get("proposals") or []),
            "activation_confirmation_rows": len(cf.get("activation_confirmations") or []),
            "draft_customer_comms_rows": len(cf.get("draft_customer_comms") or []),
        },
        "finance_status_counts": fin.get("status_counts") or {},
        "recent_failure_samples": {
            "recurring_job_failures_shown": diag["counts"]["recurring_job_failures_shown"],
            "activation_failures_shown": diag["counts"]["activation_failures_shown"],
            "communication_delivery_failures_shown": diag["counts"]["communication_delivery_failures_shown"],
        },
    }
