from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from backend.app.core.config import settings


# Use a hash scheme that works reliably in dev environments without native deps.
# (We can move to bcrypt/argon2 in Phase 4 hardening once the toolchain is stable.)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str, roles: list[str]) -> str:
    # Use effective runtime setting so admin can adjust token expiry without restart.
    from backend.app.services.runtime_settings_service import get_effective_security_settings

    expire_minutes = int(get_effective_security_settings(None).get("access_token_expire_minutes", settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "roles": roles,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

