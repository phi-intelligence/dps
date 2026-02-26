import type { Metadata } from "next";
import ServiceDetailLayout from "@/components/sections/ServiceDetailLayout";
import { getServiceBySlug } from "@/lib/content";
import { COMPANY } from "@/lib/constants";

const SLUG = "heating/boiler-installation";

const fallbackMetadata = {
  title: "Boiler Installation",
  description: `New boiler installation in ${COMPANY.areas}. Gas Safe registered engineers, all major brands, full commissioning and warranty registration.`,
};

const fallbackProps = {
  title: "Boiler Installation",
  subtitle: "Professional new boiler installation by Gas Safe registered engineers. Supply, fit, and commission.",
  backgroundImage: "/images/140d49a2-daf4-4c0f-b0c4-881f971b97c0.jpg",
  sideImage: "/images/140d49a2-daf4-4c0f-b0c4-881f971b97c0.jpg",
  sideImageAlt: "New boiler neatly installed in kitchen cupboard with copper pipework",
  introduction: `A new boiler is a significant investment, and it pays to have it installed correctly. DPS Heating Services LTD provides full boiler installation across ${COMPANY.areas}, including a free survey, system design, supply and installation of the new boiler, commissioning, and warranty registration. We are Gas Safe registered and work with all leading brands.`,
  included: [
    "Free survey and quote",
    "Boiler and system design advice",
    "Full installation to current regulations",
    "Commissioning and testing",
    "Manufacturer warranty registration",
    "Removal and disposal of old boiler",
    "Building regulations certificate",
  ],
  issues: [
    { icon: "flame" as const, title: "Boiler Over 10 Years Old", description: "Older boilers are less efficient and more likely to develop faults. A new A-rated boiler can significantly reduce heating bills." },
    { icon: "checkCircle" as const, title: "Frequent Breakdowns", description: "If your boiler is breaking down regularly, replacement is often more cost-effective than continued repairs." },
    { icon: "gauge" as const, title: "Rising Energy Bills", description: "An inefficient boiler uses more gas to produce the same amount of heat, costing you more each month." },
    { icon: "wrench" as const, title: "Moving to a New Property", description: "A new property may benefit from a new boiler installation to match the size and requirements of the home." },
  ],
  steps: [
    { icon: "phone" as const, number: "01", title: "Free Survey", description: "We visit your property to assess your heating needs and recommend the right boiler." },
    { icon: "clipboardList" as const, number: "02", title: "Written Quote", description: "You receive a clear, fixed quote with no hidden charges before any work begins." },
    { icon: "wrench" as const, number: "03", title: "Installation Day", description: "Our engineers install the new boiler neatly and efficiently, protecting your home throughout." },
    { icon: "shield" as const, number: "04", title: "Commission & Register", description: "The boiler is commissioned, tested, and registered for warranty. You receive all documentation." },
  ],
  trustPoints: [
    { icon: "shield" as const, title: "Fully Compliant", description: "All installations meet current Gas Safe and building regulation requirements." },
    { icon: "star" as const, title: "Leading Brands", description: "We install Worcester Bosch, Vaillant, Baxi, Ideal, and Viessmann boilers." },
    { icon: "clock" as const, title: "Typically One Day", description: "Most boiler replacements are completed within a single working day." },
  ],
  faqs: [
    { question: "How long does a boiler installation take?", answer: "Most boiler replacements are completed in one day. More complex installations, such as system changes, may take longer." },
    { question: "Which boilers do you install?", answer: "We install all major brands including Worcester Bosch, Vaillant, Baxi, Ideal, and Viessmann. We can advise on the best option for your home." },
    { question: "Will my home be left clean and tidy?", answer: "Absolutely. We use protective coverings throughout and leave your home as we found it." },
    { question: "What warranty comes with a new boiler?", answer: "Most new boilers come with a 5–12 year manufacturer warranty when installed by a registered engineer. We handle all registration on your behalf." },
  ],
  breadcrumbs: [
    { label: "Home", href: "/" },
    { label: "Services", href: "/services" },
    { label: "Heating", href: "/services/heating" },
    { label: "Boiler Installation" },
  ],
  serviceValue: "boiler-installation",
  showGasSafeNote: true,
  accentColor: "red" as const,
};

export async function generateMetadata(): Promise<Metadata> {
  const service = await getServiceBySlug(SLUG);
  if (service) {
    return {
      title: service.metaTitle ?? service.title,
      description: service.metaDescription ?? fallbackMetadata.description,
    };
  }
  return fallbackMetadata;
}

export default async function BoilerInstallationPage() {
  const cms = await getServiceBySlug(SLUG);
  const props = cms ?? fallbackProps;
  return <ServiceDetailLayout {...props} />;
}
