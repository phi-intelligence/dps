# Scope of Work — DPS Heating Services Ltd Website

**Client:** DPS Heating Services Ltd  
**Document date:** [Insert date]  
*(Payment terms are in a separate document.)*

---

## 1. Project overview

Delivery of a professional marketing website for DPS Heating Services Ltd, focused on generating enquiries for heating, air conditioning, and plumbing services across London and surrounding areas. The site will be built with modern, maintainable technology; responsive and accessible; and optimised for search and conversions. A **content management system (CMS)** will be set up so that the client can update key content from a web dashboard without code or technical knowledge.

---

## 2. Deliverables included

### 2.1 Website build and delivery for client hosting

- **Responsive website** (desktop, tablet, mobile) built with Next.js and React.
- **Dark and light theme** with user toggle; consistent branding and contrast.
- **Fast loading** and basic performance optimisation (images, structure).
- **SEO foundation:** semantic structure, meta titles/descriptions, Open Graph support across main pages.
- **Hosting:** The client has an **IT team and a private cloud provider**. We will deliver the **built application and deployment documentation** (e.g. build steps, environment variables, recommended stack) so the client’s IT team can deploy and run the site on their private cloud. We do not host the site; hosting and infrastructure are the client’s responsibility. We will work with the client’s IT team as needed to ensure a smooth handover and go-live on their environment.

### 2.2 Public-facing pages (24 pages)

- **Home** — Hero, trust bar, services overview, “How we work”, testimonials, calls to action.
- **About** — Company story, credentials (e.g. Gas Safe), approach, CTA.
- **Contact** — Contact details (phone, email, hours), enquiry/quote form.
- **Service areas** — Coverage list and “where we work” content.
- **Urgent enquiries** — Prominent phone CTA and gas emergency number (0800 111 999).
- **Service Finder / Tools** — Service selector and simple quote calculator.
- **Portfolio** — Completed projects, stats, featured project, client testimonials.
- **Services hub** — Overview of heating and air conditioning with links to sub-pages.
- **Heating** — Category page plus **6** detail pages (e.g. boiler repair, installation, servicing, central heating, radiators, power flushing).
- **Air conditioning** — Category page plus **5** detail pages (e.g. AC installation, servicing, repairs, commercial AC, maintenance).
- **Plumbing** — Category page plus **2** detail pages (e.g. plumbing repairs, general plumbing).

Service pages will include: clear intro, “what’s included”, common issues, process steps, trust points, FAQs, and quote/CTA.

### 2.3 Enquiry and quote handling

- **Quote / contact form** — Name, phone, email, service type, message; validation and success/error handling.
- **Site-wide “Get a quote” modal** — Same form available from header and key CTAs.
- **Inquiry storage** — Form submissions stored so they can be viewed in the admin area (e.g. simple backend or agreed storage method).
- **Email integration** — **Included.** When a visitor submits an enquiry or quote request, the client will be **notified by email** (to an address they provide) so they can respond promptly. The integration will work with the client’s existing mail setup or private cloud environment as agreed with their IT team.

### 2.4 Admin area (internal use)

- **Admin login** — Secure login (credentials as agreed; test credentials replaced before or at launch).
- **Admin dashboard** — List of enquiries with search; update status (e.g. pending, contacted, completed); delete; view contact and service details.
- **Access** — Admin area not linked in main navigation; access via direct URL only.

### 2.5 Landline number

- We will **provide the client with a dedicated landline number** for use on the website (e.g. Contact page, header, Urgent enquiries) and for customer enquiries. The number will be configured and displayed on the site as the primary contact number; call handling and forwarding (if any) are as agreed with the client.

### 2.6 Content and branding

- **Structure and copy** — Page structure, headings, and placeholder or initial copy for all delivered pages.
- **Company details** — Placeholders or final fields for phone, email, address, Gas Safe number, company number, service areas, opening hours. Client to supply final values; these will be editable via the CMS.
- **Reviews and portfolio** — Placeholder or initial reviews and portfolio projects; client to supply final text and images where needed. Editable via CMS.
- **Imagery** — Use of placeholder or client-supplied images; guidance on image optimisation for client photos.

### 2.7 Content update pipeline

- **Repository:** Website code and (where applicable) content are stored in a **Git repository** (e.g. GitHub or GitLab). The client does not need to use Git for day-to-day updates; the CMS is the primary way to edit content.
- **Deployment:** The client’s **IT team** will build and deploy the site on their **private cloud**. We will provide documentation so that when content is published in the CMS (or when code is updated), the IT team can rebuild and deploy as needed (e.g. via webhook, CI/CD, or manual build). We will agree the exact process with the client’s IT team during handover.
- **Services used:** Version control (GitHub/GitLab), the chosen CMS (Sanity or Contentful), and the client’s own hosting. All will be documented in the handover for the client and their IT team.

### 2.8 Content management system (CMS) — easy content updates

A **hosted content management system** will be connected so the client can update the website from a simple online dashboard. No code or Git required.

- **CMS service:** A hosted CMS such as **Sanity.io** or **Contentful** (chosen to stay within free tier where possible). The client will receive login details and a short user guide.
- **Editable in the dashboard:**
  - Company details (phone, email, address, Gas Safe number, company number, opening hours)
  - Service areas list
  - Customer reviews (name, service, rating, quote)
  - Portfolio projects (title, category, location, description, image, stats)
  - Key service and page copy (as agreed in the content model)
  - Navigation labels and links (if included in the content model)
- **Handover:** Written guide and, if agreed, one short training session (e.g. 30–45 minutes) on how to log in, edit content, and publish. Any ongoing CMS costs beyond the free tier will be clearly explained before go-live.

### 2.9 AI chat assistant

- **Chat widget** — Floating chat on the site for quick questions.
- **AI assistant** — Answers about services, areas, and contact using company info (e.g. powered by Gemini API). The client or provider will supply the API key; typical usage is low cost or within free tier for normal traffic. Any ongoing API cost is the client’s responsibility unless otherwise agreed.

### 2.10 Documentation and handover

- **Website details document** — Sitemap, list of all pages, main sections per page, and key features (for reference and presentations).
- **CMS user guide** — How to log in, edit content, and publish; what each section is for.
- **Technical handover** — How to access admin, where API keys (e.g. chat) are configured, deployment and mail-integration notes for the client’s IT team, and who to contact for technical changes. No ongoing support or maintenance is included unless agreed separately.

---

## 3. Out of scope (unless agreed and quoted separately)

- **Professional copywriting** — Only structure and placeholders; full professional copy is extra.
- **Photography or video** — Only use of client-supplied or stock/placeholder media.
- **E‑commerce or payments** — No online payment or booking payments.
- **Hosting and infrastructure** — The client’s IT team and private cloud provider are responsible for hosting; we deliver the application and documentation only. We do not charge for or manage hosting.
- **Content updates after launch** — One round of minor content tweaks can be included; ongoing updates are support/maintenance and quoted separately.
- **Third-party API costs** — Any costs for chat or other APIs beyond free tier are the client’s responsibility unless agreed otherwise.
- **Training beyond one session** — Additional training or support is quoted separately.

---

## 4. Assumptions

- The client will provide: final company details (phone, email, address, Gas Safe number), service areas, opening hours, and any preferred images and review text in good time. The **landline number** we provide will be used as the primary contact number on the site unless the client specifies otherwise.
- The client has an **IT team and a private cloud provider**. Hosting, deployment, and infrastructure are the client’s responsibility; we deliver the built application and documentation and will work with the IT team as needed for handover. **Mail integration** for enquiry notifications will be implemented to work with the client’s mail setup or environment.
- One main round of feedback after the initial build; additional design or feature changes may be quoted as change requests.
- No bespoke integrations (e.g. booking systems, accounting) unless specifically quoted.
- The website will be maintained by the client or their IT team using the CMS and documentation; ongoing technical support is not included unless agreed.
- The CMS will be chosen (Sanity or Contentful) as agreed; if the client requires a different CMS or extra features, this will be quoted separately.

---

## 5. Timeline (indicative)

- **Kick-off / content** — [X] weeks for the client to supply details and assets.
- **Build and CMS setup** — [X] weeks for development, CMS configuration, and internal testing.
- **Revisions** — Up to [X] round(s) of feedback and amendments within scope.
- **Launch** — Go-live and handover by [date], subject to client sign-off and hosting/DNS readiness.


---

## 6. Acceptance

By signing below, the client confirms acceptance of this scope and the deliverables listed. Payment terms are set out in a separate document. Changes beyond this scope will be agreed in writing and may incur additional charges.

**Client signature:** _________________________ **Date:** ________  

**Provider signature:** _________________________ **Date:** ________  

---

*This Scope of Work should be read alongside the Website Details document (sitemap and page list) where relevant.*
