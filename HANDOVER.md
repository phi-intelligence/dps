# PHI-DPS — Development team handover

**Purpose:** Single source of truth for onboarding engineers so development can continue without losing critical context. Read this together with `README.md`, `DEPLOYMENT.md`, `PRODUCTION_CHECKLIST.md`, `MARATHON_PIPELINE.md`, and `OPS_ALIGNMENT_TODO.md`.

---

## 1. What this product is

**PHI-DPS** is a field-service / M&E operations platform: CRM (leads/customers), quoting, dispatch (jobs, engineers, vehicles), time punch, compliance certificates, invoicing, contracts (commercial/amendments/activation), rollout automation, communications, and operational diagnostics.

**Repository layout (monorepo):**

| Area | Path | Stack |
|------|------|--------|
| API | `backend/` | Python 3.12+, FastAPI, SQLAlchemy, Uvicorn |
| Admin web | `web/` | React 19, TypeScript, Create React App (`react-scripts` 5), Leaflet / react-leaflet |
| Engineer mobile | `mobile/` | Flutter (Dart ≥3.3), `http`, `geolocator` |
| App entry (Docker/CLI) | Repo root `backend_main.py` | Re-exports `backend.app.main:app` |

**Important:** The Python package is `backend.app` — run the API with **`PYTHONPATH` = repository root** (see §4).

---

## 2. Architecture (mental model)

```
Browser (React SPA)  ──HTTPS/HTTP──►  FastAPI (Uvicorn)  ──►  DB (SQLite dev / Postgres prod)
       │                                      │
       │                                      ├── document storage (local / S3)
       └── Reads apiBase from config.ts       └── webhooks (comms, e-sign, rollout…)

Flutter engineer app  ──HTTP──►  Same API (JWT from /auth/token)
```

- **Admin UI** talks to the API from the **user’s browser**. The API URL must be **browser-reachable** (not Docker internal hostname `backend:8000` on the host machine).
- **Mobile** uses the same REST API; base URL is **platform-specific** (§7).

---

## 3. Documentation map (do not skip)

| Document | Use |
|----------|-----|
| `README.md` | Docker quick start, rollout endpoints overview |
| `DEPLOYMENT.md` | Env vars, CORS, DB/migrations, backups, recurring jobs, diagnostics |
| `PRODUCTION_CHECKLIST.md` | Go-live checklist (secrets, TLS, bootstrap off, etc.) |
| `.env.example` | **Canonical list** of backend environment variables (copy to private `.env`) |
| `web/.env.example` | CRA: only `REACT_APP_*` exposed; copy to `web/.env.local` for local overrides |
| `MARATHON_PIPELINE.md` | Historical delivery gates (§5.1–§5.19) — marked Done |
| `FINAL_MARATHON_PLAN.md` | Full scope reference (if present) |
| `OPS_ALIGNMENT_TODO.md` | **Remaining product/ops gaps** (offline queue, SLA realism, etc.) |
| `web/README.md` | CRA scripts + **HMR troubleshooting** |
| `mobile/README.md` | Flutter + **iOS codesign / Android emulator API IP** |

---

## 4. Local development — backend (API)

### Prerequisites

- Python **3.12+** recommended (matches `backend/Dockerfile`).
- Create a **virtualenv** at repo root or under `backend/` — **always activate before running** so `uvicorn` and deps resolve.

```bash
cd /path/to/phi-dps
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Environment

1. Copy **`.env.example` → `.env`** in the repo root (or export vars in your shell).
2. Default dev uses **SQLite** (`PHI_DPS_DATABASE_URL=sqlite:///./dev.db` in example).
3. With **`PHI_DPS_DEV_BOOTSTRAP=1`**, default users are created (see `.env.example` comments for emails/passwords — **disable in production**).

### Run server

From **repository root** (critical for imports):

```bash
export PYTHONPATH=.
# optional: export $(grep -v '^#' .env | xargs)   # or use direnv
uvicorn backend_main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://127.0.0.1:8000/health`
- Readiness (DB): `GET http://127.0.0.1:8000/health/ready`
- Preflight: `PYTHONPATH=. python backend/scripts/check_deploy_env.py` (add `--strict` for CI-like checks)

### Docker

- `docker compose up --build` — requires **Docker daemon running**.
- Compose file uses `env_file: .env.example` for demos; **real environments must use a private env file** (see `DEPLOYMENT.md`).

### Database notes

- **SQLite:** additive migrations run on startup via `migrate_sqlite_schema` in `backend/app/db/sqlite_migrations.py`.
- **PostgreSQL:** `create_all` creates missing tables; **schema changes** must be managed by your migration process. Reference DDL under `backend/db/postgres/` when aligning with production.

---

## 5. Local development — admin web (`web/`)

```bash
cd web
npm ci    # or npm install
npm start
```

- Opens dev server (typically `http://localhost:3000`).
- **API base URL** resolution (`web/src/config.ts`):
  1. `window.__PHI_DPS_CONFIG__.apiBase` from `web/public/config.js` (runtime, no rebuild)
  2. `REACT_APP_PHI_DPS_API_BASE` at **build** time
  3. Default `http://127.0.0.1:8000`

Set for local dev (optional): `web/.env.local`:

```bash
REACT_APP_PHI_DPS_API_BASE=http://127.0.0.1:8000
```

### Frontend pitfalls (known issues)

1. **`[HMR] Hot Module Replacement is disabled`** — See `web/README.md`. Use `npm start`, not a static server on the production build; avoid `NODE_ENV=production` for dev; clear cache / hard refresh.
2. **Leaflet / “Map container is already initialized”** — **`React.StrictMode` was removed** from `web/src/index.tsx` to avoid double-mount in dev breaking Leaflet. Re-enabling StrictMode may require map lifecycle fixes.
3. **Dependencies:** `web/package.json` pins **`ajv` / `ajv-keywords`** compatible with `react-scripts` — if `npm install` breaks schema resolution, align versions as in `package.json`.
4. **Fragile local fixes:** If `node_modules` was manually patched (webpack/HMR workarounds), those changes are **not durable** — prefer **documented reinstall**, **CRACO**, or **patch-package** for repeatable builds.

### Live dispatch map

- Component: `web/src/phase4/LiveDispatchMap.tsx`
- Uses **react-leaflet** + OpenStreetMap tiles.
- **Polling interval:** **10 seconds** (near–real-time dispatch; server push not implemented yet).
- See `OPS_ALIGNMENT_TODO.md` for follow-engineer freshness/aging and push updates.

### Client-side validation (recent)

In `web/src/App.tsx`:

- **Leads:** name required; valid email **if** provided (empty email allowed if phone-only); phone length check if provided; **at least email or phone**; **issue description ≥ 10 characters**.
- **Jobs:** quote must exist and **`status` must be `accepted`** (case-insensitive). **Backend may still allow other flows** — enforce server-side if product requires it.

---

## 6. Local development — mobile (`mobile/`)

```bash
cd mobile
flutter pub get
flutter run --dart-define=PHI_DPS_API_BASE=http://<HOST>:8000
```

### API base (`mobile/lib/main.dart`)

- Override with **`--dart-define=PHI_DPS_API_BASE=...`** for physical devices (use **machine LAN IP**).
- **Defaults when env empty:**
  - **Android emulator:** `http://10.0.2.2:8000` (host loopback from emulator — **`127.0.0.1` is wrong**).
  - **iOS Simulator / desktop:** `http://127.0.0.1:8000`.

### Engineer telemetry

- Continuous GPS via **`Geolocator.getPositionStream`** (movement filter + throttled **`POST /tracking/telemetry/engineer`**).
- Aligns with backend schema **`EngineerPhoneTelemetryIn`** (latitude, longitude, optional heading, speed, accuracy, `occurred_at`).
- **Not production-grade without:** offline queue, retry, battery policy review — see `OPS_ALIGNMENT_TODO.md`.

### Platform issues (read `mobile/README.md`)

- **macOS / iOS Simulator codesign “resource fork / detritus”** — xattr/Full Disk Access workarounds; **Android emulator** often simpler for API testing.
- **Android Gradle** merge/resource locks — stop daemons, `flutter clean`, documented in `mobile/README.md`.

---

## 7. Security & secrets (critical)

- **Never commit** real `.env`, API keys, JWT secrets, or PEM files.
- **`.env.example`** and **`web/.env.example`** are templates only.
- Production: `PHI_DPS_DEV_BOOTSTRAP=0`, strong `PHI_DPS_SECRET_KEY`, rotate webhook HMAC secrets (`PHI_DPS_NOTIFICATION_WEBHOOK_SECRET`, `PHI_DPS_COMMUNICATION_WEBHOOK_SECRET`, `PHI_DPS_ESIGN_WEBHOOK_SECRET`).
- **CORS:** `PHI_DPS_CORS_ORIGINS` must list the **actual admin web origin(s)**.

---

## 8. Authentication

- Staff/mobile: **`POST /auth/token`** (form-urlencoded `username`, `password`) → JWT.
- Web stores token (see `TOKEN_KEY` in `App.tsx`) and sends `Authorization: Bearer …`.
- RBAC is role-based; permissions vary by module — verify role for new endpoints in `backend/app/modules/auth` and route dependencies.

---

## 9. Key backend modules (navigation)

| Concern | Typical location |
|---------|------------------|
| Route aggregation | `backend/app/api/routes.py` |
| Config | `backend/app/core/config.py` |
| Tracking / telemetry | `backend/app/modules/tracking/` — e.g. `POST /tracking/telemetry/engineer` |
| Dispatch / jobs | `backend/app/modules/dispatch/` |
| CRM | `backend/app/modules/crm/` |
| Quotes | `backend/app/modules/quoting/` |
| Time | `backend/app/modules/time_tracking/` |
| Rollout | `backend/app/modules/rollout/` — internal scheduler env-gated |

Tests live under `backend/tests/` (e.g. `test_dispatch_telemetry_and_recommendations.py`). Run with `pytest` from repo root with `PYTHONPATH=.` set.

---

## 10. Operations & background work

- **Rollout runner:** `PHI_DPS_ROLLOUT_RUNNER_ENABLED` — prefer **off** on multiple API replicas; use cron + script or API (see `DEPLOYMENT.md`).
- **Recurring jobs:** `PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py` — single runner per environment.
- **Diagnostics:** `GET /system/dashboard/operations-diagnostics`, `GET /system/integration-status` (documented in `DEPLOYMENT.md`).

---

## 11. What was recently emphasized (field + dispatch UX)

- Mobile: **continuous GPS** + throttled telemetry to **`/tracking/telemetry/engineer`**; status text on engineer home.
- Web: **LiveDispatchMap** with markers, user location, follow controls; **10s refresh**.
- Web: stricter **lead** and **job** validation (see §5).
- **`OPS_ALIGNMENT_TODO.md`** tracks remaining M&E alignment (offline queue, SLA calendars, dispatch-ready checks beyond UI, etc.).

---

## 12. Risks & technical debt to plan for

| Risk | Mitigation |
|------|------------|
| Client-only job/lead rules | Add server-side validation if contracts require it |
| Telemetry offline / flaky networks | Implement queue + retry (`OPS_ALIGNMENT_TODO.md`) |
| CRA / webpack fragility | Pin deps; consider CRACO or migrate tooling in a planned sprint |
| No Alembic in repo | Own migration strategy for Postgres |
| macOS Flutter codesign | Use Android emulator or documented xattr/FDA workarounds |
| Docker not running locally | Use native Python + `npm start` + `flutter run` instead |

---

## 13. Quick verification checklist for new devs

1. Backend: `/health` and `/health/ready` OK.
2. Web: login works; login screen shows expected **API base** line.
3. Web: open **Live dispatch** tab — map loads (tiles + markers) without console errors.
4. Mobile (emulator): login + jobs list; telemetry calls succeed to host API (`10.0.2.2` on Android emulator).
5. Run **`check_deploy_env.py`** before any staging/prod deploy.

---

## 14. Contacts / ownership

- **Product owner / security / infra:** assign internally.
- **This file:** update when stack, env vars, or runbooks change.

---

*Last updated for handover: March 2026.*
