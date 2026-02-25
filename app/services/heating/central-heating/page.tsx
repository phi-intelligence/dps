import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Central Heating Installation & Repairs",
  description: `Central heating installation and repairs in ${COMPANY.areas}. Gas Safe registered engineers for all central heating needs.`,
};

export default function CentralHeatingPage() {
  return (
    <ServiceDetailLayout
      title="Central Heating"
      subtitle="Central heating installation, upgrades, and repairs for homes and businesses across London."
      backgroundImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
      sideImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
      sideImageAlt="Engineer installing copper heating pipework in a commercial building"
      introduction={`Whether you are installing central heating for the first time, upgrading an existing system, or having your current system repaired, DPS Heating Services LTD can help. We provide comprehensive central heating services across ${COMPANY.areas}, covering everything from new system design to component replacement, all carried out by our Gas Safe registered engineers.`}
      included={[
        "Full system design and quote",
        "New central heating installation",
        "System upgrades and extensions",
        "Pipe work installation",
        "Radiator installation",
        "System pressure testing",
        "Commissioning and balancing",
        "Building regulations certificate",
      ]}
      issues={[
        {
          icon: "thermometer",
          title: "No Existing Central Heating",
          description: "We design and install complete central heating systems for properties that currently rely on electric or other heating methods.",
        },
        {
          icon: "flame",
          title: "Extending Your System",
          description: "Adding rooms or extensions to your property? We can extend your existing central heating to cover new areas.",
        },
        {
          icon: "gauge",
          title: "System Not Heating Properly",
          description: "Cold spots, uneven heating, or low pressure can indicate a need for repairs or a system flush.",
        },
        {
          icon: "wrench",
          title: "Ageing System",
          description: "Older central heating systems can be inefficient and unreliable. A system upgrade can improve performance and reduce bills.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Free Survey",
          description: "We visit your property to assess your needs and design the right solution.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Detailed Quote",
          description: "You receive a written quote covering all work and materials, with no hidden costs.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Installation",
          description: "Our engineers carry out the work professionally, protecting your home throughout.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Commissioning",
          description: "The system is balanced and tested. You receive a building regulations certificate.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Gas Safe Registered",
          description: "All central heating work is carried out by Gas Safe registered engineers.",
        },
        {
          icon: "star",
          title: "Clean and Tidy",
          description: "We protect your home during installation and leave everything clean when we are done.",
        },
        {
          icon: "clock",
          title: "Upfront Pricing",
          description: "You receive a fixed quote before work starts — no surprise charges.",
        },
      ]}
      faqs={[
        {
          question: "How long does a central heating installation take?",
          answer: "A standard installation typically takes 3–5 days depending on the size of the property. We will give you a clear timeline as part of your quote.",
        },
        {
          question: "Do you install smart thermostats?",
          answer: "Yes. We can install smart thermostats and controls alongside your central heating system for improved convenience and efficiency.",
        },
        {
          question: "Can you work on older systems?",
          answer: "Yes. We carry out repairs and upgrades on all types of central heating systems regardless of age.",
        },
        {
          question: "Will my home be left clean?",
          answer: "Absolutely. We use protective coverings throughout and tidy up fully before we leave.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Central Heating" },
      ]}
      serviceValue="central-heating"
      showGasSafeNote
      accentColor="red"
    />
  );
}
