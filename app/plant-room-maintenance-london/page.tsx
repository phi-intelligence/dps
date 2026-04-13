import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, Cog, HardHat, MapPin, ShieldCheck, Wrench } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";

export const metadata: Metadata = {
  title: "Plant Room Maintenance London | DPS Heating Services Ltd",
  description:
    "24/7 commercial gas and heating engineers covering London and the South East. Plant rooms, breakdowns, servicing and compliance.",
  alternates: {
    canonical: "/plant-room-maintenance-london",
  },
};

export default function PlantRoomMaintenanceLondonPage() {
  const imageBase = "/imagesv2/seo/plant-room-maintenance-london";

  return (
    <div className="bg-[#f2ede3] text-brand-text">
      <PageHero
        title="Plant Room Maintenance London"
        subtitle="Practical plant room maintenance carried out by engineers who work on live commercial systems every day."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Plant Room Maintenance London" },
        ]}
        backgroundImage={`${imageBase}/hero_boiler.png`}
        variant="luxury"
        darkHero
        compact
      />

      <section className="py-12 md:py-16 bg-[#f7f3ea]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[2rem] border border-[#e0d3b8] bg-white/90 p-6 md:p-8 shadow-[0_12px_34px_rgba(0,0,0,0.08)]">
            <h2 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.16em] text-[#171b1f]">
              Plant Room Maintenance London - Service Coverage Map
            </h2>
            <p className="mt-4 text-sm md:text-base leading-relaxed text-[#2f3740]">
              Plant rooms are at the heart of most commercial heating systems, and small issues there can quickly become major building problems. At DPS, we carry out routine plant room maintenance, fault finding, and remedial works that keep systems safe, stable, and ready for day-to-day demand.
            </p>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {[
                {
                  title: "Mechanical Assets",
                  text: "Pumps, valves, pipework, heat exchangers and circulation elements.",
                  icon: Wrench,
                },
                {
                  title: "Control And Safety",
                  text: "Interlocks, fail-safes, controls logic and compliance-critical checks.",
                  icon: ShieldCheck,
                },
                {
                  title: "Gas And Boiler Integration",
                  text: "Gas-fired plant stability within wider heating and plant room systems.",
                  icon: HardHat,
                },
              ].map(({ title, text, icon: Icon }) => (
                <div key={title} className="rounded-xl border border-[#e2d7bf] bg-[#f9f6ef] p-4">
                  <Icon size={16} className="text-[#b8963a] mb-2" />
                  <h3 className="text-xs font-technical font-extrabold uppercase tracking-[0.18em] text-[#1a1f24] mb-1">
                    {title}
                  </h3>
                  <p className="text-sm text-[#37414c] leading-relaxed">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 md:py-16 bg-[#0c1218]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="space-y-6">
            {[
              {
                heading: "Routine Maintenance That Prevents Escalation",
                text: "Most major breakdowns start as small warning signs. We pick these up early through regular checks and planned servicing, helping clients avoid avoidable downtime and emergency spend.",
              },
              {
                heading: "Planned Works Sequenced Around Operations",
                text: "We plan works around site access, occupancy, and business hours so maintenance can be done properly without unnecessary disruption to staff, tenants, or residents.",
              },
              {
                heading: "Emergency Stabilisation When Failures Occur",
                text: "If a failure happens, we focus on making the system safe first, restoring service where possible, and giving clear next steps for full repair and long-term reliability.",
              },
            ].map((item, idx) => (
              <article
                key={item.heading}
                className={`rounded-2xl border p-5 md:p-6 ${
                  idx === 1
                    ? "border-[#e2c977] bg-[#141c25]"
                    : "border-white/10 bg-white/[0.04]"
                }`}
              >
                <h3 className="text-sm md:text-base font-technical font-extrabold uppercase tracking-[0.16em] text-white mb-2">
                  {item.heading}
                </h3>
                <p className="text-sm text-[#d2dae4] leading-relaxed">{item.text}</p>
              </article>
            ))}
          </div>

          <aside className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 h-fit">
            <h3 className="text-[10px] font-technical font-extrabold uppercase tracking-[0.3em] text-[#d8bf75] mb-4">
              Regional Delivery
            </h3>
            <ul className="space-y-3 text-sm text-[#d2dae4]">
              <li className="flex items-start gap-2">
                <MapPin size={14} className="mt-0.5 text-[#e2c977]" />
                Covering London, Kent, Essex and the South East
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={14} className="mt-0.5 text-[#e2c977]" />
                FM-friendly reporting and decision-ready priorities
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={14} className="mt-0.5 text-[#e2c977]" />
                Linked support for Commercial Gas Engineer London scope
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 size={14} className="mt-0.5 text-[#e2c977]" />
                Continuity for Gas Engineer Kent / South East portfolios
              </li>
            </ul>
            <Link
              href="/contact"
              className="mt-5 inline-flex w-full items-center justify-center rounded-full bg-[#e2c977] px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] text-[#111820] hover:bg-[#ecd895] transition-colors"
            >
              Request Plant Room Review
            </Link>
          </aside>
        </div>
      </section>

      <section className="py-12 md:py-16 bg-[#f7f3ea]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="relative h-72 md:h-[26rem] rounded-[1.8rem] overflow-hidden border border-[#e0d3b8]">
              <Image src={`${imageBase}/Plant-Room-Redesigns-PW-Heating-and-Plumbing.jpg`} alt="Plant room maintenance image A" fill className="object-cover" />
            </div>
            <div className="grid gap-6">
              <div className="relative h-40 md:h-[12.3rem] rounded-[1.3rem] overflow-hidden border border-[#e0d3b8]">
                <Image src={`${imageBase}/Commercial-boiler-plant-room-1.jpg`} alt="Plant room maintenance image B" fill className="object-cover" />
              </div>
              <div className="relative h-40 md:h-[12.3rem] rounded-[1.3rem] overflow-hidden border border-[#e0d3b8]">
                <Image src={`${imageBase}/IMG_7463-2.webp`} alt="Plant room maintenance image C" fill className="object-cover" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-8 md:py-10 bg-[#f7f3ea]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <article className="rounded-2xl border border-[#e0d3b8] bg-white/92 p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Day-To-Day Plant Room Work We Actually Deliver
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-3">
              Our engineers regularly service boilers, pumps, valves, controls, pipework, and safety components in live plant rooms. We carry out routine checks, identify wear before it becomes a failure, and fix issues that impact heating performance or compliance.
            </p>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              You get clear reporting after every visit: what was done, what needs attention now, and what should be planned next. This gives facilities teams and property managers a practical maintenance plan rather than a list of vague recommendations.
            </p>
          </article>
          <article className="rounded-2xl border border-[#e0d3b8] bg-[#f1e8d8] p-6 md:p-8">
            <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.14em] text-[#171b1f] mb-3">
              Why Clients Choose DPS
            </h3>
            <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
              We combine practical site experience with strong communication and dependable follow-through. Whether you need regular plant room maintenance, linked commercial gas support, or multi-site coverage across London, Kent, Essex and the South East, DPS provides one accountable engineering team.
            </p>
          </article>
        </div>
      </section>

      <section className="py-12 md:py-14 bg-[#0c1218]">
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
                  <Cog size={14} className="text-[#e2c977] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <CTABanner
        title="Need Plant Room Maintenance In London?"
        subtitle="DPS provides planned and reactive plant room engineering support across London, Kent, Essex and the South East."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
