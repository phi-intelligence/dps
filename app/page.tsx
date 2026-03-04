"use client";

import { useEffect, useState } from "react";
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
  ShieldCheck,
  BadgeCheck,
  MessageSquare,
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

  const [flippedValueCard, setFlippedValueCard] = useState<string | null>(null);

  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-hidden relative">
      {/* Hero + quick meta strip — dark theme */}
      <section
        className="relative min-h-[70vh] md:min-h-[80vh] lg:min-h-[90vh] pt-24 md:pt-28 pb-14 md:pb-16 overflow-visible md:overflow-hidden bg-[#05080c]"
        aria-label="Hero"
      >
        <div className="absolute inset-0">
          <Image
            src="/images/blueprint-boiler-cutaway.png"
            alt=""
            fill
            className="opacity-60 object-cover object-center"
            priority
            aria-hidden
          />
          <div className="absolute inset-0 bg-[#05080c]/85" />
          <div className="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-[#05080c] to-transparent" />
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -top-40 -right-40 h-[32rem] w-[32rem] rotate-3 border border-white/10 rounded-[3rem]" />
            <div className="absolute -bottom-40 -left-40 h-[26rem] w-[26rem] -rotate-6 border border-[#e2c977]/20 rounded-[3rem]" />
            <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/25 to-transparent" />
          </div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1.6fr] gap-10 lg:gap-16 items-start lg:items-center">
            {/* Left column – copy and CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="flex flex-col justify-between"
            >
              <div>
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="inline-flex items-center gap-3 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 backdrop-blur"
                >
                  <div className="h-1.5 w-1.5 rounded-sm bg-[#e2c977] animate-pulse" />
                  <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-white/90">
                    Design • Engineer • Maintain // {COMPANY.areas}
                  </span>
                </motion.div>

                <div className="mt-6 md:mt-8 space-y-3 md:space-y-4">
                  <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-[3.7rem] font-technical font-extrabold tracking-[0.22em] md:tracking-[0.24em] leading-[1.15] uppercase text-white">
                    Precision{" "}
                    <span className="inline-block text-[#e2c977]">
                      Heating
                    </span>{" "}
                    &amp; Plumbing
                  </h1>
                  <p className="max-w-md text-sm md:text-base text-[#b3c0d0] font-medium leading-relaxed">
                    Engineered heating and plumbing for commercial plant rooms and homes across {COMPANY.areas}.
                  </p>
                </div>

                <div className="mt-8 md:mt-10 flex flex-col sm:flex-row gap-4 sm:gap-5">
                  <button
                    type="button"
                    onClick={() => openQuoteModal()}
                    className="group relative inline-flex items-center justify-center gap-2 rounded-full bg-[#e2c977] px-8 py-4 text-sm font-technical font-bold uppercase tracking-[0.25em] text-[#0a0f14] shadow-[0_20px_40px_rgba(0,0,0,0.3)] transition-transform hover:-translate-y-0.5 hover:bg-[#e8d07a]"
                  >
                    <span className="relative z-10">Book A Consultation</span>
                    <ArrowRight
                      size={18}
                      className="relative z-10 transition-transform group-hover:translate-x-1"
                    />
                  </button>

                  <a
                    href="tel:+442071234567"
                    className="inline-flex items-center justify-center gap-2 rounded-full border border-white/20 bg-white/5 px-8 py-4 text-xs font-technical font-bold uppercase tracking-[0.3em] text-white/90 backdrop-blur transition-all hover:bg-white/10 hover:border-[#e2c977]/40"
                  >
                    <Phone size={16} className="text-[#e2c977]" />
                    020&nbsp;7123&nbsp;4567
                  </a>

                  <Link
                    href="/services"
                    className="inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-6 py-4 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-white/80 hover:bg-white/10 hover:text-white"
                  >
                    <ChevronDown size={14} />
                    View services
                  </Link>
                </div>
              </div>

            </motion.div>

            {/* Right column – geometric logo composition */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.9 }}
              className="relative mt-8 lg:mt-0"
            >
              <div className="relative h-auto lg:h-full min-h-[220px] sm:min-h-[240px] md:min-h-[320px] lg:min-h-[420px]">
                <div className="absolute inset-0 rounded-[1.8rem] sm:rounded-[2.2rem] lg:rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-[#10141a] via-[#151b21] to-[#04060a] shadow-[0_24px_60px_rgba(0,0,0,0.6)]" />
                <div className="absolute inset-2 sm:inset-4 lg:inset-[1.4rem] rounded-[1.5rem] sm:rounded-[2rem] border border-[#2f3841] bg-gradient-to-br from-[#0f151b] via-[#151c24] to-[#04060a]" />

                <div className="absolute inset-2 sm:inset-4 lg:inset-[1.4rem] overflow-hidden rounded-[1.5rem] sm:rounded-[2rem]">
                  <div className="absolute -left-20 top-10 h-[120%] w-[70%] -skew-x-6 bg-gradient-to-b from-[#b8963a]/15 via-[#e2c977]/4 to-transparent" />
                  <div className="absolute right-3 top-0 h-full w-[45%] bg-gradient-to-b from-white/6 via-transparent to-[#b8963a]/10" />

                  <div className="absolute inset-4 sm:inset-6 lg:inset-8 grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
                    <div className="flex flex-col justify-between">
                      <div className="rounded-3xl border border-white/10 bg-white/5 px-4 py-3">
                        <span className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#9aa3b0]">
                          Commercial &amp; Domestic
                        </span>
                        <p className="mt-2 text-xs text-[#c7ced7]">
                          Boiler plant, hot water, mechanical and plumbing
                          delivered as engineered systems.
                        </p>
                      </div>
                      <div className="rounded-3xl border border-white/8 bg-[#05080b]/70 px-4 py-3 mt-4">
                        <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#e2c977]">
                          Areas Covered
                        </span>
                        <p className="mt-2 text-[11px] text-[#c7ced7]">
                          {COMPANY.areas}
                        </p>
                      </div>
                    </div>
                    <div className="relative flex items-center justify-center">
                      <div className="relative h-28 w-28 sm:h-36 sm:w-36 md:h-56 md:w-56">
                        <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-[#e2c977]/40 via-transparent to-transparent blur-2xl" />
                        <div className="absolute inset-0 rounded-[2rem] border border-[#e2c977]/60 bg-[#050608]/70 backdrop-blur">
                          <Image
                            src="/images/logo.png"
                            alt={COMPANY.name}
                            fill
                            className="object-contain p-6 drop-shadow-[0_0_40px_rgba(226,201,119,0.55)]"
                            sizes="(max-width: 640px) 256px, (max-width: 768px) 320px, (max-width: 1024px) 352px, 384px"
                            priority
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Operational snapshot – card-based highlights */}
      <section className="relative bg-[#f7f3ea] py-16 md:py-24 overflow-hidden">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-24 top-1/4 h-48 w-72 rotate-6 rounded-[2.5rem] border border-[#e2c977]/25 bg-[#e2c977]/5" />
          <div className="absolute -left-20 bottom-1/4 h-40 w-64 -rotate-6 rounded-[2.5rem] border border-[#d4af37]/20 bg-[#e2c977]/5" />
          <div className="absolute right-1/4 top-0 h-32 w-32 rotate-12 rounded-2xl border border-[#e0d3b8]/30" />
          <div className="absolute left-1/3 bottom-0 h-24 w-40 -rotate-6 rounded-[1.5rem] border border-[#e2c977]/15" />
          <div className="absolute inset-x-8 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/20 to-transparent" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Descriptive guarantees without cards */}
          <div className="max-w-5xl mx-auto grid gap-6 md:grid-cols-2">
            <div className="relative pl-5 md:pl-6">
              <div className="absolute left-0 top-1 h-8 w-px bg-gradient-to-b from-[#e2c977] via-[#f5e9c6] to-transparent" />
              <div className="flex items-center gap-2">
                <Shield size={18} className="text-[#b8963a]" />
                <span className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#555b60]">
                  Gas Safe Registered
                </span>
              </div>
              <p className="mt-2 text-xs md:text-sm text-[#22272c]">
                Certificate-backed compliance on every live connection.
              </p>
            </div>
            <div className="relative pl-5 md:pl-6">
              <div className="absolute left-0 top-1 h-8 w-px bg-gradient-to-b from-[#e2c977] via-[#f5e9c6] to-transparent" />
              <div className="flex items-center gap-2">
                <Clock size={18} className="text-[#b8963a]" />
                <span className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#555b60]">
                  24/7 Capability
                </span>
              </div>
              <p className="mt-2 text-xs md:text-sm text-[#22272c]">
                Planned maintenance and emergency response when it matters.
              </p>
            </div>
          </div>

          {/* Trust highlights as individual cards */}
          <div className="max-w-5xl mx-auto mt-10 md:mt-14 grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.05 }}
              className="rounded-2xl border border-white/80 bg-white/90 px-4 py-6 shadow-[0_18px_50px_rgba(0,0,0,0.06)] hover:shadow-[0_22px_56px_rgba(0,0,0,0.08)] transition-shadow duration-300 flex flex-col items-center justify-center gap-3 min-h-[120px] md:min-h-[140px]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[#e0d3b8] bg-white/70">
                <ShieldCheck size={20} className="text-[#b8963a]" />
              </div>
              <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.3em] text-[#2b3136] text-center">
                Gas Safe
              </span>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="rounded-2xl border border-white/80 bg-white/90 px-4 py-6 shadow-[0_18px_50px_rgba(0,0,0,0.06)] hover:shadow-[0_22px_56px_rgba(0,0,0,0.08)] transition-shadow duration-300 flex flex-col items-center justify-center gap-3 min-h-[120px] md:min-h-[140px]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[#e0d3b8] bg-white/70">
                <BadgeCheck size={20} className="text-[#b8963a]" />
              </div>
              <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.3em] text-[#2b3136] text-center">
                Fully Insured
              </span>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.15 }}
              className="rounded-2xl border border-white/80 bg-white/90 px-4 py-6 shadow-[0_18px_50px_rgba(0,0,0,0.06)] hover:shadow-[0_22px_56px_rgba(0,0,0,0.08)] transition-shadow duration-300 flex flex-col items-center justify-center gap-3 min-h-[120px] md:min-h-[140px]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[#e0d3b8] bg-white/70">
                <MessageSquare size={20} className="text-[#b8963a]" />
              </div>
              <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.3em] text-[#2b3136] text-center">
                Free Quotes
              </span>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="rounded-2xl border border-white/80 bg-white/90 px-4 py-6 shadow-[0_18px_50px_rgba(0,0,0,0.06)] hover:shadow-[0_22px_56px_rgba(0,0,0,0.08)] transition-shadow duration-300 flex flex-col items-center justify-center gap-3 min-h-[120px] md:min-h-[140px]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[#e0d3b8] bg-white/70">
                <Clock size={20} className="text-[#b8963a]" />
              </div>
              <span className="text-[10px] md:text-xs font-technical font-bold uppercase tracking-[0.3em] text-[#2b3136] text-center">
                Same-Day Service
              </span>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tri-panel value proposition – dark themed */}
      <section className="relative bg-[#05080c] py-24 md:py-32 overflow-hidden">
        <div className="absolute inset-x-0 -top-10 h-10 bg-gradient-to-b from-[#f2ede3] to-transparent opacity-70" />
        {/* Geometric background accents */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-10 h-64 w-64 rotate-6 border border-white/6 rounded-[3rem]" />
          <div className="absolute -left-32 bottom-0 h-52 w-80 -rotate-6 border border-[#e2c977]/20 rounded-[3rem]" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid gap-8 md:grid-cols-[minmax(0,1.2fr)_minmax(0,1.6fr)] items-start">
            <div className="space-y-4">
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                Why Clients Choose {COMPANY.name}
              </span>
              <h2 className="mt-4 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                Engineered Reliability. Luxury Finish.
              </h2>
              <p className="max-w-md text-xs text-[#9aa3b0]">
                From commercial boiler plant rooms to domestic homes, we combine
                disciplined engineering with precise, clean installs and
                transparent communication.
              </p>
            </div>
            <div className="grid gap-5 md:grid-cols-3">
              {/* Commercial Systems card */}
              <motion.div
                initial={{ opacity: 0, y: 12, x: 0 }}
                whileInView={{ opacity: 1, y: 0, x: [0, -3, 3, -2, 2, 0] }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.7, delay: 0.1 }}
                className="relative group h-52 sm:h-56 md:h-64 [perspective:1200px]"
                onClick={() =>
                  setFlippedValueCard(
                    flippedValueCard === "commercial" ? null : "commercial"
                  )
                }
              >
                <div
                  className={`absolute inset-0 rounded-3xl border border-white/12 bg-[#0f151c] px-5 py-6 text-[#d6e0ec] [transform-style:preserve-3d] transition-transform duration-500 group-hover:[transform:rotateY(180deg)] ${
                    flippedValueCard === "commercial"
                      ? "[transform:rotateY(180deg)]"
                      : ""
                  }`}
                >
                  {/* Front face */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 [backface-visibility:hidden]">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#e2c977]/70 bg-[#10161f]">
                      <Building2 size={26} className="text-[#e2c977]" />
                    </div>
                    <span className="text-[10px] font-technical font-extrabold uppercase tracking-[0.35em] text-[#e2c977] text-center">
                      Commercial Systems
                    </span>
                  </div>
                  {/* Back face */}
                  <div className="absolute inset-0 flex flex-col justify-center gap-3 px-5 py-5 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                    <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#e2c977]">
                      Commercial Systems
                    </span>
                    <p className="text-sm text-[#c7ced7]">
                      Plant rooms, packaged boiler solutions and PPM contracts
                      for offices, retail, and facilities management.
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Domestic Excellence card */}
              <motion.div
                initial={{ opacity: 0, y: 12, x: 0 }}
                whileInView={{ opacity: 1, y: 0, x: [0, -3, 3, -2, 2, 0] }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.7, delay: 0.16 }}
                className="relative group h-52 sm:h-56 md:h-64 [perspective:1200px]"
                onClick={() =>
                  setFlippedValueCard(
                    flippedValueCard === "domestic" ? null : "domestic"
                  )
                }
              >
                <div
                  className={`absolute inset-0 rounded-3xl border border-white/12 bg-[#0f151c] px-5 py-6 text-[#d6e0ec] [transform-style:preserve-3d] transition-transform duration-500 group-hover:[transform:rotateY(180deg)] ${
                    flippedValueCard === "domestic"
                      ? "[transform:rotateY(180deg)]"
                      : ""
                  }`}
                >
                  {/* Front face */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 [backface-visibility:hidden]">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#e2c977]/70 bg-[#10161f]">
                      <Home size={26} className="text-[#e2c977]" />
                    </div>
                    <span className="text-[10px] font-technical font-extrabold uppercase tracking-[0.35em] text-[#e2c977] text-center">
                      Domestic Excellence
                    </span>
                  </div>
                  {/* Back face */}
                  <div className="absolute inset-0 flex flex-col justify-center gap-3 px-5 py-5 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                    <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#e2c977]">
                      Domestic Excellence
                    </span>
                    <p className="text-sm text-[#c7ced7]">
                      Clean boilers, fault finding, CP12, and emergency response
                      with respect for your home.
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* End-to-End Care card */}
              <motion.div
                initial={{ opacity: 0, y: 12, x: 0 }}
                whileInView={{ opacity: 1, y: 0, x: [0, -3, 3, -2, 2, 0] }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.7, delay: 0.22 }}
                className="relative group h-52 sm:h-56 md:h-64 [perspective:1200px]"
                onClick={() =>
                  setFlippedValueCard(
                    flippedValueCard === "endtoend" ? null : "endtoend"
                  )
                }
              >
                <div
                  className={`absolute inset-0 rounded-3xl border border-white/18 bg-[#11161d] px-5 py-6 text-[#e4edf7] [transform-style:preserve-3d] transition-transform duration-500 group-hover:[transform:rotateY(180deg)] ${
                    flippedValueCard === "endtoend"
                      ? "[transform:rotateY(180deg)]"
                      : ""
                  }`}
                >
                  {/* Front face */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 [backface-visibility:hidden]">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/40 bg-white/5">
                      <Zap size={26} className="text-[#e2c977]" />
                    </div>
                    <span className="text-[10px] font-technical font-extrabold uppercase tracking-[0.35em] text-[#e2c977] text-center">
                      End-to-End Care
                    </span>
                  </div>
                  {/* Back face */}
                  <div className="absolute inset-0 flex flex-col justify-center gap-3 px-5 py-5 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                    <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#e2c977]">
                      End-to-End Care
                    </span>
                    <p className="text-sm text-[#c7d0dd]">
                      Design, install, commission and maintain — one point of
                      accountability across the entire lifecycle.
                    </p>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Services matrix – semi-minimal cards within an island */}
      <section
        className="relative bg-[#f2ede3] py-20 md:py-24 overflow-hidden"
        aria-label="Core services overview"
      >
        {/* Geometric background instead of waves */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-6 h-52 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/30 bg-[#e2c977]/12" />
          <div className="absolute -left-40 bottom-0 h-56 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/24 bg-[#d4af37]/8" />
          <div className="absolute right-1/4 top-1/3 h-28 w-40 rotate-12 rounded-3xl border border-[#e0d3b8]/40" />
          <div className="absolute left-1/3 bottom-4 h-24 w-44 -rotate-6 rounded-[2rem] border border-[#e2c977]/25" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/22 to-transparent" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 overflow-visible">
          {/* Island header */}
          <div className="relative rounded-[2.5rem] bg-white/95 px-5 sm:px-8 md:px-10 py-10 md:py-12 shadow-[0_24px_70px_rgba(0,0,0,0.08)] border border-[#e0d3b8]">
            <div className="pointer-events-none absolute -right-32 -top-16 h-40 w-64 rotate-6 bg-gradient-to-br from-[#e2c977]/24 via-transparent to-transparent rounded-[3rem]" />
            <div className="pointer-events-none absolute -left-32 -bottom-20 h-40 w-72 -rotate-6 bg-gradient-to-tr from-[#10141a]/10 via-transparent to-transparent rounded-[3rem]" />

            <div className="relative flex flex-col items-center text-center gap-3 mb-8">
              <span className="text-xs md:text-sm font-technical font-bold uppercase tracking-[0.45em] text-[#b8963a]">
                Services
              </span>
              <h2 className="text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.26em] text-[#171b1f]">
                Mechanical, Electrical &amp; Gas
              </h2>
              <p className="max-w-xl text-sm text-[#3c444b]">
                Three clear paths into how we work with commercial estates and
                domestic homeowners.
              </p>
            </div>
          </div>

          {/* Cards overlapping the island */}
          <div className="relative -mt-6 md:-mt-8 px-1 sm:px-2 lg:px-4">
            <div className="grid gap-6 lg:grid-cols-3 items-stretch">
              {/* Commercial card */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4 }}
                className="relative overflow-hidden rounded-[1.8rem] border border-[#2d3a46] bg-gradient-to-br from-[#05070b] via-[#0f151c] to-[#020508] px-5 py-6 text-[#d6e0ec] shadow-[0_18px_50px_rgba(0,0,0,0.28)] hover:-translate-y-1 transition-transform duration-300"
              >
                <div className="pointer-events-none absolute -right-14 -top-10 h-24 w-32 rotate-6 bg-gradient-to-br from-[#e2c977]/35 via-transparent to-transparent" />
                <div className="relative flex flex-col gap-4 h-full justify-between">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                        Commercial
                      </span>
                      <h3 className="mt-2 text-base font-technical font-extrabold uppercase tracking-[0.22em] text-white">
                        Boiler Plant &amp; HVAC
                      </h3>
                      <p className="mt-2 text-xs text-[#b3c0d0] line-clamp-3">
                        Designed plant rooms, packaged boiler systems, and
                        facilities maintenance with clear reporting.
                      </p>
                    </div>
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#e2c977]/70 bg-white/5">
                      <Building2 size={18} className="text-[#b8963a]" />
                    </div>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5 text-[9px] font-technical uppercase tracking-[0.28em] text-[#e2c977] max-h-[48px] overflow-hidden">
                    {COMMERCIAL_SERVICES.map((s) => (
                      <span
                        key={s.label}
                        className="rounded-full border border-white/20 bg-white/5 px-2.5 py-1"
                      >
                        {s.label}
                      </span>
                    ))}
                  </div>
                  <Link
                    href="/services/commercial"
                    className="mt-3 inline-flex items-center justify-center gap-2 text-[9px] font-technical font-bold uppercase tracking-[0.3em] text-[#e2c977]"
                  >
                    View commercial services
                    <ArrowRight size={12} />
                  </Link>
                </div>
              </motion.div>

              {/* Domestic card */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.06 }}
                className="relative overflow-hidden rounded-[1.8rem] border border-[#2d3a46] bg-gradient-to-br from-[#05070b] via-[#0f151c] to-[#020508] px-5 py-6 text-[#d6e0ec] shadow-[0_18px_50px_rgba(0,0,0,0.28)] hover:-translate-y-1 transition-transform duration-300"
              >
                <div className="pointer-events-none absolute -left-14 top-0 h-24 w-32 -rotate-6 bg-gradient-to-br from-[#e2c977]/35 via-transparent to-transparent" />
                <div className="relative flex flex-col gap-4 h-full justify-between">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                        Domestic
                      </span>
                      <h3 className="mt-2 text-base font-technical font-extrabold uppercase tracking-[0.22em] text-white">
                        Home Heating &amp; Hot Water
                      </h3>
                      <p className="mt-2 text-xs text-[#b3c0d0] line-clamp-3">
                        Boiler upgrades, servicing, safety certificates and
                        plumbing repairs delivered with minimal disruption.
                      </p>
                    </div>
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#e2c977]/70 bg-white/5">
                      <Home size={18} className="text-[#b8963a]" />
                    </div>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5 text-[9px] font-technical uppercase tracking-[0.28em] text-[#e2c977] max-h-[48px] overflow-hidden">
                    {DOMESTIC_SERVICES.map((s) => (
                      <span
                        key={s.label}
                        className="rounded-full border border-white/20 bg-white/5 px-2.5 py-1"
                      >
                        {s.label}
                      </span>
                    ))}
                  </div>
                  <Link
                    href="/services/domestic"
                    className="mt-3 inline-flex items-center justify-center gap-2 text-[9px] font-technical font-bold uppercase tracking-[0.3em] text-[#e2c977]"
                  >
                    View domestic services
                    <ArrowRight size={12} />
                  </Link>
                </div>
              </motion.div>

              {/* Project delivery card */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.12 }}
                className="relative overflow-hidden rounded-[1.8rem] border border-[#2d3a46] bg-gradient-to-br from-[#05070b] via-[#0f151c] to-[#020508] px-5 py-6 text-[#d6e0ec] shadow-[0_16px_40px_rgba(0,0,0,0.12)] hover:-translate-y-1 transition-transform duration-300"
              >
                <div className="pointer-events-none absolute -right-16 bottom-0 h-24 w-32 rotate-6 border border-white/10 opacity-40" />
                <div className="relative flex flex-col gap-4 h-full justify-between">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                        Project Delivery
                      </span>
                      <h3 className="mt-2 text-base font-technical font-extrabold uppercase tracking-[0.22em] text-white">
                        Design • Install • Maintain
                      </h3>
                      <p className="mt-2 text-xs text-[#b3c0d0] line-clamp-3">
                        Mechanical, electrical and gas projects delivered as
                        complete packages with a single, disciplined team.
                      </p>
                    </div>
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-white/5">
                      <Target size={18} className="text-[#e2c977]" />
                    </div>
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-2 text-[9px] font-technical uppercase tracking-[0.28em]">
                    <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[#e2c977]">
                      Mechanical
                    </span>
                    <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[#e2c977]">
                      Gas
                    </span>
                    <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[#e2c977]">
                      Plumbing
                    </span>
                    <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[#e2c977]">
                      Electrical
                    </span>
                  </div>
                  <Link
                    href="/services"
                    className="mt-3 inline-flex items-center justify-center gap-2 text-[9px] font-technical font-bold uppercase tracking-[0.3em] text-white"
                  >
                    Explore all services
                    <ArrowRight size={12} />
                  </Link>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Core services scroll sequence in framed dark band */}
      <section className="relative bg-[#0b1015] py-24 md:py-28">
        <div className="absolute inset-0 bg-gradient-to-b from-[#05070b] via-[#05070b] to-[#080c10]" />
        {/* <div className="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-[#f2ede3] to-transparent opacity-80" /> */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                How We Work
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                Engineered From First Sketch
              </h2>
            </div>
            <p className="max-w-md text-xs text-[#9aa3b0]">
              Visualise the full journey from design to commissioning with our
              scroll-sequenced overview.
            </p>
          </div>

          <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#05080c] via-[#05080c] to-[#0c141f] shadow-[0_30px_80px_rgba(0,0,0,0.6)]">
            <CoreServicesSection
              title="Our Core Services"
              subtitle="Mechanical, electrical, and gas solutions — installation, maintenance, and compliance across commercial and domestic projects."
              dark
              frameDir="/images/how-we-work-frames/frame"
              frameCount={145}
            />
          </div>
        </div>
      </section>

      {/* Sectors we serve – geometric grid */}
      <section
        className="relative bg-[#f7f3ea] py-20 md:py-24"
        aria-label="Sectors we work with"
      >
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#b8963a]">
                Industries
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-[#171b1f]">
                Sectors We Partner With
              </h2>
            </div>
                  <p className="max-w-md text-sm text-[#3c444b]">
              Tailored solutions for estates, facilities and asset owners across
              London, Kent, Essex and Surrey.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-8">
            {SECTORS_WITH_IMAGES.slice(0, 6).map((sector, i) => (
              <motion.div
                key={sector.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                className="group relative overflow-hidden rounded-3xl border border-[#e0d3b8] bg-white shadow-[0_16px_40px_rgba(0,0,0,0.04)]"
              >
                <div className="relative aspect-[4/3] overflow-hidden">
                  <Image
                    src={sector.image ?? "/images/our-services-commercial.png"}
                    alt={sector.label}
                    fill
                    className="object-cover transition-transform duration-500 group-hover:scale-105"
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                </div>
                <div className="relative flex items-center justify-between px-5 py-4">
                  <span className="inline-flex items-center rounded-full bg-black/55 px-3 py-1 text-sm font-technical font-bold uppercase tracking-[0.25em] text-[#e2c977] backdrop-blur-sm">
                    {sector.label}
                  </span>
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/30 bg-black/45 text-white">
                    <Briefcase size={16} />
                  </span>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="flex flex-wrap gap-3 border-t border-[#e0d3b8] pt-6">
            {SECTORS_WE_DEAL_WITH.filter(
              (s) => !SECTORS_WITH_IMAGES.some((img) => img.label === s)
            ).map((sector) => (
              <div
                key={sector}
                className="flex items-center gap-2 rounded-2xl border border-[#e0d3b8] bg-white px-4 py-2 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#4e555c]"
              >
                <div className="h-1 w-5 bg-gradient-to-r from-[#e2c977] via-[#f5e9c6] to-transparent" />
                {sector}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service areas map – light card with darker side panel */}
      <section
        className="relative bg-[#f2ede3] py-20 md:py-24"
        aria-label="Service areas map"
      >
        <SectionWaves variant="cool" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#b8963a]">
                Coverage
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-[#171b1f]">
                Where We Operate
              </h2>
            </div>
            <p className="max-w-md text-xs text-[#5b6167]">
              Strategic coverage across London and the South East with
              engineered response times and clear communication.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.8fr_1.1fr] items-start">
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="relative h-[420px] overflow-hidden rounded-[2rem] border border-[#d5c7aa] bg-white shadow-[0_24px_60px_rgba(0,0,0,0.15)]"
            >
              <ServiceAreasMap />
              <div className="pointer-events-none absolute inset-0 rounded-[2rem] ring-1 ring-inset ring-black/5" />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="relative overflow-hidden rounded-[1.75rem] border border-[#1e252e] bg-[#0c1219] px-6 py-6 text-[#c7d0dd]"
            >
              <div className="absolute -right-12 top-0 h-32 w-32 rotate-12 border border-white/10" />
              <div className="relative">
                <h3 className="flex items-center gap-2 text-xs font-technical font-bold uppercase tracking-[0.35em] text-[#e2c977]">
                  <MapPin size={14} />
                  Areas Covered
                </h3>
                <p className="mt-3 text-xs text-[#a5b1c1]">
                  We cover key commercial and residential zones across the South
                  East. If you sit just outside the map, call us — we&apos;ll
                  advise honestly.
                </p>
                <div className="mt-5 grid grid-cols-2 gap-2">
                  {SERVICE_AREAS.map((area) => (
                    <div
                      key={area}
                      className="flex items-center gap-2 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#bcc6d4]"
                    >
                      <span className="h-1 w-4 bg-gradient-to-r from-[#e2c977] via-[#f5e9c6] to-transparent" />
                      {area}
                    </div>
                  ))}
                </div>
                <div className="mt-6 border-t border-white/10 pt-4">
                  <p className="text-[10px] font-technical uppercase tracking-[0.3em] text-[#939fb0]">
                    Not sure we cover your area?
                  </p>
                  <Link
                    href="/service-areas"
                    className="mt-3 inline-flex items-center gap-2 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-white"
                  >
                    <ArrowRight size={14} />
                    View all service areas
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Mission & vision section */}
      <section
        className="relative bg-[#0b1015] py-20 md:py-24"
        aria-label="Our mission and vision"
      >
        {/* Geometric background instead of waves */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-10 h-56 w-72 rotate-6 border border-white/6 rounded-[3rem]" />
          <div className="absolute -left-32 bottom-0 h-52 w-80 -rotate-6 border border-[#e2c977]/20 rounded-[3rem]" />
          {/* <div className="absolute inset-x-8 top-1/2 h-px bg-gradient-to-r from-transparent via-white/12 to-transparent" /> */}
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-5xl mx-auto"
          >
            <div className="mb-10 space-y-4">
              <span className="text-[11px] md:text-xs font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977]">
                What Drives Us
              </span>
              <p className="text-sm md:text-base text-[#98a4b4] max-w-3xl leading-relaxed">
                Every project is treated as a piece of engineered infrastructure,
                not just a job. That mindset shapes how we design, specify and
                maintain systems.
              </p>
              <div className="h-px w-full bg-gradient-to-r from-transparent via-white/15 to-transparent" />
            </div>

            <div className="grid gap-8 md:grid-cols-2">
              <div className="relative pl-6 md:pl-8">
                <div className="absolute left-0 top-0 h-12 w-px bg-gradient-to-b from-[#e2c977] via-[#f5e9c6] to-transparent" />
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-[#e2c977]/40 bg-white/5">
                    <Target size={18} className="text-[#e2c977]" />
                  </div>
                  <h3 className="text-sm md:text-base font-technical font-extrabold uppercase tracking-[0.3em] text-white">
                    Our Mission
                  </h3>
                </div>
                <p className="text-sm md:text-base text-[#a5b1c1] leading-relaxed">
                  {COMPANY.mission}
                </p>
              </div>

              <div className="relative pl-6 md:pl-8">
                <div className="absolute left-0 top-0 h-12 w-px bg-gradient-to-b from-[#e2c977] via-[#f5e9c6] to-transparent" />
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-[#e2c977]/40 bg-white/5">
                    <Eye size={18} className="text-[#e2c977]" />
                  </div>
                  <h3 className="text-sm md:text-base font-technical font-extrabold uppercase tracking-[0.3em] text-white">
                    Our Vision
                  </h3>
                </div>
                <p className="text-sm md:text-base text-[#a5b1c1] leading-relaxed">
                  {COMPANY.vision}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* About DPS section */}
      <section
        className="relative bg-[#05080c] py-20 md:py-24"
        aria-label="About DPS Heating Services"
      >
        <div className="absolute inset-x-0 -top-10 h-10 bg-gradient-to-b from-[#0b1015] to-transparent opacity-70" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#05080c] via-[#05080c] to-[#0f151c] px-6 py-6 lg:px-8 lg:py-8"
          >
            <div className="pointer-events-none absolute -right-40 -top-20 h-40 w-72 rotate-6 border border-white/10 opacity-40 rounded-[3rem]" />
            <div className="pointer-events-none absolute -left-40 bottom-0 h-40 w-80 -rotate-6 border border-[#e2c977]/25 opacity-50 rounded-[3rem]" />

            <div className="relative grid gap-8 lg:grid-cols-[1.1fr_1.3fr] items-center">
              <div className="space-y-5">
                <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                  About {COMPANY.name}
                </span>
                <h2 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                  Disciplined Engineers. Clean Installs.
                </h2>
                <p className="text-xs text-[#a5b1c1]">
                  Founded in {COMPANY.founded} by {COMPANY.founder},{" "}
                  {COMPANY.name} brings {COMPANY.industryExperience} of
                  experience across domestic and commercial plant. We combine
                  tight workmanship, robust H&amp;S and transparent
                  communication.
                </p>
                <div className="space-y-3">
                  {[
                    "Gas Safe on every live connection",
                    "24/7 responsive capability for key clients",
                    "Transparent, line-item pricing",
                    "Health & Safety baked into every method statement",
                  ].map((item) => (
                    <div
                      key={item}
                      className="flex items-center gap-3 text-[10px] font-technical uppercase tracking-[0.3em] text-[#9aa3b0]"
                    >
                      <span className="h-[2px] w-6 bg-gradient-to-r from-[#e2c977] via-[#f5e9c6] to-transparent" />
                      {item}
                    </div>
                  ))}
                </div>
                <Link
                  href="/about"
                  className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-6 py-3 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-white hover:bg-white/10"
                >
                  <ArrowRight size={14} />
                  More about our approach
                </Link>
              </div>
              <div className="relative h-44 w-full md:h-56 lg:h-64">
                <div className="absolute -inset-3 rounded-[2rem] bg-gradient-to-br from-[#e2c977]/35 via-transparent to-transparent blur-2xl" />
                <div className="relative h-full w-full overflow-hidden rounded-[2rem] border border-white/20">
                  <Image
                    src="/images/plumbing-pipes.jpg"
                    alt="DPS engineer working on complex pipework"
                    fill
                    className="object-cover object-center"
                    sizes="(max-width: 1024px) 100vw, 50vw"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats + trust band */}
      <section className="relative bg-[#05080c] py-20 md:py-24">
        <SectionWaves variant="warm" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                Track Record
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                Numbers That Back The Work
              </h2>
            </div>
            <p className="max-w-md text-xs text-[#9aa3b0]">
              We don&apos;t talk about reliability — we model it, measure it and
              report it. Every contract is grounded in actual performance.
            </p>
          </div>

          <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#05080c] via-[#05080c] to-[#10161f] px-4 py-10 md:px-8 md:py-12">
            <div className="mb-10">
              <StatsCounter />
            </div>

            <div className="grid gap-8 md:grid-cols-4">
              {trustPoints.map((point, i) => (
                <motion.div
                  key={point.title}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08, duration: 0.4 }}
                  className="relative"
                >
                  <div className="relative flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#e2c977]/40 bg-[#141a23]">
                      <point.icon size={22} className="text-[#e2c977]" />
                    </div>
                    <h3 className="text-sm font-technical font-extrabold uppercase tracking-[0.26em] text-white">
                      {point.title}
                    </h3>
                    <p className="text-[11px] text-[#b3c0d0]">
                      {point.description}
                    </p>
                  </div>
                  <span className="pointer-events-none absolute -top-6 -left-2 text-5xl font-technical font-black text-white/3">
                    0{i + 1}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Sponsors & accreditations strip */}
      <section
        className="relative bg-[#05080c] py-16 border-y border-white/5"
        aria-label="Community sponsorship and accreditations"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center gap-8">
            <div className="flex items-center gap-3 text-[10px] font-technical uppercase tracking-[0.4em] text-[#9aa3b0]">
              <div className="h-[1px] w-10 bg-gradient-to-r from-[#e2c977] via-[#f5e9c6] to-transparent" />
              Proudly accredited &amp; supporting community sport
              <div className="h-[1px] w-10 bg-gradient-to-l from-[#e2c977] via-[#f5e9c6] to-transparent" />
            </div>

            <div className="grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-10 w-full max-w-3xl">
              <div className="flex flex-col items-center gap-3">
                <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-white/20 bg-white/5 shadow-[0_18px_40px_rgba(0,0,0,0.5)]">
                  <Image
                    src="/images/gas-safe-register.png"
                    alt="Gas Safe Register"
                    fill
                    className="object-contain p-3"
                    sizes="96px"
                  />
                </div>
                <p className="text-[10px] font-technical uppercase tracking-[0.3em] text-[#d6e0ec] text-center">
                  Gas Safe Register
                </p>
              </div>

              <div className="flex flex-col items-center gap-3">
                <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-white/24 bg-white/5 shadow-[0_20px_50px_rgba(0,0,0,0.6)]">
                  <Image
                    src="/images/next-level-fc.png"
                    alt="Next Level FC"
                    fill
                    className="object-contain p-4"
                    sizes="112px"
                  />
                </div>
                <p className="text-[10px] font-technical uppercase tracking-[0.3em] text-[#d6e0ec] text-center">
                  Next Level FC Sponsor
                </p>
              </div>

              <div className="flex flex-col items-center gap-3">
                <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-white/20 bg-white/5 shadow-[0_18px_40px_rgba(0,0,0,0.5)]">
                  <Image
                    src="/images/safe-contractor.png"
                    alt="SafeContractor Approved"
                    fill
                    className="object-contain p-3"
                    sizes="96px"
                  />
                </div>
                <p className="text-[10px] font-technical uppercase tracking-[0.3em] text-[#d6e0ec] text-center">
                  SafeContractor Approved
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA – tuned for light/gold */}
      <CTABanner
        title="Ready To Brief Your Project?"
        subtitle="Share your drawings or describe the issue and we’ll come back with clear next steps, options, and transparent pricing."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
