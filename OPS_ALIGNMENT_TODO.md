# M&E Operations Alignment TODO

Prioritized gap list to align PHI-DPS with real-world Mechanical & Electrical service operations.

## P0 - Field Execution (Engineer App)
- [x] Replace manual location updates with continuous GPS stream + movement threshold batching (Flutter: `Geolocator.getPositionStream`, throttled `POST /tracking/telemetry/engineer`).
- [ ] Add offline queue/retry for telemetry, punch, job forms, media, signatures, parts usage.
- [ ] Add engineer workflows for required completion evidence (forms/signatures/media/parts) before close.
- [x] Show telemetry health + last successful sync timestamp in mobile UI (status line on engineer home).

## P0 - Live Dispatch Map
- [x] Add in-app interactive map with real markers and auto-centering controls.
- [ ] Add follow-selected-engineer mode with freshness/aging visual states.
- [x] Reduce polling lag and/or add push updates for near-real-time dispatch decisions (10s poll; push still TODO).

## P1 - Lead -> Quote -> Job Orchestration
- [ ] Add explicit workflow state model (triage -> survey -> quote -> accept -> dispatch).
- [ ] Add quote chase and stale lead automation (timers, reminders, escalation).
- [ ] Add dispatch-ready checks from accepted quotes (parts readiness, compliance prerequisites).
- [x] Web UI: leads require contact (email or phone) + issue description; jobs require **accepted** quote (see `web/src/App.tsx` validation).

## P1 - SLA/PPM Realism
- [ ] Implement business-calendar-aware SLA clocks (working hours, pauses, customer exceptions).
- [ ] Add PPM capacity-aware scheduling and route-friendly clustering.
- [ ] Add SLA breach prediction alerts with actionable recommendations.

## P1 - Compliance Hardening
- [ ] Enforce job-type compliance packs and template/version governance.
- [ ] Add competence gate checks at assignment time (expiry + role fit).
- [ ] Add certificate expiry lifecycle reminders and re-issue workflow.

## P2 - Inventory/Procurement Field Depth
- [ ] Add substitute part rules and van replenishment suggestions.
- [ ] Add serial/lot traceability for regulated equipment flows.
- [ ] Add barcode-first receiving/picking UX.

## P2 - Commercial & Finance Control
- [ ] Expand approvals for invoice exceptions, SLA waivers, and high-value PO controls.
- [ ] Add credit note/refund workflow parity (or integrated external finance sync).
- [ ] Add profitability leakage diagnostics per contract/job.

## P3 - Operational Intelligence
- [ ] Add repeat-fault detection and root-cause workflow triggers.
- [ ] Add dispatcher control-tower KPIs with recommended next actions.
- [ ] Add role-based daily operational runbooks in UI.

