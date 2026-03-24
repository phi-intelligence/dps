from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.modules.auth.models import User
from backend.app.modules.crm.schemas import (
    CustomerCommunicationPreferenceCreateIn,
    CustomerCommunicationPreferenceOut,
    CustomerCommunicationPreferencePatchIn,
)
from backend.app.services.authorization_policy import (
    CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE,
    CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION,
)
from backend.app.services.authorization_service import require_permission_http
from backend.app.services import communication_recipient_suppression_service as comm_hygiene
from backend.app.services import customer_communication_preference_service as pref_svc

router = APIRouter(prefix="/customers", tags=["customers"])


def _require_view_commercial_prefs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_VIEW_CONTRACT_CUSTOMER_COMMUNICATION, db=db)
    return current_user


def _require_manage_prefs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    require_permission_http(current_user, CAN_MANAGE_CUSTOMER_COMMUNICATION_PREFERENCE, db=db)
    return current_user


@router.get(
    "/{customer_id}/communication-preferences",
    response_model=list[CustomerCommunicationPreferenceOut],
)
def list_customer_communication_preferences_endpoint(
    customer_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_commercial_prefs),
) -> list[CustomerCommunicationPreferenceOut]:
    try:
        rows = pref_svc.list_preferences_for_customer(db, customer_id=customer_id)
        return [CustomerCommunicationPreferenceOut.model_validate(r) for r in rows]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{customer_id}/communication-preferences",
    response_model=CustomerCommunicationPreferenceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_communication_preference_endpoint(
    customer_id: str,
    payload: CustomerCommunicationPreferenceCreateIn,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_manage_prefs),
) -> CustomerCommunicationPreferenceOut:
    try:
        row = pref_svc.create_preference(
            db,
            customer_id=customer_id,
            channel=payload.channel,
            enabled=payload.enabled,
            contact_reference=payload.contact_reference,
            preferred=payload.preferred,
            quiet_hours_start=payload.quiet_hours_start,
            quiet_hours_end=payload.quiet_hours_end,
            timezone_name=payload.timezone_name,
            notes=payload.notes,
            commit=True,
        )
        return CustomerCommunicationPreferenceOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.patch(
    "/communication-preferences/{preference_id}",
    response_model=CustomerCommunicationPreferenceOut,
)
def patch_customer_communication_preference_endpoint(
    preference_id: str,
    payload: CustomerCommunicationPreferencePatchIn,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_manage_prefs),
) -> CustomerCommunicationPreferenceOut:
    try:
        row = pref_svc.patch_preference(
            db,
            preference_id=preference_id,
            enabled=payload.enabled,
            contact_reference=payload.contact_reference,
            preferred=payload.preferred,
            quiet_hours_start=payload.quiet_hours_start,
            quiet_hours_end=payload.quiet_hours_end,
            timezone_name=payload.timezone_name,
            notes=payload.notes,
            commit=True,
        )
        return CustomerCommunicationPreferenceOut.model_validate(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{customer_id}/communication-safety")
def customer_communication_safety_endpoint(
    customer_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(_require_view_commercial_prefs),
) -> dict:
    try:
        return comm_hygiene.communication_safety_for_customer(db, customer_id=customer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
