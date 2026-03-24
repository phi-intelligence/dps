from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from backend.app.core.config import settings

DOC_DOWNLOAD_TYP = "phi_dps_doc_dl"


def create_document_download_token(
    *,
    document_id: str,
    context: str,
    customer_id: str | None,
    ttl_seconds: int | None = None,
) -> str:
    ttl = ttl_seconds if ttl_seconds is not None else int(settings.PHI_DPS_DOCUMENT_DOWNLOAD_TOKEN_TTL_SECONDS)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": document_id,
        "typ": DOC_DOWNLOAD_TYP,
        "ctx": context,
        "cid": customer_id,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_document_download_token(token: str) -> dict[str, Any]:
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if data.get("typ") != DOC_DOWNLOAD_TYP:
        raise JWTError("wrong token type")
    return data
