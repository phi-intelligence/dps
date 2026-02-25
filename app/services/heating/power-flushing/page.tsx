import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Power Flushing",
  description: `Professional power flushing in ${COMPANY.areas}. Remove sludge and debris from your central heating system to restore efficiency.`,
};

export default function PowerFlushingPage() {
  return (
    <ServiceDetailLayout
      title="Power Flushing"
      subtitle="Professional power flushing to remove sludge and debris from your central heating system and restore full efficiency."
      backgroundImage="/images/c3f0259f-ffbb-408c-b420-a8c70e4a8190.jpg"
      sideImage="/images/c3f0259f-ffbb-408c-b420-a8c70e4a8190.jpg"
      sideImageAlt="Heating system pipes and valve manifold"
      introduction={`Over time, central heating systems can accumulate sludge, rust, and debris that reduce efficiency and cause problems such as cold radiators, noisy pipes, and boiler breakdowns. A professional power flush from DPS Heating Services LTD can restore your heating system to full working order. We carry out power flushing across ${COMPANY.areas} using professional equipment to thoroughly clean your entire system.`}
      included={[
        "Full central heating system flush",
        "Chemical descaling treatment",
        "Inhibitor added to protect system",
        "Individual radiator flushing",
        "System pressure and flow testing",
        "Before and after flow comparison",
        "Written report",
      ]}
      issues={[
        {
          icon: "thermometer",
          title: "Cold Radiators",
          description: "If your radiators are cold at the bottom or have cold patches, sludge build-up is often the cause.",
        },
        {
          icon: "alertCircle",
          title: "Noisy Boiler or Pipes",
          description: "Banging, gurgling, or rattling pipes can indicate a circulation problem caused by debris in the system.",
        },
        {
          icon: "gauge",
          title: "Slow to Heat Up",
          description: "A system full of sludge takes longer to reach temperature and uses more energy in the process.",
        },
        {
          icon: "flame",
          title: "Before a New Boiler",
          description: "A power flush is recommended before installing a new boiler to protect the new equipment from contamination.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Book an Assessment",
          description: "Contact us to discuss your heating system and arrange a visit.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "System Assessment",
          description: "We assess your system and confirm whether a power flush is the right solution.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Power Flush",
          description: "The power flushing equipment is connected and the system is thoroughly cleaned.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Inhibitor & Report",
          description: "A corrosion inhibitor is added to protect the system, and you receive a written report.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Gas Safe Registered",
          description: "All work carried out by qualified, Gas Safe registered engineers.",
        },
        {
          icon: "zap",
          title: "Improved Efficiency",
          description: "A clean system heats your home faster and uses less energy, reducing your bills.",
        },
        {
          icon: "clock",
          title: "Extends System Life",
          description: "Regular flushing reduces wear on your boiler and pump, extending the life of your heating system.",
        },
      ]}
      faqs={[
        {
          question: "How long does a power flush take?",
          answer: "A power flush typically takes 6–8 hours for an average-sized home. Larger properties or heavily contaminated systems may take longer.",
        },
        {
          question: "How do I know if my system needs a power flush?",
          answer: "Signs include cold patches on radiators, noisy pipes or boiler, slow heating, or dark discoloured water when bleeding radiators.",
        },
        {
          question: "How often should I power flush my system?",
          answer: "Most systems benefit from a power flush every 5–10 years, or when installing a new boiler.",
        },
        {
          question: "Will a power flush fix my boiler problems?",
          answer: "If sludge build-up is causing your boiler to work harder or break down, a power flush can resolve or significantly improve the issue.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Power Flushing" },
      ]}
      serviceValue="power-flushing"
      showGasSafeNote
      accentColor="red"
    />
  );
}
