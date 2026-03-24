"""§5.19 — Permission-gated drafting helpers (no autonomous side effects)."""
from __future__ import annotations

from typing import Literal
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.crm.models import Customer, Lead
from backend.app.modules.dispatch.models import Job
from backend.app.modules.quoting.models import Quote, QuoteItem
from backend.app.services import ai_provider_service as ai
from backend.app.services import authorization_policy as policy
from backend.app.services import authorization_service as authz
from backend.app.services.runtime_settings_service import get_effective_feature_flags

router = APIRouter(prefix="/ai", tags=["ai"])


def _require_ai_drafting(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    authz.require_permission_http(user, policy.CAN_AI_ASSISTED_DRAFTING, db=db)
    return user


class AiDraftingAssistIn(BaseModel):
    task: Literal["quote_summary", "follow_up_notes", "proposal_explanation", "dispatch_prioritization_hint"]
    quote_id: str | None = None
    lead_id: str | None = None
    job_ids: list[str] | None = None
    extra_context: str | None = Field(None, max_length=8000)


class AiDraftingAssistOut(BaseModel):
    suggested_text: str
    model: str
    disclaimer: str


_SYSTEM_BY_TASK: dict[str, str] = {
    "quote_summary": (
        "You summarize commercial quotes for internal staff. Use short bullets. "
        "Do not promise coverage, SLAs, or legal terms not present in the data."
    ),
    "proposal_explanation": (
        "Explain a field-service quote in plain, professional UK English suitable for a customer email draft. "
        "Do not invent services, prices, or contractual terms beyond what is given."
    ),
    "follow_up_notes": (
        "Suggest concise internal follow-up notes for sales staff (not customer-facing). Checklist style."
    ),
    "dispatch_prioritization_hint": (
        "Offer prioritization hints for a human dispatcher only. You do not assign engineers or change records. "
        "Reference SLA, compliance, and priority fields when relevant."
    ),
}


def _build_user_prompt(db: Session, body: AiDraftingAssistIn) -> str:
    chunks: list[str] = []
    if body.task in ("quote_summary", "proposal_explanation"):
        if not body.quote_id:
            raise ValueError("quote_id is required for this task")
        q = db.get(Quote, body.quote_id)
        if not q:
            raise ValueError("Quote not found")
        cust = db.get(Customer, q.customer_id) if q.customer_id else None
        items = db.query(QuoteItem).filter(QuoteItem.quote_id == q.id).order_by(QuoteItem.id.asc()).all()
        lines = [f"- {it.description} x{it.quantity} @ {it.unit_price} = {it.line_total}" for it in items]
        chunks.append(
            f"Quote id={q.id} status={q.status} currency={q.currency} "
            f"labour_total={q.labour_total} materials_total={q.materials_total} grand_total={q.grand_total}"
        )
        if cust:
            chunks.append(f"Customer: {cust.name}")
        chunks.append("Line items:\n" + ("\n".join(lines) if lines else "(none)"))
        if q.notes:
            chunks.append(f"Quote notes: {q.notes}")
    elif body.task == "follow_up_notes":
        if not body.lead_id:
            raise ValueError("lead_id is required for this task")
        lead = db.get(Lead, body.lead_id)
        if not lead:
            raise ValueError("Lead not found")
        chunks.append(
            f"Lead id={lead.id} name={lead.name} status={lead.status} email={lead.email} phone={lead.phone}\n"
            f"property_type={lead.property_type} preferred_time_slots={lead.preferred_time_slots}\n"
            f"issue_description: {lead.issue_description or ''}"
        )
    elif body.task == "dispatch_prioritization_hint":
        ids = [j for j in (body.job_ids or []) if j][:20]
        if not ids:
            raise ValueError("job_ids is required (max 20) for this task")
        rows = db.query(Job).filter(Job.id.in_(ids)).all()
        by_id = {j.id: j for j in rows}
        missing = [i for i in ids if i not in by_id]
        if missing:
            raise ValueError("One or more jobs not found")
        for jid in ids:
            j = by_id[jid]
            chunks.append(
                f"Job {j.id}: status={j.status} dispatch_priority={j.dispatch_priority} "
                f"work_type={j.work_type} sla_priority={j.sla_priority} "
                f"compliance_required={j.compliance_required} covered_under_contract={j.covered_under_contract}\n"
                f"address: {j.address[:500]}"
            )
    if body.extra_context:
        chunks.append(f"Additional context from user:\n{body.extra_context}")
    return "\n\n".join(chunks)


@router.post("/drafting/assist", response_model=AiDraftingAssistOut)
def post_ai_drafting_assist(
    body: AiDraftingAssistIn,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_ai_drafting),
) -> AiDraftingAssistOut:
    ff = get_effective_feature_flags(db)
    if not bool(ff.get("ai_assisted_drafting_enabled", False)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI-assisted drafting is disabled by runtime settings.",
        )
    try:
        user_prompt = _build_user_prompt(db, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    try:
        settings_proxy = SimpleNamespace(
            AI_ASSISTED_DRAFTING_ENABLED=bool(ff.get("ai_assisted_drafting_enabled", False)),
            GEMINI_ENABLED=bool(getattr(settings, "GEMINI_ENABLED", False)),
            GEMINI_API_KEY=str(getattr(settings, "GEMINI_API_KEY", "") or ""),
            GEMINI_MODEL=str(getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"),
            GEMINI_BASE_URL=str(getattr(settings, "GEMINI_BASE_URL", "") or ""),
        )
        text = ai.run_text_prompt(
            settings_proxy,
            system_instruction=_SYSTEM_BY_TASK[body.task],
            user_prompt=user_prompt,
            max_output_tokens=640,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    svc = ai.get_ai_provider_service(settings_proxy)
    return AiDraftingAssistOut(
        suggested_text=text,
        model=svc.get_default_model(),
        disclaimer="Draft only. A human must verify before customer send or operational action. AI does not run workflows.",
    )
