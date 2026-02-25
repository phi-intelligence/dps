import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Domestic Mechanical Services",
  description: `Domestic mechanical services including heating installation, pipework, and maintenance across ${COMPANY.areas}.`,
};

export default function DomesticMechanicalServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Mechanical Services"
      subtitle={`Heating system installation, pipework, and maintenance for homes across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/our-services-domestic.png"
      sideImageAlt="Domestic heating and mechanical systems"
      introduction={`DPS Heating Services delivers mechanical solutions for domestic clients across ${COMPANY.areas}. From heating system installation and upgrades to radiator and pipework installation, preventative maintenance, and reactive repairs, our qualified engineers keep your home heating running safely and efficiently.`}
      included={CORE_SERVICE_SECTOR_SERVICES.mechanical.domestic}
      issues={[
        {
          icon: "settings",
          title: "System Inefficiency",
          description: "Older or poorly maintained heating and pipework can waste energy and increase bills.",
        },
        {
          icon: "thermometer",
          title: "Heating Upgrades",
          description: "Upgrading your heating system or pipework can improve comfort and reduce long-term costs.",
        },
        {
          icon: "checkCircle",
          title: "Reactive Repairs",
          description: "When something fails, our engineers provide fast fault finding and repair to get you back up and running.",
        },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Contact us to describe your requirements or report a fault." },
        { icon: "search", number: "02", title: "Assessment & Quote", description: "We assess the job and provide a clear quote before any work begins." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our qualified engineers complete installation, maintenance, or repairs to a high standard." },
        { icon: "checkCircle", number: "04", title: "Handover & Advice", description: "We hand over the system with any relevant documentation and advice." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Qualified Engineers", description: "All mechanical work is carried out by trained, experienced engineers." },
        { icon: "fileText", title: "Clear Documentation", description: "We provide documentation and records where required for warranty and peace of mind." },
        { icon: "clock", title: "Responsive Service", description: "Planned maintenance and reactive callouts when you need us." },
      ]}
      faqs={[
        { question: "What is included in domestic mechanical maintenance?", answer: "We cover heating system checks, radiator and pipework checks, and preventative servicing tailored to your home system." },
        { question: "Do you install new heating systems?", answer: "Yes. We install and upgrade domestic heating systems, radiators, and pipework across London, Kent, Essex and Surrey." },
        { question: "How often should I have my heating system serviced?", answer: "We recommend annual servicing for most systems. We can advise on the right schedule for your setup." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Mechanical Services", href: "/services/mechanical" },
        { label: "Domestic" },
      ]}
      serviceValue="mechanical-domestic"
      accentColor="red"
    />
  );
}
