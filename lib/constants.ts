export const OPENING_HOURS = {
  weekday: "08:00 - 18:00",
  saturday: "09:00 - 13:00",
  sunday: "Closed",
};

export const COMPANY = {
  name: "DPS Heating Services Ltd",
  phone: "ADD_PHONE_NUMBER", // TODO: Replace with real phone number
  email: "ADD_EMAIL_ADDRESS", // TODO: Replace with real email
  address: "ADD_ADDRESS", // TODO: Replace with real address
  companyNumber: "ADD_COMPANY_NUMBER", // TODO: Replace with real company number
  gasSafeNumber: "ADD_GAS_SAFE_NUMBER", // TODO: Replace with real Gas Safe number
  areas: "London and Surrounding Areas", // TODO: Replace with real service areas
}

export const NAV_LINKS = [
  { label: "Home", href: "/" },
  {
    label: "Services",
    href: "/services",
    children: [
      { label: "Heating Services", href: "/services/heating" },
      { label: "Air Conditioning", href: "/services/air-conditioning" },
    ],
  },
  { label: "About Us", href: "/about" },
  { label: "Portfolio", href: "/portfolio" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Contact", href: "/contact" },
]

export const SERVICE_AREAS = [
  "London",
  "Westminster",
  "Chelsea",
  "Kensington",
  "Fulham",
  "Hammersmith",
  "Wandsworth",
  "Battersea",
  "Clapham",
  "Brixton",
  "Streatham",
  "Balham",
  "Tooting",
  "Wimbledon",
  "Kingston",
  "Richmond",
  "Twickenham",
  "Putney",
  "Southfields",
  "Earlsfield",
  // TODO: Replace with real service area names
]

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
    title: "Office AC Multi-Zone System",
    category: "Air Conditioning",
    location: "Chelsea",
    description:
      "Daikin VRF system across three open-plan office floors. Individual zone control for each department with centralised management and remote monitoring.",
    image: "/images/ac-installation.jpg",
    stats: [
      { label: "Zones", value: "8" },
      { label: "Brand", value: "Daikin" },
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
    title: "Residential Split AC",
    category: "Air Conditioning",
    location: "Richmond",
    description:
      "Mitsubishi Electric wall-mounted split system for a loft conversion. Quiet operation, Wi-Fi control, and energy-efficient inverter technology.",
    image: "/images/ac-unit-indoor.jpg",
    stats: [
      { label: "Brand", value: "Mitsubishi" },
      { label: "Duration", value: "1 day" },
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
