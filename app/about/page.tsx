"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
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
import { motion, useInView } from "framer-motion";

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

function AnimatedStatValue({ value }: { value: string }) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const numericPart = parseFloat(value);
  const suffix = value.replace(String(numericPart), "");
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!isInView) return;

    let frameId: number;
    const duration = 1200;
    const start = performance.now();

    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      // easeOutQuad
      const eased = t * (2 - t);
      const current = numericPart * eased;
      setDisplay(
        Number.isInteger(numericPart)
          ? Math.round(current)
          : parseFloat(current.toFixed(1))
      );
      if (t < 1) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [isInView, numericPart]);

  return (
    <motion.span ref={ref}>
      {display}
      {suffix}
    </motion.span>
  );
}

export default function AboutPage() {
  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-x-hidden">
      <PageHero
        title="About Us"
        subtitle={`${COMPANY.name} — mechanical, electrical and gas services across ${COMPANY.areas}. Professional engineering you can rely on.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "About Us" }]}
        backgroundImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
        variant="luxury"
        showCTA
        ctaText="Talk to Us"
        ctaHref="/contact"
        compact
      />

      {/* Intro + image collage – light geometric band */}
      <section
        className="relative bg-[#f7f3ea] py-20 md:py-24 overflow-hidden"
        aria-label="About DPS"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 -top-16 h-48 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/30 bg-[#e2c977]/10" />
          <div className="absolute -left-40 bottom-0 h-52 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/24 bg-[#d4af37]/8" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/25 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_1.4fr] items-center">
            <div className="space-y-5">
              <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.4em] text-[#b8963a]">
                Our Story
              </span>
              <h2 className="text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.26em] text-[#171b1f]">
                Engineering You Can Trust
              </h2>
              <p className="text-sm md:text-base text-[#3c444b] leading-relaxed">
                {COMPANY.vision}
              </p>
              <p className="text-sm text-[#3c444b] leading-relaxed">
                Founded in {COMPANY.founded} by {COMPANY.founder},{" "}
                {COMPANY.name} delivers expert mechanical, electrical, and gas
                services across domestic and commercial sectors. With{" "}
                {COMPANY.industryExperience} of experience, every project is
                treated as engineered infrastructure, not just a job.
              </p>
            </div>

            {/* Engineering in action — geometric image composition */}
            <div className="relative">
              <div className="relative mx-auto max-w-xl rounded-[2.2rem] border border-[#e0d3b8] bg-white/90 shadow-[0_24px_70px_rgba(0,0,0,0.16)] px-4 py-4 sm:px-6 sm:py-6">
                <div className="grid gap-3 sm:gap-4 grid-cols-2">
                  <div className="relative col-span-2 aspect-[5/3] overflow-hidden rounded-[1.8rem]">
                    <Image
                      src="/images/about/plant-room-inspection.png"
                      alt="Engineer performing inspection on industrial boiler and plant room equipment"
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 100vw, 60vw"
                      loading="lazy"
                    />
                  </div>
                  <div className="relative aspect-[4/3] overflow-hidden rounded-[1.5rem]">
                    <Image
                      src="/images/about/boiler-diagnostic.png"
                      alt="Technician taking diagnostic readings on boiler with combustion analyzer"
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 50vw, 30vw"
                      loading="lazy"
                    />
                  </div>
                  <div className="relative aspect-[4/3] overflow-hidden rounded-[1.5rem]">
                    <Image
                      src="/images/about/gas-meter-inspection.png"
                      alt="Gas Safe engineer inspecting outdoor gas meter"
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 50vw, 30vw"
                      loading="lazy"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats + philosophy – single dark geometric band */}
      <section
        className="relative bg-[#05080c] py-20 md:py-24 overflow-hidden"
        aria-label="Our philosophy and track record"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-8 h-60 w-72 rotate-6 rounded-[3rem] border border-white/8" />
          <div className="absolute -left-40 bottom-0 h-56 w-80 -rotate-6 rounded-[3rem] border border-[#e2c977]/25" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-white/12 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="space-y-3 max-w-xl">
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                What We Stand For
              </span>
              <h2 className="text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                Transparency, Integrity, Professionalism
              </h2>
              <p className="text-xs md:text-sm text-[#a5b1c1] leading-relaxed">
                {COMMITMENT_COPY}
              </p>
              <p className="text-xs md:text-sm text-[#a5b1c1] leading-relaxed">
                {COMPANY.mission}
              </p>
            </div>

          </div>

          <div className="grid gap-6 md:grid-cols-4">
            {STATS.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-5 text-center"
              >
                <p className="text-3xl md:text-4xl font-technical font-extrabold text-white tracking-tight">
                  <AnimatedStatValue value={stat.value} />
                </p>
                <p className="mt-2 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#9aa3b0]">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-6 max-w-lg text-[11px] md:text-xs text-[#9aa3b0]">
            Every statistic is tied to real projects delivered across{" "}
            {COMPANY.areas}. It&apos;s how we measure the reliability clients
            feel on site.
          </p>
        </div>
      </section>

      {/* Meet the founder – full-width achievement showcase */}
      <section
        className="relative py-24 md:py-32 overflow-hidden"
        aria-label="Meet the founder"
      >
        <div className="absolute inset-0 bg-[#05080c]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-90" />
        <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977]/70 to-transparent opacity-70" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute right-0 top-1/4 h-72 w-96 -rotate-6 rounded-[3rem] border border-[#e2c977]/12" />
          <div className="absolute left-0 bottom-1/4 h-64 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/10" />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-px w-full max-w-xl bg-gradient-to-r from-transparent via-[#e2c977]/20 to-transparent" />
        </div>

        <div className="relative w-full px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14 md:mb-16">
            <span className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4 block">
              The person behind {COMPANY.name}
            </span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white tracking-[0.2em] uppercase">
              Meet the Founder
            </h2>
            <p className="mt-4 text-[#9aa3b0] text-sm md:text-base max-w-2xl mx-auto">
              Leadership, standards and values that define how we work.
            </p>
          </div>

          <div className="relative w-full">
            <div className="overflow-hidden rounded-none md:rounded-[2.25rem] border-y md:border-2 border-[#e2c977]/30 bg-gradient-to-br from-[#0a0f14] via-[#0d1319] to-[#0a0f14] shadow-[0_32px_80px_rgba(0,0,0,0.6),0_0_0_1px_rgba(226,201,119,0.1)]">
              <div className="grid gap-0 md:grid-cols-[minmax(380px,1.15fr)_1fr] min-h-[380px] md:min-h-[520px]">
                {/* Founder image – full-width column, properly visible */}
                <div className="relative w-full h-[340px] sm:h-[400px] md:h-full md:min-h-[520px]">
                  <div className="absolute inset-0 bg-gradient-to-t md:bg-gradient-to-r from-[#0a0f14]/80 via-transparent to-transparent md:via-transparent md:to-[#0a0f14]/60 z-10 pointer-events-none" />
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-3/4 bg-gradient-to-b from-transparent via-[#e2c977]/50 to-transparent rounded-full hidden md:block z-20" />
                  <Image
                    src="/images/about/founder-800.jpg"
                    alt={`${COMPANY.founder}, Founder of ${COMPANY.name}`}
                    fill
                    className="object-cover object-[65%_20%] md:object-[75%_center]"
                    sizes="(max-width: 768px) 100vw, 55vw"
                    loading="lazy"
                    priority={false}
                  />
                </div>

                {/* Content */}
                <div className="relative flex flex-col justify-center px-6 py-10 md:px-12 md:py-14">
                  <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977] mb-2">
                    Founder
                  </span>
                  <h3 className="text-3xl md:text-4xl lg:text-[2.75rem] font-technical font-extrabold uppercase tracking-[0.22em] text-[#e2c977] mb-5">
                    {COMPANY.founder}
                  </h3>
                  <p className="text-sm md:text-base text-[#b3c0d0] leading-relaxed mb-8 max-w-xl">
                    <span className="text-white font-semibold">
                      Founder of {COMPANY.name}
                    </span>
                    {" — "}
                    After a successful career in the corporate sector,{" "}
                    {COMPANY.founder} established {COMPANY.name} with a clear
                    ambition: to deliver a truly bespoke mechanical, electrical,
                    and gas service.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {[
                      "Discipline in every engineered system",
                      "Integrity in pricing, reporting and handover",
                      "Reliability on planned and emergency work",
                      `Coverage across ${COMPANY.areas}`,
                    ].map((item) => (
                      <div
                        key={item}
                        className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/5 px-4 py-3"
                      >
                        <span className="h-[2px] w-5 flex-shrink-0 bg-[#e2c977]" />
                        <span className="text-[11px] md:text-xs font-technical uppercase tracking-[0.25em] text-[#d6e0ec]">
                          {item}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why choose us – dark geometric grid */}
      <section
        className="relative bg-[#0b1015] py-20 md:py-24 overflow-hidden"
        aria-label="Why choose us"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-8 h-60 w-80 rotate-6 rounded-[3rem] border border-white/8" />
          <div className="absolute -left-40 bottom-0 h-56 w-80 -rotate-6 rounded-[3rem] border border-[#e2c977]/25" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-white/12 to-transparent" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 md:mb-16">
            <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977] mb-4 block">
              Why Clients Choose DPS
            </span>
            <h2 className="text-3xl md:text-4xl font-technical font-extrabold text-white tracking-[0.26em] uppercase">
              What We Deliver
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {WHY_CHOOSE_ITEMS.map((item, i) => (
              <div
                key={item.title}
                className="group relative overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/5 px-6 py-6 md:px-7 md:py-7 transition-transform duration-300 hover:-translate-y-1"
              >
                <div className="pointer-events-none absolute -right-10 -top-10 h-20 w-24 rotate-6 border border-white/10 opacity-40" />
                <div className="relative flex flex-col gap-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#e2c977]/40 bg-[#141a23]">
                      <item.icon size={20} className="text-[#e2c977]" />
                    </div>
                    <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#9aa3b0]">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="text-[11px] md:text-xs font-technical font-extrabold uppercase tracking-[0.3em] text-white">
                    {item.title}
                  </h3>
                  <p className="text-[11px] md:text-sm text-[#b3c0d0] leading-relaxed">
                    {item.strength}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Accreditations & certifications — achievement showcase */}
      <section
        className="relative py-24 md:py-32 overflow-hidden"
        aria-label="Accreditations and certifications"
      >
        {/* Dark base with gold-accent band */}
        <div className="absolute inset-0 bg-[#05080c]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-90" />
        <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977]/70 to-transparent opacity-70" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[80%] w-[90%] max-w-2xl rounded-full border border-[#e2c977]/15 opacity-60" />
          <div className="absolute right-0 top-20 h-40 w-64 rotate-12 rounded-[2rem] border border-[#e2c977]/12" />
          <div className="absolute left-0 bottom-20 h-36 w-56 -rotate-12 rounded-[2rem] border border-[#e2c977]/12" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center text-center mb-16 md:mb-20">
            <span className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4 block">
              Trusted credentials
            </span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white tracking-[0.2em] uppercase mb-4">
              Our Accreditations & Achievements
            </h2>
            <p className="text-[#b3c0d0] text-sm md:text-base max-w-xl leading-relaxed">
              Certifications that reflect our commitment to safety, compliance and community. Each badge represents a standard we meet and maintain.
            </p>
            <div className="flex items-center gap-4 mt-6 text-[11px] font-technical uppercase tracking-[0.35em] text-[#9aa3b0]">
              <span className="h-[1px] w-8 bg-[#e2c977]/50" />
              Certified · Compliant · Community
              <span className="h-[1px] w-8 bg-[#e2c977]/50" />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-14 md:grid-cols-3 md:gap-16 w-full max-w-4xl mx-auto">
            {/* Gas Safe Register */}
            <div className="group flex flex-col items-center">
              <div className="relative flex h-36 w-36 md:h-40 md:w-40 items-center justify-center rounded-full border-2 border-[#e2c977]/40 bg-gradient-to-b from-white/10 to-white/5 shadow-[0_24px_56px_rgba(0,0,0,0.5),0_0_0_1px_rgba(226,201,119,0.15)] transition-all duration-300 group-hover:border-[#e2c977]/70 group-hover:shadow-[0_28px_64px_rgba(0,0,0,0.6),0_0_32px_rgba(226,201,119,0.12)]">
                <Image
                  src="/images/gas-safe-register.png"
                  alt="Gas Safe Register"
                  fill
                  className="object-contain p-5"
                  sizes="160px"
                />
              </div>
              <p className="mt-4 text-xs md:text-sm font-technical font-bold uppercase tracking-[0.28em] text-white text-center">
                Gas Safe Register
              </p>
              <p className="mt-1 text-[11px] text-[#9aa3b0] text-center max-w-[200px]">
                Industry-recognised gas safety certification
              </p>
            </div>

            {/* Next Level FC Sponsor */}
            <div className="group flex flex-col items-center md:-mt-4">
              <div className="relative flex h-40 w-40 md:h-44 md:w-44 items-center justify-center rounded-full border-2 border-[#e2c977]/50 bg-gradient-to-b from-white/12 to-white/5 shadow-[0_28px_64px_rgba(0,0,0,0.55),0_0_0_1px_rgba(226,201,119,0.2)] transition-all duration-300 group-hover:border-[#e2c977]/80 group-hover:shadow-[0_32px_72px_rgba(0,0,0,0.6),0_0_40px_rgba(226,201,119,0.15)]">
                <Image
                  src="/images/next-level-fc.png"
                  alt="Next Level FC"
                  fill
                  className="object-contain p-6"
                  sizes="176px"
                />
              </div>
              <p className="mt-4 text-xs md:text-sm font-technical font-bold uppercase tracking-[0.28em] text-[#e2c977] text-center">
                Next Level FC Sponsor
              </p>
              <p className="mt-1 text-[11px] text-[#9aa3b0] text-center max-w-[200px]">
                Proud community partnership
              </p>
            </div>

            {/* SafeContractor Approved */}
            <div className="group flex flex-col items-center">
              <div className="relative flex h-36 w-36 md:h-40 md:w-40 items-center justify-center rounded-full border-2 border-[#e2c977]/40 bg-gradient-to-b from-white/10 to-white/5 shadow-[0_24px_56px_rgba(0,0,0,0.5),0_0_0_1px_rgba(226,201,119,0.15)] transition-all duration-300 group-hover:border-[#e2c977]/70 group-hover:shadow-[0_28px_64px_rgba(0,0,0,0.6),0_0_32px_rgba(226,201,119,0.12)]">
                <Image
                  src="/images/safe-contractor.png"
                  alt="SafeContractor Approved"
                  fill
                  className="object-contain p-5"
                  sizes="160px"
                />
              </div>
              <p className="mt-4 text-xs md:text-sm font-technical font-bold uppercase tracking-[0.28em] text-white text-center">
                SafeContractor Approved
              </p>
              <p className="mt-1 text-[11px] text-[#9aa3b0] text-center max-w-[200px]">
                Audited health & safety and quality standards
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Who we work with – full-width showcase */}
      <section
        className="relative py-24 md:py-28 overflow-hidden"
        aria-label="Sectors we work with"
      >
        <div className="absolute inset-0 bg-[#0b1015]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-80" />
        <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977]/60 to-transparent opacity-70" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[70%] w-[85%] max-w-3xl rounded-full border border-[#e2c977]/10 opacity-50" />
          <div className="absolute right-0 top-1/4 h-48 w-64 rotate-12 rounded-[2rem] border border-white/5" />
          <div className="absolute left-0 bottom-1/4 h-40 w-56 -rotate-12 rounded-[2rem] border border-[#e2c977]/10" />
        </div>

        <div className="relative w-full px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 md:mb-16">
            <span className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4 block">
              Our client base
            </span>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white tracking-[0.2em] uppercase">
              Who We Work With
            </h2>
            <p className="mt-4 text-[#9aa3b0] text-sm md:text-base max-w-2xl mx-auto">
              From homeowners to estates and corporates — we deliver the same standards across every sector.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 max-w-6xl mx-auto">
            {SECTORS_SERVED.map((sector) => (
              <div
                key={sector}
                className="group relative rounded-2xl border border-white/10 bg-white/5 px-6 py-6 md:px-7 md:py-8 text-center transition-all duration-300 hover:border-[#e2c977]/30 hover:bg-white/[0.08]"
              >
                <span className="absolute left-4 top-4 h-[2px] w-6 bg-gradient-to-r from-[#e2c977] to-transparent opacity-70" />
                <p className="text-xs md:text-sm font-technical font-bold uppercase tracking-[0.28em] text-white leading-snug">
                  {sector}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABanner
        title="Get in touch"
        subtitle="Ready to book a service or get a free quote? Call us today or use our online form."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
