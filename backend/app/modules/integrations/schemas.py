from __future__ import annotations

from pydantic import BaseModel


class GasSafeLookupIn(BaseModel):
    registration_number: str


class GasSafeLookupOut(BaseModel):
    provider: str
    registration_number: str
    engineer_name: str
    validity_until: str

