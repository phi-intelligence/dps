# PHI-DPS API vs UI Gap Report

**Generated:** March 22, 2025  
**Scope:** Backend API routes vs web frontend (web/src) usage

---

## Executive Summary

The phi-dps backend exposes **30+ route modules** with hundreds of endpoints. The frontend uses roughly **70–80 distinct API paths** across 7 main components. Large portions of the backend—assets, sites, inventory, analytics, SLA, PPM, approvals, competence, integrations, automation/tasks, and many contract workflows—are not surfaced in the UI.

---

## 1. Backend APIs with NO Frontend Usage

These routes are defined in the backend but not called from `web/src`.

### Auth
| Method | Path | Notes |
|--------|------|-------|
| GET | `/auth/me` | Current user profile not displayed |
| POST | `/auth/dev/bootstrap` | Dev-only; no UI trigger |

### Admin (permissions catalog & AI status)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/admin/permissions/catalog` | Permission catalog not exposed |
| GET | `/admin/permissions/users/{user_id}` | Per-user grants not used |
| POST | `/admin/permissions/users/{user_id}/grants` | Grant creation not in UI |
| PATCH | `/admin/permissions/grants/{grant_id}` | Grant update not in UI |
| DELETE | `/admin/permissions/grants/{grant_id}` | Grant deletion not in UI |
| GET | `/admin/ai/status` | AI provider status not shown |

### Customers / Communication Preferences
| Method | Path | Notes |
|--------|------|-------|
| GET | `/customers/{id}/communication-preferences` | All CRUD for comm prefs |
| POST | `/customers/{id}/communication-preferences` | |
| PATCH | `/customers/{id}/communication-preferences/{pref_id}` | |
| GET | `/customers/{id}/communication-safety` | Safety settings not surfaced |

### Quoting
| Method | Path | Notes |
|--------|------|-------|
| GET | `/quotes/{quote_id}` | Quote detail view missing |

### Jobs / Dispatch
| Method | Path | Notes |
|--------|------|-------|
| GET | `/jobs/{id}/costing` | Job costing not displayed |
| GET | `/jobs/{id}/labour-costing` | Labour costing not displayed |
| POST | `/jobs/{id}/assign` | Manual assign not in UI |
| POST | `/jobs/{id}/accept` | Accept job (field) not in UI |
| POST | `/jobs/{id}/status` | Status updates not in UI |
| POST | `/jobs/{id}/forms/{form_key}/submit` | Form submissions |
| POST | `/jobs/{id}/completion/signature/require` | Completion workflows |
| POST | `/jobs/{id}/completion/media/require` | |
| POST | `/jobs/{id}/signature` | |
| POST | `/jobs/{id}/media` | |
| POST | `/jobs/{id}/parts-usage` | |
| POST | `/jobs/{id}/parts-reconciliation/approve` | |
| POST | `/jobs/{id}/follow-on/from-defects` | Follow-on job creation |
| POST | `/jobs/{id}/equipment-assign` | Equipment assign |
| (etc.) | Various job lifecycle routes | Many job workflow endpoints |

### Dispatch
| Method | Path | Notes |
|--------|------|-------|
| GET | `/dispatch/jobs/{id}/eta` | ETA display not in UI |
| GET | `/dispatch/jobs/{id}/timeline` | Timeline not in UI |
| POST | `/dispatch/jobs/{id}/customer-notify/on-my-way` | On-my-way notification |
| PATCH | `/dispatch/jobs/{id}/manual-eta` | Manual ETA override |
| GET | `/dispatch/jobs/{id}/recommendations` | Recommendations not used |
| POST | `/dispatch/jobs/{id}/assign-best` | Assign best engineer |
| GET | `/dispatch/engineers/availability` | Engineer availability |
| POST | `/dispatch/vehicle-bindings` | Vehicle bindings |

### Tracking
| Method | Path | Notes |
|--------|------|-------|
| POST | `/tracking/telemetry` | Telemetry submission (mobile/app) |
| POST | `/tracking/telemetry/engineer` | |
| POST | `/tracking/telemetry/vehicle` | |

### Time
| Method | Path | Notes |
|--------|------|-------|
| POST | `/time/timesheets/approve` | Timesheet approval workflow |
| POST | `/time/payroll/export` | Payroll export |

### Invoicing
| Method | Path | Notes |
|--------|------|-------|
| POST | `/invoicing/invoices/{id}/hold` | Hold invoice |
| POST | `/invoicing/invoices/{id}/release-hold` | Release hold |
| POST | `/invoicing/invoices/{id}/finance-review` | Finance review workflow |
| POST | `/invoicing/invoices/{id}/clear-finance-review` | Clear finance review |

### Entire modules (no UI at all)
| Module | Description |
|--------|-------------|
| **Assets** | CRUD, schedules, maintenance, history |
| **Competence** | Qualifications CRUD |
| **Inventory** | Items, locations, reservations, transfers, purchase orders |
| **Analytics** | ETL, dashboard, margin, variance |
| **Integrations** | Gas Safe lookup |
| **Sites** | CRUD, assets, history, jobs |
| **SLA** | Policies CRUD |
| **PPM** | Schedules CRUD, run-generation |
| **Ops** | Recommendations, suppressions, dashboard |
| **Approvals** | Dashboard, list, approve, reject |
| **Vehicles** | Dashboard, inspections, defects |
| **Automation** | Runs, dashboard, run-for-recommendation |
| **Tasks** | Dashboard follow-up/commercial/finance, list, get, patch, complete |

### Labour (partial)
| Method | Path | Notes |
|--------|------|-------|
| POST | `/labour/calendars/{id}/days` | Calendar days not managed in UI |
| GET | `/labour/calendars/{id}/days` | |
| POST | `/labour/rule-sets` | Rule sets not used |
| GET | `/labour/rule-sets` | |
| GET | `/labour/rule-sets/{id}` | |
| PATCH | `/labour/rule-sets/{id}` | |

### Equipment (partial)
| Method | Path | Notes |
|--------|------|-------|
| Most equipment routes | Dashboard, CRUD, movements, calibration, inspection, assign, move | Only `/equipment/vehicles/{id}/readiness-summary` used in FieldJobConsole |

### Contracts (large subset)
| Description | Notes |
|-------------|-------|
| Contract CRUD, amendments workflow, repricing internal review, activation confirmations internal release, communications send/approve, reviews, version CRUD | CommercialHub uses dashboards and readable-change only; full workflow not wired |

### System (partial)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/system/jobs` | Recurring system jobs list |
| GET | `/system/jobs/{id}` | |
| PATCH | `/system/jobs/{id}` | |
| POST | `/system/jobs/{id}/run` | |
| POST | `/system/jobs/run-due` | |
| GET | `/system/job-runs` | |
| GET | `/system/job-runs/{id}` | |
| POST | `/system/job-runs/{id}/retry` | |
| GET | `/system/communication-template-registry` | |
| GET | `/system/dashboard/jobs` | |

---

## 2. Backend APIs with Minimal or Weak Frontend Usage

| Route | Where used | Issue |
|-------|------------|-------|
| `GET /quotes` | App.tsx, LabourAiToolsHub | List only; no quote detail, no accept flow surfaced clearly |
| `POST /quotes/{id}/accept` | App.tsx | Exists but UX is buried in main tab |
| `GET /crm/leads` | App.tsx, LabourAiToolsHub | Labour hub uses for AI context only; no lead workflow UI |
| `GET /jobs` | App.tsx | Simple list; FieldJobConsole expects manual job ID input (no job picker) |
| `GET /rollout/waves` | App.tsx | Basic list; wave start/complete and automation flow not wired |
| `POST /rollout/automation/run-cycle` | App.tsx | Single button; no structured UI for cycle results |
| `GET /dispatch/live-map` | LiveDispatchMap | Map present; unclear if full UI is finished |
| `GET /time/timesheets` | App.tsx | Date input only; no timesheet approval or payroll export |
| `POST /time/punch/in`, `/out` | App.tsx | No offline queue, no clear punch validation feedback |
| `GET /compliance/certificates` | App.tsx | List only; no certificate detail or download |
| `GET /invoicing/invoices` | App.tsx | List only; hold/release/finance-review not exposed |
| `GET /contracts/{id}/versions/{vid}/readable-change` | CommercialHub | Used for version diff; contract selection UX is limited |
| `GET /portal/me/*` | ClientPortalHub | Portal uses many routes; some panels may be incomplete |
| `GET /admin/access-groups` etc. | OrgAccessHub | Org access UI exists; permission catalog and per-user grants not used |
| `GET /equipment/vehicles/{id}/readiness-summary` | FieldJobConsole | Only equipment route used; no broader equipment management |

---

## 3. UX Gaps in Existing Screens

### 3.1 Validation and feedback
| Component | Issue |
|-----------|-------|
| Lead form | No email/phone validation; error only in `setAppError` |
| Quote form | No numeric range checks on quantity/price; single "Add at least one quote item" check |
| Job form | No address validation; empty `scheduled_at` allowed |
| Geofence form | Latitude/longitude not validated; defaults may be incorrect |
| Convert lead form | No required-field or email format validation |
| Timesheet date | No date format validation |
| FieldJobConsole job ID | Free text; no validation or autocomplete from job list |

### 3.2 Error handling
| Issue | Details |
|-------|---------|
| Generic error display | Many components use `setAppError`/`setAuthError`; raw error strings shown |
| No error boundaries | No global or per-tab error boundary |
| Inconsistent FetchState | CommercialHub uses per-section errors; other tabs less consistent |
| No retry | Failed fetches have no retry option |
| 401 handling | Logout on 401 not always surfaced clearly |

### 3.3 Layout and navigation
| Issue | Details |
|-------|---------|
| Crowded top bar | 14+ tabs in single bar; can feel overwhelming |
| No breadcrumbs | No deep linking or breadcrumb navigation |
| FieldJobConsole | Job dropdown from `jobs` prop unclear; rendered in "Field" tab |
| CommercialHub | 19 nav anchors; long scroll and heavy cognitive load |

### 3.4 Missing or weak UX
| Issue | Details |
|-------|---------|
| Loading states | Mostly "Loading..." text; no skeletons |
| Success confirmations | No clear feedback (e.g., "Lead converted", "Quote accepted") |
| Certificate/invoice generation | "Working..." only; no clear completion feedback |
| Punch in/out | No visual confirmation; distance validation message can be buried |
| LabourAiToolsHub | AI output shown; no "copy" or "apply" actions |
| Pagination | Leads, quotes, jobs, customers have no pagination for large lists |

### 3.5 Accessibility and consistency
| Issue | Details |
|-------|---------|
| Labels | Some `<label>` elements may not be wired to inputs |
| Status pills | Ad-hoc color logic; no shared design system |
| ARIA | Inconsistent `aria-label` and ARIA attributes |

### 3.6 Security / UX
| Issue | Details |
|-------|---------|
| Dev credentials | Pre-filled `admin@example.com`, `admin`; should be disabled/flagged in production |
| OrgAccessHub | Raw permission keys; could use clearer labels (backend labels exist) |

### 3.7 Performance
| Issue | Details |
|-------|---------|
| Request cancellation | No cancellation on tab change |
| CommercialHub | Loads many dashboards at once; could be split or lazy-loaded |

---

## 4. Suggested Priority Order for Surfacing Backend Features

### P0 – Critical for core workflows
1. **Quote detail + accept flow** – `GET /quotes/{id}`, `POST /quotes/{id}/accept` already called; add dedicated quote detail view and clear accept UX.
2. **Job picker for FieldJobConsole** – Use `GET /jobs` to populate job selector instead of free-text ID.
3. **Timesheet approval** – `POST /time/timesheets/approve` for supervisor workflow.
4. **Success feedback** – Add confirmations for lead convert, quote accept, punch in/out, certificate/invoice generation.

### P1 – High value, moderate effort
5. **Invoicing hold/release** – `POST /invoicing/invoices/{id}/hold`, `release-hold` for finance workflow.
6. **Finance review workflow** – `POST /invoicing/invoices/{id}/finance-review`, `clear-finance-review`.
7. **Current user display** – `GET /auth/me` to show logged-in user in header.
8. **Communication preferences** – UI for `GET/POST/PATCH /customers/{id}/communication-preferences`.
9. **Certificate detail + download** – Extend compliance tab with certificate view and download.

### P2 – Operational efficiency
10. **Job costing / labour costing** – `GET /jobs/{id}/costing`, `labour-costing` for field/ops visibility.
11. **Dispatch ETA / timeline** – `GET /dispatch/jobs/{id}/eta`, `timeline` for live dispatch view.
12. **On-my-way notification** – `POST /dispatch/jobs/{id}/customer-notify/on-my-way` for customer comms.
13. **Assign best engineer** – `POST /dispatch/jobs/{id}/assign-best` for dispatcher UI.
14. **Engineer availability** – `GET /dispatch/engineers/availability` for scheduling.
15. **Payroll export** – `POST /time/payroll/export` for finance.

### P3 – Admin and internal tools
16. **Permission catalog** – `GET /admin/permissions/catalog` in OrgAccessHub.
17. **Per-user grants** – `GET/POST/PATCH/DELETE /admin/permissions/users/{id}...` for fine-grained access.
18. **AI provider status** – `GET /admin/ai/status` for ops visibility.
19. **System jobs + runs** – `/system/jobs`, `/system/job-runs` for recurring job management.
20. **Automation runs** – Automation dashboard for `run-for-recommendation`, `run-for-proposal`.

### P4 – New modules (larger scope)
21. **Sites** – Site CRUD and linkage to jobs/assets.
22. **Assets** – Asset management and maintenance.
23. **Inventory** – Items, locations, reservations, transfers.
24. **SLA policies** – SLA configuration.
25. **PPM schedules** – Planned preventative maintenance.
26. **Approvals** – Approval dashboard and workflow.
27. **Vehicles** – Inspections, defects.
28. **Competence** – Qualifications management.
29. **Analytics** – Margin, variance dashboards.
30. **Ops** – Recommendations, suppressions.

---

## Appendix: Frontend components and their API usage

| Component | Location | APIs used |
|-----------|----------|-----------|
| App.tsx | web/src/App.tsx | auth/token, crm/customers, crm/leads, crm/leads/convert, quotes, quotes/accept, jobs, tracking/geofences, time/punch, time/timesheets, compliance/certificates, invoicing/invoices, invoicing/invoices/generate, invoicing/invoices/pay, rollout/* |
| LiveDispatchMap | web/src/phase4/LiveDispatchMap.tsx | dispatch/live-map |
| FieldJobConsole | web/src/phase4/FieldJobConsole.tsx | jobs/{id}, jobs/{id}/sla, jobs/{id}/equipment-readiness, jobs/{id}/equipment-requirements, jobs/{id}/completion-requirements, equipment/vehicles/{id}/readiness-summary |
| LabourAiToolsHub | web/src/phase4/LabourAiToolsHub.tsx | labour/calendars, labour/calendars/{id}, labour/calendars/{id}/import-feed, quotes, crm/leads, ai/drafting/assist |
| CommercialHub | web/src/phase4/CommercialHub.tsx | contracts/dashboard/*, system/dashboard/*, invoicing/dashboard/*, documents, documents/{id}/download |
| OrgAccessHub | web/src/phase4/OrgAccessHub.tsx | admin/access-groups, admin/customers/{id}/access-groups, admin/customer-access-groups, crm/customers |
| ClientPortalHub | web/src/phase4/ClientPortalHub.tsx | portal/me/dashboard, portal/me/documents, portal/me/communications, portal/me/contracts, portal/me/repricing-proposals, portal/me/activation-confirmations, portal/me/invoices |
