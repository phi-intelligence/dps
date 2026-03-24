# PHI-DPS Engineer Mobile — Final Release Control Plan

## 1) Current release status

- Current status: **limited field pilot ready**.
- Internal pilot baseline capabilities are complete and validated on mobile checks (`flutter analyze`, `flutter test`) in current environment.
- Broader rollout is still blocked primarily by media scalability risk under large real-world evidence volumes.

## 2) What is complete

- Core engineer workflow (auth, jobs, accept, punch, forms/signature/media/parts, sync/outbox, diagnostics).
- Wave 7+ hardening (idempotency on critical writes, replay/conflict guards, media limit enforcement).
- Wave 8/9/10 operator experience and field completeness improvements.
- Wave 11 production hardening pass (media batching/planning improvements + diagnostics/support snapshot improvements).
- Wave 11b phase-2 preparation:
  - feature flag `engineer_media_phase2_enabled`
  - media capability endpoint
  - upload-session + commit skeleton endpoints
  - mobile conditional branch with safe fallback to legacy media flow

## 3) What is pilot-ready

For limited field pilot:

- Legacy media flow (`POST /jobs/{id}/media`) remains stable and compatible.
- New media phase-2 path exists behind feature flag and can be selectively enabled in controlled cohorts.
- Support runbook and diagnostics surfaces are sufficient for pilot triage and escalation.

## 4) What remains blocked for broader rollout

- Full large-object media transport (presigned/object-upload commit path) is not yet complete.
- Need field evidence that media failure rates under pilot thresholds are acceptable (or phase-2 full transport delivered).
- Need production soak evidence for phase-2 session lifecycle behavior if enabled for any cohort.

## 5) How media Phase 2 affects rollout decisions

- Phase 2 **reduces rollout risk** by enabling a controlled dual-path migration.
- It does **not** by itself remove the broader-rollout blocker yet, because MVP phase-2 commit still uses JSON payloads.
- Rollout decision impact:
  - limited pilot: proceed with legacy default; optional selective phase-2 enablement
  - broader rollout: require either (a) acceptable media error metrics with legacy+controls, or (b) full object-upload phase-2 completion

## 6) Exact limited field pilot execution steps

1. **Freeze candidate build**
   - Tag pilot candidate and lock release branch for controlled changes only.
2. **Pre-pilot gates**
   - Run mobile checks and backend hardening suite in CI-compatible environment.
   - Confirm API base URL + account roster + support channel.
3. **Pilot day 0 smoke**
   - Execute staging smoke sheet and UAT critical scenarios.
4. **Pilot cohort enablement**
   - Start with legacy media path for all pilot users.
   - If needed, enable `engineer_media_phase2_enabled` in staging first, then for a small pilot subset.
5. **Daily operations cadence**
   - Track: 413 rate, media retries, sync failed/conflict rows, assignment/punch defects.
   - Capture support snapshots from diagnostics for every P0/P1 issue.
6. **Change-control checkpoint (daily)**
   - Triage defects by severity and decide: hotfix now, queue for post-pilot, or defer.
7. **Pilot exit review**
   - Compare defect trend against go/no-go thresholds.
   - Decide expand/hold based on reliability and support load.

## 7) Bug triage rules during pilot

Severity definitions:

- **P0 (pilot-stop):**
  - data loss/corruption
  - duplicate payroll-impacting punches not recoverable
  - widespread login/session failure
  - crash loops blocking core workflow
- **P1 (same-day fix or mitigation):**
  - repeated sync failure/conflict on critical actions
  - media submission failure blocking completion for normal jobs
  - assignment mismatch causing wrong job access behavior
- **P2 (next patch window):**
  - recoverable UX defects with workaround
  - non-blocking diagnostics/display issues
- **P3 (backlog):**
  - low-impact polish

Pilot triage actions:

- P0: halt rollout expansion, hotfix required.
- P1: allow pilot continuation only with mitigation + owner + ETA.
- P2/P3: document and schedule; do not destabilize pilot branch.

## 8) Release-control rules

### What is frozen

- API contracts used by current mobile clients (`/jobs/{id}/media` legacy flow especially).
- Core write-path behavior and idempotency semantics.
- Outbox/sync semantics during active pilot window.

### What can still change

- Documentation, runbooks, pilot procedures.
- Targeted bug fixes that reduce pilot risk (P0/P1 only).
- Feature-flag configuration and scoped enablement rules.
- Diagnostics/readability improvements that do not alter core contracts.

### What must wait

- Broad architecture redesigns.
- Full media transport replacement across all users without staged evidence.
- Non-critical feature expansion unrelated to pilot reliability/support.

## 9) Media-flow recommendation for pilot

Recommendation for this pilot window:

- **Keep old media flow as default for all pilot users.**
- **Enable new Phase 2 path only for selected users/environments** if specific media reliability issues appear and support coverage is active.
- Do not force full cutover during limited pilot.

Rationale:

- Lowest operational risk while preserving an immediate controlled experiment path.
- Maintains backward compatibility and fast rollback via feature flag.

## 10) Final release recommendation (current)

- **Internal pilot only:** passed previously.
- **Limited field pilot:** **ready** with release-control discipline in this plan.
- **Broader rollout:** **not ready** until media risk is closed by evidence or full phase-2 transport completion.
