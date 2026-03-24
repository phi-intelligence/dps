"""
Code-based templates for contract-scoped customer communications.

All customer-facing copy is generated here — routes must not embed ad hoc strings.

§5.17: versioned ``template_key`` (see ``communication_template_registry``) and en/fr locale support.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.core.config import settings
from backend.app.services.runtime_settings_service import get_effective_notifications_settings


# --- Explicit communication types (deterministic) ---
COMMS_REPRICING_PROPOSAL_RELEASED = "repricing_proposal_released"
COMMS_REPRICING_PROPOSAL_REMINDER = "repricing_proposal_reminder"
COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER = "repricing_proposal_esign_reminder"
COMMS_REPRICING_PROPOSAL_REJECTED_FOLLOW_UP = "repricing_proposal_rejected_follow_up"
COMMS_REPRICING_PROPOSAL_COUNTER_REQUESTED_FOLLOW_UP = "repricing_proposal_counter_requested_follow_up"
COMMS_ACTIVATION_CONFIRMATION_RELEASED = "activation_confirmation_released"
COMMS_ACTIVATION_CONFIRMATION_REMINDER = "activation_confirmation_reminder"
COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP = "activation_confirmation_acknowledgement_follow_up"
COMMS_CONTRACT_FOLLOW_UP_NOTICE = "contract_follow_up_notice"

ALL_COMMUNICATION_TYPES: frozenset[str] = frozenset(
    {
        COMMS_REPRICING_PROPOSAL_RELEASED,
        COMMS_REPRICING_PROPOSAL_REMINDER,
        COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
        COMMS_REPRICING_PROPOSAL_REJECTED_FOLLOW_UP,
        COMMS_REPRICING_PROPOSAL_COUNTER_REQUESTED_FOLLOW_UP,
        COMMS_ACTIVATION_CONFIRMATION_RELEASED,
        COMMS_ACTIVATION_CONFIRMATION_REMINDER,
        COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP,
        COMMS_CONTRACT_FOLLOW_UP_NOTICE,
    }
)

# Default channel for customer-visible intents (stub delivery still records workflow).
CHANNEL_EMAIL = "email"
CHANNEL_SMS = "sms"
CHANNEL_PORTAL_NOTICE = "portal_notice"
CHANNEL_INTERNAL_DRAFT = "internal_draft"


def type_default_channel(communication_type: str) -> str:
    if communication_type == COMMS_CONTRACT_FOLLOW_UP_NOTICE:
        return CHANNEL_INTERNAL_DRAFT
    return CHANNEL_EMAIL


def type_requires_approval(communication_type: str) -> bool:
    """Policy: reminders and sensitive follow-ups require explicit approval before send."""
    return communication_type in (
        COMMS_REPRICING_PROPOSAL_REMINDER,
        COMMS_REPRICING_PROPOSAL_ESIGN_REMINDER,
        COMMS_ACTIVATION_CONFIRMATION_REMINDER,
        COMMS_ACTIVATION_CONFIRMATION_ACK_FOLLOW_UP,
        COMMS_REPRICING_PROPOSAL_REJECTED_FOLLOW_UP,
        COMMS_REPRICING_PROPOSAL_COUNTER_REQUESTED_FOLLOW_UP,
    )


def template_key_for_type(communication_type: str, *, locale: str | None = None) -> str:
    from backend.app.services.communication_template_registry import build_template_key, normalize_locale

    if locale is None:
        eff = get_effective_notifications_settings(None)
        locale = normalize_locale(str(eff["communication_template_locale"]))
    return build_template_key(communication_type, locale=locale)


def _portal_support_email() -> str:
    eff = get_effective_notifications_settings(None)
    return str(eff["portal_support_email"])


def _portal_support_phone() -> str:
    eff = get_effective_notifications_settings(None)
    return str(eff["portal_support_phone"])


def _lang(locale: str | None) -> str:
    lo = (locale or "en").strip().lower()
    return "fr" if lo.startswith("fr") else "en"


def _L(locale: str | None, en: str, fr: str) -> str:
    return fr if _lang(locale) == "fr" else en


@dataclass
class RenderedCommunication:
    subject: str | None
    body_text: str
    body_html: str | None
    customer_safe_summary: dict[str, Any]
    link_hints: dict[str, str]


def _portal(path: str) -> str:
    base = settings.PHI_DPS_PORTAL_WEB_BASE
    return f"{base}{path}"


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        from datetime import timezone

        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def render_repricing_proposal_released(
    *,
    proposal_reference: str,
    contract_name: str,
    contract_code: str,
    customer_name: str,
    currency: str,
    current_value: float | None,
    proposed_value: float | None,
    validity_end: datetime | None,
    customer_expiry: datetime | None,
    proposal_id: str,
    stored_document_id: str | None,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/repricing-proposals/{proposal_id}")
    subj = (
        f"Commercial proposal ready for review — {proposal_reference}"
        if _lang(locale) == "en"
        else f"Proposition commerciale prête à l'examen — {proposal_reference}"
    )
    lines = [
        _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
        "",
        _L(
            locale,
            f"A commercial proposal is available for contract {contract_name} ({contract_code}).",
            f"Une proposition commerciale est disponible pour le contrat {contract_name} ({contract_code}).",
        ),
        _L(locale, f"Proposal reference: {proposal_reference}", f"Référence de la proposition : {proposal_reference}"),
    ]
    if current_value is not None:
        lines.append(
            _L(
                locale,
                f"Current basis: {currency} {current_value:,.2f}",
                f"Base actuelle : {currency} {current_value:,.2f}",
            )
        )
    if proposed_value is not None:
        lines.append(
            _L(
                locale,
                f"Proposed value: {currency} {proposed_value:,.2f}",
                f"Valeur proposée : {currency} {proposed_value:,.2f}",
            )
        )
    if validity_end:
        lines.append(
            _L(locale, f"Commercial validity: {_fmt_dt(validity_end)}", f"Validité commerciale : {_fmt_dt(validity_end)}")
        )
    if customer_expiry:
        lines.append(
            _L(locale, f"Please respond by: {_fmt_dt(customer_expiry)}", f"Merci de répondre avant le {_fmt_dt(customer_expiry)}")
        )
    lines.extend(
        [
            "",
            _L(
                locale,
                f"View and respond in your customer portal: {portal_url}",
                f"Consultez et répondez dans votre portail client : {portal_url}",
            ),
            _L(
                locale,
                f"Support: {_portal_support_email()} | {_portal_support_phone()}",
                f"Assistance : {_portal_support_email()} | {_portal_support_phone()}",
            ),
        ]
    )
    body = "\n".join(lines)
    open_lbl = _L(locale, "Open portal", "Ouvrir le portail")
    html = f"<p>{body.replace(chr(10), '<br/>')}</p><p><a href=\"{portal_url}\">{open_lbl}</a></p>"
    summary = {
        "proposal_reference": proposal_reference,
        "contract_code": contract_code,
        "portal_path": f"/repricing-proposals/{proposal_id}",
    }
    hints = {"portal_repricing_proposal": portal_url}
    if stored_document_id:
        hints["stored_document_id"] = stored_document_id
    return RenderedCommunication(subj, body, html, summary, hints)


def render_repricing_proposal_reminder(
    *,
    proposal_reference: str,
    contract_code: str,
    customer_name: str,
    customer_expiry: datetime | None,
    proposal_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/repricing-proposals/{proposal_id}")
    subj = (
        f"Reminder: proposal {proposal_reference} awaiting your response"
        if _lang(locale) == "en"
        else f"Rappel : proposition {proposal_reference} en attente de votre réponse"
    )
    parts = [
        _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
        "",
        _L(
            locale,
            f"This is a reminder regarding proposal {proposal_reference} for contract {contract_code}.",
            f"Il s'agit d'un rappel concernant la proposition {proposal_reference} pour le contrat {contract_code}.",
        ),
        _L(
            locale,
            f"Please review and respond in the portal: {portal_url}",
            f"Veuillez consulter et répondre via le portail : {portal_url}",
        ),
    ]
    if customer_expiry:
        parts.append(
            _L(locale, f"Response target: {_fmt_dt(customer_expiry)}", f"Date limite de réponse : {_fmt_dt(customer_expiry)}")
        )
    parts.extend(["", _L(locale, f"Support: {_portal_support_email()}", f"Assistance : {_portal_support_email()}")])
    body = "\n".join(parts).strip()
    html = f"<p>{body.replace(chr(10), '<br/>')}</p>"
    return RenderedCommunication(
        subj,
        body,
        html,
        {"proposal_reference": proposal_reference, "reminder": True},
        {"portal_repricing_proposal": portal_url},
    )


def render_repricing_proposal_esign_reminder(
    *,
    proposal_reference: str,
    contract_code: str,
    customer_name: str,
    proposal_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/repricing-proposals/{proposal_id}")
    subj = (
        f"Reminder: complete your electronic signature — {proposal_reference}"
        if _lang(locale) == "en"
        else f"Rappel : finalisez votre signature électronique — {proposal_reference}"
    )
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"Our records show the electronic signature for proposal {proposal_reference} ({contract_code}) is still outstanding.",
                f"D'après nos informations, la signature électronique de la proposition {proposal_reference} ({contract_code}) est toujours en attente.",
            ),
            _L(
                locale,
                "If you already started signing, please return to the signing session from your email invitation.",
                "Si vous avez déjà commencé, reprenez la session depuis l'invitation reçue par e-mail.",
            ),
            _L(
                locale,
                f"You can also open the proposal in your customer portal for context: {portal_url}",
                f"Vous pouvez aussi ouvrir la proposition dans le portail pour référence : {portal_url}",
            ),
            "",
            _L(locale, f"Support: {_portal_support_email()}", f"Assistance : {_portal_support_email()}"),
        ]
    )
    html = f"<p>{body.replace(chr(10), '<br/>')}</p>"
    return RenderedCommunication(
        subj,
        body,
        html,
        {"proposal_reference": proposal_reference, "reminder": True, "esign": True},
        {"portal_repricing_proposal": portal_url},
    )


def render_repricing_rejected_follow_up(
    *,
    proposal_reference: str,
    contract_code: str,
    customer_name: str,
    proposal_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    subj = (
        f"Follow-up: your feedback on {proposal_reference}"
        if _lang(locale) == "en"
        else f"Suivi : votre retour sur {proposal_reference}"
    )
    portal_url = _portal(f"/repricing-proposals/{proposal_id}")
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"We noted your response to proposal {proposal_reference} ({contract_code}).",
                f"Nous avons pris note de votre réponse à la proposition {proposal_reference} ({contract_code}).",
            ),
            _L(
                locale,
                "Your account team will contact you with next steps.",
                "Votre équipe commerciale vous contactera pour la suite.",
            ),
            _L(locale, f"Portal reference: {portal_url}", f"Lien portail : {portal_url}"),
            "",
            _L(locale, f"Support: {_portal_support_email()}", f"Assistance : {_portal_support_email()}"),
        ]
    )
    return RenderedCommunication(
        subj,
        body,
        f"<p>{body.replace(chr(10), '<br/>')}</p>",
        {"proposal_reference": proposal_reference, "follow_up": "rejected"},
        {"portal_repricing_proposal": portal_url},
    )


def render_repricing_counter_follow_up(
    *,
    proposal_reference: str,
    contract_code: str,
    customer_name: str,
    proposal_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    subj = (
        f"Follow-up: counter-request for {proposal_reference}"
        if _lang(locale) == "en"
        else f"Suivi : demande de contre-proposition pour {proposal_reference}"
    )
    portal_url = _portal(f"/repricing-proposals/{proposal_id}")
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"We received a counter-request related to proposal {proposal_reference} ({contract_code}).",
                f"Nous avons reçu une demande de contre-proposition concernant la proposition {proposal_reference} ({contract_code}).",
            ),
            _L(
                locale,
                "Commercial will review and respond in line with your request.",
                "Le service commercial l'examinera et répondra conformément à votre demande.",
            ),
            _L(locale, f"Portal reference: {portal_url}", f"Lien portail : {portal_url}"),
        ]
    )
    return RenderedCommunication(
        subj,
        body,
        f"<p>{body.replace(chr(10), '<br/>')}</p>",
        {"proposal_reference": proposal_reference, "follow_up": "counter_requested"},
        {"portal_repricing_proposal": portal_url},
    )


def render_activation_confirmation_released(
    *,
    confirmation_reference: str,
    contract_name: str,
    contract_code: str,
    customer_name: str,
    effective_date: datetime | None,
    confirmation_id: str,
    stored_document_id: str | None,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/activation-confirmations/{confirmation_id}")
    subj = (
        f"Contract change confirmation — {confirmation_reference}"
        if _lang(locale) == "en"
        else f"Confirmation de changement de contrat — {confirmation_reference}"
    )
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"Your contract {contract_name} ({contract_code}) has an activation confirmation available.",
                f"Votre contrat {contract_name} ({contract_code}) : une confirmation d'activation est disponible.",
            ),
            _L(locale, f"Reference: {confirmation_reference}", f"Référence : {confirmation_reference}"),
            _L(locale, f"Effective date: {_fmt_dt(effective_date)}", f"Date d'effet : {_fmt_dt(effective_date)}"),
            "",
            _L(locale, f"Review in the portal: {portal_url}", f"Consultation dans le portail : {portal_url}"),
            _L(locale, f"Support: {_portal_support_email()}", f"Assistance : {_portal_support_email()}"),
        ]
    )
    hints = {"portal_activation_confirmation": portal_url}
    if stored_document_id:
        hints["stored_document_id"] = stored_document_id
    return RenderedCommunication(
        subj,
        body,
        f"<p>{body.replace(chr(10), '<br/>')}</p>",
        {"confirmation_reference": confirmation_reference, "contract_code": contract_code},
        hints,
    )


def render_activation_confirmation_reminder(
    *,
    confirmation_reference: str,
    contract_code: str,
    customer_name: str,
    confirmation_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/activation-confirmations/{confirmation_id}")
    subj = (
        f"Reminder: please review {confirmation_reference}"
        if _lang(locale) == "en"
        else f"Rappel : veuillez consulter {confirmation_reference}"
    )
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"Please review activation confirmation {confirmation_reference} for {contract_code}.",
                f"Veuillez consulter la confirmation d'activation {confirmation_reference} pour le contrat {contract_code}.",
            ),
            portal_url,
        ]
    )
    return RenderedCommunication(
        subj,
        body,
        f"<p>{body.replace(chr(10), '<br/>')}</p>",
        {"confirmation_reference": confirmation_reference, "reminder": True},
        {"portal_activation_confirmation": portal_url},
    )


def render_activation_ack_follow_up(
    *,
    confirmation_reference: str,
    contract_code: str,
    customer_name: str,
    confirmation_id: str,
    locale: str | None = None,
) -> RenderedCommunication:
    portal_url = _portal(f"/activation-confirmations/{confirmation_id}")
    subj = (
        f"Reminder: acknowledgement for {confirmation_reference}"
        if _lang(locale) == "en"
        else f"Rappel : accusé de réception pour {confirmation_reference}"
    )
    body = "\n".join(
        [
            _L(locale, f"Dear {customer_name},", f"Bonjour {customer_name},"),
            "",
            _L(
                locale,
                f"Please confirm receipt of activation confirmation {confirmation_reference} ({contract_code}).",
                f"Veuillez confirmer la réception de la confirmation d'activation {confirmation_reference} ({contract_code}).",
            ),
            portal_url,
        ]
    )
    return RenderedCommunication(
        subj,
        body,
        f"<p>{body.replace(chr(10), '<br/>')}</p>",
        {"confirmation_reference": confirmation_reference, "follow_up": "acknowledgement"},
        {"portal_activation_confirmation": portal_url},
    )


def render_contract_follow_up_notice(
    *,
    contract_name: str,
    contract_code: str,
    internal_note: str,
    locale: str | None = None,
) -> RenderedCommunication:
    subj = (
        f"Internal: contract follow-up — {contract_code}"
        if _lang(locale) == "en"
        else f"Interne : suivi contrat — {contract_code}"
    )
    body = "\n".join(
        [
            _L(locale, f"Contract: {contract_name} ({contract_code})", f"Contrat : {contract_name} ({contract_code})"),
            "",
            internal_note,
        ]
    )
    return RenderedCommunication(
        subj,
        body,
        None,
        {"contract_code": contract_code, "internal": True},
        {},
    )
