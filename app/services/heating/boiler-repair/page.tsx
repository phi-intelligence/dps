import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Boiler Repair",
  description: `Expert boiler repair in ${COMPANY.areas}. Gas Safe registered engineers, fast response, all makes and models covered.`,
};

export default function BoilerRepairPage() {
  return (
    <ServiceDetailLayout
      title="Boiler Repair"
      subtitle="Fast, reliable boiler repairs by Gas Safe registered engineers. We aim to fix your boiler on the first visit."
      backgroundImage="/images/de580d83-e113-4fa5-8635-779e1377cae6.jpg"
      sideImage="/images/de580d83-e113-4fa5-8635-779e1377cae6.jpg"
      sideImageAlt="Open boiler showing internal components during diagnosis"
      introduction={`A broken boiler is never convenient. DPS Heating Services LTD provides fast, professional boiler repair across ${COMPANY.areas}. Our Gas Safe registered engineers carry a wide range of parts, allowing us to diagnose and fix most faults on the first visit. We work on all major boiler brands and both domestic and commercial properties.`}
      included={[
        "Full boiler diagnosis",
        "Error code analysis",
        "Pressure check and rebalancing",
        "Component repair or replacement",
        "Safety checks and testing",
        "Written job report",
      ]}
      issues={[
        {
          icon: "alertCircle",
          title: "Unusual Noises",
          description: "Banging, kettling, or rumbling sounds can indicate a build-up of limescale or a failing pump.",
        },
        {
          icon: "thermometer",
          title: "No Heat or Hot Water",
          description: "If your boiler is not producing heat or hot water, there may be a fault with the ignition or heat exchanger.",
        },
        {
          icon: "gauge",
          title: "Low Pressure",
          description: "A boiler that keeps losing pressure may have a leak in the system or a faulty pressure relief valve.",
        },
        {
          icon: "flame",
          title: "Pilot Light Issues",
          description: "If your pilot light keeps going out, this could indicate a faulty thermocouple or gas supply issue.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Call Us",
          description: "Get in touch by phone or our contact form. Describe the problem so we can prepare.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "Engineer Visit",
          description: "A Gas Safe registered engineer arrives at your property to carry out a full diagnosis.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Repair",
          description: "We fix the fault using quality parts, aiming to complete the repair on the same visit.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Safety Check & Sign-off",
          description: "Full safety testing is completed before we leave, and you receive a written report.",
        },
      ]}
      trustPoints={[
        {
          icon: "clock",
          title: "Fast Response",
          description: "We aim for same-day or next-day appointments for boiler faults.",
        },
        {
          icon: "shield",
          title: "Gas Safe Registered",
          description: "All repairs are carried out by certified Gas Safe engineers.",
        },
        {
          icon: "flame",
          title: "All Makes & Models",
          description: "Worcester Bosch, Vaillant, Baxi, Ideal, Viessmann, and many more.",
        },
      ]}
      faqs={[
        {
          question: "How much does a boiler repair cost?",
          answer:
            "The cost depends on the fault and parts required. We provide a clear quote before any work begins so there are no surprises.",
        },
        {
          question: "How long does a boiler repair take?",
          answer:
            "Most repairs are completed within 1–2 hours on the first visit. More complex faults may require parts to be ordered.",
        },
        {
          question: "Do you carry parts with you?",
          answer:
            "Yes — our engineers carry a wide range of common parts to help fix most faults on the first visit.",
        },
        {
          question: "Should I replace my boiler instead of repairing it?",
          answer:
            "If your boiler is over 10 years old and needs frequent repairs, replacement may be more cost-effective. We will always give you honest advice.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Boiler Repair" },
      ]}
      serviceValue="boiler-repair"
      showGasSafeNote
      accentColor="red"
    />
  );
}
