# PHI-DPS — Product decisions register

**Purpose:** Working register for **Product**, **Engineering**, and **Operations** to resolve ambiguities identified in `PHI_DPS_MISSING_EXECUTION_DETAILS.md`. Each item is a **decision record**, not a specification.  
**Source:** Derived from `PHI_DPS_MISSING_EXECUTION_DETAILS.md` (execution gaps, open questions, edge cases, NFRs, RBAC gaps).

**How to use**
- Review **§1 Priority queue** in weekly triage; drive **Release-blocking** and **Compliance-blocking** items to `Decided` first.
- Update row **Status** and **Actual decision date** when closed; add a one-line **Decision reference** (link to ticket, ADR, or spec section).
- **Owner** is the **accountable** person (not always the executor).

**Status legend**
| Status | Meaning |
|--------|---------|
| `Open` | No decision yet |
| `In review` | Options under review |
| `Decided` | Recorded and communicated |
| `Deferred` | Explicitly postponed (see note) |
| `Superseded` | Replaced by another ID |

**Blocking legend**
| Blocking | Meaning |
|----------|---------|
| `Release-blocking` | Delays production go-live if unresolved |
| `Compliance-blocking` | Regulatory / safety / payroll integrity risk |
| `Feature-blocking` | Blocks a named feature/epic |
| `Non-blocking` | Can ship with interim policy |

**Default target:** Unless set, use **90 days** from first register publication for `Open` **Release-blocking** items.

---

## 1. Priority queue — highest risk unresolved (review first)

Order: global risk (reporting integrity, compliance, money, safety) then operational scale.

| Rank | ID | Title | Module | Blocking | Owner |
|------|-----|-------|--------|----------|-------|
| 1 | D-001 | Canonical `Job.status` enum & invalid transitions | Dispatch / Jobs | Release-blocking | Product + Principal Engineer |
| 2 | D-002 | Canonical `Quote.status` enum & revision-after-send rules | Quoting | Release-blocking | Product + Commercial |
| 3 | D-003 | Dispatch-ready definition (checklist + system enforcement) | Dispatch | Release-blocking | Product + Ops |
| 4 | D-004 | Certificate type matrix (job/work_type/asset → cert + validity) | Compliance | Compliance-blocking | Compliance lead + Product |
| 5 | D-005 | Server-side validation parity vs admin web / mobile | Cross-cutting API | Release-blocking | Principal Engineer |
| 6 | D-006 | Reassignment mid-job (punch, telemetry, customer notify) | Dispatch + Time | Compliance-blocking | Product + Ops |
| 7 | D-007 | Quote monetary change after customer acceptance | Quoting + Jobs | Release-blocking | Commercial + Product |
| 8 | D-008 | Cancellation after dispatch (stock, SLA, charges) | Dispatch + Inventory + Finance | Release-blocking | Product + Finance |
| 9 | D-009 | Invoice generation business gates (vs permission-only) | Invoicing | Release-blocking | Finance + Product |
| 10 | D-010 | Stock reservation moment & release on cancel | Inventory | Release-blocking | Ops + Finance |
| 11 | D-011 | Telemetry & PII retention periods | Tracking + Security | Compliance-blocking | DPO / Security + Product |
| 12 | D-012 | Mobile offline queue + idempotency contract | Mobile + API | Feature-blocking | Principal Engineer + Product |
| 13 | D-013 | RBAC: signed-off matrix + product↔code role mapping | Identity & Access | Release-blocking | Product Owner |
| 14 | D-014 | Competency expiry: block vs override | Dispatch + Competence | Compliance-blocking | Ops + Compliance |
| 15 | D-015 | SLA clock: calendar vs wall-clock MVP | Contracts + Dispatch | Feature-blocking | Product |
| 16 | D-016 | Punch overlap / duplicate rules & corrections | Time | Compliance-blocking | HR/Ops + Product |
| 17 | D-017 | Credit note / refund scope in PHI-DPS vs external finance | Invoicing | Release-blocking | Finance |
| 18 | D-018 | Partial completion vs revisit vs follow-on job | Dispatch | Feature-blocking | Product |
| 19 | D-019 | Customer dispute handling (freeze billing? case entity?) | CRM + Invoicing | Feature-blocking | Commercial + Product |
| 20 | D-020 | NFR SLOs (p95 API, RPO/RTO, availability) | Platform / NFR | Release-blocking | Engineering Lead + Ops |

---

## 2. Decision register by module

Within each module, items are ordered **highest blocking risk first** (Release → Compliance → Feature → Non-blocking).

---

### Cross-cutting — Domain vocabulary & API standards

| ID | D-001 |
|----|------|
| **Title** | Canonical `Job.status` enum and state machine |
| **Context** | `Job.status` is stringly-typed; reporting, automation, and API validation diverge. |
| **Options considered** | (a) Publish enum + DB check constraint; (b) Enum in app only; (c) Free text with validation layer |
| **Recommended option** | (a) Documented enum + migrate DB + enforce on write paths |
| **Downstream impact** | Dashboards, mobile, completion gates, search indexes, tests |
| **Blocking status** | Release-blocking |
| **Owner** | Product Owner (business states) + Principal Engineer (implementation) |
| **Target decision date** | TBD +45 days |

| ID | D-002 |
|----|------|
| **Title** | Canonical `Quote.status` enum and revision model |
| **Context** | Quotes use `draft`/`accepted` inconsistently; post-send edits need audit. |
| **Options considered** | (a) Status enum + immutable accepted row + new revision ID; (b) Version column on same quote; (c) New quote record per revision |
| **Recommended option** | (a)+(c) hybrid: superseded link + new quote id for new money |
| **Downstream impact** | Job creation from quote, portal acceptance, invoicing |
| **Blocking status** | Release-blocking |
| **Owner** | Product Owner + Commercial lead |
| **Target decision date** | TBD +45 days |

| ID | D-005 |
|----|------|
| **Title** | Server-side validation parity (CRM, quoting, jobs) with UI |
| **Context** | Web/mobile may validate stricter than API (security and consistency risk). |
| **Options considered** | (a) Pydantic validators mirror UI rules; (b) Shared schema package; (c) Document gaps only |
| **Recommended option** | (a) + tests for divergence |
| **Downstream impact** | All clients; regression tests |
| **Blocking status** | Release-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +60 days |

| ID | D-021 |
|----|------|
| **Title** | API pagination / sort / filter standard |
| **Context** | Defaults and max limits differ by endpoint; clients guess. |
| **Options considered** | (a) Global standard doc + middleware defaults; (b) Per-resource appendix; (c) OpenAPI only |
| **Recommended option** | (a)+(b): cap `limit`≤200, default 50, `total` where feasible |
| **Downstream impact** | Web, mobile, integrations |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

| ID | D-022 |
|----|------|
| **Title** | Idempotency for mutating APIs (punch, telemetry, mobile retries) |
| **Context** | Retries can duplicate punches or events without a key policy. |
| **Options considered** | (a) `Idempotency-Key` header + server store; (b) Natural keys (job+time window); (c) Client-only dedupe |
| **Recommended option** | (a) for punch and critical POSTs |
| **Downstream impact** | Mobile sync, API gateway, DB |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

| ID | D-023 |
|----|------|
| **Title** | Auth: token refresh, revoke, password policy, account lockout |
| **Context** | Long-lived JWTs vs security; lockout not fully specified. |
| **Options considered** | (a) Short JWT + refresh token; (b) Rotate on logout list; (c) Status quo + docs |
| **Recommended option** | (a) for production; document interim for MVP |
| **Downstream impact** | All clients, session handling |
| **Blocking status** | Release-blocking |
| **Owner** | Security lead + Principal Engineer |
| **Target decision date** | TBD +60 days |

---

### Platform / Non-functional requirements (NFR)

| ID | D-020 |
|----|------|
| **Title** | NFR SLOs: latency, availability, RPO/RTO |
| **Context** | `DEPLOYMENT.md` is operational but not numeric SLOs. |
| **Options considered** | (a) One-page SLO (p95, monthly uptime, RPO); (b) Tiered (MVP vs enterprise); (c) Defer |
| **Recommended option** | (a) with MVP minimums |
| **Downstream impact** | Hosting budget, alerting, on-call |
| **Blocking status** | Release-blocking |
| **Owner** | Engineering Lead + Ops |
| **Target decision date** | TBD +45 days |

| ID | D-024 |
|----|------|
| **Title** | Scale assumptions (engineers, jobs/day, telemetry rate) |
| **Context** | Capacity planning and load tests need targets. |
| **Options considered** | (a) Document peak assumptions; (b) Load test to current max; (c) Elastic only |
| **Recommended option** | (a) + annual review |
| **Downstream impact** | DB sizing, rate limits |
| **Blocking status** | Non-blocking |
| **Owner** | Engineering Lead |
| **Target decision date** | TBD +120 days |

| ID | D-025 |
|----|------|
| **Title** | Retention: telemetry events, audit logs, PDFs, comms bodies |
| **Context** | Legal vs cost; GDPR/compliance may require minimization. |
| **Options considered** | (a) Retention schedule by category; (b) Infinite until policy; (c) Customer-specific |
| **Recommended option** | (a) with legal review |
| **Downstream impact** | Purge jobs, storage cost |
| **Blocking status** | Compliance-blocking |
| **Owner** | DPO / Legal + Product |
| **Target decision date** | TBD +60 days |

| ID | D-026 |
|----|------|
| **Title** | Security logging: PII in access logs (`PHI_DPS_LOG_JSON_ACCESS`) |
| **Context** | JSON access logs need redaction rules. |
| **Options considered** | (a) Field allowlist; (b) Hash user ids; (c) No PII in URLs |
| **Recommended option** | (a)+(c) |
| **Downstream impact** | Log pipeline, SIEM |
| **Blocking status** | Release-blocking |
| **Owner** | Security lead |
| **Target decision date** | TBD +60 days |

| ID | D-027 |
|----|------|
| **Title** | File upload limits (size, MIME, malware scan) |
| **Context** | Document storage envs exist; limits not unified in product spec. |
| **Options considered** | (a) Global max 25MB + scan; (b) Per doc type; (c) Client-only |
| **Recommended option** | (b) with hard ceiling |
| **Downstream impact** | Portal, mobile attachments |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer + Security |
| **Target decision date** | TBD +90 days |

| ID | D-028 |
|----|------|
| **Title** | API timeouts and long-running jobs (PDF gen, webhooks) |
| **Context** | Clients need retry guidance; server needs worker pattern for heavy work. |
| **Options considered** | (a) 30s HTTP + async job + poll; (b) Increase timeout; (c) Document only |
| **Recommended option** | (a) for certificate/invoice generation |
| **Downstream impact** | UX, job queue |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

| ID | D-029 |
|----|------|
| **Title** | Observability: mandatory dashboards/alerts for go-live |
| **Context** | Diagnostics endpoints exist; go-live checklist not tied to alerts. |
| **Options considered** | (a) Minimum alert set (5xx rate, DB, queue depth); (b) Full SRE pack; (c) Manual checks |
| **Recommended option** | (a) |
| **Downstream impact** | Ops runbooks |
| **Blocking status** | Release-blocking |
| **Owner** | Ops + Engineering Lead |
| **Target decision date** | TBD +45 days |

---

### Identity & access / RBAC

| ID | D-013 |
|----|------|
| **Title** | Signed-off RBAC matrix + product role ↔ code role mapping |
| **Context** | Code has `Admin`, `Finance`, …; product may say `super_admin`, `warehouse_admin`. |
| **Options considered** | (a) Single matrix doc + map names; (b) Add DB roles; (c) Permission-only |
| **Recommended option** | (a); add roles only if matrix requires |
| **Downstream impact** | Every module UI and API |
| **Blocking status** | Release-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +60 days |

| ID | D-030 |
|----|------|
| **Title** | Compliance ownership role (`compliance_admin` vs `Admin`/`Ops_Manager`) |
| **Context** | No `Compliance` role in `authorization_policy.py`. |
| **Options considered** | (a) New role + permissions; (b) Map to Admin subset + training; (c) Ops_Manager + checklist |
| **Recommended option** | (b) short-term; (a) if segregation of duties required |
| **Downstream impact** | Certificate templates, overrides |
| **Blocking status** | Compliance-blocking |
| **Owner** | Product Owner + Compliance lead |
| **Target decision date** | TBD +45 days |

| ID | D-031 |
|----|------|
| **Title** | Warehouse role: new DB role vs `Ops_Manager`/`Admin` |
| **Context** | Inventory may need segregated approval. |
| **Options considered** | (a) `Warehouse` role; (b) Permission keys on Ops; (c) Admin-only |
| **Recommended option** | (b) unless audit requires (a) |
| **Downstream impact** | Inventory routes, PO flow |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner + Finance/Ops |
| **Target decision date** | TBD +90 days |

| ID | D-032 |
|----|------|
| **Title** | Engineer fine-grained permissions (completion APIs vs read-only) |
| **Context** | `Engineer` has empty permission set; routes use role gates. |
| **Options considered** | (a) Add keys for submit form/media/parts; (b) Role-only; (c) Per-job scope |
| **Recommended option** | (a) for auditable toggles |
| **Downstream impact** | Mobile + backend |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer + Product |
| **Target decision date** | TBD +90 days |

| ID | D-033 |
|----|------|
| **Title** | Dispatcher override: SLA / equipment block without Ops |
| **Context** | Matrix ambiguous; safety risk. |
| **Options considered** | (a) Dispatcher can never override; (b) With `can_override_*`; (c) Escalation workflow |
| **Recommended option** | (b) aligned with existing permission keys |
| **Downstream impact** | Dispatch UI, audit |
| **Blocking status** | Compliance-blocking |
| **Owner** | Product + Ops |
| **Target decision date** | TBD +60 days |

| ID | D-034 |
|----|------|
| **Title** | Viewer scope: global read vs entity-scoped only |
| **Context** | Scoped access groups exist; product intent unclear. |
| **Options considered** | (a) Scoped only; (b) Global read-all Viewer; (c) Remove Viewer |
| **Recommended option** | (a) default |
| **Downstream impact** | `scoped_access_service` rules |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

| ID | D-035 |
|----|------|
| **Title** | Break-glass admin accounts procedure |
| **Context** | Emergency access vs audit. |
| **Options considered** | (a) Named break-glass users + MFA + log review; (b) Shared account forbidden; (c) Time-bound grants |
| **Recommended option** | (a)+(c) |
| **Downstream impact** | Auth, audit |
| **Blocking status** | Compliance-blocking |
| **Owner** | Security + Product |
| **Target decision date** | TBD +60 days |

| ID | D-036 |
|----|------|
| **Title** | Internal access group soft-delete vs hard-delete |
| **Context** | Deactivating groups affects historical audits. |
| **Options considered** | (a) Soft-delete + `active` flag; (b) Hard-delete blocked if memberships exist; (c) Archive |
| **Recommended option** | (a) |
| **Downstream impact** | Org access admin UI |
| **Blocking status** | Non-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +120 days |

---

### CRM — Leads & customers

| ID | D-037 |
|----|------|
| **Title** | Canonical lead lifecycle states |
| **Context** | Automation (chase, conversion) needs stable states. |
| **Options considered** | (a) `new`→`qualified`→`converted`|`lost`|`archived`; (b) Minimal open/closed; (c) CRM sync states |
| **Recommended option** | (a) |
| **Downstream impact** | Lead list filters, reporting |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +60 days |

| ID | D-038 |
|----|------|
| **Title** | Duplicate leads: merge vs reject vs flag |
| **Context** | Data quality for outbound comms. |
| **Options considered** | (a) Soft dup on email+phone + manual merge; (b) Auto-merge; (c) Reject duplicate |
| **Recommended option** | (a) |
| **Downstream impact** | CRM API, UI |
| **Blocking status** | Non-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

| ID | D-039 |
|----|------|
| **Title** | Lead convert idempotency & duplicate POST handling |
| **Context** | Double-submit from UI. |
| **Options considered** | (a) Idempotency-Key; (b) Return existing customer; (c) 409 conflict |
| **Recommended option** | (b)+(c) |
| **Downstream impact** | CRM routes |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

| ID | D-040 |
|----|------|
| **Title** | Customer vs site vs contract: when job must reference `site_id` / `contract_id` |
| **Context** | Portal scoping and compliance jobs need rules. |
| **Options considered** | (a) Rule table by `work_type`; (b) Dispatcher always optional; (c) Contract-first for PPM only |
| **Recommended option** | (a) documented |
| **Downstream impact** | Job create form, validation |
| **Blocking status** | Compliance-blocking |
| **Owner** | Product + Compliance |
| **Target decision date** | TBD +60 days |

| ID | D-041 |
|----|------|
| **Title** | Customer `account_status` (on hold) blocking dispatch / invoice |
| **Context** | Finance hold should stop field work or billing. |
| **Options considered** | (a) `active`/`on_hold`/`closed` on customer; (b) Contract flag only; (c) Manual process |
| **Recommended option** | (a) + block rules configurable |
| **Downstream impact** | Dispatch, invoicing |
| **Blocking status** | Release-blocking |
| **Owner** | Finance + Product |
| **Target decision date** | TBD +60 days |

| ID | D-042 |
|----|------|
| **Title** | Customer org hierarchy depth (parent org, sites) |
| **Context** | Portal and B2B billing may need levels. |
| **Options considered** | (a) Flat customer + sites; (b) Multi-level org; (c) External IdP groups |
| **Recommended option** | (a) until revenue requires (b) |
| **Downstream impact** | CRM model, portal |
| **Blocking status** | Non-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +120 days |

---

### Quoting

| ID | D-007 |
|----|------|
| **Title** | Quote change after send / after customer view |
| **Context** | Trust and billing integrity; OPS TODO. |
| **Options considered** | (a) New revision only; (b) Editable until accepted; (c) Staff waiver with audit |
| **Recommended option** | (a) + (c) for exceptions |
| **Downstream impact** | Quote API, portal, job linkage |
| **Blocking status** | Release-blocking |
| **Owner** | Commercial + Product |
| **Target decision date** | TBD +45 days |

| ID | D-043 |
|----|------|
| **Title** | Who may accept quote: portal customer vs staff override |
| **Context** | Authority and audit trail. |
| **Options considered** | (a) Customer-only + staff with permission; (b) Staff-only MVP; (c) Dual sign-off high value |
| **Recommended option** | (a) |
| **Downstream impact** | Portal + quoting routes |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +60 days |

| ID | D-044 |
|----|------|
| **Title** | Accept quote concurrency (two sessions accept) |
| **Context** | Race on single quote. |
| **Options considered** | (a) First wins + 409 for second; (b) Lock on open; (c) Idempotent accept |
| **Recommended option** | (a) |
| **Downstream impact** | Quoting service |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

---

### Dispatch & jobs

| ID | D-003 |
|----|------|
| **Title** | Dispatch-ready checklist (enforce vs advisory) |
| **Context** | OPS TODO: parts + compliance before send. |
| **Options considered** | (a) Hard gate in API; (b) Warnings only; (c) Config profile per customer |
| **Recommended option** | (a) with override permission + reason |
| **Downstream impact** | Job assign, inventory, equipment readiness |
| **Blocking status** | Release-blocking |
| **Owner** | Product + Ops |
| **Target decision date** | TBD +45 days |

| ID | D-006 |
|----|------|
| **Title** | Reassignment mid-job: punch, telemetry, customer notify |
| **Context** | Payroll continuity and customer expectation. |
| **Options considered** | (a) Close open punch + mandatory reason + optional notify; (b) Transfer punch (complex); (c) Block reassignment if punched in |
| **Recommended option** | (a) |
| **Downstream impact** | Dispatch routes, time, comms |
| **Blocking status** | Compliance-blocking |
| **Owner** | Product + HR/Ops |
| **Target decision date** | TBD +45 days |

| ID | D-008 |
|----|------|
| **Title** | Cancellation after dispatch: stock release, SLA, restock charges |
| **Context** | Revenue and inventory reconciliation. |
| **Options considered** | (a) Workflow with finance approval if parts moved; (b) Auto-release soft reserve; (c) Manual only |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Job status, inventory, billing |
| **Blocking status** | Release-blocking |
| **Owner** | Product + Finance |
| **Target decision date** | TBD +60 days |

| ID | D-018 |
|----|------|
| **Title** | Partial completion vs blocked vs new sub-job |
| **Context** | Engineer cannot complete until requirements satisfied. |
| **Options considered** | (a) Stay blocked until done; (b) `partial` status + revisit job; (c) Force complete with waiver |
| **Recommended option** | (b) + waiver permission |
| **Downstream impact** | Job completion service |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

| ID | D-045 |
|----|------|
| **Title** | Who may transition job status (engineer vs dispatcher vs system) |
| **Context** | RBAC and automation hooks. |
| **Options considered** | (a) Matrix by status; (b) Engineer limited set; (c) Admin-only for cancel |
| **Recommended option** | (a) documented per D-001 |
| **Downstream impact** | All job PATCH routes |
| **Blocking status** | Release-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +60 days |

| ID | D-046 |
|----|------|
| **Title** | Job requirement bundles: which job types mandatory |
| **Context** | Completion gate depends on configured requirements. |
| **Options considered** | (a) Template per `work_type`; (b) Per contract; (c) Manual per job |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Job forms/media/signatures |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance + Product |
| **Target decision date** | TBD +60 days |

| ID | D-047 |
|----|------|
| **Title** | `GET /jobs` query params for engineers (status, date range) |
| **Context** | Currently filtered by assignee; filters not fully documented. |
| **Options considered** | (a) Add optional filters; (b) Client-side only; (c) Paginated cursor |
| **Recommended option** | (a) minimal set |
| **Downstream impact** | Mobile, API |
| **Blocking status** | Non-blocking |
| **Owner** | Principal Engineer + Product |
| **Target decision date** | TBD +120 days |

---

### Engineer assignment & dispatch intelligence

| ID | D-014 |
|----|------|
| **Title** | Competency expiry: hard block vs override |
| **Context** | OPS TODO; regulatory risk if unqualified assignee. |
| **Options considered** | (a) Block assign; (b) Override with permission + reason; (c) Warn only |
| **Recommended option** | (a) + (b) |
| **Downstream impact** | Assign job, recommendations |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance + Ops |
| **Target decision date** | TBD +45 days |

| ID | D-048 |
|----|------|
| **Title** | Offer job vs hard assign (expiry, fallback) |
| **Context** | Mobile list is assignment-based today. |
| **Options considered** | (a) Hard assign only MVP; (b) Offer with timeout; (c) Bidding (out of scope) |
| **Recommended option** | (a) then (b) |
| **Downstream impact** | Dispatch UX, notifications |
| **Blocking status** | Non-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +120 days |

| ID | D-049 |
|----|------|
| **Title** | Assign-best / recommendations: error codes when no engineer |
| **Context** | API contract for empty result vs 400. |
| **Options considered** | (a) 200 + empty payload + reason; (b) 404; (c) 422 unmet constraints |
| **Recommended option** | (a) with structured `reason_code` |
| **Downstream impact** | Dispatcher UI |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

---

### Tracking & telemetry

| ID | D-011 |
|----|------|
| **Title** | Telemetry + PII retention |
| **Context** | Legal minimization vs operations history. |
| **Options considered** | (a) 90d events / 1y aggregates; (b) Customer-defined; (c) Infinite |
| **Recommended option** | (a) pending legal |
| **Downstream impact** | DB purge, map history |
| **Blocking status** | Compliance-blocking |
| **Owner** | DPO + Product |
| **Target decision date** | TBD +60 days |

| ID | D-050 |
|----|------|
| **Title** | Business thresholds for fresh / aging / stale telemetry |
| **Context** | Env vars exist; product thresholds for map vs auto-assign differ. |
| **Options considered** | (a) Single table by use case; (b) Global constants; (c) Per customer |
| **Recommended option** | (a) |
| **Downstream impact** | Dispatch map, recommendations |
| **Blocking status** | Feature-blocking |
| **Owner** | Product + Ops |
| **Target decision date** | TBD +90 days |

| ID | D-051 |
|----|------|
| **Title** | Telemetry: batch ingest vs single, rate limits, clock skew |
| **Context** | Mobile may batch offline points later. |
| **Options considered** | (a) Single POST only MVP; (b) Batch endpoint; (c) Server reorder by `occurred_at` |
| **Recommended option** | (c) + (b) in phase 2 |
| **Downstream impact** | Tracking API, mobile |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

---

### Time & attendance

| ID | D-016 |
|----|------|
| **Title** | Punch duplicate / overlapping intervals & corrections |
| **Context** | Wage compliance; punch immutability. |
| **Options considered** | (a) Reject overlap; (b) Adjustment record only; (c) Supervisor edit with audit |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Time routes, payroll export |
| **Blocking status** | Compliance-blocking |
| **Owner** | HR/Ops + Product |
| **Target decision date** | TBD +45 days |

| ID | D-052 |
|----|------|
| **Title** | Punch → timesheet → payroll approval chain |
| **Context** | Who approves (supervisor role vs manager field). |
| **Options considered** | (a) Role `Ops_Manager` approves; (b) Per-user manager; (c) External payroll only |
| **Recommended option** | (b) long-term; (a) interim |
| **Downstream impact** | Time module, RBAC |
| **Blocking status** | Feature-blocking |
| **Owner** | Finance/Ops + Product |
| **Target decision date** | TBD +90 days |

| ID | D-053 |
|----|------|
| **Title** | GPS required for punch vs optional with flag |
| **Context** | Indoor / device failure. |
| **Options considered** | (a) Required with override permission; (b) Optional with compliance warning; (c) Always optional |
| **Recommended option** | (b) |
| **Downstream impact** | Mobile, audit |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance + Product |
| **Target decision date** | TBD +60 days |

| ID | D-054 |
|----|------|
| **Title** | Duplicate punch API response shape (idempotent replay) |
| **Context** | Mobile retries need clear contract. |
| **Options considered** | (a) 200 + same body; (b) 409 + existing id; (c) Idempotency-Key |
| **Recommended option** | (a)+(c) |
| **Downstream impact** | Time API |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

---

### Compliance & certificates

| ID | D-004 |
|----|------|
| **Title** | Certificate matrix: job/work_type/asset → cert type + validity |
| **Context** | Regulatory mapping not fully documented in product layer. |
| **Options considered** | (a) Master matrix doc + config table; (b) Code enums only; (c) Per contract override |
| **Recommended option** | (a)+(c) |
| **Downstream impact** | Completion gates, portal docs |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance lead + Product |
| **Target decision date** | TBD +45 days |

| ID | D-055 |
|----|------|
| **Title** | Certificate void/regenerate: supersession chain, no silent delete |
| **Context** | Audit and customer trust. |
| **Options considered** | (a) Void + reason + new cert id; (b) Delete draft only; (c) Regenerate in place |
| **Recommended option** | (a) |
| **Downstream impact** | Compliance service, storage |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance lead |
| **Target decision date** | TBD +60 days |

| ID | D-056 |
|----|------|
| **Title** | Certificate PDF generation: sync vs async + failure UX |
| **Context** | Timeouts and retries. |
| **Options considered** | (a) Async job + notify; (b) Sync with long timeout; (c) Manual regenerate |
| **Recommended option** | (a) |
| **Downstream impact** | API, engineer mobile |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

| ID | D-057 |
|----|------|
| **Title** | Template version governance for certificates |
| **Context** | Which template version applies to issued cert. |
| **Options considered** | (a) Pin version at issue; (b) Always latest; (c) Contract-specific |
| **Recommended option** | (a) |
| **Downstream impact** | Compliance templates |
| **Blocking status** | Compliance-blocking |
| **Owner** | Compliance lead |
| **Target decision date** | TBD +60 days |

| ID | D-058 |
|----|------|
| **Title** | Customer-visible certificates on portal |
| **Context** | Which doc types exposed vs internal-only. |
| **Options considered** | (a) Customer-facing list per job; (b) All issued; (c) Customer request flow |
| **Recommended option** | (a) |
| **Downstream impact** | Portal |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

---

### Invoicing & finance

| ID | D-009 |
|----|------|
| **Title** | Invoice generation gates (job milestone vs permission-only) |
| **Context** | Finance permissions exist; business rule for when generate is allowed not unified. |
| **Options considered** | (a) Require `job.status=completed`; (b) Milestone flags; (c) Commercial approval |
| **Recommended option** | (a) + optional milestone for deposits |
| **Downstream impact** | Invoicing routes, job flow |
| **Blocking status** | Release-blocking |
| **Owner** | Finance + Product |
| **Target decision date** | TBD +45 days |

| ID | D-017 |
|----|------|
| **Title** | Credit note / refund: in-app vs export-only vs external system of record |
| **Context** | OPS TODO; audit parity. |
| **Options considered** | (a) PHI-DPS credit note entity + export; (b) External only; (c) Full ERP sync |
| **Recommended option** | (a) for MVP |
| **Downstream impact** | Invoicing schema, finance queue |
| **Blocking status** | Release-blocking |
| **Owner** | Finance |
| **Target decision date** | TBD +60 days |

| ID | D-059 |
|----|------|
| **Title** | When finance hold on invoice is mandatory vs optional |
| **Context** | `finance_reviewed` and permissions; business policy varies. |
| **Options considered** | (a) High-value threshold; (b) All commercial jobs; (c) Manual only |
| **Recommended option** | (a) configurable |
| **Downstream impact** | Invoicing workflow |
| **Blocking status** | Feature-blocking |
| **Owner** | Finance + Product |
| **Target decision date** | TBD +90 days |

| ID | D-060 |
|----|------|
| **Title** | Payment capture: in-app vs external + callback failures |
| **Context** | Pay endpoint vs real PSP. |
| **Options considered** | (a) Mark paid manually + reference; (b) Webhook from PSP; (c) No payment in MVP |
| **Recommended option** | (a) until (b) integrated |
| **Downstream impact** | Invoicing, webhooks |
| **Blocking status** | Release-blocking |
| **Owner** | Finance + Engineering |
| **Target decision date** | TBD +60 days |

---

### Contracts & commercial

| ID | D-015 |
|----|------|
| **Title** | SLA clock: business calendar vs wall-clock (MVP) |
| **Context** | OPS TODO; `PHI_DPS_ACCEPTANCE_POLICY_MODE` interacts with workflows. |
| **Options considered** | (a) Wall-clock MVP; (b) Calendar + holidays import; (c) Customer-specific windows |
| **Recommended option** | (a) then (b) |
| **Downstream impact** | SLA services, contracts |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

| ID | D-061 |
|----|------|
| **Title** | Amendment vs activation ordering (single diagram of record) |
| **Context** | Many paths in codebase; engineers need one diagram. |
| **Options considered** | (a) Product publishes flowchart + links to env modes; (b) Code as docs; (c) BPMN |
| **Recommended option** | (a) |
| **Downstream impact** | Commercial hub, contracts team |
| **Blocking status** | Release-blocking |
| **Owner** | Commercial + Product |
| **Target decision date** | TBD +60 days |

| ID | D-062 |
|----|------|
| **Title** | Acceptance policy mode truth table (`PHI_DPS_ACCEPTANCE_POLICY_MODE`) |
| **Context** | Engineers need matrix: mode × action → requirement. |
| **Options considered** | (a) Markdown matrix in `/docs`; (b) In-app help; (c) Automated tests as spec |
| **Recommended option** | (a)+(c) |
| **Downstream impact** | Contract activation, e-sign |
| **Blocking status** | Compliance-blocking |
| **Owner** | Commercial + Compliance |
| **Target decision date** | TBD +60 days |

| ID | D-063 |
|----|------|
| **Title** | Which contract version is operative for field work |
| **Context** | Multiple versions; field confusion. |
| **Options considered** | (a) Active version pointer on contract; (b) Job pins version at create; (c) Latest always |
| **Recommended option** | (b) |
| **Downstream impact** | Job, portal, PDFs |
| **Blocking status** | Feature-blocking |
| **Owner** | Product + Commercial |
| **Target decision date** | TBD +90 days |

| ID | D-064 |
|----|------|
| **Title** | E-sign webhook payload contract & template registry versioning |
| **Context** | Provider-specific; regression risk on upgrade. |
| **Options considered** | (a) Versioned webhook handler + fixture tests; (b) Provider doc link only; (c) Stub only |
| **Recommended option** | (a) |
| **Downstream impact** | Webhooks, contracts |
| **Blocking status** | Release-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +60 days |

| ID | D-065 |
|----|------|
| **Title** | Commercial vs Finance boundary on repricing vs invoice hold |
| **Context** | RBAC ambiguity. |
| **Options considered** | (a) RACI doc; (b) System enforces order; (c) Same person dual role |
| **Recommended option** | (a)+(b) where possible |
| **Downstream impact** | Permissions, workflow |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

---

### Inventory & stock

| ID | D-010 |
|----|------|
| **Title** | Stock reservation moment & consumption vs release on cancel |
| **Context** | Financial variance if ambiguous. |
| **Options considered** | (a) Soft reserve at dispatch-ready, consume on parts submit; (b) Reserve at job create; (c) No reserve |
| **Recommended option** | (a) |
| **Downstream impact** | Inventory service, job cancel |
| **Blocking status** | Release-blocking |
| **Owner** | Ops + Finance |
| **Target decision date** | TBD +45 days |

| ID | D-066 |
|----|------|
| **Title** | Van stock vs warehouse: where mobile deducts |
| **Context** | Field vans vs central stock. |
| **Options considered** | (a) Engineer van location only; (b) Choose at pick; (c) Warehouse-only MVP |
| **Recommended option** | (a) where van model exists |
| **Downstream impact** | Parts usage API, mobile |
| **Blocking status** | Feature-blocking |
| **Owner** | Ops + Product |
| **Target decision date** | TBD +90 days |

| ID | D-067 |
|----|------|
| **Title** | Strict parts reconciliation: block vs override path |
| **Context** | `STRICT_PARTS_RECONCILIATION` env exists. |
| **Options considered** | (a) Block completion; (b) Ops override + audit; (c) Warn |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Job completion |
| **Blocking status** | Compliance-blocking |
| **Owner** | Ops + Finance |
| **Target decision date** | TBD +60 days |

| ID | D-068 |
|----|------|
| **Title** | Serial/lot traceability scope (regulated flows) |
| **Context** | OPS TODO P2. |
| **Options considered** | (a) Out of MVP; (b) Lot on job lines only; (c) Full trace |
| **Recommended option** | (a) or (b) for regulated vertical |
| **Downstream impact** | Inventory model |
| **Blocking status** | Non-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +180 days |

---

### Portal & customer experience

| ID | D-069 |
|----|------|
| **Title** | Portal job list scope and customer-visible fields |
| **Context** | API gaps for portal vs internal. |
| **Options considered** | (a) Minimal fields; (b) Parity with contract; (c) Configurable visibility |
| **Recommended option** | (a) + contract for expansion |
| **Downstream impact** | Portal routes |
| **Blocking status** | Feature-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +90 days |

---

### Communications & rollout

| ID | D-070 |
|----|------|
| **Title** | Customer comms idempotency with provider (SendGrid etc.) |
| **Context** | Duplicate sends on retry. |
| **Options considered** | (a) Provider idempotency key; (b) DB dedupe on id; (c) At-least-once + accept dupes |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Comms service, webhooks |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer |
| **Target decision date** | TBD +90 days |

---

### Mobile & field operations

| ID | D-012 |
|----|------|
| **Title** | Mobile offline queue: size, conflict policy, max age |
| **Context** | OPS TODO; data loss risk. |
| **Options considered** | (a) SQLite queue + FIFO replay; (b) 7d TTL; (c) Block writes when offline |
| **Recommended option** | (a)+(b) |
| **Downstream impact** | Flutter app, API idempotency |
| **Blocking status** | Feature-blocking |
| **Owner** | Principal Engineer + Product |
| **Target decision date** | TBD +90 days |

| ID | D-071 |
|----|------|
| **Title** | No GPS / engineer offline: punch and telemetry behavior |
| **Context** | Edge cases in §7 of source doc. |
| **Options considered** | (a) Block punch without fix; (b) Allow with reason code; (c) Manual coords |
| **Recommended option** | (b) with audit |
| **Downstream impact** | Mobile, time, compliance flags |
| **Blocking status** | Compliance-blocking |
| **Owner** | Product + Compliance |
| **Target decision date** | TBD +60 days |

---

### CRM / Finance cross-cutting

| ID | D-019 |
|----|------|
| **Title** | Customer dispute: freeze invoicing? case entity? |
| **Context** | Ad-hoc email vs system of record. |
| **Options considered** | (a) `Case` entity linked to customer/job; (b) Tag + manual hold; (c) External CRM |
| **Recommended option** | (a) minimal |
| **Downstream impact** | CRM, invoicing holds |
| **Blocking status** | Feature-blocking |
| **Owner** | Commercial + Product |
| **Target decision date** | TBD +90 days |

---

### Dispatch — revisit & follow-on

| ID | D-072 |
|----|------|
| **Title** | Revisit required: follow-on job from defect vs manual job |
| **Context** | Code may support follow-on; product rule unclear. |
| **Options considered** | (a) Auto follow-on from defect workflow; (b) Dispatcher creates linked job; (c) Same job reopen |
| **Recommended option** | (b) + link to parent |
| **Downstream impact** | Dispatch routes |
| **Blocking status** | Non-blocking |
| **Owner** | Product Owner |
| **Target decision date** | TBD +120 days |

---

## 3. Register maintenance

| Action | Frequency | Owner |
|--------|-----------|-------|
| Triage **Open** Release-blocking | Weekly | Product Owner |
| Align with `PHI_DPS_MISSING_EXECUTION_DETAILS.md` | When gaps doc changes | Principal Engineer |
| Archive **Decided** to ADR or `/docs/domain` | Per decision | Accountable owner |

---

## 4. Document control

| Field | Value |
|-------|--------|
| **Version** | 1.0 |
| **Derived from** | `PHI_DPS_MISSING_EXECUTION_DETAILS.md` |
| **Related** | `HANDOVER.md`, `OPS_ALIGNMENT_TODO.md`, `backend/app/services/authorization_policy.py` |

---

*This register is a living document; update status and dates as decisions close.*
