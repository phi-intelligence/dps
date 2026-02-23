# DPS Heating Services Ltd — Website Details & Sitemap

This document describes the full website structure, all pages, and key details for use in presentations and documentation.

---

## 1. Site Overview

| Item | Detail |
|------|--------|
| **Site name** | DPS Heating Services Ltd |
| **Tagline / default title** | DPS Heating Services Ltd \| Heating & Air Conditioning |
| **Default meta description** | Professional heating and air conditioning services across London and Surrounding Areas. Gas Safe registered engineers, fast response, free quotes. |
| **Primary audience** | Domestic and commercial customers in London and surrounding areas |
| **Core offering** | Heating (boilers, central heating, radiators, power flushing), Air Conditioning (install, service, repair, commercial, maintenance), Plumbing (repairs, general plumbing) |

---

## 2. Company Details (from site constants)

| Field | Current value | Notes |
|-------|----------------|--------|
| **Company name** | DPS Heating Services Ltd |
| **Phone** | ADD_PHONE_NUMBER | Placeholder — replace with real number |
| **Email** | ADD_EMAIL_ADDRESS | Placeholder — replace with real email |
| **Address** | ADD_ADDRESS | Placeholder — replace with real address |
| **Company number** | ADD_COMPANY_NUMBER | Placeholder — replace with real company number |
| **Gas Safe number** | ADD_GAS_SAFE_NUMBER | Placeholder — replace with real Gas Safe number |
| **Service areas** | London and Surrounding Areas | Used in copy; see list below for areas |

### Opening hours

| Day | Hours |
|-----|--------|
| Mon–Fri | 08:00 – 18:00 |
| Saturday | 09:00 – 13:00 |
| Sunday | Closed |

### Service areas (listed on site)

London, Westminster, Chelsea, Kensington, Fulham, Hammersmith, Wandsworth, Battersea, Clapham, Brixton, Streatham, Balham, Tooting, Wimbledon, Kingston, Richmond, Twickenham, Putney, Southfields, Earlsfield (+ surrounding areas — call to confirm).

### Customer reviews (sample, 3)

- **James T.** — Boiler Repair — 5★ — “Brilliant service from start to finish…”
- **Sarah M.** — Boiler Installation — 5★ — “Had a new combi boiler installed…”
- **David P.** — Boiler Servicing — 5★ — “Annual boiler service carried out efficiently…”

---

## 3. Tech Stack & Structure

- **Framework:** Next.js 16 (App Router), React 19, TypeScript (strict)
- **Styling:** Tailwind CSS v4, `@theme` in `globals.css` for brand tokens
- **Animation:** Framer Motion (scroll reveals), GSAP + ScrollTrigger, Three.js (hero 3D, pipe network)
- **Icons:** Lucide React via `lib/icons.tsx`
- **Fonts:** Plus Jakarta Sans (body), Space Grotesk (headings / technical)
- **Theme:** Light/dark mode via `data-theme` and Tailwind `dark:` (class-based)
- **Global layout:** `LayoutShell` (Header + main + Footer), `ThemeProvider`, `QuoteModalProvider`, Chat widget

---

## 4. Sitemap (all routes)

```
/
├── /about
├── /contact
├── /service-areas
├── /emergency          (Urgent Enquiries)
├── /tools              (Service Finder + Quote Calculator)
├── /services
│   ├── /services/heating
│   │   ├── /services/heating/boiler-repair
│   │   ├── /services/heating/boiler-installation
│   │   ├── /services/heating/boiler-servicing
│   │   ├── /services/heating/central-heating
│   │   ├── /services/heating/radiators
│   │   └── /services/heating/power-flushing
│   ├── /services/air-conditioning
│   │   ├── /services/air-conditioning/ac-installation
│   │   ├── /services/air-conditioning/ac-servicing
│   │   ├── /services/air-conditioning/ac-repairs
│   │   ├── /services/air-conditioning/commercial-ac
│   │   └── /services/air-conditioning/ac-maintenance
│   └── /services/plumbing
│       ├── /services/plumbing/plumbing-repairs
│       └── /services/plumbing/general-plumbing
└── /admin
    ├── /admin/login
    └── /admin/dashboard
```

---

## 5. Navigation (main site)

- **Home** → `/`
- **Services** (dropdown)
  - Heating Services → `/services/heating`
  - Air Conditioning → `/services/air-conditioning`
- **About Us** → `/about`
- **Service Areas** → `/service-areas`
- **Contact** → `/contact`

Header also includes: theme toggle (light/dark), phone number, “Get a Free Quote” (opens quote modal). Admin is not in main nav; access via `/admin/login`.

---

## 6. Page-by-page details

### 6.1 Home — `/`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Landing: introduce DPS, services, trust, and drive quotes/calls |
| **Title** | Default (DPS Heating Services Ltd \| Heating & Air Conditioning) |

**Sections (top to bottom):**

1. **Hero** — Full-height; Gas Safe badge, logo, “DPS Heating.” gradient headline, short intro, “Get a Free Quote” + “Call Us Now”; 3D hero scene (e.g. logo/model).
2. **Trust bar** — Glass panel with trust points (e.g. Fast Response, Gas Safe, Clean & Tidy, Transparent Pricing).
3. **Our Services** — Two cards: Heating (boiler repair/install/servicing, link to `/services/heating`), Air Conditioning (AC install/servicing/commercial, link to `/services/air-conditioning`).
4. **About / Engineering quality** — “Qualified Engineers”, short company blurb, bullet list, “About Us” link.
5. **Engineer photo strip** — Full-width image + overlay text (“Gas Safe Registered Engineers / Every Job Done Right”).
6. **How We Work** — ProcessSteps (dark variant): steps from contact to completion.
7. **Why Choose DPS** — Stats counter + four trust points (Fast Response, Gas Safe, Clean & Tidy, Transparent Pricing).
8. **Final CTA** — “Ready to Book?” with quote/call prompt.

**Features:** Quote modal trigger, EnergyFlowBackground, SectionWaves, Framer Motion/GSAP.

---

### 6.2 About Us — `/about`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Company story, credentials, approach |
| **Title** | About Us \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “About Us”, subtitle, breadcrumbs (Home → About Us), background image.
2. **Who We Are** — Gas Safe badge, headline, intro paragraphs, Gas Safe registration callout (number placeholder).
3. **Our approach** — Three cards: Reliability, Fully Qualified Engineers, Honest Transparent Pricing.
4. **Blueprint billboard** — Visual/content block.
5. **CTA banner** — Book/quote prompt.

---

### 6.3 Contact — `/contact`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Contact info + quote/contact form |
| **Title** | Contact Us \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Contact Us”, subtitle, breadcrumbs (Home → Contact).
2. **Contact & form** — Two columns:
   - **Left:** Call Us (phone), Email Us (email), Opening Hours (Mon–Fri, Sat, Sun).
   - **Right:** Quote/contact form (name, phone, email, service, message) submitting as inquiry (e.g. localStorage/admin).
3. **CTA / urgency** — Supporting copy and prompts.

---

### 6.4 Service Areas — `/service-areas`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Show coverage and list areas |
| **Title** | Service Areas \| DPS Heating Services Ltd |
| **Meta** | DPS covers London and surrounding areas; local engineers |

**Sections:**

1. **Page hero** — “Service Areas”, subtitle, breadcrumbs (Home → Service Areas).
2. **Where We Work** — Intro copy, “Not sure if we cover your area?” card with phone CTA.
3. **Areas we cover** — Grid of area names (from SERVICE_AREAS).
4. **Map / visual** — Optional map or imagery (e.g. ServiceAreasMap component if used).
5. **CTA banner.**

---

### 6.5 Urgent Enquiries — `/emergency`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Urgent heating/AC and gas emergency guidance |
| **Title** | Urgent Enquiries (or similar) \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Urgent Enquiries”, subtitle, breadcrumbs (Home → Urgent Enquiries).
2. **Phone CTA** — Prominent “Call us” with company phone, opening hours note.
3. **Common urgent issues** — Three cards: Boiler Breakdown, Heating Fault, **Gas Emergency — 0800 111 999** (National Gas Emergency).
4. **Quote form** — For non-emergency follow-up.
5. **CTA banner.**

---

### 6.6 Service Finder / Tools — `/tools`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Help users pick a service and get indicative quote |
| **Title** | Service Finder \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Service Finder”, subtitle, breadcrumbs (Home → Service Finder).
2. **Service selector** — ServiceWizard: category + service choice, links to relevant service pages.
3. **Instant quote calculator** — QuoteCalculator: indicative price range by service, property type, urgency.
4. **CTA banner.**

---

### 6.7 Services hub — `/services`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Overview of heating and AC; link to category pages |
| **Title** | Our Services \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Our Services”, subtitle, breadcrumbs (Home → Services).
2. **Categories** — Two main cards:
   - **Heating Services** — Boiler repair/install/servicing, central heating, radiators, power flushing; link to `/services/heating`.
   - **Air Conditioning** — AC install, servicing, repair, domestic/commercial, maintenance; link to `/services/air-conditioning`.
3. **Why DPS** — Gas Safe, Fast Response, Experience.
4. **Blueprint billboard** (if present).
5. **CTA banner.**

---

### 6.8 Heating category — `/services/heating`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | List all heating services with links to detail pages |
| **Title** | Heating Services \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Heating Services”, breadcrumbs (Home → Services → Heating Services).
2. **Intro** — Gas Safe badge, “Heating You Can Trust”.
3. **Service list** — Six services with short descriptions and links:
   - Boiler Repair → `/services/heating/boiler-repair`
   - Boiler Installation → `/services/heating/boiler-installation`
   - Boiler Servicing → `/services/heating/boiler-servicing`
   - Central Heating → `/services/heating/central-heating`
   - Radiator Services → `/services/heating/radiators`
   - Power Flushing → `/services/heating/power-flushing`
4. **Process steps** (How we work).
5. **Blueprint billboard** (if present).
6. **CTA banner.**

---

### 6.9 Heating service detail pages (shared layout)

Each uses **ServiceDetailLayout** with: PageHero, Strategic Overview (intro + image), “What’s included”, “Common issues”, ProcessSteps, Trust points, FAQ accordion, Quote form + CTA.

| URL | Service |
|-----|---------|
| `/services/heating/boiler-repair` | Boiler Repair |
| `/services/heating/boiler-installation` | Boiler Installation |
| `/services/heating/boiler-servicing` | Boiler Servicing |
| `/services/heating/central-heating` | Central Heating |
| `/services/heating/radiators` | Radiator Services |
| `/services/heating/power-flushing` | Power Flushing |

---

### 6.10 Air Conditioning category — `/services/air-conditioning`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | List all AC services with links to detail pages |
| **Title** | Air Conditioning \| DPS Heating Services Ltd |

**Sections:**

1. **Page hero** — “Air Conditioning”, breadcrumbs (Home → Services → Air Conditioning).
2. **Intro** — F-Gas certified badge, “AC Systems Done Right”.
3. **Service list** — Five services with links:
   - AC Installation → `/services/air-conditioning/ac-installation`
   - AC Servicing → `/services/air-conditioning/ac-servicing`
   - AC Repairs → `/services/air-conditioning/ac-repairs`
   - Commercial AC → `/services/air-conditioning/commercial-ac`
   - Maintenance Contracts → `/services/air-conditioning/ac-maintenance`
4. **Process steps**, billboard (if present), CTA banner.

---

### 6.11 Air Conditioning service detail pages (shared layout)

Same structure as heating detail pages (ServiceDetailLayout).

| URL | Service |
|-----|---------|
| `/services/air-conditioning/ac-installation` | AC Installation |
| `/services/air-conditioning/ac-servicing` | AC Servicing |
| `/services/air-conditioning/ac-repairs` | AC Repairs |
| `/services/air-conditioning/commercial-ac` | Commercial AC |
| `/services/air-conditioning/ac-maintenance` | Maintenance Contracts |

---

### 6.12 Plumbing category — `/services/plumbing`

| Attribute | Detail |
|-----------|--------|
| **Purpose** | List plumbing services (technical/“operational” copy) |
| **Title** | Plumbing \| DPS Heating Services Ltd |

**Services listed (with links where available):**

- Hydraulic Repair → `/services/plumbing/plumbing-repairs`
- General Architecture → `/services/plumbing/general-plumbing`
- Leak Diagnostics, Aqueous Design, Infrastructure Feed, Pipework Integrity (some links may be placeholder `#` or “coming soon”).

**Sections:** Page hero, intro, service grid, process steps (e.g. Signal Uplink, Engineer Deployment, Node Resolution, System Optimized), billboard, CTA.

---

### 6.13 Plumbing service detail pages

| URL | Service |
|-----|---------|
| `/services/plumbing/plumbing-repairs` | Plumbing Repairs (Hydraulic Repair) |
| `/services/plumbing/general-plumbing` | General Plumbing |

Same layout pattern: hero, overview, included, issues, steps, trust, FAQ, quote/CTA.

---

### 6.14 Admin — `/admin/login` and `/admin/dashboard`

| Page | URL | Purpose |
|------|-----|--------|
| **Admin login** | `/admin/login` | Test login: credentials shown (admin / admin); Authenticate submits and redirects to dashboard (full page navigation after setting auth in localStorage). |
| **Admin dashboard** | `/admin/dashboard` | Protected by client-side auth check. Lists inquiries (from inquiry service, e.g. localStorage): search, status (pending/contacted/completed), update status, delete. Sidebar: Inquiries, View Site, Logout. |

Admin is not linked in main navigation; access by going directly to `/admin/login`.

---

## 7. Global UI elements

- **Header** — Logo “DPS Solutions”, nav links, theme toggle, phone, “Get a Free Quote” (opens quote modal). Sticky; glass effect on scroll.
- **Footer** — Logo, short blurb, phone, email; Heating links (5); AC links (5); Quick links (About, Service Areas, Contact). Brand and legal/copyright.
- **Quote modal** — Site-wide; opened from header or “Get a Free Quote” buttons. Multi-step: choose service → contact details → submit. Submissions create inquiries (e.g. stored for admin).
- **Chat widget** — Floating chat (e.g. bottom-right); AI assistant (e.g. Gemini/OpenAI) for DPS services, areas, booking. Lazy-loaded panel.

---

## 8. Key flows

1. **Get a quote** — User clicks “Get a Free Quote” → modal opens → select service → enter details → submit → success message; inquiry appears in admin dashboard (when using localStorage backend).
2. **Contact** — User visits `/contact` → sees phone/email/hours + form → submits form → same inquiry flow as above.
3. **Find service** — User goes to `/tools` → Service Finder or Quote Calculator → navigates to service page or gets estimate.
4. **Urgent** — User goes to `/emergency` → sees phone + gas emergency number 0800 111 999 → can call or submit form.
5. **Admin** — User goes to `/admin/login` → enters admin/admin → Authenticate → redirect to `/admin/dashboard` → view/search/update/delete inquiries.

---

## 9. File reference (for presentations)

- **Company/config:** `lib/constants.ts` (COMPANY, OPENING_HOURS, SERVICE_AREAS, REVIEWS, NAV_LINKS)
- **Layout:** `app/layout.tsx` (metadata, theme script, LayoutShell, providers)
- **Layout UI:** `components/layout/LayoutShell.tsx`, `Header.tsx`, `Footer.tsx`
- **Quote:** `lib/quote-modal-context.tsx`, `components/ui/QuoteModal.tsx`, `QuoteForm.tsx`
- **Inquiries:** `lib/inquiry-service.ts` (client-side storage); admin: `app/admin/login/page.tsx`, `app/admin/dashboard/page.tsx`
- **Service detail template:** `components/sections/ServiceDetailLayout.tsx`
- **Pages:** `app/**/page.tsx` per route above

---

*Document generated for DPS Heating Services Ltd website. Update company placeholders (phone, email, address, Gas Safe number, company number) in `lib/constants.ts` before production.*
