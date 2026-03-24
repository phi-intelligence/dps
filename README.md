# PHI-DPS

Phase 6 deployment and rollout operations baseline.

Execution order for remaining roadmap work: [MARATHON_PIPELINE.md](./MARATHON_PIPELINE.md). Production setup, backup, and diagnostics: [DEPLOYMENT.md](./DEPLOYMENT.md).

## Quick start (Docker)

1. Copy `.env.example` to `.env` (or another private env file), set secrets, and point Compose at it for non-demo use.
2. Build and run:
   - `docker compose up --build`
3. Backend:
   - `http://localhost:8000/health`
4. Web:
   - `http://localhost:3000`
5. Optional pre-flight: `PYTHONPATH=. python backend/scripts/check_deploy_env.py`
6. **Production:** follow [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md). Admin web must know the API URL: `REACT_APP_PHI_DPS_API_BASE` at build or `config.js` at deploy ([DEPLOYMENT.md](./DEPLOYMENT.md)).

## Rollout operations endpoints

- Runner cycle: `POST /rollout/automation/run-cycle`
- Alert list: `GET /rollout/alerts`
- Alert digest: `GET /rollout/alerts/digest`
- Retry failed notifications: `POST /rollout/notifications/retries/process`
- Webhook callback:
  - `POST /rollout/notifications/webhooks/{channel}`
  - headers:
    - `X-Event-Id`
    - `X-Signature` (hex HMAC-SHA256 over raw request body)

## Notes

- Internal scheduler is env-gated (`PHI_DPS_ROLLOUT_RUNNER_ENABLED=1`).
- Notification integrations are currently stubs with retry/dead-letter flow for rollout safety testing.
