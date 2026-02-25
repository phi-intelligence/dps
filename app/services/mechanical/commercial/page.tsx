import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Commercial Mechanical Services",
  description: `Commercial mechanical services including plant room maintenance, PPM contracts, heating systems, and facilities management across ${COMPANY.areas}.`,
};

export default function CommercialMechanicalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Mechanical Services"
      subtitle={`Plant room installations, PPM contracts, commercial heating systems, and facilities management across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/our-services-commercial.png"
      sideImageAlt="Commercial plant room and mechanical systems"
      introduction={`DPS Heating Services delivers full mechanical engineering solutions for commercial clients across ${COMPANY.areas}. From plant room installations and PPM contracts to commercial heating systems, pipework, and reactive maintenance, our qualified engineers keep your commercial mechanical systems running safely and efficiently.`}
      included={CORE_SERVICE_SECTOR_SERVICES.mechanical.commercial}
      issues={[
        {
          icon: "settings",
          title: "System Inefficiency",
          description: "Older or poorly maintained commercial heating and pipework systems can waste energy and increase running costs.",
        },
        {
          icon: "alertCircle",
          title: "Plant Room Issues",
          description: "Commercial plant rooms require regular inspection and maintenance to avoid breakdowns and compliance failures.",
        },
        {
          icon: "thermometer",
          title: "Heating Upgrades",
          description: "Upgrading commercial heating or pipework can improve performance and reduce long-term costs.",
        },
        {
          icon: "checkCircle",
          title: "Reactive Repairs",
          description: "When something fails, our engineers provide fast fault finding and repair to minimise downtime.",
        },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Contact us to describe your commercial mechanical requirements or report a fault." },
        { icon: "search", number: "02", title: "Assessment & Quote", description: "We assess the job and provide a clear quote before any work begins." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our qualified engineers complete installation, maintenance, or repairs to a high standard." },
        { icon: "checkCircle", number: "04", title: "Handover & Documentation", description: "We hand over the system with any relevant documentation and advice." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified Engineers", description: "All mechanical work is carried out by trained, experienced engineers." },
        { icon: "fileText", title: "Clear Documentation", description: "We provide documentation and records where required for compliance and warranty." },
        { icon: "clock", title: "Responsive Service", description: "Planned maintenance and reactive callouts to keep your commercial systems running." },
      ]}
      faqs={[
        { question: "What is included in commercial mechanical maintenance?", answer: "We cover heating system checks, plant room inspections, pipework and valve checks, and preventative servicing tailored to your commercial system, plus PPM contracts where required." },
        { question: "Do you work on commercial plant rooms?", answer: "Yes. We install, maintain, and repair commercial plant rooms and associated pipework and controls across London, Kent, Essex and Surrey." },
        { question: "How often should commercial mechanical systems be maintained?", answer: "Frequency depends on the system and use. We can advise on a suitable maintenance schedule and offer PPM contracts for commercial clients." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Mechanical Services", href: "/services/mechanical" },
        { label: "Commercial" },
      ]}
      serviceValue="mechanical-commercial"
      accentColor="red"
    />
  );
}
