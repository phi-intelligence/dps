from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.audit.models import AuditLog


def create_audit_log(
    db: Session,
    *,
    actor_user_id: str | None,
    method: str,
    path: str,
    status_code: int,
    action: str | None = None,
) -> None:
    # Keep this intentionally lightweight: audit data is best-effort and should not block the response.
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            method=method,
            path=path,
            status_code=status_code,
            action=action,
        )
    )

    # Caller can decide whether to commit; for middleware we do a small best-effort commit.
    # We do not expose commit flag to avoid accidental missing commits elsewhere.
    db.commit()

