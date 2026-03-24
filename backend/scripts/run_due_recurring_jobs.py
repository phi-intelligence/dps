#!/usr/bin/env python3
"""
Run due recurring system jobs once (§5.8).

Production: schedule with cron (e.g. every 5–15 minutes). Use **one runner per environment**
(concurrencyPolicy Forbid, advisory lock, or a single VM) — see DEPLOYMENT.md § "Recurring jobs".

  From repository root (directory that contains the `backend` package):

    PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py --limit 10
    PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py --limit 20 --actor-email ops@example.com

Default actor: first match for ``admin@example.com``, else ``None`` (jobs still run).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run due PHI-DPS recurring system jobs once.",
        epilog="Full ops notes: DEPLOYMENT.md (Recurring jobs §5.8). API alternative: POST /system/jobs/run-due",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max jobs to run this invocation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry_run=True for every job (no mutations)",
    )
    parser.add_argument(
        "--actor-email",
        default=os.getenv("PHI_DPS_RECURRING_JOBS_ACTOR_EMAIL"),
        help="User email to attribute runs to (default: env PHI_DPS_RECURRING_JOBS_ACTOR_EMAIL or admin@example.com)",
    )
    args = parser.parse_args()

    if not os.getenv("PHI_DPS_DATABASE_URL"):
        print("PHI_DPS_DATABASE_URL is not set.", file=sys.stderr)
        return 2

    from backend.app.db.session import SessionLocal
    from backend.app.modules.auth.models import User
    from backend.app.services import recurring_job_runner_service as rjr

    db = SessionLocal()
    try:
        actor_id = None
        requested = (args.actor_email or "").strip()
        email = requested or "admin@example.com"
        actor = db.query(User).filter(User.email == email).first()
        if actor:
            actor_id = actor.id
        elif requested:
            print(f"No user with email {email!r}; runs will have null actor.", file=sys.stderr)
        runs = rjr.run_due_jobs(
            db,
            limit=args.limit,
            dry_run_override=True if args.dry_run else None,
            actor_user_id=actor_id,
            commit=True,
        )
        print(f"Executed {len(runs)} job run(s).")
        for run in runs:
            print(f"  - {run.job_key} -> {run.status} (dry_run={run.dry_run})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
