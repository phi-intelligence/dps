"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Image from "next/image";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { motion } from "framer-motion";

const ServiceAreasMap = dynamic(
  () => import("@/components/ui/ServiceAreasMap"),
  { ssr: false, loading: () => <div className="w-full h-full bg-brand-navy animate-pulse rounded-3xl" /> }
);
import {
  Flame,
  Wind,
  Phone,
  ArrowRight,
  Zap,
  Shield,
  Clock,
  Star,
  ChevronDown,
  MapPin,
} from "lucide-react";
import TrustBar from "@/components/ui/TrustBar";
import ServiceCard from "@/components/ui/ServiceCard";
import ReviewCard from "@/components/ui/ReviewCard";
import CTABanner from "@/components/ui/CTABanner";
import StatsCounter from "@/components/sections/StatsCounter";
import ProcessSteps from "@/components/sections/ProcessSteps";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";
import Hero3DScene from "@/components/animations/Hero3DScene";
import SectionWaves from "@/components/ui/SectionWaves";
import { COMPANY, REVIEWS, SERVICE_AREAS } from "@/lib/constants";
import { registerGSAP, gsap } from "@/components/animations/gsap-init";

const services = [
  {
    icon: Flame,
    title: "Heating",
    description: "Expert boiler and heating system services for domestic and commercial properties.",
    subservices: ["Boiler Repair", "Boiler Installation", "Boiler Servicing"],
    href: "/services/heating",
  },
  {
    icon: Wind,
    title: "Air Conditioning",
    description: "Professional AC installation and servicing for homes and businesses.",
    subservices: ["AC Installation", "AC Servicing", "Commercial AC"],
    href: "/services/air-conditioning",
  },
];

const trustPoints = [
  {
    icon: Zap,
    title: "Fast Response",
    description: "We respond quickly and aim for same-day appointments for urgent work.",
  },
  {
    icon: Shield,
    title: "Gas Safe Registered",
    description: "All engineers are Gas Safe registered and fully qualified.",
  },
  {
    icon: Star,
    title: "Clean & Tidy Work",
    description: "We respect your home — always leaving the work area clean.",
  },
  {
    icon: Clock,
    title: "Transparent Pricing",
    description: "Clear quotes upfront — no hidden charges, ever.",
  },
];

export default function HomePage() {
  const { openQuoteModal } = useQuoteModal();
  useEffect(() => {
    registerGSAP();
  }, []);

  return (
    <div className="bg-brand-surface text-brand-text overflow-hidden relative">
      <EnergyFlowBackground />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-32 pb-20 overflow-hidden" aria-label="Hero">
        {/* Background image */}
        <div className="absolute inset-0 z-0">
          <Image
            src="/images/blueprint-boiler-cutaway.png"
            alt=""
            fill
            className="object-cover object-center opacity-30 dark:opacity-20"
            sizes="100vw"
            priority
            aria-hidden
          />
          <div className="absolute inset-0 bg-brand-surface/55 dark:bg-brand-surface/85" />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 border border-brand-red/10 bg-brand-red/5 backdrop-blur-md rounded-full px-4 py-1.5 mb-8"
              >
                <div className="w-2 h-2 rounded-full bg-brand-red animate-pulse" />
                <span className="text-brand-red text-sm font-technical tracking-widest uppercase">
                  Gas Safe Registered // {COMPANY.areas}
                </span>
              </motion.div>

              <div className="flex items-center gap-5 mb-6">
                <Image
                  src="/images/logo.jpg"
                  alt="DPS Heating Services"
                  width={80}
                  height={80}
                  priority
                  loading="eager"
                  className="rounded-2xl shadow-lg shadow-brand-red/10"
                  style={{ width: "auto", height: "auto" }}
                />
                <h1 className="text-5xl md:text-8xl font-technical font-bold text-brand-text leading-[1.05] tracking-tighter uppercase">
                  DPS<br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-red via-brand-purple to-brand-blue animate-gradient-x">
                    Heating.
                  </span>
                </h1>
              </div>

              <p className="text-xl md:text-2xl text-brand-muted mb-10 max-w-xl leading-relaxed font-light uppercase tracking-wider">
                Professional heating &amp; air conditioning services across {COMPANY.areas}. Gas Safe registered engineers you can trust.
              </p>

              <div className="flex flex-col sm:flex-row gap-5">
                <button
                  type="button"
                  onClick={() => openQuoteModal()}
                  className="group relative inline-flex items-center justify-center gap-2 bg-brand-red text-white px-8 py-4 rounded-full font-bold text-lg transition-all hover:bg-brand-red/80 overflow-hidden shadow-xl shadow-brand-red/20"
                >
                  <span className="relative z-10">Get a Free Quote</span>
                  <ArrowRight size={20} className="relative z-10 group-hover:translate-x-1 transition-transform" />
                  <div className="absolute inset-0 bg-brand-card-hover scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
                </button>
                <a
                  href={`tel:${COMPANY.phone}`}
                  className="inline-flex items-center justify-center gap-2 bg-transparent border border-brand-card-border-hover hover:border-brand-blue/50 hover:bg-brand-blue/5 text-brand-text px-8 py-4 rounded-full font-technical font-bold text-base tracking-widest uppercase transition-all"
                >
                  <Phone size={18} className="text-brand-blue" />
                  Call Us Now
                </a>
              </div>
            </motion.div>

            {/* Right column: 3D logo */}
            <div className="relative w-full flex justify-center lg:justify-end">
              <Hero3DScene className="w-full" modelPath="/dps.glb" />
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 hidden md:block z-10"
          aria-hidden
        >
          <div className="w-5 h-8 border border-brand-card-border-hover rounded-full flex items-start justify-center pt-2">
            <motion.div
              animate={{ y: [0, 10, 0], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-1 h-1 bg-brand-red rounded-full shadow-[0_0_8px_rgba(220,38,38,0.5)]"
            />
          </div>
        </motion.div>
      </section>

      {/* Trust Bar */}
      <div className="relative z-20 -mt-10 px-4">
        <div className="max-w-6xl mx-auto glass-panel rounded-2xl p-2 shadow-2xl shadow-brand-red/5">
          <TrustBar />
        </div>
      </div>

      {/* Services Overview */}
      <section className="py-48 relative z-10 bg-brand-steel overflow-hidden" aria-label="Our services">
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-24 text-center"
          >
            <span className="text-brand-red text-sm font-bold uppercase tracking-[0.4em] mb-4 block">
              What We Do
            </span>
            <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Our <span className="text-brand-red">Services</span>
            </h2>
            <p className="text-brand-muted mt-6 max-w-2xl mx-auto text-sm font-light leading-relaxed uppercase tracking-wider">
              Reliable heating and air conditioning services for homes and businesses across {COMPANY.areas}.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {services.map((service, i) => (
              <ServiceCard key={service.title} {...service} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* About / Engineering Quality */}
      <section className="py-48 bg-brand-surface relative overflow-hidden">
        <SectionWaves variant="mixed" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="space-y-10 order-2 lg:order-1"
            >
              <div>
                <span className="text-brand-blue text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
                  About DPS Heating
                </span>
                <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase leading-none">
                  Qualified <br /><span className="text-brand-blue">Engineers.</span>
                </h2>
              </div>
              <p className="text-brand-muted text-sm font-light leading-relaxed uppercase tracking-wider max-w-lg">
                DPS Heating Services Ltd has been providing professional heating and air conditioning services across {COMPANY.areas} for over a decade. All our engineers are Gas Safe registered and fully insured.
              </p>
              <div className="space-y-5">
                {[
                  { label: "Gas Safe registered on every job" },
                  { label: "Full system inspection before sign-off" },
                  { label: "Upfront, transparent pricing" },
                  { label: "Domestic and commercial work covered" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-4 group">
                    <div className="w-1.5 h-1.5 rounded-full bg-brand-blue/30 group-hover:bg-brand-blue transition-colors shrink-0" />
                    <span className="text-[10px] font-technical font-bold text-brand-muted group-hover:text-brand-text transition-colors uppercase tracking-widest">{item.label}</span>
                  </div>
                ))}
              </div>
              <Link
                href="/about"
                className="inline-flex items-center gap-3 border border-brand-card-border-hover hover:border-brand-blue/40 bg-brand-card hover:bg-brand-blue/5 text-brand-text px-8 py-4 rounded-full font-technical font-bold text-[10px] tracking-widest uppercase transition-all"
              >
                <ArrowRight size={14} className="text-brand-blue" />
                About Us
              </Link>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="order-1 lg:order-2 relative aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl"
            >
              <Image
                src="/images/plumbing-pipes.jpg"
                alt="DPS qualified engineer working on plumbing and heating systems"
                fill
                className="object-cover object-center"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Engineer Photo Strip */}
      <div className="relative h-80 overflow-hidden">
        <Image
          src="/images/hero-bg.jpg"
          alt="DPS engineer working on a boiler installation"
          fill
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-brand-surface/60" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-4">
            <p className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.5em] mb-3">
              Gas Safe Registered Engineers
            </p>
            <p className="text-brand-text text-2xl md:text-4xl font-technical font-extrabold tracking-widest uppercase">
              Every Job Done Right
            </p>
          </div>
        </div>
      </div>

      {/* How We Work */}
      <ProcessSteps
        title="How We Work"
        subtitle="Simple, straightforward service from first contact to job completion — with no hidden surprises."
        dark
      />

      {/* Why Choose DPS */}
      <section className="py-48 bg-brand-steel relative overflow-hidden">
        <SectionWaves variant="warm" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-40"
          >
            <h2 className="text-4xl md:text-7xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase">
              Why Choose <span className="text-brand-red">DPS</span>
            </h2>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.6em]">
              Professional Heating &amp; Air Conditioning Services
            </p>
          </motion.div>

          <div className="mb-48">
            <StatsCounter />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-16">
            {trustPoints.map((point, i) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="group relative"
              >
                <div className="relative z-10">
                  <div className="w-16 h-16 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-red/20 group-hover:bg-brand-red/5 transition-all duration-500">
                    <point.icon size={28} className="text-brand-red group-hover:scale-110 transition-transform" />
                  </div>
                  <h3 className="text-brand-text text-lg font-technical font-extrabold mb-4 tracking-widest uppercase">{point.title}</h3>
                  <p className="text-brand-muted text-[10px] font-technical leading-relaxed uppercase tracking-widest">{point.description}</p>
                </div>

                <span className="absolute -top-6 -left-4 text-7xl font-technical font-black text-white/[0.02] group-hover:text-brand-red/[0.04] transition-colors pointer-events-none">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Areas Map */}
      <section className="py-48 bg-brand-surface relative overflow-hidden" aria-label="Service areas map">
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Heading */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 border border-brand-red/20 bg-brand-red/5 backdrop-blur-md rounded-full px-5 py-2 mb-6">
              <MapPin size={13} className="text-brand-red" />
              <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                Coverage
              </span>
            </div>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase leading-none mb-6">
              Where We <span className="text-brand-red">Operate</span>
            </h2>
            <p className="text-brand-muted text-sm font-light uppercase tracking-wider max-w-xl mx-auto">
              {SERVICE_AREAS.length}+ areas across South-West London. Click any pin to find out more.
            </p>
          </motion.div>

          {/* Map + sidebar grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
            {/* Map */}
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="lg:col-span-2 relative rounded-3xl overflow-hidden border border-brand-card-border shadow-2xl"
              style={{ height: "520px" }}
            >
              <ServiceAreasMap />
              {/* Gradient fade on edges */}
              <div className="pointer-events-none absolute inset-0 rounded-3xl ring-1 ring-inset ring-white/5" />
            </motion.div>

            {/* Area list */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-brand-steel border border-brand-card-border rounded-3xl p-6 lg:p-8 self-start"
            >
              <h3 className="text-xs font-technical font-bold uppercase tracking-[0.3em] text-brand-red mb-6 flex items-center gap-2">
                <MapPin size={12} />
                Areas Covered
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {SERVICE_AREAS.map((area) => (
                  <div
                    key={area}
                    className="flex items-center gap-2 text-[10px] font-technical font-bold uppercase tracking-widest text-brand-muted hover:text-brand-text transition-colors group"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-red/30 group-hover:bg-brand-red transition-colors shrink-0" />
                    {area}
                  </div>
                ))}
              </div>
              <div className="mt-8 pt-6 border-t border-brand-card-border">
                <p className="text-[10px] text-brand-muted font-technical uppercase tracking-widest mb-4">
                  Not sure we cover your area?
                </p>
                <Link
                  href="/service-areas"
                  className="inline-flex items-center gap-2 text-[10px] font-technical font-bold uppercase tracking-widest text-brand-red hover:text-brand-text transition-colors"
                >
                  <ArrowRight size={12} />
                  View all service areas
                </Link>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <CTABanner
        title="Ready to Book?"
        subtitle={`Get in touch today for a free, no-obligation quote. Our engineers are ready to help.`}
      />
    </div>
  );
}
