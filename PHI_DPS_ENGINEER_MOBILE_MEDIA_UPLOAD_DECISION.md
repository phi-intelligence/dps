# Engineer mobile — media upload decision (Wave 7)

## Current contract

- **Transport:** `POST /jobs/{job_id}/media` with JSON body (`JobMediaSubmitIn`: `media_type`, `payloads[]` of arbitrary JSON objects, typically base64 photo blobs).
- **Server validation (Wave 7):** Rejects requests when the **canonical JSON serialization** of the body exceeds **2,097,152 bytes (2 MiB)** with HTTP **413** and a clear error message. Constant: `ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES` in `backend/app/modules/dispatch/engineer_mobile_constants.py` (aligned with the mobile client’s JSON size guard: `kMaxQueuedMediaPayloadBytes` in `mobile/lib/core/sync/sync_coordinator.dart`, asserted in `mobile/test/sync_media_limit_alignment_test.dart`).

## Recommendation for MVP / pilot

**Keep the JSON/base64 path** with documented limits for the **internal / limited field pilot**.

| Aspect | Decision |
|--------|----------|
| **MVP** | Keep JSON/base64; enforce **2 MiB** cap server-side; return **413** when exceeded. |
| **Risk** | Large photos, retries, and concurrent uploads can stress memory and JSON parse time; base64 inflates size ~4/3. |
| **Mitigation (short term)** | Client-side compression/resolution caps (already assumed in mobile policy); engineer training to limit photos per submit; monitor 413 rates. |
| **Follow-up (not in Wave 7)** | Safer production pattern: **presigned URL / multipart upload** to object storage with small JSON metadata POST — requires infra and mobile contract change; document as Phase 2. |

## Exact limits

- **Maximum JSON body (server):** **2 MiB** per `POST /jobs/{id}/media` request (serialized JSON length in UTF-8).
- **Idempotency:** Same as other engineer writes — `Idempotency-Key` honored; replays return the stored success response; conflicting body under same key → **409**.

## When to escalate to multipart/presigned

- Pilots show **frequent 413** or **timeout** on media.
- Need **offline queue of large blobs** without holding multi‑MiB JSON in SQLite.
- Security/compliance requires **virus scan or content-type validation** at upload edge.
