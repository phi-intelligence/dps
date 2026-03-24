# Production go-live checklist

Use this list to **close** the product for a real environment. Feature development (marathon §5.1–§5.19) is complete; production is **configuration + operations**.

## Phase A — Build & deploy

- [ ] **Private env file**: production uses a secret-backed `.env` (or platform equivalent), not committed `.env.example`.
- [ ] **Database**: PostgreSQL (or chosen server) provisioned; backups + restore drill scheduled. Apply [backend/db/postgres/](backend/db/postgres/) DDL if you are not on SQLite auto-migrations.
- [ ] **Admin web API URL**:
  - [ ] **Build-time**: set `REACT_APP_PHI_DPS_API_BASE` to the **browser-reachable** API origin (e.g. `https://api.example.com`), **or**
  - [ ] **Runtime**: after deploy, edit `config.js` in the static root so `window.__PHI_DPS_CONFIG__.apiBase` is that origin (no rebuild).
  - [ ] Confirm login screen shows the expected “API base” line.
- [ ] **Docker web image**: `docker compose build --build-arg REACT_APP_PHI_DPS_API_BASE=https://... web` when using [web/Dockerfile](web/Dockerfile).
- [ ] **TLS**: HTTPS for API and web in front of users.

## Phase B — Backend configuration

- [ ] `PHI_DPS_SECRET_KEY` strong and unique; not `dev-secret-change-me`.
- [ ] `PHI_DPS_DEV_BOOTSTRAP=0` (no default users in production).
- [ ] `PHI_DPS_ROLLOUT_RUNNER_ENABLED=0` on API replicas unless you intentionally run the in-process loop.
- [ ] `PHI_DPS_CORS_ORIGINS` lists your **real** admin web origin(s) (scheme + host + port).
- [ ] `PHI_DPS_PORTAL_WEB_BASE` is the **customer** portal URL used in emails/PDFs (not localhost).
- [ ] Webhook HMAC secrets rotated: `PHI_DPS_NOTIFICATION_WEBHOOK_SECRET`, `PHI_DPS_COMMUNICATION_WEBHOOK_SECRET`, `PHI_DPS_ESIGN_WEBHOOK_SECRET`.
- [ ] **Preflight**: `PYTHONPATH=. python backend/scripts/check_deploy_env.py --strict` passes (or every WARN is accepted and documented).

## Phase C — Integrations

- [ ] Outbound email/SMS (or simulated mode consciously chosen).
- [ ] E-sign (DocuSign etc.): demo → production credentials; Connect/webhook URL and secret match.
- [ ] Document storage: `s3` (or local with backup path) configured and tested upload/download.
- [ ] Optional AI drafting: `GEMINI_*` + `PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED` only if used; staff trained to review output.

## Phase D — Operations

- [ ] `GET /health` + `GET /health/ready` in load balancer health checks.
- [ ] Recurring jobs: single runner per environment ([DEPLOYMENT.md](DEPLOYMENT.md) cron / `run_due_recurring_jobs.py`).
- [ ] Logs: e.g. `PHI_DPS_LOG_JSON_ACCESS=1` shipped to your aggregator.
- [ ] Runbook: who responds to `GET /system/dashboard/operations-diagnostics` alerts.
- [ ] Real admin users and RBAC; remove reliance on bootstrap passwords.

## Phase E — Acceptance

- [ ] Staging UAT: portal + admin critical path (quote/job/invoice or your contract/repricing path as applicable).
- [ ] Legal/commercial: credit notes external-system stance, SLAs, privacy/DPA as required.

When **A–E** are checked, treat the release as **production-ready for your organisation**.
