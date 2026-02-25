"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { Shield, Award, Eye, Phone, Cpu, Wrench, Zap, Flame } from "lucide-react";
import { motion, useScroll, useTransform } from "framer-motion";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ScrollSequenceSection from "@/components/sections/ScrollSequenceSection";
import { registerGSAP } from "@/components/animations/gsap-init";
import { COMPANY, ACCREDITATIONS, CAPABILITY_CORE_SERVICES, KEY_STRENGTHS, SECTORS_SERVED, HEALTH_SAFETY_COPY, COMMITMENT_COPY } from "@/lib/constants";

const approach = [
  {
    icon: Shield,
    title: "Reliability You Can Count On",
    description: "We arrive on time, communicate clearly, and complete every job to a high standard — no exceptions.",
  },
  {
    icon: Award,
    title: "Fully Qualified Engineers",
    description: "Gas Safe registered engineers with years of hands-on experience across all makes and models.",
  },
  {
    icon: Eye,
    title: "Honest, Transparent Pricing",
    description: "You receive a clear, fixed quote before any work begins. No hidden charges, no surprises.",
  },
];

export default function AboutPage() {
  const whoWeAreRef = useRef<HTMLElement>(null);

  const { scrollYProgress } = useScroll({
    target: whoWeAreRef,
    offset: ["start center", "end center"],
  });
  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  useEffect(() => {
    registerGSAP();
  }, []);

  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="About Us"
        subtitle={`${COMPANY.name} — Mechanical, electrical, and gas services across domestic and commercial sectors. Professional engineering across ${COMPANY.areas}.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "About Us" }]}
        backgroundImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
        compact
      />

      {/* Who We Are — same design as How We Work: timeline + alternating cards */}
      <ScrollSequenceSection
        ref={whoWeAreRef}
        frameDir="/images/about-who-we-are-frames/frame"
        frameCount={145}
        className="py-12 sm:py-24 md:py-32 lg:py-40 pl-[max(0.75rem,env(safe-area-inset-left))] pr-[max(0.75rem,env(safe-area-inset-right))] sm:px-4 bg-brand-surface"
        contentClassName="max-w-7xl mx-auto relative z-10"
        aria-label="Who we are"
      >
        <div className="text-center mb-12 sm:mb-16 md:mb-24 lg:mb-32 relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full border border-brand-red/20 bg-brand-red/5 mb-3 sm:mb-6 md:mb-8"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse" />
            <span className="text-[9px] sm:text-[10px] font-technical font-bold uppercase tracking-[0.35em] sm:tracking-[0.4em] text-brand-red">
              Gas Safe Registered
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-technical font-extrabold mb-3 sm:mb-6 md:mb-8 text-brand-text tracking-wider uppercase px-1 sm:px-2"
          >
            Who We <span className="text-brand-muted/50">Are.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-[11px] sm:text-sm font-light max-w-2xl mx-auto uppercase tracking-[0.15em] sm:tracking-[0.2em] text-brand-muted px-1 sm:px-2 leading-snug"
          >
            Commercial &amp; domestic mechanical, electrical, and gas services across {COMPANY.areas}. Discipline, integrity, reliability.
          </motion.p>
        </div>

        <div className="relative">
          <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] bg-brand-card-border hidden lg:block">
            <motion.div
              className="absolute top-0 left-0 right-0 bg-brand-red origin-top"
              style={{ height: lineHeight }}
            />
          </div>

          <div className="space-y-8 sm:space-y-12 md:space-y-16 lg:space-y-0 relative z-10">
            {/* 01 — Intro + values (left) */}
            <div className="relative lg:flex items-center justify-between lg:h-80">
              <div className="lg:w-[45%] lg:text-right lg:order-1">
                <motion.div
                  initial={{ opacity: 0, x: -50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl bg-brand-navy/70 backdrop-blur-md border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                >
                  <p className="text-[9px] sm:text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-2 sm:mb-3">01</p>
                  <h3 className="text-lg sm:text-xl md:text-2xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">Who We Are</h3>
                  <p className="text-brand-text/90 font-light leading-relaxed text-sm md:text-base mb-4">
                    {COMPANY.name} specialises in both the domestic and commercial sectors, delivering comprehensive mechanical, electrical, and gas services. We provide reliable, high-quality solutions tailored to meet the needs of homeowners, landlords, and businesses.
                  </p>
                  <p className="text-brand-muted font-light leading-relaxed text-xs sm:text-sm">
                    Our experienced team is committed to safety, efficiency, and exceptional workmanship across every project we undertake.
                  </p>
                </motion.div>
              </div>
              <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red" />
              </div>
              <div className="hidden lg:block lg:w-[45%] lg:order-2" />
            </div>

            {/* 02 — Services list (right) */}
            <div className="relative lg:flex items-center justify-between lg:h-80">
              <div className="hidden lg:block lg:w-[45%] lg:order-1" />
              <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red" />
              </div>
              <div className="lg:w-[45%] lg:text-left lg:order-2">
                <motion.div
                  initial={{ opacity: 0, x: 50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl bg-brand-navy/70 backdrop-blur-md border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                >
                  <p className="text-[9px] sm:text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-2 sm:mb-3">02</p>
                  <h3 className="text-lg sm:text-xl md:text-2xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">What We Do</h3>
                  <p className="text-brand-text/90 font-medium text-xs sm:text-sm mb-3">We provide mechanical, electrical, and gas services including:</p>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 list-none">
                    {CAPABILITY_CORE_SERVICES.flatMap((cat) => cat.items).slice(0, 8).map((item) => (
                      <li key={item} className="flex items-center gap-2 text-xs sm:text-sm text-brand-muted">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-red shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </div>
            </div>

            {/* 03 — Pride paragraph (left) */}
            <div className="relative lg:flex items-center justify-between lg:h-80">
              <div className="lg:w-[45%] lg:text-right lg:order-1">
                <motion.div
                  initial={{ opacity: 0, x: -50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl bg-brand-navy/70 backdrop-blur-md border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                >
                  <p className="text-[9px] sm:text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-2 sm:mb-3">03</p>
                  <h3 className="text-lg sm:text-xl md:text-2xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">Our Story</h3>
                  <p className="text-brand-muted font-light leading-relaxed text-xs sm:text-sm mb-4">
                    Founded in {COMPANY.founded} by {COMPANY.founder}, after many years of dedicated service in the Armed Forces and a successful career within the corporate sector, {COMPANY.name} was established from a strong desire to succeed and to deliver a truly bespoke service within a diverse and highly competitive industry.
                  </p>
                  <p className="text-brand-muted font-light leading-relaxed text-xs sm:text-sm">
                    The ambition was clear — to build a company committed to providing an exceptional level of service, available 24 hours a day, 7 days a week. Built on the core values of <strong className="text-brand-text font-semibold">discipline</strong>, <strong className="text-brand-text font-semibold">integrity</strong>, and <strong className="text-brand-text font-semibold">reliability</strong>, we pride ourselves on delivering dependable solutions with professionalism and meticulous attention to detail. With {COMPANY.industryExperience} of industry experience, we maintain stringent quality standards and rigorous adherence to comprehensive Health &amp; Safety practices.
                  </p>
                </motion.div>
              </div>
              <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red" />
              </div>
              <div className="hidden lg:block lg:w-[45%] lg:order-2" />
            </div>

            {/* 04 — Quote (right) */}
            <div className="relative lg:flex items-center justify-between lg:h-80">
              <div className="hidden lg:block lg:w-[45%] lg:order-1" />
              <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red" />
              </div>
              <div className="lg:w-[45%] lg:text-left lg:order-2">
                <motion.div
                  initial={{ opacity: 0, x: 50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl border-l-4 border-brand-red bg-brand-navy/70 backdrop-blur-md border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                >
                  <p className="text-[9px] sm:text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-2 sm:mb-3">04</p>
                  <h3 className="text-lg sm:text-xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">The DPS Promise</h3>
                  <p className="text-brand-text font-technical font-bold text-base md:text-lg leading-snug">
                    At {COMPANY.name}, our clients take precedence in every project we undertake. Your satisfaction, safety, and trust are our highest priorities.
                  </p>
                </motion.div>
              </div>
            </div>

            {/* 05 — Gas Safe + stats (left) */}
            <div className="relative lg:flex items-center justify-between lg:h-80">
              <div className="lg:w-[45%] lg:text-right lg:order-1">
                <motion.div
                  initial={{ opacity: 0, x: -50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl bg-brand-navy/70 backdrop-blur-md border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                >
                  <p className="text-[9px] sm:text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-2 sm:mb-3">05</p>
                  <h3 className="text-lg sm:text-xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">Certified &amp; Experienced</h3>
                  <p className="text-brand-muted font-light text-xs sm:text-sm mb-4">
                    With {COMPANY.industryExperience} of industry experience, we maintain stringent quality standards and rigorous Health &amp; Safety practices — excellence remains at the forefront of everything we do.
                  </p>
                  <div className="p-4 rounded-xl border border-brand-card-border bg-brand-surface/50 text-center mb-4">
                    <p className="text-brand-text font-technical font-bold tracking-widest uppercase text-xs">Gas Safe Registered</p>
                    <p className="text-brand-red font-mono font-semibold mt-1">{COMPANY.gasSafeNumber}</p>
                    <p className="text-brand-muted text-[10px] font-technical uppercase tracking-wider mt-2">Fully insured · Qualified engineers</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-brand-card-border bg-brand-surface/50 p-4 text-center">
                      <p className="text-3xl sm:text-4xl font-technical font-extrabold text-brand-red tracking-tighter">10+</p>
                      <p className="text-[9px] tracking-[0.2em] uppercase text-brand-muted font-bold font-technical mt-1">Years</p>
                    </div>
                    <div className="rounded-xl border border-brand-card-border bg-brand-surface/50 p-4 text-center">
                      <p className="text-3xl sm:text-4xl font-technical font-extrabold text-brand-blue tracking-tighter">500+</p>
                      <p className="text-[9px] tracking-[0.2em] uppercase text-brand-muted font-bold font-technical mt-1">Jobs</p>
                    </div>
                  </div>
                </motion.div>
              </div>
              <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                <motion.div initial={{ scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red" />
              </div>
              <div className="hidden lg:block lg:w-[45%] lg:order-2" />
            </div>
          </div>
        </div>
      </ScrollSequenceSection>

      {/* Capability — Core Services, Key Strengths, H&S, Sectors, Commitment */}
      <section className="py-24 md:py-32 bg-brand-steel relative overflow-hidden" aria-label="Our capability">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              What We Offer
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">
              Our <span className="text-brand-red">Capability</span>
            </h2>
            <p className="text-brand-muted text-sm font-light max-w-2xl mx-auto uppercase tracking-wider">
              A specialist provider of mechanical, electrical, and gas services operating across domestic and commercial sectors. We deliver safe, compliant, and high-quality engineering solutions tailored to each client and project.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            {CAPABILITY_CORE_SERVICES.map((service, i) => {
              const Icon = service.title === "Mechanical Services" ? Wrench : service.title === "Electrical Services" ? Zap : Flame;
              return (
                <motion.div
                  key={service.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-brand-navy border border-brand-card-border rounded-2xl p-6 hover:border-brand-red/20 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-brand-red/10 border border-brand-red/20 flex items-center justify-center">
                      <Icon size={18} className="text-brand-red" />
                    </div>
                    <h3 className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-widest">
                      {service.title}
                    </h3>
                  </div>
                  <ul className="space-y-2">
                    {service.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-brand-muted text-xs font-technical uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-red shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              );
            })}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-10"
          >
            <h3 className="text-brand-text text-xs font-technical font-bold uppercase tracking-[0.3em] mb-4 text-center">Key Strengths</h3>
            <div className="flex flex-wrap justify-center gap-3">
              {KEY_STRENGTHS.map((strength, i) => (
                <span
                  key={i}
                  className="px-4 py-2 rounded-full border border-brand-card-border bg-brand-navy/80 text-brand-muted text-[10px] font-technical uppercase tracking-wider"
                >
                  {strength}
                </span>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-6 md:p-8 rounded-2xl border border-brand-card-border bg-brand-navy/50 mb-10"
          >
            <h3 className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-widest mb-3">Health &amp; Safety &amp; Compliance</h3>
            <p className="text-brand-muted text-xs sm:text-sm font-light leading-relaxed uppercase tracking-wider">
              {HEALTH_SAFETY_COPY}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-10"
          >
            <h3 className="text-brand-text text-xs font-technical font-bold uppercase tracking-[0.3em] mb-4 text-center">Sectors Served</h3>
            <div className="flex flex-wrap justify-center gap-3">
              {SECTORS_SERVED.map((sector) => (
                <span
                  key={sector}
                  className="px-4 py-2 rounded-full border border-brand-red/20 bg-brand-red/5 text-brand-text text-[10px] font-technical font-bold uppercase tracking-wider"
                >
                  {sector}
                </span>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto"
          >
            <p className="text-brand-muted text-sm font-light leading-relaxed uppercase tracking-wider">
              {COMMITMENT_COPY}
            </p>
          </motion.div>
        </div>
      </section>

      {/* Accreditations */}
      <section className="py-48 bg-brand-steel relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Accreditations &amp; Qualifications
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Certified. <span className="text-brand-muted/40">Compliant.</span>
            </h2>
          </motion.div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {ACCREDITATIONS.map((acc, i) => (
              <motion.div
                key={acc.title}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="bg-brand-navy border border-brand-card-border rounded-2xl p-6"
              >
                <h3 className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-widest mb-3">
                  {acc.title}
                </h3>
                {acc.items.length > 0 ? (
                  <ul className="space-y-1">
                    {acc.items.map((item) => (
                      <li key={item} className="text-brand-muted text-[10px] font-technical uppercase tracking-wider">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-brand-muted text-[10px] font-technical uppercase tracking-wider">Held</p>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Our Approach */}
      <section className="py-48 bg-brand-navy relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[600px] bg-brand-blue/5 blur-[180px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              The <span className="text-brand-red">DPS Promise</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {approach.map((item, i) => (
              <div key={item.title} className="bg-brand-surface rounded-[2.5rem] p-12 text-center border border-brand-card-border shadow-2xl hover:border-brand-red/30 transition-all duration-500 group relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-24 h-24 bg-brand-navy border border-brand-card-border rounded-3xl flex items-center justify-center mx-auto mb-10 group-hover:bg-brand-red/10 group-hover:border-brand-red/30 transition-all duration-500 relative">
                  <item.icon size={40} className="text-brand-text/20 group-hover:text-brand-red transition-all duration-500 relative z-10" />
                </div>
                <h3 className="text-xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className="text-brand-muted text-xs leading-relaxed font-light uppercase tracking-wider">
                  {item.description}
                </p>

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-red/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Engineers at Work Photo Section */}
      <section className="py-48 bg-brand-surface overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-24"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Our Engineers
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Experienced. <span className="text-brand-muted/40">Qualified.</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative overflow-hidden rounded-3xl border border-brand-card-border group"
            >
              <Image
                src="/images/engineers-at-work.png"
                alt="DPS engineers working on commercial heating installation"
                width={600}
                height={450}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black/70 to-transparent">
                <p className="text-white text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Commercial Heating Installation
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative overflow-hidden rounded-3xl border border-brand-card-border group"
            >
              <Image
                src="/images/9687b2e0-9aaf-4272-adc5-52162cb88115.jpeg"
                alt="DPS engineer team installing copper heating pipework"
                width={600}
                height={450}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black/70 to-transparent">
                <p className="text-white text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Central Heating Pipework
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Proud sponsor — Next Level FC */}
      <section className="py-16 md:py-20 bg-brand-navy border-y border-brand-card-border" aria-label="Community sponsorship">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-brand-muted text-sm font-technical font-bold uppercase tracking-[0.4em] mb-8">
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
      </section>

      <CTABanner
        title="Get in Touch"
        subtitle="Ready to book a service or get a free quote? Call us today or use our online form."
      />
    </div>
  );
}
