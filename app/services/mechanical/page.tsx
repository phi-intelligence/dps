import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";
import ServiceAudienceTabs from "@/components/sections/ServiceAudienceTabs";

const COMMERCIAL_MECHANICAL_CARDS = [
  {
    title: "Heating system installation",
    description: "Full design, supply and installation of commercial heating systems tailored to building load and compliance needs.",
    image: "/imagesv2/commercial_mechanical/commercial_heating.webp",
    imageAlt: "Commercial heating system installation",
  },
  {
    title: "Heating system repairs",
    description: "Fast fault finding and repair for commercial heating systems to minimise downtime.",
    image: "/imagesv2/commercial_mechanical/commercial_heating_repair.jpg",
    imageAlt: "Commercial heating repairs",
  },
  {
    title: "Pumps, valves & controls replacement",
    description: "Replacement and commissioning of pumps, motorised valves, and controls for reliable operation.",
    image: "/imagesv2/commercial_mechanical/commercial_pump.jpg",
    imageAlt: "Commercial pumps and valves replacement",
  },
  {
    title: "Pipework installation & modifications",
    description: "New pipework runs and modifications to existing commercial systems completed to current standards.",
    image: "/imagesv2/commercial_mechanical/commercial_pipework.png",
    imageAlt: "Commercial pipework installation",
  },
  {
    title: "HIU installation / servicing / repairs",
    description: "Heat interface unit installation, servicing, and repairs with manufacturer-aligned maintenance.",
    image: "/imagesv2/commercial_mechanical/commercial_hiu.webp",
    imageAlt: "Commercial HIU services",
  },
  {
    title: "Pressurisation and expansion systems",
    description: "Installation and maintenance of pressurisation units and expansion vessels for stable sealed systems.",
    image: "/imagesv2/commercial_mechanical/commercial_pressure.jpg",
    imageAlt: "Commercial pressurisation systems",
  },
  {
    title: "Expansion vessels",
    description: "Sizing, installation, and replacement of expansion vessels for safe, efficient system operation.",
    image: "/imagesv2/commercial_mechanical/expansion_vessels.webp",
    imageAlt: "Commercial expansion vessel services",
  },
  {
    title: "Leak detection & repairs",
    description: "Systematic leak detection and durable repairs to protect assets and prevent recurrence.",
    image: "/imagesv2/commercial_mechanical/leak_detection.png",
    imageAlt: "Commercial leak detection and repair",
  },
  {
    title: "System balancing",
    description: "Hydronic balancing to achieve design flow rates and improve comfort and efficiency.",
    image: "/imagesv2/commercial_mechanical/system_balance.jpg",
    imageAlt: "Commercial system balancing",
  },
  {
    title: "Powerflushing / system cleaning",
    description: "Chemical cleaning and powerflushing to remove sludge and restore system performance.",
    image: "/imagesv2/commercial_mechanical/power_flushing.jpg",
    imageAlt: "Commercial powerflushing and system cleaning",
  },
  {
    title: "General mechanical maintenance",
    description: "Routine planned maintenance and minor repairs to keep commercial systems operating reliably.",
    image: "/imagesv2/commercial_mechanical/general.jpg",
    imageAlt: "Commercial mechanical maintenance",
  },
];

const DOMESTIC_MECHANICAL_CARDS = [
  {
    title: "Heating installation / upgrades",
    description: "New domestic heating systems and upgrades to improve comfort and efficiency.",
    image: "/imagesv2/domestic_mechanical/domestic_heating.jpg",
    imageAlt: "Domestic heating installation",
  },
  {
    title: "Radiators, valves and TRVs",
    description: "Supply and installation of radiators and control valves for balanced heat distribution.",
    image: "/imagesv2/domestic_mechanical/radiator.jpg",
    imageAlt: "Domestic radiators and valves",
  },
  {
    title: "Pumps & motorised valves",
    description: "Repair and replacement of pumps and motorised valves to restore system performance.",
    image: "/imagesv2/domestic_mechanical/domestic_pump.jpg",
    imageAlt: "Domestic pumps and motorised valves",
  },
  {
    title: "Pipework repairs / alterations",
    description: "Heating and plumbing pipework repairs and reroutes with minimal disruption.",
    image: "/imagesv2/domestic_mechanical/pipework.png",
    imageAlt: "Domestic pipework repairs",
  },
  {
    title: "Leaks & water issues",
    description: "Leak detection and repair for heating and plumbing systems with advice to prevent recurrence.",
    image: "/imagesv2/domestic_mechanical/domestic_leak.jpg",
    imageAlt: "Domestic leaks and water issues",
  },
  {
    title: "Cylinders / hot water systems",
    description: "Installation, repair, and replacement of hot water cylinders and associated pipework.",
    image: "/imagesv2/domestic_mechanical/domestic_hot_water.jpg",
    imageAlt: "Domestic cylinder and hot water systems",
  },
  {
    title: "Unvented cylinder works (G3)",
    description: "G3-qualified installation, servicing, and repairs for unvented hot water cylinders.",
    image: "/imagesv2/domestic_mechanical/unvented.jpg",
    imageAlt: "Domestic unvented cylinder works",
  },
  {
    title: "Powerflushing",
    description: "Sludge removal and system cleaning to improve heat output and protect components.",
    image: "/imagesv2/domestic_mechanical/power_flushing.jpg",
    imageAlt: "Domestic powerflushing service",
  },
  {
    title: "General plumbing & heating repair",
    description: "Routine domestic plumbing and heating repairs completed with clear communication and tidy workmanship.",
    image: "/imagesv2/domestic_mechanical/domestic_plumbing.jpg",
    imageAlt: "General domestic plumbing and heating repair",
  },
];

export const metadata: Metadata = {
  title: "Mechanical Services",
  description: `Heating systems, plant room installations, pipework, and preventative maintenance across ${COMPANY.areas}. Commercial and domestic mechanical engineering.`,
};

export default function MechanicalServicesPage() {
  const services = CORE_SERVICE_SECTOR_SERVICES.mechanical;

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Mechanical Services"
        subtitle={`Heating system installation, plant room installations, pipework, and preventative maintenance across ${COMPANY.areas}.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Mechanical Services" },
        ]}
        backgroundImage="/images/core-services/mechanical.png"
        compact
      />
      <ServiceAudienceTabs
        commercialTitle="Commercial Mechanical Services"
        domesticTitle="Domestic Mechanical Services"
        commercialServices={services.commercial}
        domesticServices={services.domestic}
        commercialCards={COMMERCIAL_MECHANICAL_CARDS}
        domesticCards={DOMESTIC_MECHANICAL_CARDS}
      />
    </div>
  );
}
