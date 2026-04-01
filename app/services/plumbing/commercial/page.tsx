import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const COMMERCIAL_PLUMBING_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Commercial plumbing installation",
    description: "Planned plumbing installations for commercial sites, including plant and distribution systems.",
    image: "/imagesv2/commercial_mechanical/commercial_pipework.png",
    imageAlt: "Commercial plumbing and pipework installation",
  },
  {
    title: "Commercial plumbing repairs",
    description: "Reactive repairs for leaks, failed components, and system faults to minimise operational downtime.",
    image: "/imagesv2/commercial_mechanical/leak_detection.png",
    imageAlt: "Commercial plumbing repair and leak tracing",
  },
  {
    title: "Planned maintenance",
    description: "PPM-aligned inspections and servicing for valves, pumps, and associated plumbing infrastructure.",
    image: "/imagesv2/commercial_mechanical/general.jpg",
    imageAlt: "Commercial plumbing maintenance in plant room",
  },
];

export const metadata: Metadata = {
  title: "Commercial Plumbing Services",
  description: `Commercial plumbing installation, repairs, and planned maintenance across ${COMPANY.areas}.`,
};

export default function CommercialPlumbingServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Plumbing Services"
      subtitle={`Commercial plumbing installation, repairs, and planned maintenance across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/imagesv2/commercial_mechanical/commercial_pipework.png"
      sideImageAlt="Commercial plumbing and pipework systems"
      introduction={`DPS Heating Services provides responsive and planned commercial plumbing support across ${COMPANY.areas}. We deliver installations, reactive repairs, leak detection, and preventative maintenance to keep commercial buildings compliant, safe, and operational.`}
      included={CORE_SERVICE_SECTOR_SERVICES.plumbing.commercial}
      serviceCards={COMMERCIAL_PLUMBING_SERVICE_CARDS}
      issues={[
        { icon: "alertCircle", title: "Active leaks", description: "Leaks in commercial environments can rapidly cause downtime and property damage." },
        { icon: "settings", title: "Pipework upgrades", description: "Aging or modified systems often need upgraded pipework and valve arrangements." },
        { icon: "checkCircle", title: "Compliance checks", description: "Routine plumbing checks help maintain compliance and avoid avoidable failures." },
        { icon: "clock", title: "Reactive callouts", description: "Fast attendance is critical when faults affect daily building operations." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Scope review", description: "Share drawings, site info, or fault details with our team." },
        { icon: "search", number: "02", title: "Site assessment", description: "We assess the system and confirm scope, timeframe, and materials." },
        { icon: "wrench", number: "03", title: "Delivery", description: "Our engineers complete works to current standards with clear communication." },
        { icon: "checkCircle", number: "04", title: "Handover", description: "We test, verify, and hand over with relevant notes and advice." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Commercial-ready team", description: "Experienced engineers for occupied buildings and critical infrastructure." },
        { icon: "fileText", title: "Clear reporting", description: "Transparent updates and records for planned and reactive works." },
        { icon: "clock", title: "Responsive support", description: "Rapid callout options when commercial plumbing faults occur." },
      ]}
      faqs={[
        { question: "Do you support planned and reactive plumbing?", answer: "Yes. We handle both planned commercial plumbing works and reactive callouts." },
        { question: "Do you provide leak detection?", answer: "Yes. We carry out leak tracing, repair, and follow-up checks to verify resolution." },
        { question: "Can you align works with maintenance schedules?", answer: "Yes. We can deliver plumbing works within your broader PPM or FM schedule." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Plumbing Services", href: "/services/plumbing" },
        { label: "Commercial" },
      ]}
      serviceValue="plumbing-commercial"
      theme="luxury"
      accentColor="red"
    />
  );
}
