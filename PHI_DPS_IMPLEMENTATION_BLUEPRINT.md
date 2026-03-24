# PHI-DPS — Implementation blueprint

**Audience:** Engineers implementing features aligned with `PHI_DPS_PRODUCT_DECISIONS_REGISTER.md`.  
**Status:** Implementation guidance — **assumes recommended options in the decisions register are approved defaults** until an item is formally `Decided` and amended via ADR/ticket.  
**Rule:** Do **not** invent business rules beyond this blueprint + closed ADRs + `backend/` code that is already authoritative.

**Related:** `HANDOVER.md`, `DEPLOYMENT.md`, `PHI_DPS_MISSING_EXECUTION_DETAILS.md`, `OPS_ALIGNMENT_TODO.md`.

---

## How to read this document

| Column | Meaning |
|--------|---------|
| **Decision IDs** | Tie-back to `PHI_DPS_PRODUCT_DECISIONS_REGISTER.md` |
| **Assumed default** | Recommended option from register — **change only after PO signoff** |
| **Code anchor** | Primary package/path in repo today |

---

## Global conventions (apply to all modules)

### Assumed defaults (cross-cutting)

| Topic | Assumed default | Decision IDs |
|-------|-----------------|--------------|
| Job/quote status | Enforce via Pydantic + DB constraints after migration | D-001, D-002 |
| API list params | `limit` default 50, max 200; `offset` default 0; document sort per resource | D-021 |
| Idempotency | `Idempotency-Key` header on punch + critical POSTs; 24h server-side store | D-022 |
| Pagination response | Prefer `items` + `total` where feasible | D-021 |
| Audit | Status changes, financial events, override actions → `audit_log` / domain tables | D-001–D-072 |

### Domain entities (logical, cross-module)

- **Party:** `User`, `Customer`, portal `Client` identity.  
- **Commercial:** `Lead`, `Customer`, `Quote`, `QuoteItem`, `Contract`, contract versions/amendments.  
- **Operations:** `Job`, assignments, `Punch`, telemetry events, `Vehicle`, engineer qualifications.  
- **Compliance:** `Certificate`, job requirement bundles, equipment readiness.  
- **Money:** `Invoice`, (future) `CreditNote` per D-017.  
- **Stock:** inventory locations, movements, parts usage lines (strict mode per env).

### Webhooks / events (inbound)

| Source | Router / path pattern | Notes |
|--------|-------------------------|-------|
| Communications provider | `POST /webhooks/communications/provider` | HMAC per `.env.example` |
| E-sign provider | `POST /webhooks/esign/provider` | Provider-specific headers |
| Rollout | `POST /rollout/notifications/webhooks/{channel}` | `X-Event-Id`, `X-Signature` |
| SendGrid (optional) | Documented in `.env.example` | Ingest secret |

### Background / scheduled work

| Mechanism | Path / trigger | Notes |
|-----------|----------------|------|
| Recurring system jobs | `PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py` | Cron or `POST /system/jobs/run-due` |
| Rollout runner | `PHI_DPS_ROLLOUT_RUNNER_ENABLED` | Prefer off in multi-replica prod |
| SQLite migrations | `migrate_sqlite_schema` on startup | Postgres: separate migration tool |
| Telemetry retention purge | **Implement when D-011/D-025 decided** | Scheduled job or external |

### Permissions (fine-grained keys)

**Source of truth:** `backend/app/services/authorization_policy.py` — `ALL_PERMISSION_KEYS`, `ROLE_PERMISSIONS`.  
**Enforcement:** `require_permission(...)` or `user_has_permission(...)` + route `require_roles(...)`.

### Frontend (admin web)

**Code anchor:** `web/src/App.tsx` (tabbed shell), `web/src/config.ts` (API base).  
**Map integration:** `web/src/phase4/LiveDispatchMap.tsx`.

### Mobile

**Code anchor:** `mobile/lib/main.dart` — engineer login, jobs, punch, telemetry.

---

# 1. Platform & cross-cutting API

**Decision IDs:** D-005, D-021, D-022, D-023, D-020, D-025–D-029.

## Domain entities

- `ApiIdempotencyRecord` (proposed) — key hash, route, user, response fingerprint, `created_at`, TTL.
- `AuditLog` — existing audit module.

## DB tables & relationships

| Table | Relationships | Notes |
|-------|---------------|-------|
| *(proposed)* `idempotency_keys` | → `users.id` optional | Only if D-022 implemented |
| `audit_logs` | polymorphic target refs | Extend metadata for idempotency replay |

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| *Convention* | All `GET` list | `limit`, `offset`; validate caps |
| *Future* | `POST` punch, telemetry, pay | Accept `Idempotency-Key` |

## Service-layer responsibilities

- **Central validators:** Mirror `web` rules for leads/quotes/jobs in Pydantic `Field` validators / `@model_validator` (D-005).
- **Pagination helper:** Shared dependency `Pagination` with `limit_max=200`.
- **Idempotency middleware** (optional): For selected routes, return cached 200/409.

## Validation rules

- Reject `limit` > 200 with `422`.
- Unicode/normalize email on CRM where applicable.

## Background jobs

- Nightly: purge expired idempotency rows (if table exists).

## Events/webhooks

- N/A at platform layer (consume in integrations module).

## Permissions

- N/A (infrastructure).

## Audit logging

- Log idempotent replay: `action=idempotent_replay`, `idempotency_key=hash`.

## Frontend screens

- Global error toast for `422` validation (parity with server).

## Mobile screens

- Send `Idempotency-Key` UUID per offline replayed request (D-012).

## Test cases

- Parametrize: `limit=201` → 422.
- Same `Idempotency-Key` + same body → identical response; different body → 409.

## Rollout notes

- Ship validation parity **before** advertising mobile offline queue.

## Migration risks

- DB constraint on `jobs.status` may require data cleanup script before `ALTER CHECK`.

---

# 2. Identity & access (auth, admin, org access)

**Decision IDs:** D-013, D-030–D-036, D-023.

## Domain entities

- `User`, `Role`, `user_roles`, `UserPermissionGrant`, `InternalAccessGroup`, `GroupPermissionGrant`, scoped entity links.

## DB tables & relationships

**Code anchor:** `backend/app/modules/auth/models.py`, `org_access_models.py`, `permission_models.py`.

- `users` — `id`, `email`, `hashed_password`, `is_active`, `assigned_vehicle_id`.
- `roles` — `name` unique.
- `user_roles` — M2M.
- `user_permission_grants` — per-key allow/deny, `expires_at`.
- Internal groups + memberships + entity scopes (§5.13 enterprise).

## API endpoints

| Prefix | Router | Notes |
|--------|--------|-------|
| `/auth` | `modules/auth/routes.py` | Token, me |
| `/auth` admin | `modules/auth/admin_routes.py` | Users, roles, grants |

## Service-layer responsibilities

- `authorization_service` — effective permissions, grant CRUD.
- `scoped_access_service` — internal entity visibility.
- Password hashing — `passlib` / `hash_password`.

## Validation rules

- Email format; unique email; password complexity **when D-023 decided** (document min length interim).

## Background jobs

- Expire grants: optional cron to soft-deactivate expired rows (if not query-filtered only).

## Events/webhooks

- None outbound; inbound N/A.

## Permissions

- `can_admin_permission_grants`, `can_admin_org_access` — see `authorization_policy.py`.
- **Assumed mapping (D-013):** Product labels → DB roles: `super_admin` → `Admin` + procedures; `warehouse_admin` → `Ops_Manager` or new role when D-031 decided.

## Audit logging

- All grant changes, role assignments, break-glass (D-035) with actor + reason.

## Frontend screens

- Admin user list, permission grants UI (if exposed), org access (if enabled).

## Mobile screens

- Login only; token storage.

## Test cases

- Engineer has no finance keys by default.
- Deny grant overrides allow for same key.

## Rollout notes

- Bootstrap users off in prod (`PHI_DPS_DEV_BOOTSTRAP=0`).

## Migration risks

- Adding `Warehouse` role (D-031) requires seed migration + `ROLE_PERMISSIONS` update.

---

# 3. CRM (leads, customers)

**Decision IDs:** D-037–D-042, D-019, D-039.

## Domain entities

- `Lead`, `Customer` (+ future `Case` for disputes D-019).

## DB tables & relationships

**Code anchor:** `backend/app/modules/crm/models.py`.

- Leads → convert → Customer; jobs/quotes reference `customer_id`.

## API endpoints

| Prefix | Path examples |
|--------|----------------|
| `/crm` | `POST /crm/leads`, `GET /crm/leads`, `POST /crm/leads/{id}/convert`, `GET /crm/customers` |

## Service-layer responsibilities

- Lead create/update; convert idempotent response (D-039); duplicate detection hook (D-038).

## Validation rules

- **Assumed (D-005):** At least one of email/phone; issue description min length (match `web/src/App.tsx`); server mirrors.

## Background jobs

- Optional: nightly duplicate lead report.

## Events/webhooks

- None required for MVP.

## Permissions

- `require_roles("Admin", "Dispatcher", ...)` per route — **verify each endpoint**.

## Audit logging

- Lead convert: customer id, lead id, actor.

## Frontend screens

- Leads tab, customers tab in `App.tsx`.

## Mobile screens

- None unless field CRM added.

## Test cases

- Convert twice returns stable customer / 409 per D-039.
- `on_hold` customer blocks dispatch when D-041 implemented (`account_status` field).

## Rollout notes

- Add `account_status` column + backfill `active`.

## Migration risks

- Customer hold (D-041) touches dispatch assign validation.

---

# 4. Quoting

**Decision IDs:** D-002, D-007, D-043, D-044.

## Domain entities

- `Quote`, `QuoteItem`; revision link `supersedes_quote_id` *(when implemented)*.

## DB tables & relationships

**Code anchor:** `backend/app/modules/quoting/models.py`.

- `quotes.status` — migrate to constrained enum.
- Items cascade delete or soft-delete per policy.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/quotes` | `POST /quotes`, `GET /quotes`, `GET /quotes/{id}`, `POST /quotes/{id}/accept`, send if exists |

## Service-layer responsibilities

- `quoting/service.py` — create, accept; **block monetary edit** if status ≥ sent (D-007); create new quote for new money with `supersedes_quote_id`.

## Validation rules

- Accept: concurrency — first wins; second `409` with current quote state (D-044).
- Job creation from quote: quote must be `accepted` (align web + server).

## Background jobs

- Quote expiry job (optional): `sent` → `expired` after N days (product config).

## Events/webhooks

- Optional: notify commercial on accept.

## Permissions

- Commercial create/send; Finance visibility per matrix (D-013).

## Audit logging

- Accept event: user id, timestamp, quote revision id.

## Frontend screens

- Quotes section in `App.tsx`; validation parity.

## Mobile screens

- None.

## Test cases

- Two parallel accepts → one 200, one 409.
- Edit line item on `sent` → 400.

## Rollout notes

- Data migration: map legacy inconsistent statuses to new enum.

## Migration risks

- Existing accepted quotes with edited rows — **data audit script** before constraint.

---

# 5. Dispatch — jobs, assignment, completion

**Decision IDs:** D-001, D-003, D-006, D-008, D-018, D-045, D-046, D-047, D-048, D-014.

## Domain entities

- `Job`, `JobFormRequirement`, submissions, media, signatures, parts usage, equipment readiness, **assignments** (on job row).

## DB tables & relationships

**Code anchor:** `backend/app/modules/dispatch/models.py`, `service.py`.

- `jobs` — `status`, `assigned_engineer_id`, `quote_id`, `contract_id`, `site_id`, addresses, SLA fields.
- Requirement / submission tables per type.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/jobs` | `GET ""` (list), `POST ""`, `GET /{id}`, `POST /{id}/assign`, `POST /{id}/accept`, `POST /{id}/status`, completion bundles |
| `/dispatch` | See §6 |

## Service-layer responsibilities

- `list_jobs` — Admin/Dispatcher all; Engineer filtered by `assigned_engineer_id`.
- `assign_job` — competency check (D-014); block if expired unless override permission + reason stored.
- `dispatch_ready` **gate** (D-003): callable before assign — quote accepted, address ok, equipment policy, parts policy, vehicle block check.
- **Reassignment (D-006):** close open punch or migrate — **implement single policy**: e.g. auto punch-out on reassignment with reason.
- **Cancel (D-008):** release soft reservation (inventory), set status `cancelled`, SLA stop, optional charge line (future).

## Validation rules

- Status transitions only if allowed by state machine (D-001).
- Engineer cannot list others’ jobs (already enforced on list).

## Background jobs

- SLA risk recompute (existing contract hooks); stale job reminders.

## Events/webhooks

- Optional: customer notify on reassignment (comms module).

## Permissions

- `require_roles` per route; overrides `can_override_vehicle_block`, `can_override_equipment_block` where applicable.

## Audit logging

- Every `status` change: from, to, actor, reason (mandatory for cancel/reassign).

## Frontend screens

- Jobs, dispatch tabs; Live map; assign UI.

## Mobile screens

- Job list (assigned only), job id punch, telemetry.

## Test cases

- Engineer GET jobs only assigned.
- Assign without competency → 400; with override + reason → 200.
- Reassignment writes audit row.

## Rollout notes

- Feature-flag `DISPATCH_READY_ENFORCED=true` when D-003 ready.

## Migration risks

- Enum migration on `jobs.status` may break reporting dashboards — version BI queries.

---

# 6. Dispatch intelligence, tracking & ETA

**Decision IDs:** D-003, D-050, D-051, D-011, D-049.

## Domain entities

- `EngineerLatestLocation`, `EngineerTelemetryEvent`, vehicle locations, dispatch recommendations, ETA state.

## DB tables & relationships

**Code anchor:** `backend/app/modules/tracking/`, `dispatch_intelligence_routes.py`, `dispatch_tracking_routes.py`.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/dispatch` | `GET /engineers/availability`, `GET /jobs/{id}/recommendations`, `POST /jobs/{id}/assign-best`, `GET /jobs/{id}/eta`, tracking |
| `/tracking` | `POST /telemetry/engineer`, vehicle telemetry, geofences |

## Service-layer responsibilities

- `append_engineer_phone_telemetry` — engineer id from JWT; store `occurred_at`.
- Recommendations: return structured empty result + `reason_code` (D-049).
- Freshness: env `PHI_DPS_TELEMETRY_*` — align product thresholds (D-050).

## Validation rules

- Lat/lon range; `occurred_at` not future > clock skew allowance (D-051).

## Background jobs

- Telemetry prune (D-011) — scheduled delete from `engineer_telemetry_events` older than retention.

## Events/webhooks

- None required outbound for MVP.

## Permissions

- Engineer: `POST /tracking/telemetry/engineer` — `require_roles("Engineer")`.

## Audit logging

- Override vehicle/equipment block → existing audit paths.

## Frontend screens

- `LiveDispatchMap.tsx`; dispatch recommendations panel if present.

## Mobile screens

- Continuous GPS → `POST /tracking/telemetry/engineer`.

## Test cases

- Stale telemetry → `stale` flag on map DTO.
- Rate limit telemetry POST (optional) under load.

## Rollout notes

- Retention job first on staging — measure DB size impact.

## Migration risks

- Bulk delete telemetry — run off-peak; archive if compliance requires.

---

# 7. Time & attendance (punch, timesheets)

**Decision IDs:** D-006, D-016, D-052–D-054, D-053.

## Domain entities

- `Punch` (in/out), timesheet aggregates, approval state *(extend when D-052 decided)*.

## DB tables & relationships

**Code anchor:** `backend/app/modules/time_tracking/`.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/time` | `POST /time/punch/in`, `POST /time/punch/out`, timesheets, payroll export |

## Service-layer responsibilities

- Enforce single open punch per user (D-016).
- Reassignment (D-006): if policy = auto clock-out, insert boundary punches with `reason=reassignment`.
- Idempotent punch (D-022, D-054): dedupe by `Idempotency-Key` or natural key window.

## Validation rules

- GPS optional with warning flag in audit (D-053) — **field** `location_source=gps|manual|unknown`.

## Background jobs

- None mandatory.

## Events/webhooks

- Payroll export file generation — document SLA (D-028).

## Permissions

- Engineer: own punch; Admin/Dispatcher: timesheet approve per route.

## Audit logging

- Punch immutable; adjustments as new rows (D-016).

## Frontend screens

- Time / punch sections in `App.tsx`.

## Mobile screens

- Punch in/out in `main.dart`.

## Test cases

- Second punch-in without punch-out → 409.
- Idempotency replay → same response body.

## Rollout notes

- Deploy idempotency table before mobile offline rollout.

## Migration risks

- Backfill open punches on deploy — script to identify anomalies.

---

# 8. Compliance & certificates

**Decision IDs:** D-004, D-055–D-058, D-056, D-046.

## Domain entities

- `Certificate`, template registry, job completion requirements.

## DB tables & relationships

**Code anchor:** `backend/app/modules/compliance/`.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/compliance` | `GET/POST` certificates, generate |

## Service-layer responsibilities

- Generate PDF — **async job** pattern (D-028): return `202` + `job_id` + poll URL when long-running.
- Certificate matrix enforcement (D-004): config table `certificate_requirements(work_type, asset_type, cert_type, validity_months)`.
- Void (D-055): `status=voided`, `supersedes_certificate_id`, reason mandatory.

## Validation rules

- Cannot void without reason; cannot delete issued rows.

## Background jobs

- Certificate generation worker; retry with backoff on transient failure (D-056).

## Events/webhooks

- Optional: notify engineer on failure.

## Permissions

- Issue/void: Admin/Compliance mapping (D-030); engineer submit field data per D-032.

## Audit logging

- All generations, voids, template version used (D-057).

## Frontend screens

- Certificates in `App.tsx`; compliance admin when built.

## Mobile screens

- Future: certificate checklist / photo capture.

## Test cases

- Missing requirement blocks completion (integration with job gate).
- Void creates supersession chain.

## Rollout notes

- Ship matrix config CSV → DB seed for staging.

## Migration risks

- Changing matrix mid-flight — version effective dates on rules table.

---

# 9. Invoicing & finance

**Decision IDs:** D-009, D-017, D-059, D-060, D-041, D-019.

## Domain entities

- `Invoice`, finance review flags; future `CreditNote` (D-017).

## DB tables & relationships

**Code anchor:** `backend/app/modules/invoicing/`.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/invoicing` | `GET /invoicing/invoices`, `POST .../generate`, `POST .../pay`, `POST .../hold`, finance review endpoints |

## Service-layer responsibilities

- **Generate gate (D-009):** require `job.status == completed` (or explicit milestone flag on job) — **not** permission alone.
- Credit note (D-017): export-first entity with `external_ref` optional.
- Customer hold (D-041): block generate if customer `account_status=on_hold`.

## Validation rules

- Line totals; currency; job linkage.

## Background jobs

- Retry failed payment callbacks (D-060) — DLQ table or `invoicing_delivery_failures` pattern.

## Events/webhooks

- Inbound payment confirmation when PSP integrated.

## Permissions

- `can_hold_invoice`, `can_mark_finance_review`, etc. — `authorization_policy.py`.

## Audit logging

- Every state change on invoice; finance review actor.

## Frontend screens

- Invoicing section in `App.tsx`.

## Mobile screens

- None for MVP.

## Test cases

- Generate on incomplete job → 400 when gate enabled.
- Hold blocks pay.

## Rollout notes

- Feature flag `INVOICE_REQUIRE_JOB_COMPLETED=true`.

## Migration risks

- Historical invoices for non-completed jobs — grandfather clause in migration.

---

# 10. Inventory & stock

**Decision IDs:** D-010, D-066–D-068, D-008.

## Domain entities

- Locations (warehouse/van), stock balances, movements, parts usage lines.

## DB tables & relationships

**Code anchor:** `backend/app/modules/inventory/`.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/inventory` | stock, movements, parts usage POST to job |

## Service-layer responsibilities

- Soft reserve at **dispatch-ready** (D-010); consume on parts usage submit; release on cancel if not consumed.
- Strict reconciliation env — block completion (D-067).

## Validation rules

- Non-negative stock when strict; override requires permission.

## Background jobs

- Nightly stock reconciliation report (optional).

## Events/webhooks

- Low stock alert (future).

## Permissions

- `Ops_Manager` / `Admin` / future `Warehouse` (D-031).

## Audit logging

- Every movement; override with reason.

## Frontend screens

- Inventory if present in `App.tsx` or separate route.

## Mobile screens

- Parts usage entry when added to Flutter app.

## Test cases

- Cancel job releases reservation.
- Strict mode blocks completion when lines don’t reconcile.

## Rollout notes

- Migrate: backfill reservations = 0 for legacy jobs.

## Migration risks

- Double-release if cancel retried — idempotent release by job id.

---

# 11. Contracts, SLA, PPM, commercial

**Decision IDs:** D-015, D-061–D-065, D-063, D-064.

## Domain entities

- `Contract`, `ContractVersion`, amendments, activation runs, repricing proposals, customer comms.

## DB tables & relationships

**Code anchor:** `backend/app/modules/contracts/` (large surface).

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/contracts` | CRUD, versions, activation, webhooks consumer |
| `/sla` | SLA endpoints |
| `/ppm` | PPM schedules |

## Service-layer responsibilities

- Publish **single diagram** in `/docs` (D-061); code follows `PHI_DPS_ACCEPTANCE_POLICY_MODE`.
- SLA MVP: wall-clock (D-015) — document in API responses; calendar later.

## Validation rules

- Activation guards per policy mode (D-062); integration tests as spec.

## Background jobs

- Contract renewal scans, repricing follow-ups — recurring jobs.

## Events/webhooks

- E-sign: verify signature per provider (D-064); fixture tests.

## Permissions

- Commercial/Finance split per D-065; `can_decide_contract_review`, etc.

## Audit logging

- Version transitions; e-sign receipt payload hash.

## Frontend screens

- Commercial hub / contracts UI (as routed in app).

## Mobile screens

- None.

## Test cases

- Policy mode matrix: one test per mode × action.

## Rollout notes

- Contract schema migrations — use Postgres migration tool in prod.

## Migration risks

- Long-running contract migrations — blue/green or read-only window.

---

# 12. Portal (customer)

**Decision IDs:** D-043, D-069, D-058.

## Domain entities

- Portal session customer; scoped jobs/assets/sites/contracts.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/portal` | `GET /portal/me/jobs`, tracking, documents |

## Service-layer responsibilities

- `portal_access_service` — `can_customer_access_job`, etc.

## Validation rules

- Never expose internal engineer PII beyond policy.

## Background jobs

- None.

## Events/webhooks

- N/A.

## Permissions

- `Client` role only on portal routes.

## Audit logging

- Portal document downloads.

## Frontend screens

- Separate portal SPA if exists; else section under web.

## Mobile screens

- None (customer app out of scope unless product adds).

## Test cases

- Customer A cannot access Customer B job URL.

## Rollout notes

- Portal base URL env `PHI_DPS_PORTAL_WEB_BASE`.

## Migration risks

- Scope expansion — migrate portal access rules carefully.

---

# 13. Competence & qualifications

**Decision IDs:** D-014.

## Domain entities

- `Qualification` per engineer, competency, expiry.

## DB tables & relationships

**Code anchor:** `backend/app/modules/competence/`.

## API endpoints

| Prefix | `/competence` |

## Service-layer responsibilities

- Called from `assign_job` — block if expired; override path logs `competency_override` audit.

## Validation rules

- Expiry date ≥ today for new qualifications.

## Background jobs

- Expiry warning digest email (optional).

## Events/webhooks

- None.

## Permissions

- Admin/Ops manage qualifications.

## Audit logging

- Overrides mandatory (D-014).

## Frontend screens

- Qualification admin.

## Mobile screens

- Read-only “your qualifications” optional.

## Test cases

- Assign gas job without gas competency → 400.

## Rollout notes

- Seed competencies from CSV.

## Migration risks

- Bulk expiry backfill — communications to ops.

---

# 14. Operations, system, automation, documents

**Decision IDs:** D-029, D-028, D-027.

## Domain entities

- `RecurringSystemJob`, runs, operational diagnostics aggregates.

## API endpoints

| Prefix | Examples |
|--------|----------|
| `/system` | health, jobs, diagnostics, `integration-status` |
| `/ops` | recommendations, automation |
| `/documents` | upload/download metadata |
| `/automation`, `/tasks` | internal tasks |

## Service-layer responsibilities

- Diagnostics aggregation for go-live alerts (D-029).
- Document storage: local/S3 per env; presigned TTL.

## Validation rules

- Upload MIME/size (D-027).

## Background jobs

- `run_due_recurring_jobs.py`; document virus scan hook *(future)*.

## Events/webhooks

- N/A.

## Permissions

- Admin for destructive system routes.

## Audit logging

- System job runs, failures in `recurring_system_job_runs`.

## Frontend screens

- Commercial hub diagnostics panel if wired.

## Mobile screens

- None.

## Test cases

- `GET /system/integration-status` returns 200 with flags.

## Rollout notes

- Cron in k8s with `concurrencyPolicy: Forbid`.

## Migration risks

- Job definition schema changes — version `payload_json`.

---

# 15. Communications & rollout

**Decision IDs:** D-070.

## Domain entities

- Contract customer communications, rollout notifications, deliveries.

## API endpoints

- Comms draft/send under `/contracts` and related; `/rollout/*`.

## Service-layer responsibilities

- Idempotent send with provider id (D-070).

## Validation rules

- Break-glass requires reason + permission `can_break_glass_communication_suppression`.

## Background jobs

- Retry failed deliveries; dead letter queue.

## Events/webhooks

- Inbound provider status.

## Permissions

- Contract comms keys in `authorization_policy.py`.

## Audit logging

- Every send attempt; break-glass rows.

## Frontend screens

- Comms pipeline UI.

## Mobile screens

- None.

## Test cases

- Duplicate provider id ignored.

## Rollout notes

- Staging provider sandbox first.

## Migration risks

- Template version change — pin version in send record.

---

# 16. Mobile app (Flutter)

**Decision IDs:** D-012, D-071, D-022.

## Domain entities

- Local queue SQLite *(when implemented)*: `outbox(id, payload, idempotency_key, created_at, status)`.

## DB tables & relationships

- N/A server-side except idempotency store.

## API endpoints

- Same REST as web where role allows; prefer `10.0.2.2` Android emulator.

## Service-layer responsibilities

- Client: exponential backoff; replay queue; show sync status (OPS TODO).

## Validation rules

- Queue max size / age (D-012) — enforce client-side + server reject stale timestamps if policy added.

## Background jobs

- None on device except timer for sync.

## Events/webhooks

- N/A.

## Permissions

- Engineer role only for engineer APK.

## Audit logging

- Server logs mobile user agent + idempotency.

## Frontend screens

- N/A.

## Mobile screens

- Login, engineer home, jobs, punch, telemetry status — `mobile/lib/main.dart`.

## Test cases

- Integration test against mock API; offline queue unit tests.

## Rollout notes

- App signing, Play Store tracks; MDM optional.

## Migration risks

- API version negotiation — add `X-Api-Client-Version` header for support.

---

# 17. Cross-reference: priority decisions → implementation epics

| ID | Epic summary |
|----|----------------|
| D-001 | Job status enum + migration + OpenAPI enum |
| D-002 | Quote revision model + constraints |
| D-003 | `dispatch_ready` service + assign gate |
| D-004 | Certificate matrix table + completion integration |
| D-005 | Pydantic parity tests per domain |
| D-006 | Reassignment + punch policy in one PR |
| D-009 | Invoice generate guard middleware |
| D-010 | Reservation columns / inventory service |
| D-011/D-025 | Purge jobs + legal signoff |
| D-012 | Mobile outbox + API idempotency |
| D-013 | Published RBAC matrix PDF + role seed |
| D-022 | Idempotency middleware |

---

# Document control

| Field | Value |
|-------|--------|
| **Version** | 1.0 |
| **Source decisions** | `PHI_DPS_PRODUCT_DECISIONS_REGISTER.md` (recommended options) |
| **Codebase root** | `backend/app/`, `web/`, `mobile/` |
| **Owner** | Principal Engineer + Product Owner (joint) |

---

*Update this blueprint when a decision moves from recommended default to a different approved outcome (reference ADR ID in section header).*
