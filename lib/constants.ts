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
  // TODO: Replace with real customer reviews
]
