import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Environmental Calibration",
  description: `Strategic AC maintenance and thermal calibration in ${COMPANY.areas}. Optimize environmental output and infrastructure longevity.`,
};

export default function ACServicingPage() {
  return (
    <ServiceDetailLayout
      title="Calibration"
      subtitle="Exhaustive thermal maintenance and environmental calibration for sustained efficiency."
      backgroundImage="/images/ac-unit-indoor.jpg"
      sideImage="/images/ac-unit-indoor.jpg"
      sideImageAlt="Tactical environmental management"
      introduction={`Strategic maintenance modules ensure your environmental management hardware operates at maximum efficiency thresholds. DPS Heating Services Ltd executes high-level AC calibration for domestic and commercial architectures across ${COMPANY.areas}. Our operatives are specialized in refrigerant fluid dynamics and mechanical node optimization for all Tier 1 manufacturers.`}
      included={[
        "Internal & External Node Inspection",
        "Filtration Membrane Cleansing/Replacement",
        "Thermal Coil Decontamination",
        "Refrigerant Fluid Dynamics Analysis",
        "Electronic Control Loop Verification",
        "Condensate Drainage Pathway Clearing",
        "Thermal Output Performance Matrix",
        "Digital Operational Report",
      ]}
      issues={[
        {
          icon: "wind",
          title: "Thermal Output Variance",
          description: "Contaminated filtration membranes and coils significantly degrade environmental output.",
        },
        {
          icon: "alertCircle",
          title: "Acoustical Anomaly",
          description: "Vibrations or olfactory deviations indicating microbial growth or mechanical wear.",
        },
        {
          icon: "settings",
          title: "Cycle Overdue",
          description: "Mandated annual maintenance for hardware platform stability.",
        },
        {
          icon: "checkCircle",
          title: "Efficiency Attrition",
          description: "Unmaintained environmental units consume excessive energy to reach target thermal setpoints.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Module Request",
          description: "Schedule your maintenance module via the secure portal or direct comms.",
        },
        {
          icon: "settings",
          number: "02",
          title: "Operative Inbound",
          description: "A certified refrigeration specialist is dispatched to your site coordinates.",
        },
        {
          icon: "wind",
          number: "03",
          title: "Calibration Cycle",
          description: "Exhaustive hardware inspection and performance optimization suite execution.",
        },
        {
          icon: "fileText",
          number: "04",
          title: "System Sign-off",
          description: "Generation of high-integrity digital service records and operational logs.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Certified Specialists",
          description: "All environmental calibration work executed by fully F-Gas certified engineering operatives.",
        },
        {
          icon: "fileText",
          title: "Operational Data",
          description: "Comprehensive digital reports provided for audit and maintenance log requirements.",
        },
        {
          icon: "zap",
          title: "Cross-Platform Experts",
          description: "Specialized support for Mitsubishi, Daikin, LG, Samsung, and industrial units.",
        },
      ]}
      faqs={[
        {
          question: "Required frequency of calibration?",
          answer: "Strategic maintenance cycles are mandated annually to ensure air quality, efficiency, and platform reliability.",
        },
        {
          question: "Scope of the maintenance module?",
          answer: "Includes exhaustive node cleansing, fluid diagnostics, electronic loop tests, and full performance matrix verification.",
        },
        {
          question: "Efficiency impact?",
          answer: "Yes. Optimized filtration and coil dynamics significantly reduce energy consumption and improve thermal output.",
        },
        {
          question: "Supported platforms?",
          answer: "We support all major architectures including Mitsubishi Electric, Daikin, LG, Samsung, Panasonic, and Fujitsu.",
        },
      ]}
      breadcrumbs={[
        { label: "Core", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Climate", href: "/services/air-conditioning" },
        { label: "Calibration" },
      ]}
      serviceValue="ac-servicing"
      accentColor="red"
    />
  );
}
