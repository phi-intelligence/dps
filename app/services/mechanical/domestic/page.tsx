import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const DOMESTIC_PLUMBING_HEATING_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Heating system installation / upgrades",
    description: "New central heating systems and upgrades to existing installations. We design, supply and install boilers, radiators and controls to suit your home and budget.",
    image: "/imagesv2/domestic_heating.jpg",
    imageAlt: "Central heating system",
  },
  {
    title: "Radiators / valves / TRVs",
    description: "Supply and installation of radiators, manual and thermostatic radiator valves (TRVs). We size and position for even heat distribution and efficient operation.",
    image: "/images/central-heating.jpg",
    imageAlt: "Radiators and heating",
  },
  {
    title: "Pumps & motorised valves",
    description: "Replacement and repair of central heating pumps and motorised valves. Correct operation is essential for heating performance and we commission after fitting.",
    image: "/imagesv2/domestic_pump.jpg",
    imageAlt: "Heating pumps and pipework",
  },
  {
    title: "Pipework repairs / alterations",
    description: "Repairs and alterations to heating and plumbing pipework. We work with minimal disruption and leave systems leak-free and properly supported.",
    image: "/images/plumbing-pipes.jpg",
    imageAlt: "Pipework and plumbing",
  },
  {
    title: "Leaks & water issues",
    description: "Leak detection and repair for heating and plumbing systems. We locate the source, make a lasting repair and advise on preventing recurrence.",
    image: "/imagesv2/domestic_leak.jpg",
    imageAlt: "Plumbing and water systems",
  },
  {
    title: "Cylinders / hot water systems",
    description: "Installation, repair and replacement of hot water cylinders and associated pipework. We ensure correct sizing and safe discharge arrangements.",
    image: "/imagesv2/domestic_hot_water.jpg",
    imageAlt: "Domestic hot water",
  },
  {
    title: "Unvented cylinder works (G3)",
    description: "G3-qualified work on unvented hot water cylinders. We install, service and repair unvented systems in line with building regulations.",
    image: "/images/central-heating.jpg",
    imageAlt: "Unvented cylinder",
  },
  {
    title: "Powerflushing",
    description: "Powerflushing of central heating systems to remove sludge and corrosion. Restores flow and heat output and helps protect new components.",
    image: "/images/plumbing-pipes.jpg",
    imageAlt: "Powerflushing and system cleaning",
  },
  {
    title: "General plumbing & heating repair",
    description: "Routine repairs and small jobs across domestic plumbing and heating. We respond promptly and complete work to a high standard.",
    image: "/imagesv2/domestic_plumbing.jpg",
    imageAlt: "Domestic plumbing and heating",
  },
];

export const metadata: Metadata = {
  title: "Domestic Plumbing & Heating Services",
  description: `Domestic heating installation, radiators, cylinders, powerflushing, and plumbing repairs across ${COMPANY.areas}.`,
};

export default function DomesticMechanicalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Plumbing & Heating"
      subtitle={`Heating installation, radiators, cylinders, powerflushing, and plumbing repairs for homes across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/core-services/mechanical.png"
      sideImageAlt="Domestic heating and plumbing systems"
      introduction={`DPS Heating Services delivers plumbing and heating solutions for domestic clients across ${COMPANY.areas}. From heating system installation and upgrades to radiators, valves and TRVs, pumps and motorised valves, pipework repairs and alterations, leaks and water issues, cylinders and hot water systems, unvented cylinder works (G3), powerflushing, and general plumbing and heating repair — our qualified engineers keep your home heating and plumbing running safely and efficiently.`}
      included={CORE_SERVICE_SECTOR_SERVICES.mechanical.domestic}
      serviceCards={DOMESTIC_PLUMBING_HEATING_SERVICE_CARDS}
      issues={[
        { icon: "settings", title: "System inefficiency", description: "Older or poorly maintained heating and pipework can waste energy and increase bills." },
        { icon: "thermometer", title: "Heating upgrades", description: "Upgrading your heating system, radiators, or controls can improve comfort and reduce long-term costs." },
        { icon: "checkCircle", title: "Leaks & hot water", description: "Leaks, cylinder issues, and hot water problems need professional diagnosis and repair." },
        { icon: "wrench", title: "Radiators & valves", description: "Radiators, TRVs, pumps, and motorised valves can be replaced or repaired to restore performance." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Contact us to describe your requirements or report a fault." },
        { icon: "search", number: "02", title: "Assessment & quote", description: "We assess the job and provide a clear quote before any work begins." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our qualified engineers complete installation, maintenance, or repairs to a high standard." },
        { icon: "checkCircle", number: "04", title: "Handover & advice", description: "We hand over the system with any relevant documentation and advice." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified engineers", description: "All plumbing and heating work is carried out by trained, experienced engineers." },
        { icon: "fileText", title: "Clear documentation", description: "We provide documentation and records where required for warranty and peace of mind." },
        { icon: "clock", title: "Responsive service", description: "Planned maintenance and reactive callouts when you need us." },
      ]}
      faqs={[
        { question: "What is included in domestic plumbing and heating?", answer: "We cover heating system installation and upgrades, radiators and TRVs, pumps and motorised valves, pipework repairs, leaks, cylinders and hot water systems, unvented cylinder works (G3), powerflushing, and general plumbing and heating repair." },
        { question: "Do you work on unvented cylinders (G3)?", answer: "Yes. We carry out unvented cylinder installation, servicing, and repairs. G3 work is completed by qualified engineers in line with building regulations." },
        { question: "Do you offer powerflushing?", answer: "Yes. We provide powerflushing for domestic heating systems to remove sludge and restore performance." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Mechanical Services", href: "/services/mechanical" },
        { label: "Domestic" },
      ]}
      serviceValue="mechanical-domestic"
      theme="luxury"
      accentColor="red"
    />
  );
}
