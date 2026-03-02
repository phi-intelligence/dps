import type { Metadata } from "next";
import ServiceDetailLayout, { type ServiceCard } from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

const DOMESTIC_GAS_SERVICE_CARDS: ServiceCard[] = [
  {
    title: "Boiler installation & replacement",
    description: "Supply and installation of new gas boilers for your home. We advise on the right size and type, install to current standards and commission the system for you.",
    image: "/images/boiler-install.jpg",
    imageAlt: "Domestic boiler installation",
  },
  {
    title: "Boiler servicing",
    description: "Annual boiler servicing to maintain efficiency, safety and warranty. Our Gas Safe engineers check burners, flues and safety devices and leave you with a service record.",
    image: "/images/boiler-modern.jpg",
    imageAlt: "Modern boiler servicing",
  },
  {
    title: "Boiler repairs & breakdowns",
    description: "Fast diagnosis and repair of boiler breakdowns. We get your heating and hot water back on with minimal fuss and explain what was wrong.",
    image: "/images/boiler-repair.jpg",
    imageAlt: "Boiler repair",
  },
  {
    title: "Landlord Gas Safety Certificates (CP12)",
    description: "Annual gas safety inspections for rental properties and issue of CP12 certificates. Landlords must use a Gas Safe registered engineer for this legal requirement.",
    image: "/images/boiler-modern.jpg",
    imageAlt: "Gas safety inspection",
  },
  {
    title: "Gas safety checks",
    description: "Gas safety checks for homeowners and tenants. We inspect appliances, flues and pipework and advise on any issues or improvements.",
    image: "/images/boiler-modern.jpg",
    imageAlt: "Gas safety check",
  },
  {
    title: "Gas leaks / emergency response",
    description: "Response to suspected gas leaks and gas-related emergencies. If you smell gas, call the emergency number first; we can then carry out repairs once the situation is safe.",
    image: "/images/emergency-callout.jpg",
    imageAlt: "Emergency gas response",
  },
  {
    title: "Gas hob / cooker installation",
    description: "Installation of gas hobs and cookers by Gas Safe registered engineers. We connect safely, test and advise on ventilation where needed.",
    image: "/images/our-services-domestic.png",
    imageAlt: "Domestic gas appliances",
  },
  {
    title: "Flue & ventilation checks",
    description: "Checks on flues and ventilation for gas appliances. Correct flue and air supply are essential for safe operation and we advise on any remedial work.",
    image: "/images/domestic-combi-boiler.png",
    imageAlt: "Flue and boiler",
  },
  {
    title: "System upgrades",
    description: "Upgrades to your existing gas system: new boilers, better controls or improved efficiency. We quote clearly and complete the work to a high standard.",
    image: "/images/central-heating.jpg",
    imageAlt: "Central heating system",
  },
];

export const metadata: Metadata = {
  title: "Domestic Gas Services",
  description: `Domestic gas boiler installation, servicing, repairs, CP12, gas safety checks, and emergency response across ${COMPANY.areas}. Gas Safe registered.`,
};

export default function DomesticGasServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Gas Services"
      subtitle={`Gas Safe registered boiler installation, servicing, repairs, landlord CP12, and gas safety for homes across ${COMPANY.areas}.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/core-services/gas.png"
      sideImageAlt="Domestic gas safety inspection and boiler servicing"
      introduction={`All domestic gas work at DPS Heating Services is carried out by Gas Safe registered engineers across ${COMPANY.areas}. We provide boiler installation and replacement, servicing, repairs and breakdowns, Landlord Gas Safety Certificates (CP12), gas safety checks, gas leak and emergency response, gas hob and cooker installation, flue and ventilation checks, and system upgrades. Safety and compliance are at the heart of everything we do.`}
      included={CORE_SERVICE_SECTOR_SERVICES.gas.domestic}
      serviceCards={DOMESTIC_GAS_SERVICE_CARDS}
      issues={[
        { icon: "flame", title: "Boiler or appliance fault", description: "Gas boilers and appliances should be serviced regularly and repaired by Gas Safe registered engineers only." },
        { icon: "shield", title: "Landlord gas safety (CP12)", description: "Landlords must have annual gas safety checks carried out by a Gas Safe registered engineer." },
        { icon: "alertCircle", title: "Gas emergency", description: "If you smell gas or suspect a leak, turn off the supply, ventilate, and call the gas emergency number. We can then support with repairs." },
        { icon: "checkCircle", title: "New installation or upgrade", description: "Boiler and appliance installation must be done by Gas Safe registered engineers for safety and warranty." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in touch", description: "Call us or use our form to book a service, safety check, or report an issue." },
        { icon: "search", number: "02", title: "Quote & appointment", description: "We provide a clear quote and arrange a convenient appointment with a Gas Safe engineer." },
        { icon: "wrench", number: "03", title: "Work carried out", description: "Our Gas Safe registered engineer completes the work to the required safety standards." },
        { icon: "fileText", number: "04", title: "Certificate & report", description: "You receive the relevant certificate (e.g. CP12) or report for your records." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Gas Safe registered", description: "All gas work is carried out by Gas Safe registered engineers." },
        { icon: "fileText", title: "Certificates provided", description: "We issue CP12 and other certificates where required for landlords and compliance." },
        { icon: "clock", title: "Emergency callouts", description: "We offer emergency callouts for gas-related issues where safe to do so." },
      ]}
      faqs={[
        { question: "Are you Gas Safe registered?", answer: "Yes. All gas work is carried out by Gas Safe registered engineers. Our registration details can be verified on the Gas Safe Register website." },
        { question: "Do you do landlord gas safety checks (CP12)?", answer: "Yes. We carry out landlord gas safety inspections and issue CP12 certificates for rental properties across London, Kent, Essex and Surrey." },
        { question: "Do you install gas hobs and cookers?", answer: "Yes. We install gas hobs and cookers and carry out flue and ventilation checks. All work is done by Gas Safe registered engineers." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Gas Services", href: "/services/gas" },
        { label: "Domestic" },
      ]}
      serviceValue="gas-domestic"
      showGasSafeNote
      accentColor="red"
    />
  );
}
