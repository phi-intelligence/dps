import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "General Plumbing Services",
  description: `General plumbing services in ${COMPANY.areas}. Tap installation, toilet fitting, pipework, appliance connections from qualified plumbers.`,
};

export default function GeneralPlumbingPage() {
  return (
    <ServiceDetailLayout
      title="General Plumbing Services"
      subtitle="Reliable planned plumbing work for homes and businesses."
      backgroundImage="/images/kitchen-plumbing.jpg"
      sideImage="/images/kitchen-plumbing.jpg"
      sideImageAlt="Plumber installing new kitchen sink"
      introduction={`Need a plumber for planned work? Whether it is fitting new fixtures, moving pipework, or upgrading your system, DPS Heating Services Ltd provides reliable general plumbing services across ${COMPANY.areas}. We offer free quotes for all planned work and stick to our prices — no surprises.`}
      included={[
        "Tap and Mixer Installation",
        "Toilet and Cistern Fitting",
        "Pipework Installation and Rerouting",
        "Appliance Connection (Dishwasher, Washing Machine)",
        "Water Pressure Checks and Optimisation",
        "Stopcock and Valve Replacement",
        "Garden Tap Installation",
      ]}
      issues={[
        {
          icon: "home",
          title: "New fixtures needed",
          description: "Upgrading taps, toilets, or showers and need a professional fit.",
        },
        {
          icon: "checkCircle",
          title: "Appliance installation",
          description: "Connecting a new dishwasher, washing machine, or water softener.",
        },
        {
          icon: "droplets",
          title: "Pipework changes",
          description: "Moving or extending pipework during a renovation or extension.",
        },
        {
          icon: "wrench",
          title: "System upgrade",
          description: "Upgrading older plumbing components or improving water pressure.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Get a Quote",
          description: "Describe the work needed. We provide a free, no-obligation quote.",
        },
        {
          icon: "checkCircle",
          number: "02",
          title: "Job Scheduled",
          description: "We agree a convenient date and time for the work to be carried out.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Work Carried Out",
          description: "Our plumber completes the work cleanly and professionally.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Tested & Signed Off",
          description: "Everything is tested and checked before we leave.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Free Quotes",
          description: "We provide clear, written quotes before any work begins — no surprises.",
        },
        {
          icon: "star",
          title: "Clean & Tidy",
          description: "We always protect work areas and leave your home clean and tidy.",
        },
        {
          icon: "clock",
          title: "Weekend Availability",
          description: "Saturday appointments available for planned work.",
        },
      ]}
      faqs={[
        {
          question: "Do you provide a quote before starting?",
          answer: "Yes — we always provide a clear written quote before commencing any work. There are no hidden charges.",
        },
        {
          question: "Do you work on weekends?",
          answer: "Saturday appointments are available for planned plumbing work. Contact us to arrange a convenient time.",
        },
        {
          question: "Are you insured?",
          answer: "Yes. DPS Heating Services Ltd holds full public liability insurance for all domestic and commercial plumbing work.",
        },
        {
          question: "How quickly can you start the work?",
          answer: "For planned plumbing work, we can typically schedule within a few days. Contact us to check availability.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Plumbing", href: "/services/plumbing" },
        { label: "General Plumbing" },
      ]}
      serviceValue="general-plumbing"
    />
  );
}
