import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";
import ServiceAudienceTabs from "@/components/sections/ServiceAudienceTabs";

const COMMERCIAL_PLUMBING_CARDS = [
  {
    title: "Commercial plumbing installation",
    description: "Planned plumbing installations for commercial buildings, estates, and managed properties.",
    image: "/imagesv2/commercial_plumbing/commercial_plumbing.jpg",
    imageAlt: "Commercial plumbing installation",
  },
  {
    title: "Commercial plumbing repairs",
    description: "Fast fault diagnosis and repairs for leaks, failed fixtures, and damaged plumbing components.",
    image: "/imagesv2/commercial_plumbing/plumbing%20repair.jpeg",
    imageAlt: "Commercial plumbing repairs",
  },
  {
    title: "Pipework upgrades and alterations",
    description: "Pipe reroutes, upgrades, and distribution changes for changing commercial layouts and demand.",
    image: "/imagesv2/commercial_plumbing/Pipework%20upgrade.jpg",
    imageAlt: "Commercial pipework upgrades",
  },
  {
    title: "Leak detection and trace & access",
    description: "Targeted leak detection and remediation to reduce property impact and downtime.",
    image: "/imagesv2/commercial_plumbing/Leak%20detection.jpg",
    imageAlt: "Commercial leak tracing",
  },
  {
    title: "Valves, pumps and controls servicing",
    description: "Inspection and servicing of associated plumbing components to keep systems reliable.",
    image: "/imagesv2/commercial_plumbing/Valves%2C%20pumps%20and%20controls.jpg",
    imageAlt: "Commercial plumbing valves and pumps servicing",
  },
  {
    title: "Hot water and cylinder systems",
    description: "Commercial hot-water system and cylinder plumbing works, including repair and upgrade support.",
    image: "/imagesv2/commercial_plumbing/Hot%20water%20and%20cylinder%20systems.webp",
    imageAlt: "Commercial hot water and cylinder plumbing systems",
  },
  {
    title: "Planned preventative plumbing maintenance",
    description: "Scheduled preventative plumbing checks and servicing to reduce reactive failures.",
    image: "/imagesv2/commercial_plumbing/Planned%20preventative%20plumbing%20maintenance.jpg",
    imageAlt: "Commercial preventative plumbing maintenance",
  },
  {
    title: "Reactive callouts and emergency repairs",
    description: "Rapid commercial callout support for urgent plumbing faults and emergency situations.",
    image: "/imagesv2/commercial_plumbing/emergency-repairs.png",
    imageAlt: "Commercial plumbing emergency callouts",
  },
];

const DOMESTIC_PLUMBING_CARDS = [
  {
    title: "General plumbing repairs",
    description: "Everyday domestic plumbing repairs with prompt attendance and clear pricing.",
    image: "/imagesv2/domestic%20plumbing/General-Plumbing-Repair.webp",
    imageAlt: "General domestic plumbing repairs",
  },
  {
    title: "Tap, toilet and fixture installation",
    description: "Installation and replacement of taps, toilets, and fixtures across kitchen and bathroom spaces.",
    image: "/imagesv2/domestic%20plumbing/Tap_installation.jpeg",
    imageAlt: "Domestic fixtures installation",
  },
  {
    title: "Pipework repairs and reroutes",
    description: "Repairs and pipework changes to address wear, leaks, or renovation requirements.",
    image: "/imagesv2/domestic%20plumbing/Pipework%20repairs%20and%20reroutes.jpg",
    imageAlt: "Domestic pipework repairs",
  },
  {
    title: "Leak detection and repairs",
    description: "Leak tracing and durable repairs to prevent recurring water damage.",
    image: "/imagesv2/domestic%20plumbing/leak_detection.jpg",
    imageAlt: "Domestic leak detection",
  },
  {
    title: "Appliance plumbing connections",
    description: "Safe plumbing connections for appliances with checks on flow and drainage.",
    image: "/imagesv2/domestic%20plumbing/Appliance%20plumbing%20connections.jpg",
    imageAlt: "Domestic appliance plumbing connections",
  },
  {
    title: "Water pressure optimisation",
    description: "Diagnosis and adjustment works to improve domestic flow and water pressure performance.",
    image: "/imagesv2/domestic%20plumbing/Water%20pressure%20optimisation.webp",
    imageAlt: "Domestic water pressure optimisation",
  },
  {
    title: "Hot water cylinder plumbing works",
    description: "Domestic cylinder-associated plumbing repairs, upgrades, and system-side connections.",
    image: "/imagesv2/domestic%20plumbing/Hot_water.png",
    imageAlt: "Domestic hot water cylinder plumbing works",
  },
  {
    title: "Emergency domestic plumbing callouts",
    description: "Fast domestic response for urgent leaks, failures, and out-of-hours plumbing issues.",
    image: "/imagesv2/domestic%20plumbing/emergency-repairs.png",
    imageAlt: "Emergency domestic plumbing callouts",
  },
];

export const metadata: Metadata = {
  title: "Plumbing Services",
  description: `Commercial and domestic plumbing services including repairs, leak detection, pipework upgrades, and planned maintenance across ${COMPANY.areas}.`,
};

export default function PlumbingServicesPage() {
  const services = CORE_SERVICE_SECTOR_SERVICES.plumbing;

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Plumbing Services"
        subtitle={`Commercial and domestic plumbing services including repairs, leak detection, pipework upgrades, and planned maintenance across ${COMPANY.areas}.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Plumbing Services" },
        ]}
        backgroundImage="/imagesv2/domestic%20plumbing/General-Plumbing-Repair.webp"
        compact
      />
      <ServiceAudienceTabs
        commercialTitle="Commercial Plumbing Services"
        domesticTitle="Domestic Plumbing Services"
        commercialServices={services.commercial}
        domesticServices={services.domestic}
        commercialCards={COMMERCIAL_PLUMBING_CARDS}
        domesticCards={DOMESTIC_PLUMBING_CARDS}
      />
    </div>
  );
}
