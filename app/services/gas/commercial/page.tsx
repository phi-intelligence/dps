import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Commercial Gas Services",
  description: `Commercial gas installation, servicing, safety inspections, and emergency callouts across ${COMPANY.areas}. Gas Safe registered.`,
};

export default function CommercialGasServicesPage() {
  return (
    <ServiceDetailLayout
      title="Commercial Gas Services"
      subtitle={`Commercial gas installation, servicing, safety inspections, and PPM across ${COMPANY.areas}. Gas Safe registered.`}
      backgroundImage="/images/our-services-commercial.png"
      sideImage="/images/our-services-commercial.png"
      sideImageAlt="Commercial gas safety inspection and maintenance"
      introduction={`All commercial gas work at DPS Heating Services is carried out by Gas Safe registered engineers across ${COMPANY.areas}. We provide commercial gas installation and servicing, gas safety inspections, commercial boiler servicing and repair, PPM and planned gas maintenance, and 24-hour emergency callouts. Safety and compliance are at the heart of everything we do.`}
      included={CORE_SERVICE_SECTOR_SERVICES.gas.commercial}
      issues={[
        { icon: "flame", title: "Boiler or Appliance Fault", description: "Commercial gas appliances should be serviced regularly and repaired by Gas Safe registered engineers only." },
        { icon: "shield", title: "Gas Safety Inspections", description: "Commercial premises often require regular gas safety inspections and certification." },
        { icon: "alertCircle", title: "Gas Emergency", description: "If you smell gas or suspect a leak, turn off the supply, ventilate, and call the gas emergency number. We can then support with repairs." },
        { icon: "checkCircle", title: "New Installation or Upgrade", description: "Commercial gas boiler and appliance installation must be done by Gas Safe registered engineers for safety and warranty." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Call us or use our online form to book a service, inspection, or report an issue." },
        { icon: "search", number: "02", title: "Quote & Appointment", description: "We provide a clear quote and arrange a convenient appointment with a Gas Safe engineer." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our Gas Safe registered engineer completes the work to the required safety standards." },
        { icon: "fileText", number: "04", title: "Certificate & Report", description: "You receive the relevant certificate or report for your records and compliance." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Gas Safe Registered", description: "All gas work is carried out by Gas Safe registered engineers." },
        { icon: "fileText", title: "Certificates Provided", description: "We issue gas safety certificates and reports where required for commercial compliance." },
        { icon: "clock", title: "Emergency Callouts", description: "We offer 24/7 emergency callouts for gas-related issues where safe to do so." },
      ]}
      faqs={[
        { question: "Are you Gas Safe registered for commercial work?", answer: "Yes. All gas work is carried out by Gas Safe registered engineers. Our registration details can be verified on the Gas Safe Register website." },
        { question: "Do you provide commercial gas safety inspections?", answer: "Yes. We carry out gas safety inspections and issue the relevant certificates for commercial premises across London, Kent, Essex and Surrey." },
        { question: "Do you offer emergency gas callouts for commercial?", answer: "We offer emergency callouts for gas-related issues. If you smell gas or have a gas emergency, you must call the gas emergency number first; we can then assist with any repairs once the situation is safe." },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Gas Services", href: "/services/gas" },
        { label: "Commercial" },
      ]}
      serviceValue="gas-commercial"
      showGasSafeNote
      accentColor="red"
    />
  );
}
