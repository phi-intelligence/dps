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
  Building2,
  Home,
  Phone,
  ArrowRight,
  Zap,
  Shield,
  Clock,
  Star,
  ChevronDown,
  MapPin,
  Target,
  Eye,
  Briefcase,
} from "lucide-react";
import TrustBar from "@/components/ui/TrustBar";
import ReviewCard from "@/components/ui/ReviewCard";
import CTABanner from "@/components/ui/CTABanner";
import StatsCounter from "@/components/sections/StatsCounter";
import CoreServicesSection from "@/components/sections/CoreServicesSection";
import SectionWaves from "@/components/ui/SectionWaves";
import { COMPANY, REVIEWS, SERVICE_AREAS, COMMERCIAL_SERVICES, DOMESTIC_SERVICES, SECTORS_WE_DEAL_WITH, SECTORS_WITH_IMAGES } from "@/lib/constants";
import { registerGSAP, gsap } from "@/components/animations/gsap-init";

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
      {/* Hero Section */}
      <div className="relative">
        <section className="relative min-h-screen flex items-center pt-32 pb-20 overflow-hidden" aria-label="Hero">
        {/* Background image — blueprint */}
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
                  DESIGN • ENGINEER • MAINTAIN // {COMPANY.areas}
                </span>
              </motion.div>

              <div className="mb-6">
                <h1 className="text-4xl md:text-6xl lg:text-7xl font-technical font-bold text-[#d4af37] leading-[1.1] tracking-tighter uppercase">
                  {COMPANY.name}
                </h1>
              </div>

              <p className="text-xl md:text-2xl text-brand-muted mb-10 max-w-xl leading-relaxed font-light uppercase tracking-wider">
                Professional heating and plumbing services across {COMPANY.areas}. Gas Safe registered engineers you can trust.
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

            {/* Right column: logo (same as navbar) */}
            <div className="relative w-full flex justify-center lg:justify-end">
              <div className="w-full aspect-square max-h-[min(85vh,680px)] min-h-[320px] flex items-center justify-center">
                <div className="relative w-64 h-64 sm:w-80 sm:h-80 md:w-96 md:h-96 lg:w-[22rem] lg:h-[22rem]">
                  <Image
                    src="/images/logo.png"
                    alt={COMPANY.name}
                    fill
                    className="object-contain drop-shadow-[0_0_24px_rgba(212,175,55,0.3)]"
                    sizes="(max-width: 640px) 256px, (max-width: 768px) 320px, (max-width: 1024px) 384px, 352px"
                    priority
                  />
                </div>
              </div>
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
              className="w-1 h-1 bg-brand-red rounded-full shadow-[0_0_8px_rgba(212,175,55,0.5)]"
            />
          </div>
        </motion.div>
      </section>
      </div>

      {/* Trust Bar */}
      <div className="relative z-20 -mt-10 px-4">
        <div className="max-w-6xl mx-auto glass-panel rounded-2xl p-2 shadow-2xl shadow-brand-red/5">
          <TrustBar />
        </div>
      </div>

      {/* Services Overview — Commercial & Domestic with images */}
      <section className="py-24 md:py-32 relative z-10 bg-brand-steel overflow-hidden" aria-label="Our services">
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12 md:mb-16 text-center"
          >
            <span className="text-brand-red text-sm font-bold uppercase tracking-[0.4em] mb-4 block">
              What We Do
            </span>
            <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Our <span className="text-brand-red">Services</span>
            </h2>
            <p className="text-brand-muted mt-6 max-w-2xl mx-auto text-sm font-light leading-relaxed uppercase tracking-wider">
              Reliable heating and plumbing services for homes and businesses across {COMPANY.areas}.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
            {/* Commercial section */}
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="group"
            >
              <Link
                href="/services/commercial"
                className="block rounded-3xl overflow-hidden border border-brand-card-border bg-brand-card hover:border-brand-red/30 transition-all duration-300 shadow-xl hover:shadow-2xl"
              >
                <div className="relative aspect-[16/9] overflow-hidden">
                  <Image
                    src="/images/our-services-commercial.png"
                    alt="Commercial boiler plant — PPM, plant room maintenance, and facilities management"
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-700"
                    sizes="(max-width: 1024px) 100vw, 50vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                    <div className="flex items-center gap-3 mb-2">
                      <Building2 size={20} className="text-brand-red" />
                      <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                        Commercial
                      </span>
                    </div>
                    <h3 className="text-xl md:text-2xl font-technical font-extrabold text-white tracking-tight uppercase">
                      Commercial Boiler &amp; Plant
                    </h3>
                    <p className="text-white/80 text-[10px] md:text-xs font-technical uppercase tracking-wider mt-1">
                      PPM contracts, plant room maintenance, 24-hour emergency support.
                    </p>
                  </div>
                </div>
                <div className="p-4 md:p-5 border-t border-brand-card-border">
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-technical font-bold uppercase tracking-widest text-brand-muted">
                    {COMMERCIAL_SERVICES.slice(0, 4).map((s) => (
                      <span key={s.label}>{s.label}</span>
                    ))}
                  </div>
                  <span className="inline-flex items-center gap-2 mt-3 text-brand-red text-xs font-technical font-bold uppercase tracking-widest group-hover:gap-3 transition-all">
                    View commercial services <ArrowRight size={14} />
                  </span>
                </div>
              </Link>
            </motion.div>

            {/* Domestic section */}
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="group"
            >
              <Link
                href="/services/domestic"
                className="block rounded-3xl overflow-hidden border border-brand-card-border bg-brand-card hover:border-brand-red/30 transition-all duration-300 shadow-xl hover:shadow-2xl"
              >
                <div className="relative aspect-[16/9] overflow-hidden">
                  <Image
                    src="/images/our-services-domestic.png"
                    alt="Domestic combi boiler — heating and hot water for your home"
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-700"
                    sizes="(max-width: 1024px) 100vw, 50vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                    <div className="flex items-center gap-3 mb-2">
                      <Home size={20} className="text-brand-red" />
                      <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                        Domestic
                      </span>
                    </div>
                    <h3 className="text-xl md:text-2xl font-technical font-extrabold text-white tracking-tight uppercase">
                      Domestic Heating &amp; Hot Water
                    </h3>
                    <p className="text-white/80 text-[10px] md:text-xs font-technical uppercase tracking-wider mt-1">
                      Boiler installation, servicing, CP12, plumbing, and emergency callouts.
                    </p>
                  </div>
                </div>
                <div className="p-4 md:p-5 border-t border-brand-card-border">
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-technical font-bold uppercase tracking-widest text-brand-muted">
                    {DOMESTIC_SERVICES.map((s) => (
                      <span key={s.label}>{s.label}</span>
                    ))}
                  </div>
                  <span className="inline-flex items-center gap-2 mt-3 text-brand-red text-xs font-technical font-bold uppercase tracking-widest group-hover:gap-3 transition-all">
                    View domestic services <ArrowRight size={14} />
                  </span>
                </div>
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Our Core Services — same scroll-sequence style as How We Work */}
      <CoreServicesSection
        title="Our Core Services"
        subtitle="Mechanical, electrical, and gas solutions — installation, maintenance, and compliance across commercial and domestic projects."
        dark
        frameDir="/images/how-we-work-frames/frame"
        frameCount={145}
      />

      {/* Sectors We Deal With */}
      <section className="py-24 md:py-32 bg-brand-surface relative overflow-hidden" aria-label="Sectors we work with">
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12 md:mb-16"
          >
            <span className="text-brand-red text-sm font-bold uppercase tracking-[0.4em] mb-4 block">
              Industries We Serve
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Sectors We <span className="text-brand-red">Deal With</span>
            </h2>
            <p className="text-brand-muted mt-6 max-w-2xl mx-auto text-sm font-light leading-relaxed uppercase tracking-wider">
              Heating, plumbing, and gas services tailored to the specific needs of your sector — from offices and retail to healthcare and facilities management.
            </p>
          </motion.div>

          {/* Grid of sector images */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 md:gap-6 mb-12 md:mb-16"
          >
            {SECTORS_WITH_IMAGES.map((sector, i) => (
              <motion.div
                key={sector.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
                className="group group/card relative aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border bg-brand-steel shadow-xl hover:shadow-2xl hover:border-brand-red/30 transition-all duration-300"
              >
                <Image
                  src={sector.image ?? "/images/our-services-commercial.png"}
                  alt={sector.label}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1280px) 33vw, 20vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                  <span className="text-white text-sm md:text-base font-technical font-bold uppercase tracking-widest drop-shadow-sm">
                    {sector.label}
                  </span>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Remaining sectors as pills (add images later) */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="flex flex-wrap justify-center gap-3 md:gap-4"
          >
            {SECTORS_WE_DEAL_WITH.filter(
              (s) => !SECTORS_WITH_IMAGES.some((img) => img.label === s)
            ).map((sector, i) => (
              <motion.div
                key={sector}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.04, duration: 0.4 }}
                className="group flex items-center gap-2 px-5 py-3 rounded-2xl border border-brand-card-border bg-brand-steel/80 hover:border-brand-red/30 hover:bg-brand-red/5 transition-all duration-300"
              >
                <Briefcase size={14} className="text-brand-red shrink-0 opacity-80 group-hover:opacity-100" />
                <span className="text-[10px] font-technical font-bold uppercase tracking-widest text-brand-text group-hover:text-brand-red/90 transition-colors">
                  {sector}
                </span>
              </motion.div>
            ))}
          </motion.div>
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
              London, Kent, Essex and Surrey. Click any pin to find out more.
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

      {/* Mission & Vision — compact */}
      <section className="py-16 md:py-24 bg-brand-surface relative overflow-hidden" aria-label="Our mission and vision">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-10"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
              What Drives Us
            </span>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="p-6 md:p-8 rounded-2xl border border-brand-card-border bg-brand-steel/80 backdrop-blur-sm hover:border-brand-red/20 transition-colors"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-brand-red/10 border border-brand-red/20 flex items-center justify-center">
                  <Target size={18} className="text-brand-red" />
                </div>
                <h3 className="text-lg font-technical font-extrabold text-brand-text uppercase tracking-widest">
                  Our Mission
                </h3>
              </div>
              <p className="text-brand-muted text-sm font-light leading-relaxed uppercase tracking-wider">
                {COMPANY.mission}
              </p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="p-6 md:p-8 rounded-2xl border border-brand-card-border bg-brand-steel/80 backdrop-blur-sm hover:border-brand-red/20 transition-colors"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-brand-red/10 border border-brand-red/20 flex items-center justify-center">
                  <Eye size={18} className="text-brand-red" />
                </div>
                <h3 className="text-lg font-technical font-extrabold text-brand-text uppercase tracking-widest">
                  Our Vision
                </h3>
              </div>
              <p className="text-brand-muted text-sm font-light leading-relaxed uppercase tracking-wider">
                {COMPANY.vision}
              </p>
            </motion.div>
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
                Founded in {COMPANY.founded} by {COMPANY.founder}, {COMPANY.name} delivers expert mechanical, electrical, and gas services across domestic and commercial sectors. With {COMPANY.industryExperience} of industry experience, we are committed to exceptional workmanship, strict Health &amp; Safety standards, and a responsive 24/7 service built on discipline, integrity, and reliability. All our engineers are Gas Safe registered and fully insured.
              </p>
              <div className="space-y-5">
                {[
                  { label: "Gas Safe registered on every job" },
                  { label: "24/7 responsive service capability" },
                  { label: "Upfront, transparent pricing" },
                  { label: "Rigorous Health & Safety and compliance" },
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

      {/* Proud sponsor — Next Level FC + accreditations */}
      <section className="relative z-10 py-16 md:py-20 bg-brand-navy border-y border-brand-card-border" aria-label="Community sponsorship and accreditations">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
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
              Professional Heating &amp; Plumbing Services
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

      {/* Final CTA */}
      <CTABanner
        title="Ready to Book?"
        subtitle={`Get in touch today for a free, no-obligation quote. Our engineers are ready to help.`}
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
