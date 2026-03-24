# PHI-DPS — Missing execution details (engineering specification gaps)

**Audience:** Architects, tech leads, product owners, senior engineers.  
**Purpose:** Complement `HANDOVER.md`, vision docs, and `OPS_ALIGNMENT_TODO.md` by listing **implementation-critical** decisions that are still ambiguous or only partially encoded in code/UI.  
**Constraint:** This document does **not** restate product vision; it exposes **guesswork** that would block production-grade delivery.

---

## 1. Executive summary

**What PHI-DPS is (one paragraph)**  
PHI-DPS is a **field-service and compliance-oriented M&E operations platform** delivered as a monorepo: a **FastAPI** backend with broad domain coverage (CRM, quoting, dispatch, tracking/telemetry, time punch, compliance certificates, invoicing, inventory/parts usage, contracts including amendments and activation, customer communications, e-sign integration, rollout automation, and operational diagnostics), a **React** admin web app, and a **Flutter** engineer mobile client. Integrations (email/SMS, object storage, optional AI drafting, DocuSign-style e-sign) are environment-driven; RBAC combines **named roles** with **fine-grained permission keys** and optional **per-user / group grants** and **scoped entity access**.

**What is already well-defined**  
- **Operations runbooks (engineering):** `HANDOVER.md`, `DEPLOYMENT.md`, `PRODUCTION_CHECKLIST.md`, `.env.example` — how to run, deploy, audit env vars, health checks, backups, recurring jobs, CORS/API URL model for the SPA.  
- **Security baseline:** JWT auth, role + permission resolution (`authorization_policy.py` + grants), webhook HMAC patterns documented at a high level.  
- **Marathon delivery history:** `MARATHON_PIPELINE.md` marks many feature gates “Done” at a product milestone level.  
- **Known product gaps (prioritized):** `OPS_ALIGNMENT_TODO.md` (offline mobile, SLA realism, dispatch-ready checks, etc.).  
- **Concrete code reality:** Many routes and models exist; **behavior is not always fully specified** outside code (status strings, side effects, idempotency, cross-module rules).

**What remains ambiguous for “no-guesswork” engineering**  
- **Canonical domain vocabulary:** Allowed lifecycle states per entity, invalid transitions, and **one source of truth** (vs stringly-typed `status` fields).  
- **End-to-end business rules:** What happens when quotes change after acceptance, jobs cancel after dispatch, stock is short, certificates fail generation, or telemetry is stale — **policy** is not fully documented for all paths.  
- **RBAC product matrix:** Code defines roles (`Admin`, `Finance`, `Commercial`, `Ops_Manager`, `Dispatcher`, `Engineer`, `Client`, `Viewer`) and permission keys; **your** org may want names like `super_admin` / `warehouse_admin` **mapped** to these — mapping and “who may do what per screen” for **every** workflow is not a single signed-off matrix in-repo.  
- **Non-functional targets:** Performance, scale, RTO/RPO, retention, mobile offline — **partially** implied by `DEPLOYMENT.md`, not locked as SLOs.  
- **API as contract:** OpenAPI may exist at runtime, but **pagination defaults, sorting guarantees, idempotency keys, and validation parity** between web/mobile and server are not fully specified as a reviewed document.

---

## 2. Missing domain decisions

Each row is a **product decision** still open or only partially implemented; engineers currently infer behavior from code paths, UI checks, or convention.

### Lead lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Canonical lead states** | Drives automation (chase, SLA, conversion) | `Lead` may lack a strict enum in UX vs DB | States: `new` → `qualified` → `converted` \| `lost` \| `archived`; define `lost_reason`, `owner_user_id`. |
| **Conversion prerequisites** | Blocks bad CRM data | Web validates copy length; **server** may not mirror all checks | **Server-side** mirror: contact + minimum issue description; optional required fields for sector (gas/oil/electrical). |
| **Duplicate leads** | Data quality | Unclear merge vs reject | Default: soft-duplicate detection on email+phone; manual merge by Admin/Dispatcher only. |

### Customer lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Customer vs site vs contract hierarchy** | Portal scoping, job addressing | Model exists but **operational rules** vary | Document: when a job **must** reference `site_id` / `contract_id` for compliance vs reactive cash work. |
| **Credit hold / account status** | Dispatch and invoicing | Not always explicit in one place | Add `account_status` (or use contract flags): `active` / `on_hold` / `closed`; block dispatch when on hold if finance says so. |

### Quote lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Allowed quote statuses** | Billing integrity | `draft` / `accepted` / others used inconsistently | Enum: `draft` → `sent` → `accepted` \| `rejected` \| `expired`; **no silent edit** after `sent` — use **revision** (new quote version or amendment record). |
| **Revision after customer viewed** | Trust and audit | OPS TODO calls this out | After `sent`, changes create **new revision** with trace to parent; acceptance binds to **revision id**. |
| **Acceptance authority** | Who can accept | Portal vs staff | Define: customer acceptance path + staff override with audit. |

### Job lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Canonical job statuses** | Reporting and automation | `Job.status` is stringly; many transitions in code | Product must publish enum + diagram: e.g. `created` → `dispatched` → `accepted` (engineer) → `on_site` → `completed` \| `completion_blocked_*` \| `cancelled`. |
| **Who moves status** | RBAC | Engineer vs dispatcher vs system | Define triggers: engineer accept vs dispatcher force-complete vs system gate (forms). |
| **Cancellation economics** | Revenue and parts | Open | Cancellation **after** parts reserved: policy for restock charges, who approves. |

### Engineer assignment lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Assign vs engineer self-accept** | Mobile list semantics | Recently fixed: engineers see **assigned** jobs only on `GET /jobs` | Document: optional workflow “offer job” vs “hard assign”; if offered, expiry time and fallback assignee. |
| **Reassignment mid-job** | Safety and billing | Partial rules in dispatch endpoints | Define: require **reason**, notify customer option, **punch** validity (close open punch?), telemetry handoff. |
| **Competency gating** | Compliance | OPS TODO | Block assignment if required competency expired; **override** requires named permission + reason. |

### Dispatch-ready rules  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Definition of “dispatch-ready”** | Prevents bad sends | OPS TODO: parts + compliance | Checklist: accepted quote revision, address geocoded or confirmed, **equipment readiness** evaluated, **parts** available or policy “materials_optional”, vehicle not blocked. |
| **Stale telemetry** | ETA and safety | Env vars for freshness exist; **business** thresholds not unified | Define: `fresh` / `aging` / `stale` thresholds per use case (map vs auto-assign). |

### Certificate lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Regime per job type** | CP12 / gas safety etc. | Templates exist; **which job types require which cert** | Compliance matrix: `job.work_type` + `asset` → required certificate **type** and **validity period**. |
| **Regeneration / void** | Audit | Open | Void with reason + supersession link; never delete issued PDF without audit. |
| **Customer-visible vs internal** | Portal | Define portal document set per job. |

### Invoice lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **When invoice may be generated** | Revenue recognition | Finance permissions exist | Rule: invoice only after **job completion** or explicit **milestone** flag; hold/release semantics already permission-based — document **business** when hold is mandatory. |
| **Credit note / refund** | OPS TODO | External finance | Default: **export-only** credit note record in PHI-DPS + reference to external system until integrated. |

### Contract lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Amendment vs activation ordering** | Large surface in codebase | Many policy envs | Single diagram: proposal → review → customer response → e-sign → activation; **parallel** paths for repricing vs legal amendment. |
| **Acceptance policy modes** | `PHI_DPS_ACCEPTANCE_POLICY_MODE` | Engineers need truth table | Document matrix: which actions require formal acceptance / e-sign per mode. |

### Stock reservation and consumption lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Reserve at job create vs dispatch vs on-site** | Inventory truth | Implementation-specific | Default: **soft reserve** at dispatch-ready; **consume** on parts usage submit; **release** on cancel if unissued. |
| **Negative stock** | Warehouse policy | Strict mode env exists | Define: `STRICT` blocks completion; override path = Ops + audit. |
| **Van stock vs warehouse** | Field reality | Model-dependent | Define whether mobile deducts from **van location** only. |

### Timesheet and payroll approval lifecycle  
| Decision title | Why it matters | Guesswork risk | Recommended default |
|----------------|----------------|----------------|---------------------|
| **Punch → timesheet → payroll** | Payroll disputes | Punch exists; approval chain may be incomplete in spec | States: `submitted` → `supervisor_approved` → `payroll_locked`; define who is supervisor (role vs manager field). |
| **Duplicate / overlapping punches** | Wage compliance | Open | Block duplicate open punch; overlapping intervals = **error** unless override with reason. |

---

## 3. Canonical domain model that still needs to be locked

**Note:** PHI-DPS already has many SQLAlchemy models; this section is a **specification checklist**, not an instruction to duplicate tables. Use it to ensure **documentation and APIs** align with the same entity names and keys.

### Identity & access (`modules/auth`, org access)  
| Entity | Purpose | Key fields | Relationships | Indexes | Lifecycle timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|----------------------|--------------|----------------|
| `User` | Staff & engineer login | `id`, `email`, `is_active`, `assigned_vehicle_id` | ↔ `Role` M2M; grants | `email` unique | `created_at` if present | Prefer **deactivate** vs delete | Break-glass admin accounts? |
| `Role` | Named role baseline | `name` | ↔ `User` | `name` unique | — | No | Map product roles to `authorization_policy.ROLE_PERMISSIONS` |
| `UserPermissionGrant` | Override role | `permission_key`, `effect`, `expires_at` | → `User` | user+key | `expires_at` | Deactivate | |
| `InternalAccessGroup` / scopes | Entity visibility | group ids, scopes | memberships | — | — | Soft-delete group? | Exact scope granularity for contracts/sites |

### CRM (`modules/crm`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Lead` | Pre-customer pipeline | contact, issue, status | → `Customer` on convert | status, created | `created_at` | Archive vs delete | |
| `Customer` | Bill-to / portal identity | name, email | → jobs, contracts, sites | email | | | Hierarchy vs org chart depth |

### Commercial / quoting (`modules/quoting`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Quote` / `QuoteItem` | Pricing package | `status`, totals | → customer, job (optional) | customer, status | | Prefer revision not delete | Revision table vs new quote id |

### Dispatch (`modules/dispatch`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Job` | Work unit | `status`, `address`, `assigned_engineer_id`, `quote_id`, `contract_id` | engineer, quote, requirements | status, engineer, created | `created_at`, `scheduled_at` | **No** — cancel | Canonical status enum |
| `Job*Requirement` / submissions | Completion evidence | requirement keys, `satisfied_at` | → job | job_id | | N/A | Which jobs mandatory? |

### Tracking (`modules/tracking`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `EngineerTelemetryEvent` / `EngineerLatestLocation` | Live map + dispatch | lat/lon, freshness | → engineer user | engineer_id | `occurred_at` | Events append-only | Retention window |
| `Vehicle*` | Fleet tracking | vehicle id, assignment | engineer | | | | |

### Time (`modules/time_tracking`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Punch` | In/out | job_id, times | → job, user | job, user | punch times | **Immutable** edit rules | GPS required? |

### Compliance (`modules/compliance`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Certificate` | Regulatory PDF/metadata | type, job_id, expiry | job, asset | job, type | issued_at, expires_at | Void + supersede | Template version governance |

### Invoicing (`modules/invoicing`)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Invoice` | AR | `status`, `finance_reviewed` | job | job, status | | | Payment capture in-app vs external |

### Inventory (`modules/inventory` — if present)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Stock` / `Movement` / `PartsUsage` | Van + warehouse | sku, qty, location | job lines | sku, location | | | Serial/lot (OPS TODO) |

### Contracts (`modules/contracts` + related)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| `Contract`, `ContractVersion`, amendments, activation runs | Legal + operational | status, version | customer, sites | | | Version never deleted | Which version is “operative” for field |

### Communications / rollout (multiple modules)  
| Entity | Purpose | Key fields | Relationships | Indexes | Timestamps | Soft delete? | Open questions |
|--------|---------|------------|---------------|---------|------------|--------------|----------------|
| Customer comms records, rollout notifications | Auditable delivery | delivery status, provider ids | contract/job | | | | Idempotency with provider |

---

## 4. Required state machines

**Instruction:** Publish each as a diagram + table in `/docs/domain` and align **API errors** to illegal transitions.

### `Quote`  
- **Allowed states (minimum):** `draft`, `sent`, `accepted`, `rejected`, `expired`, `superseded` (optional).  
- **Valid transitions:** `draft`→`sent`; `sent`→`accepted`|`rejected`|`expired`; `draft`→`superseded` (optional).  
- **Invalid:** `accepted`→`draft` (no); any change to monetary fields on `accepted` without new revision.  
- **Triggers:** user send, customer accept API, expiry job, staff manual close.  
- **Audit:** who accepted, when, IP/portal user id if applicable.

### `Job`  
- **Allowed states:** product-defined superset (see §2); code uses many strings — **must be frozen**.  
- **Valid transitions:** e.g. `created`→`dispatched`; `dispatched`→`accepted` (engineer); …→`completed`; `*`→`cancelled` with rules.  
- **Invalid:** `completed`→`dispatched` without reopen workflow; engineer-only paths for dispatcher-only statuses.  
- **Triggers:** assign, engineer accept, status PATCH (role-gated), completion gate satisfied, cancel.  
- **Audit:** status change log (who, from, to, reason).

### `Assignment` (logical, may be `Job.assigned_engineer_id` + timestamps)  
- **States:** `unassigned` → `assigned` → `reassigned` / `accepted_by_engineer`.  
- **Invalid:** assign to engineer lacking competency (unless override).  
- **Audit:** reassignment reason mandatory.

### `Punch` session  
- **States:** `none`, `open_in` (on a job), `closed`.  
- **Invalid:** two open punches for same user without overlap resolution.  
- **Audit:** punch times immutable; correction = adjustment record.

### `Invoice`  
- **States:** `draft`, `issued`, `paid`, `held`, `void` (if supported).  
- **Invalid:** `paid`→`draft`.  
- **Audit:** finance review flags already in API — document business meaning.

### `ContractVersion` / activation  
- **States:** per contracts module (draft proposal → active).  
- **Invalid:** skip legally required acceptance when policy mode requires it.  
- **Audit:** e-sign events, webhook receipts.

### `StockMovement` (if implemented)  
- **States:** `reserved` → `picked` → `consumed` \| `released`.  
- **Invalid:** consume without pick on strict van policy (if chosen).

---

## 5. RBAC matrix that must be defined

**Code baseline today:** Roles in DB: `Admin`, `Finance`, `Commercial`, `Ops_Manager`, `Dispatcher`, `Engineer`, `Client`, `Viewer`. Fine-grained keys in `authorization_policy.py` (invoice hold, POs, contract comms, overrides, org access, AI drafting, etc.). **Engineer** has **no** fine-grained keys by default (`frozenset()`). Many routes use **`require_roles(...)`** only.

**Product-owner mapping (proposed naming alignment)**  

| Product label | Map to code role | Notes |
|---------------|------------------|-------|
| `super_admin` | `Admin` + break-glass procedures | “Super” is operational, not a second codebase role unless added to DB. |
| `ops_admin` | `Ops_Manager` + parts of `Dispatcher` | Clarify who runs diagnostics vs dispatch. |
| `dispatcher` | `Dispatcher` | |
| `engineer` | `Engineer` | Mobile + punch + telemetry; **no** finance keys. |
| `finance_admin` | `Finance` | Invoice + PO approvals as per keys. |
| `compliance_admin` | **TBD** — often `Admin` or `Ops_Manager` + training | Code has no single `Compliance` role; **must decide** ownership of certificate templates / overrides. |
| `warehouse_admin` | **TBD** — inventory routes may be `Admin` / `Ops_Manager` | Define if warehouse is separate role in DB. |
| `customer_portal_user` | `Client` | Portal routes separate prefix; scoped by customer/org. |

**Matrix skeleton (must be completed per module)** — mark **ambiguous** until signed off.

| Module / capability | Admin | Finance | Commercial | Ops_Manager | Dispatcher | Engineer | Client | Viewer |
|---------------------|-------|---------|------------|-------------|------------|----------|--------|--------|
| CRM leads/customers CRUD | full | ? | ? | ? | ? | read? | none | read? |
| Quotes create/send | full | ? | full | ? | ? | none | partial (portal?) | none |
| Jobs create/assign/reassign | full | no | ? | ? | full | partial (accept own) | none | read? |
| Dispatch map / ETA | full | ? | ? | ? | full | own | tracking subset | none |
| Telemetry ingest | full | no | no | no | no | own | no | no |
| Punch / timesheets | full | ? | no | ? | ? | own | none | none |
| Certificates issue/void | full | no | ? | ? | ? | field submit? | view? | none |
| Invoices / finance review | full | full | partial | no | no | none | portal pay/view? | none |
| Contracts / amendments | full | partial | full | partial | no | none | portal | none |
| Inventory / parts | full | ? | no | full | ? | issue parts? | none | none |
| Org access / grants | full | no | no | no | no | no | no | no |

**Ambiguous permissions needing explicit signoff**  
- **Engineer:** which job completion APIs vs read-only.  
- **Dispatcher:** can override SLA / equipment block without Ops permission?  
- **Viewer:** read scope — global vs entity-scoped only.  
- **Commercial vs Finance:** repricing vs invoice hold boundaries.

---

## 6. API contract gaps

**General gaps (all modules)**  
- **Pagination:** `limit`/`offset` common; **default limits**, max caps, and **total count** return not always specified for list endpoints.  
- **Sorting:** Often implicit (e.g. `created_at desc`); **must be documented** per list.  
- **Filtering:** Query params partially implemented; **contract** for combined filters missing.  
- **Idempotency:** Webhooks document HMAC; **mutating** POSTs from mobile (punch, telemetry) need **idempotency-Key** policy for retries.  
- **Validation parity:** Admin web may validate stricter than API (e.g. leads/jobs) — **server must be source of truth**.

**Module-specific**  

| Module | Missing / weak contract areas |
|--------|------------------------------|
| **Auth** | Token refresh / revoke strategy; password policy; lockout. |
| **CRM** | Lead convert idempotency; duplicate handling response. |
| **Quoting** | Accept quote: exact body, concurrency if two accept. |
| **Jobs** | Engineer `GET /jobs` — now filtered; document **query params** if extended (`status`, date). Job status PATCH — allowed values list in OpenAPI schema. |
| **Dispatch intelligence** | Recommendations / assign-best: error codes when no engineer. |
| **Tracking** | Telemetry: batch vs single; rate limits; clock skew on `occurred_at`. |
| **Time** | Punch: duplicate detection response shape. |
| **Compliance** | Certificate generate: async vs sync; failure body. |
| **Invoicing** | Pay/hold: payment provider callback vs internal only. |
| **Inventory** | Parts usage: line validation, strict mode errors. |
| **Contracts** | Webhook payloads for e-sign; versioning of template registry. |
| **Portal** | Customer-visible fields; job list scope. |

---

## 7. Edge cases and failure scenarios

| Scenario | Expected system behavior (to specify & implement consistently) | Affected modules | Audit trail | User-visible alerts |
|----------|------------------------------------------------------------------|------------------|-------------|---------------------|
| **Engineer offline** | Queue mutations on device; replay with idempotency; show sync state | Mobile, all write APIs | append-only sync log | Engineer: banner; Dispatcher: stale telemetry |
| **No GPS** | Punch may be blocked or allowed with manual reason + compliance risk flag | Time, dispatch | reason code | Engineer warning |
| **Late / out-of-order telemetry** | Accept with `occurred_at`; reconcile “latest” vs “freshest” policy (`PHI_DPS_OPERATIONAL_POSITION_MODE`) | Tracking | event log | Map freshness badge |
| **Duplicate punches** | Reject second open punch; idempotent replay returns same result | Time | duplicate attempt logged | Clear error to engineer |
| **Job reassignment mid-visit** | Close or migrate punch; notify customer optional; map re-center | Dispatch, time, comms | reassignment reason | Dispatcher + engineer |
| **Missing stock** | Block completion if strict; else allow with `materials_optional` + approval | Inventory, job completion | override id | Ops task |
| **Quote revised after acceptance** | Immutable accepted revision; new quote id for new money | Quoting, jobs | linkage | Commercial |
| **Failed certificate generation** | Retry policy; job stays `completion_blocked`; engineer notified | Compliance | error detail | Engineer + compliance queue |
| **Failed invoice callback** | DLQ / manual finance queue | Invoicing, diagnostics | failure row | Finance |
| **Expired qualification** | Block assignment; override permission | Competence, dispatch | override | Dispatcher |
| **Customer disputes** | Freeze invoicing? open case object? | CRM, invoicing, contracts | case log | Commercial |
| **Partial completion** | Job stays blocked or new sub-job / revisit flag | Dispatch, job requirements | | |
| **Revisit required** | Follow-on job from defect (code may exist) vs manual | Dispatch | link to parent job | |
| **Cancelled after dispatch** | Release stock, stop SLA clock, notify engineer | Dispatch, inventory, comms | cancel reason | All parties per policy |

---

## 8. Non-functional requirements that must be made explicit

| Area | What to lock | Current doc/code hints |
|------|--------------|-------------------------|
| **Performance** | p95 API latency targets for map, job list, punch; batch sizes | Not in SLO form |
| **Scale** | Max engineers, jobs/day, telemetry events/sec, DB size growth | Guess from deployment |
| **Availability** | Multi-region? single region RTO | `DEPLOYMENT.md` process-level |
| **Backup / recovery** | RPO/RTO for DB + S3 documents | `DEPLOYMENT.md` general guidance |
| **Retention** | Telemetry events, audit logs, PDFs, comms bodies | Legal vs cost — **not** fully specified |
| **Security logging** | `PHI_DPS_LOG_JSON_ACCESS`; what counts as PII in logs | Partial |
| **Observability** | Which dashboards/alerts are **required** for go-live | Diagnostics endpoints exist |
| **Mobile offline** | Queue size, conflict policy, max age of queued ops | `OPS_ALIGNMENT_TODO.md` |
| **File uploads** | Max size, MIME, virus scan, storage backend | Document storage envs |
| **API timeouts / retries** | Client retry backoff; server timeout for PDF gen | Handover mentions fragility, not numbers |

---

## 9. Priority decisions for product owner — “Must decide before continuing”

Ranked by **implementation risk × business impact** for a compliance-heavy M&E field service product.

| # | Decision | Affected modules | Risk if ambiguous | Recommendation |
|---|----------|------------------|-------------------|----------------|
| 1 | **Canonical enums** for `Job.status`, `Quote.status`, lead/customer account states | All | Reporting nonsense, bad automation | Workshop + publish diagram; align DB constraints |
| 2 | **Server-side validation parity** with web/mobile for leads, quotes, jobs | CRM, quoting, dispatch | Security & data integrity | Pydantic validators + tests |
| 3 | **Dispatch-ready checklist** (commercial + ops + compliance) | Dispatch, inventory, contracts | Wrong dispatches | Product checklist keyed off job/quote |
| 4 | **Reassignment + punch rules** mid-job | Dispatch, time | Payroll & safety disputes | Mandatory policy doc |
| 5 | **Telemetry retention + PII** | Tracking, security | Legal / cost | Retention schedule |
| 6 | **Offline-first mobile contract** (idempotency, conflicts) | Mobile | Data loss or duplicates | Queue spec + API keys |
| 7 | **Certificate matrix** (job/asset → cert type) | Compliance | Regulatory gap | Signed compliance table |
| 8 | **Stock reservation moment** | Inventory | Financial variance | Default in §2 |
| 9 | **Quote change after send** | Quoting | Customer disputes | Revision-only rule |
| 10 | **Cancellation policy** post-dispatch | Dispatch, finance, inventory | Revenue leakage | Business signoff |
| 11 | **Invoice generation gates** | Invoicing | Early billing | Tie to job milestone |
| 12 | **Credit note scope** | Invoicing | Audit | In-app vs external |
| 13 | **RBAC matrix** completion for Viewer/Dispatcher/Engineer edge cases | Auth | Over/under permission | §5 workshop |
| 14 | **Warehouse role** existence | Auth, inventory | Wrong approvals | Add role or map to Ops |
| 15 | **Compliance admin role** | Auth, compliance | Orphan processes | Assign to Admin/Ops |
| 16 | **SLA clock** (calendar vs wall) | Contracts, dispatch | Wrong SLA breaches | OPS TODO — decide MVP |
| 17 | **Customer dispute object** | CRM, invoicing | Ad-hoc email | Minimal case entity |
| 18 | **Partial completion semantics** | Dispatch | Blocked forever vs split jobs | Define |
| 19 | **API pagination/sort** standard | All APIs | Client bugs | Document per resource |
| 20 | **NFR SLOs** (p95, RPO) | Infra | Unbounded spend / incidents | One-page SLO |

---

## Document control

- **Owner:** Product + principal engineer (joint).  
- **Update when:** Any new domain entity, status string, or permission key ships without updating this spec.  
- **Related:** `HANDOVER.md`, `DEPLOYMENT.md`, `OPS_ALIGNMENT_TODO.md`, `backend/app/services/authorization_policy.py`, OpenAPI export from FastAPI.

---

*Generated for PHI-DPS execution readiness — field-service & compliance M&E context.*
