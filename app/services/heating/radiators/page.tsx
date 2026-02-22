import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Radiator Installation & Repairs",
  description: `Radiator installation, replacement, and repairs in ${COMPANY.areas}. Gas Safe registered engineers for all radiator work.`,
};

export default function RadiatorsPage() {
  return (
    <ServiceDetailLayout
      title="Radiator Services"
      subtitle="Radiator installation, replacement, repairs, and balancing for homes and businesses across London."
      backgroundImage="/images/b5ec6a7e-9a7d-4a9d-8596-8a89110fa626.jpg"
      sideImage="/images/b5ec6a7e-9a7d-4a9d-8596-8a89110fa626.jpg"
      sideImageAlt="Heating pipe system with valves and fittings"
      introduction={`From a single radiator replacement to a full re-radiation of your property, DPS Heating Services Ltd provides all aspects of radiator work across ${COMPANY.areas}. Our Gas Safe registered engineers can install new radiators, replace old ones, repair leaks, and balance your system to ensure every room heats evenly.`}
      included={[
        "New radiator installation",
        "Radiator replacement",
        "Radiator relocation",
        "Thermostatic valve fitting",
        "Leak repair",
        "Radiator bleeding and balancing",
        "System pressure check",
        "Full testing and sign-off",
      ]}
      issues={[
        {
          icon: "thermometer",
          title: "Cold Spots on Radiators",
          description: "If your radiator is cold at the top or bottom, it may need bleeding or have a build-up of sludge.",
        },
        {
          icon: "alertCircle",
          title: "Leaking Radiator",
          description: "A leaking radiator or valve needs prompt attention to prevent water damage.",
        },
        {
          icon: "wrench",
          title: "Old or Inefficient Radiators",
          description: "Replacing old, undersized radiators with modern high-output models can improve your heating efficiency.",
        },
        {
          icon: "settings",
          title: "Uneven Heating",
          description: "If some rooms are warmer than others, your system may need balancing.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Contact Us",
          description: "Get in touch to explain what you need. We will arrange a suitable appointment.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "Assessment",
          description: "Our engineer assesses the job and provides a clear quote before starting work.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Work Carried Out",
          description: "The radiator work is completed to a high standard with minimal disruption.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Testing",
          description: "The system is tested and checked for leaks before the engineer leaves.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Gas Safe Registered",
          description: "All radiator and pipework is handled by Gas Safe registered engineers.",
        },
        {
          icon: "clock",
          title: "Prompt Service",
          description: "Most radiator jobs can be completed in a single visit.",
        },
        {
          icon: "star",
          title: "Tidy Work",
          description: "We protect your walls and floors throughout and clean up after every job.",
        },
      ]}
      faqs={[
        {
          question: "How long does it take to fit a new radiator?",
          answer: "A single radiator replacement usually takes 1–2 hours. Fitting a new radiator in a room without existing pipework will take longer.",
        },
        {
          question: "Can you move a radiator to a different wall?",
          answer: "Yes. We can relocate radiators and extend the pipework to the new position.",
        },
        {
          question: "What size radiator do I need?",
          answer: "The correct size depends on the room dimensions and heat loss. We will advise on the right output for each room.",
        },
        {
          question: "Can you bleed and balance my system?",
          answer: "Yes. We can bleed radiators and balance the system to ensure even heat distribution throughout your property.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Radiator Services" },
      ]}
      serviceValue="radiators"
      showGasSafeNote
      accentColor="red"
    />
  );
}
