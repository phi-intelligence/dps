import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY, CORE_SERVICE_SECTOR_SERVICES } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Domestic Gas Services",
  description: `Domestic gas installation, servicing, landlord CP12, and emergency callouts across ${COMPANY.areas}. Gas Safe registered.`,
};

export default function DomesticGasServicesPage() {
  return (
    <ServiceDetailLayout
      title="Domestic Gas Services"
      subtitle={`Gas installation and servicing, landlord gas safety (CP12), and emergency callouts for homes across ${COMPANY.areas}. Gas Safe registered.`}
      backgroundImage="/images/our-services-domestic.png"
      sideImage="/images/our-services-domestic.png"
      sideImageAlt="Domestic gas safety inspection and boiler servicing"
      introduction={`All domestic gas work at DPS Heating Services is carried out by Gas Safe registered engineers across ${COMPANY.areas}. We provide gas installation and servicing, landlord gas safety certification (CP12), boiler installation and repairs, system diagnosis, and emergency callouts. Safety and compliance are at the heart of everything we do.`}
      included={CORE_SERVICE_SECTOR_SERVICES.gas.domestic}
      issues={[
        { icon: "flame", title: "Boiler or Appliance Fault", description: "Gas appliances should be serviced regularly and repaired by Gas Safe registered engineers only." },
        { icon: "shield", title: "Landlord Gas Safety (CP12)", description: "Landlords must have annual gas safety checks carried out by a Gas Safe registered engineer." },
        { icon: "alertCircle", title: "Gas Emergency", description: "If you smell gas or suspect a leak, turn off the supply, ventilate, and call the gas emergency number. We can then support with repairs." },
        { icon: "checkCircle", title: "New Installation or Upgrade", description: "Gas boiler and appliance installation must be done by Gas Safe registered engineers for safety and warranty." },
      ]}
      steps={[
        { icon: "phone", number: "01", title: "Get in Touch", description: "Call us or use our online form to book a service, inspection, or report an issue." },
        { icon: "search", number: "02", title: "Quote & Appointment", description: "We provide a clear quote and arrange a convenient appointment with a Gas Safe engineer." },
        { icon: "wrench", number: "03", title: "Work Carried Out", description: "Our Gas Safe registered engineer completes the work to the required safety standards." },
        { icon: "fileText", number: "04", title: "Certificate & Report", description: "You receive the relevant certificate (e.g. CP12) or report for your records." },
      ]}
      trustPoints={[
        { icon: "shield", title: "Gas Safe Registered", description: "All gas work is carried out by Gas Safe registered engineers." },
        { icon: "fileText", title: "Certificates Provided", description: "We issue CP12 and other certificates where required for landlords and compliance." },
        { icon: "clock", title: "Emergency Callouts", description: "We offer 24/7 emergency callouts for gas-related issues where safe to do so." },
      ]}
      faqs={[
        { question: "Are you Gas Safe registered?", answer: "Yes. All gas work is carried out by Gas Safe registered engineers. Our registration details can be verified on the Gas Safe Register website." },
        { question: "Do you do landlord gas safety checks (CP12)?", answer: "Yes. We carry out landlord gas safety inspections and issue CP12 certificates for rental properties across London, Kent, Essex and Surrey." },
        { question: "Do you offer emergency gas callouts?", answer: "We offer emergency callouts for gas-related issues. If you smell gas or have a gas emergency, you must call the gas emergency number first; we can then assist with any repairs once the situation is safe." },
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
