# PHI-DPS — deployment and operations (Phase 3 hardening)

This document supports **§5.6–5.8** of the marathon plan: standing up environments, secrets, health checks, diagnostics, and recurring jobs. For ordered delivery gates, see [MARATHON_PIPELINE.md](./MARATHON_PIPELINE.md).

## New environment checklist (§5.6)

1. Copy `.env.example` to `.env` (or inject equivalent key/value secrets in your platform). **Do not** point production at `.env.example` as the only file — compose samples use it for convenience; real deploys need a private env source.
2. Set strong `PHI_DPS_SECRET_KEY` and all webhook HMAC secrets; configure `PHI_DPS_DATABASE_URL` (Postgres or SQLite).
3. Set `PHI_DPS_CORS_ORIGINS` to your real web app origin(s); set `PHI_DPS_PORTAL_WEB_BASE` for customer links in emails/PDFs.
4. Set `PHI_DPS_DEV_BOOTSTRAP=0` in production unless you are deliberately recreating demo users.
5. Set `PHI_DPS_ROLLOUT_RUNNER_ENABLED=0` for typical production API deployments (use cron or `POST /system/jobs/run-due` instead).
6. Run the env audit: `PYTHONPATH=. python backend/scripts/check_deploy_env.py` — use `--strict` in CI when the environment should be production-like.
7. Start the API; verify `GET /health` and `GET /health/ready` (readiness runs `SELECT 1` on the DB).
8. Log in with a real admin user (or the one-time bootstrap accounts if bootstrap is still on in a staging sandbox).
9. Open **Commercial hub** in the web app for cross-domain dashboards, or call `GET /system/integration-status` and `GET /system/dashboard/operations-diagnostics` with an admin token.

## Admin web (React) — API base URL

The SPA calls the backend from the **user’s browser**. The API origin is **not** derived from Docker internal DNS (`http://backend:8000` is wrong for browsers on the host).

1. **Build-time (recommended for immutable images):** set `REACT_APP_PHI_DPS_API_BASE` when building the web image (see `web/Dockerfile` `ARG` / `docker-compose.yml` `args`).
2. **Runtime:** ship `config.js` next to `index.html` and set `window.__PHI_DPS_CONFIG__ = { apiBase: "https://api.example.com" };` (see `web/public/config.js`). Rebuild not required.
3. **Local dev:** optional `web/.env.local` with `REACT_APP_PHI_DPS_API_BASE=http://127.0.0.1:8000`.

See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) and [web/.env.example](./web/.env.example).

## Environment variables

- Copy `.env.example` to `.env` and fill values. Never commit real secrets.
- **Core:** `PHI_DPS_SECRET_KEY`, `PHI_DPS_DATABASE_URL`, `PHI_DPS_CORS_ORIGINS`.
- **Portal links:** `PHI_DPS_PORTAL_WEB_BASE` (customer-facing web origin, not the API host).
- **Portal copy:** `PHI_DPS_PORTAL_SUPPORT_EMAIL`, `PHI_DPS_PORTAL_SUPPORT_PHONE` (optional; defaults exist in `config.py`).
- **E-sign:** `PHI_DPS_ESIGN_*` (see `.env.example`). JWT private key path must be readable only by the API process.
- **Outbound email:** `PHI_DPS_COMMUNICATION_*`, SMTP credentials.
- **Webhooks:** `PHI_DPS_NOTIFICATION_WEBHOOK_SECRET`, `PHI_DPS_COMMUNICATION_WEBHOOK_SECRET`, `PHI_DPS_ESIGN_WEBHOOK_SECRET` — rotate independently per environment.
- **Policy / automation:** `PHI_DPS_ACCEPTANCE_POLICY_MODE`, `PHI_DPS_AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE`, recurring job `payload_json` (via `/system/jobs` API), not always separate env keys.
- **Observability (§5.7):** `PHI_DPS_LOG_JSON_ACCESS=1` emits one JSON line per request to logger `phi_dps.access` (health endpoints excluded). Ship those logs to your aggregator in production.

Every variable read by `backend/app/core/config.py`, rollout (`PHI_DPS_ROLLOUT_*`), auth bootstrap emails (`PHI_DPS_*_EMAIL` / `PHI_DPS_*_PASSWORD` in `modules/auth/service.py`), and `GEMINI_*` is listed or cross-referenced in `.env.example`. Treat that file as the canonical checklist when auditing a new environment.

### Secrets audit (before go-live)

- Rotate `PHI_DPS_SECRET_KEY`, all webhook HMAC secrets, SMTP and S3 credentials, and DocuSign RSA material from any dev defaults.
- Ensure JWT private key files and `.env` are not world-readable on the host.
- Confirm `PHI_DPS_DEV_BOOTSTRAP=0` so default passwords are not recreated in production.

SQLite dev DBs pick up **additive** columns via `migrate_sqlite_schema()` on startup. For PostgreSQL or full migrations, use your organisation’s migration tool (e.g. Alembic); apply the same additive columns as in `sqlite_migrations.py` or generate equivalents, and keep ORM models in sync. There is no bundled Alembic revision in-repo — production teams should own migration history.

**PostgreSQL:** `migrate_sqlite_schema` is a no-op. You still get `create_all` on startup (creates missing tables); **alter** history must be applied with your migration tool. Staging should mirror production migration order before go-live.

## Process and startup

- Run the API with `PHI_DPS_DEV_BOOTSTRAP=0` in production unless you intentionally want default admin/bootstrap behaviour.
- **Health:** `GET /health` (liveness). `GET /health/ready` runs `SELECT 1` against the configured database (readiness).
- **Idempotency:** startup calls `Base.metadata.create_all` and SQLite migrations; safe to repeat if the process restarts or multiple workers start (SQLite additive migrations use per-column guards).

## Docker Compose note

The sample [docker-compose.yml](./docker-compose.yml) mounts `env_file: .env.example` for a quick demo. For anything beyond local experimentation, point `env_file` at a **private** `.env` (or remove the file from version control and inject secrets via your host).

## Backup and restore

- **SQLite:** stop the API (or ensure no writers), copy the database file configured in `PHI_DPS_DATABASE_URL`, and copy `PHI_DPS_DOCUMENT_STORAGE_ROOT` if using local document storage.
- **PostgreSQL:** use `pg_dump` / `pg_restore` (or managed backup) for the application database. Restore **before** re-pointing traffic; run your migration tool if restoring to a newer code version.
- **S3 / object storage:** enable versioning or periodic bucket replication if compliance requires it; presigned download links in the app do not replace durable backup of the underlying objects.
- **Order of restore:** database first (referential integrity), then files whose metadata rows exist, or restore DB from a backup taken together with storage snapshot for a consistent cut.

## Document and file storage

- Default local provider: `PHI_DPS_DOCUMENT_STORAGE_PROVIDER=local`, `PHI_DPS_DOCUMENT_STORAGE_ROOT`.
- S3-compatible: set provider to `s3` and supply bucket, region, credentials, optional endpoint (e.g. MinIO). Presigned TTL via `PHI_DPS_S3_PRESIGNED_TTL_SECONDS`. Keys may fall back to `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` when `PHI_DPS_S3_*` are unset (see `documents` storage adapter).
- **Backup:** include document storage root or bucket in backup scope; DB alone is not sufficient if PDFs/objects live on disk or S3.
- **Permissions:** the API user needs read/write on `PHI_DPS_DOCUMENT_STORAGE_ROOT` (local) or IAM-equivalent for the bucket prefix.

## Recurring jobs (§5.8)

- Definitions live in `recurring_job_runner_service.DEFAULT_JOB_SEED`; runs are stored in `recurring_system_job_runs`.
- **Cron pattern:** from the repository root, with `PYTHONPATH` set to the directory that contains the `backend` package:

  `PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py --limit 20`

- **Actor attribution:** pass `--actor-email user@example.com` or set `PHI_DPS_RECURRING_JOBS_ACTOR_EMAIL` so job run rows show who triggered the CLI (defaults to `admin@example.com` when that user exists).
- Use **one runner per environment** to avoid overlapping executions. Tune `--limit` to the number of due jobs you allow per tick.
- **API:** `POST /system/jobs/run-due` (authenticated, privileged) is an alternative to cron when an internal scheduler is acceptable.
- **Single-runner enforcement:** use a process manager, Kubernetes `CronJob` with `concurrencyPolicy: Forbid`, or an external lock (e.g. Postgres advisory lock) if you run multiple API replicas — only one process should execute `run-due` at a time per environment.
- **Idempotency (high level):** amendment activation and recommendation scans are designed to be safe when re-run; commercial follow-up scans dedupe on communication records and entity ids. Still prefer single-runner to avoid duplicate drafts under race conditions.

Example cron (every 15 minutes, single host):

`*/15 * * * * cd /app && PHI_DPS_DATABASE_URL=... PYTHONPATH=. python backend/scripts/run_due_recurring_jobs.py --limit 30 >>/var/log/phi-dps-recurring.log 2>&1`

## Operational diagnostics (§5.7)

- **Recurring failures:** `GET /system/dashboard/job-failures`
- **Cross-domain failures:** `GET /system/dashboard/operations-diagnostics` — one JSON payload with:
  - `recurring_job_failures` — failed `recurring_system_job_runs`
  - `contract_activation_failures` — failed activation runs
  - `customer_communication_delivery_failures` — failed outbound comms deliveries
  - `communication_provider_webhook_failures` — inbound provider webhooks where `processing_status=failed`
  - `rollout_notification_delivery_failures` — rollout `notification_deliveries` in `failed` or `dead_letter`
  - `rollout_webhook_invalid_signatures` — rollout callback posts with bad HMAC (`notification_webhook_events.signature_valid=false`)
  - `counts` — how many rows are included per section (capped by `limit_each`, default 40, max 200)
  The **Commercial hub** “Operational diagnostics” panel mirrors this endpoint.
- **Integration readiness (no secrets):** `GET /system/integration-status`
- **Aggregated blocker counts:** `GET /system/dashboard/operations-blockers-overview`
- **Contract side:** `GET /contracts/dashboard/activation-failures`, `GET /contracts/dashboard/version-history-summary`, `GET /contracts/{id}/versions/{vid}/readable-change`, `GET /contracts/{id}/versions/active-summary`, `GET /contracts/dashboard/activation-customer-lifecycle`
- **Structured access logs:** enable `PHI_DPS_LOG_JSON_ACCESS=1` and collect logger `phi_dps.access` in production (excludes `/health` and `/health/ready`).
- **Error shape:** API errors follow FastAPI conventions (`detail` string or list for validation). Prefer diagnostics endpoints over scraping logs when triaging domain failures.

## Finance queue (§5.4)

- `GET /invoicing/dashboard/finance-queue` (Admin, Finance)
- `GET /invoicing/dashboard/reconciliation-summary` — open invoice age buckets and outstanding totals
- `GET /invoicing/invoices/export-rows` — stable JSON rows for CSV / downstream import (optional `status` filter)
- Invoice list supports `status` and `finance_reviewed` query filters on `GET /invoicing/invoices`
- Invoice finance sign-off: `POST /invoicing/invoices/{id}/finance-review`, `POST .../clear-finance-review`

## Provider setup (quick checklist)

1. **SMTP:** set communication env vars; verify with a non-production inbox.
2. **DocuSign:** integration key, user GUID, account ID, RSA key, auth server (demo vs prod), Connect URL pointing at `POST /webhooks/esign/provider`, Connect HMAC secret matching `PHI_DPS_ESIGN_WEBHOOK_SECRET`.
3. **Communication provider webhooks:** HMAC secret aligned with `PHI_DPS_COMMUNICATION_WEBHOOK_SECRET`.

## Support

- Prefer diagnostics endpoints and commercial/contract dashboards before reading raw DB rows.
- For recurring job debugging, use `GET /system/job-runs` with filters (`run_status=failed`, `job_key=...`).
