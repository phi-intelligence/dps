export const OPENING_HOURS = {
  weekday: "08:00 - 18:00",
  saturday: "09:00 - 13:00",
  sunday: "Closed",
};

export const COMPANY = {
  name: "DPS Heating Services LTD",
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
  industryExperience: "over 10 years",
  mission: "To deliver reliable, compliant mechanical, electrical, and gas solutions with discipline, integrity, and reliability — putting our clients first, 24 hours a day, 7 days a week.",
  vision: "To be the trusted choice for commercial and domestic engineering services across London and the Southeast, known for exceptional workmanship, clear communication, and long-term partnerships built on trust.",
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
  { label: "About Us", href: "/about" },
  { label: "Portfolio", href: "/portfolio" },
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
  "Electrical Services": "/images/core-services/electrical.png",
  "Gas Services": "/images/core-services/gas.png",
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
      "Plant room installations and maintenance",
      "Commercial heating system installation and upgrades",
      "PPM contracts and planned maintenance",
      "Pipework systems and distribution",
      "Preventative and reactive maintenance",
      "Commercial facilities management (PPM packages)",
      "24-hour emergency breakdowns",
      "Fault finding and diagnosis",
    ],
    domestic: [
      "Heating system installation and upgrades",
      "Radiator and pipework installation and repairs",
      "Preventative maintenance and servicing",
      "Reactive repairs and fault finding",
      "System upgrades and efficiency improvements",
    ],
  },
  electrical: {
    commercial: [
      "Electrical installations and upgrades (commercial)",
      "Fault finding and testing",
      "Compliance inspections and certification",
      "Maintenance contracts and PPM",
      "Distribution and distribution boards",
      "Emergency lighting and testing",
    ],
    domestic: [
      "Electrical installations and upgrades (domestic)",
      "Fault finding and testing",
      "Landlord electrical safety inspections",
      "Consumer unit upgrades",
      "Maintenance and reactive repairs",
    ],
  },
  gas: {
    commercial: [
      "Commercial gas installation and servicing",
      "Gas safety inspections (commercial)",
      "Commercial boiler servicing and repair",
      "PPM and planned gas maintenance",
      "24-hour emergency gas callouts",
    ],
    domestic: [
      "Gas installation and servicing",
      "Landlord gas safety certification (CP12)",
      "Boiler installation, servicing and repairs",
      "System diagnosis and repair",
      "Emergency gas callouts",
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
    name: "James T.",
    service: "Boiler Repair",
    rating: 5,
    quote:
      "Brilliant service from start to finish. Engineer arrived on time, diagnosed the fault quickly, and had it fixed within the hour. Highly recommended.",
  },
  {
    name: "Sarah M.",
    service: "Boiler Installation",
    rating: 5,
    quote:
      "Had a new combi boiler installed last month. The team were professional, tidy, and explained everything clearly. Great value for money.",
  },
  {
    name: "David P.",
    service: "Boiler Servicing",
    rating: 5,
    quote:
      "Annual boiler service carried out efficiently and professionally. Engineer was friendly, thorough, and explained exactly what was checked. Will definitely use again.",
  },
  {
    name: "Emily R.",
    service: "AC Installation",
    rating: 5,
    quote:
      "Had a split system installed in our home office. The team were incredibly neat and finished ahead of schedule. The room is now perfectly cool all summer. Couldn't be happier.",
  },
  {
    name: "Mark H.",
    service: "Central Heating",
    rating: 5,
    quote:
      "Complete central heating system installed in our Victorian terrace. Pipework was routed cleanly, radiators balanced perfectly. House is warm throughout for the first time in years.",
  },
  {
    name: "Lisa W.",
    service: "Commercial AC",
    rating: 5,
    quote:
      "DPS installed a multi-zone system across our office floors. Minimal disruption to our staff, and the ongoing maintenance contract gives us total peace of mind.",
  },
  // TODO: Replace with real customer reviews
]

export const PORTFOLIO_PROJECTS = [
  {
    title: "Commercial Boiler Plant Room",
    category: "Heating",
    location: "Westminster",
    description:
      "Full plant room installation for a commercial office building. Two high-efficiency cascade boilers, header system, and building management integration.",
    image: "/images/bb694770-ebf9-4854-877f-46073a4e9746.jpg",
    stats: [
      { label: "Boilers", value: "2" },
      { label: "Floors Served", value: "6" },
    ],
  },
  {
    title: "Victorian Terrace Central Heating",
    category: "Heating",
    location: "Clapham",
    description:
      "Complete central heating installation in a period property. New combi boiler, 12 radiators, and smart thermostat — fitted with minimal disruption to original features.",
    image: "/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg",
    stats: [
      { label: "Radiators", value: "12" },
      { label: "Duration", value: "4 days" },
    ],
  },
  {
    title: "Commercial Plumbing & Plant Room",
    category: "Plumbing",
    location: "Chelsea",
    description:
      "Full commercial plumbing installation for an office building. New plant room, mains distribution, and bathroom fit-outs across three floors.",
    image: "/images/plumbing-pipes.jpg",
    stats: [
      { label: "Floors", value: "3" },
      { label: "Fittings", value: "24" },
    ],
  },
  {
    title: "Emergency Boiler Replacement",
    category: "Heating",
    location: "Wandsworth",
    description:
      "Same-day callout for a failed boiler in a family home. Old unit removed and new Worcester Bosch combi fitted, tested, and commissioned within 8 hours.",
    image: "/images/de580d83-e113-4fa5-8635-779e1377cae6.jpg",
    stats: [
      { label: "Response", value: "2 hrs" },
      { label: "Completed", value: "Same day" },
    ],
  },
  {
    title: "Bathroom & Kitchen Plumbing",
    category: "Plumbing",
    location: "Richmond",
    description:
      "Complete bathroom and kitchen plumbing refurbishment. New pipework, sanitaryware connections, and appliance installations in a period property.",
    image: "/images/kitchen-plumbing.jpg",
    stats: [
      { label: "Rooms", value: "2" },
      { label: "Duration", value: "3 days" },
    ],
  },
  {
    title: "Power Flush & System Upgrade",
    category: "Heating",
    location: "Battersea",
    description:
      "Full system power flush followed by new thermostatic radiator valves throughout. Restored heat output and reduced energy bills by an estimated 15%.",
    image: "/images/central-heating.jpg",
    stats: [
      { label: "Radiators", value: "10" },
      { label: "Savings", value: "~15%" },
    ],
  },
  // TODO: Replace with real project data
]
