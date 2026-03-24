# PHI-DPS Engineer Mobile — Final Completion Execution Plan

This document converts the final completion backlog into practical delivery waves to finish the engineer app efficiently after Waves 1–7.

Scope here is execution: what to build, in what order, with dependencies and done criteria.

---

## Execution Principles

- Build on existing core workflow and Wave 7 hardening.
- Prefer high-impact, low-risk increments first.
- Front-load items required for limited field pilot; defer broad-rollout refinements.
- Run each wave with backend/mobile parallel tracks where possible.

---

## Wave 8 — Field Reliability + Must-Have Usability

### Goal
Close the highest-risk field usability gaps that directly affect limited field pilot success and operator confidence.

### Exact features to implement
1. Engineer Notes + Job Activity Timeline
2. SKU / Inventory Lookup for Parts
3. Conflict/Retry UX upgrade (409/400/403/413 guided actions)
4. Media workflow hardening UX (size meter, compression guidance, split helper)
5. Active Job / In-Progress consolidated screen

### Backend changes needed
- Engineer-safe notes endpoints: create/list (assignment check, audit fields, idempotency support).
- Engineer-safe SKU search endpoint (sku/name/location/availability, pagination).
- Optional: read endpoint for active-session summary (if current read model insufficient).

### Mobile changes needed
- Job detail: activity timeline + notes composer/list.
- Parts flow: SKU search picker and selected-item parts entry.
- Outbox/sync UI: explicit per-error remediation actions.
- Media submit: preflight payload estimate + immediate 413 remediation hints.
- Active Job screen: quick actions (accept/punch/evidence/pending sync).

### Dependencies
- Notes and SKU lookup are backend-first.
- Conflict/retry UX and media UX can start immediately.
- Active Job can start immediately with existing APIs; enhance if summary endpoint lands.

### Definition of done
- Notes can be created/viewed only for assigned jobs and survive offline/reconnect via queue.
- Parts can be submitted using in-app SKU lookup (no manual SKU-only dependency).
- 409/400/403/413 are shown with clear user actions; no generic dead-end failures.
- Media flow warns before oversize submits and guides user to recover.
- Engineers can run core job flow from one active-job screen.
- Automated tests added for new repositories/interceptors/state logic + backend route tests.

### Risk level
**Medium** (new APIs + UX changes, but bounded domain and high payoff).

---

## Wave 9 — Broader Rollout Enablers (Ops + Compliance)

### Goal
Add operational completeness features needed before broad rollout across more engineers/jobs.

### Exact features to implement
1. Engineer certificate/compliance visibility
2. Push notifications (assignment/status updates + sync nudge)
3. Vehicle checks / daily readiness
4. Richer site/customer context pack
5. Better forms UX (draft/resume/section progress/inline required-key guidance)

### Backend changes needed
- Engineer-safe compliance read endpoints + policy updates.
- Device push token registration endpoint + notification event publishing.
- Engineer-facing vehicle checklist/defect endpoints (or role exposure on existing endpoints).
- Site/customer context aggregated read model endpoint.
- Optional form schema metadata endpoint (if dynamic forms path chosen).

### Mobile changes needed
- Compliance tab/cards and certificate viewer states.
- FCM/APNs registration and notification routing/deeplinks.
- Vehicle checklist screens (start-of-day, defect capture).
- Context cards in job detail (access info, contacts, asset history).
- Forms UX rework with local draft and resume logic.

### Dependencies
- Mostly backend-first except parts of forms UX and local draft persistence.
- Push requires both backend events and mobile platform setup.

### Definition of done
- Engineers can view compliance/certificate context per job.
- Push notifications arrive and open correct job context.
- Vehicle check can be completed and submitted by engineer role.
- Job detail includes richer site/customer context from aggregated read model.
- Forms are draftable/resumable with improved pre-submit validation UX.

### Risk level
**Medium-High** (cross-platform push + multiple backend slices).

---

## Wave 10 — Productivity + Supportability

### Goal
Improve daily planning, support diagnostics, and completion professionalism at scale.

### Exact features to implement
1. Calendar/day planning view
2. Diagnostics/support tooling v2 (export package + correlation references)
3. Customer signoff/share improvements
4. Offline job pack (assigned jobs cache-first read path)

### Backend changes needed
- Optional day-planning endpoint (if client-side grouping from `/jobs` is insufficient).
- Optional diagnostics upload endpoint (if centralized support ingest desired).
- Optional signoff summary/share artifact endpoint.

### Mobile changes needed
- Agenda/day planner UI from assigned jobs.
- Diagnostics export (local bundle, optional upload, share intent).
- Post-signoff summary UX + share/send actions.
- Cache-first assigned jobs list/detail with stale indicators.

### Dependencies
- Day planning and offline job pack can start immediately on mobile using current reads.
- Diagnostics upload/signoff artifact depend on backend if server persistence is required.

### Definition of done
- Engineer can plan day from agenda view and navigate quickly to next job.
- Support can receive a consistent diagnostics package for issue triage.
- Customer signoff UX includes clear completion summary and share action.
- Assigned jobs remain usable offline with explicit stale-state indicators.

### Risk level
**Medium** (mostly mobile-heavy, low core workflow disruption).

---

## Wave 11 — Post-Pilot Enhancements / Strategic Extensions

### Goal
Implement lower-priority but high-value long-term capabilities after real pilot feedback.

### Exact features to implement
1. Telemetry strategy v2 (adaptive sampling/batching/privacy controls)
2. Leave/availability management
3. Engineer expenses capture
4. Multi-asset/follow-on workflow enhancements

### Backend changes needed
- Telemetry policy/retention controls and optional config endpoints.
- Availability/leave APIs and workflow.
- Expense APIs, policy rules, approval routing.
- Follow-on request APIs for engineer-safe workflow.

### Mobile changes needed
- Adaptive telemetry controls and state-based cadence.
- Leave/availability calendar and request flow.
- Expense capture (receipt, amount, category, job link).
- Follow-on request UI linked from active job/evidence flow.

### Dependencies
- Primarily backend-first; should be informed by internal/limited pilot telemetry and support feedback.

### Definition of done
- Feature-specific acceptance validated with product/ops and measured against pilot feedback metrics.

### Risk level
**Medium** (domain expansion; avoid during urgent rollout windows).

---

## Features by Start Condition

## Can start immediately (mobile-first)
- Conflict/retry UX improvements on existing status codes.
- Media pre-submit size meter and remediation UX.
- Active-job consolidated screen (first iteration).
- Forms UX improvements that do not require new schema endpoint.
- Day planning from current jobs data.
- Offline job pack/cache-first read path for assigned jobs.
- Diagnostics export package (local/share-first approach).

## Blocked by backend changes
- Engineer notes create/list APIs.
- SKU lookup/search for engineer role.
- Compliance/certificate visibility for engineer role.
- Push notification event + token backend path.
- Vehicle checklist endpoints/role access (if not already exposed).
- Rich site/customer context aggregated endpoint.
- Signoff share artifact endpoint (if server-generated output required).

## Should wait for internal/limited pilot feedback
- Telemetry strategy v2 tuning.
- Leave/availability module.
- Expenses module.
- Expanded follow-on/multi-asset enhancements.

---

## Recommended Efficient Order (Cross-Wave)

1. **Start Wave 8 mobile-first work immediately**: conflict/retry UX, media UX, active-job shell.
2. **Parallel backend sprint for Wave 8 APIs**: notes + SKU lookup.
3. **Close Wave 8 end-to-end** and run focused UAT on real jobs.
4. **Wave 9 backend foundations first**: compliance, push registration/events, context read model.
5. **Wave 9 mobile integration** with staged rollout flags.
6. **Wave 10 mostly mobile improvements** with optional backend hooks.
7. **Wave 11 after pilot evidence** (avoid speculative overbuild).

---

## Cursor Execution Checklist (Remaining Work)

Use this as the execution tracker for all remaining work.

### Wave 8 checklist
- [ ] Backend: Engineer notes endpoints (`POST/GET`) + assignment/RBAC checks.
- [ ] Backend: SKU search endpoint for engineer role.
- [ ] Backend: Tests for notes/SKU APIs + idempotency behavior where writes exist.
- [ ] Mobile: Notes composer/list + timeline section on job detail.
- [ ] Mobile: SKU lookup UI integrated into parts submission.
- [ ] Mobile: Conflict/retry cards for 400/403/409/413/5xx.
- [ ] Mobile: Media preflight payload estimator and 413 guidance.
- [ ] Mobile: Active-job consolidated screen with quick actions.
- [ ] QA: Weak-network replay and duplicate submission checks updated.
- [ ] Docs: Capability matrix + pilot docs updated for notes/SKU/conflict UX.

### Wave 9 checklist
- [ ] Backend: Compliance/certificate read APIs for engineer role.
- [ ] Backend: Push token registration + assignment/status event emission.
- [ ] Backend: Vehicle check APIs (or engineer role enablement).
- [ ] Backend: Aggregated site/customer context endpoint.
- [ ] Backend: Optional dynamic form schema endpoint decision.
- [ ] Mobile: Compliance tab and document states.
- [ ] Mobile: Push setup (FCM/APNs), deeplinks, notification handling.
- [ ] Mobile: Vehicle checklist and defect reporting screens.
- [ ] Mobile: Rich context cards in job detail.
- [ ] Mobile: Form draft/resume and enhanced required-field UX.
- [ ] QA: Notification and role-permission validation pack.

### Wave 10 checklist
- [ ] Mobile: Day planning/agenda view and next-job shortcuts.
- [ ] Mobile: Diagnostics v2 export package and support metadata.
- [ ] Mobile: Signoff summary/share UX.
- [ ] Mobile: Cache-first assigned jobs and stale-state indicators.
- [ ] Backend (optional): Diagnostics ingest endpoint.
- [ ] Backend (optional): Signoff artifact generation endpoint.
- [ ] QA: Offline read-path validation and diagnostics support drill.

### Wave 11 checklist
- [ ] Product/ops decision gate from pilot metrics.
- [ ] Backend: Telemetry policy controls.
- [ ] Mobile: Adaptive telemetry/batching.
- [ ] Backend+mobile: Leave/availability module.
- [ ] Backend+mobile: Expenses module.
- [ ] Backend+mobile: Follow-on workflow enhancements.

### Cross-wave governance checklist
- [ ] Each wave has explicit API contracts and error semantics documented.
- [ ] Each wave has automated tests and staging smoke scripts updated.
- [ ] Outbox/idempotency behavior verified on all new write paths.
- [ ] Release/UAT/playbook docs updated at wave end.
- [ ] Pilot risk register updated after every wave.

