from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import require_roles
from backend.app.modules.integrations.connectors import GasSafeConnector
from backend.app.modules.integrations.errors import IntegrationError
from backend.app.modules.integrations.schemas import GasSafeLookupIn, GasSafeLookupOut


router = APIRouter(prefix="/integrations", tags=["integrations"])


def integration_error_to_http(err: IntegrationError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"provider": err.provider, "code": err.code, "message": err.message},
    )


@router.post("/gas-safe/lookup", response_model=GasSafeLookupOut)
def gas_safe_lookup(
    payload: GasSafeLookupIn,
    _user=Depends(require_roles("Admin", "Dispatcher")),
) -> GasSafeLookupOut:
    connector = GasSafeConnector()
    try:
        res = connector.lookup(registration_number=payload.registration_number)
        return GasSafeLookupOut(
            provider=connector.provider_name,
            registration_number=res.registration_number,
            engineer_name=res.engineer_name,
            validity_until=res.validity_until,
        )
    except IntegrationError as e:
        raise integration_error_to_http(e) from e

