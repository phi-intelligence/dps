import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Commercial Electrical Services",
  description: `Commercial electrical installations, compliance inspections, and maintenance contracts across ${COMPANY.areas}.`,
};

export default function CommercialElectricalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Electrical Services"
      subtitle={`Electrical installations, fault finding, compliance inspections, and maintenance contracts for commercial premises across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/our-services-commercial.png"
      sideImageAlt="Commercial electrical testing and installation"
      introduction={`DPS Heating Services provides electrical installation, testing, and maintenance for commercial clients across ${COMPANY.areas}. From new installations and upgrades to fault finding, compliance inspections, maintenance contracts, and emergency lighting, our engineers help keep your commercial electrical systems safe and compliant.`}
      included={CORE_SERVICE_SECTOR_SERVICES.electrical.commercial}
      issues={[
        { icon: "zap", title: "Faults or Tripping", description: "Recurring trips or unexplained faults need professional testing and diagnosis to ensure safety." },
        { icon: "alertCircle", title: "Compliance Requirements", description: "Commercial premises often require periodic electrical inspections and certificates." },
        { icon: "settings", title: "Upgrades or New Installations", description: "Refurbishment or system upgrades need qualified electrical design and installation." },
        { icon: "fileText", title: "Maintenance Contracts", description: "Planned electrical maintenance reduces the risk of failure and supports compliance." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Contact us with your commercial electrical requirements or to report a fault." },
        { icon: "search", number: "02", title: "Assessment & Quote", description: "We assess the work required and provide a clear, no-obligation quote." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our qualified engineers complete installation, testing, or repairs to the required standards." },
        { icon: "fileText", number: "04", title: "Certification & Handover", description: "Where applicable we provide certificates and documentation for your records." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified & Compliant", description: "Electrical work is carried out by qualified engineers in line with current regulations." },
        { icon: "fileText", title: "Certificates & Reports", description: "We provide test certificates and inspection reports where required." },
        { icon: "clock", title: "Fault Finding & Response", description: "Fast fault finding and repair to minimise disruption and maintain safety." },
      ]}
      faqs={[
        { question: "What commercial electrical work do you carry out?", answer: "We provide electrical installations and upgrades, fault finding and testing, compliance inspections, maintenance contracts, and emergency lighting for commercial premises." },
        { question: "Do you provide electrical certificates for commercial properties?", answer: "Yes. We provide appropriate certificates and reports for the work carried out, including inspection and test documentation where required." },
        { question: "Are you available for emergency electrical faults?", answer: "We offer responsive callouts for electrical faults. Contact us to discuss availability and we will prioritise where there is a safety concern." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Electrical Services", href: "/services/electrical" },
        { label: "Commercial" },
      ]}
      serviceValue="electrical-commercial"
      accentColor="red"
    />
  );
}
