# Wave 5 — Offline queue & sync policy

## Operation policies

| Action | Policy | Persistence |
|--------|--------|-------------|
| Punch in / out | **Try-now-then-queue** | Drift outbox on offline or recoverable network failure |
| Accept job | **Try-now-then-queue** | Drift outbox on offline or recoverable network failure |
| Form submit | **Try-now-then-queue** | Same |
| Signature | **Try-now-then-queue** | Same |
| Parts usage | **Try-now-then-queue** | Same |
| Media (JSON base64) | **Online-only submit**; recoverable failure queues **only if** payload ≤ `kMaxQueuedMediaPayloadBytes` (2 MiB) | **Blocked** when offline (no blind queue of huge base64 blobs) |
| Telemetry (`POST /tracking/telemetry/engineer`) | **Best-effort, no persist** | Not written to outbox (avoid flooding; optional future compaction) |

## Idempotency

- Each queued row stores a unique `idempotency_key` (UUID v4).
- [IdempotencyInterceptor](../lib/core/network/idempotency_interceptor.dart) sends `Idempotency-Key` on replay.
- Backend may ignore the header until Wave 6+ server support; keys remain for forward compatibility.

## Sync engine

- Sequential processing, mutex to prevent concurrent runs.
- Exponential backoff per row (`attemptCount`), max 12 attempts → `failed`.
- HTTP 409 → `conflict` (no endless retry).
- Client 4xx (except 408/429) → `failed` immediately where classified non-recoverable.
- Rows deleted on 2xx; `last_engine_sync_utc` stored in `sync_metadata`.

## Triggers

- App start (post-frame), every 45s while app open, connectivity changes, after enqueue, manual “Sync” on diagnostics screen.

## Wave 6+ ideas

- Server-side idempotency storage keyed by header.
- Multipart / presigned media + durable offline media queue.
- Telemetry ring buffer or batched compact queue.
- Extend idempotent semantics server-side for queued accept and evidence writes.
