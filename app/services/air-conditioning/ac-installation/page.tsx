import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "AC Installation",
  description: `Professional air conditioning installation in ${COMPANY.areas}. Domestic and commercial systems, all major brands, full commissioning.`,
};

export default function ACInstallationPage() {
  return (
    <ServiceDetailLayout
      title="AC Installation"
      subtitle="Professional supply and installation of air conditioning systems for homes and businesses."
      backgroundImage="/images/ac-installation.jpg"
      sideImage="/images/ac-installation.jpg"
      sideImageAlt="Air conditioning unit being installed"
      introduction={`DPS Heating Services Ltd installs a wide range of air conditioning systems for homes and businesses across ${COMPANY.areas}. Whether you need a single-room split system for your home or a multi-zone commercial installation, we manage the entire process from survey and design through to commissioning and handover. All our engineers are F-Gas certified.`}
      included={[
        "Free site survey and design",
        "System and brand recommendation",
        "Full electrical installation",
        "Commissioning and performance testing",
        "User controls and app setup",
        "Full handover and user training",
        "Installation certificate",
      ]}
      issues={[
        {
          icon: "wind",
          title: "Rooms Getting Too Hot",
          description: "If your home or office overheats in summer, an air conditioning system provides effective and efficient cooling.",
        },
        {
          icon: "checkCircle",
          title: "Improving Workplace Comfort",
          description: "Comfortable temperature control can improve concentration and productivity in offices and commercial spaces.",
        },
        {
          icon: "clipboardList",
          title: "New Build or Renovation",
          description: "The best time to install air conditioning is during a build or renovation, with minimal disruption.",
        },
        {
          icon: "wrench",
          title: "Replacing an Old System",
          description: "Modern AC systems are significantly more efficient than older units, reducing running costs.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Free Survey",
          description: "We visit your property to assess your needs and recommend the right system.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Written Proposal",
          description: "You receive a detailed quote with the recommended system and full installation costs.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Installation",
          description: "Our engineers complete the installation neatly and with minimal disruption to your property.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Commissioning & Handover",
          description: "The system is tested, you are shown how to use it, and you receive all documentation.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "F-Gas Certified",
          description: "All engineers hold the necessary F-Gas certification for refrigerant handling.",
        },
        {
          icon: "star",
          title: "Leading Brands",
          description: "We install Mitsubishi Electric, Daikin, LG, Samsung, and other top brands.",
        },
        {
          icon: "zap",
          title: "Energy Efficient",
          description: "We recommend the most energy-efficient systems to keep running costs low.",
        },
      ]}
      faqs={[
        {
          question: "What type of AC system is right for my home?",
          answer: "This depends on the size and layout of your property. Our survey will identify the best option and we will explain the choices clearly.",
        },
        {
          question: "How long does installation take?",
          answer: "A single split system usually takes one day. Multi-zone installations take longer depending on the number of units.",
        },
        {
          question: "Do I need planning permission?",
          answer: "Most domestic installations fall under Permitted Development. We will advise you if planning permission is required for your specific situation.",
        },
        {
          question: "Which brands do you install?",
          answer: "We work with Mitsubishi Electric, Daikin, LG, Samsung, Panasonic, and Fujitsu. We can advise on the best option for your needs and budget.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Air Conditioning", href: "/services/air-conditioning" },
        { label: "AC Installation" },
      ]}
      serviceValue="ac-installation"
      accentColor="red"
    />
  );
}
