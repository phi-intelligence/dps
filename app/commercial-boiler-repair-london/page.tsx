import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, Flame, Gauge, MapPin, ShieldCheck, Thermometer } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";

export const metadata: Metadata = {
  title: "Commercial Boiler Repair London | DPS Heating Services Ltd",
  description:
    "24/7 commercial gas and heating engineers covering London and the South East. Plant rooms, breakdowns, servicing and compliance.",
  alternates: {
    canonical: "/commercial-boiler-repair-london",
  },
};

export default function CommercialBoilerRepairLondonPage() {
  const imageBase = "/imagesv2/seo/commercial-boiler-repair-london";

  return (
    <div className="bg-[#efe9de] text-brand-text">
      <PageHero
        title="Commercial Boiler Repair London"
        subtitle="Fast, practical boiler repair support for commercial buildings where heating and hot water cannot be left down."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Commercial Boiler Repair London" },
        ]}
        backgroundImage={`${imageBase}/hero.png`}
        variant="luxury"
        darkHero
        compact
      />

      <section className="py-14 md:py-18 bg-[#f6f1e7]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="rounded-[1.9rem] border border-[#e0d3b8] bg-white/90 p-6 md:p-8">
              <h2 className="text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.15em] text-[#171b1f]">
                Boiler Breakdown Response Path
              </h2>
              <p className="mt-4 text-sm md:text-base text-[#2f3740] leading-relaxed">
              When a boiler goes down, the priority is always safety first, then getting your system back up and running as quickly as possible. Our engineers attend commercial sites across London every day to diagnose faults, carry out repairs, and restore dependable heating and hot water.
              </p>
              <div className="mt-6 space-y-4">
                {[
                  { title: "Initial Triage", text: "Stabilise risk and identify immediate service impact.", icon: AlertTriangle },
                  { title: "Root-Cause Diagnostics", text: "Check the boiler, controls, gas supply and linked heating system.", icon: Gauge },
                  { title: "Repair And Validation", text: "Complete repairs properly and confirm stable performance before handover.", icon: CheckCircle2 },
                  { title: "Aftercare Plan", text: "Flag risks and recommend next steps to reduce repeat breakdowns.", icon: Thermometer },
                ].map(({ title, text, icon: Icon }) => (
                  <div key={title} className="flex items-start gap-3 rounded-xl border border-[#e5dbc6] bg-[#fbf8f1] px-4 py-3">
                    <Icon size={16} className="mt-0.5 text-[#b8963a] shrink-0" />
                    <div>
                      <h3 className="text-xs font-technical font-extrabold uppercase tracking-[0.18em] text-[#1d242b]">{title}</h3>
                      <p className="text-sm text-[#36414b]">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <aside className="rounded-[1.9rem] border border-[#dac9a6] bg-[#111a23] p-6 md:p-8 text-[#d2dbe5]">
              <h3 className="text-[10px] font-technical font-extrabold uppercase tracking-[0.32em] text-[#e2c977] mb-4">
                Service Commitments
              </h3>
              <ul className="space-y-3 text-sm">
                <li className="flex gap-2">
                  <ShieldCheck size={14} className="mt-0.5 text-[#e2c977]" />
                  Safety-first, compliance-led boiler repair on every callout
                </li>
                <li className="flex gap-2">
                  <Flame size={14} className="mt-0.5 text-[#e2c977]" />
                  Clear fault reporting with practical repair options
                </li>
                <li className="flex gap-2">
                  <MapPin size={14} className="mt-0.5 text-[#e2c977]" />
                  London, Kent, Essex and South East coverage
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 size={14} className="mt-0.5 text-[#e2c977]" />
                  Follow-on recommendations to reduce repeat breakdowns
                </li>
                <li className="flex gap-2">
                  <CheckCircle2 size={14} className="mt-0.5 text-[#e2c977]" />
                  Linked support for wider commercial gas and heating systems
                </li>
              </ul>
              <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-4">
                <p className="text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] text-[#e2c977] mb-2">
                  Typical Support
                </p>
                <p className="text-sm text-[#d2dbe5] leading-relaxed">
                  Emergency breakdown attendance, fault diagnostics, parts replacement, performance checks, and planned remedial works for commercial boilers and linked plant room equipment.
                </p>
              </div>
              <Link
                href="/contact"
                className="mt-6 inline-flex w-full items-center justify-center rounded-full bg-[#e2c977] px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] text-[#0f141b] hover:bg-[#ecd894] transition-colors"
              >
                Request Boiler Support
              </Link>
            </aside>
          </div>
        </div>
      </section>

      <section className="py-14 md:py-18 bg-[#0f1821]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="relative h-64 rounded-2xl overflow-hidden border border-white/10">
              <Image src={`${imageBase}/boiler-room.jpg`} alt="Commercial boiler repair image A" fill className="object-cover" />
            </div>
            <div className="relative h-64 rounded-2xl overflow-hidden border border-white/10">
              <Image src={`${imageBase}/commercial-gas-and-heating-solution-london.webp`} alt="Commercial boiler repair image B" fill className="object-cover" />
            </div>
            <div className="relative h-64 rounded-2xl overflow-hidden border border-white/10">
              <Image src={`${imageBase}/boiler-room-rolling-platform-RollaStep-MP-1024x768.webp`} alt="Commercial boiler repair image C" fill className="object-cover" />
            </div>
          </div>
        </div>
      </section>

      <section className="py-10 md:py-12 bg-[#f6f1e7]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-[#e0d3b8] bg-white/92 p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Boiler Repairs That Last
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-3">
              In many cases, the failed part is only one part of the problem. We check the wider system around the boiler, including controls, circulation, and plant room conditions, so repairs are not just temporary fixes.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              You receive clear updates on what caused the issue, what has been repaired, and what should be scheduled next. That gives facilities teams and property managers confidence in both compliance and reliability.
            </p>
          </article>
          <article className="rounded-2xl border border-[#e0d3b8] bg-[#f1e8d8] p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Support Across London And The South East
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-3">
              We cover London, Kent, Essex and the South East, supporting both one-off emergency jobs and ongoing planned maintenance. If faults extend beyond a single boiler, we can also support wider heating, gas, and plant room requirements without passing you between contractors.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              For multi-site clients, this means one accountable team, consistent standards, and straightforward communication across every property.
            </p>
          </article>
        </div>
      </section>

      <section className="py-12 md:py-14 bg-[#0f1821]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 md:p-8">
            <h3 className="text-lg font-technical font-extrabold uppercase tracking-[0.2em] text-white mb-4">
              Why Clients Trust DPS
            </h3>
            <ul className="grid gap-3 sm:grid-cols-2">
              {[
                "Gas Safe registered",
                "Commercial gas qualified",
                "Fully insured",
                "Trusted by facilities management companies",
              ].map((item) => (
                <li key={item} className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm text-[#d1d9e2] flex items-center gap-2">
                  <CheckCircle2 size={14} className="text-[#e2c977] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <CTABanner
        title="Need Commercial Boiler Repair In London?"
        subtitle="DPS provides diagnostic-led boiler repair support across London, Kent, Essex and the South East."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
