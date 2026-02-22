import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Climate Control Deployment",
  description: `Next-gen AC installation in ${COMPANY.areas}. Domestic and commercial thermal management solution deployment.`,
};

export default function ACInstallationPage() {
  return (
    <ServiceDetailLayout
      title="Climate Control"
      subtitle="Strategic deployment of high-efficiency thermal management systems."
      backgroundImage="/images/ac-installation.jpg"
      sideImage="/images/ac-installation.jpg"
      sideImageAlt="Tactical climate control deployment"
      introduction={`We architect and deploy a comprehensive matrix of air conditioning systems for domestic and commercial environments across ${COMPANY.areas}. From single-split thermal units to complex multi-zone climate architectures, we manage the entire deployment lifecycle — from reconnaissance and schematic design to final commissioning and operative training. Our systems utilize Tier 1 hardware for maximum environmental control.`}
      included={[
        "Site Reconnaissance & Schematic Design",
        "Hardware Platform Recommendation",
        "Full Infrastructure Integration (Electrical/Circuit)",
        "System Commissioning & Performance Matrix",
        "Digital Interface & App Initialization",
        "Operative Training on System Parameters",
        "Structural Sign-off Certification",
      ]}
      issues={[
        {
          icon: "wind",
          title: "Thermal Saturation",
          description: "Internal environments exceeding comfortable operative thresholds during peak solar cycles.",
        },
        {
          icon: "checkCircle",
          title: "Infrastructure Optimization",
          description: "Commercial environments requiring precision climate control to maintain staff productivity.",
        },
        {
          icon: "clipboardList",
          title: "Core Construction",
          description: "The optimal phase for climate control integration is during initial structural build or renovation.",
        },
        {
          icon: "wrench",
          title: "Platform Obsolescence",
          description: "Legacy environmental systems operating significantly below modern efficiency curves.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Initial Recon",
          description: "Field visit to assess structural coordinates and environmental requirements.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Technical Proposal",
          description: "Generation of written schematics, hardware selection, and deployment logistics.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Active Integration",
          description: "Engineering operatives execute the full deployment with minimal site disruption.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Final Activation",
          description: "System commissioning, performance verification, and user-interface training.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "F-Gas Certified",
          description: "All operatives hold full compliance certifications for refrigerant management.",
        },
        {
          icon: "star",
          title: "Tier 1 Platforms",
          description: "We deploy Mitsubishi, Daikin, LG, Samsung, and high-spec industrial systems.",
        },
        {
          icon: "zap",
          title: "Efficiency Optimized",
          description: "Prioritizing high-SEER hardware to minimize long-term operational expenditure.",
        },
      ]}
      faqs={[
        {
          question: "Logistics for residential deployment?",
          answer: "Architecture is determined by structural layout. Our reconnaissance phase identifies the optimal hardware for your coordinates.",
        },
        {
          question: "Deployment timeline for standard systems?",
          answer: "A single-split thermal node typically requires one operational day. Multi-zone architectures vary by complexity.",
        },
        {
          question: "Regulatory constraints?",
          answer: "Most domestic deployments fall under Permitted Development. Our technical leads will advise if special authorization is required.",
        },
        {
          question: "Supported Hardware Platforms?",
          answer: "We support Mitsubishi Electric, Daikin, LG, Samsung, Panasonic, and other high-integrity environmental systems.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Climate", href: "/services/air-conditioning" },
        { label: "Deployment" },
      ]}
      serviceValue="ac-installation"
      accentColor="red"
    />
  );
}
