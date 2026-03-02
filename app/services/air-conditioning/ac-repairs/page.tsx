import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "AC Repairs",
  description: `Air conditioning repairs in ${COMPANY.areas}. Fast diagnosis and repair of all AC faults, all major brands covered.`,
};

export default function ACRepairsPage() {
  return (
    <ServiceDetailLayout
      title="AC Repairs"
      subtitle="Fast, professional air conditioning repairs for domestic and commercial systems across London."
      backgroundImage="/images/ac-unit-indoor.jpg"
      sideImage="/images/ac-unit-indoor.jpg"
      sideImageAlt="Air conditioning unit being repaired"
      introduction={`When your air conditioning stops working, you want it fixed quickly. DPS Heating Services LTD provides prompt AC repair services across ${COMPANY.areas} for all major brands of domestic and commercial systems. Our engineers carry out thorough diagnostics to identify the fault and carry out the repair efficiently, aiming to restore your system on the first visit wherever possible.`}
      included={[
        "Full system diagnosis",
        "Refrigerant leak detection and repair",
        "Electrical fault finding",
        "Component replacement",
        "Refrigerant top-up or recharge",
        "Performance testing after repair",
        "Written job report",
      ]}
      issues={[
        {
          icon: "wind",
          title: "Not Cooling or Heating",
          description: "If your AC is running but not producing the right temperature, there may be a refrigerant leak or compressor issue.",
        },
        {
          icon: "alertCircle",
          title: "System Not Turning On",
          description: "Electrical faults, tripped breakers, or control board issues can prevent your AC from starting.",
        },
        {
          icon: "settings",
          title: "Unusual Noises",
          description: "Rattling, grinding, or hissing sounds from your AC unit usually indicate a mechanical or refrigerant issue.",
        },
        {
          icon: "checkCircle",
          title: "Water Leaking",
          description: "A blocked condensate drain is a common cause of water leaking from an indoor AC unit.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Contact Us",
          description: "Call or message us to describe the problem. We will arrange a prompt visit.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "Diagnosis",
          description: "Our engineer carries out a full diagnostic to identify the cause of the fault.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Repair",
          description: "The fault is repaired and parts replaced as needed, aiming for a same-visit fix.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Testing & Sign-off",
          description: "The system is fully tested before the engineer leaves and you receive a written report.",
        },
      ]}
      trustPoints={[
        {
          icon: "clock",
          title: "Prompt Service",
          description: "We aim for fast appointment availability for AC repair calls.",
        },
        {
          icon: "shield",
          title: "F-Gas Certified",
          description: "All refrigerant work is carried out by F-Gas certified engineers.",
        },
        {
          icon: "zap",
          title: "All Major Brands",
          description: "Mitsubishi, Daikin, LG, Samsung, Fujitsu, Panasonic, and more.",
        },
      ]}
      faqs={[
        {
          question: "How much does an AC repair cost?",
          answer: "The cost depends on the fault and any parts required. We give you a clear quote before proceeding with any repair work.",
        },
        {
          question: "Can you repair any brand of AC?",
          answer: "Yes. We repair all major brands including Mitsubishi Electric, Daikin, LG, Samsung, Panasonic, and Fujitsu.",
        },
        {
          question: "What if I need a refrigerant top-up?",
          answer: "Our engineers are F-Gas certified and can legally handle and recharge refrigerants. We will also check for and repair any leaks.",
        },
        {
          question: "Is it worth repairing an old AC unit?",
          answer: "It depends on the age and condition of the system. We will give you honest advice on whether a repair or replacement is better value.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Air Conditioning", href: "/services/air-conditioning" },
        { label: "AC Repairs" },
      ]}
      serviceValue="ac-repairs"
      accentColor="blue"
    />
  );
}
