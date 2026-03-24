# PHI-DPS Engineer Mobile — staging / manual smoke run sheet

**Use:** one pass on **staging** API before internal pilot sign-off.  
**Tester:** ______________ **Date:** ______________ **Build:** ______________ **API base:** ______________

Check each row: **Pass** / **Fail** + short note if fail.

| # | Area | Preconditions | Steps | Pass? | Notes |
|---|------|---------------|-------|-------|-------|
| 1 | **Login** | Staging engineer account | Open app → enter creds → Login | | |
| 2 | **Jobs list** | Logged in | Jobs list loads; shows assigned work | | |
| 3 | **Job detail** | Job in list | Open a job; address/status visible | | |
| 4 | **Accept job** | Job assignable | Tap Accept → success or clear error | | |
| 5 | **Punch in** | Geofence OK, on site | Punch in → success | | |
| 6 | **Punch out** | Punched in | Punch out → success | | |
| 7 | **Form submit** | Form required on job | Fill required keys → submit → 200 / UI OK | | |
| 8 | **Signature** | Sig required | Capture/submit → success | | |
| 9 | **Media (<2 MiB)** | Photo requirement | Submit small payload (under cap) → success | | |
| 10 | **Parts** | Parts line + valid SKU | Submit lines → success or clear SKU error | | |
| 11 | **Sync / offline** | — | Airplane on → queue an action → off → sync drains / shows error | | |
| 12 | **Diagnostics** | — | Open diagnostics/settings → version, API URL, outbox counts visible | | |
| 13 | **Failure visibility** | Optional | Induce 400 (e.g. double punch in) → user sees message, not silent hang | | |
| 14 | **409 / conflict** | Optional harness | If testing: 409 shows readable message (idempotency misuse) | | |

**Fail capture:** screenshot of error + diagnostics screen + approximate time + job id.

**Sign-off:** Staging smoke **PASS** / **FAIL** — Name: ______________ Date: ______________
