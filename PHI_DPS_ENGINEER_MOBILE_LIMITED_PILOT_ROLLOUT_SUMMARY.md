# PHI-DPS Engineer Mobile — Limited Pilot Rollout Summary

## 1. Executive summary

The PHI-DPS engineer mobile app has reached a stable level suitable for **limited field pilot rollout**. Core field workflows are implemented and hardened, including replay-safe write paths, offline/sync support patterns, and operator diagnostics.

Current status:

- **Release status:** limited field pilot ready (under release-control rules)
- **Pilot recommendation:** proceed with controlled limited field pilot
- **Broader rollout status:** gated pending pilot evidence, especially around media scalability behavior

In practical terms, the product is ready to be used by a limited cohort of real engineers with active operations/support oversight, while broader rollout remains intentionally controlled until pilot outcomes are reviewed.

## 2. What the app now supports

The app currently supports the following production-relevant capabilities for engineer operations:

- **Login and session management**
  - engineer authentication, session persistence, logout and re-auth paths
- **Jobs list and job detail**
  - assigned-job visibility with operational context
- **Active-job experience**
  - active-job highlighting, resume behavior, persisted active context
- **Accept job**
  - engineer acceptance with replay-safe backend behavior
- **Punch in / punch out**
  - geofence-aware punch workflows and sequencing validation
- **Telemetry (best-effort)**
  - field location telemetry behavior aligned with current policy
- **Completion readiness**
  - readiness checks tied to completion requirements
- **Evidence submission**
  - forms, signature, media, and parts submission workflows
- **Notes and activity timeline**
  - engineer notes plus typed activity events where safely available
- **SKU lookup**
  - engineer-safe inventory search to improve parts-entry quality
- **Sync and outbox**
  - queued operations, retry/discard controls, conflict visibility
- **Diagnostics and settings**
  - app/session/sync visibility and support snapshot support
- **Assignment alerts (MVP)**
  - in-app assignment alerting path for practical field awareness
- **Vehicle checks / daily inspections**
  - daily vehicle inspection flow and issue capture using current backend support

Overall, the app now covers the full day-to-day engineer core path with pilot-grade resilience controls.

## 3. What the pilot is intended to prove

The limited field pilot is intended to validate real-world behavior before broader rollout in the areas that matter most to operations and service quality:

- **Workflow usability**
  - engineers can complete jobs efficiently without avoidable friction
- **Sync reliability**
  - outbox and retry behavior remains stable under weak and changing network conditions
- **Evidence reliability**
  - forms/signature/media/parts submissions complete reliably in normal field scenarios
- **Supportability**
  - support and ops can diagnose issues quickly using available diagnostics/snapshots
- **Media behavior under field usage**
  - current media strategy performs acceptably for pilot workload and device/network diversity
- **Engineer adoption confidence**
  - engineers can consistently use the app as primary workflow, with clear escalation paths

## 4. What is intentionally controlled during pilot

Pilot is run under explicit release-control discipline to protect reliability and learning quality:

- **Feature freeze / change control**
  - only targeted pilot-risk fixes (P0/P1) during active pilot window
  - no broad feature expansion during pilot
- **Legacy media default**
  - existing media path remains default for pilot stability
- **Media Phase 2 path**
  - new phase-2 media path is feature-flagged and only enabled for selected subset if needed
- **Issue triage rules**
  - severity-based pilot triage (P0/P1/P2/P3) with clear stop/mitigate/defer policy
- **Controlled pilot cohort**
  - limited participant group with named support ownership and daily review cadence

This controlled approach ensures pilot data is actionable and not distorted by uncontrolled concurrent changes.

## 5. Known limitations / broader-rollout blockers

The primary broader-rollout blocker remains **media scalability under larger real-world evidence loads**:

- current contract is still JSON/base64-centric for legacy compatibility
- 2 MiB request-cap constraints remain part of operational behavior
- media phase-2 foundation exists but full large-object transport path is not yet complete

Additional broader-rollout constraints:

- broader release remains dependent on pilot evidence and objective reliability outcomes
- rollout progression requires demonstrated supportability at pilot scale without unacceptable operational burden

These limits are known, documented, and being managed deliberately through staged rollout controls.

## 6. Support and escalation model

During pilot:

- **Engineer reporting path**
  - engineers report issues through the agreed pilot support channel with job/time/context
- **Ops/support first checks**
  - confirm environment/session state, network status, and expected workflow preconditions
  - review sync/outbox state and recent errors in diagnostics
- **Diagnostics snapshot usage**
  - support snapshot and diagnostics context are captured for reproducible triage
  - repeated patterns (e.g., media failures, sync conflicts) are tracked daily
- **Blocker criteria**
  - issues are treated as blockers when they cause data-risk, core workflow failure, or repeated inability to complete normal jobs

This model is designed to reduce time-to-triage and maintain safe pilot continuity.

## 7. Success criteria for the limited field pilot

Pilot is considered successful when the following practical criteria are met across the pilot window:

- **Failure rates are acceptable**
  - no sustained critical failure trend in core workflows
- **Sync behavior is acceptable**
  - no systemic outbox deadlocks; retries/conflicts are manageable and recoverable
- **Evidence/media behavior is acceptable**
  - normal job evidence can be completed without recurring media-related blocking patterns
- **Support burden is acceptable**
  - incident volume and severity remain within planned support capacity
- **Engineer experience is acceptable**
  - engineers can reliably complete end-to-end job workflows with manageable friction

If these conditions are not met, broader rollout remains gated and corrective actions are prioritized.

## 8. Final recommendation

Proceed with the **limited field pilot** under the established release-control model.

Maintain a gated rollout posture:

- keep broader rollout **blocked** until pilot evidence is reviewed and accepted
- keep legacy media as default during pilot
- use phase-2 media path selectively via feature flag where controlled validation is needed

This recommendation balances delivery progress with operational safety and responsible rollout discipline.
