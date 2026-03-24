from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EtlRunOut(BaseModel):
    snapshot_id: str
    snapshot_date: str


class DashboardOut(BaseModel):
    snapshot_date: str | None
    data: dict[str, Any]

