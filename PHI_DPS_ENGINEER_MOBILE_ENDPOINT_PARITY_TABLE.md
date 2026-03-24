# PHI-DPS Engineer Mobile — Engineer Endpoint Parity Table

Scope: engineer-facing backend endpoints relevant to mobile app workflows.

Legend:

- **Implemented**: endpoint is used by current mobile code path.
- **Implemented (conditional)**: used when feature flag/capability allows.
- **Intentionally not used**: backend endpoint is admin/dispatch scope or outside engineer mobile scope.
- **Gap**: engineer-relevant endpoint exists but no mobile integration yet.

## 1) Auth and session

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `POST /auth/token` | `mobile/lib/features/auth/data/auth_repository.dart` | Implemented | Login flow. |
| `GET /auth/me` | `mobile/lib/features/auth/data/current_user_repository.dart` | Implemented | Used for vehicle assignment context. |

## 2) Jobs and core workflow

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `GET /jobs` | `mobile/lib/features/jobs/data/jobs_repository.dart` | Implemented | Jobs list. |
| `GET /jobs/{job_id}` | `mobile/lib/features/jobs/data/jobs_repository.dart` | Implemented | Job detail. |
| `POST /jobs/{job_id}/accept` | `mobile/lib/core/sync/sync_coordinator.dart` (+ jobs repo direct path) | Implemented | Queue + idempotency handling. |
| `GET /tracking/geofences/{job_id}` | `mobile/lib/features/jobs/data/jobs_repository.dart` | Implemented | Geofence awareness for punch context. |

## 3) Time and telemetry

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `POST /time/punch/in` | `mobile/lib/core/sync/sync_coordinator.dart` and `mobile/lib/features/time_punch/data/time_repository.dart` | Implemented | Outbox path used for reliability. |
| `POST /time/punch/out` | `mobile/lib/core/sync/sync_coordinator.dart` and `mobile/lib/features/time_punch/data/time_repository.dart` | Implemented | Outbox path used for reliability. |
| `POST /tracking/telemetry/engineer` | `mobile/lib/core/sync/sync_coordinator.dart` | Implemented | Best-effort policy. |

## 4) Completion and evidence

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `GET /jobs/{job_id}/completion-requirements` | `mobile/lib/features/completion/data/completion_repository.dart` | Implemented | Completion readiness. |
| `POST /jobs/{job_id}/forms/{form_key}/submit` | `mobile/lib/core/sync/sync_coordinator.dart`, `mobile/lib/features/evidence/data/job_evidence_repository.dart` | Implemented | Queue + immediate paths. |
| `POST /jobs/{job_id}/signature` | `mobile/lib/core/sync/sync_coordinator.dart`, `mobile/lib/features/evidence/data/job_evidence_repository.dart` | Implemented | Queue + immediate paths. |
| `POST /jobs/{job_id}/media` | `mobile/lib/core/sync/sync_coordinator.dart`, `mobile/lib/features/evidence/data/job_evidence_repository.dart` | Implemented | Legacy/default media path. |
| `GET /jobs/media/capabilities` | `mobile/lib/core/sync/sync_coordinator.dart` | Implemented | Phase-2 branch decision. |
| `POST /jobs/{job_id}/media/upload-sessions` | `mobile/lib/core/sync/sync_coordinator.dart` | Implemented (conditional) | Used when phase-2 flag enabled. |
| `POST /jobs/{job_id}/media/upload-sessions/{session_id}/commit` | `mobile/lib/core/sync/sync_coordinator.dart` | Implemented (conditional) | Falls back to legacy media on failure. |
| `POST /jobs/{job_id}/parts-usage` | `mobile/lib/core/sync/sync_coordinator.dart`, `mobile/lib/features/evidence/data/job_evidence_repository.dart` | Implemented | Queue + immediate paths. |
| `GET /inventory/engineer/items/search` | `mobile/lib/features/evidence/data/inventory_lookup_repository.dart` | Implemented | SKU lookup support. |

## 5) Activity and notes

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `GET /jobs/{job_id}/activity` | `mobile/lib/features/jobs/data/job_activity_repository.dart` | Implemented | Timeline rendering in job activity section. |
| `POST /jobs/{job_id}/notes` | `mobile/lib/core/sync/sync_coordinator.dart` | Implemented | Queued/synced note submission. |

## 6) Vehicle checks

| Backend endpoint | Mobile implementation | Status | Notes |
|---|---|---|---|
| `GET /vehicles/{vehicle_id}/inspections/latest` | `mobile/lib/features/vehicles/data/vehicle_checks_repository.dart` | Implemented | Daily check context. |
| `GET /vehicles/{vehicle_id}/defects?status=open` | `mobile/lib/features/vehicles/data/vehicle_checks_repository.dart` | Implemented | Open defect visibility. |
| `POST /vehicles/{vehicle_id}/inspections` | `mobile/lib/features/vehicles/data/vehicle_checks_repository.dart` | Implemented | Daily inspection submission. |
| `POST /vehicles/{vehicle_id}/defects` | `mobile/lib/features/vehicles/data/vehicle_checks_repository.dart` | Implemented | Issue capture from check flow. |

## 7) Engineer-scope intentional non-coverage

These endpoints exist in backend but are intentionally not exposed in engineer mobile due to role/scope:

- time approvals and payroll export endpoints (admin/office scope)
- job costing/labour-costing endpoints (dispatcher/admin scope)
- admin settings/runtime controls

## 8) Current actionable gaps

1. Validate backend test coverage for activity typed events and media phase-2 branch behavior in CI-supported Python runtime.
2. Keep docs synchronized when engineer capabilities change (notes and media phase-2 are now implemented/conditional, not blocked).
