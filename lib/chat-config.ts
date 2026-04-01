import { COMPANY } from "@/lib/constants";

export interface ServicePriceRange {
  domestic: [number, number];
  commercial: [number, number];
}

export interface ServiceItem {
  slug: string;
  label: string;
  href: string;
  priceRange: ServicePriceRange;
}

export interface ServiceCategory {
  slug: string;
  label: string;
  href: string;
  services: ServiceItem[];
}

export const SERVICE_MAP: Record<string, ServiceCategory> = {
  mechanical: {
    slug: "mechanical",
    label: "Mechanical",
    href: "/services/mechanical",
    services: [
      { slug: "mechanical-commercial", label: "Commercial Mechanical Services", href: "/services/mechanical", priceRange: { domestic: [0, 0], commercial: [150, 12000] } },
      { slug: "mechanical-domestic", label: "Domestic Mechanical Services", href: "/services/mechanical", priceRange: { domestic: [80, 5000], commercial: [0, 0] } },
      { slug: "central-heating", label: "Central Heating", href: "/services/mechanical", priceRange: { domestic: [2000, 5000], commercial: [4000, 12000] } },
      { slug: "power-flushing", label: "Power Flushing", href: "/services/mechanical", priceRange: { domestic: [180, 450], commercial: [280, 900] } },
    ],
  },
  plumbing: {
    slug: "plumbing",
    label: "Plumbing",
    href: "/services/plumbing",
    services: [
      { slug: "plumbing-commercial", label: "Commercial Plumbing Services", href: "/services/plumbing", priceRange: { domestic: [0, 0], commercial: [120, 1500] } },
      { slug: "plumbing-domestic", label: "Domestic Plumbing Services", href: "/services/plumbing", priceRange: { domestic: [80, 750], commercial: [0, 0] } },
      { slug: "general-plumbing", label: "General Plumbing", href: "/services/plumbing/general-plumbing", priceRange: { domestic: [80, 450], commercial: [120, 700] } },
      { slug: "plumbing-repairs", label: "Plumbing Repairs", href: "/services/plumbing/plumbing-repairs", priceRange: { domestic: [80, 400], commercial: [120, 600] } },
    ],
  },
  electrical: {
    slug: "electrical",
    label: "Electrical",
    href: "/services/electrical",
    services: [
      { slug: "electrical-commercial", label: "Commercial Electrical Services", href: "/services/electrical", priceRange: { domestic: [0, 0], commercial: [120, 2000] } },
      { slug: "electrical-domestic", label: "Domestic Electrical Services", href: "/services/electrical", priceRange: { domestic: [80, 900], commercial: [0, 0] } },
      { slug: "fault-finding-diagnosis", label: "Fault Finding & Diagnosis", href: "/services/electrical", priceRange: { domestic: [80, 350], commercial: [120, 500] } },
    ],
  },
  gas: {
    slug: "gas",
    label: "Gas",
    href: "/services/gas",
    services: [
      { slug: "gas-commercial", label: "Commercial Gas Services", href: "/services/gas", priceRange: { domestic: [0, 0], commercial: [100, 3000] } },
      { slug: "gas-domestic", label: "Domestic Gas Services", href: "/services/gas", priceRange: { domestic: [70, 1500], commercial: [0, 0] } },
      { slug: "boiler-installation", label: "Boiler Installation", href: "/services/gas", priceRange: { domestic: [1800, 3500], commercial: [3500, 7000] } },
      { slug: "boiler-servicing", label: "Boiler Servicing", href: "/services/gas", priceRange: { domestic: [70, 120], commercial: [100, 180] } },
      { slug: "boiler-repair", label: "Boiler Repair", href: "/services/gas", priceRange: { domestic: [80, 350], commercial: [120, 600] } },
      { slug: "emergency-callouts", label: "Emergency Call outs", href: "/emergency", priceRange: { domestic: [80, 350], commercial: [120, 600] } },
    ],
  },
};

export const URGENCY_MULTIPLIER = {
  standard: 1.0,
  urgent: 1.3,
  emergency: 1.6,
} as const;

export const QUICK_ACTIONS = [
  { label: "Get a Quote", href: "/contact" },
  { label: "Our Services", href: "/services" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Call Us", href: `tel:${COMPANY.phone}` },
] as const;
