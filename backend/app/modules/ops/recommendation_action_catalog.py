"""
Deterministic mapping: operational recommendation_type -> allowed advisory action_type values.

Actions are suggestions only; execution is always gated by preview + explicit confirmation in the workflow service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final


@dataclass(frozen=True)
class CatalogAction:
    action_type: str
    action_label: str
    action_description: str
    risk_level: str  # low | medium | high
    requires_confirmation: bool
    requires_override_reason: bool
    input_schema: dict[str, Any]
    auto_resolve_on_success: bool


# Stable action identifiers (also used by API clients).
ASSIGN_BEST_ENGINEER: Final = "assign_best_engineer"
MANUAL_ASSIGN_ENGINEER: Final = "manual_assign_engineer"
SET_MANUAL_ETA: Final = "set_manual_eta"
SEND_ON_MY_WAY_NOTIFICATION: Final = "send_on_my_way_notification"

CREATE_TRANSFER_REQUEST: Final = "create_transfer_request"
CREATE_PURCHASE_ORDER_DRAFT: Final = "create_purchase_order_draft"
RELEASE_CONFLICTING_RESERVATION: Final = "release_conflicting_reservation"
MARK_FOR_STOCK_REVIEW: Final = "mark_for_stock_review"

GENERATE_MISSING_CERTIFICATE: Final = "generate_missing_certificate"
REGENERATE_COST_SNAPSHOT: Final = "regenerate_cost_snapshot"
HOLD_INVOICE: Final = "hold_invoice"
MARK_FOR_FINANCE_REVIEW: Final = "mark_for_finance_review"

CREATE_CONTRACT_REVIEW_NOTE: Final = "create_contract_review_note"
MARK_FOR_RENEWAL_REVIEW: Final = "mark_for_renewal_review"
MARK_FOR_REPRICING_REVIEW: Final = "mark_for_repricing_review"
GENERATE_REPRICING_PROPOSAL: Final = "generate_repricing_proposal"

# Low-risk automation (draft / internal task + AutomationRun); no silent finals.
AUTOMATION_CONTRACT_REVIEW_TASK: Final = "automation_contract_review_task"

RESOLVE_DEFECT: Final = "resolve_defect"
ASSIGN_ALTERNATE_EQUIPMENT: Final = "assign_alternate_equipment"
MOVE_EQUIPMENT: Final = "move_equipment"
MARK_VEHICLE_REVIEW_REQUIRED: Final = "mark_vehicle_review_required"


def _a(
    action_type: str,
    *,
    label: str,
    description: str,
    risk_level: str = "medium",
    requires_confirmation: bool = True,
    requires_override_reason: bool = False,
    input_schema: dict[str, Any] | None = None,
    auto_resolve_on_success: bool = False,
) -> CatalogAction:
    return CatalogAction(
        action_type=action_type,
        action_label=label,
        action_description=description,
        risk_level=risk_level,
        requires_confirmation=requires_confirmation,
        requires_override_reason=requires_override_reason,
        input_schema=input_schema or {},
        auto_resolve_on_success=auto_resolve_on_success,
    )


ACTION_DEFINITIONS: dict[str, CatalogAction] = {
    ASSIGN_BEST_ENGINEER: _a(
        ASSIGN_BEST_ENGINEER,
        label="Assign best qualified engineer",
        description="Assign the top-ranked qualified engineer from dispatch intelligence for the related job.",
        risk_level="high",
        input_schema={},
    ),
    MANUAL_ASSIGN_ENGINEER: _a(
        MANUAL_ASSIGN_ENGINEER,
        label="Assign engineer (manual)",
        description="Assign a specific engineer to the job (dispatcher judgment).",
        risk_level="high",
        requires_override_reason=True,
        input_schema={
            "type": "object",
            "required": ["engineer_id"],
            "properties": {"engineer_id": {"type": "string"}},
        },
    ),
    SET_MANUAL_ETA: _a(
        SET_MANUAL_ETA,
        label="Set manual customer ETA",
        description="Set manual ETA minutes for customer-facing ETA / portal messaging.",
        risk_level="medium",
        input_schema={
            "type": "object",
            "required": ["eta_minutes"],
            "properties": {"eta_minutes": {"type": "integer", "minimum": 1}},
        },
    ),
    SEND_ON_MY_WAY_NOTIFICATION: _a(
        SEND_ON_MY_WAY_NOTIFICATION,
        label="Send on-my-way notification",
        description="Record on-my-way / customer notification for the job (customer-facing).",
        risk_level="high",
        input_schema={},
    ),
    CREATE_TRANSFER_REQUEST: _a(
        CREATE_TRANSFER_REQUEST,
        label="Create stock transfer (draft)",
        description="Create a draft internal stock transfer to mitigate the shortage (no ship/receive).",
        risk_level="low",
        input_schema={
            "type": "object",
            "properties": {
                "from_location_id": {"type": "string"},
                "to_location_id": {"type": "string"},
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["sku", "quantity"],
                        "properties": {"sku": {"type": "string"}, "quantity": {"type": "number", "minimum": 0.0001}},
                    },
                },
            },
        },
    ),
    CREATE_PURCHASE_ORDER_DRAFT: _a(
        CREATE_PURCHASE_ORDER_DRAFT,
        label="Create purchase order draft",
        description="Create a draft purchase order for replenishment (not sent to supplier).",
        risk_level="low",
        input_schema={
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string"},
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["sku", "quantity", "unit_cost"],
                        "properties": {
                            "sku": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unit_cost": {"type": "number"},
                        },
                    },
                },
            },
        },
    ),
    RELEASE_CONFLICTING_RESERVATION: _a(
        RELEASE_CONFLICTING_RESERVATION,
        label="Release a stock reservation",
        description="Release a specific reservation contributing to the shortage (requires explicit reservation id).",
        risk_level="high",
        input_schema={
            "type": "object",
            "required": ["reservation_id"],
            "properties": {"reservation_id": {"type": "string"}},
        },
    ),
    MARK_FOR_STOCK_REVIEW: _a(
        MARK_FOR_STOCK_REVIEW,
        label="Flag for stock review",
        description="Record an internal stock review flag on the recommendation audit trail (no ledger movement).",
        risk_level="low",
        requires_confirmation=False,
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
    GENERATE_MISSING_CERTIFICATE: _a(
        GENERATE_MISSING_CERTIFICATE,
        label="Generate compliance certificate",
        description="Generate a compliance certificate record for the job (downstream document hooks may run).",
        risk_level="high",
        input_schema={
            "type": "object",
            "properties": {"certificate_type": {"type": "string", "default": "completion"}},
        },
    ),
    REGENERATE_COST_SNAPSHOT: _a(
        REGENERATE_COST_SNAPSHOT,
        label="Regenerate job cost snapshot",
        description="Persist a fresh job cost snapshot from current costing inputs.",
        risk_level="medium",
        input_schema={},
    ),
    HOLD_INVOICE: _a(
        HOLD_INVOICE,
        label="Hold invoice",
        description="Mark invoice as held for finance review when compliance/costing preconditions apply.",
        risk_level="high",
        input_schema={"type": "object", "properties": {"hold_note": {"type": "string"}}},
    ),
    MARK_FOR_FINANCE_REVIEW: _a(
        MARK_FOR_FINANCE_REVIEW,
        label="Mark for finance review",
        description=(
            "Create an auditable InternalFollowUpTask (finance_review) linked to the invoice; "
            "on success, also appends a short cross-reference note on the invoice record."
        ),
        risk_level="low",
        requires_confirmation=False,
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
    CREATE_CONTRACT_REVIEW_NOTE: _a(
        CREATE_CONTRACT_REVIEW_NOTE,
        label="Add contract review note",
        description="Append an internal contract review note (commercial follow-up).",
        risk_level="low",
        requires_confirmation=False,
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
    MARK_FOR_RENEWAL_REVIEW: _a(
        MARK_FOR_RENEWAL_REVIEW,
        label="Mark for renewal review",
        description="Ensure renewal review date is set / brought forward on the contract.",
        risk_level="medium",
        input_schema={},
    ),
    MARK_FOR_REPRICING_REVIEW: _a(
        MARK_FOR_REPRICING_REVIEW,
        label="Mark for repricing review",
        description="Append a repricing review note on the contract.",
        risk_level="medium",
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
    GENERATE_REPRICING_PROPOSAL: _a(
        GENERATE_REPRICING_PROPOSAL,
        label="Generate repricing proposal",
        description=(
            "Create a formal ContractRepricingProposal from the contract repricing review "
            "(structured CPQ output; does not change live contract pricing or email the customer)."
        ),
        risk_level="medium",
        input_schema={
            "type": "object",
            "properties": {
                "contract_id": {"type": "string"},
                "repricing_review_id": {"type": "string"},
                "supersede_previous": {"type": "boolean"},
                "currency": {"type": "string"},
            },
        },
    ),
    AUTOMATION_CONTRACT_REVIEW_TASK: _a(
        AUTOMATION_CONTRACT_REVIEW_TASK,
        label="Create contract review follow-up (automation)",
        description=(
            "Opens or reuses a structured ContractReview and creates an InternalFollowUpTask "
            "(auditable AutomationRun; no contract pricing or activation changes)."
        ),
        risk_level="low",
        requires_confirmation=False,
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
    RESOLVE_DEFECT: _a(
        RESOLVE_DEFECT,
        label="Resolve vehicle defect",
        description="Close an open vehicle defect with resolution notes.",
        risk_level="high",
        input_schema={
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"},
                "defect_id": {"type": "string"},
                "resolution_notes": {"type": "string"},
            },
        },
        auto_resolve_on_success=True,
    ),
    ASSIGN_ALTERNATE_EQUIPMENT: _a(
        ASSIGN_ALTERNATE_EQUIPMENT,
        label="Assign alternate equipment",
        description="Move/assign field equipment to an engineer or vehicle (validated target).",
        risk_level="high",
        input_schema={
            "type": "object",
            "required": ["equipment_id", "target", "target_id"],
            "properties": {
                "equipment_id": {"type": "string"},
                "target": {"type": "string", "enum": ["engineer", "vehicle", "warehouse", "site"]},
                "target_id": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
    ),
    MOVE_EQUIPMENT: _a(
        MOVE_EQUIPMENT,
        label="Move equipment",
        description="Move equipment to warehouse/site/engineer/vehicle using the equipment service.",
        risk_level="high",
        input_schema={
            "type": "object",
            "required": ["equipment_id", "target", "target_id"],
            "properties": {
                "equipment_id": {"type": "string"},
                "target": {"type": "string"},
                "target_id": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
    ),
    MARK_VEHICLE_REVIEW_REQUIRED: _a(
        MARK_VEHICLE_REVIEW_REQUIRED,
        label="Mark vehicle for review",
        description="Record an internal vehicle readiness review flag (audit-only).",
        risk_level="low",
        requires_confirmation=False,
        input_schema={"type": "object", "properties": {"note": {"type": "string"}}},
    ),
}

_DISPATCH_ACTIONS: tuple[str, ...] = (
    ASSIGN_BEST_ENGINEER,
    MANUAL_ASSIGN_ENGINEER,
    SET_MANUAL_ETA,
    SEND_ON_MY_WAY_NOTIFICATION,
)
_DISPATCH_OMW_ONLY: tuple[str, ...] = (SEND_ON_MY_WAY_NOTIFICATION, SET_MANUAL_ETA)

_INVENTORY_ACTIONS: tuple[str, ...] = (
    CREATE_TRANSFER_REQUEST,
    CREATE_PURCHASE_ORDER_DRAFT,
    RELEASE_CONFLICTING_RESERVATION,
    MARK_FOR_STOCK_REVIEW,
)

_INVOICE_COMPLIANCE_ACTIONS: tuple[str, ...] = (
    GENERATE_MISSING_CERTIFICATE,
    REGENERATE_COST_SNAPSHOT,
    HOLD_INVOICE,
    MARK_FOR_FINANCE_REVIEW,
)

_CONTRACT_ACTIONS: tuple[str, ...] = (
    CREATE_CONTRACT_REVIEW_NOTE,
    MARK_FOR_RENEWAL_REVIEW,
    MARK_FOR_REPRICING_REVIEW,
)

_REPRICING_WITH_PROPOSAL: tuple[str, ...] = (
    AUTOMATION_CONTRACT_REVIEW_TASK,
    CREATE_CONTRACT_REVIEW_NOTE,
    MARK_FOR_REPRICING_REVIEW,
    GENERATE_REPRICING_PROPOSAL,
)

_EQUIPMENT_ACTIONS: tuple[str, ...] = (
    ASSIGN_ALTERNATE_EQUIPMENT,
    MOVE_EQUIPMENT,
    MARK_VEHICLE_REVIEW_REQUIRED,
)

_VEHICLE_DEFECT_ACTIONS: tuple[str, ...] = (RESOLVE_DEFECT, MARK_VEHICLE_REVIEW_REQUIRED)


# recommendation_type (from recommendation_engine rules) -> ordered action types
RECOMMENDATION_TYPE_TO_ACTIONS: dict[str, tuple[str, ...]] = {
    # Alias for tests / policy engines (same inventory surface as stock_shortage_reserved).
    "inventory_risk": _INVENTORY_ACTIONS,
    "contract_attention": (AUTOMATION_CONTRACT_REVIEW_TASK, CREATE_CONTRACT_REVIEW_NOTE),
    "sla_breach_risk": _DISPATCH_ACTIONS,
    "stale_telemetry_active_job": _DISPATCH_ACTIONS,
    "no_qualified_dispatch_candidate": _DISPATCH_ACTIONS,
    "engineer_overload": _DISPATCH_ACTIONS,
    "low_eta_confidence_imminent_visit": _DISPATCH_ACTIONS,
    "customer_on_my_way_not_notified": _DISPATCH_OMW_ONLY,
    "stock_shortage_reserved": _INVENTORY_ACTIONS,
    "parts_reconciliation_block": (MARK_FOR_STOCK_REVIEW, CREATE_TRANSFER_REQUEST),
    "invoice_release_hold": _INVOICE_COMPLIANCE_ACTIONS,
    "completion_compliance_gap": (GENERATE_MISSING_CERTIFICATE, MARK_FOR_FINANCE_REVIEW),
    "low_margin_job": (MARK_FOR_FINANCE_REVIEW, REGENERATE_COST_SNAPSHOT),
    "material_cost_variance": (MARK_FOR_FINANCE_REVIEW, REGENERATE_COST_SNAPSHOT),
    "contract_nearing_expiry": _CONTRACT_ACTIONS,
    "contract_repeated_sla_breaches": (CREATE_CONTRACT_REVIEW_NOTE, MARK_FOR_RENEWAL_REVIEW),
    "high_reactive_volume": (CREATE_CONTRACT_REVIEW_NOTE, MARK_FOR_REPRICING_REVIEW, GENERATE_REPRICING_PROPOSAL),
    "contract_negative_margin": _REPRICING_WITH_PROPOSAL,
    "contract_margin_deterioration": _REPRICING_WITH_PROPOSAL,
    "contract_high_reactive_burden": _REPRICING_WITH_PROPOSAL,
    "contract_renewal_risk": (MARK_FOR_RENEWAL_REVIEW, CREATE_CONTRACT_REVIEW_NOTE),
    "contract_repricing_opportunity": (
        MARK_FOR_REPRICING_REVIEW,
        GENERATE_REPRICING_PROPOSAL,
        CREATE_CONTRACT_REVIEW_NOTE,
    ),
    "contract_site_cost_hotspot": (
        CREATE_CONTRACT_REVIEW_NOTE,
        MARK_FOR_REPRICING_REVIEW,
        GENERATE_REPRICING_PROPOSAL,
    ),
    "contract_asset_reactive_hotspot": (
        CREATE_CONTRACT_REVIEW_NOTE,
        MARK_FOR_REPRICING_REVIEW,
        GENERATE_REPRICING_PROPOSAL,
    ),
    "ppm_schedule_overdue": (CREATE_CONTRACT_REVIEW_NOTE,),
    "qualification_expiring": (MARK_VEHICLE_REVIEW_REQUIRED,),
    "asset_service_overdue": (CREATE_CONTRACT_REVIEW_NOTE,),
    "equipment_required_missing": (ASSIGN_ALTERNATE_EQUIPMENT, MOVE_EQUIPMENT, MARK_VEHICLE_REVIEW_REQUIRED),
    "equipment_readiness_warning": (ASSIGN_ALTERNATE_EQUIPMENT, MOVE_EQUIPMENT, MARK_VEHICLE_REVIEW_REQUIRED),
    "equipment_calibration_compliance_risk": (MARK_VEHICLE_REVIEW_REQUIRED, MARK_FOR_FINANCE_REVIEW),
    "equipment_calibration_due_heavy_schedule": (MARK_VEHICLE_REVIEW_REQUIRED, CREATE_CONTRACT_REVIEW_NOTE),
    "equipment_out_of_service_referenced": (ASSIGN_ALTERNATE_EQUIPMENT, MOVE_EQUIPMENT),
    "equipment_tomorrow_schedule_gap": (CREATE_TRANSFER_REQUEST, MARK_FOR_STOCK_REVIEW),
    "vehicle_no_inspection_today": (MARK_VEHICLE_REVIEW_REQUIRED,),
    "vehicle_inspection_failed_critical": (MARK_VEHICLE_REVIEW_REQUIRED, RESOLVE_DEFECT),
    "vehicle_critical_defect_open": (RESOLVE_DEFECT, MARK_VEHICLE_REVIEW_REQUIRED),
    "vehicle_blocked_assigned_upcoming_work": (RESOLVE_DEFECT, ASSIGN_ALTERNATE_EQUIPMENT),
    "labour_excessive_overtime": (MARK_FOR_FINANCE_REVIEW,),
    "labour_out_of_hours_burden": (MARK_FOR_FINANCE_REVIEW,),
    "labour_costing_completeness_gap": (REGENERATE_COST_SNAPSHOT, MARK_FOR_FINANCE_REVIEW),
    "labour_travel_heavy_contract": (
        MARK_FOR_REPRICING_REVIEW,
        GENERATE_REPRICING_PROPOSAL,
        CREATE_CONTRACT_REVIEW_NOTE,
    ),
    "overdue_invoice_followup": (MARK_FOR_FINANCE_REVIEW, HOLD_INVOICE),
}


def actions_for_recommendation_type(recommendation_type: str) -> tuple[str, ...]:
    return RECOMMENDATION_TYPE_TO_ACTIONS.get(recommendation_type, ())
