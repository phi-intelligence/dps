import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const DOMESTIC_PLUMBING_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "General plumbing repairs",
    description: "From leaks and faulty taps to toilet issues and pipework faults, we provide fast domestic repairs.",
    image: "/imagesv2/domestic_mechanical/domestic_plumbing.jpg",
    imageAlt: "Domestic plumbing repairs in kitchen and bathroom",
  },
  {
    title: "Fixture installation",
    description: "Professional installation of taps, toilets, and other fixtures with clean, tidy workmanship.",
    image: "/imagesv2/domestic_mechanical/domestic_leak.jpg",
    imageAlt: "Domestic fixture and plumbing installation",
  },
  {
    title: "Pipework and leak solutions",
    description: "Leak detection, pipework alterations, and pressure optimisation for reliable day-to-day performance.",
    image: "/imagesv2/domestic_mechanical/pipework.png",
    imageAlt: "Domestic pipework and leak repair",
  },
];

export const metadata: Metadata = {
  title: "Domestic Plumbing Services",
  description: `Domestic plumbing repairs, fixture installation, and leak solutions across ${COMPANY.areas}.`,
};

export default function DomesticPlumbingServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Plumbing Services"
      subtitle={`Domestic plumbing repairs, fixture installation, and leak solutions across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/imagesv2/domestic_mechanical/domestic_plumbing.jpg"
      sideImageAlt="Domestic plumbing and repairs"
      introduction={`DPS Heating Services delivers reliable domestic plumbing support across ${COMPANY.areas}. Whether you need urgent repairs, planned plumbing upgrades, or fixture installations, our engineers work cleanly, safely, and with clear communication from start to finish.`}
      included={CORE_SERVICE_SECTOR_SERVICES.plumbing.domestic}
      serviceCards={DOMESTIC_PLUMBING_SERVICE_CARDS}
      issues={[
        { icon: "droplets", title: "Leaks and drips", description: "Small leaks can escalate quickly if not diagnosed and repaired early." },
        { icon: "wrench", title: "Faulty fixtures", description: "Worn or damaged taps, toilets, and valves need proper replacement and testing." },
        { icon: "gauge", title: "Pressure issues", description: "Poor water pressure often points to valve, pipework, or system-side problems." },
        { icon: "checkCircle", title: "Planned upgrades", description: "Plumbing improvements can raise reliability and reduce repeat failures." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Tell us the issue", description: "Share the fault details or planned works and your preferred times." },
        { icon: "search", number: "02", title: "Assessment", description: "We diagnose the issue and confirm scope and costs before starting." },
        { icon: "wrench", number: "03", title: "Repair or install", description: "Our engineers complete the work using quality parts and proven methods." },
        { icon: "checkCircle", number: "04", title: "Testing and handover", description: "We test performance, tidy up, and confirm everything is working correctly." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified engineers", description: "Experienced domestic engineers with a safety-first approach." },
        { icon: "star", title: "Clean and tidy", description: "We protect your property and leave work areas clean on completion." },
        { icon: "clock", title: "Fast response", description: "Prompt attendance for urgent domestic plumbing issues." },
      ]}
      faqs={[
        { question: "Do you handle small domestic plumbing jobs?", answer: "Yes. We handle both small fixes and larger domestic plumbing works." },
        { question: "Do you offer emergency plumbing support?", answer: "Yes. We offer rapid response for urgent domestic plumbing issues." },
        { question: "Can you install new fixtures?", answer: "Yes. We install taps, toilets, and other plumbing fixtures as part of planned works." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Plumbing Services", href: "/services/plumbing" },
        { label: "Domestic" },
      ]}
      serviceValue="plumbing-domestic"
      theme="luxury"
      accentColor="red"
    />
  );
}
