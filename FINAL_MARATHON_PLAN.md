# PHI-DPS — FINAL_MARATHON_PLAN.md

## Purpose

This file is the **final-stretch development roadmap** for PHI-DPS after the DocuSign slice and the broader commercial/operations platform build.

Use this to continue development in a new chat or session with a clear endgame plan.

**Sequential execution checklist:** work one gate at a time in order — see [MARATHON_PIPELINE.md](./MARATHON_PIPELINE.md).

---

# 1. Current project state

PHI-DPS is already a very advanced production-grade platform for an M&E / heating / plumbing / facilities business like DPS Heating Services.

It already includes the major backbone:

- CRM / leads / quotes
- jobs / dispatch / telemetry / nearest engineer
- timesheets / labour costing / profitability
- inventory / procurement hooks
- compliance / certificates
- invoicing / payments
- contract / SLA / PPM / assets / sites
- repricing reviews / proposals / customer release
- formal customer acceptance / provider-backed e-sign flow
- amendment creation / approval / activation
- contract versioning / scheduled activations
- activation confirmations
- customer communications / outbound delivery / webhook hygiene
- recommendation engine / low-risk automation
- recurring jobs
- RBAC / approvals / per-user grants / group access
- AI provider env wiring
- **DocuSign provider integration** (real provider behind abstraction: JWT, envelopes, embedded signing, Connect webhooks; stub remains for dev/tests)

This means the platform is no longer in early architecture stage.
It is in the **final serious build stretch**.

---

# 2. Current completion estimate

Realistic estimate at this point:

- **Core platform capability:** about **96%+**
- **Production-ready first rollout:** about **90% to 94%**
- **Mature polished SaaS:** about **78% to 85%**

Meaning:
- the major system foundations are built
- what remains is mainly:
  - rollout hardening
  - commercial/legal refinement
  - operational reliability
  - UX/admin polish
  - enterprise refinement
  - supportability

---

# 3. Main objective for the final stretch

Get PHI-DPS from **advanced production-capable platform** to **real first-rollout-ready product**.

For the remainder of development, optimize for:

- operational safety
- rollout readiness
- supportability
- admin usability
- legal/commercial confidence
- deployment confidence
- real-world issue handling

---

# 4. Final-stretch development strategy

Use this priority order for all remaining work:

1. **workflow gaps that can block real usage**
2. **operational hardening and observability**
3. **admin / UI / support usability**
4. **enterprise refinements**
5. **nice-to-have polish**

Do not waste the final stretch on low-value abstraction unless it clearly unlocks rollout.

---

# 5. Remaining work — master plan

## PHASE 1 — Final commercial/legal workflow hardening

These are the highest-value remaining product slices.

### 5.1 Customer communications follow-up automation polish

**Goal:**
Automatically generate safe follow-up communications/tasks for stalled commercial flows.

**Examples:**
- proposal released but not viewed
- proposal viewed but not responded
- activation confirmation released but not viewed
- activation confirmation viewed but not acknowledged
- e-sign sent but not completed

**Deliver:**
- tighter recurring jobs around these states
- communication draft generation policies
- reminder suppression if customer already responded
- comms dashboards with “needs action now”

**Exit condition:**
Commercial team can trust PHI-DPS to surface all stalled customer workflows.

---

### 5.2 Acceptance-to-amendment / activation policy tightening

**Goal:**
Make it explicit which workflows require:
- simple response
- formal in-product acceptance
- provider e-sign

**Deliver:**
- policy review matrix
- stricter config/policy behavior where needed
- blocker visibility in dashboards
- stronger readiness explanations

**Exit condition:**
No ambiguity about whether a proposal can become an amendment or activation.

---

### 5.3 Activation completion customer communications polish

**Goal:**
Complete the “customer knows it’s live” workflow.

**Deliver:**
- optional auto-create activation confirmation rows on successful activation
- activation communication drafts/reminders
- follow-up when activation confirmation not viewed/acknowledged

**Exit condition:**
Activation lifecycle is fully visible both internally and to the customer.

---

## PHASE 2 — Finance / accounting / commercial safety hardening

### 5.4 Deeper accounting integration polish

**Goal:**
Make invoice, credit, payment, and export flows safer for real finance operations.

**Potential deliverables:**
- stronger invoice state review
- export consistency
- finance-only review queues
- payment reconciliation helpers
- credit note / adjustment placeholder flow if needed
- “held / released / finance-reviewed” clarity in dashboards

**Exit condition:**
Finance can operate safely without ad hoc interpretation.

---

### 5.5 Contract history / diff polish

**Goal:**
Make contract history easier to trust and easier to read.

**Deliver:**
- richer field diff categories
- better version detail rendering
- recent change dashboards
- current active version summaries
- maybe contract change reason taxonomy later

**Exit condition:**
Admins/commercial users can explain contract changes without reading raw JSON.

---

## PHASE 3 — Operational reliability / supportability / rollout hardening

This is one of the most important final bands.

### 5.6 Deployment + environment hardening

**Goal:**
Ensure the platform can be reliably deployed, configured, and recovered.

**Deliver:**
- final environment variable review
- secrets handling audit
- startup idempotency hardening
- migration strategy cleanup
- `.env.example` completeness
- deployment docs
- backup/restore notes
- file/document storage operational notes
- provider setup docs (SMTP, DocuSign, webhook secrets)

**Exit condition:**
A new environment can be stood up cleanly and safely.

---

### 5.7 Observability + operational diagnostics

**Goal:**
Make production issues diagnosable.

**Deliver:**
- structured logs review
- error reporting consistency
- dashboard for failed recurring jobs
- dashboard for failed communications / failed webhooks / failed activations
- health endpoints if needed
- provider integration status pages
- “what is blocked and why” views

**Exit condition:**
Support/admin team can understand failures without deep code diving.

---

### 5.8 Background worker / cron deployment pattern

**Goal:**
Move from “scheduler model exists” to “scheduler is operationally deployable”.

**Deliver:**
- documented cron/worker invocation pattern
- CLI or management command if useful
- run-due cadence recommendations
- production-safe concurrency/idempotency notes
- “single runner” guidance

**Exit condition:**
Recurring jobs can reliably run in production without confusion.

---

## PHASE 4 — UX/admin usability finalization

### 5.9 Admin workflow UX pass

**Goal:**
Reduce friction for commercial/admin/finance/ops users.

**Priority surfaces:**
- contract dashboards
- repricing dashboards
- proposal lifecycle views
- amendment/activation views
- communications dashboards
- recurring job dashboards
- org/group access admin screens
- document visibility / downloads
- customer safety / suppression views

**Exit condition:**
Core users can operate daily workflows without relying on engineering knowledge.

---

### 5.10 Portal UX pass

**Goal:**
Make customer portal polished enough for real client use.

**Priority surfaces:**
- proposal view
- formal acceptance state
- e-sign status
- activation confirmation
- timeline clarity
- document download clarity
- invoices / communications / visibility consistency

**Exit condition:**
Customer-facing flows feel intentional, clear, and trustworthy.

---

### 5.11 Mobile/field UX stabilization

**Goal:**
Ensure engineer-facing workflows are stable and clean.

**Priority surfaces:**
- punch in/out
- telemetry edge cases
- equipment/vehicle readiness visibility
- job details / requirements / forms / signatures / media / parts usage
- offline/poor connection behavior review if relevant

**Exit condition:**
Field workflows are reliable enough for real-day usage.

---

## PHASE 5 — Enterprise / advanced control refinements

These matter, but after rollout blockers.

### 5.12 Customer org hierarchy deepening

**Goal:**
Support larger customer orgs more elegantly.

**Possible deliverables:**
- richer customer access groups
- billing vs operations contact scopes
- site-scoped customer contact groups
- org hierarchy expansion

**Exit condition:**
Large customer access models are manageable.

---

### 5.13 Nested groups / deeper internal org access

**Goal:**
Support more complex internal enterprises.

**Possible deliverables:**
- nested groups
- group inheritance
- more refined org admin permissions
- delegated org admins

**Exit condition:**
Enterprise internal access can scale without many one-off grants.

---

### 5.14 Break-glass / override workflows

**Goal:**
Let authorized users override suppressions/blocks safely.

**Examples:**
- send despite suppression
- override vehicle/equipment readiness
- emergency communications override

**But only with:**
- explicit permission
- audit log
- reason capture

**Exit condition:**
Emergency handling exists without compromising normal safety.

---

## PHASE 6 — Optional but high-value enhancements

### 5.15 Real multi-provider communication support
- additional email provider
- SMS provider
- webhook normalization across providers
- template/channel routing

### 5.16 Additional e-sign providers
- second provider behind abstraction
- provider fallback strategy if needed

### 5.17 Template versioning / localization
- communications template registry
- versioned templates
- locale support

### 5.18 Holiday/calendar import feeds
- admin-managed imports
- external feed ingestion
- region updates

### 5.19 AI-assisted drafting
Only behind service control.

Use for:
- draft summaries
- draft follow-up notes
- proposal explanation text
- internal prioritization suggestions

Do **not** use it for:
- autonomous business actions

---

# 6. Recommended execution order for the last stretch

## Sprint band A — rollout blockers
1. ~~Real e-sign provider implementation finalize and harden~~ **Done (DocuSign behind abstraction; production hardening can continue as needed)**
2. Customer/commercial follow-up automation polish
3. Acceptance policy tightening
4. Activation completion customer comms polish

## Sprint band B — production operations
5. Deployment/env hardening
6. Background worker/cron deployment pattern
7. Observability / diagnostics / operational dashboards

## Sprint band C — usability
8. Admin UX pass
9. Portal UX pass
10. Mobile/field UX stabilization

## Sprint band D — enterprise refinement
11. Customer org hierarchy deepening
12. Nested groups / delegated org controls
13. Break-glass overrides

## Sprint band E — optional expansion
14. More providers
15. Template versioning / localization
16. AI-assisted drafting
17. Holiday feed import

---

# 7. What “done enough for first real rollout” looks like

PHI-DPS is ready for a serious first rollout when all of these are true:

## Commercial workflow
- repricing proposal can be released
- customer can respond / accept formally / e-sign if required
- amendment can be created
- amendment can be approved
- amendment can be activated
- version history is trustworthy
- customer can receive activation confirmation

## Communications
- outbound communications work
- delivery events are ingested
- suppression logic is enforced
- reminder/follow-up workflows exist
- communication dashboards are reliable

## Operations
- recurring jobs can run predictably
- failed jobs are visible
- dispatch / field workflows are stable
- inventory / costing / compliance / invoicing are usable end to end

## Security / access
- RBAC + grants + groups + scopes are stable
- secrets handling is safe
- audit trail exists for sensitive actions

## Deployment / support
- environment setup is documented
- providers are configurable
- production failures are diagnosable
- migrations/startup are safe

---

# 8. Final marathon-mode development rules

For the rest of the build, follow these rules:

## 8.1 Prefer closure over abstraction
Do not invent new architectural layers unless they clearly unlock rollout.

## 8.2 Preserve existing state machines
Extend cleanly. Do not rewrite stable workflows unnecessarily.

## 8.3 Keep routes thin
All meaningful logic stays in services.

## 8.4 Do not weaken approvals / policy gates
Especially around:
- contract changes
- customer communications
- e-sign
- finance-sensitive actions

## 8.5 No hidden automation
Any automation must be:
- visible
- idempotent
- logged
- safe

## 8.6 Favor dashboards and support visibility
Late-stage production readiness depends heavily on operational visibility.

## 8.7 Keep backward compatibility unless explicitly changing policy
Especially around acceptance modes and existing portal workflows.

---

# 9. Marathon status (pipeline §5.1–§5.19)

All gates in **[MARATHON_PIPELINE.md](./MARATHON_PIPELINE.md)** through **§5.19** are **Done**, including Sprint band E (multi-provider comms, e-sign fallbacks, template localization, holiday feed import, controlled AI drafting).

**Next focus is not a numbered marathon gate** but continuous hardening:

- Production **Postgres** DDL where you do not rely on SQLite migrations (see `backend/db/postgres/`).
- **DocuSign** and other providers: credential rotation, webhook reliability, and runbook detail.
- **UX**: admin web (`web/`) parity with new APIs; field polish as operators request.
- **Finance**: credit notes remain **external-system** by design; invoice export is the integration surface.

---

# 10. Continuation instruction (post-marathon)

Use when extending the product after the marathon table is complete:

> Extend PHI-DPS from the current baseline: preserve RBAC, approval gates, auditability, and service-layer patterns. Prefer small, test-backed changes; add UI where APIs exist; document env and DDL for production databases.

---

# 11. What is left (product sense)

There is **no remaining marathon row**. Remaining work is **open-ended quality**:

- Deeper **ICS** coverage (recurrence, time zones) if real feeds require it.
- **Structured LLM outputs** (`run_structured_prompt`) if you need typed JSON beyond text drafting.
- **In-app credit notes** only if you explicitly scope a finance submodule (today: external system + export).

---

# 12. Short closing summary

PHI-DPS is already a very advanced production-grade platform.

Ongoing effort shifts to **rollout hardening**, **operator UX**, **provider reliability**, and **tenant-specific workflows**—not greenfield architecture.

This is no longer about inventing the system.
It is about keeping the existing system **supportable and trustworthy** in real operations.
