# PHI-DPS Engineer Mobile — Backend/Frontend Parity Pipeline

## Goal

Close remaining gaps between implemented backend engineer-safe capabilities and mobile/frontend behavior, with emphasis on pilot reliability and UX consistency.

## Phase 1 — Critical correctness and messaging alignment (start now)

1. Fix activity timeline backend field mapping mismatches that can break typed events.
2. Update stale mobile messaging that still says engineer notes are unsupported.
3. Refresh capability matrix to reflect current implemented state.

Definition of done:

- activity endpoint returns typed events without model-field runtime errors
- mobile messages match actual backend capabilities
- parity docs no longer claim notes are blocked

Status: **Completed**

## Phase 2 — Engineer-scope endpoint coverage audit

1. Verify each engineer-safe backend endpoint has mobile usage or intentional defer reason.
2. Flag non-mobile backend endpoints as out-of-scope (admin/dispatch only).
3. Produce a parity checklist for release-control reviews.

Definition of done:

- explicit mapping table: endpoint -> mobile screen/repo -> status
- list of intentional gaps with owner and rationale

Status: **In progress** (parity table created in `PHI_DPS_ENGINEER_MOBILE_ENDPOINT_PARITY_TABLE.md`)

## Phase 3 — Pilot UI/UX polish pass

1. Harmonize error/remediation language across action points and diagnostics.
2. Reduce stale helper text and duplicate guidance.
3. Validate critical user journeys under weak network with manual scripts.

Definition of done:

- no contradictory UX guidance in core flows
- support/playbook language aligned with app surfaces

## Phase 4 — Pilot hardening validation

1. Run `flutter analyze` and `flutter test`.
2. Run backend engineer hardening tests in CI-supported Python environment.
3. Record pass/fail and residual risks.

Definition of done:

- mobile checks green
- backend hardening checks green in target CI/runtime
- unresolved issues explicitly documented for release-control decision
