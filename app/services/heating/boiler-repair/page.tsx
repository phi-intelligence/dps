import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Thermodynamic Repair",
  description: `Expert hydraulic and thermal recovery in ${COMPANY.areas}. Gas Safe registered engineers, rapid fault isolation.`,
};

export default function BoilerRepairPage() {
  return (
    <ServiceDetailLayout
      title="Thermodynamic Repair"
      subtitle="Rapid-response hydraulic and thermal system restoration by Gas Safe operatives."
      backgroundImage="/images/boiler-repair.jpg"
      sideImage="/images/boiler-repair.jpg"
      sideImageAlt="Tactical boiler diagnostics"
      introduction={`When your thermal core fails, rapid deployment is essential. DPS Heating Services Ltd provides advanced thermodynamic repair across ${COMPANY.areas}. Our Gas Safe operatives utilize high-precision diagnostics to isolate faults and restore system integrity, with a primary mission of first-visit resolution.`}
      included={[
        "Real-time Fault Isolation",
        "Error Code Diagnostics",
        "Hydraulic Pressure Balancing",
        "Critical Component Calibration",
        "Safety Loop Verification",
        "System Log Generation",
      ]}
      issues={[
        {
          icon: "alertCircle",
          title: "Acoustical Deviation",
          description: "Kettling or internal vibrations indicating secondary heat exchange contamination or pump failure.",
        },
        {
          icon: "thermometer",
          title: "Thermal Output Failure",
          description: "Complete cessation of heat generation. Critical status requiring immediate triage.",
        },
        {
          icon: "gauge",
          title: "Pressure Attrition",
          description: "Consistent hydraulic pressure loss indicative of a breach in the primary circuit.",
        },
        {
          icon: "flame",
          title: "Combustion Instability",
          description: "Pilot light failure or intermittent ignition sequence interruption.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Triage Signal",
          description: "Connect via the uplink. Describe the system deviation for preliminary analysis.",
        },
        {
          icon: "alertCircle",
          number: "02",
          title: "Field Deployment",
          description: "Our certified operative reaches your coordinates for physical diagnostics.",
        },
        {
          icon: "wrench",
          number: "03",
          title: "Node Resolution",
          description: "System recovery is executed using high-integrity components and precision tools.",
        },
        {
          icon: "shield",
          number: "04",
          title: "Operational Sign-off",
          description: "Exhaustive safety matrix testing is performed before system reactivation.",
        },
      ]}
      trustPoints={[
        {
          icon: "clock",
          title: "Rapid Deployment",
          description: "Priority routing for critical failures throughout our operational zone.",
        },
        {
          icon: "shield",
          title: "Certified Integrity",
          description: "All work executed by Gas Safe registered engineering operatives only.",
        },
        {
          icon: "flame",
          title: "Multi-Platform Support",
          description: "Expertise across all major architectures — Worcester, Vaillant, Baxi, and industrial units.",
        },
      ]}
      faqs={[
        {
          question: "What are the logistics for repair costs?",
          answer:
            "Fees are determined by fault complexity and required hardware modules. We provide transparent transmission of costs prior to execution.",
        },
        {
          question: "What is the timeline for system recovery?",
          answer:
            "Standard repairs are typically resolved within a 2-hour operational window on the initial deployment.",
        },
        {
          question: "Are component modules stored in-vehicle?",
          answer:
            "Affirmative. Our operatives carry an optimized inventory of high-frequency failure components.",
        },
        {
          question: "Is decommissioning required?",
          answer:
            "In scenarios where legacy systems are beyond structural integrity thresholds, we may recommend a total architecture upgrade.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Thermal", href: "/services/heating" },
        { label: "Repair" },
      ]}
      serviceValue="boiler-repair"
      showGasSafeNote
      accentColor="red"
    />
  );
}
