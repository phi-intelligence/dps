from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class QualificationCreateIn(BaseModel):
    engineer_user_id: str
    competency: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    document_ref: str | None = None


class QualificationOut(BaseModel):
    id: str
    engineer_user_id: str
    competency: str
    issued_at: datetime | None
    expires_at: datetime | None
    document_ref: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class QualificationValidityOut(BaseModel):
    competency: str
    valid: bool
    expires_at: datetime | None

