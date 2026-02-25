import type { Metadata } from "next";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ServiceWizard from "@/components/ui/ServiceWizard";
import QuoteCalculator from "@/components/ui/QuoteCalculator";

export const metadata: Metadata = {
  title: "Service Finder",
  description:
    "Find the right heating or plumbing service and get an instant quote estimate. DPS Heating Services — London.",
};

export default function ToolsPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Service Finder"
        subtitle="Choose your service and get an instant quote estimate, or browse our heating and plumbing options."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Service Finder" },
        ]}
        compact
      />

      <section className="py-24 bg-brand-steel" aria-label="Service selector">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl md:text-4xl font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
            Service Selector
          </h2>
          <p className="text-brand-muted text-sm font-technical uppercase tracking-wider mb-10">
            Pick a category and service to go straight to the right page.
          </p>
          <ServiceWizard />
        </div>
      </section>

      <section className="py-24 bg-brand-surface" aria-label="Quote calculator">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl md:text-4xl font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
            Instant Quote Calculator
          </h2>
          <p className="text-brand-muted text-sm font-technical uppercase tracking-wider mb-10">
            Get an indicative price range based on service, property type, and urgency.
          </p>
          <QuoteCalculator />
        </div>
      </section>

      <CTABanner />
    </div>
  );
}
