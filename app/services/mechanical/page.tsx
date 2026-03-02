import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import SectorChoiceSection from "@/components/sections/SectorChoiceSection";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Mechanical Services",
  description: `Heating systems, plant room installations, pipework, and preventative maintenance across ${COMPANY.areas}. Commercial and domestic mechanical engineering.`,
};

export default function MechanicalServicesPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Mechanical Services"
        subtitle={`Heating system installation, plant room installations, pipework, and preventative maintenance across ${COMPANY.areas}.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Mechanical Services" },
        ]}
        backgroundImage="/images/core-services/mechanical.png"
        compact
      />
      <SectorChoiceSection basePath="mechanical" serviceImageKey="Mechanical Services" />
    </div>
  );
}
