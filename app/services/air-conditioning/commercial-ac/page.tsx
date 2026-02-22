import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Commercial Air Conditioning",
  description: `Commercial air conditioning installation and maintenance in ${COMPANY.areas}. Professional solutions for offices, retail, and commercial premises.`,
};

export default function CommercialACPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Air Conditioning"
      subtitle="Professional air conditioning solutions for offices, retail units, restaurants, and commercial premises."
      backgroundImage="/images/bb694770-ebf9-4854-877f-46073a4e9746.jpg"
      sideImage="/images/bb694770-ebf9-4854-877f-46073a4e9746.jpg"
      sideImageAlt="Commercial heating and ventilation plant room installation"
      introduction={`DPS Heating Services Ltd provides commercial air conditioning solutions for businesses across ${COMPANY.areas}. Whether you need a single system for a small office or a multi-zone solution for a larger commercial building, we design, install, and maintain AC systems that keep your staff and customers comfortable all year round. We work around your schedule to minimise disruption to your business.`}
      included={[
        "Commercial site survey and system design",
        "Supply and installation of commercial AC",
        "Multi-zone and VRF system installation",
        "Electrical connections and integration",
        "Full commissioning and handover",
        "Ongoing service and maintenance contracts",
        "Compliance documentation",
      ]}
      issues={[
        {
          icon: "checkCircle",
          title: "Office or Workspace Comfort",
          description: "Maintaining a comfortable temperature improves staff wellbeing and productivity.",
        },
        {
          icon: "wind",
          title: "Retail or Customer-Facing Environments",
          description: "A comfortable environment encourages customers to stay longer and return more often.",
        },
        {
          icon: "wrench",
          title: "Replacing Existing Systems",
          description: "We can upgrade older commercial AC systems to more efficient, quieter, and reliable modern alternatives.",
        },
        {
          icon: "settings",
          title: "Server Rooms and Technical Spaces",
          description: "We install dedicated precision cooling systems to protect sensitive equipment.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Site Survey",
          description: "We visit your premises to assess your requirements and recommend the right solution.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Proposal and Quote",
          description: "You receive a detailed written proposal with full system design and pricing.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Installation",
          description: "We work around your business hours to minimise disruption during installation.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Commissioning & Handover",
          description: "The system is commissioned, tested, and your staff are shown how to operate it.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "F-Gas Certified",
          description: "All refrigerant work is carried out by fully F-Gas certified engineers.",
        },
        {
          icon: "clock",
          title: "Minimal Disruption",
          description: "We work flexibly around your business to reduce any impact on your operations.",
        },
        {
          icon: "star",
          title: "Ongoing Support",
          description: "We offer maintenance contracts to keep your commercial systems running reliably.",
        },
      ]}
      faqs={[
        {
          question: "What types of commercial AC do you install?",
          answer: "We install split systems, multi-split systems, VRF/VRV systems, cassette units, and ceiling concealed systems depending on your requirements.",
        },
        {
          question: "Do you offer maintenance contracts?",
          answer: "Yes. We offer scheduled maintenance contracts to keep your commercial systems serviced and compliant throughout the year.",
        },
        {
          question: "Can you work out of hours to minimise disruption?",
          answer: "Yes. We can arrange out-of-hours installation and maintenance work to suit your business schedule.",
        },
        {
          question: "Which brands do you install for commercial premises?",
          answer: "We work with Mitsubishi Electric, Daikin, LG, Samsung, and other leading commercial AC brands.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Air Conditioning", href: "/services/air-conditioning" },
        { label: "Commercial AC" },
      ]}
      serviceValue="commercial-ac"
      accentColor="blue"
    />
  );
}
