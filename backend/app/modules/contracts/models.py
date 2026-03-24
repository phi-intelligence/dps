from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True, nullable=False)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), index=True, nullable=True)

    # Human identifiers
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    contract_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # ppm_only | ppm_plus_reactive | full_maintenance | labour_only | compliance_only

    status: Mapped[str] = mapped_column(String(32), default="active", index=True, nullable=False)

    term_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    term_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    renewal_review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    billing_frequency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contract_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    covered_assets_mode: Mapped[str] = mapped_column(String(32), default="all_assets", nullable=False)
    # all_assets | selected_assets
    covered_asset_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    service_inclusions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    exclusions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    default_sla_policy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sla_policies.id"), nullable=True, index=True
    )

    # Legacy PPM cadence (still supported for older flows).
    ppm_interval_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    next_ppm_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Legacy SLA minute targets (used when no policy attached).
    sla_response_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    sla_attendance_minutes: Mapped[int] = mapped_column(Integer, default=240, nullable=False)
    sla_completion_minutes: Mapped[int] = mapped_column(Integer, default=720, nullable=False)

    # Commercial renewal / repricing workflow (aligned with ContractReview decisions).
    # not_due | due_soon | in_review | repricing_review | ready_to_renew | renewed | at_risk | exit_pending
    renewal_status: Mapped[str] = mapped_column(String(32), default="not_due", index=True, nullable=False)
    renewal_review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    renewal_review_last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    renewal_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    repricing_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    # low | normal | high | critical
    account_attention_level: Mapped[str] = mapped_column(String(16), default="normal", index=True, nullable=False)
    churn_risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    # §5.17 — BCP 47-style tag (e.g. en, fr); customer comm templates fall back to global env when unset.
    communication_locale: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
