#!/usr/bin/env python3
"""
Deployment environment sanity checks (§5.6).

Load variables into the process environment first (e.g. `set -a && source .env && set +a`
or your orchestrator's secret injection), then run:

  PYTHONPATH=. python backend/scripts/check_deploy_env.py
  PYTHONPATH=. python backend/scripts/check_deploy_env.py --strict   # exit 1 if any issue
"""
from __future__ import annotations

import argparse
import os
import sys


def _collect_issues(*, strict: bool = False) -> list[str]:
    issues: list[str] = []

    sk = os.getenv("PHI_DPS_SECRET_KEY", "")
    if not sk or sk in ("dev-secret-change-me", "change-me") or "change-me" in sk.lower():
        issues.append("PHI_DPS_SECRET_KEY is missing or looks like a placeholder")

    if os.getenv("PHI_DPS_DEV_BOOTSTRAP", "1") == "1":
        issues.append("PHI_DPS_DEV_BOOTSTRAP=1 seeds default users on startup — set 0 in production")

    nws = os.getenv("PHI_DPS_NOTIFICATION_WEBHOOK_SECRET", "")
    if not nws or nws in ("dev-webhook-secret", "change-me-webhook-secret"):
        issues.append("PHI_DPS_NOTIFICATION_WEBHOOK_SECRET is missing or looks like a dev default")

    cws = os.getenv("PHI_DPS_COMMUNICATION_WEBHOOK_SECRET", "")
    if not cws or cws == "dev-comm-webhook-secret":
        issues.append("PHI_DPS_COMMUNICATION_WEBHOOK_SECRET is missing or looks like a dev default")

    if os.getenv("PHI_DPS_ROLLOUT_RUNNER_ENABLED", "0") == "1":
        issues.append(
            "PHI_DPS_ROLLOUT_RUNNER_ENABLED=1 starts an in-process rollout loop — usually 0 for production API replicas"
        )

    if strict:
        portal = os.getenv("PHI_DPS_PORTAL_WEB_BASE", "").strip().lower()
        if portal and ("127.0.0.1" in portal or "localhost" in portal):
            issues.append(
                "PHI_DPS_PORTAL_WEB_BASE points at localhost — customer email/PDF links will be wrong in real deployments"
            )
        if not (os.getenv("PHI_DPS_CORS_ORIGINS") or "").strip():
            issues.append(
                "PHI_DPS_CORS_ORIGINS unset — API defaults to localhost dev origins; set explicit admin web URL(s) for production"
            )

    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="PHI-DPS deploy env checks")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any warning is reported (for CI / pre-flight)",
    )
    args = p.parse_args()
    issues = _collect_issues(strict=args.strict)
    for msg in issues:
        print(f"WARN: {msg}", file=sys.stderr)
    if not issues:
        print("OK: no common deployment warnings detected (still review .env.example and DEPLOYMENT.md).")
    return 1 if args.strict and issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
