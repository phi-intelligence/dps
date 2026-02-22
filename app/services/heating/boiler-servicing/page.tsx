import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Boiler Servicing",
  description: `Annual boiler service in ${COMPANY.areas}. Gas Safe registered engineers. Keep your boiler safe, efficient, and warranty compliant.`,
};

export default function BoilerServicingPage() {
  return (
    <ServiceDetailLayout
      title="Boiler Servicing"
      subtitle="Annual boiler service by Gas Safe registered engineers. Keep your boiler safe, efficient, and covered under warranty."
      backgroundImage="/images/a2361d3b-a0e7-4df7-9753-8d55f55004f5.jpg"
      sideImage="/images/a2361d3b-a0e7-4df7-9753-8d55f55004f5.jpg"
      sideImageAlt="Boiler installed on wall with copper pipework"
      introduction={`An annual boiler service is the best way to keep your heating system safe and running efficiently. DPS Heating Services Ltd provides thorough boiler servicing across ${COMPANY.areas} carried out by Gas Safe registered engineers. A service can also be a condition of your boiler warranty, so it is important not to skip it.`}
      included={[
        "Visual inspection of boiler and flue",
        "Gas pressure and flow checks",
        "Heat exchanger inspection",
        "Flue gas analysis",
        "Safety device testing",
        "Seals and gasket check",
        "System pressure check",
        "Service report and certificate",
      ]}
      issues={[
        {
          icon: "settings",
          title: "Annual Service Due",
          description: "Boilers should be serviced every year to stay safe and efficient, and to maintain your warranty.",
        },
        {
          icon: "alertCircle",
          title: "Higher Energy Bills",
          description: "An unserviced boiler can become inefficient over time, using more gas to produce the same heat.",
        },
        {
          icon: "flame",
          title: "Strange Noises or Smells",
          description: "Unusual sounds or a faint smell may indicate a problem that a service can identify early.",
        },
        {
          icon: "checkCircle",
          title: "Moving into a New Home",
          description: "If you have just moved in, a service will confirm the boiler is safe and working correctly.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Book Your Service",
          description: "Call us or use our online form to book a convenient appointment.",
        },
        {
          icon: "settings",
          number: "02",
          title: "Engineer Arrives",
          description: "A Gas Safe registered engineer arrives at your home at the agreed time.",
        },
        {
          icon: "flame",
          number: "03",
          title: "Full Service Carried Out",
          description: "A thorough inspection and service of all key boiler components is completed.",
        },
        {
          icon: "fileText",
          number: "04",
          title: "Report Issued",
          description: "You receive a written service report and certificate for your records.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Gas Safe Registered",
          description: "All servicing is carried out by registered Gas Safe engineers.",
        },
        {
          icon: "fileText",
          title: "Written Certificate",
          description: "We provide a full service report and certificate for your records and warranty.",
        },
        {
          icon: "clock",
          title: "Quick and Convenient",
          description: "A standard boiler service takes around 45–60 minutes.",
        },
      ]}
      faqs={[
        {
          question: "How often should I have my boiler serviced?",
          answer: "Your boiler should be serviced annually by a Gas Safe registered engineer. This is often a requirement of the manufacturer warranty.",
        },
        {
          question: "How long does a boiler service take?",
          answer: "A standard boiler service usually takes 45–60 minutes.",
        },
        {
          question: "Will I receive a certificate?",
          answer: "Yes. We provide a full written service report and certificate after every service.",
        },
        {
          question: "Can servicing reduce my heating bills?",
          answer: "Yes. A well-maintained boiler runs more efficiently, which can reduce your gas consumption and lower your energy bills.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Heating", href: "/services/heating" },
        { label: "Boiler Servicing" },
      ]}
      serviceValue="boiler-servicing"
      showGasSafeNote
      accentColor="red"
    />
  );
}
