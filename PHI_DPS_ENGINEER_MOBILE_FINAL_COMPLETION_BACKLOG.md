# PHI-DPS Engineer Mobile — Final Completion Backlog

This backlog covers **remaining completion work after Waves 1–7**.  
It assumes core engineer workflow is already live: auth/session, jobs list/detail, accept, punch, telemetry, readiness, evidence, outbox/sync, diagnostics, and backend idempotency hardening.

Only gaps and next-phase completion work are listed below.

---

## Must-Have Before Limited Field Pilot

### 1) Engineer Notes + Job Activity Timeline
- **Why it matters:** Engineers need field notes and a clear activity trail for handover, dispute handling, and continuity.
- **Current gap:** No engineer-safe notes endpoint; no unified timeline in mobile for key events.
- **Backend dependency:** New engineer-scoped notes APIs (`create/list`), assignment checks, audit fields.
- **Mobile work required:** Notes composer, notes list, timeline section on job detail, offline queue for note create.
- **UX/UI impact:** Adds a high-utility “Job activity” panel and quick note action.
- **Offline/sync impact:** Try-now-then-queue; idempotency key required for note create.
- **Acceptance criteria:** Engineer can add/view notes on assigned jobs; notes visible after reconnect; duplicate submit does not duplicate notes.
- **Priority:** **P0**

### 2) SKU / Inventory Lookup for Parts Submission
- **Why it matters:** Free-text SKU entry causes avoidable failure and support load.
- **Current gap:** Parts entry relies on exact SKU knowledge.
- **Backend dependency:** Engineer-safe stock search/read endpoint with basic filters (sku/name/location/availability).
- **Mobile work required:** SKU search modal/autocomplete, selected item chips, quantity + location capture.
- **UX/UI impact:** Faster, safer parts capture with fewer errors.
- **Offline/sync impact:** Cache recent lookup results locally; queue parts submit as already implemented.
- **Acceptance criteria:** Engineer can search/select SKU from app; parts submission error rate drops; unavailable SKU is clearly flagged.
- **Priority:** **P0**

### 3) Conflict/Retry UX Upgrade (409/400/403 clarity)
- **Why it matters:** Reliability includes clear operator actions when sync fails.
- **Current gap:** Error surfacing exists but lacks guided resolution flow by status class.
- **Backend dependency:** None mandatory (existing status codes are usable).
- **Mobile work required:** Actionable retry cards: “retry”, “edit/resubmit”, “discard duplicate”, “contact dispatch”.
- **UX/UI impact:** Reduces confusion and duplicate action attempts.
- **Offline/sync impact:** Strongly improves outbox handling confidence.
- **Acceptance criteria:** For 409/400/403/413, UI shows clear next step; conflicts no longer appear as generic failures.
- **Priority:** **P0**

### 4) Staged Media Workflow Hardening (without redesign)
- **Why it matters:** Media is the most failure-prone payload path in field conditions.
- **Current gap:** 2 MiB cap and server guard exist; user guidance around compression/chunking is basic.
- **Backend dependency:** None for phase 1 hardening; phase 2 requires presigned/multipart APIs.
- **Mobile work required:** Pre-submit payload meter, compression presets, "split media set" helper, clearer 413 handling.
- **UX/UI impact:** Fewer blocked completions and support calls.
- **Offline/sync impact:** Keep current online-first policy, but improve retry guidance and failed-item visibility.
- **Acceptance criteria:** User sees estimated payload size before submit; 413 handling provides immediate remediation path.
- **Priority:** **P0**

### 5) Stronger Active-Job / In-Progress Experience
- **Why it matters:** Field engineers need one-screen operational focus while on site.
- **Current gap:** Core actions exist but active-job context is fragmented.
- **Backend dependency:** Optional read endpoints for “active session” summary; not mandatory for first cut.
- **Mobile work required:** Dedicated Active Job view (status, timer, required evidence, pending outbox items, quick actions).
- **UX/UI impact:** Better throughput and fewer missed steps.
- **Offline/sync impact:** Surface pending operations and local state in-context.
- **Acceptance criteria:** Engineer can complete a standard job end-to-end from active-job screen without deep navigation.
- **Priority:** **P1 (high)**

---

## Should-Have Before Broader Rollout

### 6) Engineer Certificate / Compliance Visibility
- **Why it matters:** Engineers need to view required cert/compliance artifacts in field.
- **Current gap:** Certificate/compliance flow is blocked by RBAC/policy for engineer usage.
- **Backend dependency:** Engineer-safe read endpoints and role policy updates.
- **Mobile work required:** Compliance tab on job detail + download/view states.
- **UX/UI impact:** Better first-time fix and fewer calls back to office.
- **Offline/sync impact:** Cache metadata and last-opened docs; online fetch for heavy files.
- **Acceptance criteria:** Engineer can see job-required compliance documents and status.
- **Priority:** **P1**

### 7) Push Notifications (Job updates + sync prompts)
- **Why it matters:** Engineers should not rely on manual refresh for assignment/priority changes.
- **Current gap:** No push channel integrated in mobile flow.
- **Backend dependency:** Notification registration endpoint + event triggers + token lifecycle.
- **Mobile work required:** FCM/APNs setup, token registration, notification routing/deeplinks.
- **UX/UI impact:** Better responsiveness and fewer missed assignments.
- **Offline/sync impact:** Push can trigger opportunistic sync after reconnect.
- **Acceptance criteria:** Assignment/status changes arrive as notifications and open the correct job.
- **Priority:** **P1**

### 8) Vehicle Checks / Daily Readiness
- **Why it matters:** Operational and compliance requirement for many field teams.
- **Current gap:** No engineer-facing pre-shift vehicle checklist in mobile app.
- **Backend dependency:** Existing/expanded vehicle inspection endpoints + engineer role access.
- **Mobile work required:** Daily checklist flow, defect capture, submit + acknowledgment.
- **UX/UI impact:** Adds start-of-day safety workflow.
- **Offline/sync impact:** Queue checklist submit if offline.
- **Acceptance criteria:** Engineer can complete and submit daily vehicle checks; defects visible to dispatcher.
- **Priority:** **P1**

### 9) Richer Site/Customer Context Pack
- **Why it matters:** Better preparation before arrival improves completion speed.
- **Current gap:** Job detail lacks deeper customer/site/asset context bundle.
- **Backend dependency:** Aggregated read model (site notes, access instructions, asset history, contact preferences).
- **Mobile work required:** Structured context cards with collapsible sections.
- **UX/UI impact:** Fewer mistakes and missed constraints.
- **Offline/sync impact:** Cache context snapshot for assigned jobs.
- **Acceptance criteria:** Engineer can view key site access and asset context without leaving job detail.
- **Priority:** **P1**

### 10) Better Forms UX (drafts, sectioning, validation hints)
- **Why it matters:** Form friction is a major source of incomplete submissions.
- **Current gap:** Functional submission exists, but UX is basic.
- **Backend dependency:** Optional schema metadata endpoint for dynamic form definitions.
- **Mobile work required:** Form draft persistence, section progress, inline required-key guidance, resume draft.
- **UX/UI impact:** Faster completion and fewer validation errors.
- **Offline/sync impact:** Drafts local-first; submit via existing queue path.
- **Acceptance criteria:** Engineers can save/resume form drafts; missing required fields are obvious before submit.
- **Priority:** **P1**

### 11) Calendar / Day Planning View
- **Why it matters:** Engineers need daily route and schedule visibility.
- **Current gap:** Jobs list exists, but no day planning experience.
- **Backend dependency:** Optional scheduled-jobs/day endpoint (or client sort from existing list).
- **Mobile work required:** Day agenda view, route-order hints, “next job” quick action.
- **UX/UI impact:** Better planning and reduced idle time.
- **Offline/sync impact:** Cached day agenda from last sync.
- **Acceptance criteria:** Engineer sees day schedule and can jump to next planned job quickly.
- **Priority:** **P2**

### 12) Diagnostics / Support Tooling v2
- **Why it matters:** Scale requires fast support triage beyond basic diagnostics.
- **Current gap:** Current diagnostics are useful but limited for escalations.
- **Backend dependency:** Optional support trace endpoint upload.
- **Mobile work required:** One-tap diagnostics export, correlation IDs, filtered outbox inspection.
- **UX/UI impact:** Minimal end-user impact, major support gain.
- **Offline/sync impact:** Export should work offline and upload later.
- **Acceptance criteria:** Support can identify failing operation, payload class, and status pattern from export.
- **Priority:** **P2**

### 13) Customer Signoff / Share Improvements
- **Why it matters:** Clean signoff output reduces billing disputes.
- **Current gap:** Signature submit exists but post-signoff sharing flow is limited.
- **Backend dependency:** Optional endpoint to generate/send signoff summary artifact.
- **Mobile work required:** Signoff confirmation summary and “share/send” options.
- **UX/UI impact:** Improves completion professionalism and customer trust.
- **Offline/sync impact:** Queue send/share intents where possible.
- **Acceptance criteria:** Engineer can confirm what was signed and trigger share/send workflow.
- **Priority:** **P2**

---

## Nice-to-Have / Later Enhancements

### 14) Leave / Availability Management
- **Why it matters:** Better workforce planning and dispatch quality.
- **Current gap:** No engineer self-service availability controls in app.
- **Backend dependency:** Availability/leave request APIs and approval workflow.
- **Mobile work required:** Availability calendar + leave request screens.
- **UX/UI impact:** Medium; useful outside urgent workflow.
- **Offline/sync impact:** Queue requests.
- **Acceptance criteria:** Engineer can submit leave/availability updates and see request status.
- **Priority:** **P3**

### 15) Engineer Expenses Capture
- **Why it matters:** Field expenses tied to job improve cost traceability.
- **Current gap:** No expenses flow in mobile.
- **Backend dependency:** Expense endpoints + policy/rules.
- **Mobile work required:** Receipt capture, category, amount, job linkage.
- **UX/UI impact:** Additional admin workflow.
- **Offline/sync impact:** Queue metadata; media strategy needed for receipts.
- **Acceptance criteria:** Engineer can submit expense with receipt and job association.
- **Priority:** **P3**

### 16) Telemetry Strategy v2 (battery/privacy/cadence)
- **Why it matters:** Better balance of ops insight vs battery/data and privacy.
- **Current gap:** Best-effort telemetry exists, but no adaptive policy by state/network.
- **Backend dependency:** Optional ingestion policy controls + retention/reporting changes.
- **Mobile work required:** Adaptive sampling (idle/en-route/on-site), batching, user transparency settings.
- **UX/UI impact:** Mostly behind-the-scenes; minor settings UI.
- **Offline/sync impact:** Best-effort remains; optional short local burst buffer.
- **Acceptance criteria:** Measurable reduction in battery/data impact with no critical visibility loss.
- **Priority:** **P3**

### 17) Offline Job Pack (assigned jobs cache-first)
- **Why it matters:** Improves resilience when signal is poor.
- **Current gap:** Jobs list/detail are online-supported but not cache-first UX.
- **Backend dependency:** None mandatory.
- **Mobile work required:** Assigned-jobs caching policy, stale markers, refresh controls.
- **UX/UI impact:** Better confidence in weak-network areas.
- **Offline/sync impact:** Significant read-path resilience gain.
- **Acceptance criteria:** Engineer can open last-synced assigned jobs while offline with clear stale indicators.
- **Priority:** **P3**

### 18) Multi-asset / Follow-on Field Workflow Enhancements
- **Why it matters:** Complex jobs often require structured follow-on handling.
- **Current gap:** Follow-on logic exists on backend but limited field UX.
- **Backend dependency:** Optional engineer-safe follow-on APIs (create/request).
- **Mobile work required:** Follow-on suggestion/request UI linked to evidence.
- **UX/UI impact:** Helps avoid unresolved defect handoffs.
- **Offline/sync impact:** Queue follow-on request.
- **Acceptance criteria:** Engineer can request structured follow-on work from the job flow.
- **Priority:** **P3**

---

## Ranked Top-15 Remaining Features

1. Engineer Notes + Job Activity Timeline  
2. SKU / Inventory Lookup for Parts  
3. Conflict/Retry UX Upgrade (409/400/403/413)  
4. Staged Media Workflow Hardening (pre-submit guard + remediation)  
5. Stronger Active-Job / In-Progress Experience  
6. Engineer Certificate / Compliance Visibility  
7. Push Notifications (assignment/status updates)  
8. Vehicle Checks / Daily Readiness  
9. Richer Site/Customer Context Pack  
10. Better Forms UX (drafts/sections/inline guidance)  
11. Calendar / Day Planning View  
12. Diagnostics / Support Tooling v2  
13. Customer Signoff / Share Improvements  
14. Telemetry Strategy v2  
15. Offline Job Pack (cache-first assigned jobs)

---

## Best Implementation Order

1. **Notes API + mobile notes/timeline** (P0)  
2. **SKU lookup API + parts selector UI** (P0)  
3. **Conflict/retry UX polish** (mobile-first, no backend blocker)  
4. **Media hardening UX** (mobile-first; keep existing backend cap)  
5. **Active-job screen consolidation** (mobile-first)  
6. **Compliance visibility APIs + UI**  
7. **Push notification infrastructure + app wiring**  
8. **Vehicle checks workflow**  
9. **Site/customer context read model + UI**  
10. **Forms UX upgrades + optional dynamic schema support**  
11. **Calendar/day planning**  
12. **Diagnostics export/tooling v2**  
13. **Signoff/share enhancements**  
14. **Telemetry strategy v2**  
15. **Offline job-pack + later workforce/expenses modules**

---

## What Requires Backend Changes First

- Engineer notes create/list endpoints + RBAC policy.
- SKU/stock lookup for engineer role.
- Engineer compliance/certificate visibility endpoints.
- Push notification token registration + event publishing.
- Vehicle inspection/check APIs (if current coverage is insufficient for engineer flow).
- Aggregated site/customer context endpoint (or equivalent read model).
- Optional dynamic form schema endpoint.
- Optional signoff/share artifact endpoint.
- Optional telemetry ingestion policy controls.

---

## What Can Be Built Immediately on Mobile (No New Backend Required)

- Conflict/retry UX improvements for existing status codes (400/403/409/413/5xx).
- Media pre-submit size meter and better failure guidance around current 2 MiB cap.
- Active-job consolidated UI with existing endpoints.
- Better forms UX around current submission contract (drafts local-first, section progress).
- Diagnostics export/packaging from local state + existing responses.
- Day planning view using current jobs list data (client-side grouping/sorting).
- Offline job cache for assigned jobs using current read endpoints.

