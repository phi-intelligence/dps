# PHI-DPS Engineer Mobile — Implementation Build Spec

**Audience:** Cursor / developers executing the Flutter refactor and feature build.  
**Source truth:** `PHI_DPS_CURRENT_IMPLEMENTED_LOGIC_AUDIT.md`, `mobile/lib/main.dart`, `mobile/lib/auth_token.dart`, FastAPI modules under `backend/app/modules/`.  
**Non-goals:** Redesigning dispatch/finance domains; adding new product surfaces unless **blocking** mobile production behavior (listed in §7).

---

## 1. Build goal

### 1.1 Target

Deliver a **production-oriented** PHI-DPS **Engineer** Flutter app that:

- Uses **only** endpoints the **Engineer** role can call today (unless §7 extends the backend).
- Implements **structured navigation**, **repositories**, **typed errors**, **local cache + outbox** for punch/telemetry (then expand).
- Surfaces **job completion gates** (`JobCompletionRequirementsBundleOut`) and engineer submit paths for forms, media, signatures, parts usage.
- Aligns UX with **actual** server rules: **geofence required for punch**, **string job statuses**, **completion** via `try_finalize_job_completion_if_possible` after submissions.

### 1.2 What already exists (do not throw away — refactor)

| Asset | Location | Behavior |
|-------|----------|----------|
| API base resolution | `main.dart` → `apiBase` | `PHI_DPS_API_BASE` dart-define; Android default `10.0.2.2:8000` |
| Token parse | `auth_token.dart` | `parseAccessTokenFromAuthJson` — **keep** as library API |
| Login | `POST /auth/token` | form-urlencoded username/password |
| Jobs list | `GET /jobs?limit=50&offset=0` | Engineer: assigned only |
| Punch | `POST /time/punch/in`, `POST /time/punch/out` | JSON body `job_id`, `latitude`, `longitude` |
| Telemetry | `POST /tracking/telemetry/engineer` | JSON per `EngineerPhoneTelemetryIn` |
| GPS | `geolocator` | Stream + throttle; **preserve** behavior for telemetry |

### 1.3 What must be built

- **App layering:** `core/` (HTTP, auth, errors, config, drift), `features/*` (jobs, time, tracking, completion, …), `app/` (router, theme).
- **Replace monolithic `main.dart` screens** with routed feature screens and shared widgets.
- **Repositories** for each API surface; **DTOs** matching Pydantic response models (subset in Dart).
- **Drift** SQLite: `jobs` cache, `outbox` for queued writes, `sync_state` metadata.
- **Unified error model** mapping FastAPI `detail` (string or JSON object) to UI actions.

### 1.4 What must be hardened

- **No silent failures** on punch/telemetry — show structured errors; queue when offline (after Wave 4).
- **Idempotency** for replayed punch/telemetry **after** backend supports it (§7).
- **Misnamed `ApiClient.vehicleId`** in current code: JWT `sub` is **user id**, not `assigned_vehicle_id` — **rename** to `tokenSubjectUserId` or remove; use `GET /auth/me` + §7 field for vehicle.

---

## 2. Technical architecture for the Flutter app

### 2.1 Decisions (locked for this spec)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State | **flutter_riverpod** (3.x) | Testable, explicit providers, fits feature modules |
| Navigation | **go_router** | Typed routes, deep links later |
| HTTP | **dio** | Interceptors, timeouts, cancel tokens |
| Local DB | **drift** + Drift codegen | Typed SQL, migrations |
| Secure storage | **flutter_secure_storage** | Access/refresh tokens |
| JSON | **json_serializable** + `build_runner` | DTOs match backend |

### 2.2 Folder structure (create)

```
mobile/
  lib/
    app/
      app.dart                 # MaterialApp.router
      router.dart              # GoRouter configuration
      theme.dart
    core/
      config/
        app_config.dart        # PHI_DPS_API_BASE, env, feature flags
      network/
        dio_client.dart        # Dio + base options
        auth_interceptor.dart  # Bearer injection
        logging_interceptor.dart
        api_error_interceptor.dart
        idempotency_interceptor.dart  # Idempotency-Key when backend ready
      errors/
        api_exception.dart     # Typed API failure
        error_mapper.dart      # DioException → ApiException
      auth/
        session_controller.dart
        token_storage.dart     # flutter_secure_storage wrapper
        jwt_util.dart          # move sub decode from main.dart
      persistence/
        app_database.dart      # Drift database class
        tables/
          jobs_cache.dart
          outbox_ops.dart
          sync_metadata.dart
        daos/
          jobs_cache_dao.dart
          outbox_dao.dart
      sync/
        sync_worker.dart
        sync_state_notifier.dart
      logging/
        app_logger.dart
    features/
      auth/
        data/auth_repository.dart
        presentation/login_screen.dart
      jobs/
        data/jobs_repository.dart
        data/models/job_dto.dart
        presentation/job_list_screen.dart
        presentation/job_detail_screen.dart
        presentation/widgets/job_status_chip.dart
      time_punch/
        data/time_repository.dart
        data/models/punch_dto.dart
        presentation/punch_screen.dart
      tracking/
        data/tracking_repository.dart
        data/engineer_telemetry_service.dart  # stream + throttle (from main.dart)
      completion/
        data/completion_repository.dart
        presentation/completion_checklist_screen.dart
      forms/
        data/forms_repository.dart
        presentation/job_form_screen.dart
      media/
        data/media_repository.dart
        presentation/job_media_screen.dart
      signatures/
        data/signatures_repository.dart
        presentation/job_signature_screen.dart
      inventory_parts/
        data/parts_repository.dart
        presentation/job_parts_screen.dart
      vehicles/
        data/vehicles_repository.dart
        presentation/vehicle_inspection_screen.dart
      compliance/
        data/compliance_repository.dart   # stub until §7 backend
      notifications/
        local_notifications_service.dart  # optional; no backend push today
      settings/
        presentation/settings_screen.dart
    main.dart                  # thin: bootstrap ProviderScope + runApp
  test/
  integration_test/
```

### 2.3 Feature-module structure

Each feature under `features/<name>/`:

- **`data/`** — repository calling `Dio` via `dio_client.dart`; maps JSON → DTO; **no** `BuildContext`.
- **`presentation/`** — widgets/screens; **only** call `Ref`/`Provider` or callbacks.

### 2.4 Core shared infrastructure

- **`core/network/dio_client.dart`**: single `Provider<Dio>` with baseUrl from `AppConfig`.
- **`core/errors`**: all API failures become `ApiException` with `statusCode`, `message`, `rawDetail` (dynamic).
- **`core/persistence`**: Drift owns cache + outbox; **never** store raw passwords.

### 2.5 State management

- **Global:** `SessionController` (Notifier) — `AuthState` (`unauthenticated` | `authenticated` | `loading`).
- **Feature:** `AsyncNotifier` / `FutureProvider` for job list, job detail, completion bundle.
- **Sync:** `SyncStateNotifier` — `idle` | `syncing` | `error` + pending count.

### 2.6 API client pattern

- **One** `Dio` instance; repositories take `Dio` and path constants.
- **No** duplicate `ApiClient` class in `main.dart` — delete after migration.

### 2.7 Repository / service pattern

- **Repository** = one backend aggregate (e.g. `JobsRepository`: `listJobs`, `getJob`, `acceptJob`, `getCompletionRequirements`).
- **Service** = long-running or streams (e.g. `EngineerTelemetryService` wraps `Geolocator` + throttle + calls `TrackingRepository`).

### 2.8 Local persistence

- **Drift** tables: see §6.
- **Secure storage:** access token (and refresh if later added).

### 2.9 Sync engine placement

- **`core/sync/sync_worker.dart`**: invoked on app resume, connectivity regain, periodic timer; reads `outbox_ops`; **does not** run inside build().

### 2.10 Error handling pattern

- Interceptors convert Dio errors → `ApiException`.
- UI: `ref.watch(provider).when(error: (e, _) => _ErrorView(apiException: e))` pattern.

### 2.11 Auth / session pattern

- On login success: persist token → `SessionController` authenticated → `go_router` redirect to `/jobs`.
- On **401** from API: clear token → redirect to `/login`.
- **Optional:** `GET /auth/me` after login to hydrate user id (email) — **required** once vehicle id needed from API (§7).

---

## 3. Core app infrastructure to build first

### 3.1 Network client wrapper

| Item | Detail |
|------|--------|
| **Files** | `lib/core/network/dio_client.dart`, `lib/core/config/app_config.dart` |
| **Purpose** | Single Dio with `baseUrl`, connect/send timeouts (e.g. 30s), `validateStatus: (s) => s < 500` optional — **prefer** treating 4xx as errors with body parse |
| **Dependencies** | `dio`, `flutter_riverpod` |
| **Acceptance** | All repositories inject same `Dio`; unit test with mock adapter |

### 3.2 Auth token storage

| Item | Detail |
|------|--------|
| **Files** | `lib/core/auth/token_storage.dart`, `lib/core/auth/session_controller.dart` |
| **Purpose** | Read/write `access_token` to secure storage; expose `Future<String?> getToken()` |
| **Dependencies** | `flutter_secure_storage` |
| **Acceptance** | Cold start restores session if token present; logout clears storage |

### 3.3 Request interceptor (auth)

| Item | Detail |
|------|--------|
| **Files** | `lib/core/network/auth_interceptor.dart` |
| **Purpose** | `Authorization: Bearer <token>` on every request except `/auth/token` |
| **Dependencies** | `dio`, `token_storage` |
| **Acceptance** | Mocked `Dio` shows header on secured routes |

### 3.4 Unified API error model

| Item | Detail |
|------|--------|
| **Files** | `lib/core/errors/api_exception.dart`, `lib/core/errors/error_mapper.dart` |
| **Purpose** | Parse FastAPI body: `detail` string OR `detail: { "missing_required_keys": [...] }` OR list |
| **Dependencies** | `dio` |
| **Acceptance** | Golden tests for each `detail` shape from `dispatch`/`time_tracking` |

### 3.5 App config / env

| Item | Detail |
|------|--------|
| **Files** | `lib/core/config/app_config.dart` |
| **Purpose** | `String get apiBase` — **preserve** existing dart-define rules from `main.dart` |
| **Dependencies** | `flutter/foundation.dart` |
| **Acceptance** | `flutter test` passes with `--dart-define=PHI_DPS_API_BASE=http://127.0.0.1:9` |

### 3.6 Logger / diagnostics

| Item | Detail |
|------|--------|
| **Files** | `lib/core/logging/app_logger.dart` |
| **Purpose** | `debugPrint` wrapper; **no** JWT in logs; optional `X-Client-Version` header via `package_info_plus` |
| **Dependencies** | `package_info_plus` |
| **Acceptance** | Dio interceptor adds `X-Client-Version: <app_version>` |

### 3.7 Local database (Drift)

| Item | Detail |
|------|--------|
| **Files** | `lib/core/persistence/app_database.dart`, `tables/*.dart` |
| **Schema (v1)** | See §6.1 |
| **Dependencies** | `drift`, `drift_flutter`, `sqlite3_flutter_libs`, `path_provider` |
| **Acceptance** | `flutter pub run build_runner build` succeeds; migration from empty DB |

### 3.8 Queued operation model

| Item | Detail |
|------|--------|
| **Files** | `lib/core/persistence/tables/outbox_ops.dart`, `lib/core/sync/queue_models.dart` |
| **Purpose** | Typed `operation_type` enum: `punchIn`, `punchOut`, `telemetry` (later: `formSubmit` only if idempotent) |
| **Acceptance** | Insert row → worker processes → status `completed` or `failed` |

### 3.9 Idempotency key generation

| Item | Detail |
|------|--------|
| **Files** | `lib/core/sync/idempotency.dart` |
| **Purpose** | `Uuid v4` per logical operation; store in outbox row; send as `Idempotency-Key` header **when backend implements** |
| **Dependencies** | `uuid` |
| **Acceptance** | Same outbox row replay sends same key |

### 3.10 Sync status tracking

| Item | Detail |
|------|--------|
| **Files** | `lib/core/persistence/tables/sync_metadata.dart`, `lib/core/sync/sync_state_notifier.dart` |
| **Purpose** | `last_successful_sync_at`, `pending_outbox_count` |
| **Acceptance** | Settings screen shows pending count + last sync time |

---

## 4. Feature modules

### 4.1 Jobs

| Field | Specification |
|-------|----------------|
| **Purpose** | List assigned jobs; open detail; accept job; show raw `status` and SLA fields available to Engineer. |
| **Backend endpoints** | `GET /jobs` (query `limit`, `offset`); `GET /jobs/{job_id}`; `POST /jobs/{job_id}/accept` body `JobEngineerAcceptIn` (`required_competencies` optional list); `GET /jobs/{job_id}/completion-requirements`; `GET /jobs/{job_id}/sla`; `GET /jobs/{job_id}/equipment-readiness` |
| **NOT available to Engineer** | `POST /jobs/{job_id}/status` (Dispatcher/Admin only) — **do not** call. |
| **DTOs** | `JobDto` from `JobOut` fields in `dispatch/schemas.py` (at minimum: `id`, `address`, `status`, `scheduled_at`, `assigned_engineer_id`, `quote_id`, `customer_id`, `site_latitude`, `site_longitude`, `sla_*`, `material_policy`). |
| **Repositories** | `JobsRepository` |
| **Screens** | `JobListScreen`, `JobDetailScreen` |
| **Local storage** | Cache `JobDto` rows in `jobs_cache` table; refresh on pull-to-refresh |
| **Edge cases** | Empty list = true empty state, not error; `403` on another engineer’s job — should not occur if list is assigned-only |
| **Acceptance** | List matches `GET /jobs`; detail matches `GET /jobs/{id}`; Accept calls `POST .../accept` and updates status to `accepted` per server response |
| **Dependencies** | `core/network`, `auth`, `completion` (for navigation to checklist) |

---

### 4.2 Time & Punch

| Field | Specification |
|-------|----------------|
| **Purpose** | Punch in/out with GPS; optional timesheet view. |
| **Backend endpoints** | `POST /time/punch/in`, `POST /time/punch/out` body `PunchInOutIn`: `job_id`, `latitude`, `longitude`, optional `occurred_at`, `offline_device_id`; `GET /time/timesheets?date=YYYY-MM-DD` |
| **Pre-flight** | `GET /tracking/geofences/{job_id}` — Engineer allowed — **if 404 or error**, show “Geofence not configured — punch may fail” and still allow attempt (server enforces). |
| **DTOs** | `PunchDto` from `PunchOut` schema |
| **Repositories** | `TimeRepository`, `GeofenceRepository` (thin `GET /tracking/geofences/{job_id}`) |
| **Screens** | `PunchScreen` (or embedded in `JobDetailScreen`) |
| **Local storage** | Outbox rows for punch when offline |
| **Edge cases** | Audit: **duplicate punch-in possible** — until §7 fix, UI shows warning if last punch in DB is `in` without `out` (requires **GET** punch history — **not** on current API; **workaround:** show last success message only, or add backend `GET /time/punches` — **§7**) |
| **Acceptance** | Successful punch parses `PunchOut`; 400 shows `detail` string |
| **Dependencies** | `geolocator`, `jobs`, `sync` |

---

### 4.3 Tracking

| Field | Specification |
|-------|----------------|
| **Purpose** | Throttled `POST /tracking/telemetry/engineer` with `EngineerPhoneTelemetryIn` fields: `latitude`, `longitude`, `occurred_at`, `accuracy`, `heading`, `speed`, `battery`. |
| **Backend** | Same endpoint; no Engineer `GET` for own telemetry history in audited routes. |
| **Repositories** | `TrackingRepository` |
| **Services** | `EngineerTelemetryService` — move logic from `main.dart` (`_minSendInterval`, `_minMoveMeters`) |
| **Local storage** | Outbox for telemetry events when offline |
| **Edge cases** | Failures must not crash app; queue for retry |
| **Acceptance** | Matches current throttle behavior + optional `battery` from `Battery` plugin (add dependency if desired) |
| **Dependencies** | `dio`, `sync` |

---

### 4.4 Job workflow actions

| Field | Specification |
|-------|----------------|
| **Purpose** | Engineer actions that **exist** on backend: **Accept** (§4.1), **Follow-on from defects** `POST /jobs/{job_id}/follow-on/from-defects` body `FollowOnFromDefectsIn` (`defects: list[str]`). |
| **NOT in scope** | Arbitrary job status updates — **Dispatcher only**. |
| **Screens** | Accept button on `JobDetailScreen`; optional follow-on dialog |
| **Acceptance** | Follow-on returns `created_job_ids`; handle 400 `detail` |

---

### 4.5 Forms & Checklists

| Field | Specification |
|-------|----------------|
| **Purpose** | Submit `POST /jobs/{job_id}/forms/{form_key}/submit` body `JobFormSubmitIn` (`data: map`). Requirements come from completion bundle `form_requirements` with `required_keys_json`. |
| **Backend** | Dispatcher sets requirements via `POST /jobs/{job_id}/forms/{form_key}/requirements` — **Admin/Dispatcher** — mobile **only submits**. |
| **UI** | Dynamic form: parse `required_keys_json` as JSON array of strings; require those keys in `data` |
| **Repositories** | `FormsRepository` |
| **Screens** | `JobFormScreen` (per `form_key`) |
| **Edge cases** | 400 with `detail.missing_required_keys` — show list |
| **Acceptance** | Successful submit returns `JobFormSubmissionOut`; refresh completion bundle |

---

### 4.6 Media capture & upload

| Field | Specification |
|-------|----------------|
| **Purpose** | `POST /jobs/{job_id}/media` body `JobMediaSubmitIn`: `media_type` (default `photo`), `payloads: list<map>` — **not multipart file upload** in current API; payloads are **JSON dictionaries** (e.g. base64 or metadata). **Confirm** with backend team expected shape; until then, use **minimal** map e.g. `{"uri": "...", "captured_at": "..."}` **only if** server accepts — **verify against `JobMediaSubmission` usage** or integration test. |
| **Repositories** | `MediaRepository` |
| **Screens** | `JobMediaScreen` — camera/gallery → build `payloads` |
| **Risk** | If backend expects base64 in JSON, implement encoding; **do not** invent S3 upload without backend |
| **Acceptance** | Photo count satisfies `JobMediaRequirement.required_photo_count` when server counts rows |

---

### 4.7 Signatures

| Field | Specification |
|-------|----------------|
| **Purpose** | `POST /jobs/{job_id}/signature` body `JobSignatureSubmitIn` (`signature: map`). |
| **Repositories** | `SignaturesRepository` |
| **Screens** | `JobSignatureScreen` — capture points or base64 in `signature` map per product decision |
| **Acceptance** | `JobSignatureRequirementOut.satisfied_at` non-null after submit |

---

### 4.8 Compliance / Certificates

| Field | Specification |
|-------|----------------|
| **Purpose** | **Current backend:** `GET /compliance/certificates`, `POST /compliance/certificates/generate` → **`require_roles`** **Admin, Dispatcher only** — **Engineer cannot use**. |
| **Mobile behavior** | **Hide** certificate generation OR show read-only message: “Certificates are created by dispatch.” **Do not** ship broken API calls. |
| **If backend adds Engineer read** (§7) | Then `ComplianceRepository.listCertificates(jobId)` |
| **Dependencies** | Blocked on §7 for any real feature |

---

### 4.9 Inventory / Parts

| Field | Specification |
|-------|----------------|
| **Purpose** | `POST /jobs/{job_id}/parts-usage` body `JobPartsUsageSubmitIn` (`items: list[dict]`). |
| **Backend** | `reconcile_parts_usage_submission` may raise **400** — parse `detail` |
| **Repositories** | `PartsRepository` |
| **Screens** | `JobPartsScreen` |
| **Acceptance** | Items satisfy `required_parts_items_count` when counted server-side |

---

### 4.10 Vehicle checks

| Field | Specification |
|-------|----------------|
| **Purpose** | `POST /vehicles/{vehicle_id}/inspections`, `GET` list/latest; defects endpoints if product needs. |
| **Access** | `_ensure_vehicle_access`: Engineer only **own** `user.assigned_vehicle_id`. |
| **Blocker** | `UserOut` **does not** expose `assigned_vehicle_id` — **§7 required** or manual entry **not allowed** for production. |
| **Repositories** | `VehiclesRepository` |
| **Screens** | `VehicleInspectionScreen` |
| **Payload** | `VehicleInspectionCreateIn` per `vehicles/schemas.py` — engineer_id must match current user for Engineer |

---

### 4.11 Notifications

| Field | Specification |
|-------|----------------|
| **Purpose** | No push notification API for **mobile** in audited backend. |
| **Implementation** | **Optional:** `flutter_local_notifications` for “sync pending” reminders; **no** FCM wiring until backend provides device registration + topics. |
| **Acceptance** | Feature-flagged off by default |

---

### 4.12 Sync / Offline

| Field | Specification |
|-------|----------------|
| **Purpose** | Outbox processor + connectivity; **see §6** |
| **Dependencies** | `connectivity_plus`, `drift`, `sync_worker` |

---

### 4.13 Settings / Diagnostics

| Field | Specification |
|-------|----------------|
| **Purpose** | Display API base (read-only), app version, “Clear cache”, logout, sync status |
| **Files** | `settings_screen.dart` |

---

## 5. Screen-by-screen build spec

| Route name | Path | Purpose | Data sources | Actions | Loading | Empty | Error | Offline | Permission |
|------------|------|---------|--------------|---------|---------|-------|-------|---------|------------|
| `LoginScreen` | `/login` | OAuth2 password | — | POST `/auth/token` | button disabled | — | show `ApiException` | login requires network | public |
| `JobListScreen` | `/jobs` | Assigned work | `GET /jobs` + cache | navigate to detail | pull refresh | “No jobs assigned” | banner | show cached + stale badge | authenticated |
| `JobDetailScreen` | `/jobs/:id` | Job context | `GET /jobs/:id`, `GET .../completion-requirements`, `GET .../sla`, geofence GET | Accept, Punch, Navigate to sub-screens | skeleton | — | per-section | cached job + warnings | authenticated |
| `PunchPanel` | `/jobs/:id/punch` or section | Punch in/out | GPS + `POST /time/punch/*` | punch | busy overlay | — | geofence/punch errors | queue + “pending sync” | Engineer |
| `CompletionChecklistScreen` | `/jobs/:id/completion` | Gate status | completion bundle | open form/media/etc. | — | all satisfied banner | — | read-only cache | authenticated |
| `JobFormScreen` | `/jobs/:id/forms/:formKey` | Submit form | requirement + POST submit | submit | — | — | missing keys | queue **if** safe | — |
| `JobMediaScreen` | `/jobs/:id/media` | Photos | media requirement + POST | submit | — | — | — | queue | — |
| `JobSignatureScreen` | `/jobs/:id/signature` | Sign | POST signature | submit | — | — | — | queue | — |
| `JobPartsScreen` | `/jobs/:id/parts` | Parts lines | POST parts-usage | submit | — | — | inventory errors | queue | — |
| `VehicleInspectionScreen` | `/vehicles/inspection` | Pre-use | §7 vehicle id + POST inspection | submit | — | no vehicle | — | queue | — |
| `SettingsScreen` | `/settings` | Diagnostics | local + `GET /auth/me` | logout, clear | — | — | — | — | authenticated |

**Note:** `GET /dispatch/jobs/{job_id}/tracking` is **Dispatcher/Admin only** — **do not** add Engineer screen for it unless backend changes.

---

## 6. Offline-first execution design

### 6.1 Queue table schema (Drift)

Table `outbox_ops`:

| Column | Type | Notes |
|--------|------|-------|
| `id` | int PK autoincrement | |
| `client_op_id` | text UNIQUE | UUID for idempotency |
| `operation_type` | text | `punch_in`, `punch_out`, `telemetry`, (future) |
| `http_method` | text | POST |
| `path` | text | e.g. `/time/punch/in` |
| `request_body_json` | text | Full JSON body |
| `idempotency_key` | text | Same as `client_op_id` unless split |
| `created_at` | datetime | |
| `attempt_count` | int | |
| `last_attempt_at` | datetime | nullable |
| `last_error` | text | nullable |
| `status` | text | `pending`, `in_flight`, `completed`, `failed` |

Table `jobs_cache`: `job_id`, `json_payload`, `fetched_at`.

### 6.2 Queued operation types (safe)

| Type | Safe to queue | Notes |
|------|----------------|-------|
| `punch_in` / `punch_out` | **Yes** after §7 idempotency | Until then **queue but warn** duplicate risk |
| `telemetry` | **Yes** (best-effort) | May be stale; server uses `occurred_at` |
| `GET` | **No** | Cache only |

### 6.3 Sync worker behavior

- Trigger: `app resume`, `connectivity` changed to online, periodic **15s** while pending & foreground.
- **FIFO** by `created_at`.
- **Mark** `in_flight` → POST → success → `completed` + delete row; failure → `attempt_count++`, `last_error`, `pending`.

### 6.4 Retry policy

- Exponential backoff: `min(60s, 2^attempt * 2s)`; max **5** attempts then `failed` + user notification.

### 6.5 Dedupe / idempotency

- Send `Idempotency-Key: <client_op_id>` when `dio` + backend **§7** ready.
- **Until backend:** accept duplicate punch risk (audit gap).

### 6.6 Media upload strategy

- **Large JSON** in outbox may exceed SQLite row size — **Phase:** store payload path on disk (`file://` in app dir) + reference in outbox; **or** only queue after §7 multipart.
- **MVP:** media submit **online-only** if payloads are large.

### 6.7 Stale data markers

- Show `fetched_at` on job detail if older than **5 minutes** when offline.

### 6.8 Conflict behavior

- **Server wins** on replay; if 409/400 duplicate, treat as success if detail indicates idempotent hit (§7).

### 6.9 User-visible sync indicators

- App bar badge: `N pending`; **Settings** screen full list.

---

## 7. Backend changes required for mobile production-readiness

Only **necessary** changes.

| # | Why insufficient | Affected | Change | Blocking? | Safe now? |
|---|------------------|----------|--------|-----------|-----------|
| B1 | Duplicate `punch_in` rows possible | `time_tracking/service.py` `punch_in` | Reject open `in` without `out` for same user/job | **Blocking** for payroll integrity | Add test + fix |
| B2 | Mobile replay duplicates | `time_tracking/routes.py` (or middleware) | Accept `Idempotency-Key` header; store hash of `(user_id, key)` → return same `PunchOut` | **Blocking** for offline punch | **Requires** DB table or cache |
| B3 | Engineer cannot see vehicle id | `auth/schemas.py` `UserOut`, `GET /auth/me` | Add `assigned_vehicle_id: str \| None` | **Blocking** vehicle UX without hacks | Yes — additive field |
| B4 | Engineer cert visibility | `compliance/routes.py` | Add `Engineer` to `GET /certificates` with **scope** = jobs assigned to user OR read-only cert summary for job | **Non-blocking** if product accepts dispatch-only certs | **Careful** with data leakage — filter by `job_id` + assignment |
| B5 | Optional: dispatch tracking for engineer | `dispatch_tracking_routes.py` | Add Engineer role with **same** assignment check as `GET /jobs/{id}` | **Non-blocking** | Product decision |
| B6 | Punch history for mobile | new `GET /time/punches` or extend timesheet | Return today’s punches for engineer | **Non-blocking** for duplicate UX | New endpoint |

---

## 8. Testing specification

### 8.1 Unit tests

- `auth_token_test.dart` — **keep**; add `error_mapper_test.dart`, `idempotency_test.dart`, `outbox_dao_test.dart` (drift in-memory).

### 8.2 Widget tests

- `login_screen_test.dart` — loading + error text
- `job_list_screen_test.dart` — empty vs list (mock provider)

### 8.3 Integration tests

- `integration_test/app_test.dart` — login → job list (against **real** backend or `docker-compose` with seed user) — **gate** in CI.

### 8.4 Offline / sync tests

- Drift in-memory: insert outbox → worker processes → row deleted (mock Dio returning 200).

### 8.5 Retry / idempotency tests

- Mock Dio: first call 503, second 200 with same body — worker retries.

### 8.6 Geofence / punch edge cases

- Fixture: 400 `detail` “Geofence not set” — UI shows message.

### 8.7 Job workflow

- Mock `POST /jobs/{id}/accept` → 200 `JobOut.status == accepted`.

### 8.8 Upload failures

- `POST /jobs/{id}/media` 400 — show `detail`.

### 8.9 Stale telemetry

- Queue old `occurred_at` — server accepts; verify client sends UTC ISO-8601.

---

## 9. Implementation order

### Wave 1 — Foundational infrastructure

| Tasks | Dependencies | Definition of done |
|-------|----------------|---------------------|
| Add `pubspec` deps: riverpod, go_router, dio, drift, secure_storage, uuid, connectivity_plus, json_serializable, build_runner | — | `flutter pub get` clean |
| `AppConfig`, `Dio` + interceptors, `ApiException`, `TokenStorage`, `SessionController` | — | Login works end-to-end |
| Drift schema + outbox tables (empty worker) | Wave 1 deps | DB opens on iOS/Android |
| Thin `main.dart` + `go_router` | Session | `/login` ↔ `/jobs` |

### Wave 2 — Core engineer workflow

| Tasks | Dependencies | Definition of done |
|-------|----------------|---------------------|
| `JobsRepository` + `JobListScreen` + `JobDetailScreen` | Wave 1 | `GET /jobs`, `GET /jobs/{id}` |
| `GeofenceRepository` + pre-punch check UI | Wave 2 | `GET /tracking/geofences/{job_id}` |
| `TimeRepository` + punch UI | Wave 2 | Punch in/out live |
| `TrackingRepository` + telemetry service | Wave 1 | Parity with `main.dart` throttle |
| `CompletionRepository` + checklist UI | Wave 2 | `GET .../completion-requirements` |

### Wave 3 — Compliance / evidence

| Tasks | Dependencies | Definition of done |
|-------|----------------|---------------------|
| Forms repository + screen | Wave 2 | Submit at least one `form_key` |
| Media + signature + parts screens | Wave 2 | Each hits real POST once in manual QA |
| Vehicle inspection | **B3** or workaround | **Blocked** until `assigned_vehicle_id` on `/auth/me` |

### Wave 4 — Offline / sync hardening

| Tasks | Dependencies | Definition of done |
|-------|----------------|---------------------|
| `SyncWorker` for punch + telemetry | Wave 1–2 | Airplane mode test: queues + replays |
| **B1** backend | — | Duplicate punch prevented |
| **B2** backend | Wave 4 + B2 | Idempotent replay |

### Wave 5 — Operational extras

| Tasks | Dependencies | Definition of done |
|-------|----------------|---------------------|
| `GET /time/timesheets` screen | Wave 2 | Engineer sees today |
| Settings + diagnostics | Wave 1 | Version, logout, pending count |
| `follow-on` defects | Wave 2 | Optional |

---

## 10. Cursor execution checklist

Use this **in order**; check off when done.

- [ ] **W1:** Add dependencies to `mobile/pubspec.yaml` per §2.1; run `flutter pub get`.
- [ ] **W1:** Create `lib/core/config/app_config.dart` — copy `apiBase` logic from `main.dart` verbatim.
- [ ] **W1:** Create `lib/core/network/dio_client.dart` + `auth_interceptor.dart` reading token from `TokenStorage`.
- [ ] **W1:** Create `lib/core/errors/api_exception.dart` + `error_mapper.dart` parsing `detail`.
- [ ] **W1:** Create `lib/core/auth/token_storage.dart`, `session_controller.dart`, `jwt_util.dart` (move `sub` decode from `main.dart`).
- [ ] **W1:** Create `lib/app/router.dart` — routes `/login`, `/jobs`, `/jobs/:id`, `/settings`.
- [ ] **W1:** Create `lib/features/auth/presentation/login_screen.dart` — migrate from `LoginScreen` in `main.dart`.
- [ ] **W1:** Create `lib/core/persistence/app_database.dart` with Drift tables from §6.1; run `build_runner`.
- [ ] **W1:** Replace `main.dart` with `runApp(ProviderScope(child: PhiDpsApp()))` only.
- [ ] **W2:** Implement `JobsRepository` — `GET /jobs`, `GET /jobs/{id}`; DTOs match `JobOut`.
- [ ] **W2:** Implement `JobListScreen`, `JobDetailScreen` — remove dropdown job id hack; **no** manual job id field.
- [ ] **W2:** Implement `GET /tracking/geofences/{job_id}` + warning banner.
- [ ] **W2:** Implement `TimeRepository` + punch UI; include optional `offline_device_id` (stable device id from `uuid` + storage) in JSON body.
- [ ] **W2:** Migrate telemetry to `EngineerTelemetryService` + `TrackingRepository`.
- [ ] **W2:** Implement `CompletionRepository` + checklist from `GET /jobs/{id}/completion-requirements`.
- [ ] **W3:** Implement `FormsRepository` + `JobFormScreen` — handle `missing_required_keys` in `detail`.
- [ ] **W3:** Implement `MediaRepository` + `JobMediaScreen` — **confirm payload shape** with backend test.
- [ ] **W3:** Implement `SignaturesRepository` + `JobSignatureScreen`.
- [ ] **W3:** Implement `PartsRepository` + `JobPartsScreen`.
- [ ] **W3:** Implement `POST /vehicles/{id}/inspections` **after** B3 (`UserOut.assigned_vehicle_id`) — **do not** ship without it.
- [ ] **W4:** Implement `SyncWorker` + `outbox_ops` processing for punch + telemetry only.
- [ ] **W4:** Coordinate backend PRs for B1 + B2.
- [ ] **W5:** Timesheet screen + Settings + optional follow-on defects.
- [ ] **All:** Remove dead code from old `main.dart`; ensure `flutter test` + `flutter analyze` passes.
- [ ] **All:** Document **no** calls to `/dispatch/jobs/*` tracking for Engineer (403) and **no** `/compliance/certificates` until B4.

---

## Appendix A — Known backend ↔ mobile mismatches

| Topic | Fact |
|-------|------|
| `ApiClient.vehicleId` in current `main.dart` | JWT `sub` = **user id**, not vehicle — **rename** |
| `GET /dispatch/jobs/{job_id}/tracking` | **Dispatcher/Admin** — Engineer **403** |
| Compliance certificates REST | **Admin/Dispatcher** only |
| Job status transitions | **No** central allow-list in `update_job_status` — mobile must not rely on client-side enum |
| Invoice generation | Requires **completed** job + certificate — **engineer app does not** generate invoices |

---

## Appendix B — pubspec dependency block (add to `mobile/pubspec.yaml`)

```yaml
dependencies:
  flutter_riverpod: ^2.5.1
  go_router: ^14.2.0
  dio: ^5.7.0
  drift: ^2.18.0
  sqlite3_flutter_libs: ^0.5.24
  path_provider: ^2.1.4
  path: ^1.9.0
  flutter_secure_storage: ^9.2.2
  uuid: ^4.5.1
  connectivity_plus: ^6.0.5
  package_info_plus: ^8.0.0
  json_annotation: ^4.9.0
  geolocator: ^13.0.2  # existing
  http: ^1.2.2        # remove after migration to dio if unused

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.11
  drift_dev: ^2.18.0
  json_serializable: ^6.8.0
```

*(Version pins may be bumped by `flutter pub upgrade` within SDK constraints.)*

---

**End of build spec.**
