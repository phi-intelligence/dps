"""§5.14 — record break-glass overrides with mandatory reason text."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.modules.system.break_glass_models import BreakGlassOverrideAudit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


MIN_BREAK_GLASS_REASON_LEN = 12


def _dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), default=str)


def record_break_glass_override(
    db: Session,
    *,
    actor_user_id: str | None,
    override_kind: str,
    target_type: str,
    target_id: str,
    reason: str,
    metadata: dict[str, Any] | None = None,
    commit: bool = False,
) -> BreakGlassOverrideAudit:
    r = (reason or "").strip()
    if len(r) < MIN_BREAK_GLASS_REASON_LEN:
        raise ValueError(
            f"Break-glass reason must be at least {MIN_BREAK_GLASS_REASON_LEN} characters (audit requirement §5.14)"
        )
    row = BreakGlassOverrideAudit(
        id=str(uuid.uuid4()),
        actor_user_id=actor_user_id,
        override_kind=override_kind.strip(),
        target_type=target_type.strip(),
        target_id=target_id.strip(),
        reason=r[:8000],
        metadata_json=_dumps(metadata) if metadata else None,
        created_at=utc_now(),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row
