import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";
import ServiceAudienceTabs from "@/components/sections/ServiceAudienceTabs";

const COMMERCIAL_ELECTRICAL_CARDS = [
  {
    title: "Electrical fault finding (heating related)",
    description: "Systematic diagnosis of heating-related electrical faults across controls, wiring, and ancillaries.",
    image: "/imagesv2/commercial_electrical/commercial_electric.jpg",
    imageAlt: "Commercial electrical fault finding",
  },
  {
    title: "Controls wiring & diagnostics",
    description: "Wiring, diagnostics, and commissioning for controls and BMS interfaces.",
    image: "/imagesv2/commercial_electrical/commercial_wiring.jpg",
    imageAlt: "Commercial controls wiring",
  },
  {
    title: "Programmer / thermostat replacement",
    description: "Replacement and commissioning of commercial programmers and thermostats.",
    image: "/imagesv2/commercial_electrical/commercial_thermostat.jpg",
    imageAlt: "Commercial thermostat replacement",
  },
  {
    title: "Pumps / valves electrical testing",
    description: "Electrical testing for pumps and motorised valves to verify safe switching and operation.",
    image: "/imagesv2/commercial_electrical/commercial_testing.jpg",
    imageAlt: "Commercial pumps and valves testing",
  },
  {
    title: "Isolation & safety checks",
    description: "Isolation and electrical safety checks with clear findings for compliance documentation.",
    image: "/imagesv2/commercial_electrical/safety.webp",
    imageAlt: "Commercial electrical safety checks",
  },
  {
    title: "Emergency electrical diagnostics",
    description: "Rapid M&E-related diagnostics for critical failures requiring immediate attention.",
    image: "/imagesv2/commercial_electrical/commercial_diagnosis.jpg",
    imageAlt: "Emergency commercial electrical diagnostics",
  },
];

const DOMESTIC_ELECTRICAL_CARDS = [
  {
    title: "Heating controls fault finding",
    description: "Fault finding on thermostats, programmers, wiring, and control circuits in homes.",
    image: "/imagesv2/domestic_electrical/heating%20control.jpg",
    imageAlt: "Domestic heating controls fault finding",
  },
  {
    title: "Thermostat / programmer replacement",
    description: "Supply and replacement of domestic thermostats and programmers with proper commissioning.",
    image: "/imagesv2/domestic_electrical/thermostat.jpg",
    imageAlt: "Domestic thermostat replacement",
  },
  {
    title: "Wiring centre diagnostics",
    description: "Diagnostics and repair at wiring centres controlling boilers, pumps, and valves.",
    image: "/imagesv2/domestic_electrical/wiring%20centre.jpg",
    imageAlt: "Domestic wiring centre diagnostics",
  },
  {
    title: "Electrical checks for heating systems",
    description: "Heating-related electrical checks and EICR-context reporting for safety and landlord compliance.",
    image: "/imagesv2/domestic_electrical/eicr.jpeg",
    imageAlt: "Domestic electrical compliance checks",
  },
];

export const metadata: Metadata = {
  title: "Electrical Services",
  description: `Electrical installations, fault finding, compliance inspections, and maintenance contracts across ${COMPANY.areas}. Commercial and domestic.`,
};

export default function ElectricalServicesPage() {
  const services = CORE_SERVICE_SECTOR_SERVICES.electrical;

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Electrical Services"
        subtitle={`Electrical installations, fault finding, compliance inspections, and maintenance contracts across ${COMPANY.areas}.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Electrical Services" },
        ]}
        backgroundImage="/images/core-services/electrical.png"
        compact
      />
      <ServiceAudienceTabs
        commercialTitle="Commercial Electrical Services"
        domesticTitle="Domestic Electrical Services"
        commercialServices={services.commercial}
        domesticServices={services.domestic}
        commercialCards={COMMERCIAL_ELECTRICAL_CARDS}
        domesticCards={DOMESTIC_ELECTRICAL_CARDS}
      />
    </div>
  );
}
