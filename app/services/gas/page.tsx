import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import SectorChoiceSection from "@/components/sections/SectorChoiceSection";
import { COMPANY } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Gas Services",
  description: `Gas installation, servicing, landlord safety inspections, and emergency callouts across ${COMPANY.areas}. Gas Safe registered engineers.`,
};

export default function GasServicesPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Gas Services"
        subtitle={`Gas installation and servicing, landlord safety inspections, and commercial and domestic gas works across ${COMPANY.areas}. Gas Safe registered.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Gas Services" },
        ]}
        backgroundImage="/images/core-services/gas.png"
        compact
      />
      <SectorChoiceSection basePath="gas" serviceImageKey="Gas Services" />
    </div>
  );
}
