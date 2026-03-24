# PHI-DPS — Current implemented logic audit (code-truth)

**Document type:** Evidence-based audit of **what the code does today**.  
**Scope:** Backend (FastAPI), admin web (`web/`), engineer mobile (`mobile/`).  
**Method:** Repository inspection; behavior labeled **explicit** (enforced in code), **implicit** (convention/string), **partial** (some paths only), **missing** (not implemented).

---

## 1. Canonical enums and transition rules

### 1.1 Job statuses

| What the code does | Evidence |
|--------------------|----------|
| **DB default** | `Job.status` default `"created"` (`backend/app/modules/dispatch/models.py`). |
| **String column** | `String(64)` — **no DB enum constraint**; any string can be stored if written. |
| **Values observed in services** | `created` (create_job); engineer accept sets `"accepted"` (`dispatch/routes.py` engineer_accept_job_endpoint → `update_job_status(..., "accepted")`); punch-in sets `"on_site"` (`time_tracking/service.py` `punch_in`); punch-out sets `"completion_pending_forms"` then calls `try_finalize_job_completion_if_possible` (`time_tracking/service.py` `punch_out`). |
| **Completion gate** | `try_finalize_job_completion_if_possible` (`dispatch/service.py`): if no requirements → inventory gate; if requirements exist and not all `satisfied_at` → `completion_blocked_forms` (default `blocked_status`); if parts strict blocks → `completion_blocked_inventory`; else `completed` (default `completed_status`). |
| **Terminal / active sets** | `TERMINAL_JOB_STATUSES = {"completed", "closed", "cancelled"}`; `ON_JOB_STATUSES = {"in_progress"}` (`dispatch/availability_service.py`). **Note:** Many code paths use `"in_progress"` but default job creation uses `"created"` — **implicit inconsistency** unless transitions always rename status. |
| **Live map** | `live_map_service.py` uses `TERMINAL_JOB_STATUSES` from availability_service for non-terminal jobs. |
| **Transitions** | `update_job_status` (`dispatch/service.py`) **assigns any string** passed in — **no central allow-list** in that function. Dispatcher `POST /jobs/{id}/status` uses payload `status` with `JobStatusUpdateIn`. |

**Frontend (`web/src/App.tsx`):** Job creation validates **accepted** quote client-side. **Backend** `create_job` (`dispatch/service.py`) only requires `customer_id` or `quote_id`; it does **not** enforce quote `status == accepted`. **Explicit gap:** direct API calls can create jobs from non-accepted quotes unless another layer blocks (none in audited `create_job`).

**Mobile:** Lists jobs via `GET /jobs`; displays `status` string only.

| Classification | **implicit** + **partial** enforcement (fragile enum). |

---

### 1.2 Quote statuses

| What the code does | Evidence |
|--------------------|----------|
| **DB default** | `Quote.status` default `"draft"` (`quoting/models.py`). |
| **accept_quote** | Sets `status = "accepted"` and `accepted_at` (`quoting/service.py`); calls `reserve_parts_for_quote`. **No check** that quote was `draft` before accept in the snippet — **verify** `accept_quote` for duplicate accept. |
| **Other values** | Not centrally enumerated; **stringly-typed**. |

**Frontend:** `acceptQuote` + job form require quote `status === "accepted"` (case-insensitive) before create job (`web/src/App.tsx`).

| Classification | **implicit**; **partial** parity (web stricter than API may be). |

---

### 1.3 Lead statuses

| What the code does | Evidence |
|--------------------|----------|
| **DB default** | `Lead.status` default `"new"` (`crm/models.py`). |
| **Convert** | `lead.status = "converted"` on convert (`crm/service.py`). |
| **Other lifecycle** | **Not** implemented as a state machine in audited paths; **stringly-typed**. |

| Classification | **implicit**; **minimal** transitions in code. |

---

### 1.4 Invoice statuses

| What the code does | Evidence |
|--------------------|----------|
| **DB default** | `Invoice.status` default `"unpaid"` (`invoicing/models.py`); column `String(16)`. |
| **Service values** | `generate_invoice` sets `status="unpaid"`; `hold_invoice` → `"held"`; `release_invoice_from_hold` → `"unpaid"`; `pay_invoice` → `"paid"` (`invoicing/service.py`). |
| **Filters** | `list_invoices` filters by `status`; reconciliation uses `unpaid`, `held`, `paid`. |

**Refund/credit note:** **Not** implemented in-app; `finance_operations_dashboard` exposes `credit_notes_and_adjustments.in_app_supported: False` (`invoicing/service.py`).

| Classification | **explicit** for `unpaid` | `held` | `paid`; **no** credit note entity in audited paths. |

---

### 1.5 Contract / amendment / activation (statuses)

| What the code does | Evidence |
|--------------------|----------|
| **Contract** | `Contract.status` default `"active"`; `renewal_status` with comment listing values (`contracts/models.py`). **String fields.** |
| **Amendment blocking for policy** | `blockers_for_activation` filters amendments with `ContractAmendment.status.in_(("approved", "scheduled"))` (`acceptance_policy_service.py`). |
| **Full contract state machine** | **Not** summarized in one place in this audit; large `contracts/` surface — **partial** documentation in code. |

| Classification | **partial** + **config-driven** acceptance policy (separate section). |

---

### 1.6 Punch / timesheet states

| What the code does | Evidence |
|--------------------|----------|
| **Punch.kind** | `"in"` or `"out"` only (`time_tracking/models.py` comment + usage). |
| **Punch.valid** | Boolean; punch-out can be `valid=False` if outside geofence (`time_tracking/service.py`). |
| **TimesheetApproval.status** | Default `"approved"` (`time_tracking/models.py`). |
| **Transitions** | `punch_in` requires geofence + assignment check; `punch_out` requires previous `in` (`time_tracking/service.py`). **`punch_in` does not check for an existing unclosed `in` punch** — duplicate `in` rows are **possible** (**explicit** gap in `punch_in`). |

**Offline:** `offline_device_id` on `Punch` model — **field present**; **idempotency** not verified in audit.

| Classification | **explicit** for `in`/`out`; **partial** duplicate handling (needs full file read for production claim). |

---

### 1.7 Inconsistencies (summary)

| Issue | Detail |
|-------|--------|
| Job status strings | `availability_service` uses `in_progress` for “on job”; jobs default `created` — **naming drift** across modules unless all transitions normalize. |
| Backend vs web | Quote/job **extra** validation in `App.tsx` may exceed API — **backend is source of truth** for security; risk if API called directly. |
| No central enum registry | Statuses are **mostly** free strings in DB. |

---

## 2. RBAC matrix as currently implemented

### 2.1 Static permission keys and role baselines

**File:** `backend/app/services/authorization_policy.py`

- **Keys:** `ALL_PERMISSION_KEYS` — e.g. `can_hold_invoice`, `can_release_invoice`, `can_mark_finance_review`, PO keys, contract comms keys, `can_override_vehicle_block`, `can_override_equipment_block`, `can_manage_labour_rules`, `can_admin_permission_grants`, `can_admin_org_access`, `can_run_ops_automation`, AI drafting, break-glass comms, etc.
- **Role → permissions:** `ROLE_PERMISSIONS`: `Admin` = all keys; `Finance`, `Commercial`, `Ops_Manager`, `Dispatcher`, `Engineer`, `Client`, `Viewer` mapped with finite sets; **Engineer** and **Client** and **Viewer** have **empty** permission sets (`frozenset()`).

### 2.2 Resolution order

**File:** `backend/app/services/authorization_service.py`  
`user_has_permission`: deny grant → allow grant → group deny → group allow → role baseline.

### 2.3 Route dependencies

- **Widespread:** `require_roles(...)` on routers (`deps.py`).
- **Fine-grained:** `require_permission_http(current_user, CAN_*, db=db)` used on **subset** of routes (e.g. `invoicing/routes.py` hold/release with `CAN_HOLD_INVOICE` / `CAN_RELEASE_INVOICE`; `vehicles` override; `labour` routes; `contracts` partial; `inventory` partial; `automation`; `ai/drafting`).

**Approximate pattern:** `require_roles` **many** endpoints; `require_permission` **fewer** — invoice hold is **both** role **and** permission (explicit in `invoicing/routes.py`).

### 2.4 Group / scoped access

**Files:** `scoped_access_service.py`, `org_access_service.py`, models under `auth/org_access_models.py`.  
**Behavior:** Internal entity visibility (contracts/sites) layered for non-Admin users; **Admin** bypasses scopes (per HANDOVER-style docs). **Not** re-derived in full in this audit.

### 2.5 Engineer / mobile-relevant API

| Endpoint area | Implementation |
|---------------|----------------|
| `GET /jobs` | `list_jobs_endpoint`: **Admin, Dispatcher, Engineer** — engineers filtered to assigned jobs only (`dispatch/routes.py` + `service.list_jobs`). |
| `POST /time/punch/*` | Engineer role (`time_tracking/routes.py`). |
| `POST /tracking/telemetry/engineer` | Engineer only (`tracking/routes.py`). |
| `POST /quotes`, `POST /crm/leads` | **Not** engineer (quoting/crm routes). |

### 2.6 Frontend

**File:** `web/src/App.tsx`  
Single SPA; **no** separate RBAC matrix in frontend — relies on API **401/403** and whatever tabs are shown (likely all tabs for logged-in user — **verify** if UI hides by role).

**Gap:** If UI shows buttons but API returns 403, **implicit** UX failure — **not** fully audited per screen.

| Classification | **explicit** in backend for roles; **partial** fine-grained coverage. |

---

## 3. Compliance certificate matrix (code-implied)

| What the code does | Evidence |
|--------------------|----------|
| **Model** | `Certificate`: `certificate_type` `String(32)`; `status` default `"generated"` (`compliance/models.py`). |
| **Invoice gate** | `generate_invoice` requires **at least one** certificate for job with `status.in_(["generated", "signed"])` (`invoicing/service.py`). |
| **Central matrix** | **No** `job.work_type` → `certificate_type` table found in audit; **not config-driven** in reviewed files. |
| **Creation** | `compliance/service.py` passes `certificate_type` from payload (`schemas.py` has `certificate_type: str`). |

| Classification | **implicit** typing; **hardcoded** behavior only where tests/docs add rules; **not** a full regulatory matrix in code. |

---

## 4. Finance rules currently implemented

| Rule | Backend | UI |
|------|---------|-----|
| **Generate invoice** | `job.status == "completed"` **and** compliance certificate exists (`generated` or `signed`) (`invoicing/service.py` `generate_invoice`). | Web calls API; **not** verified for duplicate guard in UI. |
| **Hold** | `hold_invoice`: cannot hold `paid`; cannot double-hold (`invoicing/service.py`). Route: `require_roles` + `require_permission_http(..., CAN_HOLD_INVOICE)` (`invoicing/routes.py`). | |
| **Release** | `release_invoice_from_hold`: must be `held` (`invoicing/service.py`). Permission `CAN_RELEASE_INVOICE` on route. | |
| **Pay** | `pay_invoice`: cannot pay if `held`; idempotent if already `paid` (`invoicing/service.py`). **No** external PSP callback in audited function — sets `paid_at` internally. | |
| **Finance review** | `mark_invoice_finance_reviewed` / `clear_invoice_finance_review` — blocks if `paid` (`invoicing/service.py`). **Permission** keys on routes (`routes.py`). | |
| **Credit notes** | **Explicitly not in-app** — dashboard JSON (`invoicing/service.py`). | |

| Classification | **explicit** for generate/hold/release/pay; **missing** external payment webhooks in audited `pay_invoice`. |

---

## 5. Contract acceptance policy (`PHI_DPS_ACCEPTANCE_POLICY_MODE`)

**Files:** `backend/app/services/acceptance_policy_service.py`, `backend/app/core/config.py` (`Settings.ACCEPTANCE_POLICY_MODE`), `.env.example`.

### 5.1Modes (explicit allowed set)

`acceptance_policy_mode()` returns one of:

- `warn_only`
- `require_formal_acceptance_for_amendment`
- `require_formal_acceptance_for_activation`
- `require_provider_esign_for_activation`
- `require_provider_esign_for_amendment_and_activation`  

Invalid env → **`warn_only`**.

### 5.2 Blockers

- **`blockers_for_amendment_creation`:** formal `ProposalAcceptanceRecord` or provider e-sign depending on mode (`acceptance_policy_service.py`).
- **`blockers_for_activation`:** formal acceptance and/or provider e-sign per mode; uses `has_completed_any_acceptance_record` / `has_completed_provider_esign`.

**Note:** `blockers_for_activation` contains nested `if mode == "require_formal_acceptance_for_activation"` inside a tuple that lists `require_formal_acceptance_for_amendment` — **only** activation mode triggers formal block in that inner branch (code structure).

### 5.3 API surface

- `acceptance_policy_matrix()` static rows; `evaluate_policy_blockers_summary` for dashboards (`acceptance_policy_service.py`).
- Contracts/amendment services import blockers (`amendment_service.py`, `contract_version_service.py`).

| Classification | **explicit** env-driven policy; **partial** truth table spread across functions + tests (`test_proposal_esign_acceptance_policy.py`). |

---

## 6. Mobile offline and conflict behavior

**File:** `mobile/lib/main.dart` (and `auth_token.dart`).

| Capability | Status |
|------------|--------|
| **Offline queue** | **Missing** — no SQLite/outbox; all calls are immediate `http`. |
| **Retries** | **Missing** — no automatic retry layer. |
| **Idempotency** | **Missing** — no `Idempotency-Key` header on requests. |
| **Telemetry replay** | **Best-effort only** — throttled sends; failures show status text; **no** queue. |
| **Punch replay** | **Best-effort** — `unawaited` telemetry before punch; **no** duplicate protection. |
| **Conflict handling** | **Missing**. |
| **Punch model** | Backend accepts `offline_device_id` in schema (`time_tracking`); **mobile does not set** it in audited `main.dart` punch body. |

| Classification | **missing** for production offline; **explicit** online-only behavior. |

---

## 7. Hard NFR-related logic already present

| Area | What exists | Evidence |
|------|-------------|----------|
| **Health** | `GET /health` returns `{"status":"ok","service":"phi-dps-api"}` | `backend/app/main.py` |
| **Readiness** | `GET /health/ready` runs `SELECT 1`; **503** on failure | `main.py` |
| **JSON access log** | Optional `PHI_DPS_LOG_JSON_ACCESS`; skips `/health` and `/health/ready` | `main.py` `json_access_log_middleware`, `config.py` |
| **Telemetry freshness** | `PHI_DPS_TELEMETRY_FRESH_SECONDS`, `PHI_DPS_TELEMETRY_AGING_SECONDS`, `PHI_DPS_OPERATIONAL_POSITION_MODE`, `PHI_DPS_DISPATCH_RECOMMEND_STALE`, `PHI_DPS_AVG_VEHICLE_SPEED_MPS` | `backend/app/core/config.py` |
| **Parts strict** | `PHI_DPS_STRICT_PARTS_RECONCILIATION` | `config.py` |
| **CORS** | `PHI_DPS_CORS_ORIGINS` | `config.py` |
| **Document storage** | Local/S3 settings, presigned TTL | `config.py` |
| **Startup** | `create_all`, `migrate_sqlite_schema`, bootstrap, rollout scheduler, warm cache | `main.py` `on_startup` |
| **Retention jobs** | **Not** found as scheduled purge in audit — **missing** or in scripts not read. |
| **Rate limits** | **Not** seen in `main.py` middleware — **missing** global rate limit. |
| **Request timeouts** | **Not** configured in audited `main.py` — **implicit** Uvicorn defaults. |

**Deployment docs:** `DEPLOYMENT.md`, `PRODUCTION_CHECKLIST.md` describe ops; **not** re-quoted here.

| Classification | **explicit** health/ready/log; **partial** telemetry config; **missing** retention/rate-limit in app code. |

---

## A. Current behavior that is already production-usable

- Health/readiness endpoints for load balancers (`main.py`).
- JWT auth + role checks on most routes (`deps.py`, routers).
- Invoice lifecycle **service** rules (hold/release/pay) with permission checks on key routes (`invoicing/`).
- Acceptance policy **centralized** in `acceptance_policy_service.py` with env mode.
- Job completion gate with **forms/inventory** branches (`try_finalize_job_completion_if_possible`).
- Engineer job list **scoped** to assignee (`dispatch/routes.py` + `service.list_jobs`).
- Engineer telemetry endpoint with JWT identity (`tracking/routes.py`).

---

## B. Current behavior that is fragile or inconsistent

- **Job status** strings not enforced by a single enum (DB or service).
- **`in_progress` vs `created` / `on_site` / `completion_pending_forms`** drift across availability vs job lifecycle.
- **Quote accept** may not enforce prior state (depends on full `accept_quote`).
- **Web-only validation** for leads/jobs vs API direct calls.
- **Punch** geofence required — mobile app **must** have geofence configured or punch fails (`time_tracking/service.py`); **implicit** coupling.
- **Duplicate punch-in** not rejected by `punch_in` (`time_tracking/service.py`).
- **Mobile:** no offline/idempotency — **fragile** on poor networks.

---

## C. Business-critical areas where code and docs may not align

- **Invoice generation** requires **compliance certificate** — product docs may say “invoice when job done” without **certificate** requirement (`invoicing/service.py`).
- **Credit notes** explicitly **external** in finance dashboard JSON — docs promising “in-app credit” would **misalign**.
- **Acceptance policy** modes are **env-only** — must match legal/commercial runbooks.
- **Job from quote:** UI requires **accepted** quote; **API** does not — policy docs assuming “API always matches UI” would **misalign**.

---

## D. Top 20 code-truth findings for product owners (before freezing policy)

1. Job statuses are **not** centrally enumerated in DB.
2. `availability_service` terminal vs job `update_job_status` **naming** may differ for `in_progress`.
3. Invoice generation **hard-requires** `job.status == completed` **and** certificate `generated|signed`.
4. Credit notes **in_app_supported: False** in finance dashboard payload.
5. Acceptance policy **five** modes + invalid → `warn_only`.
6. Engineer **GET /jobs** returns **only assigned** jobs.
7. Quote `accept` sets `accepted` **only**; no revision model in `accept_quote` snippet.
8. Lead `converted` only on convert; no other lead states enforced.
9. Punch **requires** geofence row for job.
10. Punch-out drives completion pipeline and **may** set `completion_blocked_*`.
11. `PHI_DPS_STRICT_PARTS_RECONCILIATION` affects completion (`try_finalize` / inventory).
12. Telemetry freshness uses **env seconds** (`config.py`).
13. `LOG_JSON_ACCESS` optional structured access log.
14. **No** API rate limit in `main.py` audit.
15. **No** telemetry retention purge in app startup.
16. Mobile: **no** offline queue.
17. Mobile: **no** idempotency keys.
18. RBAC: **Engineer** has **zero** fine-grained permission keys by default.
19. Invoice hold requires **both** role set **and** `can_hold_invoice` where implemented.
20. **`create_job`** does not validate quote **`accepted`** (UI-only check in `web`); certificate `certificate_type` remains a **free string** with **no** central job-type matrix in audited compliance code.

---

## Mobile app — implemented vs. remaining (for planning)

### Implemented (evidence: `mobile/lib/main.dart`, `mobile/lib/auth_token.dart`, tests)

- Login via `POST /auth/token`; token parsed with `parseAccessTokenFromAuthJson` (`auth_token.dart`).
- `GET /jobs` for assigned jobs; job picker + manual job id field.
- `POST /tracking/telemetry/engineer` with throttling (GPS stream + periodic).
- `POST /time/punch/in` and `/out` with lat/lon JSON.
- Android manifest: `INTERNET`, cleartext, location permissions.
- iOS: NSAppTransportSecurity local networking.
- Widget + unit tests (`test/widget_test.dart`, `test/auth_token_test.dart`).

### Not implemented (same files)

- Offline queue / retry / sync.
- Idempotency headers.
- Vehicle inspection, forms, media, parts, certificates, calendar, leave.
- Setting `offline_device_id` on punch.
- Rich job detail / SLA / customer contact.

### Backend capabilities available but **not** wired in mobile

- `/vehicles/{id}/inspections` for engineers with `assigned_vehicle_id` (`vehicles/routes.py`).
- Job completion requirements, compliance, inventory — other clients (web).

---

**End of audit.**  
*Update when refactors add enums, mobile offline, or central validation.*
