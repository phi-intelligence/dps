# PHI-DPS Engineer Mobile Capability Matrix

Legend:
- **Online supported**
- **Offline queued**
- **Best-effort only**
- **Blocked by backend**
- **Blocked by RBAC/policy**

## Engineer-visible actions

| Action | Classification | Notes |
|---|---|---|
| Login | Online supported | Requires API reachability and token issuance. |
| Logout | Online supported | Local token clear; no server dependency. |
| Jobs list (`GET /jobs`) | Online supported | Read-only, no offline cache-first UX yet. |
| Job detail (`GET /jobs/{id}`) | Online supported | Read-only fetch with refresh. |
| Job accept (`POST /jobs/{id}/accept`) | Online supported + Offline queued | Wave 6 `SyncCoordinator`; **Wave 7** server honors `Idempotency-Key`, replay-safe accept when already in engineer workflow. |
| Punch in (`POST /time/punch/in`) | Online supported + Offline queued | Client idempotency key; **Wave 7** server stores successful responses for keyed replays; **409** if key reused with different body. |
| Punch out (`POST /time/punch/out`) | Online supported + Offline queued | Same as punch in (Wave 7 server idempotency). |
| Telemetry (`POST /tracking/telemetry/engineer`) | Best-effort only | No persistence to outbox by design (high-volume signal). |
| Form submission | Online supported + Offline queued | **Wave 7:** server idempotency + duplicate normalized payload returns same submission row. |
| Signature submission | Online supported + Offline queued | **Wave 7:** server idempotency + duplicate signature JSON short-circuits. |
| Media/photo submission | Online supported (guarded) | Offline is blocked; **Wave 7** server rejects JSON body **> 2 MiB** with **413** (see media decision doc). |
| Parts usage submission | Online supported + Offline queued | **Wave 7:** server idempotency + duplicate payload short-circuits (no second reconciliation). |
| Engineer notes | Online supported + Offline queued | `POST /jobs/{id}/notes` exists with idempotency; mobile submits via sync coordinator and shows in activity timeline. |
| Certificates/compliance artifacts | Blocked by RBAC/policy | Current certificate endpoints are Admin/Dispatcher only for engineer flow. |
| Sync diagnostics screen | Online supported + local | Reads local outbox + triggers sync/retry controls. |
| App diagnostics/settings screen | Online supported + local | Shows app/version/config/session/sync status details. |
| Open in maps | Online supported | External app handoff. |

## Policy summary by write path

| Write path | Policy |
|---|---|
| Punch / Accept / Forms / Signature / Parts | Try-now-then-queue |
| Telemetry | Best-effort only (no persist) |
| Media | Online-first with offline block and size guard |

## Remaining blocked capabilities

- Engineer-safe certificate/compliance retrieval/upload endpoints.
- **Large-object upload** beyond JSON/base64 MVP (presigned/multipart — see `PHI_DPS_ENGINEER_MOBILE_MEDIA_UPLOAD_DECISION.md`).
- **Concurrent first-send** idempotency race (same key, simultaneous requests) — documented limitation; retries after first success are safe.
