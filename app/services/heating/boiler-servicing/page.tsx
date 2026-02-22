import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "System Certification",
  description: `Annual thermal core diagnostics in ${COMPANY.areas}. Gas Safe registered operatives. Maintain operational equilibrium and warranty compliance.`,
};

export default function BoilerServicingPage() {
  return (
    <ServiceDetailLayout
      title="System Certification"
      subtitle="Exhaustive annual diagnostics and safety compliance verification by certified operatives."
      backgroundImage="/images/boiler-modern.jpg"
      sideImage="/images/boiler-modern.jpg"
      sideImageAlt="Tactical thermal core calibration"
      introduction={`A strategic maintenance cycle ensures your thermal architecture maintains peak operational equilibrium and absolute safety. Our Gas Safe operatives execute an exhaustive diagnostic protocol, covering all critical interfaces and performance vectors. Regular certification is essential for proactive fault identification and sustained manufacturer warranty compliance.`}
      included={[
        "Visual Integrity Inspection of Flue & Core",
        "Operational Gas Pressure & Flow Analysis",
        "Heat Exchange Module Triage",
        "Precision Combustion Exhaust Analysis",
        "Safety Loop & Control Interlock Testing",
        "Gasket & Structural Seal Verification",
        "Hydraulic System Pressure Calibration",
        "Digital Service Certification & Log",
      ]}
      issues={[
        {
          icon: "settings",
          title: "Maintenance Cycle Overdue",
          description: "Annual certification is mandated for optimal performance and warranty preservation.",
        },
        {
          icon: "alertCircle",
          title: "Operational Cost Variance",
          description: "Uncalibrated cores consume excessive gas to maintain thermal output thresholds.",
        },
        {
          icon: "flame",
          title: "Systemic Irregularities",
          description: "Minor acoustical or olfactory deviations identified during early-stage diagnostics.",
        },
        {
          icon: "checkCircle",
          title: "Site Acquisition",
          description: "Verify the structural condition of thermal assets following property acquisition.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Uplink Request",
          description: "Schedule your maintenance cycle via the primary portal or direct audio.",
        },
        {
          icon: "settings",
          number: "02",
          title: "Operative Inbound",
          description: "A certified Gas Safe engineer is dispatched to your coordinates at the target time.",
        },
        {
          icon: "flame",
          number: "03",
          title: "Diagnostic Execution",
          description: "Exhaustive component testing and performance optimization is carried out.",
        },
        {
          icon: "fileText",
          number: "04",
          title: "System Validation",
          description: "Generation of high-integrity service records and digital compliance logs.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Certified Operatives",
          description: "All diagnostic protocols executed by high-level Gas Safe registered engineers.",
        },
        {
          icon: "fileText",
          title: "Precision Logs",
          description: "Comprehensive digital documentation provided for insurance and warranty records.",
        },
        {
          icon: "clock",
          title: "Optimized Scheduling",
          description: "Tactical appointment windows designed to minimize operational downtime.",
        },
      ]}
      faqs={[
        {
          question: "What is the frequency of certification cycles?",
          answer: "Manufacturers and safety protocols mandate an annual maintenance cycle to maintain operational integrity.",
        },
        {
          question: "Operational window for a standard service?",
          answer: "A standard thermal core diagnostic typically requires 45 to 60 minutes of field time.",
        },
        {
          question: "Is digital documentation provided?",
          answer: "Affirmative. A full structural service record is generated and transmitted on tactical completion.",
        },
        {
          question: "Does certification impact efficiency?",
          answer: "Yes. Precision calibration of combustion and hydraulic variables often leads to immediate operational savings.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Thermal", href: "/services/heating" },
        { label: "Certification" },
      ]}
      serviceValue="boiler-servicing"
      showGasSafeNote
      accentColor="red"
    />
  );
}
