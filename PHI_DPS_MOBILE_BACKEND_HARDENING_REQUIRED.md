# PHI-DPS Mobile Backend Hardening Required

Only items that now directly block full production readiness for the engineer mobile app.

## 1) Server-side idempotency enforcement
- **Status (Wave 7):** **Implemented** for engineer-critical writes: `POST /time/punch/in`, `POST /time/punch/out`, `POST /jobs/{id}/accept`, `POST .../forms/{form_key}/submit`, `POST .../signature`, `POST .../media`, `POST .../parts-usage`. Table: `api_idempotency_records` (`ApiIdempotencyRecord`).
- **Replay semantics:** Same user + scope + `Idempotency-Key` + same canonical request body → returns stored JSON **success** response; different body → **409**.
- **Residual risk:** Concurrent **first** requests with the same key may still double-execute (see `PHI_DPS_ENGINEER_MOBILE_REPLAY_CONFLICT_TEST_PACK.md`).

## 2) Duplicate punch-in / punch-out protection
- **Status (Wave 7):** **Implemented** in `time_tracking` service (sequence validation) + punch routes now persist **successful** idempotent responses for keyed retries.
- **Follow-up:** None required for pilot unless new edge cases appear in field data.

## 3) Media upload contract hardening
- **Status (Wave 7):** **Partially** — server enforces **2 MiB** max JSON body on `POST .../media` (**413**); MVP decision documented in `PHI_DPS_ENGINEER_MOBILE_MEDIA_UPLOAD_DECISION.md`.
- **Follow-up:** Presigned/multipart upload when pilots exceed JSON limits or need offline bulk.

## 4) Engineer-safe notes endpoint
- **Issue:** No engineer write endpoint for job notes.
- **Affected endpoint/service/model:** Dispatch/job notes API surface (missing endpoint/model path).
- **Why mobile needs it:** Required action is visible in engineer UI but cannot be completed.
- **Priority:** **P1**
- **Safe to implement immediately:** **Yes** if scoped to simple append-only note with job-assignment checks.

## 5) SKU lookup/search API for engineer parts entry
- **Issue:** Parts usage requires exact SKU strings; mobile has no lookup/search.
- **Affected endpoint/service/model:** Inventory catalog read/search endpoint for engineer role.
- **Why mobile needs it:** Reduces failed submissions and support load from manual SKU entry.
- **Priority:** **P1**
- **Safe to implement immediately:** **Yes** with read-only filtered search endpoint.

## 6) Stronger status transition validation
- **Status (Wave 7):** **Partially** — engineer `POST /jobs/{id}/accept` rejects **terminal** jobs (`completed`, `cancelled`) and supports **replay-safe** behavior when the same engineer has already progressed (`accepted`, `on_site`, `en_route`, `completion_pending_forms`). Broader workflow FSM is still a future hardening pass.
