# PHI‑DPS — Gap Analysis, Target-State Workflows, and Deep Build Specification

## Purpose of this document

This document is the implementation-grade brief for **PHI‑DPS**, an M&E operations platform for a contractor like DPS Heating Services Ltd.  
It is written so a development agent can follow it as a product and engineering guide, not just as a feature checklist.

This is **not** a simple field-tracking app.  
This is a **mechanical, electrical, gas, compliance, dispatch, asset, commercial maintenance, and financial operations platform**.

The purpose of PHI‑DPS is to:

- increase engineer productivity
- reduce travel waste and dispatcher overhead
- improve SLA performance
- improve compliance and audit readiness
- accelerate invoicing and cash collection
- improve contract margin visibility
- strengthen customer experience
- make DPS look more premium and operationally mature than competitors

---

# 1. Strategic Positioning

## 1.1 What PHI‑DPS is

PHI‑DPS should be built as an **M&E operations command system**.

It must manage:

- lead capture and customer onboarding
- quoting and approval
- reactive jobs
- planned preventative maintenance (PPM)
- asset and site history
- engineer scheduling and dynamic dispatch
- live field execution
- compliance documentation and certificates
- timesheets, clock-in/out, labour costing
- van stock, warehouse stock, materials usage, procurement
- invoicing, payments, and contract profitability
- customer communication and portal access
- analytics, operational alerts, and optimisation insights

## 1.2 What PHI‑DPS is not

PHI‑DPS should not be treated as just:

- a CRM
- a dispatch board
- a tracking screen
- a time clock app
- a certificate generator
- a quoting tool

Those are modules inside the platform.  
The platform’s real value is in **how they work together**.

## 1.3 Core outcome

The system should behave like this:

> every enquiry becomes structured operational data;
> every job is scheduled with context;
> every engineer action is captured once at source;
> every compliance requirement is enforced by workflow;
> every completed job flows automatically into costing, invoicing, customer updates, and reporting.

---

# 2. Gap Analysis Matrix

## 2.1 Current DPS state vs market vs PHI‑DPS target

| Domain | Current DPS State | Typical Industry Standard | PHI‑DPS Target State |
|---|---|---|---|
| CRM | Leads, convert to customer | Leads, customer records, reminders | Full commercial CRM with lead routing, quote follow-up, contract renewal, upsell tracking |
| Quotes | Create, list, accept | Quote to job flow | Versioned quoting, approval workflows, cost assumptions, margin preview, optional deposit collection |
| Jobs | Create, assign, update status | Job board + status changes | Job lifecycle with SLA, dependencies, pre-job checks, asset/site linkage, cost and compliance gates |
| Dispatch | Manual assign by engineer_id | Calendar + live location + route help | Dynamic dispatch engine with nearest qualified engineer, workload balancing, urgent job insertion |
| Tracking | Geofence + punch location | Live technician/vehicle GPS | Continuous phone + van telemetry, route intelligence, ETA, audit trail, exception alerts |
| Mobile app | Login, jobs, punch in/out | Job start/complete + notes + photos | Full field execution console: forms, readings, photos, signatures, certificates, parts, defects, offline sync |
| Time tracking | Punch in/out, timesheets, approve | Timesheets + payroll export | GPS-verified attendance, job-level labour costing, overtime rules, shift logic, exception review |
| Compliance | Certificates generate/store | Certificates/forms/checklists | End-to-end compliance engine with templates, gates, renewals, competence enforcement, audit packs |
| Assets | Partial / emerging | Asset register + service history | Site > asset > maintenance > fault history > PPM > warranty > compliance lineage |
| Inventory | Partial / emerging | Stock and parts tracking | Warehouse + van stock + reservations + procurement + usage + margin impact |
| Invoicing | Generate/pay | Job to invoice | Invoice release rules, contract billing, T&M vs fixed price, staged billing, credit control workflows |
| Portal | Me views for jobs/certs/invoices | Basic portal | Premium client portal: ETA, documents, service history, open issues, approvals, payments |
| Analytics | Dashboard + ETL run | KPI dashboards | Operational intelligence: dispatch recommendations, SLA risk, margin leakage, idle gaps, recurring faults |
| Commercial contracts | Limited | PPM and service agreements | SLA-backed contract engine with planned/reactive blending, entitlements, renewals, profitability |

## 2.2 Main gaps to close first

The most important gaps are:

1. **Dynamic dispatch logic**
2. **Live telemetry from engineer phone and van**
3. **Asset / site / contract-centric workflows**
4. **Deep mobile field execution**
5. **Inventory + procurement + job costing linkage**
6. **Compliance as a release gate, not a side process**
7. **Customer communication and ETA transparency**
8. **Operational decision support, not only dashboards**

---

# 3. Platform Operating Model

## 3.1 Five product pillars

Cursor should structure thinking around these 5 pillars.

### Pillar A — Revenue Operations
This pillar covers:

- leads
- CRM
- quotes
- sales follow-up
- quote acceptance
- deposits
- contract upsells
- renewals

### Pillar B — Field Operations
This pillar covers:

- jobs
- scheduling
- dispatch
- engineer availability
- live tracking
- route optimisation
- field mobile workflows
- clock-in/clock-out

### Pillar C — Compliance and Service Assurance
This pillar covers:

- certificates
- checklists
- RAMS acknowledgement
- competence validation
- audit trails
- document packs
- regulatory workflow enforcement

### Pillar D — Service Delivery Economics
This pillar covers:

- labour capture
- material usage
- inventory
- procurement
- job costing
- contract profitability
- invoice automation
- cash collection

### Pillar E — Client Experience and Retention
This pillar covers:

- ETA updates
- portal
- certificates and invoices
- service history
- planned maintenance reminders
- contract reporting
- issue transparency

All workflows should be designed so they strengthen all 5 pillars together.

---

# 4. Canonical End-to-End Workflow

This section explains the full target workflow in detail.

## 4.1 Workflow 1 — New reactive service request

### Step 1: Enquiry enters system
A customer calls, emails, fills the portal form, or is created manually by office staff.

System behaviour:

- create a **Lead** if customer is new
- attach enquiry to **Customer** if existing
- classify request type:
  - reactive breakdown
  - service request
  - quote request
  - PPM callout
  - compliance visit
  - emergency callout
- capture location and service address
- capture issue details, urgency, and preferred access window
- identify whether this relates to an existing contract, site, or asset

Target logic:

- if known customer + known site + known asset, prefill all relevant history
- if contract exists, show contract entitlement and SLA immediately
- if emergency, surface high-priority dispatch path

### Step 2: Triage
Dispatcher or coordinator triages the enquiry.

System should show:

- customer importance / contract tier
- SLA obligations
- known asset history
- recurring faults
- last engineer who attended
- open invoices or commercial flags
- required competencies likely needed

Target outcome:

- quote required
- dispatch directly
- schedule survey first
- raise follow-on maintenance recommendation

### Step 3: Quote or immediate job creation
If quote needed:

- build quote from labour + materials + access assumptions
- attach asset/site context
- optionally reserve long-lead materials
- generate branded quote
- send for digital approval

If no quote needed:

- create job directly
- tag as T&M / fixed price / contract-covered / warranty / emergency

### Step 4: Dispatch readiness check
Before dispatch, the system should verify:

- job has location / geofence center
- required competencies are known
- customer contact details exist
- contract/SLA attached if relevant
- prerequisite documents/checklists known
- material requirement known or marked unknown

### Step 5: Dispatch decision
The dispatch engine should score candidate engineers using:

- live location from phone
- live location from van
- engineer availability state
- job load today
- current active job status
- required competencies/certifications
- territory/service area rules
- van stock / tools fit
- expected travel time
- SLA urgency

System outputs:

- best engineer recommendation
- alternatives 2 and 3
- why selected
- risk flags (traffic, overbooked, cert expiring, no stock)

Dispatcher can:

- accept recommendation
- manually override with reason

### Step 6: Engineer mobile execution
Engineer receives:

- job details
- customer/contact
- location/navigation
- asset history
- checklists/forms required
- expected parts
- compliance requirements
- notes/photos from prior visits

Engineer actions:

- accepts/acknowledges job
- starts travel status
- system sends customer ETA if enabled
- upon arrival, geofence triggers or confirms arrival
- engineer clocks in / job starts

### Step 7: On-site job execution
Engineer mobile app must support:

- start/stop job timers
- punch in/out
- task checklist completion
- photos and videos
- voice/text notes
- asset readings
- defects found
- material usage entry
- customer signature
- follow-on works recommendation
- quote raise from site if needed
- compliance data entry

### Step 8: Compliance capture
If the job requires compliance:

- required template is selected automatically based on job type
- engineer fills readings and mandatory fields
- system validates mandatory fields before completion
- digital signatures collected
- certificate generated and stored
- customer copy available instantly

### Step 9: Completion controls
A job cannot fully complete unless required rules pass.

Completion gates may include:

- mandatory checklist complete
- mandatory photos present
- required certificate generated
- material usage logged or explicitly waived
- labour recorded
- signature captured if required

### Step 10: Invoice release
Invoice generation should not be independent manual admin.

The system should:

- read actual labour
- read actual materials used
- apply contract pricing rules or T&M logic
- include certificates and job summary
- release invoice automatically or queue for finance review

Invoice release should be blocked if:

- compliance missing
- job status incomplete
- labour not approved where required
- contractual billing rule unresolved

### Step 11: Post-job intelligence
System should update:

- customer history
- site history
- asset history
- recurring fault markers
- engineer performance metrics
- margin estimate vs actual
- renewal / follow-on opportunity

---

## 4.2 Workflow 2 — Planned preventative maintenance contract

This is where PHI‑DPS can become much stronger than generic field tools.

### Contract creation
A commercial customer has:

- one or more sites
- one or more assets per site
- a service agreement
- response obligations
- planned visits
- included / excluded works

The system must support:

- contract term
- billing frequency
- PPM schedule frequency
- asset list under contract
- SLA rules
- contact hierarchy
- escalation rules
- entitlements and exclusions

### PPM planning logic
The planner should:

- generate visits based on contract schedule
- group jobs geographically where sensible
- group multiple assets at same site into one planned attendance
- warn if visits will breach monthly/quarterly obligations

### PPM execution
Engineers should follow digital planned maintenance forms.

Outputs should include:

- service checklist result
- asset readings
- defects found
- pass/fail state
- follow-on remedial recommendation
- compliance documents if required

### Follow-on works flow
If defects are found:

- system raises remedial quote or reactive follow-up job
- links it back to the original PPM visit
- tracks conversion rate from PPM findings to revenue

### Contract reporting
Commercial clients should be able to view:

- completed PPM visits
- outstanding actions
- asset condition
- compliance packs
- SLA metrics
- invoice status

---

## 4.3 Workflow 3 — Emergency callout and schedule reshuffle

This is a major differentiator if done well.

### Trigger
An urgent call arrives.

### System response
The dispatch engine should:

- assess SLA urgency
- find nearest qualified available engineer
- consider whether currently assigned engineer can be interrupted
- calculate knock-on schedule impact
- suggest reshuffle plan

Suggested response should show:

- who to send
- expected ETA
- which scheduled jobs will shift
- customer communication impact
- risk score

### Dispatcher action
Dispatcher approves or overrides.

### Customer automation
Impacted customers receive:

- delay notice if appropriate
- revised ETA or appointment window

This reduces phone traffic and improves professionalism.

---

# 5. Deep Module Specification

## 5.1 CRM and Lead Management

### Purpose
Turn enquiries into structured opportunities and service relationships.

### Workflow logic
- all inbound enquiries become leads or linked customer activities
- each lead has source, urgency, service type, region, property/site details
- conversion creates customer + site + optional asset shell records
- all later quotes/jobs trace back to the original lead source

### Must-have behaviours
- quote follow-up reminders
- stale lead queue
- lost quote reasons
- renewal opportunity tracking
- customer segmentation (domestic/commercial/FM/landlord)

### Why this matters
Most service systems underuse CRM.  A premium M&E platform should connect sales to operations and renewals.

---

## 5.2 Quoting and Estimation

### Purpose
Convert work demand into profitable, professional jobs.

### Workflow logic
- quotes can be created from lead, survey, PPM defect, or engineer recommendation
- support quote revisions without losing history
- quote acceptance can trigger job creation automatically
- quote should carry assumptions into dispatch and invoicing

### Core features
- labour lines
- material lines
- markup rules
- optional items
- exclusions and assumptions
- digital acceptance
- deposit rules
- version history

### Advanced features to beat market
- margin preview before send
- stock availability warnings before send
- engineer-generated on-site remedial quote flow
- follow-up automation for pending quotes

---

## 5.3 Job Management

### Purpose
Represent operational work from creation to closure.

### Workflow logic
Each job should know:

- customer
- site
- asset(s)
- contract or quote origin
- service category
- status
- required competencies
- required documents/checklists
- materials expected
- SLA target
- billing rule

### Target statuses
Suggested canonical statuses:

- draft
- awaiting approval
- ready to schedule
- scheduled
- dispatched
- en route
- on site
- paused
- completed pending compliance
- completed pending finance
- closed
- cancelled

### Why current systems fail
Many tools have only simple status fields.  PHI‑DPS should make statuses operationally meaningful and automation-friendly.

---

## 5.4 Dispatch and Scheduling

### Purpose
Put the right engineer in the right place at the right time with the least waste.

### Current weakness to fix
Manual assignment + punch-based location is not enough.

### Target workflow
Dispatch must use:

- schedule board
- live engineer location
- live van location
- active job states
- skill/certification fit
- travel time estimates
- territory rules
- job priority/SLA
- capacity balancing

### Dispatch engine recommendation model
For each candidate engineer, calculate score using:

- skill fit
- certification validity
- current distance/travel time
- current and next jobs
- expected overrun risk
- van stock match
- working hours/overtime
- customer/account preference

### Dispatcher console should show
- map
- calendar
- engineer availability lanes
- warnings
- recommended assignment
- urgent insertion controls
- delays/conflicts

### Premium capability
- one-click schedule rebalance
- bulk geographic grouping for PPM work
- traffic-aware ETA updates
- emergency override mode

---

## 5.5 Tracking, Telemetry, and Location Intelligence

### Purpose
Tracking is not a standalone product feature.  It is an input into dispatch, audit, ETA, timesheets, and safety.

### Required target state
Track both:

- engineer phone location
- van/device telematics location

### Why both matter
- phone indicates actual engineer location when out of van
- van provides stronger fleet route and vehicle-state view

### Telemetry workflow
Phone app sends periodic location events.
Van device sends periodic location events.
System stores:

- raw event stream
- latest known location per engineer
- latest known location per vehicle

### How location is used
- nearest engineer selection
- customer ETA updates
- arrival verification
- timesheet validation
- route efficiency analytics
- no-show / unexpected deviation alerts

### Important rule
Tracking should not just paint dots on a map.
It must drive decisions.

---

## 5.6 Mobile Field Execution

### Purpose
The engineer app should be the single field workstation.

### Current state
Too limited if it only does login, job list, punch in/out.

### Target mobile workflow
Engineer opens today’s schedule.
Engineer can:

- accept job
- navigate
- update status
- clock in/out
- see asset/site history
- complete forms/checklists
- upload photos/videos
- record parts used
- generate certificates
- collect signature
- create follow-on works
- capture customer notes
- work offline and sync later

### Offline behaviour
All mission-critical field actions must queue locally if offline:

- punches
- photos
- form submissions
- notes
- signatures
- parts usage

### Why this matters
Offline resilience is a professional requirement for field teams.

---

## 5.7 Compliance and Certification Engine

### Purpose
Make regulatory delivery structured, auditable, and hard to get wrong.

### Workflow logic
Compliance should be woven into jobs.
Not done afterward as admin cleanup.

### Target behaviours
- job type decides required form/certificate/checklist
- engineer cannot close where mandatory fields missing
- certificate auto-generates from captured data
- expiry reminders generated automatically
- competence status checked before engineer assignment

### Compliance domains
Potentially support:

- gas certificates
- electrical forms
- service sheets
- inspection checklists
- commissioning sheets
- landlord cert workflows
- commercial audit packs

### Premium differentiator
Provide downloadable customer-ready document packs by job, site, contract, or time period.

---

## 5.8 Site, Asset, and Plant Register

### Purpose
Commercial M&E work revolves around assets and sites, not isolated jobs.

### Entity hierarchy
Customer
→ Site
→ Building/Area
→ Asset / Plant / System
→ Service history / defects / documents / warranty / certificates

### Workflow logic
Every new job should be optionally linked to:

- a known site
- one or more known assets
- or create a new asset from site visit

### Asset record should track
- manufacturer/model/serial
- asset class
- installation date
- contract coverage
- warranty status
- recurring faults
- service history
- readings
- parts history

### Why this matters
This is a major difference between generic FSM and serious M&E service operations software.

---

## 5.9 Contract and SLA Engine

### Purpose
Handle the commercial reality of service agreements.

### Contract model should support
- fixed term
- billing cadence
- PPM obligations
- included reactive hours or exclusions
- response times
- site/asset coverage
- escalation rules
- contract contacts
- renewal dates

### SLA workflow logic
Each job linked to a contract should compute:

- target response time
- target attendance time
- target completion time
- breach risk state

The dashboard should surface:

- jobs near breach
- actual vs SLA performance by contract
- chronic under-service risk

### Why this matters
This is critical for winning and retaining commercial clients.

---

## 5.10 Inventory, Van Stock, and Procurement

### Purpose
Control material availability and protect margin.

### Workflow logic
- quote can reserve likely parts
- dispatch should warn if van stock not suitable
- engineer logs actual usage on site
- warehouse and van stock reconcile automatically
- procurement triggered by thresholds or reservations

### Target outcomes
- fewer repeat visits due to missing parts
- better job costing
- fewer invoice disputes
- better purchasing efficiency

### Premium capabilities
- engineer transfer request between vans
- substitute part suggestions
- part availability before assignment
- supplier lead-time warnings on quote

---

## 5.11 Time Tracking, Attendance, and Payroll

### Purpose
Capture labour accurately and feed payroll and costing.

### Workflow logic
Track:

- shift clock-in/out
- job start/stop
- travel time where relevant
- breaks
- overtime
- subcontractor hours

### Validation rules
- punches store GPS
- geofence can validate site arrival/departure
- mismatch events go to exception review queue

### Important distinction
Clock-in/clock-out is workforce control.
Job timer is job costing.
Both must exist and be related, but they are not the same thing.

### Premium features
- missed punch recovery workflow
- suspicious punch alerts
- labour cost per job in near-real time
- payroll hold if exceptions unresolved

---

## 5.12 Invoicing, Payments, and Revenue Release

### Purpose
Convert completed operational work into cash quickly and correctly.

### Workflow logic
Invoice should pull from:

- approved labour
- parts used
- contract rules
- quote/pricebook rules
- callout charges
- emergency uplift rules

### Invoice release controls
Block or warn if:

- job not fully complete
- missing compliance
- missing timesheet approval
- unpriced materials used
- contract billing rule unclear

### Premium features
- same-day invoice target
- staged billing for larger works
- recurring contract billing
- automated chaser sequences
- portal payment experience

---

## 5.13 Portal and Customer Experience

### Purpose
Reduce admin workload and make the company look premium.

### Customer should be able to
- log service request
- approve quote
- view job status
- see ETA / engineer on the way
- download certificates and invoices
- pay invoices
- view service history
- view asset records if commercial
- view open recommendations / defects

### Commercial customer portal should also offer
- site-level filtering
- contract performance summary
- compliance pack downloads
- planned visit calendar

This is a major differentiator for FM and commercial clients.

---

## 5.14 Analytics and Operational Intelligence

### Purpose
Turn operational data into recommendations.

### Baseline dashboards
- jobs by status
- response times
- engineer utilisation
- invoice pipeline
- compliance expiries
- quote conversion
- contract performance

### Target intelligent recommendations
- nearest qualified engineer suggestion
- SLA breach risk alert
- low van stock before dispatch alert
- repeated asset fault alert
- invoice blocked due to missing field work alert
- margin erosion on contract warning
- renewal opportunity list

### Premium outcome
The system should not only report what happened.
It should recommend what to do next.

### Recommendation lifecycle — implemented (engine + API)

**Docs in code:** `backend/app/services/recommendation_engine.py` (module docstring) and `backend/app/services/recommendation_lifecycle.py`.

| Control | Behaviour |
|--------|------------|
| **Dedupe** | Same `recommendation_key` updates a single **open** row. |
| **Cooldown / reopen** | After **dismiss** / **human resolve** / **auto-resolve**, a **new** open row for the same key is blocked for configurable hours (`PHI_DPS_OPS_REC_COOLDOWN_DISMISS_HOURS` / `PHI_DPS_OPS_REC_COOLDOWN_RESOLVE_HOURS`), unless **severity increases**, **`PHI_DPS_OPS_RECOMMENDATION_RULE_VERSION`** changed since last close, or cooldown elapsed. **`POST /ops/recommendations/{id}/reopen`** reopens the closed row (bypasses cooldown). |
| **Per-row snooze** | `suppressed_until` + `suppression_notes` on the recommendation; default list/dashboard feeds omit snoozed items; `GET /ops/recommendations?include_suppressed=true` shows them. **`POST /ops/recommendations/{id}/snooze`**. |
| **Scope suppression (scan)** | Table `recommendation_suppressions`: match by exact `recommendation_key` or by **category** with optional **contract** / **site** filter. While active, **new** rows for that scope are not created; an existing **open** row is still updated and kept in the active key set so auto-resolve does not drop it. **`POST/GET/DELETE /ops/recommendations/suppressions`**. |
| **Repeated-occurrence escalation** | Each emit logs `recommendation_occurrence_events`; if fire count in rolling window ≥ `PHI_DPS_OPS_REC_ESCALATION_MIN_FIRES`, severity bumps one step. Config: `PHI_DPS_OPS_REC_ESCALATION_WINDOW_HOURS`, `PHI_DPS_OPS_REC_ESCALATION_ENABLED`. Details in `detail.lifecycle`. |
| **Closed audit** | `closed_as`: `dismissed` \| `resolved` \| `auto_resolved`. |

Further ideas (multi-step escalation, queue routing, category-wide snooze without scan table) can build on this layer.

---

# 6. What Cursor Should Change to Beat the Market

## 6.1 Do not build only CRUD screens
Each module should have:

- domain logic
- validations
- event triggers
- automation rules
- operational states
- release gates

## 6.2 Make dispatch truly intelligent
Must include:

- live telemetry
- nearest engineer query
- skill + cert fit
- workload balancing
- route optimization
- urgent reshuffle recommendations

## 6.3 Make the mobile app the operational center
Not just punch app.
It must be the engineer’s end-to-end field tool.

## 6.4 Make compliance part of workflow, not admin afterthought
Certificates and checklists must be embedded into job completion logic.

## 6.5 Make commercial sites/assets/contracts first-class citizens
This is how PHI‑DPS becomes an M&E operations platform instead of a general trades app.

## 6.6 Make finance and operations deeply linked
Quotes, jobs, time, stock, invoices, and margin must all connect.

## 6.7 Make customer experience visibly premium
ETA, portal, document access, branded reports, and issue visibility should feel enterprise-grade.

---

# 7. Build Priorities

## Priority 1 — Operational intelligence foundation
- live phone telemetry
- live van telemetry
- latest engineer/vehicle state
- nearest engineer endpoint
- improved dispatch board

## Priority 2 — Commercial M&E data model
- customer/site/asset hierarchy
- contract model
- SLA engine
- PPM generation

## Priority 3 — Field execution depth
- offline-first mobile workflows
- forms/checklists
- photos/signatures
- parts usage
- follow-on works
- certificate generation from mobile

## Priority 4 — Economic control
- van stock and warehouse stock
- procurement flows
- job costing
- invoice release controls
- contract profitability

## Priority 5 — Client differentiation
- ETA updates
- advanced portal
- compliance packs
- planned maintenance visibility
- renewal / recommendation engine

---

# 8. Final Build Principle for Cursor

Cursor should follow this principle throughout implementation:

> PHI‑DPS is not a set of disconnected modules.
> It is one operational workflow engine where sales, dispatch, field execution, compliance, costing, invoicing, and customer experience all reinforce each other.

Every new feature should answer:

1. what operational problem does this solve?
2. what data should it create or consume?
3. what module does it trigger next?
4. what control or automation does it enable?
5. how does it save time, reduce risk, improve margin, or improve client experience?

If a feature does not improve one of those outcomes, it should be reconsidered.

---

# 9. Final Conclusion

PHI‑DPS already has the beginnings of a serious operations platform.

But to become top among competitors, it must evolve from a workflow system into a **decision-driven M&E operating platform**.

That means:

- live dispatch intelligence
- site/asset/contract-centric operations
- rich field execution
- compliance-driven workflow enforcement
- real job costing and procurement linkage
- premium customer visibility
- operational recommendations, not just dashboards

That is the target state Cursor should build toward.
