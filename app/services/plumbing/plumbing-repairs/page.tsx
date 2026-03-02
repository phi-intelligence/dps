import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Hydraulic Resolution",
  description: `Rapid hydraulic restoration and breach containment in ${COMPANY.areas}. High-integrity plumbing repairs by certified operatives.`,
};

export default function PlumbingRepairsPage() {
  return (
    <ServiceDetailLayout
      title="Hydraulic Resolution"
      subtitle="Rapid containment and restoration of high-pressure hydraulic systems."
      backgroundImage="/images/plumbing-repairs.jpg"
      sideImage="/images/plumbing-repairs.jpg"
      sideImageAlt="Tactical hydraulic repair"
      introduction={`Systemic hydraulic failures require immediate containment protocols. From localized breach resolution to total circuit restoration, DPS Heating Services LTD deploys high-integrity plumbing solutions across ${COMPANY.areas}. Our qualified operatives carry an optimized hardware inventory to ensure rapid first-contact resolution for both domestic and commercial infrastructures.`}
      included={[
        "Sonic Breach Identification",
        "Primary Circuit Containment",
        "Hydraulic Node Replacement",
        "Flow Rate Optimization",
        "Pressure Gradient Calibration",
        "Infrastructure Stress Testing",
        "Total System Validation",
      ]}
      issues={[
        {
          icon: "droplets",
          title: "Systemic Breach",
          description: "Visible hydraulic exit points or moisture ingress — immediate containment required.",
        },
        {
          icon: "alertCircle",
          title: "Interface Attrition",
          description: "Dripping tap nodes wasting significant water volumes and indicating seal decay.",
        },
        {
          icon: "gauge",
          title: "Pressure Decay",
          description: "Low hydraulic output indicating potential circuit blockages or supply-side failure.",
        },
        {
          icon: "wrench",
          title: "Valve Failure",
          description: "Isolation and containment hardware experiencing mechanical transition failure.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Triage Alert",
          description: "Connect via the uplink. Describe the hydraulic deviation for tactical preparation.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "Operative Deployment",
          description: "Rapid dispatch of a certified plumber to your coordinates for breach analysis.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Technical Execution",
          description: "Resolution of the hydraulic fault using high-grade components and precision tools.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Integrity Sign-off",
          description: "Pressure testing and structural verification before site departure.",
        },
      ]}
      trustPoints={[
        {
          icon: "zap",
          title: "Rapid Deployment",
          description: "Same-day priority routing for critical hydraulic containment throughout the zone.",
        },
        {
          icon: "shield",
          title: "Insured Integrity",
          description: "All operatives are fully insured for high-stakes domestic and commercial deployment.",
        },
        {
          icon: "clock",
          title: "First-Contact Resolution",
          description: "Vans equipped with an extensive component matrix to maximize immediate recovery.",
        },
      ]}
      faqs={[
        {
          question: "Logistics for urgent containment?",
          answer: "For critical breaches, we aim for sub-2-hour deployment windows. Contact the priority uplink immediately.",
        },
        {
          question: "Resolution rate on initial contact?",
          answer: "We maintain an optimized inventory protocol to ensure high rates of single-contact resolution.",
        },
        {
          question: "Containment warranties?",
          answer: "Affirmative. All hydraulic resolution work is backed by a structural integrity guarantee.",
        },
        {
          question: "Industrial infrastructure support?",
          answer: "Yes. Our operatives are certified for both residential and high-capacity commercial hydraulic systems.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Hydraulic", href: "/services/plumbing" },
        { label: "Resolution" },
      ]}
      serviceValue="plumbing-repairs"
      accentColor="red"
    />
  );
}
