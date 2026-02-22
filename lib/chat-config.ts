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
  heating: {
    slug: "heating",
    label: "Heating",
    href: "/services/heating",
    services: [
      { slug: "boiler-repair", label: "Boiler Repair", href: "/services/heating/boiler-repair", priceRange: { domestic: [80, 350], commercial: [120, 500] } },
      { slug: "boiler-installation", label: "Boiler Installation", href: "/services/heating/boiler-installation", priceRange: { domestic: [1500, 3500], commercial: [2500, 6000] } },
      { slug: "boiler-servicing", label: "Boiler Servicing", href: "/services/heating/boiler-servicing", priceRange: { domestic: [70, 120], commercial: [100, 180] } },
      { slug: "central-heating", label: "Central Heating", href: "/services/heating/central-heating", priceRange: { domestic: [2000, 5000], commercial: [4000, 12000] } },
      { slug: "radiators", label: "Radiators", href: "/services/heating/radiators", priceRange: { domestic: [150, 800], commercial: [300, 2000] } },
      { slug: "power-flushing", label: "Power Flushing", href: "/services/heating/power-flushing", priceRange: { domestic: [300, 600], commercial: [500, 1000] } },
    ],
  },
  "air-conditioning": {
    slug: "air-conditioning",
    label: "Air Conditioning",
    href: "/services/air-conditioning",
    services: [
      { slug: "ac-installation", label: "AC Installation", href: "/services/air-conditioning/ac-installation", priceRange: { domestic: [1500, 4000], commercial: [3000, 15000] } },
      { slug: "ac-servicing", label: "AC Servicing", href: "/services/air-conditioning/ac-servicing", priceRange: { domestic: [80, 150], commercial: [120, 250] } },
      { slug: "ac-repairs", label: "AC Repairs", href: "/services/air-conditioning/ac-repairs", priceRange: { domestic: [80, 400], commercial: [120, 600] } },
      { slug: "commercial-ac", label: "Commercial AC", href: "/services/air-conditioning/commercial-ac", priceRange: { domestic: [0, 0], commercial: [5000, 25000] } },
      { slug: "ac-maintenance", label: "Maintenance Contracts", href: "/services/air-conditioning/ac-maintenance", priceRange: { domestic: [200, 500], commercial: [400, 1200] } },
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
