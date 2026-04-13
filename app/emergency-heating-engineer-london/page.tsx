import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { AlertOctagon, ArrowRight, CheckCircle2, Clock3, Flame, PhoneCall, ShieldCheck } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";

export const metadata: Metadata = {
  title: "Emergency Heating Engineer London | DPS Heating Services Ltd",
  description:
    "24/7 commercial gas and heating engineers covering London and the South East. Plant rooms, breakdowns, servicing and compliance.",
  alternates: {
    canonical: "/emergency-heating-engineer-london",
  },
};

export default function EmergencyHeatingEngineerLondonPage() {
  const imageBase = "/imagesv2/seo/emergency-heating-engineer-london";

  return (
    <div className="bg-[#f0eadf] text-brand-text">
      <PageHero
        title="Emergency Heating Engineer London"
        subtitle="24/7 emergency heating support from engineers who respond to live breakdowns every day across London and the South East."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Emergency Heating Engineer London" },
        ]}
        backgroundImage={`${imageBase}/hero.png`}
        variant="luxury"
        darkHero
        compact
      />

      <section className="py-12 md:py-14 bg-[#141d27]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-4 md:grid-cols-4">
            {[
              { label: "Rapid triage", icon: AlertOctagon },
              { label: "Safe stabilisation", icon: ShieldCheck },
              { label: "24/7 callout", icon: Clock3 },
              { label: "Clear escalation", icon: PhoneCall },
            ].map(({ label, icon: Icon }) => (
              <div key={label} className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-4 text-center">
                <Icon size={17} className="text-[#e2c977] mx-auto mb-2" />
                <p className="text-xs font-technical font-extrabold uppercase tracking-[0.16em] text-[#d3dbe5]">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-14 md:py-18 bg-[#f7f3ea]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="relative h-80 md:h-[34rem] rounded-[1.8rem] overflow-hidden border border-[#e0d3b8]">
              <Image src={`${imageBase}/Install-gas-pipes-3.jpg`} alt="Emergency heating engineer response image" fill className="object-cover" />
            </div>
            <div className="space-y-4">
              {[
                {
                  heading: "Emergency Heating Engineer London For Live Environments",
                  body: "When a heating system fails, we know the pressure on site is immediate. Our team attends live commercial and high-end residential buildings where loss of heating or hot water can affect safety, operations, and occupants.",
                },
                {
                  heading: "Incident To Resolution Workflow",
                  body: "We start with rapid triage and on-site risk checks, then stabilise the system where possible. From there, we diagnose properly and carry out corrective works with clear updates so facilities and property teams always know what is happening.",
                },
                {
                  heading: "Joined-Up Capability Across Systems",
                  body: "Most emergency faults are not isolated to one component. We can support the wider system, including gas, controls, boiler faults, and plant room issues, so you are not passed between multiple contractors during a critical incident.",
                },
              ].map((card, idx) => (
                <article key={card.heading} className={`rounded-2xl border p-5 md:p-6 ${idx === 1 ? "border-[#d5bc72] bg-[#f2e8d3]" : "border-[#e0d3b8] bg-white/90"}`}>
                  <h2 className="text-sm md:text-base font-technical font-extrabold uppercase tracking-[0.15em] text-[#171b1f] mb-2">
                    {card.heading}
                  </h2>
                  <p className="text-sm md:text-base text-[#2f3740] leading-relaxed">{card.body}</p>
                </article>
              ))}
              <div className="flex flex-wrap gap-2 pt-1">
                <Link
                  href="/contact"
                  className="inline-flex items-center gap-2 rounded-full bg-[#e2c977] px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] text-[#121821] hover:bg-[#ecd895] transition-colors"
                >
                  Request Emergency Support
                  <ArrowRight size={12} />
                </Link>
                <Link
                  href="/services/gas"
                  className="inline-flex items-center rounded-full border border-[#ccb57a] bg-white px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] text-[#1c232b] hover:bg-[#fff9e8] transition-colors"
                >
                  View Core Gas Services
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 md:py-16 bg-[#0f1821]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid gap-6 md:grid-cols-2">
          <div className="relative h-64 md:h-80 rounded-2xl overflow-hidden border border-white/10">
            <Image src={`${imageBase}/pipe-room-2-1024x768.webp`} alt="Emergency heating diagnostics image" fill className="object-cover" />
          </div>
          <div className="relative h-64 md:h-80 rounded-2xl overflow-hidden border border-white/10">
            <Image src={`${imageBase}/Expert-Gas-Pipework-Testing-Purging.jpg`} alt="Emergency heating restoration works image" fill className="object-cover" />
          </div>
        </div>
      </section>

      <section className="py-10 md:py-12 bg-[#f7f3ea]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <article className="rounded-2xl border border-[#e0d3b8] bg-white/92 p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Emergency Response Across London, Kent, Essex And The South East
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-3">
              DPS provides emergency response across London, Kent, Essex and the South East for both single sites and multi-site portfolios. We keep communication clear during callouts, work safely under pressure, and focus on restoring reliable service as quickly as possible.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              After immediate response, we provide clear follow-on recommendations so the same fault is less likely to happen again. For facilities teams, this means better continuity, fewer handover delays, and a more reliable long-term maintenance plan.
            </p>
          </article>

          <article className="rounded-2xl border border-[#e0d3b8] bg-[#f1e8d7] p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Why Clients Trust DPS
            </h3>
            <ul className="grid gap-3 sm:grid-cols-2">
              {[
                "Gas Safe registered",
                "Commercial gas qualified",
                "Fully insured",
                "Trusted by facilities management companies",
              ].map((item) => (
                <li key={item} className="rounded-xl border border-[#decfaf] bg-white/70 px-4 py-3 text-sm text-[#2d3742] flex items-center gap-2">
                  <Flame size={14} className="text-[#b8963a] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <CTABanner
        title="Need An Emergency Heating Engineer In London?"
        subtitle="DPS provides 24/7 emergency heating and gas-critical response across London, Kent, Essex and the South East."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
