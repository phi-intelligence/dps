# PHI-DPS — Engineer mobile app end-to-end plan

**Scope:** Flutter engineer field app only (`mobile/`).  
**Source truth:** `PHI_DPS_CURRENT_IMPLEMENTED_LOGIC_AUDIT.md` (code behavior), existing FastAPI routers under `backend/app/`.  
**Benchmark lens:** Mature field-service platforms (ServiceTitan, Simpro, Jobber, BigChange, Salesforce Field Service, Oracle Field Service) set expectations for **offline-capable job execution**, **structured closeout** (forms, media, signatures, parts), **clear job lifecycle**, and **operational reliability** — this plan maps those expectations onto **what PHI-DPS already exposes** vs what must be **added or tightened on the backend**.

---

## 1. Benchmark expectations (engineer mobile only)

| Capability area | Mature apps (typical) | PHI-DPS today (`mobile/lib/main.dart`) |
|-----------------|----------------------|----------------------------------------|
| **Today’s work** | Prioritized schedule, map, filters | Assigned jobs list + manual job id only |
| **Job pack** | Address, contacts, assets, SLA, notes, hazards | Not surfaced |
| **Lifecycle** | En route → on site → in progress → complete | Partially implied by punch + job status strings; **no** guided flow |
| **Time** | Clock to job, breaks, corrections with audit | Punch in/out only; **geofence required** on server (`time_tracking/service.py`) |
| **Compliance** | Checklists, certs, readings, sign-offs | **Backend** has completion requirements + certificates; **mobile** not integrated |
| **Parts** | Issue/consume, van stock, shortages | **Backend** `inventory/`, job parts usage; **mobile** none |
| **Media** | Photos/videos with job linkage | **Backend** job media requirements; **mobile** none |
| **Offline** | Queue, retry, idempotency | **None** (audit) |
| **Vehicle / H&S** | Pre-use checks, defects | **`POST /vehicles/{id}/inspections`** for assigned van; **mobile** none |
| **Commercial closeout** | Capture PO, payment ref, upsell | Invoicing is **staff/finance** in product; engineer app usually **read-only** or **capture-only** — align with `invoicing` reality (no in-app credit notes per audit) |

**Implication:** PHI-DPS backend is **broader than the current Flutter shell**. The plan prioritizes **wiring engineer-safe endpoints** already present before inventing new domains.

---

## 2. Target feature set (engineer app)

### MVP — engineers operational (safe + auditable)

| Feature | Purpose |
|---------|---------|
| **Secure session** | Token storage (flutter_secure_storage), expiry handling, re-login |
| **Today / jobs** | `GET /jobs` with filters (`status`, date) when backend supports; job detail from `GET /jobs/{id}` |
| **Job lifecycle strip** | En route → on site → work complete (statuses aligned with server + `dispatch_tracking` where Engineer role allows) |
| **Punch** | In/out with **geofence awareness** (surface error if no geofence); optional **offline queue** + idempotency |
| **Telemetry** | Throttled GPS (existing); battery-aware mode |
| **Completion gate visibility** | `GET` completion-requirements bundle for job — show **blocked** forms/media/parts |
| **Forms (minimum)** | Submit required job forms per existing dispatch APIs |
| **Photos (minimum)** | Attach to job media requirements via `documents` + dispatch media endpoints |
| **Errors** | Structured handling of 400/401/403/422/503; no raw stack traces to users |

### Phase 2 — M&E compliance depth

| Feature | Purpose |
|---------|---------|
| **Signatures** | Customer/engineer sign-off per `JobSignatureRequirement` |
| **Parts usage** | Lines against job + inventory strict path awareness |
| **Certificates** | List/generate/view **where Engineer role is allowed** (`compliance` routes) |
| **Vehicle pre-use** | Daily inspection for `assigned_vehicle_id` |
| **Equipment readiness** | Read-only equipment/calibration context for job |
| **“On my way” / ETA** | `POST /dispatch/jobs/{id}/customer-notify/on-my-way` if product enables |

### Phase 3 — hardening + scale

| Feature | Purpose |
|---------|---------|
| **Full offline** | Large outbox, conflict policy, background sync |
| **Biometric / MDM** | Org policy hooks |
| **Observability** | `X-Client-Version` header, crash reporting |
| **Load testing** | Telemetry + sync at scale |
| **Payment capture** | **Only if** product adds engineer-safe endpoint; today finance is **not** engineer-primary per RBAC audit |

---

## 3. User journeys

### J1 — Start shift (MVP+)

1. Login → home.  
2. **Optional (Phase 2):** Complete vehicle pre-use for `assigned_vehicle_id` → `POST /vehicles/{vehicle_id}/inspections`.  
3. View **today’s jobs** → select job.  
4. **En route** (if product adds status or uses existing tracking endpoints) → telemetry continues.

### J2 — Arrive and punch in

1. Open job detail → **geofence** must exist (server requirement).  
2. Punch in → server sets job `on_site` (`time_tracking/service.py`).  
3. If punch fails (no geofence, wrong assignee) → **clear error** + dispatcher escalation path (copy).

### J3 — Execute work (Phase 1–2)

1. View **completion requirements** (forms, media, parts, signatures).  
2. Complete each; app polls or refreshes until **no** `completion_blocked_*`.  
3. Punch out → server sets `completion_pending_forms` and runs `try_finalize_job_completion_if_possible` (`dispatch/service.py`).

### J4 — Offline / flaky network (MVP partial, Phase 3 full)

1. Queue punch/telemetry with **Idempotency-Key** (requires **backend** support — see §8).  
2. Replay when online; show sync state.

---

## 4. App architecture (Flutter)

```
┌─────────────────────────────────────────────────────────────┐
│  App shell (Material 3) + deep link / notification (later)   │
├─────────────────────────────────────────────────────────────┤
│  Auth + session (token, refresh policy)                     │
├─────────────────────────────────────────────────────────────┤
│  API client (dio/http) + interceptors (auth, idempotency)     │
├─────────────────────────────────────────────────────────────┤
│  Feature modules: Jobs | Time | Tracking | Completion |     │
│  Vehicles | Compliance | Inventory (Phase 2)                 │
├─────────────────────────────────────────────────────────────┤
│  Offline (Phase 1 minimal → Phase 3): Drift/SQLite outbox    │
├─────────────────────────────────────────────────────────────┤
│  State: Riverpod / Bloc (pick one per team standard)         │
└─────────────────────────────────────────────────────────────┘
```

**Principles:**  
- **Single API client** with base URL from `PHI_DPS_API_BASE` (existing pattern).  
- **Feature modules** map to router prefixes: `/jobs`, `/time`, `/tracking`, `/dispatch`, `/vehicles`, `/compliance`, `/inventory`, `/documents`.  
- **No business logic** duplicated that contradicts `PHI_DPS_CURRENT_IMPLEMENTED_LOGIC_AUDIT.md` — if backend doesn’t enforce quote acceptance on job create, **mobile does not** create jobs (engineer typically doesn’t).

---

## 5. Module breakdown

| Module | Responsibility | Primary APIs |
|--------|----------------|--------------|
| **auth** | Login, token storage, logout | `POST /auth/token`, `GET /auth/me` |
| **jobs** | List, detail, accept job | `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/accept` |
| **time** | Punch, optional timesheet | `POST /time/punch/in`, `POST /time/punch/out`, timesheet GETs |
| **tracking** | Telemetry | `POST /tracking/telemetry/engineer` |
| **dispatch** | ETA, on-my-way, tracking RO | `/dispatch/...` (role-gated) |
| **completion** | Forms, media, signatures, parts | `/jobs/.../forms`, `.../media`, `.../signature`, `.../parts-usage`, completion bundle |
| **vehicles** | Pre-use inspection | `POST /vehicles/{id}/inspections` (own van only) |
| **compliance** | Certificates | `/compliance/...` (verify Engineer on each route) |
| **inventory** | Parts lines | `/inventory/...` (Phase 2) |
| **documents** | Uploads | `/documents/...` |
| **sync** | Outbox, retry | Local DB + worker |

---

## 6. Screen-by-screen plan

| Screen | MVP | Phase 2 | Notes |
|--------|-----|---------|-------|
| Login | ✓ | | Email/password; show API base in debug |
| Home / Today | ✓ | | List assigned jobs; pull-to-refresh |
| Job detail | ✓ | ✓ | Address, status, customer contact **if API returns**; link to maps |
| **Geofence warning** | ✓ | | If `GET` geofence 404 → explain punch unavailable |
| Punch panel | ✓ | | In/out; show last punch state |
| Telemetry status | ✓ | | Existing + sync indicator when offline added |
| **Completion checklist** | ✓ | | From completion-requirements bundle |
| Form submit | ✓ | | Per job form keys |
| Photo capture | ✓ | | Media requirements |
| Signature | | ✓ | |
| Parts usage | | ✓ | |
| Certificate | | ✓ | |
| Vehicle inspection | | ✓ | |
| Settings | ✓ | ✓ | API base override (dev), about, logout |

---

## 7. API integration plan

### Already used (keep)

- `POST /auth/token`  
- `GET /jobs` (engineer-scoped)  
- `POST /tracking/telemetry/engineer`  
- `POST /time/punch/in`, `POST /time/punch/out`  
- `parseAccessTokenFromAuthJson` (`mobile/lib/auth_token.dart`)

### MVP — add

| Endpoint | Use |
|----------|-----|
| `GET /jobs/{job_id}` | Full job detail |
| `GET /jobs/{job_id}/completion-requirements` | Bundle (forms/media/parts) — `dispatch/routes.py` router prefix `/jobs` |
| `GET /dispatch/jobs/{job_id}/tracking` | Read-only operational state (see `dispatch_tracking_routes.py`) |
| Job geofence | **Verify** OpenAPI / `time_tracking` for the geofence read used before punch (server requires geofence for punch) |
| `POST /jobs/{job_id}/accept` | Engineer accept workflow |

### Phase 2 — add

- Form submit, media upload, signature submit, parts usage POSTs under `/jobs/{id}/...`  
- `POST /vehicles/{vehicle_id}/inspections`  
- `GET /compliance/certificates` filtered by `job_id`  
- `POST /compliance/certificates/generate` **if** Engineer allowed on route

### Backend prerequisites (product/engineering)

| Gap (from audit) | Action for mobile program |
|------------------|---------------------------|
| Punch duplicate `in` | **Backend** should reject duplicate open punch — mobile benefits |
| Punch `offline_device_id` | Mobile sets when **offline queue** sends |
| **Idempotency** | **New** middleware or header contract for punch/telemetry |
| **Geofence** | Jobs without geofence **cannot** punch — product must ensure geofence or **change** backend |

---

## 8. Offline / sync architecture

### Target pattern (aligned with mature apps)

1. **Outbox table** (SQLite): `id`, `method`, `path`, `body_hash`, `idempotency_key`, `created_at`, `status`, `retry_count`, `last_error`.  
2. **Worker** (connectivity + periodic): process queue FIFO; **exponential backoff**; **max age** (product config).  
3. **Idempotency-Key** header (UUID per logical operation) — **requires backend** to store and dedupe (see audit: **missing** today).  
4. **Conflict** — server wins on read; for punch, **replay** returns same id if server implements idempotency.

### MVP compromise

- **Queue only** punch + telemetry (highest risk).  
- **Read-only** when offline (show cached jobs).  
- **No** full conflict resolution.

### Phase 3

- Full queue for forms/media multipart (harder — chunking or deferred upload URLs).

---

## 9. Error handling approach

| Layer | Behavior |
|-------|----------|
| **HTTP** | Map `401` → login; `403` → “no permission” + support ref; `422` → field errors; `503` → retry banner |
| **Domain** | Parse `detail` string/list from FastAPI consistently |
| **Geofence / punch** | `ValueError` messages from server → user-facing copy (“Geofence required — contact dispatch”) |
| **Logging** | Crash reporting (Sentry/Firebase) in prod; **no PII** in logs |

---

## 10. Permissions / capability model

**Current:** `Engineer` role has **no** fine-grained permission keys (`authorization_policy.py`); access is **`require_roles("Engineer")` per route**.

**Mobile must:**

- Assume **only** endpoints that **allow Engineer** are callable.  
- **Hide** features (certificates, inventory) if `GET` returns 403 — **or** backend adds **read** capability flags to `GET /auth/me` (recommended follow-up).

**Do not** duplicate RBAC in Flutter — **trust 403** + product matrix.

---

## 11. Testing strategy

| Layer | Tooling |
|-------|---------|
| **Unit** | `auth_token`, mappers, outbox logic |
| **Widget** | Login, job list, error states |
| **Integration** | `integration_test` against **staging API** or docker-compose |
| **Contract** | Golden files for JSON samples from `/jobs`, completion bundle |
| **Manual** | Android emulator `10.0.2.2`, physical device LAN, airplane mode |

**Acceptance:** CI runs `flutter test`; integration test **nightly** on staging.

---

## 12. Release plan

| Track | Content |
|-------|---------|
| **Internal alpha** | MVP + internal dogfood |
| **Pilot** | 5–20 engineers, real jobs, support playbook |
| **GA** | Phase 2 + monitoring + rollback plan |

**Distribution:** Play Store / TestFlight; **MDM** optional Phase 3.

---

## 13. Feature specifications (per feature)

### F1 — Login & session

| Field | Value |
|-------|--------|
| **Purpose** | Secure access to engineer APIs |
| **Backend** | `POST /auth/token`; JWT in `Authorization` |
| **Mobile** | `auth_token.dart` + secure storage |
| **Edge cases** | Token expiry mid-shift → refresh policy or re-login |
| **Acceptance** | Successful login; `GET /auth/me` returns engineer id |

### F2 — Job list & detail

| Field | Value |
|-------|--------|
| **Purpose** | Replace free-text job id with structured work |
| **Backend** | `GET /jobs`, `GET /jobs/{id}` |
| **Mobile** | `JobRepository`, models for `JobOut` |
| **Edge cases** | Empty list = “no assignments” not network error |
| **Acceptance** | Detail shows address, status, quote id if present |

### F3 — Telemetry (existing)

| Field | Value |
|-------|--------|
| **Purpose** | Dispatch map / freshness |
| **Backend** | `POST /tracking/telemetry/engineer` |
| **Edge cases** | Clock skew; `occurred_at` UTC |
| **Acceptance** | Throttle respected; status line |

### F4 — Punch in/out

| Field | Value |
|-------|--------|
| **Purpose** | Time on job + drive `on_site` / completion pipeline |
| **Backend** | `time_tracking/service.py` geofence + assignee |
| **Mobile** | Pre-flight geofence check; **offline queue** MVP |
| **Edge cases** | No geofence; duplicate punch-in; punch out without in |
| **Acceptance** | Successful punch updates job status in UI after refresh |

### F5 — Completion (forms / media / parts / signatures)

| Field | Value |
|-------|--------|
| **Purpose** | Satisfy `try_finalize_job_completion_if_possible` gates |
| **Backend** | Job requirement tables + POST submit routes under dispatch |
| **Mobile** | Checklist UI; multipart uploads |
| **Edge cases** | Partial completion; strict inventory |
| **Acceptance** | Job reaches `completed` when server rules satisfied |

### F6 — Vehicle inspection (Phase 2)

| Field | Value |
|-------|--------|
| **Purpose** | H&S pre-use; readiness signals |
| **Backend** | `vehicles/routes.py` — `_ensure_vehicle_access` own van |
| **Mobile** | Inspection wizard |
| **Edge cases** | No `assigned_vehicle_id` |
| **Acceptance** | Successful POST returns inspection |

---

## 14. Sprint-by-sprint delivery plan

**Assumption:** ~2-week sprints; adjust to team velocity.

| Sprint | Goal | Deliverables |
|--------|------|--------------|
| **S1** | Foundation | Navigation shell, secure token, DI, `ApiClient` refactor, `GET /jobs/{id}`, error handling |
| **S2** | Job UX | Today screen, job detail, pull-to-refresh, maps deep link, **geofence fetch** + punch pre-checks |
| **S3** | Completion visibility | `GET` completion-requirements bundle UI, blocked states |
| **S4** | Forms v1 | First form submit path + validation |
| **S5** | Media v1 | Photo upload for one media requirement |
| **S6** | Offline MVP | Outbox for punch + telemetry; **backend idempotency** spike (parallel backend sprint) |
| **S7** | Phase 2 start | Signatures OR parts (pick by priority) |
| **S8** | Vehicle inspection | Full inspection POST for assigned van |
| **S9** | Certificates read/generate | Per route permission |
| **S10** | Hardening | Integration tests, crash reporting, pilot fixes |

**Parallel backend work:** idempotency keys, duplicate punch rejection, optional `GET /auth/me` capability flags.

---

## 15. MVP vs Phase 2 vs Phase 3 (summary)

| Tier | Includes |
|------|----------|
| **MVP** | Login, jobs, detail, geofence-aware punch, telemetry, completion checklist, **one** form + **one** media path, structured errors, **minimal** offline queue for punch/telemetry (once backend ready) |
| **Phase 2** | Signatures, parts, certificates, vehicle inspection, on-my-way |
| **Phase 3** | Full offline sync, biometrics, MDM, observability, scale testing |

---

## 16. References

- `PHI_DPS_CURRENT_IMPLEMENTED_LOGIC_AUDIT.md` — code truth  
- `PHI_DPS_IMPLEMENTATION_BLUEPRINT.md` — cross-module blueprint  
- `mobile/README.md` — Android emulator / iOS notes  
- `backend/app/services/authorization_policy.py` — engineer permissions  

---

## 17. Document control

| Field | Value |
|-------|--------|
| **Version** | 1.0 |
| **Owner** | Product + Mobile lead |
| **Next review** | After MVP sprint 3 |

---

*This plan is specific to PHI-DPS; update when backend routes or RBAC change.*
