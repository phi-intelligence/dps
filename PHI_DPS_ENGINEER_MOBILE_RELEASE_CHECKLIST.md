# PHI-DPS Engineer Mobile — release checklist (Wave 7+)

Use before **internal pilot**, **limited field pilot**, or production cut.

**Staging smoke (manual):** `PHI_DPS_ENGINEER_MOBILE_STAGING_SMOKE_RUN_SHEET.md`  
**Pilot gate status / build notes:** `PHI_DPS_ENGINEER_MOBILE_PILOT_GATE.md`

## Build & quality gates

- [ ] **Mobile:** `flutter analyze` clean (or known exceptions documented).
- [ ] **Mobile:** unit/widget tests per project convention (`flutter test`).
- [ ] **Backend:** `pytest` green including `backend/tests/test_wave7_engineer_mobile_hardening.py`.
- [ ] **Backend (fast, no full app import):** `python -m pytest backend/tests/test_wave7_unit.py -v` — run in CI when integration tests cannot load the full stack (e.g. native/PDF deps).
- [ ] **Config:** API base URL, env, and build flavors correct for target environment.
- [ ] **Version:** app version / build number bumped and traceable in diagnostics.
- [ ] **Release-control:** pilot candidate branch/tag frozen; only P0/P1 fixes allowed during pilot window.

### CI / local commands (copy-paste)

From repository root (adjust Python path to `backend/.venv` if used):

```bash
cd mobile && flutter analyze && flutter test
```

```bash
python -m pytest backend/tests/test_wave7_unit.py -v
```

```bash
# Prefer Python 3.11 or 3.12 for full API import chain (Pillow/reportlab).
python -m pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v
```

```bash
cd mobile && flutter build apk   # or: flutter build ios
```

## Auth & session

- [ ] Login succeeds against target API; token refresh / expiry behavior understood.
- [ ] Logout clears local tokens and does not leave stale sync state ambiguous.
- [ ] Invalid/expired token shows actionable message (re-login), not silent failure loops.

## Sync & offline

- [ ] Airplane mode: writes queue where policy allows; blocked actions show clear reason (e.g. media).
- [ ] Reconnect: outbox drains; **no duplicate** punch/accept/forms when `Idempotency-Key` replayed (server returns same result or 409 on key misuse).
- [ ] Sync banner / diagnostics reflect pending vs failed vs conflict counts.

## Core field flows

- [ ] Job list & detail load for engineer role.
- [ ] Accept job: success, **403** other engineer, **400** terminal job.
- [ ] Punch in/out within geofence; geofence failure message clear.
- [ ] Forms / signature / parts submit; media within **2 MiB** JSON limit.
- [ ] Media phase-2 capability endpoint check does not break legacy flow (`GET /jobs/media/capabilities`).
- [ ] If phase-2 flag enabled for test cohort: upload session create + commit succeeds for pilot scenarios.

## Observability

- [ ] API errors logged or surfaced in diagnostics (status code, correlation if any).
- [ ] Support knows how to collect **app diagnostics** screen snapshot / export if available.

## Rollback

- [ ] Previous build remains installable or rollback path documented.
- [ ] Backend migrations (if any) backward-compatible for pilot window.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Product / Ops | | |

## Pilot change-control (must acknowledge)

- [ ] P0/P1 triage owner on duty each pilot day.
- [ ] P0 = rollout hold + hotfix; P1 = same-day mitigation/fix plan.
- [ ] P2/P3 deferred unless zero-risk to pilot stability.
