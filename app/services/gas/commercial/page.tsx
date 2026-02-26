import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const COMMERCIAL_GAS_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Commercial boiler installation & replacement",
    description: "Full design, supply and installation of commercial gas boilers. We specify and fit equipment suited to your load and compliance requirements, with full commissioning and handover.",
    image: "/images/services/commercial-mechanical/plant-room-1.png",
    imageAlt: "Commercial boiler plant and pipework",
  },
  {
    title: "Commercial boiler servicing",
    description: "Scheduled servicing of commercial gas boilers to maintain efficiency, safety and warranty. Our Gas Safe engineers follow manufacturer guidelines and document all work.",
    image: "/images/services/commercial-mechanical/plant-room-2.png",
    imageAlt: "Commercial plant room with boilers and pipework",
  },
  {
    title: "Commercial boiler repairs & fault finding",
    description: "Fast diagnosis and repair of commercial boiler faults. We minimise downtime and restore heating with minimal disruption to your operations.",
    image: "/images/boiler-repair.jpg",
    imageAlt: "Boiler repair and fault finding",
  },
  {
    title: "Gas safety inspections",
    description: "Thorough gas safety inspections of commercial premises and appliances. We issue the relevant certificates and reports for your compliance records.",
    image: "/images/boiler-modern.jpg",
    imageAlt: "Gas appliance inspection",
  },
  {
    title: "Tightness testing & purging",
    description: "Tightness testing and purging of gas installations to current standards. Essential for new installations, modifications and after repair.",
    image: "/images/services/commercial-mechanical/plant-room-4.png",
    imageAlt: "Gas pipework and testing",
  },
  {
    title: "Gas pipework installation / modification",
    description: "New gas pipework runs and modifications to existing installations. All work carried out by Gas Safe registered engineers with appropriate testing and documentation.",
    image: "/images/services/commercial-mechanical/plant-room-5.png",
    imageAlt: "Gas pipework in plant room",
  },
  {
    title: "Plant room maintenance",
    description: "Routine inspection and maintenance of commercial gas plant rooms. We keep boilers, pipework and controls running safely and efficiently.",
    image: "/images/services/commercial-mechanical/plant-room-6.png",
    imageAlt: "Commercial plant room maintenance",
  },
  {
    title: "Emergency breakdowns",
    description: "24/7 emergency callouts for commercial gas breakdowns. We respond quickly to restore heating and ensure safety where it is safe to do so.",
    image: "/images/emergency-callout.jpg",
    imageAlt: "Emergency breakdown response",
  },
  {
    title: "Preventative planned maintenance (PPM)",
    description: "Structured PPM contracts for commercial gas equipment. Planned visits reduce the risk of failure and help meet insurance and compliance requirements.",
    image: "/images/central-heating.jpg",
    imageAlt: "Planned maintenance of heating systems",
  },
  {
    title: "Gas rate / combustion analysis",
    description: "Gas rate checks and combustion analysis to verify burner performance and efficiency. We identify issues before they affect safety or running costs.",
    image: "/images/services/commercial-mechanical/plant-room-3.png",
    imageAlt: "Combustion and gas rate checks",
  },
  {
    title: "System upgrades & efficiency improvements",
    description: "Upgrades and efficiency improvements to existing commercial gas systems. We advise on options and deliver installations that cut costs and improve reliability.",
    image: "/images/blueprint-plant-room.png",
    imageAlt: "Commercial heating system design",
  },
];

export const metadata: Metadata = {
  title: "Commercial Gas Services",
  description: `Commercial gas installation, boiler servicing, safety inspections, PPM, and emergency callouts across ${COMPANY.areas}. Gas Safe registered.`,
};

export default function CommercialGasServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Gas Services"
      subtitle={`Gas Safe registered commercial gas installation, servicing, safety inspections, PPM, and emergency breakdowns across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/core-services/gas.png"
      sideImageAlt="Commercial gas safety inspection and boiler plant"
      introduction={`All commercial gas work at DPS Heating Services is carried out by Gas Safe registered engineers across ${COMPANY.areas}. We provide commercial boiler installation and replacement, servicing and repairs, gas safety inspections, tightness testing and purging, gas pipework installation and modification, plant room maintenance, PPM contracts, gas rate and combustion analysis, and 24-hour emergency breakdowns. Safety and compliance are at the heart of everything we do.`}
      included={CORE_SERVICE_SECTOR_SERVICES.gas.commercial}
      serviceCards={COMMERCIAL_GAS_SERVICE_CARDS}
      issues={[
        { icon: "flame", title: "Boiler or plant fault", description: "Commercial gas boilers and appliances should be serviced regularly and repaired by Gas Safe registered engineers only." },
        { icon: "shield", title: "Gas safety inspections", description: "Commercial premises require regular gas safety inspections and certification to remain compliant." },
        { icon: "alertCircle", title: "Gas emergency", description: "If you smell gas or suspect a leak, turn off the supply, ventilate, and call the gas emergency number. We can then support with repairs." },
        { icon: "checkCircle", title: "PPM & efficiency", description: "Preventative planned maintenance and combustion analysis help reduce breakdowns and improve efficiency." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Call us or use our form to book a service, inspection, PPM, or report an issue." },
        { icon: "search", number: "02", title: "Quote & appointment", description: "We provide a clear quote and arrange a convenient appointment with a Gas Safe engineer." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our Gas Safe registered engineer completes the work to the required safety standards." },
        { icon: "fileText", number: "04", title: "Certificate & report", description: "You receive the relevant certificate or report for your records and compliance." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Gas Safe registered", description: "All commercial gas work is carried out by Gas Safe registered engineers." },
        { icon: "fileText", title: "Certificates provided", description: "We issue gas safety certificates and reports where required for commercial compliance." },
        { icon: "clock", title: "Emergency callouts", description: "We offer 24/7 emergency callouts for gas-related breakdowns where safe to do so." },
      ]}
      faqs={[
        { question: "Are you Gas Safe registered for commercial work?", answer: "Yes. All gas work is carried out by Gas Safe registered engineers. Our registration details can be verified on the Gas Safe Register website." },
        { question: "Do you provide commercial gas safety inspections and PPM?", answer: "Yes. We carry out gas safety inspections, tightness testing, combustion analysis, and preventative planned maintenance for commercial premises across London, Kent, Essex and Surrey." },
        { question: "Do you offer emergency gas callouts for commercial?", answer: "We offer emergency callouts for gas-related breakdowns. If you smell gas or have a gas emergency, you must call the gas emergency number first; we can then assist with any repairs once the situation is safe." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Gas Services", href: "/services/gas" },
        { label: "Commercial" },
      ]}
      serviceValue="gas-commercial"
      showGasSafeNote
      accentColor="red"
    />
  );
}
