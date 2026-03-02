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
  commercial: {
    slug: "commercial",
    label: "Commercial",
    href: "/services/commercial",
    services: [
      { slug: "commercial-boiler-servicing", label: "Commercial Boiler Servicing", href: "/services/heating/boiler-servicing", priceRange: { domestic: [70, 120], commercial: [100, 180] } },
      { slug: "plant-room-maintenance", label: "Plant Room Maintenance", href: "/services/commercial", priceRange: { domestic: [0, 0], commercial: [150, 500] } },
      { slug: "gas-safety-inspections", label: "Gas Safety Inspections", href: "/services/commercial", priceRange: { domestic: [0, 0], commercial: [80, 200] } },
      { slug: "ppm-contracts", label: "PPM Contracts", href: "/services/commercial", priceRange: { domestic: [0, 0], commercial: [500, 3000] } },
      { slug: "fault-finding-diagnosis", label: "Fault Finding & Diagnosis", href: "/services/heating/boiler-repair", priceRange: { domestic: [80, 350], commercial: [120, 500] } },
      { slug: "commercial-heating-systems", label: "Commercial Heating Systems", href: "/services/heating/central-heating", priceRange: { domestic: [2000, 5000], commercial: [4000, 12000] } },
      { slug: "emergency-breakdowns", label: "24 Hour Emergency Breakdowns", href: "/emergency", priceRange: { domestic: [80, 350], commercial: [120, 600] } },
      { slug: "fm-ppm-packages", label: "Facilities Management (3 Tier PPM)", href: "/services/commercial", priceRange: { domestic: [0, 0], commercial: [800, 4000] } },
      { slug: "fm-reactive-ooh", label: "Facilities Management (Reactive & OOH)", href: "/services/commercial", priceRange: { domestic: [0, 0], commercial: [120, 600] } },
    ],
  },
  domestic: {
    slug: "domestic",
    label: "Domestic",
    href: "/services/domestic",
    services: [
      { slug: "boiler-installation-servicing-repairs", label: "Boiler Installation, Servicing & Repairs", href: "/services/heating/boiler-installation", priceRange: { domestic: [70, 3500], commercial: [100, 6000] } },
      { slug: "system-diagnosis", label: "System Diagnosis", href: "/services/heating/boiler-repair", priceRange: { domestic: [80, 350], commercial: [120, 500] } },
      { slug: "landlord-gas-safety-cp12", label: "Landlord Gas Safety (CP12)", href: "/services/heating/boiler-servicing", priceRange: { domestic: [60, 120], commercial: [80, 150] } },
      { slug: "plumbing-repairs", label: "Plumbing Repairs", href: "/services/plumbing/plumbing-repairs", priceRange: { domestic: [80, 400], commercial: [120, 600] } },
      { slug: "emergency-callouts", label: "Emergency Call outs", href: "/emergency", priceRange: { domestic: [80, 350], commercial: [120, 500] } },
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
