/**
 * Site constants — used as fallback when CMS (DB) is unavailable and for content not yet in CMS.
 * CMS is the source of truth for: site config (company, opening hours), nav, reviews, portfolio,
 * accreditations, service areas, inquiries, and service detail pages that have been seeded.
 * Constants below are still used for: COMMERCIAL_SERVICES, DOMESTIC_SERVICES, CAPABILITY_*,
 * SECTORS_*, KEY_STRENGTHS, HEALTH_SAFETY_COPY, COMMITMENT_COPY, and inline page content (About, Home sections).
 */
export const OPENING_HOURS = {
  weekday: "08:00 - 18:00",
  saturday: "09:00 - 13:00",
  sunday: "Closed",
};

export const COMPANY = {
  name: "DPS Heating Services Ltd",
  legalName: "DPS Services Heating Ltd",
  phone: "ADD_PHONE_NUMBER", // TODO: Replace with real phone number
  email: "ADD_EMAIL_ADDRESS", // TODO: Replace with real email
  address: "Situated on the outskirts of Kent",
  gasSafeNumber: "ADD_GAS_SAFE_NUMBER", // TODO: Replace with real Gas Safe number
  areas: "London, Kent, Essex and Surrey",
  liabilityInsurance: true,
  indemnityInsurance: true,
  founded: "2024",
  founder: "Dominic",
  industryExperience: "over 13+ years",
  mission: "To deliver reliable, compliant mechanical, electrical, and gas solutions with discipline, integrity, and reliability — putting our clients first, 24 hours a day, 7 days a week.",
  vision: "To be the trusted choice for commercial and domestic engineering services across London and the Southeast, known for exceptional workmanship, compliance & safety, clear communication, and long-term partnerships built on trust.",
}

export const NAV_LINKS = [
  { label: "Home", href: "/" },
  {
    label: "Services",
    href: "/services",
    children: [
      { label: "Commercial Services", href: "/services/commercial" },
      { label: "Domestic Services", href: "/services/domestic" },
    ],
  },
  { label: "Portfolio", href: "/portfolio" },
  { label: "About Us", href: "/about" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Contact", href: "/contact" },
]

export const SERVICE_AREAS = ["London", "Kent", "Essex", "Surrey"]

/** Core service categories from Capability Statement — mechanical, electrical, gas. */
export const CAPABILITY_CORE_SERVICES = [
  {
    title: "Mechanical Services",
    items: [
      "Heating system installation, maintenance, and upgrades",
      "Plant room installations",
      "Pipework systems",
      "Preventative and reactive maintenance",
    ],
  },
  {
    title: "Electrical Services",
    items: [
      "Electrical installations and upgrades",
      "Fault finding and testing",
      "Compliance inspections",
      "Maintenance contracts",
    ],
  },
  {
    title: "Gas Services",
    items: [
      "Gas installation and servicing",
      "Landlord safety inspections",
      "Commercial and domestic gas works",
      "Emergency callouts",
    ],
  },
] as const

/** Core services hero images for homepage (Mechanical, Electrical, Gas). */
export const CORE_SERVICES_IMAGES: Record<string, string> = {
  "Mechanical Services": "/images/core-services/mechanical.png",
  "Electrical Services": "/imagesv2/home_electrical.jpg",
  "Gas Services": "/imagesv2/home_gas.jpg",
};

/** Core service detail page routes (for Core Services section links — hub pages). */
export const CORE_SERVICE_HREFS: Record<string, string> = {
  "Mechanical Services": "/services/mechanical",
  "Electrical Services": "/services/electrical",
  "Gas Services": "/services/gas",
};

/** Core service links from Commercial page — direct to commercial sub-pages. */
export const CORE_SERVICE_COMMERCIAL_HREFS: Record<string, string> = {
  "Mechanical Services": "/services/mechanical/commercial",
  "Electrical Services": "/services/electrical/commercial",
  "Gas Services": "/services/gas/commercial",
};

/** Core service links from Domestic page — direct to domestic sub-pages. */
export const CORE_SERVICE_DOMESTIC_HREFS: Record<string, string> = {
  "Mechanical Services": "/services/mechanical/domestic",
  "Electrical Services": "/services/electrical/domestic",
  "Gas Services": "/services/gas/domestic",
};

/** Core service type slug for sector sub-routes (mechanical | electrical | gas). */
export type CoreServiceSlug = "mechanical" | "electrical" | "gas";

/** Service lists for Commercial / Domestic sub-pages under each core service. */
export const CORE_SERVICE_SECTOR_SERVICES: Record<
  CoreServiceSlug,
  { commercial: string[]; domestic: string[] }
> = {
  mechanical: {
    commercial: [
      "Heating system installation",
      "Heating system repairs",
      "Pumps, valves & controls replacement",
      "Pipework installation & modifications",
      "HIU installation / servicing / repairs",
      "Pressurisation units",
      "Expansion vessels",
      "Leak detection & repairs",
      "System balancing",
      "Powerflushing / system cleaning",
      "General mechanical maintenance",
    ],
    domestic: [
      "Heating system installation / upgrades",
      "Radiators / valves / TRVs",
      "Pumps & motorised valves",
      "Pipework repairs / alterations",
      "Leaks & water issues",
      "Cylinders / hot water systems",
      "Unvented cylinder works (G3)",
      "Powerflushing",
      "General plumbing & heating repair",
    ],
  },
  electrical: {
    commercial: [
      "Electrical fault finding (heating related)",
      "Controls wiring & diagnostics",
      "Programmer / thermostat replacement",
      "Pumps / valves electrical testing",
      "Isolation & safety checks",
      "Emergency electrical diagnostics (M&E related)",
    ],
    domestic: [
      "Heating controls fault finding",
      "Thermostat / programmer replacement",
      "Wiring centre diagnostics",
      "Electrical checks related to heating systems (EICR certification)",
    ],
  },
  gas: {
    commercial: [
      "Commercial boiler installation & replacement",
      "Commercial boiler servicing",
      "Commercial boiler repairs & fault finding",
      "Gas safety inspections",
      "Flue & ventilation checks",
      "Tightness testing & purging",
      "Gas pipework installation / modification",
      "Plant room maintenance",
      "Emergency breakdowns",
      "Preventative planned maintenance (PPM)",
      "Gas rate / combustion analysis",
      "System upgrades & efficiency improvements",
    ],
    domestic: [
      "Boiler installation & replacement",
      "Boiler servicing",
      "Boiler repairs & breakdowns",
      "Landlord Gas Safety Certificates (CP12)",
      "Gas safety checks",
      "Gas leaks / emergency response",
      "Gas hob / cooker installation",
      "Flue & ventilation checks",
      "System upgrades",
    ],
  },
};

/** Key strengths for Capability section. */
export const KEY_STRENGTHS = [
  "24/7 responsive service capability",
  "Strong Health & Safety culture with rigorous compliance standards",
  "Client-focused delivery approach",
  "Bespoke solutions tailored to project requirements",
  "Reliable project management and clear communication",
  "Commitment to quality workmanship and regulatory compliance",
] as const

/** Sectors served for Capability section. */
export const SECTORS_SERVED = [
  "Residential",
  "Commercial premises",
  "Landlords and property management companies",
  "Corporate clients",
] as const

/** Industries we work with — homepage "Sectors We Deal With" section. */
export const SECTORS_WE_DEAL_WITH = [
  "Universities",
  "Fire Stations",
  "Hospital",
  "Offices",
  "Retail",
  "Hospitality",
  "Warehouses",
  "Schools",
  "Estate Agents (Rented Properties)",
  "Facilities Management (Properties Managed)",
] as const

/** Sectors with hero images for the homepage grid (remaining sectors shown as pills). */
export const SECTORS_WITH_IMAGES = [
  { label: "Warehouses", image: "/images/sectors/warehouse.png" },
  { label: "Offices", image: "/images/sectors/office.png" },
  { label: "Hospital", image: "/images/sectors/hospital.png" },
  { label: "Universities", image: "/images/sectors/university.png" },
  { label: "Fire Stations", image: "/images/sectors/fire-station.png" },
] as const

/** Health & Safety paragraph for Capability section. */
export const HEALTH_SAFETY_COPY =
  "Health & Safety is central to our operations. We maintain stringent quality control procedures and ensure all works are carried out in accordance with current legislation, industry regulations, and best practice standards. Risk assessments and method statements (RAMS) are prepared where required to ensure safe and controlled project delivery."

/** Commitment paragraph for Capability section. */
export const COMMITMENT_COPY =
  "DPS Heating Services Ltd is committed to delivering dependable, high-quality engineering services with professionalism and attention to detail. Our clients take precedence in every project we undertake, and we aim to build long-term partnerships based on trust, performance, and reliability."

/** Accreditations and qualifications for About page and footer. */
export const ACCREDITATIONS = [
  { title: "Gas Safe Certification", items: ["Commercial & Domestic"] },
  {
    title: "Qualifications",
    items: [
      "COCN1",
      "NDNG1 (Non-Domestic Natural Gas)",
      "SENWAT",
      "HWSS G3 (Hot Water System and Safety / Unvented)",
      "Level 3 Energy Efficiency — Gas Fired & Oil-Fired Domestic Heating and Hot Water Systems",
    ],
  },
  { title: "Safe Contractor", items: [] },
  { title: "Health & Safety", items: ["Compliant — operatives trained and H&S aware"] },
  { title: "Asbestos Awareness", items: [] },
  { title: "Working at Heights", items: [] },
] as const

/** Commercial services (9 items) for services hub and nav. */
export const COMMERCIAL_SERVICES = [
  { label: "Commercial Boiler Servicing", href: "/services/heating/boiler-servicing" },
  { label: "Plant Room Maintenance", href: "/services/commercial" },
  { label: "Gas Safety Inspections", href: "/services/commercial" },
  { label: "PPM Contracts", href: "/services/commercial" },
  { label: "Fault Finding & Diagnosis", href: "/services/heating/boiler-repair" },
  { label: "Commercial Heating Systems", href: "/services/heating/central-heating" },
  { label: "24 Hour Emergency Breakdowns", href: "/emergency" },
  { label: "Commercial Facilities Management (3 Tier PPM Packages)", href: "/services/commercial" },
  { label: "Commercial Facilities Management (Reactive & OOH Callouts)", href: "/services/commercial" },
] as const

/** Domestic services (5 items) for services hub and nav. */
export const DOMESTIC_SERVICES = [
  { label: "Boiler Installation, Servicing & Repairs", href: "/services/heating/boiler-installation" },
  { label: "System Diagnosis", href: "/services/heating/boiler-repair" },
  { label: "Landlord Gas Safety Certification (CP12)", href: "/services/heating/boiler-servicing" },
  { label: "Plumbing Repairs", href: "/services/plumbing/plumbing-repairs" },
  { label: "Emergency Call outs", href: "/emergency" },
] as const

export const REVIEWS = [
  {
    name: "Alloush",
    service: "Leaking pipe behind water tank · Walworth, London",
    rating: 5,
    quote:
      "Excellent service. Turned up on time, assessed the issue quickly, and sorted the problem on the spot until a full fix starts.",
  },
  {
    name: "Benjamin Jarman",
    service: "Replacement of two immersion heater elements · Deptford, London",
    rating: 5,
    quote:
      "Dominic arranged at short notice to replace two immersion heater elements in a hot water tank. Courteous and communicated clearly throughout. Identified a separate issue previously undiagnosed by another tradesman, explained it clearly, and recommended who could do that work. I would definitely use him again.",
  },
  {
    name: "Sally D.",
    service: "Loud whistling from kitchen tap · Upper Edmonton, London",
    rating: 5,
    quote:
      "Quick, punctual, helpful, very tidy workmanship, and reasonably priced. Would not hesitate to recommend or use again.",
  },
  {
    name: "Bhavesh",
    service: "Loud foghorn sound when flushing toilet · Finchley Church End, London",
    rating: 5,
    quote:
      "Great job. Good communication from the time of shortlisting, with clear information and costs. Job completed swiftly and to a high standard. Dom was personable, courteous, and professional. I will use his services again.",
  },
  {
    name: "Max",
    service: "Bathroom leaks and ensuite renovation · Southfields, London",
    rating: 5,
    quote:
      "Absolutely superb. Dom is now my go-to plumber. Completed the bathroom leak job; responsive, friendly, and professional. I plan a bigger ensuite renovation project with him and praise his professionalism and expertise.",
  },
  {
    name: "Rhiannon",
    service: "Non-flushing toilet cistern · Southwark, London",
    rating: 5,
    quote:
      "Fixed quickly. Toilet now flushes fine. Very good communication about arrival time and arrived on time.",
  },
  {
    name: "J. M. S.",
    service: "Leak investigation — bathroom / immersion heater · Dalston, London",
    rating: 5,
    quote:
      "Great service. Responded very quickly before and after coming out, came out straight away, and was clear and transparent about what the job required. Lovely to deal with; I would definitely recommend and hire again.",
  },
  {
    name: "Amina",
    service: "Radiator repair · Manor Park, London",
    rating: 5,
    quote:
      "Excellent service — fast, friendly, and professional. Came back another day to fit smoke alarms as well. Thanks Dom.",
  },
  {
    name: "Elizabeth",
    service: "Leaking boiler · Bromley By Bow, London",
    rating: 5,
    quote:
      "Dom came quickly and diagnosed the source of the leak rapidly and cheerfully. It turned out to be something different and the responsibility of building management, so he didn't fix it this time — but this was not due to lack of expertise and I would definitely invite him back for future plumbing work.",
  },
  {
    name: "Johann",
    service: "Banging pipes, water turned off · Rotherhithe, London",
    rating: 5,
    quote:
      "Dom turned up within minutes, diagnosed the problem, got a part, and sorted it within a couple of hours. Beautiful!",
  },
  {
    name: "Ashley",
    service: "Three radiators fitted · Upper Norwood, London",
    rating: 5,
    quote:
      "Great job, found solutions to problems during the work. Would not hesitate to use again and highly recommend.",
  },
  {
    name: "M. J. Bri",
    service: "Radiator half off wall · Streatham Hill, London",
    rating: 5,
    quote:
      "Prompt, very professional, and helpful not just on this job but other issues around the house. Certified gas engineer who gave valuable boiler advice. I would definitely recommend.",
  },
  {
    name: "Christine",
    service: "Boiler repair · Shadwell, London",
    rating: 5,
    quote:
      "Dominic was fantastic. Replied quickly, came at agreed time, and fixed the issue. I am very happy and would use him again. A great service!",
  },
  {
    name: "Sophia",
    service: "Whistling noise in the bathroom · Rotherhithe, London",
    rating: 5,
    quote:
      "Very professional, knew exactly where the issue came from, fixed it quickly. Went the extra mile and was accommodating. I would definitely use again and highly recommend him.",
  },
  {
    name: "Arash",
    service: "Washing machine replacement installation · Epsom",
    rating: 5,
    quote:
      "Dom responded very quickly and completed the job the same day. Fair quote and high-quality service. He also fixed a sink leak free of charge. Strong recommendation.",
  },
  {
    name: "U. B.",
    service: "Suspected leaking pipe in bathroom · Southwark, London",
    rating: 5,
    quote:
      "Dominic attended late afternoon on one of the hottest days, identified the fault within seconds, went to buy the part, fitted, tested, and cleaned up professionally. Knowledgeable and highly trustworthy. Highly recommended.",
  },
  {
    name: "Miles",
    service: "Leaking shower valve replacement · Highbury, London",
    rating: 5,
    quote:
      "Dominic was very helpful when an easy fix became a nightmare. Went above and beyond, including driving to a supplier for a replacement part, and completed the job quickly.",
  },
  {
    name: "Akbar",
    service: "Leaking pipe beneath boiler · Bromley By Bow, London",
    rating: 5,
    quote:
      "Quick and efficient, arrived within the hour and fixed leak within minutes. Didn't charge for a washer part that was replaced. I would definitely use again.",
  },
  {
    name: "Olu",
    service: "Leaking radiator · Peckham, London",
    rating: 5,
    quote:
      "Very polite, professional, and able to go over and fix the issue at very short notice on a Sunday. Also gave advice regarding the council. I would definitely recommend.",
  },
  {
    name: "Coeur de Lion",
    service: "Emergency repair rising main · Peckham, London",
    rating: 5,
    quote:
      "Emergency leak in basement with over a foot of water. Dom arrived in under an hour, fixed leak and pumped water, while keeping me updated by phone. Patient and professional conduct in a sensitive situation. Strong praise.",
  },
]

export const PORTFOLIO_PROJECTS = [
  {
    title: "Commercial Boiler Plant Room",
    category: "Heating",
    location: "Westminster",
    description:
      "Full plant room installation for a commercial office building. Two high-efficiency cascade boilers, header system, and building management integration — completed on schedule with zero disruption to tenants.",
    image: "/images/bb694770-ebf9-4854-877f-46073a4e9746.jpg",
    stats: [
      { label: "Boilers", value: "2" },
      { label: "Floors Served", value: "6" },
    ],
  },
  {
    title: "Immersion Heater & Leak Repair",
    category: "Plumbing",
    location: "Walworth, London",
    description:
      "Leaking pipe behind water tank for immersion heater. Assessed on arrival, temporary fix applied on the spot, then full repair completed. Customer praised punctuality and clear communication.",
    image: "/images/plumbing-pipes.jpg",
    stats: [
      { label: "Response", value: "On time" },
      { label: "Fix", value: "Same visit" },
    ],
  },
  {
    title: "Dual Immersion Heater Element Replacement",
    category: "Heating",
    location: "Deptford, London",
    description:
      "Short-notice replacement of two immersion heater elements in a hot water tank. Identified an additional fault missed by a previous tradesman and advised on next steps. Flexible scheduling and clear communication throughout.",
    image: "/images/central-heating.jpg",
    stats: [
      { label: "Elements", value: "2" },
      { label: "Booking", value: "Short notice" },
    ],
  },
  // {
  //   title: "Kitchen Tap Whistle & Vibration Fix",
  //   category: "Plumbing",
  //   location: "Upper Edmonton, London",
  //   description:
  //     "Diagnosed and resolved loud whistling and vibration from kitchen tap. Tidy workmanship, competitive pricing, and minimal disruption. Customer would not hesitate to recommend or use again.",
  //   image: "/images/kitchen-plumbing.jpg",
  //   stats: [
  //     { label: "Issue", value: "Tap noise" },
  //     { label: "Result", value: "Fully resolved" },
  //   ],
  // },
  {
    title: "Victorian Terrace Central Heating",
    category: "Heating",
    location: "Clapham",
    description:
      "Complete central heating installation in a period property. New combi boiler, 12 radiators, and smart thermostat — fitted with minimal disruption to original features.",
    image: "/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg",
    stats: [
      { label: "Radiators", value: "12" },
      { label: "Duration", value: "2 days" },
    ],
  },
  // {
  //   title: "Toilet Cistern Foghorn Noise",
  //   category: "Plumbing",
  //   location: "Finchley Church End, London",
  //   description:
  //     "Loud foghorn sound when flushing toilet — diagnosed and fixed with clear communication from quote to completion. Swift, high-standard finish. Customer described service as personable, courteous, and professional.",
  //   image: "/images/plumbing-repairs.jpg",
  //   stats: [
  //     { label: "Diagnosis", value: "Same day" },
  //     { label: "Standard", value: "High" },
  //   ],
  // },
  {
    title: "Bathroom Leaks & Ensuite Renovation Prep",
    category: "Plumbing",
    location: "Southfields, London",
    description:
      "Bathroom leak investigation and repair; client now uses us as their go-to plumber. Responsive, friendly, and professional. Larger ensuite renovation project planned with same team.",
    image: "/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg",
    stats: [
      { label: "Scope", value: "Leaks + prep" },
      { label: "Follow-up", value: "Ensuite planned" },
    ],
  },
  // {
  //   title: "Non-Flushing Cistern Repair",
  //   category: "Plumbing",
  //   location: "Southwark, London",
  //   description:
  //     "Non-flushing toilet cistern repaired quickly. Clear communication on arrival time, punctual attendance, and toilet flushing correctly after repair.",
  //   image: "/images/plumbing-repairs.jpg",
  //   stats: [
  //     { label: "Speed", value: "Fast" },
  //     { label: "Communication", value: "Clear" },
  //   ],
  // },
  {
    title: "Leak Investigation — Bathroom & Immersion",
    category: "Plumbing",
    location: "Dalston, London",
    description:
      "Rapid response to leak investigation. Attended straight away, transparent about work required, and left customer happy to recommend and hire again.",
    image: "/images/plumbing-pipes.jpg",
    stats: [
      { label: "Response", value: "Same day" },
      { label: "Outcome", value: "Resolved" },
    ],
  },
  {
    title: "Radiator Repair & Smoke Alarms",
    category: "Heating",
    location: "Manor Park, London",
    description:
      "Radiator repair carried out to a high standard. Return visit to fit smoke alarms as requested. Fast, friendly, and professional throughout.",
    image: "/images/central-heating.jpg",
    stats: [
      { label: "Radiators", value: "Repaired" },
      { label: "Extras", value: "Smoke alarms" },
    ],
  },
  {
    title: "Emergency Boiler Replacement",
    category: "Heating",
    location: "Wandsworth",
    description:
      "Same-day callout for a failed boiler in a family home. Old unit removed and new combi fitted, tested, and commissioned within 8 hours.",
    image: "/images/de580d83-e113-4fa5-8635-779e1377cae6.jpg",
    stats: [
      { label: "Response", value: "2 hrs" },
      { label: "Completed", value: "Same day" },
    ],
  },
  {
    title: "Banging Pipes & Emergency Shut-Off",
    category: "Plumbing",
    location: "Rotherhithe, London",
    description:
      "Customer had to turn water off due to banging pipes. Attended within minutes, diagnosed the fault, sourced the part, and had the system sorted within a couple of hours.",
    image: "/images/plumbing-pipes.jpg",
    stats: [
      { label: "Arrival", value: "Minutes" },
      { label: "Completion", value: "2 hours" },
    ],
  },
  {
    title: "Three Radiators Fitted",
    category: "Heating",
    location: "Upper Norwood, London",
    description:
      "Three new radiators installed. Solutions found for problems that arose during the work. Customer would not hesitate to use again and highly recommends.",
    image: "/images/central-heating.jpg",
    stats: [
      { label: "Radiators", value: "3" },
      { label: "Approach", value: "Problem-solving" },
    ],
  },
  {
    title: "Radiator Reattachment & Boiler Advice",
    category: "Heating",
    location: "Streatham Hill, London",
    description:
      "Radiator half off wall — prompt, professional fix. Also gave advice on other household issues and valuable boiler guidance as a certified gas engineer. Customer would definitely recommend.",
    image: "/images/radiator-pipes.png",
    stats: [
      { label: "Radiator", value: "Reattached" },
      { label: "Advice", value: "Boiler + general" },
    ],
  },
  {
    title: "Leaking Boiler Diagnosis",
    category: "Heating",
    location: "Bromley By Bow, London",
    description:
      "Rapid attendance and diagnosis of leaking boiler. Source of leak identified quickly; issue was building-management responsibility on this occasion. Customer would definitely invite us back for future plumbing work.",
    image: "/images/boiler-repair.jpg",
    stats: [
      { label: "Response", value: "Quick" },
      { label: "Diagnosis", value: "Accurate" },
    ],
  },
  {
    title: "Boiler Repair",
    category: "Heating",
    location: "Shadwell, London",
    description:
      "Quick reply and attendance at agreed time. Boiler issue fixed to customer’s satisfaction. Customer very happy and would use again — described as a great service.",
    image: "/images/boiler-repair.jpg",
    stats: [
      { label: "Communication", value: "Quick" },
      { label: "Outcome", value: "Fixed" },
    ],
  },
  // {
  //   title: "Leaking Tap Repair",
  //   category: "Plumbing",
  //   location: "Peckham, London",
  //   description:
  //     "Leaking tap repaired to a high standard. Customer would recommend.",
  //   image: "/images/kitchen-plumbing.jpg",
  //   stats: [
  //     { label: "Job", value: "Tap repair" },
  //     { label: "Recommend", value: "Yes" },
  //   ],
  // },
  // {
  //   title: "Bathroom Whistling Noise",
  //   category: "Plumbing",
  //   location: "Rotherhithe, London",
  //   description:
  //     "Whistling noise in bathroom — issue located and fixed quickly. Went the extra mile and was accommodating. Customer would definitely use again and highly recommends.",
  //   image: "/images/plumbing-repairs.jpg",
  //   stats: [
  //     { label: "Diagnosis", value: "Precise" },
  //     { label: "Service", value: "Extra mile" },
  //   ],
  // },
  // {
  //   title: "Washing Machine Installation & Sink Leak",
  //   category: "Plumbing",
  //   location: "Epsom",
  //   description:
  //     "Rapid response and same-day completion of washing machine replacement installation. Fair quote and high-quality work. Sink leak fixed free of charge. Strong recommendation from customer.",
  //   image: "/images/kitchen-plumbing.jpg",
  //   stats: [
  //     { label: "Completion", value: "Same day" },
  //     { label: "Extra", value: "Sink leak (FOC)" },
  //   ],
  // },
  {
    title: "Suspected Leaking Pipe in Bathroom",
    category: "Plumbing",
    location: "Southwark, London",
    description:
      "Late-afternoon call on a very hot day. Fault identified within seconds; part purchased, fitted, tested, and area cleaned up professionally. Customer described as knowledgeable and highly trustworthy.",
    image: "/images/plumbing-pipes.jpg",
    stats: [
      { label: "Diagnosis", value: "Seconds" },
      { label: "Clean-up", value: "Included" },
    ],
  },
  {
    title: "Concealed Shower Valve Replacement",
    category: "Plumbing",
    location: "Highbury, London",
    description:
      "Leaking Zyam 3/4\" concealed shower valve. What started as a simple fix became more complex; we went above and beyond, including a trip to a supplier for a replacement part, and completed the job quickly.",
    image: "/images/plumbing-repairs.jpg",
    stats: [
      { label: "Complexity", value: "Above & beyond" },
      { label: "Result", value: "Completed" },
    ],
  },
  {
    title: "Leaking Pipe Beneath Boiler",
    category: "Heating",
    location: "Bromley By Bow, London",
    description:
      "Arrived within the hour and fixed the leak in minutes. Small washer replacement not charged. Customer would definitely use again.",
    image: "/images/boiler-repair.jpg",
    stats: [
      { label: "Response", value: "< 1 hour" },
      { label: "Fix", value: "Minutes" },
    ],
  },
  {
    title: "Leaking Radiator — Sunday Callout",
    category: "Heating",
    location: "Peckham, London",
    description:
      "Very short notice on a Sunday. Polite, professional, and issue fixed. Also provided advice regarding the council. Customer would definitely recommend.",
    image: "/images/central-heating.jpg",
    stats: [
      { label: "Notice", value: "Short (Sunday)" },
      { label: "Manner", value: "Polite & pro" },
    ],
  },
  {
    title: "Faulty Heating System",
    category: "Heating",
    location: "Rotherhithe, London",
    description:
      "Friendly, helpful, and flexible when customer had to rearrange due to work. Boiler issues explained clearly; prompt and efficient. Good service received.",
    image: "/images/boiler-modern.jpg",
    stats: [
      { label: "Flexibility", value: "Rearranged" },
      { label: "Explanation", value: "Clear" },
    ],
  },
  {
    title: "Emergency Rising Main — Basement Flood",
    category: "Plumbing",
    location: "Peckham, London",
    description:
      "Emergency leak in basement with over a foot of water. Arrived in under an hour, fixed the leak and pumped water, with updates by phone throughout. Patient and professional in a sensitive situation.",
    image: "/images/emergency-callout.jpg",
    stats: [
      { label: "Response", value: "< 1 hour" },
      { label: "Situation", value: "Emergency flood" },
    ],
  },
]
