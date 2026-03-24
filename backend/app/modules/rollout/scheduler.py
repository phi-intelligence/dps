from __future__ import annotations

import os
import threading
import time
from typing import Any

from backend.app.db.session import SessionLocal
from backend.app.modules.rollout.service import run_scheduled_rollout_cycle


def rollout_runner_enabled() -> bool:
    return os.getenv("PHI_DPS_ROLLOUT_RUNNER_ENABLED", "0") == "1"


def run_rollout_cycle_once(*, force: bool = False) -> dict[str, Any]:
    db = SessionLocal()
    try:
        return run_scheduled_rollout_cycle(db, force=force)
    finally:
        db.close()


def start_rollout_scheduler_background() -> threading.Thread | None:
    """
    Lightweight dev/staging scheduler:
    - disabled by default
    - enabled via PHI_DPS_ROLLOUT_RUNNER_ENABLED=1
    """
    if not rollout_runner_enabled():
        return None

    sleep_seconds = int(os.getenv("PHI_DPS_ROLLOUT_RUNNER_SLEEP_SECONDS", "30"))
    sleep_seconds = max(sleep_seconds, 5)

    def _loop() -> None:
        while True:
            try:
                run_rollout_cycle_once(force=False)
            except Exception:
                # Best-effort background loop; never crash the process.
                pass
            time.sleep(sleep_seconds)

    thread = threading.Thread(target=_loop, name="phi-dps-rollout-runner", daemon=True)
    thread.start()
    return thread

