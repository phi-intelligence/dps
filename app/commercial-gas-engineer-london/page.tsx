import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, MapPin, ShieldCheck, Wrench, Flame, Building2 } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";

export const metadata: Metadata = {
  title: "Commercial Gas Engineer London | DPS Heating Services Ltd",
  description:
    "24/7 commercial gas and heating engineers covering London and the South East. Plant rooms, breakdowns, servicing and compliance.",
  alternates: {
    canonical: "/commercial-gas-engineer-london",
  },
};

export default function CommercialGasEngineerLondonPage() {
  const imageBase = "/imagesv2/seo/commercial-gas-engineer-london";

  return (
    <div className="bg-[#f2ede3] text-brand-text">
      <PageHero
        title="Commercial Gas Engineer London"
        subtitle="On-the-ground commercial gas support for buildings that cannot afford downtime, delivered by the DPS team across London and the South East."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Commercial Gas Engineer London" },
        ]}
        backgroundImage={`${imageBase}/hero.png`}
        variant="luxury"
        darkHero
        compact
      />

      <section className="relative bg-[#f7f3ea] py-14 md:py-18">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-7 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[2rem] border border-[#e0d3b8] bg-white/92 p-6 md:p-8 shadow-[0_14px_42px_rgba(0,0,0,0.08)]">
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#b8963a]">
                Core Service Focus
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.18em] text-[#171b1f]">
                Commercial Gas Engineer London
              </h2>
              <p className="mt-4 text-sm md:text-base leading-relaxed text-[#2f3740]">
                At DPS, this is the work we do every day: attending live sites, diagnosing gas and heating faults, carrying out repairs, and keeping systems safe and compliant. We support offices, schools, retail units, managed blocks, plant rooms, and high-end residential buildings where reliable heating and hot water are essential.
              </p>
              <p className="mt-4 text-sm md:text-base leading-relaxed text-[#2f3740]">
                Clients call us for planned servicing, annual safety checks, fault finding, emergency callouts, and plant room support. We cover London, Kent, Essex and the South East, so whether you run one site or a multi-site portfolio, you get one team, one standard, and clear updates from start to finish.
              </p>
            </div>

            <aside className="rounded-[2rem] border border-[#e0d3b8] bg-[#f3ecdf] p-6 md:p-7 shadow-[0_10px_30px_rgba(0,0,0,0.07)]">
              <h3 className="text-[10px] font-technical font-extrabold uppercase tracking-[0.32em] text-[#7b6b39] mb-4">
                Quick Snapshot
              </h3>
              <ul className="space-y-3 text-sm text-[#2f3740]">
                <li className="flex items-start gap-2">
                  <MapPin size={15} className="mt-0.5 text-[#b8963a]" />
                  Covering London, Kent, Essex and the South East
                </li>
                <li className="flex items-start gap-2">
                  <ShieldCheck size={15} className="mt-0.5 text-[#b8963a]" />
                  Gas Safe registered and commercial gas qualified
                </li>
                <li className="flex items-start gap-2">
                  <Building2 size={15} className="mt-0.5 text-[#b8963a]" />
                  Trusted by facilities management companies
                </li>
              </ul>
              <div className="mt-5 flex flex-col gap-2">
                <Link
                  href="/contact"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[#e2c977] px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.22em] text-[#0a0f14] hover:bg-[#ecd893] transition-colors"
                >
                  Request Site Visit
                </Link>
                <Link
                  href="/services/gas"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-[#c9b47a] bg-white px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.22em] text-[#1f252b] hover:bg-[#fff9e8] transition-colors"
                >
                  View Core Gas Services
                </Link>
              </div>
            </aside>
          </div>
        </div>
      </section>

      <section className="relative bg-[#0b1015] py-16 md:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 md:p-8">
            <div className="flex items-center gap-3 mb-5">
              <Wrench size={18} className="text-[#e2c977]" />
              <h3 className="text-lg md:text-xl font-technical font-extrabold uppercase tracking-[0.2em] text-white">
                What Our Commercial Gas Team Handles
              </h3>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[
                "Commercial boiler servicing and fault finding",
                "Gas safety inspections and compliance checks",
                "Plant room maintenance and performance optimisation",
                "Tightness testing, purging and gas-rate checks",
                "Reactive repairs and controlled emergency response",
                "Planned maintenance support for FM portfolios",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm text-[#d6dde7] flex items-start gap-2"
                >
                  <CheckCircle2 size={14} className="text-[#e2c977] mt-0.5 shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="relative bg-[#f7f3ea] py-16 md:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="relative h-64 md:h-80 rounded-[1.6rem] overflow-hidden border border-[#e0d3b8] shadow-[0_12px_30px_rgba(0,0,0,0.08)]">
              <Image
                src={`${imageBase}/commercial-gas-and-heating-solution-london.webp`}
                alt="Commercial gas and heating engineer in London"
                fill
                className="object-cover"
              />
            </div>
            <div className="relative h-64 md:h-80 rounded-[1.6rem] overflow-hidden border border-[#e0d3b8] shadow-[0_12px_30px_rgba(0,0,0,0.08)]">
              <Image
                src={`${imageBase}/Commercial-Boiler-Repair.webp`}
                alt="Commercial boiler repair and gas fault diagnostics"
                fill
                className="object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="relative bg-[#f7f3ea] pb-16 md:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[1.8rem] border border-[#e0d3b8] bg-white/90 p-6 md:p-8 shadow-[0_12px_34px_rgba(0,0,0,0.07)]">
            {/* <h3 className="text-lg md:text-xl font-technical font-extrabold uppercase tracking-[0.2em] text-[#171b1f] mb-4">
              Service Delivery In Action
            </h3> */}
            <div className="relative h-64 md:h-80 rounded-2xl overflow-hidden border border-[#d9ccb0] bg-[#0b1015]">
              <Image
                src={`${imageBase}/image-asset.webp`}
                alt="DPS commercial gas engineer service delivery image"
                fill
                className="object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="relative bg-[#f7f3ea] py-8 md:py-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-7">
          <article className="rounded-[1.6rem] border border-[#e0d3b8] bg-white/90 px-6 py-6 md:px-8 md:py-8 shadow-[0_10px_30px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.16em] text-[#171b1f] mb-3">
              What It Is Like Working With DPS
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              When we arrive on site, we start with safety and the immediate operational risk. We check what has failed, what can be made safe straight away, and what action is needed to restore reliable service. We work in occupied buildings every day, so we plan around access, tenants, and business hours wherever possible.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              You will always know where things stand. We explain faults in plain language, set out urgent and non-urgent items clearly, and give practical options based on your site and budget. That helps facilities managers and duty holders make good decisions quickly instead of repeatedly firefighting the same issue.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              For regional portfolios, consistency matters. We keep the same engineering standards and reporting style across London, Kent, Essex and the South East, which makes contractor management easier for FM teams and property managers.
            </p>
          </article>

          <article className="rounded-[1.6rem] border border-[#e0d3b8] bg-[#f3ecdf] px-6 py-6 md:px-8 md:py-8 shadow-[0_10px_30px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.16em] text-[#171b1f] mb-3">
              Servicing, Compliance And Fault Finding
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              Good compliance comes from doing the basics properly and doing them consistently. Our commercial gas servicing includes safety checks, condition checks, and performance testing so issues are found early, not after a shutdown.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              When faults happen, we focus on root cause, not quick patchwork. We check the wider system around the fault - controls, circulation, gas supply and plant condition - so repairs hold and repeat failures are reduced.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              We also support planned maintenance schedules for plant rooms and commercial heating systems, helping you prioritise spend and reduce unplanned outages over the year.
            </p>
          </article>

          <article className="rounded-[1.6rem] border border-[#e0d3b8] bg-white/90 px-6 py-6 md:px-8 md:py-8 shadow-[0_10px_30px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.16em] text-[#171b1f] mb-3">
              Why Businesses Choose DPS
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              We are Gas Safe registered, commercially experienced, fully insured, and trusted by facilities management companies that need responsive support and dependable results. We turn up, communicate clearly, and complete work to a standard that stands up in real operating conditions.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              If you need a Commercial Gas Engineer London team that understands day-to-day building pressures, DPS is ready to help. From reactive breakdowns to planned compliance work, we support clients across London, Kent, Essex and the South East with practical, accountable engineering.
            </p>
          </article>
        </div>
      </section>

      <section className="relative bg-[#0b1015] py-14 md:py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 md:p-8">
            <h3 className="text-lg md:text-xl font-technical font-extrabold uppercase tracking-[0.2em] text-white mb-5">
              Why Clients Trust DPS
            </h3>
            <ul className="grid gap-3 sm:grid-cols-2">
              {[
                "Gas Safe registered",
                "Commercial gas qualified",
                "Fully insured",
                "Trusted by facilities management companies",
              ].map((item) => (
                <li
                  key={item}
                  className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm text-[#d6dde7] flex items-center gap-2"
                >
                  <Flame size={14} className="text-[#e2c977] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <CTABanner
        title="Need A Commercial Gas Engineer In London?"
        subtitle="Covering London, Kent, Essex and the South East for compliance, servicing, plant room support and emergency response."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
