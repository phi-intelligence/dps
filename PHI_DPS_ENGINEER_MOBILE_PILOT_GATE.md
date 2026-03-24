# PHI-DPS Engineer Mobile — pilot gate (final)

**Last validation run:** see **§1 Build**, **§2 Backend** below (update when re-run).

---

## 1. Build verification

### Commands to use

| Platform | Purpose | Command (from `mobile/`) |
|----------|---------|----------------------------|
| **Android (debug, fast)** | CI / local sanity | `flutter build apk --debug` |
| **Android (release pilot)** | TestFlight-like sideload / Play internal | `flutter build apk --release` or `flutter build appbundle` for Play Console |
| **iOS (no signing)** | Compile check only | `flutter build ios --no-codesign --debug` or `--release` |
| **iOS (device / TestFlight)** | Real pilot install | Open `ios/Runner.xcworkspace` in Xcode → set Team → **Product → Archive**, or `flutter build ipa` with signing |

### This environment (representative run)

| Target | Result | Notes |
|--------|--------|--------|
| **Android** | **Succeeded** | `flutter build apk --debug` produced `build/app/outputs/flutter-apk/app-debug.apk`. First Gradle attempt failed (transient Maven/cache `gradle-8.3.1` + `sha1-checksums.bin`); **automatic retry** succeeded and SDK Platform 35 installed. |
| **iOS** | **Partial** | **Pod install:** succeeds with **`use_modular_headers!`** in `Podfile` **and** `export LANG=en_US.UTF-8` (CocoaPods can fail with `ASCII-8BIT` otherwise). **`flutter build ios --no-codesign --debug`** in this env hit **codesign / resource fork (“detritus”)** on `Flutter.framework` (device build). **`flutter build ios --simulator`** may still hit toolchain/xattr issues on some machines — use **Xcode → Product → Build** with a valid **Team** for reliable pilot binaries. |
| **Web** | Not required for pilot | `flutter build web` optional; Chrome not in PATH on this machine is unrelated to mobile pilot. |

### Blockers to producing a pilot build

- **Android:** Occasional **Gradle / network / cache** issues — retry or `cd android && ./gradlew clean`, clear `.gradle` if corrupted; ensure Android SDK licenses.
- **iOS:** **Apple Developer** team + signing for device/App Store; **CocoaPods** must complete (`pod install`). Use Podfile fix above if `sqlite3` modular header error appears.

---

## 2. Backend integration validation

**Command:**

```bash
cd /path/to/phi-dps
python -m pytest backend/tests/test_wave7_engineer_mobile_hardening.py -v
```

**Recommended environment:** Python **3.11–3.14** with `backend/requirements.txt` installed in a venv. Set test DB via `conftest` (`PHI_DPS_DATABASE_URL` etc. as in `backend/tests/conftest.py`).

### This environment

| Result | Detail |
|--------|--------|
| **PASS** | **5 passed** in ~61s (`Python 3.14.2`, `backend/.venv`). Tests: punch idempotency replay, idempotency 409 conflict, accept replay, form dedup, media **413**. |

**If integration fails elsewhere:**  
- **Import error (`passlib`, etc.):** `pip install -r backend/requirements.txt` (ensure `passlib>=1.7.4`).  
- **PIL/reportlab bus error:** try **Python 3.12** in CI.  
- **SQLite file lock:** delete `backend/tests/test.db` and re-run.

---

## 3. Staging smoke checklist

Use **`PHI_DPS_ENGINEER_MOBILE_STAGING_SMOKE_RUN_SHEET.md`** (one-page table). Covers login, jobs, accept, punch, form, signature, media (&lt;2 MiB), parts, sync/offline, diagnostics, failure/conflict visibility.

---

## 4. Pilot gate verdict (strict)

| Verdict | Meaning |
|---------|---------|
| **blocked** | Cannot start pilot until listed items cleared. |
| **ready for internal pilot** | Tech + smoke acceptable for **org-only** trial. |
| **ready for limited field pilot** | Internal pilot done + ops ready + no P0s. |
| **broader rollout** | **Not** granted by this gate (see product/roadmap). |

**Current judgment (based on automated checks + this doc):**

- **Technical:** `flutter analyze` / `flutter test` / `test_wave7_unit.py` / **`test_wave7_engineer_mobile_hardening.py`** — **PASS** in this run. **Android debug APK** — **built**. **iOS** — **verify** after `pod install` with updated Podfile.
- **Staging/manual:** Run sheet **not executed** in automation — **must be done** before declaring internal pilot.

**Verdict:** **Ready for limited field pilot** *conditional on* (1) **staging smoke run sheet PASS**, (2) **iOS build verified** on a Mac with signing as needed, (3) **operational** roster/channel, (4) release-control rules from `PHI_DPS_ENGINEER_MOBILE_FINAL_RELEASE_CONTROL_PLAN.md` applied.  
**Broader rollout:** **blocked** until media scalability risk is closed by pilot evidence or full phase-2 media transport completion.

### Blockers separated

| Type | Items |
|------|--------|
| **Technical** | iOS: confirm `pod install` + build after Podfile change; Android release signing for production-like pilot optional for limited pilot. |
| **Environment** | Staging API URL + test accounts; device fleet. |
| **Operational** | Execute run sheet; pilot roster; dispatcher/support coverage; escalation path (`PHI_DPS_ENGINEER_MOBILE_FIELD_DIAGNOSTICS_PLAYBOOK.md`); P0/P1 triage ownership per release-control plan. |

---

## 5. Next actions to clear the gate

1. Run **`PHI_DPS_ENGINEER_MOBILE_STAGING_SMOKE_RUN_SHEET.md`** on staging; file failures with screenshots.
2. **iOS:** `cd mobile/ios && pod install && cd .. && flutter build ios --no-codesign` (or signed archive in Xcode).
3. **Android release (optional for internal):** `flutter build apk --release` with signing config as per team.
4. Ops: confirm channel + fallback procedure; mark limited pilot window and triage owner rota.

## 6. Media phase-2 pilot control

- Default pilot mode: **legacy media flow on** (`POST /jobs/{id}/media`).
- Optional controlled experiment: enable `engineer_media_phase2_enabled` for a small subset only after day-0 stability.
- Any phase-2 regression in pilot cohort: disable flag immediately and continue on legacy path.
