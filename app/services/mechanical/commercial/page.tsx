import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const COMMERCIAL_MECHANICAL_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Heating system installation",
    description: "Full design, supply and installation of commercial heating systems. Our engineers deliver robust, efficient solutions tailored to your building and compliance requirements.",
    image: "/images/services/commercial-mechanical/plant-room-1.png",
    imageAlt: "Technicians working on commercial heating and pipework in a plant room",
  },
  {
    title: "Heating system repairs",
    description: "Fast fault finding and repair of commercial heating systems. We minimise downtime and restore heating performance with minimal disruption to your operations.",
    image: "/images/services/commercial-mechanical/plant-room-2.png",
    imageAlt: "Commercial plant room with pipes, valves and boiler units",
  },
  {
    title: "Pumps, valves & controls replacement",
    description: "Replacement and upgrade of circulation pumps, motorised valves and control equipment. We ensure correct sizing and commissioning for reliable operation.",
    image: "/images/services/commercial-mechanical/plant-room-3.png",
    imageAlt: "Pumps, valves and control units in a commercial heating system",
  },
  {
    title: "Pipework installation & modifications",
    description: "New pipework runs, distribution systems and modifications to existing installations. All work carried out to current standards with clear documentation.",
    image: "/images/services/commercial-mechanical/plant-room-4.png",
    imageAlt: "Technicians working on pipework in a commercial plant room",
  },
  {
    title: "HIU installation / servicing / repairs",
    description: "Heat interface unit installation, planned servicing and fault repair. We work with leading HIU manufacturers to maintain performance and compliance.",
    image: "/images/services/commercial-mechanical/plant-room-5.png",
    imageAlt: "Commercial boilers and pipework with technician and diagnostic equipment",
  },
  {
    title: "Pressurisation units",
    description: "Supply, installation and maintenance of pressurisation units for sealed heating systems. Correct pressure and expansion are essential for system longevity.",
    image: "/images/services/commercial-mechanical/plant-room-6.png",
    imageAlt: "Technician inspecting commercial boiler control panel",
  },
  {
    title: "Expansion vessels",
    description: "Sizing, installation and replacement of expansion vessels. We ensure adequate capacity and correct pre-charge for safe, efficient system operation.",
    image: "/images/services/commercial-mechanical/plant-room-1.png",
    imageAlt: "Commercial plant room heating installation",
  },
  {
    title: "Leak detection & repairs",
    description: "Systematic leak detection across pipework, fittings and plant. We locate and repair leaks with minimal damage to finishes and structure.",
    image: "/images/services/commercial-mechanical/plant-room-2.png",
    imageAlt: "Pipework and equipment in a commercial plant room",
  },
  {
    title: "System balancing",
    description: "Hydronic balancing of heating and cooling circuits to achieve design flow rates. Balanced systems improve comfort, efficiency and equipment life.",
    image: "/images/services/commercial-mechanical/plant-room-3.png",
    imageAlt: "Pumps, gauges and valves in a commercial heating system",
  },
  {
    title: "Powerflushing / system cleaning",
    description: "Powerflushing and chemical cleaning of heating systems to remove sludge and corrosion. Restores flow and heat output and protects new components.",
    image: "/images/services/commercial-mechanical/plant-room-4.png",
    imageAlt: "Technicians and pipework in a plant room",
  },
  {
    title: "General mechanical maintenance",
    description: "Routine inspection, servicing and small repairs across commercial mechanical systems. We keep plant rooms and heating infrastructure running reliably.",
    image: "/images/services/commercial-mechanical/plant-room-5.png",
    imageAlt: "Commercial boiler plant and pipework",
  },
];

export const metadata: Metadata = {
  title: "Commercial Mechanical Services",
  description: `Commercial mechanical services including heating systems, plant room, HIU, pipework, powerflushing, and PPM across ${COMPANY.areas}.`,
};

export default function CommercialMechanicalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Mechanical Services"
      subtitle={`Heating systems, plant room, pipework, HIU, powerflushing, and mechanical maintenance for commercial premises across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/core-services/mechanical.png"
      sideImageAlt="Commercial plant room and mechanical heating systems"
      introduction={`DPS Heating Services delivers full mechanical engineering solutions for commercial clients across ${COMPANY.areas}. From heating system installation and repairs to pumps, valves and controls, pipework and HIU installation and servicing, pressurisation units, expansion vessels, leak detection, system balancing, powerflushing, and general mechanical maintenance — our qualified engineers keep your commercial mechanical systems running safely and efficiently.`}
      included={CORE_SERVICE_SECTOR_SERVICES.mechanical.commercial}
      serviceCards={COMMERCIAL_MECHANICAL_SERVICE_CARDS}
      issues={[
        { icon: "settings", title: "System inefficiency", description: "Older or poorly maintained commercial heating and pipework can waste energy and increase running costs." },
        { icon: "alertCircle", title: "Plant room & HIU issues", description: "Commercial plant rooms and HIUs require regular inspection and maintenance to avoid breakdowns." },
        { icon: "thermometer", title: "Heating upgrades", description: "Upgrading heating systems, pipework, or controls can improve performance and reduce long-term costs." },
        { icon: "checkCircle", title: "Leaks & balancing", description: "Leak detection, repairs, and system balancing restore performance and prevent damage." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Contact us to describe your commercial mechanical requirements or report a fault." },
        { icon: "search", number: "02", title: "Assessment & quote", description: "We assess the job and provide a clear quote before any work begins." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our qualified engineers complete installation, maintenance, or repairs to a high standard." },
        { icon: "checkCircle", number: "04", title: "Handover & documentation", description: "We hand over the system with any relevant documentation and advice." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified engineers", description: "All mechanical work is carried out by trained, experienced engineers." },
        { icon: "fileText", title: "Clear documentation", description: "We provide documentation and records where required for compliance and warranty." },
        { icon: "clock", title: "Responsive service", description: "Planned maintenance and reactive callouts to keep your commercial systems running." },
      ]}
      faqs={[
        { question: "What is included in commercial mechanical maintenance?", answer: "We cover heating system checks, plant room and HIU inspections, pipework and valve checks, powerflushing, leak detection, system balancing, and preventative servicing tailored to your commercial system." },
        { question: "Do you work on commercial plant rooms and HIUs?", answer: "Yes. We install, service, and repair commercial plant rooms, HIUs, pressurisation units, expansion vessels, and associated pipework and controls across London, Kent, Essex and Surrey." },
        { question: "Do you offer powerflushing and system cleaning?", answer: "Yes. We provide powerflushing and system cleaning for commercial heating systems to restore efficiency and extend asset life." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Mechanical Services", href: "/services/mechanical" },
        { label: "Commercial" },
      ]}
      serviceValue="mechanical-commercial"
      theme="luxury"
      accentColor="red"
    />
  );
}
