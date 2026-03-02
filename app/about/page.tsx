"use client";

import Image from "next/image";
import Link from "next/link";
import {
  Shield,
  Clock,
  Target,
  MessageSquare,
  CheckCircle,
  Settings2,
  ArrowRight,
} from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import {
  COMPANY,
  KEY_STRENGTHS,
  COMMITMENT_COPY,
  SECTORS_SERVED,
} from "@/lib/constants";

const STATS = [
  { value: "10+", label: "Years experience" },
  { value: "500+", label: "Jobs completed" },
  { value: "4", label: "Areas covered" },
  { value: "5.0", label: "Client rating" },
];

const WHY_CHOOSE_ITEMS = [
  { icon: Clock, title: "24/7 capability", strength: KEY_STRENGTHS[0] },
  { icon: Shield, title: "Health & Safety", strength: KEY_STRENGTHS[1] },
  { icon: Target, title: "Client-focused", strength: KEY_STRENGTHS[2] },
  { icon: Settings2, title: "Bespoke solutions", strength: KEY_STRENGTHS[3] },
  { icon: MessageSquare, title: "Clear communication", strength: KEY_STRENGTHS[4] },
  { icon: CheckCircle, title: "Quality & compliance", strength: KEY_STRENGTHS[5] },
];

export default function AboutPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="About Us"
        subtitle={`${COMPANY.name} — mechanical, electrical and gas services across ${COMPANY.areas}. Professional engineering you can rely on.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "About Us" }]}
        backgroundImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
        showCTA
        ctaText="Talk to Us"
        ctaHref="/contact"
        compact
      />

      {/* Intro + image collage */}
      <section className="py-16 md:py-24 bg-brand-surface" aria-label="About DPS">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Our story
            </span>
            <h2 className="text-2xl md:text-3xl font-technical font-extrabold text-brand-text tracking-wider uppercase mb-6">
              Engineering you can trust
            </h2>
            <p className="text-brand-muted text-sm md:text-base font-light leading-relaxed mb-6">
              {COMPANY.vision}
            </p>
            <p className="text-brand-muted text-sm font-light leading-relaxed">
              Founded in {COMPANY.founded} by {COMPANY.founder}, {COMPANY.name} delivers expert
              mechanical, electrical, and gas services across domestic and commercial sectors.
              With {COMPANY.industryExperience} of industry experience, we are committed to
              exceptional workmanship, strict Health & Safety standards, and a responsive 24/7
              service built on discipline, integrity, and reliability.
            </p>
          </div>

          {/* Engineering in action — plant room, boiler diagnostic, gas meter */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 mt-12 md:mt-16">
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border">
              <Image
                src="/images/about/plant-room-inspection.png"
                alt="Engineer performing inspection on industrial boiler and plant room equipment"
                fill
                className="object-cover"
                sizes="(max-width: 640px) 100vw, 33vw"
                loading="lazy"
              />
            </div>
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border">
              <Image
                src="/images/about/boiler-diagnostic.png"
                alt="Technician taking diagnostic readings on boiler with combustion analyzer"
                fill
                className="object-cover"
                sizes="(max-width: 640px) 100vw, 33vw"
                loading="lazy"
              />
            </div>
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border">
              <Image
                src="/images/about/gas-meter-inspection.png"
                alt="Gas Safe engineer inspecting outdoor gas meter"
                fill
                className="object-cover"
                sizes="(max-width: 640px) 100vw, 33vw"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section className="py-12 md:py-16 bg-brand-steel border-y border-brand-card-border" aria-label="Key stats">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl md:text-4xl font-technical font-extrabold text-brand-red tracking-tight">
                  {stat.value}
                </p>
                <p className="text-[10px] font-technical font-bold uppercase tracking-widest text-brand-muted mt-1">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Our philosophy */}
      <section className="py-16 md:py-24 bg-brand-surface" aria-label="Our philosophy">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
            What we stand for
          </span>
          <h2 className="text-2xl md:text-4xl font-technical font-extrabold text-brand-text tracking-wider uppercase mb-8">
            Transparency, integrity, professionalism
          </h2>
          <p className="text-brand-muted text-sm md:text-base font-light leading-relaxed">
            {COMMITMENT_COPY}
          </p>
          <p className="text-brand-muted text-sm font-light leading-relaxed mt-6">
            {COMPANY.mission}
          </p>
        </div>
      </section>

      {/* Meet the founder */}
      <section className="py-16 md:py-24 bg-brand-steel" aria-label="Meet the founder">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="relative aspect-square min-h-[280px] md:min-h-[360px] rounded-2xl overflow-hidden border border-brand-card-border">
              <Image
                src="/images/about/founder-800.jpg"
                alt={`${COMPANY.founder}, Founder of ${COMPANY.name}`}
                fill
                className="object-cover object-right object-top"
                sizes="(max-width: 768px) 100vw, min(50vw, 480px)"
                loading="lazy"
              />
            </div>
            <div>
              <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
                Meet the founder
              </span>
              <h2 className="text-3xl md:text-4xl font-technical font-extrabold text-brand-text tracking-tight mb-6">
                {COMPANY.founder}
              </h2>
              <p className="text-brand-muted text-sm md:text-base font-light leading-relaxed mb-4">
                <span className="text-brand-text font-medium">Founder of {COMPANY.name}</span>
                {" — "}
                After a successful career in the corporate sector, {COMPANY.founder} established {COMPANY.name} with a clear
                ambition: to deliver a truly bespoke mechanical, electrical, and gas service built on{" "}
                <strong className="text-brand-text">discipline</strong>,{" "}
                <strong className="text-brand-text">integrity</strong>, and{" "}
                <strong className="text-brand-text">reliability</strong>.
              </p>
              <p className="text-brand-muted text-sm font-light leading-relaxed">
                Today the company serves domestic and commercial clients across {COMPANY.areas},
                with {COMPANY.industryExperience} of industry experience and a commitment to
                exceptional workmanship and 24/7 availability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why choose us */}
      <section className="py-16 md:py-24 bg-brand-surface" aria-label="Why choose us">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 md:mb-16">
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Why choose us?
            </span>
            <h2 className="text-3xl md:text-4xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              What we deliver
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {WHY_CHOOSE_ITEMS.map((item, i) => (
              <div
                key={item.title}
                className="p-6 md:p-8 rounded-2xl border border-brand-card-border bg-brand-steel/50 hover:border-brand-red/20 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <span className="text-brand-red font-technical font-black text-2xl tabular-nums">
                    {String(i + 1).padStart(2, "0")}.
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <item.icon size={18} className="text-brand-red shrink-0" />
                      <h3 className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-widest">
                        {item.title}
                      </h3>
                    </div>
                    <p className="text-brand-muted text-sm font-light leading-relaxed">
                      {item.strength}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Accreditations — same visual as homepage (Gas Safe, Next Level FC, SafeContractor) */}
      <section className="py-16 md:py-20 bg-brand-navy border-y border-brand-card-border" aria-label="Accreditations and sponsorship">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Certified · Compliant
            </span>
            <h2 className="text-3xl md:text-4xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Accreditations & qualifications
            </h2>
          </div>
          <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-12 lg:gap-16">
            {/* Left: Gas Safe Register */}
            <div className="relative w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 order-2 md:order-1">
              <Image
                src="/images/gas-safe-register.png"
                alt="Gas Safe Register"
                fill
                className="object-contain"
                sizes="160px"
              />
            </div>

            {/* Center: Proud sponsor of Next Level FC */}
            <div className="text-center order-1 md:order-2">
              <p className="text-brand-text text-sm font-technical font-bold uppercase tracking-[0.4em] mb-8">
                Proud sponsor of
              </p>
              <div className="flex flex-col items-center gap-6">
                <div className="relative w-36 h-36 sm:w-44 sm:h-44 flex-shrink-0">
                  <Image
                    src="/images/next-level-fc.png"
                    alt="Next Level FC"
                    fill
                    className="object-contain"
                    sizes="176px"
                  />
                </div>
                <div>
                  <h3 className="text-xl md:text-2xl font-technical font-extrabold text-brand-text uppercase tracking-wider">
                    Next Level FC
                  </h3>
                  <p className="text-brand-muted text-sm font-technical uppercase tracking-wider mt-1">
                    Engineering the future on and off the pitch
                  </p>
                </div>
              </div>
            </div>

            {/* Right: SafeContractor */}
            <div className="relative w-32 h-32 sm:w-40 sm:h-40 flex-shrink-0 order-3">
              <Image
                src="/images/safe-contractor.png"
                alt="SafeContractor Approved"
                fill
                className="object-contain"
                sizes="160px"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Sectors served (compact) */}
      <section className="py-12 bg-brand-surface" aria-label="Sectors served">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-brand-muted text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4">
            Who we work with
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {SECTORS_SERVED.map((sector) => (
              <span
                key={sector}
                className="px-4 py-2 bg-brand-red/10 text-brand-text text-xs font-technical font-bold uppercase tracking-wider rounded-full"
              >
                {sector}
              </span>
            ))}
          </div>
        </div>
      </section>

      <CTABanner
        title="Get in touch"
        subtitle="Ready to book a service or get a free quote? Call us today or use our online form."
      />
    </div>
  );
}
