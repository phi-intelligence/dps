import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const COMMERCIAL_ELECTRICAL_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Electrical fault finding (heating related)",
    description: "Systematic fault finding on heating-related electrical circuits. We trace faults in controls, wiring and ancillaries to restore heating operation quickly.",
    image: "/imagesv2/commercial_electric.jpg",
    imageAlt: "Electrical controls and heating systems",
  },
  {
    title: "Controls wiring & diagnostics",
    description: "Wiring, commissioning and diagnostics for heating controls and BMS interfaces. We ensure correct connections and document any changes for your records.",
    image: "/imagesv2/commercial_wiring.jpg",
    imageAlt: "Control units and pipework in plant room",
  },
  {
    title: "Programmer / thermostat replacement",
    description: "Supply and installation of programmers and thermostats for commercial heating. We wire and commission to manufacturer specifications.",
    image: "/imagesv2/commercial_thermostat.jpg",
    imageAlt: "Commercial boiler and control panels",
  },
  {
    title: "Pumps / valves electrical testing",
    description: "Electrical testing of pumps and motorised valves to confirm safe operation and correct switching. We document results and advise on any faults found.",
    image: "/imagesv2/commercial_testing.jpg",
    imageAlt: "Pumps and valves in commercial system",
  },
  {
    title: "Isolation & safety checks",
    description: "Isolation and safety checks on heating-related electrical circuits. We verify isolation arrangements and document findings for compliance.",
    image: "/images/core-services/electrical.png",
    imageAlt: "Electrical safety and isolation",
  },
  {
    title: "Emergency electrical diagnostics (M&E related)",
    description: "Rapid electrical diagnostics when heating or M&E systems fail. We prioritise safety and restore operation with minimal downtime.",
    image: "/imagesv2/commercial_diagnosis.jpg",
    imageAlt: "Technician with diagnostic equipment in plant room",
  },
];

export const metadata: Metadata = {
  title: "Commercial Electrical Services",
  description: `Commercial electrical fault finding, controls wiring, programmer and thermostat replacement, and M&E diagnostics across ${COMPANY.areas}.`,
};

export default function CommercialElectricalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Electrical Services"
      subtitle={`Heating-related electrical fault finding, controls wiring, programmer and thermostat replacement, and emergency M&E diagnostics across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/core-services/electrical.png"
      sideImageAlt="Commercial electrical controls and heating diagnostics"
      introduction={`DPS Heating Services provides heating-related electrical services for commercial clients across ${COMPANY.areas}. From electrical fault finding and controls wiring to programmer and thermostat replacement, pumps and valves electrical testing, isolation and safety checks, and emergency electrical diagnostics for M&E systems — our engineers help keep your commercial heating controls and electrical systems safe and operational.`}
      included={CORE_SERVICE_SECTOR_SERVICES.electrical.commercial}
      serviceCards={COMMERCIAL_ELECTRICAL_SERVICE_CARDS}
      issues={[
        { icon: "zap", title: "Heating controls faults", description: "Faulty programmers, thermostats, or wiring can cause heating failures and need professional diagnosis." },
        { icon: "alertCircle", title: "Pump and valve electrical issues", description: "Electrical testing and isolation checks ensure pumps and valves operate safely and correctly." },
        { icon: "settings", title: "Controls upgrades", description: "Replacement programmers or thermostats need qualified electrical installation and commissioning." },
        { icon: "fileText", title: "Emergency diagnostics", description: "When heating or M&E systems fail, fast electrical diagnostics minimise downtime." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Contact us with your commercial electrical or heating controls issue." },
        { icon: "search", number: "02", title: "Assessment & quote", description: "We assess the work required and provide a clear, no-obligation quote." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our qualified engineers complete fault finding, replacement, or repairs to the required standards." },
        { icon: "fileText", number: "04", title: "Handover & documentation", description: "Where applicable we provide documentation and confirm system operation." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified & compliant", description: "Electrical work is carried out by qualified engineers in line with current regulations." },
        { icon: "fileText", title: "Safety checks", description: "We carry out isolation and safety checks and document findings where required." },
        { icon: "clock", title: "Fault finding & response", description: "Fast fault finding and repair to minimise disruption and restore heating operation." },
      ]}
      faqs={[
        { question: "What commercial electrical work do you carry out?", answer: "We provide heating-related electrical fault finding, controls wiring and diagnostics, programmer and thermostat replacement, pumps and valves electrical testing, isolation and safety checks, and emergency electrical diagnostics for M&E systems." },
        { question: "Do you replace programmers and thermostats?", answer: "Yes. We supply and fit programmers and thermostats for commercial heating systems and ensure correct wiring and commissioning." },
        { question: "Are you available for emergency electrical diagnostics?", answer: "We offer responsive callouts for heating-related electrical faults. Contact us to discuss availability and we will prioritise where there is a safety or operational concern." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Electrical Services", href: "/services/electrical" },
        { label: "Commercial" },
      ]}
      serviceValue="electrical-commercial"
      theme="luxury"
      accentColor="blue"
    />
  );
}
