# PHI-DPS Engineer Mobile — Media Phase 2 Plan (Wave 11b)

## 1) Current contract and blocker

Current engineer media submission uses:

- `POST /jobs/{id}/media`
- JSON payload with base64 media (`payloads`)
- server hard limit: 2 MiB request body
- mobile preflight batching/compression to stay within cap

Why this is the main broader-rollout blocker:

- base64 JSON inflates payload size and is fragile on weaker networks
- larger real-world evidence packs require many retries/splits
- high-volume field usage increases 413 failures and support effort
- current flow is reliable for limited pilot but does not scale cleanly for broader rollout

## 2) Phase 2 objective

Introduce a **backward-compatible**, **feature-flagged** path that can be enabled gradually without breaking current clients.

Constraints:

- existing `/jobs/{id}/media` must continue to work unchanged
- new path must be modular and low-risk
- rollout must be selective and reversible

## 3) Candidate patterns and recommendation

Evaluated patterns:

1. upload session + commit
2. multipart upload
3. presigned upload

Recommended now: **upload session + commit (foundation first)**.

Why:

- fits current backend architecture and idempotency model
- allows incremental migration toward presigned/multipart later
- can be introduced as a no-break thin vertical slice
- supports staged controls (session expiry, ownership, commit audit)

Presigned/multipart remains the likely end-state for large-object scale, but session+commit is the safest immediate Wave 11b MVP step.

## 4) Proposed Phase 2 contract (MVP first)

New endpoints (feature-flag-gated):

- `GET /jobs/media/capabilities`
  - tells client if phase2 is enabled for this environment
- `POST /jobs/{job_id}/media/upload-sessions`
  - creates upload session (owner, expiry, media type)
- `POST /jobs/{job_id}/media/upload-sessions/{session_id}/commit`
  - commits media payloads for that session

MVP commit transport:

- still accepts JSON payloads to avoid big redesign
- routes through session lifecycle first
- keeps legacy endpoint untouched

Next step after MVP:

- swap commit payload from inline base64 to uploaded object references (presigned path)

## 5) Backend changes

- add runtime feature flag: `engineer_media_phase2_enabled`
- add model: `JobMediaUploadSession` (open/committed/expired, owner, expiry)
- add capability endpoint for mobile branch decision
- add session create + session commit endpoints
- keep existing `/jobs/{id}/media` fully intact

## 6) Mobile changes

- add capability check before media submit
- if phase2 enabled:
  - create upload session
  - commit via session endpoint
- if disabled or unavailable:
  - use existing legacy `/jobs/{id}/media` flow

## 7) Rollout and feature flag strategy

Default:

- `engineer_media_phase2_enabled = false`

Rollout:

1. enable in staging only
2. enable for selected pilot environment/team
3. observe error rates and support tickets
4. expand rollout only after stability threshold passes

## 8) Migration strategy

1. Ship dual-path backend + mobile branching.
2. Keep old clients on legacy flow.
3. Enable new path progressively via feature flag.
4. Once proven, move phase2 commit payload to object references (presigned uploads).
5. Deprecate legacy JSON path only after explicit adoption and risk sign-off.

## 9) Fallback behavior

- if capability endpoint fails: client falls back to legacy flow
- if session create/commit fails under phase2: client reports actionable error and can retry
- feature flag can be turned off immediately to return all traffic to legacy flow

## 10) Testing strategy

Backend:

- capability endpoint returns phase2 disabled by default
- enabled flag allows session creation/commit
- session ownership and expiry checks enforced
- idempotent commit behavior validated
- legacy `/jobs/{id}/media` regression tests remain green

Mobile:

- when phase2 disabled: legacy flow used
- when phase2 enabled: session+commit path used
- on capability/session failure: safe fallback to legacy path

## 11) Risks

- dual-path complexity (legacy + phase2) until migration completes
- session lifecycle edge cases (expired/replayed/owner mismatch)
- without presigned object upload, payload inflation still exists in MVP

Mitigation:

- keep scope narrow and feature-flagged
- preserve existing known-good path
- add clear diagnostics and staged rollout

## 12) Definition of done (Wave 11b MVP)

- phase2 feature flag exists and defaults off
- capability endpoint exists
- upload session + commit endpoints exist and are guarded by feature flag
- mobile can detect and use phase2 only when enabled
- legacy clients and endpoint continue working unchanged
- analyze/tests pass for touched mobile modules and no backend contract regressions introduced
