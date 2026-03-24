from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CertificateGenerateIn(BaseModel):
    job_id: str
    certificate_type: str


class CertificateOut(BaseModel):
    id: str
    job_id: str
    site_id: str | None = None
    asset_id: str | None = None
    contract_id: str | None = None
    certificate_type: str
    status: str
    engineer_user_id: str | None
    signed_by_engineer: bool
    signed_by_client: bool
    created_at: datetime

    model_config = {"from_attributes": True}

