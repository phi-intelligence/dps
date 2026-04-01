import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";
import ServiceAudienceTabs from "@/components/sections/ServiceAudienceTabs";

const COMMERCIAL_GAS_CARDS = [
  {
    title: "Commercial boiler installation & replacement",
    description: "Full design, supply and installation of commercial gas boilers with full commissioning and handover.",
    image: "/imagesv2/commercial_gas/commercial_boiler.jpg",
    imageAlt: "Commercial gas boiler installation",
  },
  {
    title: "Commercial boiler servicing",
    description: "Scheduled servicing of commercial gas boilers to maintain efficiency, safety, and warranty compliance.",
    image: "/imagesv2/commercial_gas/commercial_repair.jpg",
    imageAlt: "Commercial boiler servicing",
  },
  {
    title: "Commercial boiler repairs & fault finding",
    description: "Fast diagnosis and repair of commercial boiler faults to restore heating and hot water quickly.",
    image: "/imagesv2/commercial_gas/commercial_install.jpg",
    imageAlt: "Commercial gas boiler repairs",
  },
  {
    title: "Gas safety inspections",
    description: "Thorough inspections with compliance-focused reporting for commercial premises.",
    image: "/imagesv2/commercial_gas/commercial_inspect.jpg",
    imageAlt: "Commercial gas safety inspections",
  },
  {
    title: "Flue & ventilation checks",
    description: "Flue integrity and ventilation checks for commercial appliances and plant rooms.",
    image: "/imagesv2/commercial_gas/commercial_flue.jpg",
    imageAlt: "Commercial flue and ventilation checks",
  },
  {
    title: "Tightness testing & purging",
    description: "Tightness testing and purging of gas installations to current standards.",
    image: "/imagesv2/commercial_gas/testing.jpeg",
    imageAlt: "Commercial gas tightness testing and purging",
  },
  {
    title: "Gas pipework installation / modification",
    description: "New gas pipework runs and modifications to existing installations by Gas Safe engineers.",
    image: "/imagesv2/commercial_gas/pipework.webp",
    imageAlt: "Commercial gas pipework installation",
  },
  {
    title: "Plant room maintenance",
    description: "Routine inspection and maintenance of commercial gas plant rooms to keep systems reliable.",
    image: "/imagesv2/commercial_gas/plant_room.jpg",
    imageAlt: "Commercial gas plant room maintenance",
  },
  {
    title: "Emergency breakdowns",
    description: "Rapid commercial response for gas-related breakdowns and urgent faults.",
    image: "/imagesv2/commercial_gas/commercial_repair.jpg",
    imageAlt: "Commercial gas emergency breakdown response",
  },
  {
    title: "Preventative planned maintenance (PPM)",
    description: "Structured PPM contracts for commercial gas equipment to reduce failures.",
    image: "/imagesv2/commercial_gas/ppm.jpeg",
    imageAlt: "Commercial gas preventative planned maintenance",
  },
  {
    title: "Gas rate / combustion analysis",
    description: "Gas rate checks and combustion analysis to verify burner performance and efficiency.",
    image: "/imagesv2/commercial_gas/gas%20rate.webp",
    imageAlt: "Commercial gas combustion and gas rate checks",
  },
  {
    title: "System upgrades & efficiency improvements",
    description: "Upgrades to improve efficiency, reliability, and long-term operational performance.",
    image: "/imagesv2/commercial_gas/commercial_install.jpg",
    imageAlt: "Commercial gas system upgrades",
  },
];

const DOMESTIC_GAS_CARDS = [
  {
    title: "Boiler installation & replacement",
    description: "New boiler installations and replacements performed by Gas Safe engineers.",
    image: "/imagesv2/domestic_gas/boiler-install.jpg",
    imageAlt: "Domestic boiler installation",
  },
  {
    title: "Boiler servicing",
    description: "Annual boiler servicing to maintain efficiency, safety, and warranty requirements.",
    image: "/imagesv2/domestic_gas/boiler%20service.jpg",
    imageAlt: "Domestic boiler servicing",
  },
  {
    title: "Boiler repairs & breakdowns",
    description: "Fault diagnosis and repair to get heating and hot water restored quickly.",
    image: "/imagesv2/domestic_gas/boiler-repair.jpg",
    imageAlt: "Domestic boiler repairs",
  },
  {
    title: "Landlord Gas Safety Certificates (CP12)",
    description: "Landlord gas safety checks and CP12 certification for rental properties.",
    image: "/imagesv2/domestic_gas/landlord_safety.jpeg",
    imageAlt: "Landlord gas safety certificate checks",
  },
  {
    title: "Gas safety checks",
    description: "Gas safety checks for homeowners and tenants covering appliances, flues, and pipework.",
    image: "/imagesv2/domestic_gas/gas%20safe.webp",
    imageAlt: "Domestic gas safety checks",
  },
  {
    title: "Gas leaks / emergency response",
    description: "Response to suspected gas leaks and gas-related emergencies after safety procedures are followed.",
    image: "/imagesv2/domestic_gas/safe%20check.jpg",
    imageAlt: "Domestic gas leak emergency response",
  },
  {
    title: "Gas hob / cooker installation",
    description: "Installation of gas hobs and cookers by Gas Safe registered engineers.",
    image: "/imagesv2/domestic_gas/gas%20hob.webp",
    imageAlt: "Domestic gas hob and cooker installation",
  },
  {
    title: "Flue & ventilation checks",
    description: "Checks on flues and ventilation for domestic gas appliances to ensure safe operation.",
    image: "/imagesv2/domestic_gas/flue.jpg",
    imageAlt: "Domestic flue and ventilation checks",
  },
  {
    title: "System upgrades",
    description: "Upgrades to existing domestic gas systems for better efficiency and performance.",
    image: "/imagesv2/domestic_gas/upgrade.webp",
    imageAlt: "Domestic gas system upgrades",
  },
];

export const metadata: Metadata = {
  title: "Gas Services",
  description: `Gas installation, servicing, landlord safety inspections, and emergency callouts across ${COMPANY.areas}. Gas Safe registered engineers.`,
};

export default function GasServicesPage() {
  const services = CORE_SERVICE_SECTOR_SERVICES.gas;

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Gas Services"
        subtitle={`Gas installation and servicing, landlord safety inspections, and commercial and domestic gas works across ${COMPANY.areas}. Gas Safe registered.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Gas Services" },
        ]}
        backgroundImage="/images/core-services/gas.png"
        compact
      />
      <ServiceAudienceTabs
        commercialTitle="Commercial Gas Services"
        domesticTitle="Domestic Gas Services"
        commercialServices={services.commercial}
        domesticServices={services.domestic}
        commercialCards={COMMERCIAL_GAS_CARDS}
        domesticCards={DOMESTIC_GAS_CARDS}
      />
    </div>
  );
}
