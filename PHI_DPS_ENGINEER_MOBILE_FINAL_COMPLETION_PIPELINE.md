# PHI-DPS Engineer Mobile — Final Completion Pipeline

This is the final implementation pipeline for the remaining engineer-mobile work after core workflow completion.

Current baseline is assumed complete (auth/jobs/accept/active-job/punch/telemetry/readiness/evidence/notes+SKU/outbox+sync/diagnostics and backend idempotency hardening).

---

## Wave 9 — Field Resilience + Operator Clarity

### Goal
Eliminate remaining high-frequency field friction in real operations: action-point conflict handling, media reliability under larger usage, and active-job continuity polish.

### Exact features to implement
1. **Richer conflict/retry UX at action point**
   - Show context-aware remediation where action is triggered (not only diagnostics screen).
   - Distinguish `409` conflict, `400` validation, `403` access, `413` media-size, and transient `5xx/network`.
2. **Stronger media pipeline (phase 1, no architecture break)**
   - Better local compression/size presets, chunked user flow (“submit in sets”), clearer preflight warnings and post-failure recovery.
3. **Last-active-job persistence polish**
   - Persist/resume most recent active job across relaunch and refresh.
4. **Activity timeline extension (safe)**
   - Expand timeline cards for existing events where available (e.g., note + local sync status markers), without forcing backend redesign.

### Why these belong in Wave 9
- Highest operational impact with minimal domain expansion.
- Directly improves engineer throughput and reduces support tickets during scaled pilot.
- Uses mostly existing APIs and current architecture.

### Backend changes needed
- **Minimal/optional** for this wave:
  - Optional additional typed activity payload support if exposing non-note events is low-risk.
  - No mandatory new endpoint for active-job persistence.
- Keep media backend contract unchanged in this wave (2 MiB JSON cap + existing idempotency), unless a tiny safe enhancement is identified.

### Mobile changes needed
- Action-specific retry/conflict components in:
  - punch
  - note submission
  - form/signature/media/parts submission
  - accept action
- Media UX improvements:
  - stronger pre-submit meter
  - photo set guidance
  - user-friendly 413 remediation with “reduce/retake/split” path
- Persisted last-active-job pointer and resume behavior.
- Timeline rendering refinement to support event-type expansion later.

### Dependencies
- Can start immediately on mobile.
- Optional backend additions can be parallelized but are not blockers.

### Risks
- Over-complex conflict UX can become inconsistent across screens.
- Media mitigation may not be sufficient for large field usage if payload volume spikes.

### Definition of done
- Engineers can resolve most failures from the screen where failure happened.
- Active job resumes after app restart/navigation reliably.
- Media failures provide actionable, non-ambiguous next steps.
- No regression in sync/idempotency behavior.

---

## Wave 10 — Field Completeness for Broad Rollout

### Goal
Add missing field-operational capability blocks: compliance visibility, richer site/customer context, push-driven assignment awareness, and vehicle readiness workflow.

### Exact features to implement
1. **Certificate/compliance visibility** (engineer-safe read)
2. **Richer customer/site history/context** in job detail
3. **Push notifications / assignment alerts**
4. **Vehicle checks / daily inspections**

### Why these belong in Wave 10
- These are broad-rollout enablers that depend on backend capability and policy updates.
- They expand workflow scope beyond core execution into safety/compliance/awareness.

### Backend changes needed
1. Engineer-safe compliance endpoints + RBAC policy updates.
2. Aggregated site/customer context endpoint/read model (history, access notes, relevant prior context).
3. Push token registration endpoint + assignment/status event publishing.
4. Vehicle checklist endpoints (or role exposure on existing modules) with auditable submissions.

### Mobile changes needed
1. Compliance section in job detail (status + artifact access).
2. Context cards (site access constraints, key history snippets, relevant customer context).
3. Push integration (token lifecycle, deep links to job detail/active-job).
4. Daily vehicle check flow with clear start-of-day UX and defect capture.

### Dependencies
- Backend-first for each feature family.
- Mobile integration can proceed once endpoint contracts are stable.

### Risks
- Push reliability and token lifecycle edge cases.
- Compliance data access policy errors can create security or operational gaps.
- Vehicle checks can add significant UX friction if not streamlined.

### Definition of done
- Engineer can view required compliance context for assigned jobs.
- Assignment/status push alerts reliably deep-link into app.
- Vehicle checks can be completed and submitted by engineer role.
- Site/customer context materially reduces “missing info” escalations.

---

## Wave 11 — Production Hardening + Pilot Feedback Closure

### Goal
Consolidate broad-production readiness using pilot evidence, including media strategy escalation, telemetry policy tuning, and supportability hardening.

### Exact features to implement
1. **Broader production hardening from pilot feedback**
   - Top defect classes from pilot telemetry/outbox/support tickets.
2. **Media pipeline phase 2 (if pilot requires)**
   - Safer large-object contract (e.g., presigned/multipart) if 2 MiB JSON model proves insufficient.
3. **Telemetry strategy refinement**
   - Adaptive cadence/battery-aware behavior driven by field evidence.
4. **Activity timeline expansion (if useful from pilot)**
   - Add additional event types beyond notes where value is proven.

### Why these belong in Wave 11
- Should be data-driven from real usage.
- Includes potentially heavier contract changes and ops instrumentation.

### Backend changes needed
- If media phase 2 triggered:
  - upload session/presigned endpoint(s)
  - metadata commit endpoint
  - validation and audit updates
- Telemetry policy controls/config if needed.
- Optional expanded activity event generation.

### Mobile changes needed
- New media transport flow (if enabled) with fallback handling.
- Telemetry tuning and visibility controls.
- Timeline renderer for additional event types.
- Support diagnostics exports aligned with top pilot failure classes.

### Dependencies
- Requires pilot metrics and agreed cutover decision for media pipeline.

### Risks
- Media contract migration complexity.
- Telemetry changes can affect dispatch observability if over-throttled.

### Definition of done
- Top pilot reliability gaps closed and verified.
- Media reliability meets agreed production SLO under field-like loads.
- No critical unresolved blockers for broader rollout decision.

---

## Feature Start Conditions

## Can start immediately (no new backend required)
- Action-point conflict/retry UX improvements.
- Last-active-job persistence polish.
- Media UX hardening around current 2 MiB contract.
- Timeline rendering structure improvements on current note events.

## Blocked by backend work
- Compliance/certificate visibility.
- Richer site/customer context pack.
- Push assignment alerts.
- Vehicle checks/daily inspections.
- Media phase 2 (if required) contract.

## Should wait for pilot feedback
- Media phase 2 decision (trigger-based).
- Telemetry strategy refinements.
- Activity timeline expansion beyond notes.
- Final production-hardening priorities.

---

## Best Execution Order

1. **Wave 9 immediate mobile work** (conflict UX + active persistence + media UX hardening).
2. Stabilize and run short staged field validation.
3. In parallel, define and lock **Wave 10 backend contracts** (compliance/context/push/vehicle).
4. Deliver Wave 10 in thin vertical slices (one feature family at a time).
5. Collect pilot metrics and run **Wave 11** only on evidence-based priorities.

---

## Top Remaining Risks

1. **Media scalability risk** if real field payloads exceed current JSON/base64 limits frequently.
2. **Operational confusion risk** if conflict remediation differs across screens.
3. **Policy/RBAC risk** for compliance/context endpoints if engineer scope is not tightly enforced.
4. **Notification reliability risk** (delivery/deeplink/token lifecycle drift).
5. **Process friction risk** from vehicle checks if UX is heavy.

---

## Must Complete Before Broader Rollout

- Wave 9 conflict/retry UX at action point fully implemented and validated.
- Wave 10 compliance visibility + context + push + vehicle checks delivered and role-safe.
- Pilot-derived hardening items closed (Wave 11 critical subset).
- If pilot indicates high media failure rate, media phase 2 path must be delivered or formally risk-accepted with strict controls.

---

## Cursor Execution Checklist

### Wave 9 checklist
- [ ] Add action-point error handling patterns for `409/400/403/413/5xx` across core actions.
- [ ] Implement and test last-active-job persistence + resume.
- [ ] Strengthen media preflight UX and remediation flow.
- [ ] Expand timeline UI to support typed activity rendering (note-first).
- [ ] Regression test sync/idempotency and conflict behavior.

### Wave 10 checklist
- [ ] Backend: engineer-safe compliance read endpoints + tests.
- [ ] Backend: richer site/customer context endpoint + tests.
- [ ] Backend: push token registration + assignment/status eventing + tests.
- [ ] Backend: vehicle checks endpoints/role support + tests.
- [ ] Mobile: compliance UI integration.
- [ ] Mobile: context cards integration.
- [ ] Mobile: push integration + deep links.
- [ ] Mobile: vehicle checks flow.
- [ ] E2E staging validation scripts updated.

### Wave 11 checklist
- [ ] Collect and rank pilot defects/telemetry/support signals.
- [ ] Decide media phase 2 go/no-go using objective threshold.
- [ ] Implement selected hardening items (media/telemetry/activity expansion).
- [ ] Validate production readiness criteria and update release docs.

### Cross-wave controls
- [ ] Keep all new writes idempotent or explicitly non-replayable by contract.
- [ ] Update capability matrix + hardening docs after each wave.
- [ ] Ensure all user-facing failures include actionable remediation.
- [ ] Maintain modular changes with no architecture rewrite.
