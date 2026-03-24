# PHI-DPS Engineer Mobile — Wave 11 Media Hardening Decision

## Decision

For this Wave 11 pass, keep the existing backend media contract (`POST /jobs/{id}/media` JSON/base64, 2 MiB hard limit) and implement a safer mobile-side production hardening step:

- stronger capture presets (high/balanced/small-data)
- preflight batch planning
- automatic submission in smaller batches
- explicit progress and remediation messaging

This is the safest low-risk production step because it avoids backend storage/transport migration risk late in rollout while reducing the highest pilot pain point (413/large payload failures).

## Why not full media phase 2 in this pass

Full multipart/presigned migration is a larger contract change that requires:

- upload session creation and expiry rules
- object-store integration and lifecycle cleanup
- metadata commit/finalize API
- stronger audit/eventing around partial uploads
- retry and orphan handling across mobile/backend

These changes are valid for broader rollout but are too large for a low-risk hardening pass without dedicated soak time.

## Trigger for phase 2 (objective)

Escalate to media phase 2 when any of these conditions hold for pilot/field telemetry over a 7-day rolling window:

1. media failure rate > 3% of submission attempts
2. 413 responses > 1% of media submissions
3. repeated engineer-reported inability to complete evidence due to payload size in more than 5 jobs/week

## Planned phase 2 contract (next step)

1. `POST /jobs/{id}/media/upload-sessions` -> returns upload session id + per-file presigned URLs.
2. Mobile uploads files directly to object store with progress.
3. `POST /jobs/{id}/media/commit` finalizes metadata + audit record + requirement reconciliation.
4. Keep current JSON endpoint as fallback behind feature flag during cutover.

## Rollout recommendation for this decision

- internal pilot: acceptable
- limited field pilot: acceptable with monitoring of 413 and media retries
- broader rollout: acceptable only if trigger thresholds remain below limits; otherwise execute phase 2
