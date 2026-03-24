# PHI-DPS Engineer Mobile — UAT scenarios (Wave 7)

Execute on **staging** or **pilot** API with a real engineer test account.

## 1. Login & session failures

| Step | Action | Pass criteria |
|------|--------|----------------|
| 1.1 | Wrong password | Clear error; no partial sync. |
| 1.2 | Valid login | Token stored; jobs load. |
| 1.3 | Token invalidated server-side (if testable) | User prompted to re-login; no silent 401 loop. |

## 2. Offline / reconnect

| Step | Action | Pass criteria |
|------|--------|----------------|
| 2.1 | Offline: open assigned job | Cached or error is explicit (no blank screen). |
| 2.2 | Offline: queue accept + punch + form | Items appear in pending outbox. |
| 2.3 | Online: sync | Items complete; job/timesheet state consistent. |
| 2.4 | Replay same op after success | No duplicate punch rows / duplicate form rows (idempotency + dedup). |

## 3. Pending / failed / conflict actions

| Step | Action | Pass criteria |
|------|--------|----------------|
| 3.1 | Induce 400 (e.g. punch in twice) | Outbox marks failed or user can clear; message explains rule. |
| 3.2 | Induce 409 (reuse idempotency key with different body in test harness) | User sees conflict; can escalate or discard per policy. |
| 3.3 | Retry after transient 5xx | Same idempotency key succeeds without duplicate effect. |

## 4. Geofence

| Step | Action | Pass criteria |
|------|--------|----------------|
| 4.1 | Punch inside fence | Success. |
| 4.2 | Punch outside fence (where enforced) | Rejected with geofence message; engineer knows to move or contact dispatch. |

## 5. Media upload

| Step | Action | Pass criteria |
|------|--------|----------------|
| 5.1 | Submit ≤2 MiB JSON payload | Success path. |
| 5.2 | Oversize payload | **413** or client block before send; user told to reduce photos/quality. |

## 6. Accept job

| Step | Action | Pass criteria |
|------|--------|----------------|
| 6.1 | Accept assigned job | Status moves to accepted; appears in workflow. |
| 6.2 | Replay accept (sync retry) | **200** stable; no duplicate side effects. |
| 6.3 | Accept completed/cancelled job | **400**; message clear. |

## 7. Diagnostics

| Step | Action | Pass criteria |
|------|--------|----------------|
| 7.1 | Open diagnostics / sync screen | Version, API base, session, outbox counts visible. |
| 7.2 | Force sync | Completes without crash; counts update. |

## Sign-off

Tester: ______________  Date: ______________  Build: ______________
