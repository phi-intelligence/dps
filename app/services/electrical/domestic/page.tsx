import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Domestic Electrical Services",
  description: `Domestic electrical installations, fault finding, and landlord safety inspections across ${COMPANY.areas}.`,
};

export default function DomesticElectricalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Electrical Services"
      subtitle={`Electrical installations, fault finding, and safety inspections for homes across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/our-services-domestic.png"
      sideImageAlt="Domestic electrical testing and installation"
      introduction={`DPS Heating Services provides electrical installation, testing, and maintenance for domestic clients across ${COMPANY.areas}. From new installations and consumer unit upgrades to fault finding, landlord electrical safety inspections, and reactive repairs, our engineers help keep your home electrical systems safe and compliant.`}
      included={CORE_SERVICE_SECTOR_SERVICES.electrical.domestic}
      issues={[
        { icon: "zap", title: "Faults or Tripping", description: "Recurring trips or unexplained faults need professional testing and diagnosis to ensure safety." },
        { icon: "alertCircle", title: "Landlord or Compliance", description: "Rental properties often require periodic electrical inspections and certificates." },
        { icon: "settings", title: "Upgrades or New Installations", description: "Consumer unit upgrades or new circuits need qualified electrical work." },
        { icon: "fileText", title: "Maintenance & Repairs", description: "We carry out reactive repairs and maintenance to keep your home safe." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Contact us with your electrical requirements or to report a fault." },
        { icon: "search", number: "02", title: "Assessment & Quote", description: "We assess the work required and provide a clear, no-obligation quote." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our qualified engineers complete installation, testing, or repairs to the required standards." },
        { icon: "fileText", number: "04", title: "Certification & Handover", description: "Where applicable we provide certificates and documentation for your records." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified & Compliant", description: "Electrical work is carried out by qualified engineers in line with current regulations." },
        { icon: "fileText", title: "Certificates & Reports", description: "We provide test certificates and inspection reports where required." },
        { icon: "clock", title: "Fault Finding & Response", description: "Fast fault finding and repair to minimise disruption." },
      ]}
      faqs={[
        { question: "What domestic electrical work do you carry out?", answer: "We provide electrical installations and upgrades, fault finding and testing, landlord electrical safety inspections, consumer unit upgrades, and maintenance and reactive repairs for homes." },
        { question: "Do you provide electrical certificates for landlords?", answer: "Yes. We carry out electrical safety inspections and provide appropriate certificates and reports where required for rental properties." },
        { question: "Are you available for emergency electrical faults?", answer: "We offer responsive callouts for electrical faults. Contact us to discuss availability." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Electrical Services", href: "/services/electrical" },
        { label: "Domestic" },
      ]}
      serviceValue="electrical-domestic"
      accentColor="red"
    />
  );
}
