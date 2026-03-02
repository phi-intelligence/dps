# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DPS Heating Services Ltd — a Next.js 16 website for an HVAC/plumbing services company. Dark-themed, animation-heavy marketing site with service pages, contact forms, AI chatbot, admin dashboard, and 3D visuals. Deployed on AWS Amplify.

## Commands

```bash
npm run dev      # Dev server with Turbopack (http://localhost:3000)
npm run build    # Production build
npm start        # Production server
npm run lint     # ESLint
node scripts/download-images.js  # Download placeholder images from Unsplash/Picsum
```

No test framework is configured.

## Environment Variables

Requires `.env.local` with:
- `GEMINI_API_KEY` — Google Gemini API key (read from disk at runtime, not process.env, to allow hot-reload)
- `OPENAI_API_KEY` — OpenAI key (fallback if Gemini fails)

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5 (strict mode)
- **Styling:** Tailwind CSS v4 (using `@theme` directive in globals.css for brand tokens)
- **Animation:** Framer Motion (scroll-triggered viewport animations), GSAP + ScrollTrigger (advanced scroll effects)
- **3D:** Three.js via @react-three/fiber and @react-three/drei
- **AI Chat:** Google Generative AI SDK (Gemini 2.5 Flash primary), OpenAI SDK (gpt-4o-mini fallback)
- **Maps:** Leaflet + react-leaflet (service areas page)
- **Icons:** Lucide React, accessed via type-safe `ICON_MAP` in `lib/icons.tsx` (`IconName` type for safe selection)
- **Utilities:** clsx + tailwind-merge for className composition
- **Fonts:** Plus Jakarta Sans (`--font-jakarta`, body), Space Grotesk (`--font-technical`, headings)

## Architecture

### Routing

App Router with file-based routing. Key route groups:

```
/                           # Home (3D hero, service cards, reviews)
/services/{category}/{slug} # Service detail pages (heating, air-conditioning, plumbing)
/tools                      # Service Finder wizard + Quote Calculator
/contact                    # Contact form with inquiry service
/service-areas              # Leaflet map with coverage areas
/emergency                  # Emergency services page
/admin/login                # Admin login (localStorage auth, demo: admin/admin)
/admin/dashboard            # Inquiry management
/api/chat                   # POST — SSE streaming chat (Gemini → OpenAI fallback)
```

Service detail pages (6 heating + 5 AC) share `ServiceDetailLayout` (`components/sections/`) as a common template accepting props for title, introduction, included services, issues, steps, FAQs, trust points, etc.

### Component Organization

```
components/
├── animations/    # 3D scenes (Hero3DScene, Logo3D, PipeNetwork), GSAP init, thermal/energy effects
├── chat/          # ChatWidget (fixed bottom-right toggle), ChatPanel, ChatMessage
├── layout/        # Header, Footer, LayoutShell (conditionally hides chrome on /admin routes)
├── sections/      # Page-level templates (ServiceDetailLayout, ProcessSteps, StatsCounter, etc.)
└── ui/            # Reusable primitives (PageHero, ServiceCard, QuoteModal, QuoteForm, QuoteCalculator, ServiceWizard, FAQAccordion, etc.)
```

### Key Modules in `lib/`

- `constants.ts` — Company info (COMPANY), NAV_LINKS, SERVICE_AREAS, REVIEWS, OPENING_HOURS. Many values are TODOs awaiting real data.
- `chat-config.ts` — SERVICE_MAP with pricing ranges (domestic/commercial), URGENCY_MULTIPLIER (1.0/1.3/1.6), QUICK_ACTIONS for chat UI.
- `quote-modal-context.tsx` — React Context for global quote modal open/close state with preselected service support. Consumed via `useQuoteModal()`.
- `theme-provider.tsx` — Dark/light theme toggle via `data-theme` attribute, persisted in localStorage (`dps-theme`).
- `inquiry-service.ts` — Client-side localStorage CRUD for inquiries (no backend yet). Used by QuoteModal, QuoteForm, and admin dashboard.
- `hooks/use-chat.ts` — `useChat()` hook managing messages, SSE streaming, and AbortController cancellation.
- `types/chat.ts` — ChatMessage, ChatRequest interfaces.

### Data Persistence

All persistence is currently **client-side localStorage** (development pattern):
- Inquiries: `inquiryService` reads/writes to localStorage (admin dashboard consumes this)
- Theme: `dps-theme` key
- Admin auth: `dps_admin_auth` key (hardcoded demo credentials)
- No database or backend API for data storage yet

### Chat System

The `/api/chat` route reads the Gemini API key from `.env.local` on disk (via `readFileSync`) on each request — this allows updating the key without restarting the server. Responses stream via Server-Sent Events. The system prompt includes company info, service areas, pricing context, and behavior rules (British English, gas emergency hotline, disclaimers). Full message history is sent with each request.

### Quote & Wizard Flows

- **QuoteModal** — 3-step form (service selection → contact info → message). Uses focus trapping and keyboard navigation. Saves via `inquiryService`.
- **QuoteCalculator** — 5-step wizard applying urgency multipliers to SERVICE_MAP price ranges.
- **ServiceWizard** — 3-step flow that redirects to the relevant service detail page.

### Styling Conventions

- Brand colors defined as CSS custom properties via Tailwind v4 `@theme` in `globals.css` (e.g. `brand-red`, `brand-navy`, `brand-surface`)
- Dark theme is the default; light theme via `[data-theme="light"]` selector with `@custom-variant dark`
- Custom utility classes: `glass-panel` (glassmorphism), `glow-text`, `glow-box`, `gsap-reveal`
- Responsive breakpoints: `md:` and `lg:` used consistently

### Animation Patterns

- Framer Motion: `whileInView` with `viewport={{ once: true }}` for scroll-triggered reveals; staggered delays on mapped items
- GSAP: must call `registerGSAP()` from `components/animations/gsap-init.ts` before use
- Three.js scenes rendered in Canvas components (hero pipe network, 3D logo, boiler explode); lazy-loaded where possible

### Key Conventions

- Most components use `"use client"` directive for interactivity
- Path alias: `@/*` maps to project root
- UI copy uses a "technical" voice — e.g. "Deploy Service" instead of "Book", "Operational Pipeline" for process steps, "Uplink Successful" for form submission
- Image remote patterns configured for `images.unsplash.com` and `source.unsplash.com`
- `LayoutShell` (`components/layout/`) conditionally renders Header/Footer/ChatWidget — hidden on `/admin` routes
