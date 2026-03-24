# Engineer mobile — field diagnostics & escalation playbook

For **support leads**, **field trial coordinators**, and **engineers** on pilot builds.

## When to use app diagnostics

- Sync stuck (“pending” never clears).
- Repeated errors after reconnect.
- Suspected **duplicate** or **missing** punch / job evidence.
- **Login** works on web but not app (wrong environment / clock / network).

**Collect:** app version, API base URL, last error codes from sync/outbox, approximate time of failure.

## Symptom → action

| Symptom | Likely cause | First action | Escalate when |
|---------|----------------|--------------|----------------|
| “Cannot login” / 401 | Wrong password, expired token, wrong API URL | Verify credentials; confirm pilot API URL in settings/diagnostics | After 2 failed attempts with known-good creds |
| Pending items never complete | Offline, server down, 4xx/5xx on specific op | Toggle network; open diagnostics; sync | Same op fails >3 times with same message |
| **409** | Idempotency key reused with **different** payload | Stop duplicate edits; discard duplicate queued op if safe; retry once with one consistent payload | Data loss suspected |
| **413** on media | JSON payload > **2 MiB** | Reduce photos per submit or resolution | Always if blocking completion |
| Geofence punch failure | Outside radius, bad GPS | Move to site; verify location services | GPS hardware failure on multiple sites |
| Duplicate punch worry | Double-tap / retry | Check timesheet in back office; server dedup + idempotency should prevent duplicates | Duplicate labour rows appear |
| Job “wrong engineer” | Assignment changed | Refresh job list; call dispatch | Security concern |

## Retry vs escalate

- **Retry (same idempotency key, same payload):** Transient **5xx**, timeout, flaky network after reconnect.
- **Do not blind-retry:** **400** validation errors (fix data first), **403** permission, **413** (reduce payload).
- **Escalate to engineering:** **409** loops, duplicate rows in payroll after “success”, any **crash** or **data mismatch** between app and office system.

## Pilot severity triage (release-control)

- **P0 (pilot-stop):** data loss/corruption, crash loop on core workflow, widespread login failure, unrecoverable duplicate payroll-impacting records.
- **P1 (same-day fix/mitigation):** repeated sync failure on critical actions, repeated media failures blocking normal job completion, assignment mismatch causing wrong access behavior.
- **P2:** recoverable defects with clear workaround.
- **P3:** cosmetic/polish issues.

Response policy:

1. P0 -> stop rollout expansion; hotfix required before resuming.
2. P1 -> continue only with named owner, mitigation, and same-day decision.
3. P2/P3 -> backlog unless change is zero-risk to pilot stability.

## Offline / reconnect checklist

1. Confirm connectivity (browser or speed test).
2. Open diagnostics — note pending count.
3. Tap sync / retry once; wait 30–60s.
4. If unchanged, capture screenshot (diagnostics + error) and **escalate** with time window.

## References

- `PHI_DPS_ENGINEER_MOBILE_MEDIA_UPLOAD_DECISION.md` — size limits.
- `PHI_DPS_ENGINEER_MOBILE_REPLAY_CONFLICT_TEST_PACK.md` — replay behavior.
