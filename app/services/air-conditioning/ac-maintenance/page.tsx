import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "AC Maintenance Contracts",
  description: `Air conditioning maintenance contracts in ${COMPANY.areas}. Scheduled servicing to keep your systems reliable and efficient all year round.`,
};

export default function ACMaintenancePage() {
  return (
    <ServiceDetailLayout
      title="AC Maintenance Contracts"
      subtitle="Scheduled maintenance plans to keep your air conditioning systems running reliably and efficiently throughout the year."
      backgroundImage="/images/ac-unit-indoor.jpg"
      sideImage="/images/ac-installation.jpg"
      sideImageAlt="Air conditioning maintenance visit"
      introduction={`A maintenance contract is the easiest way to keep your air conditioning system in top condition. DPS Heating Services Ltd offers flexible maintenance plans for both domestic and commercial customers across ${COMPANY.areas}. With a contract in place, you get scheduled servicing, priority response times, and peace of mind that your system is being looked after professionally.`}
      included={[
        "Scheduled annual or bi-annual service visits",
        "Full system inspection and cleaning",
        "Filter and coil maintenance",
        "Refrigerant level checks",
        "Electrical component testing",
        "Priority booking for repairs",
        "Written service reports after each visit",
        "Reminder notifications for upcoming visits",
      ]}
      issues={[
        {
          icon: "settings",
          title: "Multiple AC Systems",
          description: "If you have several systems across your property, a maintenance contract makes servicing straightforward and cost-effective.",
        },
        {
          icon: "wind",
          title: "Commercial Premises",
          description: "Commercial AC systems rely on regular maintenance to stay efficient and compliant.",
        },
        {
          icon: "checkCircle",
          title: "Warranty Requirements",
          description: "Many AC manufacturers require regular servicing to maintain the warranty on the system.",
        },
        {
          icon: "clock",
          title: "Hassle-Free Maintenance",
          description: "A maintenance contract means you do not have to remember to book a service each year — we handle it for you.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Get in Touch",
          description: "Contact us to discuss your systems and requirements. We will put together the right plan for you.",
        },
        {
          icon: "clipboardList",
          number: "02",
          title: "Agree Your Plan",
          description: "We agree on the frequency and scope of visits, and you receive a clear contract.",
        },
        {
          icon: "settings",
          number: "03",
          title: "Scheduled Visits",
          description: "We carry out all scheduled service visits at convenient times with advance notice.",
        },
        {
          icon: "fileText",
          number: "04",
          title: "Reports and Records",
          description: "You receive a service report after every visit, keeping your maintenance records up to date.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Qualified Engineers",
          description: "All maintenance work is carried out by qualified, F-Gas certified engineers.",
        },
        {
          icon: "clock",
          title: "Priority Response",
          description: "Contract customers receive priority booking when repairs are needed.",
        },
        {
          icon: "star",
          title: "Flexible Plans",
          description: "We tailor maintenance plans to suit your systems, schedule, and budget.",
        },
      ]}
      faqs={[
        {
          question: "What does a maintenance contract include?",
          answer: "Plans include scheduled service visits, full system checks, cleaning, and written reports. Additional services such as repair priority can be added.",
        },
        {
          question: "How often are service visits included?",
          answer: "We typically offer annual or bi-annual visit plans. Commercial customers with heavy-use systems may benefit from more frequent visits.",
        },
        {
          question: "Can I get a contract for a single unit?",
          answer: "Yes. We offer plans for both single domestic units and multi-system commercial installations.",
        },
        {
          question: "What happens if my system needs a repair between visits?",
          answer: "Contract customers receive priority response for repair callouts and may benefit from discounted parts and labour rates.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Air Conditioning", href: "/services/air-conditioning" },
        { label: "Maintenance Contracts" },
      ]}
      serviceValue="ac-maintenance"
      accentColor="blue"
    />
  );
}
