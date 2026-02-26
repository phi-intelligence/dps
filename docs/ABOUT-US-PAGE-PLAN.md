# About Us Page — Plan

Plan for a new About Us page that follows the DPS website theme and a clear, “normal” layout (inspired by the Artemis-style reference: hero, intro + imagery, stats, philosophy, founders, why choose us).

---

## 1. DPS theme to follow

- **Colors:** Dark default (`brand-surface`, `brand-navy`, `brand-steel`), gold accent (`brand-red` #d4af37), light mode support (`data-theme="light"`).
- **Typography:** Space Grotesk for headings (technical, uppercase, tracking), Plus Jakarta Sans for body.
- **Voice:** Professional, technical — “DESIGN • ENGINEER • MAINTAIN”, Gas Safe, discipline, integrity, reliability. British English.
- **Components:** Reuse `PageHero`, `CTABanner`, existing card/panel styles, `COMPANY` and related constants from `lib/constants.ts`.

---

## 2. Route and nav

- **Route:** `/about` — new `app/about/page.tsx`.
- **Nav:** Add “About Us” back to `NAV_LINKS` (constants), `content-provider` fallback nav, and Footer quick links; optional “Talk to Us” / “Get a Quote” in hero pointing to `/contact` or quote modal.

---

## 3. Section-by-section layout (DPS version of reference)

| Reference section        | DPS About Us section        | Content source | Photos / assets |
|--------------------------|----------------------------|----------------|-----------------|
| Hero: “ABOUT US” + CTA    | **Hero** — “About Us” + subtitle + CTA | `COMPANY.name`, `COMPANY.areas` | 1 hero background (optional) |
| Intro paragraph + collage | **Intro** — Short story + 2–3 image collage | Your copy + `COMPANY.founded`, `COMPANY.founder` | **Your folder:** 2–3 team/site photos |
| Big stats (40+, 231, 32) | **Stats strip** — Years, jobs, areas, rating | Your numbers or placeholders | None (icons/numbers only) |
| Mission / transparency   | **Our philosophy** — Mission + integrity | `COMPANY.mission`, `COMMITMENT_COPY` or your text | Optional subtle bg image |
| Meet the Founders (2)    | **Meet the founder(s)** — Name, bio, headshot | Your copy + `COMPANY.founder` | **Your folder:** 1–2 headshots |
| Why Choose Us (01–04)    | **Why choose us** — 4–6 strength cards | `KEY_STRENGTHS` or your list | Optional card bg (e.g. blueprint) |
| Footer nav               | Use site Footer (no duplicate) | — | — |

---

## 4. Section specs (short)

1. **Hero**  
   - `PageHero`: title “About Us”, subtitle e.g. “{COMPANY.name} — mechanical, electrical & gas across {COMPANY.areas}”, breadcrumbs Home → About Us, optional background image, CTA “Talk to Us” or “Get a Quote” → `/contact`.

2. **Intro + image collage**  
   - One short paragraph (you provide; can pull from `COMPANY.vision` / `COMPANY.mission` as fallback).  
   - Collage: 2–3 images from your folder in a simple grid (e.g. team on site, tools, van).  
   - Layout: text left, collage right (or stacked on mobile).

3. **Stats strip**  
   - 4 items in a row (e.g. Years experience, Jobs completed, Areas covered, Client rating).  
   - You provide numbers (or we use placeholders from constants).  
   - Style: large number + label, same card style as rest of site.

4. **Our philosophy**  
   - One block of copy: transparency, integrity, clear communication (you provide, or we use `COMMITMENT_COPY` / `COMPANY.mission`).  
   - Optional: light blueprint or brand background.

5. **Meet the founder(s)**  
   - One or two people. Per person: name, short bio (you provide), headshot from your folder.  
   - DPS currently has `COMPANY.founder` (e.g. “Dominic”) — we can do one founder or two if you add a second name/bio.

6. **Why choose us**  
   - 4–6 cards (e.g. “01. Gas Safe on every job”, “02. 24/7 capability”, …).  
   - Copy from your list or `KEY_STRENGTHS`.  
   - Optional: subtle image or blueprint per card.

7. **Accreditations (optional)**  
   - Short block listing Gas Safe, insurance, qualifications — from `ACCREDITATIONS`.

8. **CTA**  
   - `CTABanner`: “Get in touch” / “Get a quote” → `/contact`.

---

## 5. Performance (avoid previous hang)

- **Images:** Only hero (and optionally 1 philosophy bg) with `priority`; all others `loading="lazy"`.  
- **No duplicate image use:** Each asset used once (no same image as full-bleed + card in one section).  
- **Lightweight animations:** Minimal Framer Motion (e.g. one `whileInView` per section or none); prefer CSS.  
- **Stable layout:** Explicit sizes / aspect ratios for image containers to avoid layout shift.

---

## 6. What we need from you

1. **Content**  
   - Intro paragraph (or confirm use of `COMPANY.vision` / `COMPANY.mission`).  
   - Stats: years experience, jobs completed, areas (or “X+”), rating (or “5.0”).  
   - Philosophy paragraph (or use `COMMITMENT_COPY`).  
   - Founder(s): name(s), short bio(s). If two founders, second name + bio.  
   - “Why choose us” list (or we use `KEY_STRENGTHS`).

2. **Photos**  
   - Path to the folder (e.g. `public/images/about/` or a path you’ll copy into the repo).  
   - Short note on what each image is (e.g. “hero”, “team on site 1”, “founder headshot”, “second founder”) so we can map them to: hero, intro collage, founder(s).

3. **Optional**  
   - Preference: one founder block vs two.  
   - Any extra section (e.g. “Our story” timeline, “Sectors we serve” from `SECTORS_SERVED`).

---

## 7. Implementation order

1. Add route `app/about/page.tsx` and restore “About Us” in nav + footer.  
2. Build sections in order: Hero → Intro + collage → Stats → Philosophy → Founders → Why choose us → (Accreditations) → CTA.  
3. Wire in your copy and photo paths once you provide them; use constants and placeholders until then.  
4. Run a quick pass: lazy loading, no duplicate images, stable layout, minimal motion.

Once you share the content and photo folder path (and any preferences from §6), we can implement this plan step by step and keep the page on-theme and performant.
