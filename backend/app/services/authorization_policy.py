"""
Static permission keys and role → permission mapping.

Deterministic; extend later with DB-driven grants per tenant.
"""
from __future__ import annotations

from typing import Final

# --- Permission keys (fine-grained) ---
CAN_HOLD_INVOICE: Final = "can_hold_invoice"
CAN_RELEASE_INVOICE: Final = "can_release_invoice"
CAN_MARK_FINANCE_REVIEW: Final = "can_mark_finance_review"
CAN_CREATE_PURCHASE_ORDER: Final = "can_create_purchase_order"
CAN_APPROVE_PURCHASE_ORDER: Final = "can_approve_purchase_order"
CAN_TRIGGER_CUSTOMER_NOTIFICATION: Final = "can_trigger_customer_notification"
CAN_DECIDE_CONTRACT_REVIEW: Final = "can_decide_contract_review"
CAN_APPROVE_REPRICING: Final = "can_approve_repricing"
CAN_OVERRIDE_VEHICLE_BLOCK: Final = "can_override_vehicle_block"
CAN_OVERRIDE_EQUIPMENT_BLOCK: Final = "can_override_equipment_block"
CAN_MANAGE_LABOUR_RULES: Final = "can_manage_labour_rules"
# Enterprise: manage per-user permission grants + audit (Admin baseline; refinable via grants).
CAN_ADMIN_PERMISSION_GRANTS: Final = "can_admin_permission_grants"
# Internal access groups, memberships, group grants, and entity scopes.
CAN_ADMIN_ORG_ACCESS: Final = "can_admin_org_access"
# Low-risk automation / internal task operator APIs (replaces role-only gate for finer control).
CAN_RUN_OPS_AUTOMATION: Final = "can_run_ops_automation"
# Contract-scoped customer communications (draft → ready → approve → send; outbound via provider abstraction).
CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION: Final = "can_view_contract_customer_communication"
CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION: Final = "can_create_contract_customer_communication"
CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND: Final = "can_approve_contract_customer_communication_send"
CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION: Final = "can_send_contract_customer_communication"
CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE: Final = "can_manage_customer_communication_preference"
# §5.14 — send despite recipient suppression (requires reason + break_glass audit row).
CAN_BREAK_GLASS_COMMUNICATION_SUPPRESSION: Final = "can_break_glass_communication_suppression"
# §5.19 — bounded LLM drafting (summaries / notes / explanations); never autonomous actions.
CAN_AI_ASSISTED_DRAFTING: Final = "can_ai_assisted_drafting"

ALL_PERMISSION_KEYS: frozenset[str] = frozenset(
    {
        CAN_HOLD_INVOICE,
        CAN_RELEASE_INVOICE,
        CAN_MARK_FINANCE_REVIEW,
        CAN_CREATE_PURCHASE_ORDER,
        CAN_APPROVE_PURCHASE_ORDER,
        CAN_TRIGGER_CUSTOMER_NOTIFICATION,
        CAN_DECIDE_CONTRACT_REVIEW,
        CAN_APPROVE_REPRICING,
        CAN_OVERRIDE_VEHICLE_BLOCK,
        CAN_OVERRIDE_EQUIPMENT_BLOCK,
        CAN_MANAGE_LABOUR_RULES,
        CAN_ADMIN_PERMISSION_GRANTS,
        CAN_ADMIN_ORG_ACCESS,
        CAN_RUN_OPS_AUTOMATION,
        CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
        CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION,
        CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND,
        CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION,
        CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE,
        CAN_BREAK_GLASS_COMMUNICATION_SUPPRESSION,
        CAN_AI_ASSISTED_DRAFTING,
    }
)

# Human-readable labels for admin catalog / UI.
PERMISSION_LABELS: dict[str, str] = {
    CAN_HOLD_INVOICE: "Hold invoices",
    CAN_RELEASE_INVOICE: "Release held invoices",
    CAN_MARK_FINANCE_REVIEW: "Mark invoices for finance review",
    CAN_CREATE_PURCHASE_ORDER: "Create purchase orders / drafts",
    CAN_APPROVE_PURCHASE_ORDER: "Approve purchase orders",
    CAN_TRIGGER_CUSTOMER_NOTIFICATION: "Trigger customer notifications (e.g. on-my-way)",
    CAN_DECIDE_CONTRACT_REVIEW: "Decide contract / repricing review actions",
    CAN_APPROVE_REPRICING: "Approve repricing internally",
    CAN_OVERRIDE_VEHICLE_BLOCK: "Override vehicle block / critical defect gates",
    CAN_OVERRIDE_EQUIPMENT_BLOCK: "Override equipment block / calibration gates",
    CAN_MANAGE_LABOUR_RULES: "Manage labour rules and holiday calendars",
    CAN_ADMIN_PERMISSION_GRANTS: "Administer per-user permission grants",
    CAN_ADMIN_ORG_ACCESS: "Manage internal access groups, group grants, and entity scopes",
    CAN_RUN_OPS_AUTOMATION: "Run low-risk automation and internal follow-up task APIs",
    CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION: "View contract customer communication pipeline and records",
    CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION: "Create and prepare contract customer communications (draft/ready)",
    CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND: "Approve customer communications that require approval before send",
    CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION: "Send (or simulate send) contract customer communications",
    CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE: "Create or update customer communication preferences (email channel, etc.)",
    CAN_BREAK_GLASS_COMMUNICATION_SUPPRESSION: "Break-glass: send contract comms despite recipient suppression (reason required; audited)",
    CAN_AI_ASSISTED_DRAFTING: "Use AI-assisted drafting (summaries, notes, explanations; human review required)",
}


def roles_including_permission(permission_key: str) -> list[str]:
    """Role names that include this permission by default (static baseline)."""
    return sorted(
        role for role, perms in ROLE_PERMISSIONS.items() if permission_key in perms
    )

# Role names must match Role.name in DB (bootstrap).
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "Admin": ALL_PERMISSION_KEYS,
    "Finance": frozenset(
        {
            CAN_HOLD_INVOICE,
            CAN_RELEASE_INVOICE,
            CAN_MARK_FINANCE_REVIEW,
            CAN_APPROVE_REPRICING,
            CAN_APPROVE_PURCHASE_ORDER,
            CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
            CAN_APPROVE_CONTRACT_CUSTOMER_COMMUNICATION_SEND,
            CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE,
        }
    ),
    "Commercial": frozenset(
        {
            CAN_DECIDE_CONTRACT_REVIEW,
            CAN_APPROVE_REPRICING,
            CAN_TRIGGER_CUSTOMER_NOTIFICATION,
            CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
            CAN_CREATE_CONTRACT_CUSTOMER_COMMUNICATION,
            CAN_SEND_CONTRACT_CUSTOMER_COMMUNICATION,
            CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE,
            CAN_AI_ASSISTED_DRAFTING,
        }
    ),
    "Ops_Manager": frozenset(
        {
            CAN_CREATE_PURCHASE_ORDER,
            CAN_APPROVE_PURCHASE_ORDER,
            CAN_OVERRIDE_VEHICLE_BLOCK,
            CAN_OVERRIDE_EQUIPMENT_BLOCK,
            CAN_MANAGE_LABOUR_RULES,
            CAN_RUN_OPS_AUTOMATION,
            CAN_AI_ASSISTED_DRAFTING,
        }
    ),
    "Dispatcher": frozenset(
        {
            CAN_CREATE_PURCHASE_ORDER,
            CAN_TRIGGER_CUSTOMER_NOTIFICATION,
            CAN_RUN_OPS_AUTOMATION,
            CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
            CAN_AI_ASSISTED_DRAFTING,
            # Dispatch ops only — no finance/commercial/override by default.
        }
    ),
    "Engineer": frozenset(),
    "Client": frozenset(),
    "Viewer": frozenset(),
}

# Recommendation / ops action_type → required permission (None = only role gate on route).
RECOMMENDATION_ACTION_PERMISSION: dict[str, str] = {
    "hold_invoice": CAN_HOLD_INVOICE,
    "mark_for_finance_review": CAN_MARK_FINANCE_REVIEW,
    "create_purchase_order_draft": CAN_CREATE_PURCHASE_ORDER,
    "send_on_my_way_notification": CAN_TRIGGER_CUSTOMER_NOTIFICATION,
    "create_contract_review_note": CAN_DECIDE_CONTRACT_REVIEW,
    "mark_for_renewal_review": CAN_DECIDE_CONTRACT_REVIEW,
    "mark_for_repricing_review": CAN_DECIDE_CONTRACT_REVIEW,
    "generate_repricing_proposal": CAN_DECIDE_CONTRACT_REVIEW,
    "automation_contract_review_task": CAN_DECIDE_CONTRACT_REVIEW,
    # resolve_defect / equipment moves: permission depends on preview.extra (severity / calibration).
}
