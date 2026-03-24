# PHI-DPS Engineer Mobile — Final Validation & Pilot Plan

**Purpose:** Practical release-readiness and validation for the **current** Waves 1–7 implementation (not a feature roadmap).

**Related docs:** `PHI_DPS_ENGINEER_MOBILE_CAPABILITY_MATRIX.md`, `PHI_DPS_MOBILE_BACKEND_HARDENING_REQUIRED.md`, `PHI_DPS_ENGINEER_MOBILE_MEDIA_UPLOAD_DECISION.md`, `PHI_DPS_ENGINEER_MOBILE_REPLAY_CONFLICT_TEST_PACK.md`, `PHI_DPS_ENGINEER_MOBILE_RELEASE_CHECKLIST.md`, `PHI_DPS_ENGINEER_MOBILE_UAT_SCENARIOS.md`, `PHI_DPS_ENGINEER_MOBILE_FIELD_DIAGNOSTICS_PLAYBOOK.md`

---

## 1. Executive summary

The **Flutter engineer mobile app** (Waves 1–7) implements auth/session, jobs list/detail, accept job, punch in/out (with geofence dependency on backend configuration), telemetry (best-effort), completion readiness, evidence flows (forms, signature, media, parts), an **outbox + sync engine**, and diagnostics/settings. The **backend** enforces punch sequence rules, stores **successful** responses keyed by **`Idempotency-Key`** on core engineer write paths, adds **replay guards** for accept/forms/signature/parts, and rejects oversized **media JSON** payloads with **413** (2 MiB cap).

**Evidence-based recommendation:** The codebase is **suitable for an internal pilot** once the **automated checks in §3** pass in a **standard environment** (see **§10 Validation execution log** for a recent local run: Flutter clean; backend integration tests may require **Python 3.11–3.12** and a healthy **Pillow/reportlab** stack—**Python 3.14** showed toolchain fragility). **Limited field pilot** is **conditionally** appropriate: enforce **media limits**, **ops support**, and **manual UAT** from §4–§5. **Broader rollout** is **not** recommended until **large-object upload**, **engineer notes**, and **SKU discovery** gaps are addressed or explicitly accepted by the business.

**Recommended release level (current judgment):** **Internal pilot ready** (pending green CI); **limited field pilot ready** only after internal pilot + operational guardrails; **broader rollout: not ready**.

---

## 2. What must be verified in code right now

| Check | What to run | Expected result | If it fails | Severity |
|-------|-------------|-----------------|-------------|----------|
| Flutter build health | `cd mobile && flutter pub get && flutter build apk` (or `ios`/`web` per target) | Build completes | Cannot ship a binary | **P0** |
| `flutter analyze` | `cd mobile && flutter analyze` | `No issues found!` | Type/lint issues may hide runtime bugs | **P0** |
| `flutter test` | `cd mobile && flutter test` | All tests pass | Regressions in auth/error/readiness UI | **P0** |
| Backend Wave 7 integration tests | `python -m pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v` | All pass | Idempotency / guards / media cap broken | **P0** |
| Backend Wave 7 **light** unit tests (no full app import) | `python -m pytest backend/tests/test_wave7_unit.py -v` | All pass | Hash/dedup logic regression | **P1** (non-blocking if integration passes) |
| Related E2E smoke | `python -m pytest backend/tests/test_phase4_e2e.py::test_end_to_end_flow_and_gdpr_delete -v` | Pass | Core API regression | **P1** |
| Engineer write **contract** spot-check | Compare mobile Dio/base URLs + paths to `backend` routers: `/auth/token`, `GET /jobs`, `POST /jobs/{id}/accept`, `POST /time/punch/in|out`, tracking telemetry, `POST /jobs/{id}/forms/.../submit`, `/signature`, `/media`, `/parts-usage`; headers `Authorization`, `Idempotency-Key` | Aligned with implemented routes | Wrong path/header → 404/401 in pilot | **P0** |
| Sync/outbox | Code review + manual tests (§4): pending queue, retry, completion | No silent data loss; user-visible state | Pilot-blocking UX/support load | **P0** |
| Replay/idempotency | Automated + manual (replay pack): same key → same success; different body → **409** | Matches Wave 7 design | Duplicate payroll/evidence risk | **P0** |
| Media 2 MiB limit | API: body > cap → **413**; client respects guard | Consistent | Engineers blocked or oversized payloads | **P0** |
| Duplicate punch guard | `punch_in` when already “in”; `punch_out` without “in” | **400** with clear message | Duplicate labour rows | **P0** |
| Accept-job replay | Accept twice / sync retry | **200** stable; terminal job **400** | Wrong job state in office | **P0** |

---

## 3. Automated validation plan

| Command / scope | Purpose | Pass criteria | Blocking? |
|-----------------|---------|---------------|-----------|
| `cd mobile && flutter analyze` | Static analysis for Dart | No issues | **Blocking** for release |
| `cd mobile && flutter test` | Unit/widget tests | All pass | **Blocking** |
| `cd mobile && flutter build <target>` | Proves toolchain produces artifact | Success | **Blocking** before device install |
| `pytest backend/tests/test_wave7_unit.py -v` | Hash + replay guard invariants without importing full app | All pass | **Non-blocking** if integration tests pass; **Blocking** if integration cannot run in CI |
| `pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v` | Idempotency, accept, form dedup, media 413 | All pass | **Blocking** for backend contract sign-off |
| `pytest backend/tests/test_phase4_e2e.py::test_end_to_end_flow_and_gdpr_delete -v` | Smoke: job, geofence, punch | Pass | **Non-blocking** but recommended |
| *(Optional)* `pytest backend/tests/ -v` — exclude slow suites | Full regression | Per project policy | **Blocking** only if policy says so |

**Missing tests before pilot (recommended, not redesign):**

- Integration tests are the main gap if the environment cannot import `backend.app.main` (native deps). Keep **`test_wave7_unit.py`** in CI as a **fast** sanity check; run **`test_wave7_engineer_mobile_hardening.py`** on **Python 3.11/3.12** in CI.
- Optional: one **client** test asserting `Idempotency-Key` is sent on outbox replay paths (if not already covered).

---

## 4. Manual verification plan

### Login / session
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| L1 | Valid pilot API URL | Login with engineer user | Jobs load; token stored | Screenshot + diagnostics |
| L2 | — | Logout | Local session cleared; login screen | Logs |

### Jobs list / detail
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| J1 | Logged in | Open list → open detail | Data matches API | Response body if API issue |

### Accept job
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| A1 | Assigned job | Accept | Status accepted / workflow advances | Job id, time |
| A2 | Job completed | Accept | Error path clear | 400 message |

### Punch in / out
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| P1 | Geofence exists, inside | Punch in | Success | GPS + fence config |
| P2 | After P1 | Punch out | Success | — |
| P3 | Already “in” | Punch in again | Validation error | — |

### Telemetry
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| T1 | Online | Move / trigger telemetry | Best-effort; no outbox spam | — |

### Completion readiness
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| C1 | Job with requirements | View readiness | Matches bundle + pending | API `/jobs/{id}/completion-requirements` if exists |

### Forms / signature / media / parts
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| E1 | Requirements set | Submit form | 200; readiness updates | missing_required_keys |
| E2 | — | Submit signature | 200 | — |
| E3 | Photos under cap | Submit media | 200 | — |
| E4 | Parts lines | Submit parts | 200 / reconciliation visible | SKU errors |

### Sync / outbox
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| S1 | Queued items | Open diagnostics | Counts accurate | DB export if possible |
| S2 | — | Trigger sync | Drains or shows error | — |

### Retry / conflict
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| R1 | — | Induce 409 (test harness) | User can recover | Message |

### Diagnostics / settings
| # | Preconditions | Steps | Expected | Capture on failure |
|---|----------------|-------|----------|-------------------|
| D1 | — | Open diagnostics | Version, API base, sync state | — |

---

## 5. Weak-network and offline validation plan

| Scenario | How to simulate | Expected app behavior | Expected backend behavior | Severity if wrong |
|----------|-----------------|------------------------|----------------------------|-------------------|
| Submit while offline | Airplane mode | Queue where policy allows; media blocked if applicable | No duplicate **successful** writes without sync | **High** |
| Submit while reconnecting | Toggle Wi‑Fi during submit | Retry or queue; no corrupt state | Idempotent replay returns same result | **High** |
| App killed with pending outbox | Kill app with pending items | On relaunch, items still pending and syncable | On sync, same `Idempotency-Key` → same outcome | **High** |
| Duplicate replay after reconnect | Same outbox op flushed twice | Single effect | Cached idempotency response | **Critical** |
| Failed then retried | Block server then allow | User retries; eventual success | Same key, no duplicate rows | **High** |
| Conflict (409) | Same key, edited body (harness) | Visible error; no infinite loop | **409** | **Medium** |
| Media size rejection | Payload > 2 MiB JSON | Client blocks or server **413** | **413** with message | **High** |
| Telemetry offline | Airplane mode | No crash; best-effort drop/queue per design | No durable duplicate telemetry expectation | **Low** |
| Accept job flaky network | Throttle proxy | Single completion or clear pending | Accept idempotent / replay-safe | **High** |
| Punch in twice / invalid punch out | Double punch in; out without in | Clear **400** messages | Sequence rules enforced | **Critical** |

---

## 6. Pilot readiness risk register

| Risk | Impact | Likelihood | Mitigation | OK internal pilot? | OK limited field? | OK broader rollout? |
|------|--------|------------|------------|----------------------|-------------------|---------------------|
| JSON/base64 media, 2 MiB cap | Cannot complete evidence on large photos | Med | Compress; split submits; Phase 2 presigned | **Yes** (with training) | **Yes** (with monitoring) | **No** without new contract |
| Concurrent first-send idempotency race | Rare duplicate effect | Low | Document; monitor duplicates | **Yes** | **Conditional** | **No** without transactional claim |
| No engineer notes API | Notes in UI unsupported | Med | Voice to dispatch / paper | **Yes** | **Yes** | **No** if product requires notes |
| No engineer SKU search | Wrong / failed parts lines | Med | Dispatcher pre-enters; cheat sheet | **Yes** | **Conditional** | **No** |
| No engineer certificate visibility | Field confusion | Med | Office sends certs | **Yes** | **Conditional** | **No** |
| Test env / Python toolchain (e.g. 3.14 + PIL) | CI false negatives or crashes | Med (env-specific) | CI on **3.11/3.12**; `test_wave7_unit.py` fast path | **Yes** | **Yes** | **Yes** once CI stable |
| Workflow gaps outside engineer accept | Ambiguous transitions on edge jobs | Low | Dispatch playbook | **Yes** | **Yes** | **Conditional** |

---

## 7. Pilot scope recommendation

**User group:** **Internal** — engineers + one **dispatcher shadow**; then **limited field** — 2–4 trusted engineers on known routes.

**Job types:** **Include:** reactive domestic heating/boiler jobs already using **quotes + dispatch** in PHI-DPS. **Exclude** (initially): multi-day commercial, jobs without geofence if punch is mandatory, jobs requiring **heavy photo packs** beyond 2 MiB per request.

**Evidence / media:** **Cap photos per submit** (e.g. 1–3); **compress** in app; **no offline media queue** per current policy—engineers must complete media online or escalate.

**Operational support:** **Daily** 15‑min check: pilot Slack/email, **413** rate, **409** rate, failed outbox count. **Dispatcher** available during field hours. **Escalation:** `PHI_DPS_ENGINEER_MOBILE_FIELD_DIAGNOSTICS_PLAYBOOK.md`.

**Logs / diagnostics:** App version, API base URL, outbox pending/failed counts, last HTTP status from sync—**daily screenshot** from pilot leads optional.

**Fallback when app fails:** **Phone dispatcher** with job number; **paper timesheet** backup for labour; **do not double-submit** after office confirms server state.

---

## 8. Go / no-go checklist

### Internal pilot — must pass

**Technical**
- [ ] `flutter analyze` clean
- [ ] `flutter test` pass
- [ ] `pytest backend/tests/test_wave7_unit.py` pass
- [ ] `pytest backend/tests/test_wave7_engineer_mobile_hardening.py` pass on **CI Python version**
- [ ] Pilot build installed on device

**Operational**
- [ ] Pilot roster + communication channel
- [ ] Dispatcher coverage during pilot windows

**Product**
- [ ] Known gaps (notes, SKU search, certs) **acknowledged in writing**

### Limited field pilot — must pass (additionally)

**Technical**
- [ ] Internal pilot **complete** with no **P0** defects open
- [ ] Media/evidence path validated on real devices/networks

**Operational**
- [ ] Daily monitoring cadence + escalation path
- [ ] Fallback procedure communicated

**Product**
- [ ] Job-type scope agreed; exclusions documented

### Broader rollout — must pass (additionally)

**Technical**
- [ ] Media strategy (presigned/multipart or proven 2 MiB sufficiency)
- [ ] Engineer notes + SKU discovery **or** waived by product with mitigations

**Operational**
- [ ] Support runbooks + training

**Product**
- [ ] Formal sign-off on risk register

---

## 9. Final recommendation

**Immediately:** Run **§3** commands on **CI-standard Python**; fix any **P0** failures; complete **§4–§5** manual scripts on staging; record results.

**After internal pilot:** Triage failures; adjust media/process; consider **limited field** only if **P0** clear.

**Before broader production:** Address **large media**, **notes**, **SKU discovery**, and **idempotency race** mitigation **or** obtain explicit business acceptance of residual risk.

---

## 10. Validation execution log (companion)

*Last updated: validation pass run in development environment.*

| Step | Command | Result |
|------|---------|--------|
| Flutter analyze | `cd mobile && flutter analyze` | **PASS** — `No issues found!` |
| Flutter test | `cd mobile && flutter test` | **PASS** — 10 tests passed |
| Backend Wave 7 (light) | `pytest backend/tests/test_wave7_unit.py -v` | **PASS** — 3 passed |
| Backend Wave 7 (integration) | `pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v` | **Not completed** in this env — first failure: incomplete `passlib` install (`passlib.utils.decor`); after `pip install 'passlib>=1.7.4'`, import proceeded then **bus error** during full app import (**Pillow/reportlab** chain under **Python 3.14**). **Recommendation:** run integration tests on **Python 3.11 or 3.12** in CI. |
| Backend E2E smoke | `pytest backend/tests/test_phase4_e2e.py::test_end_to_end_flow_and_gdpr_delete` | **Not completed** (same full-app import issue) |

**Repo change from validation:** `passlib>=1.7.4` pinned in `backend/requirements.txt`; added `backend/tests/test_wave7_unit.py` for CI-friendly checks.

---

## 11. Pilot execution quick reference (documentation)

**Automated gates (before any pilot build):** use the **“CI / local commands (copy-paste)”** block in `PHI_DPS_ENGINEER_MOBILE_RELEASE_CHECKLIST.md` — same commands as §3 above.

**Manual field validation:** follow `PHI_DPS_ENGINEER_MOBILE_UAT_SCENARIOS.md` and weak-network cases in **§5** of this document.

**When something goes wrong:** `PHI_DPS_ENGINEER_MOBILE_FIELD_DIAGNOSTICS_PLAYBOOK.md` (retry vs escalate, 409/413, geofence).

**Python for backend integration tests:** use **3.11 or 3.12** in CI if **3.14** (or similar) crashes during `Pillow`/PDF import — the **light** suite `test_wave7_unit.py` still runs without importing `main`.
