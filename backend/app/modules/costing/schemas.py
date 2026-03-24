from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobCostingLineOut(BaseModel):
    sku: str
    description: str
    stock_item_id: str | None = None
    estimated_qty: float
    reserved_qty: float
    actual_qty: float
    unit_cost: float
    unit_sell_quote: float
    estimated_cost: float
    reserved_cost: float
    actual_cost: float
    billable_from_actual: float
    variance_flags: list[str] = Field(default_factory=list)
    cost_basis_note: str | None = None


class JobCostingSummaryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    currency: str
    source: str = "live"  # live | snapshot
    estimated_material_cost: float
    reserved_material_cost: float
    actual_material_cost: float
    material_cost_variance_vs_estimate: float
    material_cost_variance_vs_reserved: float
    estimated_material_qty: float
    reserved_material_qty: float
    actual_material_qty: float
    materials_billable_from_actual: float
    labour_seconds: int
    labour_hours: float
    labour_cost: float
    labour_overtime_cost: float | None = None
    labour_doubletime_cost: float | None = None
    labour_regular_cost: float | None = None
    labour_out_of_hours_cost: float | None = None
    travel_cost: float | None = None
    labour_completeness_status: str | None = None
    labour_warnings: list[str] = Field(default_factory=list)
    labour_rate_profile_id: str | None = None
    labour_rate_profile_name: str | None = None
    labour_cost_breakdown: dict[str, Any] = Field(default_factory=dict)
    labour_calculation_basis: dict[str, Any] = Field(default_factory=dict)
    labour_rules_attribution: dict[str, Any] = Field(default_factory=dict)
    rules_completeness_status: str | None = None
    labour_note: str | None = None
    costing_warnings: list[str] = Field(default_factory=list)
    costing_status: str
    lines: list[JobCostingLineOut]


class JobLabourCostingOut(BaseModel):
    """Labour-only view (same truth as embedded job costing labour block)."""

    job_id: str
    labour_completeness_status: str | None = None
    labour_warnings: list[str] = Field(default_factory=list)
    labour_rate_profile_id: str | None = None
    labour_rate_profile_name: str | None = None
    labour_cost_breakdown: dict[str, Any] = Field(default_factory=dict)
    labour_calculation_basis: dict[str, Any] = Field(default_factory=dict)
    labour_rules_attribution: dict[str, Any] = Field(default_factory=dict)
    rules_completeness_status: str | None = None
    source: str = "live"


class JobMarginSummaryOut(BaseModel):
    job_id: str
    customer_id: str | None = None
    currency: str = "GBP"
    estimated_material_cost: float
    actual_material_cost: float
    variance_amount: float
    variance_percent: float | None = None
    unreconciled_costing_flag: bool = False
    invoice_generated_flag: bool = False
    costing_status: str | None = None
    snapshot_id: str | None = None
    invoice_before_snapshot_flag: bool = False


class JobCostVarianceRowOut(BaseModel):
    job_id: str
    customer_id: str | None = None
    job_status: str
    estimated_material_cost: float
    actual_material_cost: float
    variance_amount: float
    costing_status: str
    has_snapshot: bool
    invoice_id: str | None = None
    flags: list[str] = Field(default_factory=list)
