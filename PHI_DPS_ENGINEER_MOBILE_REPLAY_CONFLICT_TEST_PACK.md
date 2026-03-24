# Engineer mobile — replay & conflict test pack (Wave 7)

Automated coverage lives in `backend/tests/test_wave7_engineer_mobile_hardening.py` (run with project venv: `backend/.venv/bin/python -m pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v`).

## Automated scenarios (backend)

| # | Scenario | Expected |
|---|------------|----------|
| A1 | `POST /time/punch/in` twice with same body + same `Idempotency-Key` | Second response matches first; same `id` on `Punch`. |
| A2 | Same `Idempotency-Key`, **different** punch body (e.g. coordinates) | **409** conflict. |
| A3 | `POST /jobs/{id}/accept` twice with same key + body after first success | Second returns same logical success (cached or replay-safe accept). |
| A4 | Duplicate **form** submit (same normalized JSON `data`) | Second returns same submission `id` (dedup). |
| A5 | Media JSON over **2 MiB** | **413** request entity too large. |

## Manual / device scenarios (not all automated)

1. **Queued action replay after reconnect**  
   - Airplane mode → perform accept / punch / form (queued) → online → sync.  
   - Verify: single server-side effect; outbox marks completed; no duplicate rows in timesheet/job state.

2. **Duplicate signature / parts without idempotency key**  
   - Submit same signature JSON twice / same parts lines twice.  
   - Verify: duplicate signature returns stable requirement; duplicate parts payload does not double-reconcile lines (dedup path).

3. **409 conflict handling in app**  
   - Force same `Idempotency-Key` with altered body (e.g. edit payload in debugger).  
   - Verify: UI shows recoverable error; user can discard duplicate op or fix payload; outbox does not spin forever.

4. **Failed then retried submission**  
   - First attempt 500/timeout; retry with **same** idempotency key.  
   - Verify: eventual success without duplicate business rows when server had already succeeded (replay returns cached response).

5. **Accept-job replay**  
   - Accept job → navigate back → accept again (or replay from queue).  
   - Verify: **400** if terminal job; **403** if assigned to another engineer; **200** with stable job state if already accepted by same engineer.

6. **Punch sequencing**  
   - Punch in → punch in again (no out).  
   - Verify: **400** from server (“already punched in…”). Outbox should not create second `in` punch on retry of the *same* logical punch if idempotency key matches.

## Idempotency — documented limitations

- **Successful responses only** are recorded. Failed requests (4xx/5xx) are not cached; clients should retry with the **same** key for safe replay.
- **Concurrent first requests** with the same key can theoretically double-execute before either record commits; mobile retries after success are fully covered. Mitigation for a later phase: transactional “claim” row before work.

## Endpoints **not** given server idempotency in this wave

- High-volume or non-idempotent-by-design routes (e.g. **telemetry** fire-and-forget).
- **Admin/Dispatcher** bulk mutators where key semantics are unclear per resource.
- **Invoice/compliance generation** and similar multi-side-effect workflows — needs product-specific idempotency design before forcing keys.
