import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "AC Servicing",
  description: `Annual air conditioning service in ${COMPANY.areas}. Qualified engineers, all major brands, keep your system efficient and reliable.`,
};

export default function ACServicingPage() {
  return (
    <ServiceDetailLayout
      title="AC Servicing"
      subtitle="Annual air conditioning service to keep your system running efficiently, reliably, and at full performance."
      backgroundImage="/images/ac-unit-indoor.jpg"
      sideImage="/images/ac-unit-indoor.jpg"
      sideImageAlt="Engineer servicing an air conditioning unit"
      introduction={`Regular servicing is essential to keep your air conditioning system working efficiently and to extend its lifespan. DPS Heating Services LTD provides professional AC servicing for domestic and commercial systems across ${COMPANY.areas}. Our engineers are experienced with all major brands and will carry out a thorough check and clean of your system.`}
      included={[
        "Internal and external unit inspection",
        "Filter cleaning or replacement",
        "Evaporator and condenser coil cleaning",
        "Refrigerant level check",
        "Electrical component testing",
        "Condensate drain check and clear",
        "Performance test and output check",
        "Written service report",
      ]}
      issues={[
        {
          icon: "wind",
          title: "Reduced Cooling Performance",
          description: "Dirty filters and coils reduce efficiency. A service restores your system to full performance.",
        },
        {
          icon: "alertCircle",
          title: "Unusual Noises or Smells",
          description: "Strange sounds or musty smells from your AC unit can indicate a need for cleaning or a mechanical issue.",
        },
        {
          icon: "settings",
          title: "Annual Service Due",
          description: "AC systems should be serviced every year to remain efficient and to protect the warranty.",
        },
        {
          icon: "checkCircle",
          title: "Higher Running Costs",
          description: "A system that has not been serviced works harder and uses more electricity, increasing your energy bills.",
        },
      ]}
      steps={[
        {
          icon: "phone",
          number: "01",
          title: "Book a Service",
          description: "Contact us to arrange a convenient appointment for your annual AC service.",
        },
        {
          icon: "settings",
          number: "02",
          title: "Engineer Arrives",
          description: "A qualified engineer visits and carries out the full service on your system.",
        },
        {
          icon: "wind",
          number: "03",
          title: "Service Completed",
          description: "Your system is cleaned, checked, and performance tested to ensure it is working properly.",
        },
        {
          icon: "fileText",
          number: "04",
          title: "Report Provided",
          description: "You receive a written service report with any findings or recommendations.",
        },
      ]}
      trustPoints={[
        {
          icon: "shield",
          title: "Qualified Engineers",
          description: "All AC servicing is carried out by fully qualified, F-Gas certified engineers.",
        },
        {
          icon: "fileText",
          title: "Written Report",
          description: "A full service report is provided after every visit for your records.",
        },
        {
          icon: "zap",
          title: "All Major Brands",
          description: "We service Mitsubishi, Daikin, LG, Samsung, Panasonic, Fujitsu, and more.",
        },
      ]}
      faqs={[
        {
          question: "How often should I service my air conditioning?",
          answer: "Air conditioning systems should be serviced annually to maintain performance, efficiency, and warranty compliance.",
        },
        {
          question: "What does an AC service include?",
          answer: "A full service includes cleaning of filters and coils, refrigerant checks, electrical testing, condensate drain clearing, and a performance test.",
        },
        {
          question: "Will servicing reduce my energy bills?",
          answer: "Yes. A clean, well-maintained system runs more efficiently and uses less electricity, which can noticeably reduce your energy costs.",
        },
        {
          question: "Which brands do you service?",
          answer: "We service all major brands including Mitsubishi Electric, Daikin, LG, Samsung, Panasonic, and Fujitsu.",
        },
      ]}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Services", href: "/services" },
        { label: "Air Conditioning", href: "/services/air-conditioning" },
        { label: "AC Servicing" },
      ]}
      serviceValue="ac-servicing"
      accentColor="red"
    />
  );
}
