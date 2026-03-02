import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const DOMESTIC_ELECTRICAL_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Heating controls fault finding",
    description: "Fault finding on heating controls, wiring and programmers. We trace faults efficiently and repair or replace so your heating works reliably again.",
    image: "/images/core-services/electrical.png",
    imageAlt: "Heating controls and electrical",
  },
  {
    title: "Thermostat / programmer replacement",
    description: "Supply and installation of room thermostats and programmers for central heating. We wire and commission so your system responds correctly to your settings.",
    image: "/images/central-heating.jpg",
    imageAlt: "Heating controls",
  },
  {
    title: "Wiring centre diagnostics",
    description: "Diagnostics and repair at the heating wiring centre. We identify faulty connections or components and restore correct operation of pumps, valves and boiler.",
    image: "/images/core-services/electrical.png",
    imageAlt: "Wiring centre and heating electrical",
  },
  {
    title: "Electrical checks related to heating systems",
    description: "Electrical safety and operation checks on heating-related circuits. We verify isolation, switching and load and advise on any issues found.",
    image: "/images/our-services-domestic.png",
    imageAlt: "Domestic heating electrical",
  },
];

export const metadata: Metadata = {
  title: "Domestic Electrical Services (Heating)",
  description: `Heating controls fault finding, thermostat and programmer replacement, and wiring diagnostics for homes across ${COMPANY.areas}.`,
};

export default function DomesticElectricalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Electrical Services"
      subtitle={`Heating controls fault finding, thermostat and programmer replacement, and wiring diagnostics for homes across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/core-services/electrical.png"
      sideImageAlt="Domestic heating controls and electrical diagnostics"
      introduction={`DPS Heating Services provides heating-related electrical services for domestic clients across ${COMPANY.areas}. From heating controls fault finding and thermostat or programmer replacement to wiring centre diagnostics and electrical checks related to heating systems — our engineers help keep your home heating controls safe and operational.`}
      included={CORE_SERVICE_SECTOR_SERVICES.electrical.domestic}
      serviceCards={DOMESTIC_ELECTRICAL_SERVICE_CARDS}
      issues={[
        { icon: "zap", title: "Heating controls faults", description: "Faulty thermostats, programmers, or wiring can cause heating failures and need professional diagnosis." },
        { icon: "settings", title: "Controls replacement", description: "Replacement thermostats or programmers need correct wiring and commissioning." },
        { icon: "fileText", title: "Wiring centre issues", description: "Wiring centre diagnostics identify and resolve faults in heating control circuits." },
        { icon: "checkCircle", title: "Electrical checks", description: "Electrical checks related to heating systems ensure safe and compliant operation." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Contact us with your heating controls or electrical issue." },
        { icon: "search", number: "02", title: "Assessment & quote", description: "We assess the work required and provide a clear, no-obligation quote." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our qualified engineers complete fault finding, replacement, or repairs to the required standards." },
        { icon: "fileText", number: "04", title: "Handover", description: "We confirm system operation and provide any relevant documentation." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified & compliant", description: "Electrical work is carried out by qualified engineers in line with current regulations." },
        { icon: "fileText", title: "Heating-focused", description: "We specialise in heating controls and wiring, so you get the right fix first time." },
        { icon: "clock", title: "Fault finding & response", description: "Fast fault finding and repair to restore your heating with minimal disruption." },
      ]}
      faqs={[
        { question: "What domestic electrical work do you carry out?", answer: "We provide heating controls fault finding, thermostat and programmer replacement, wiring centre diagnostics, and electrical checks related to heating systems. We focus on heating-related electrical work rather than full house rewires." },
        { question: "Do you replace thermostats and programmers?", answer: "Yes. We supply and fit thermostats and programmers for domestic heating systems and ensure correct wiring and commissioning." },
        { question: "Are you available for heating control faults?", answer: "Yes. We offer responsive callouts for heating-related electrical faults. Contact us to discuss availability." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Electrical Services", href: "/services/electrical" },
        { label: "Domestic" },
      ]}
      serviceValue="electrical-domestic"
      accentColor="blue"
    />
  );
}
