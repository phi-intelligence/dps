import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Core System Deployment",
  description: `High-integrity boiler installation in ${COMPANY.areas}. Gas Safe registered architecture, next-gen systems, and full structural commissioning.`,
};

export default function BoilerInstallationPage() {
  return (
    <ServiceDetailLayout
      title="Core Installation"
      subtitle="High-integrity thermal architecture deployment by certified engineering operatives."
      backgroundImage="/images/boiler-install.jpg"
      sideImage="/images/boiler-install.jpg"
      sideImageAlt="New tactical thermal core"
      introduction={`The installation of a primary thermal core is a critical infrastructure decision. Our Gas Safe operatives design and deploy high-integrity systems tailored to your technical requirements. From initial site survey to structural commissioning and global warranty registration, we ensure your thermal architecture operates at peak efficiency from initial activation.`}
      included={[
        "Structural Site Survey",
        "Architecture Phase Planning",
        "Full Deployment to Building Code",
        "Operational Commissioning",
        "Digital Warranty Registration",
        "Legacy Hardware Decommissioning",
        "Certification of Structural Integrity",
      ]}
      issues={[
        {
          icon: "flame",
          title: "Legacy Phase 10+ Years",
          description: "Aged thermal units operate significantly below modern efficiency thresholds.",
        },
        {
          icon: "checkCircle",
          title: "Systemic Failure Rate",
          description: "Escalating repair frequency indicates total architecture instability.",
        },
        {
          icon: "gauge",
          title: "High Energy Attrition",
          description: "Inefficient cores result in excessive operational expenditure.",
        },
        {
          icon: "wrench",
          title: "Infrastructure Upgrade",
          description: "Transitioning to new property or increased thermal output requirements.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Pre-Flight Survey",
          description: "Initial reconnaissance of site coordinates and current system architecture.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Technical Schematic",
          description: "Finalization of recommended hardware modules and detailed project quote.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Active Deployment",
          description: "Operatives execute the installation with surgical precision and site protection.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Uplink & Registry",
          description: "Final commissioning, safety verification, and remote warranty initialization.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Absolute Compliance",
          description: "Deployments fully certified and compliant with all technical regulations.",
        },
        {
          icon: "star",
          title: "Tier 1 Modules",
          description: "We install Worcester Bosch, Vaillant, Baxi, and high-performance industrial units.",
        },
        {
          icon: "clock",
          title: "Rapid Lead-Times",
          description: "Total architecture displacement and reactivation typically completed within one operational cycle.",
        },
      ]}
      faqs={[
        {
          question: "What is the duration of a standard deployment?",
          answer: "A primary core replacement typically consumes one full operational day. Complex multi-zone architectures may require extended deployment windows.",
        },
        {
          question: "Which hardware platforms are supported?",
          answer: "We support and install all Tier 1 manufacturers including Worcester Bosch, Vaillant, Baxi, Ideal, and Viessmann.",
        },
        {
          question: "Will site aesthetics be impacted?",
          answer: "Minimal impact. We utilize high-level site protection and ensure comprehensive workspace sanitation post-deployment.",
        },
        {
          question: "What assurance protocols are in place?",
          answer: "Most primary modules include a 5-12 year structural warranty when deployed by our certified operatives. We manage all digital registration protocols.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Thermal", href: "/services/heating" },
        { label: "Installation" },
      ]}
      serviceValue="boiler-installation"
      showGasSafeNote
      accentColor="red"
    />
  );
}
