import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import SectorChoiceSection from "@/components/sections/SectorChoiceSection";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Electrical Services",
  description: `Electrical installations, fault finding, compliance inspections, and maintenance contracts across ${COMPANY.areas}. Commercial and domestic.`,
};

export default function ElectricalServicesPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Electrical Services"
        subtitle={`Electrical installations, fault finding, compliance inspections, and maintenance contracts across ${COMPANY.areas}.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Electrical Services" },
        ]}
        backgroundImage="/images/core-services/electrical.png"
        compact
      />
      <SectorChoiceSection basePath="electrical" serviceImageKey="Electrical Services" />
    </div>
  );
}
