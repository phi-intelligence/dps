import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Flame, Gauge, MapPin, ShieldCheck, TimerReset } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";

export const metadata: Metadata = {
  title: "Commercial Heating Engineer London | DPS Heating Services Ltd",
  description:
    "24/7 commercial gas and heating engineers covering London and the South East. Plant rooms, breakdowns, servicing and compliance.",
  alternates: {
    canonical: "/commercial-heating-engineer-london",
  },
};

export default function CommercialHeatingEngineerLondonPage() {
  const imageBase = "/imagesv2/seo/commercial-heating-engineer-london";

  return (
    <div className="bg-[#f1ebe0] text-brand-text">
      <PageHero
        title="Commercial Heating Engineer London"
        subtitle="Reliable day-to-day commercial heating support for buildings that need consistent comfort, safe operation, and quick response when faults happen."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Commercial Heating Engineer London" },
        ]}
        backgroundImage={`${imageBase}/hero_heater.png`}
        variant="luxury"
        darkHero
        compact
      />

      <section className="py-14 md:py-18 bg-[#f6f1e7]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <aside className="rounded-[1.8rem] border border-[#dfd0b2] bg-[#0d1319] p-6 md:p-7 shadow-[0_14px_36px_rgba(0,0,0,0.2)]">
              <h2 className="text-[10px] font-technical font-extrabold uppercase tracking-[0.34em] text-[#d9c078] mb-4">
                Service Objectives
              </h2>
              <ul className="space-y-3">
                {[
                  "Stabilise heating performance in occupied commercial buildings",
                  "Reduce repeat breakdowns with root-cause diagnostics",
                  "Support planned and reactive works with clear reporting",
                  "Maintain compliance while protecting operational uptime",
                ].map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-[#d7dee8] leading-relaxed">
                    <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-[#e2c977]" />
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-5 pt-5 border-t border-white/10 space-y-2 text-sm text-[#d7dee8]">
                <p className="flex items-start gap-2">
                  <MapPin size={14} className="mt-0.5 text-[#e2c977]" />
                  Covering London, Kent, Essex and the South East
                </p>
                <p className="flex items-start gap-2">
                  <ShieldCheck size={14} className="mt-0.5 text-[#e2c977]" />
                  Gas Safe registered and commercially qualified
                </p>
              </div>
            </aside>

            <div className="rounded-[1.8rem] border border-[#dfd0b2] bg-white/90 p-6 md:p-8 shadow-[0_12px_34px_rgba(0,0,0,0.07)]">
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.34em] text-[#af8d36]">
                Core Heating Service
              </span>
              <h3 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f]">
                Commercial Heating Engineer London
              </h3>
              <p className="mt-4 text-sm md:text-base leading-relaxed text-[#2f3740]">
                We work on commercial heating systems every day across London and the South East. From offices and schools to retail units and managed residential blocks, we help clients keep heating and hot water running safely and reliably.
              </p>
              <p className="mt-4 text-sm md:text-base leading-relaxed text-[#2f3740]">
                Our engineers handle plant rooms, boilers, controls, pumps, and distribution issues, whether it is an urgent fault or planned maintenance. We focus on practical fixes, clear communication, and work that stands up in real operating conditions.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <Link
                  href="/contact"
                  className="inline-flex items-center gap-2 rounded-full bg-[#e2c977] px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.22em] text-[#11161d] hover:bg-[#ead691] transition-colors"
                >
                  Book Heating Assessment
                  <ArrowRight size={12} />
                </Link>
                <Link
                  href="/services/gas"
                  className="inline-flex items-center gap-2 rounded-full border border-[#cbb57a] bg-white px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.22em] text-[#1f252b] hover:bg-[#fff9e8] transition-colors"
                >
                  Explore Core Services
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-14 md:py-18 bg-[#111922]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-center text-lg md:text-xl font-technical font-extrabold uppercase tracking-[0.22em] text-white mb-7">
            Heating Engineering Workflow
          </h3>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                title: "1. Diagnose",
                text: "Rapidly identify root-cause failures across boilers, controls, circulation and distribution assets.",
                icon: Gauge,
              },
              {
                title: "2. Stabilise",
                text: "Apply safe, practical corrective works that restore service while minimising operational disruption.",
                icon: TimerReset,
              },
              {
                title: "3. Improve",
                text: "Implement targeted upgrades and maintenance actions to reduce repeat faults and improve efficiency.",
                icon: Flame,
              },
            ].map(({ title, text, icon: Icon }) => (
              <article
                key={title}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 md:p-6 shadow-[0_12px_30px_rgba(0,0,0,0.2)]"
              >
                <Icon size={18} className="text-[#e2c977] mb-3" />
                <h4 className="text-sm font-technical font-extrabold uppercase tracking-[0.18em] text-white mb-2">
                  {title}
                </h4>
                <p className="text-sm text-[#d1d8e2] leading-relaxed">{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="py-14 md:py-18 bg-[#f6f1e7]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="relative h-[21rem] md:h-[30rem] rounded-[1.8rem] overflow-hidden border border-[#e0d3b8] shadow-[0_16px_36px_rgba(0,0,0,0.1)]">
              <Image
                src={`${imageBase}/ventilation.png`}
                alt="Commercial heating engineer inspecting plant room"
                fill
                className="object-cover"
              />
            </div>
            <div className="grid gap-6">
              <div className="relative h-48 md:h-[14rem] rounded-[1.5rem] overflow-hidden border border-[#e0d3b8] shadow-[0_12px_30px_rgba(0,0,0,0.08)]">
                <Image
                  src={`${imageBase}/repair.webp`}
                  alt="Commercial heating system diagnostics"
                  fill
                  className="object-cover"
                />
              </div>
              <div className="relative h-48 md:h-[14rem] rounded-[1.5rem] overflow-hidden border border-[#e0d3b8] shadow-[0_12px_30px_rgba(0,0,0,0.08)]">
                <Image
                  src={`${imageBase}/flue.jpg`}
                  alt="Commercial boiler and heating maintenance works"
                  fill
                  className="object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-10 md:py-12 bg-[#f6f1e7]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <article className="rounded-[1.6rem] border border-[#dfd0b2] bg-white/95 p-6 md:p-8 shadow-[0_12px_32px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.15em] text-[#171b1f] mb-3">
              Keeping Commercial Buildings Warm And Running
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              In commercial buildings, heating problems quickly become operational problems. We are used to working in live environments where there are tenants, staff, and time pressures. Our team diagnoses faults quickly, makes systems safe, and works to restore stable heating with minimal disruption.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              We regularly deal with recurring temperature issues, control faults, circulation problems, and aging plant. Instead of short-term patchwork, we look at the wider system so repairs last and site teams are not calling out for the same issue again.
            </p>
          </article>

          <article className="rounded-[1.6rem] border border-[#dfd0b2] bg-[#efe6d6] p-6 md:p-8 shadow-[0_12px_32px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.15em] text-[#171b1f] mb-3">
              Repairs, Servicing And Better System Performance
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              Many heating faults are linked to more than one component, so we do not treat boilers, controls, and distribution in isolation. We check the full picture, then explain what needs immediate action and what should be scheduled as planned work.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              Where systems are gas-fired, we align heating work with gas safety and compliance requirements. That joined-up approach gives facilities teams one accountable contractor rather than splitting responsibility across multiple providers.
            </p>
          </article>

          <article className="rounded-[1.6rem] border border-[#dfd0b2] bg-white/95 p-6 md:p-8 shadow-[0_12px_32px_rgba(0,0,0,0.06)]">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.15em] text-[#171b1f] mb-3">
              One Team Across London And The South East
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4">
              We cover London, Kent, Essex and the South East, supporting both single sites and multi-site portfolios. Clients choose us because they get consistent standards, clear updates, and engineers who understand the realities of day-to-day building operations.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              When outages happen, we provide emergency response as well as follow-on works to prevent repeat failures. If you need a Commercial Heating Engineer London team for both reactive and planned support, DPS can provide full continuity across your estate.
            </p>
          </article>
        </div>
      </section>

      <section className="py-14 md:py-16 bg-[#111922]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[1.8rem] border border-white/10 bg-white/[0.03] p-6 md:p-8">
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
                  className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm text-[#d3dbe5] flex items-center gap-2"
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
        title="Need A Commercial Heating Engineer In London?"
        subtitle="DPS supports planned and reactive commercial heating requirements across London, Kent, Essex and the South East."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
