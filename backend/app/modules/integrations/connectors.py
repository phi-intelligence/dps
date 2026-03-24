from __future__ import annotations

from dataclasses import dataclass

from backend.app.modules.integrations.errors import IntegrationProviderError


@dataclass(frozen=True)
class GasSafeLookupResult:
    registration_number: str
    engineer_name: str
    validity_until: str


class GasSafeConnector:
    """
    Stub connector for Gas Safe register.
    """

    provider_name = "GasSafe"

    def lookup(self, *, registration_number: str) -> GasSafeLookupResult:
        # Dev behaviour: any registration_number ending with "FAIL" simulates provider error.
        if registration_number.upper().endswith("FAIL"):
            raise IntegrationProviderError(
                provider=self.provider_name,
                message="Gas Safe provider rejected the request",
                code="gas_safe_rejected",
            )

        return GasSafeLookupResult(
            registration_number=registration_number,
            engineer_name="Stub Engineer",
            validity_until="2030-01-01",
        )

