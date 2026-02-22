# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DPS Heating Services Ltd — a Next.js 16 website for an HVAC/plumbing services company. Dark-themed, animation-heavy marketing site with service pages, contact forms, and 3D visuals.

## Commands

```bash
npm run dev      # Dev server with Turbopack (http://localhost:3000)
npm run build    # Production build
npm start        # Production server
npm run lint     # ESLint
node scripts/download-images.js  # Download placeholder images from Unsplash/Picsum
```

No test framework is configured.

## Tech Stack

- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5 (strict mode)
- **Styling:** Tailwind CSS v4 (using `@theme` directive in globals.css for brand tokens)
- **Animation:** Framer Motion (scroll-triggered viewport animations), GSAP + ScrollTrigger (advanced scroll effects)
- **3D:** Three.js via @react-three/fiber and @react-three/drei
- **Icons:** Lucide React, accessed via type-safe `ICON_MAP` in `lib/icons.tsx`
- **Utilities:** clsx + tailwind-merge for className composition
- **Fonts:** Plus Jakarta Sans (`--font-jakarta`, body), Space Grotesk (`--font-technical`, headings)

## Architecture

### Routing

App Router with file-based routing. Service pages follow a nested category/detail pattern:

```
/services/heating/boiler-repair
/services/plumbing/general-plumbing
/services/air-conditioning/ac-installation
```

Service detail pages share `ServiceDetailLayout` as a common template component.

### Component Organization

```
components/
├── animations/    # 3D scenes (Three.js), GSAP init, thermal/pipe effects
├── layout/        # Header (fixed nav + mobile menu), Footer
├── sections/      # Page-level content blocks (ProcessSteps, StatsCounter, etc.)
└── ui/            # Reusable primitives (PageHero, ServiceCard, CTABanner, FAQAccordion, etc.)
```

### Data & Constants

All company info, nav links, service areas, and reviews live in `lib/constants.ts`. Many values are TODOs (phone, email, address, Gas Safe number) awaiting real data.

### Styling Conventions

- Brand colors defined as CSS custom properties via Tailwind v4 `@theme` in `globals.css` (e.g. `brand-red`, `brand-navy`, `brand-surface`)
- Dark theme is the default; some sections use white/light backgrounds
- Custom utility classes: `glass-panel` (glassmorphism), `glow-text`, `glow-box`, `gsap-reveal`
- Responsive breakpoints: `md:` and `lg:` used consistently

### Animation Patterns

- Framer Motion: `whileInView` with `viewport={{ once: true }}` for scroll-triggered reveals; staggered delays on mapped items
- GSAP: must call `registerGSAP()` from `components/animations/gsap-init.ts` before use
- Three.js scenes rendered in Canvas components (hero pipe network, 3D logo, boiler explode)

### Key Conventions

- Most components use `"use client"` directive for interactivity
- Path alias: `@/*` maps to project root
- UI copy uses a "technical" voice — e.g. "Deploy Service" instead of "Book", "Operational Pipeline" for process steps
- Image remote patterns configured for `images.unsplash.com` and `source.unsplash.com`
- No backend/API routes yet — forms need endpoint integration
