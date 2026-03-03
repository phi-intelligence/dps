"use client";

import { useEffect, useRef, useState } from "react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, REVIEWS, PORTFOLIO_PROJECTS } from "@/lib/constants";
import { motion, useMotionValue, useAnimationFrame } from "framer-motion";
import Image from "next/image";
import {
  Flame,
  Wrench,
  MapPin,
  Award,
  CheckCircle,
  Building2,
  Clock,
  Star,
} from "lucide-react";

const categoryIcon: Record<string, React.ReactNode> = {
  Heating: <Flame size={14} />,
  Plumbing: <Wrench size={14} />,
};

const categoryColor: Record<string, string> = {
  Heating: "bg-brand-red/20 text-brand-red border-brand-red/30",
  Plumbing: "bg-brand-blue/20 text-brand-blue border-brand-blue/30",
};

const stats = [
  { icon: CheckCircle, label: "Projects Completed", value: "500+" },
  { icon: Clock, label: "Years Experience", value: "10+" },
  { icon: Building2, label: "Areas Covered", value: "20+" },
  { icon: Star, label: "Customer Rating", value: "5.0" },
];

type ReviewItem = (typeof REVIEWS)[number];

function ReviewMarqueeCard({ review }: { review: ReviewItem }) {
  return (
    <div className="relative flex min-h-[220px] min-w-[300px] max-w-[360px] flex-col rounded-[1.9rem] border border-[#e0d3b8] bg-white/92 px-5 pt-9 pb-6 shadow-[0_18px_50px_rgba(0,0,0,0.12)] backdrop-blur-md">
      {/* Avatar circle */}
      <div className="absolute -top-5 left-1/2 flex h-10 w-10 -translate-x-1/2 items-center justify-center rounded-full border border-[#e0d3b8] bg-[#05080c] text-xs font-technical font-bold uppercase tracking-[0.18em] text-[#e2c977]">
        {review.name.charAt(0)}
      </div>

      <div className="mt-1 text-center">
        <p className="text-xs md:text-sm font-technical font-extrabold uppercase tracking-[0.26em] text-[#171b1f]">
          {review.name}
        </p>
        <p className="mt-1 text-[10px] md:text-[11px] font-technical uppercase tracking-[0.2em] text-[#5b6167]">
          {review.service}
        </p>
      </div>

      <p className="mt-4 flex-1 text-xs md:text-sm leading-relaxed text-[#272c32]">
        {review.quote}
      </p>

      <div
        className="mt-auto flex justify-center gap-1.5 pt-4"
        aria-label={`${review.rating} out of 5 stars`}
      >
        {Array.from({ length: review.rating }).map((_, i) => (
          <Star
            key={i}
            size={22}
            className="fill-[#c9a227] text-[#c9a227] drop-shadow-[0_0_6px_rgba(201,162,39,0.5)]"
          />
        ))}
      </div>
    </div>
  );
}

function ReviewMarqueeRow({ direction }: { direction: "left" | "right" }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [cycleWidth, setCycleWidth] = useState(0);
  const x = useMotionValue(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (containerRef.current) {
      setCycleWidth(containerRef.current.scrollWidth / 2 || 0);
    }
  }, []);

  useAnimationFrame((_, delta) => {
    if (paused || cycleWidth === 0) return;

    const directionFactor = direction === "left" ? -1 : 1;
    const pixelsPerSecond = 35;
    const moveBy = (pixelsPerSecond * delta) / 1000 * directionFactor;

    let next = x.get() + moveBy;

    if (direction === "left") {
      if (next <= -cycleWidth) {
        next += cycleWidth;
      }
    } else {
      if (next >= 0) {
        next -= cycleWidth;
      }
    }

    x.set(next);
  });

  return (
    <div className="w-full overflow-hidden">
      <motion.div
        ref={containerRef}
        style={{ x }}
        className="flex gap-6 px-5 pt-10"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {[...REVIEWS, ...REVIEWS].map((review, idx) => (
          <ReviewMarqueeCard key={`${review.name}-${idx}`} review={review} />
        ))}
      </motion.div>
    </div>
  );
}

export default function PortfolioPage() {
  return (
    <div className="bg-[#f2ede3] text-brand-text">
      {/* ── Hero ── */}
      <PageHero
        title="Portfolio"
        subtitle={`Completed projects across ${COMPANY.areas}. Heating and plumbing — delivered to the highest standard.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Portfolio" }]}
        backgroundImage="/images/team-professional.jpg"
        variant="luxury"
        compact
      />

      {/* ── Stats Strip ── */}
      <section className="relative bg-[#05080c] py-18 md:py-20 overflow-hidden">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-4 h-56 w-72 rotate-6 rounded-[3rem] border border-white/6" />
          <div className="absolute -left-40 bottom-0 h-52 w-80 -rotate-6 rounded-[3rem] border border-[#e2c977]/25" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-10 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977]">
                Portfolio Snapshot
              </span>
              <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-white">
                Built Projects In Numbers
              </h2>
            </div>
            <p className="max-w-md text-xs md:text-sm text-[#9aa3b0]">
              A view over the live work delivered across {COMPANY.areas} — from
              single dwellings to multi-storey plant.
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="text-center rounded-2xl border border-white/10 bg-white/5 px-4 py-6 backdrop-blur-sm shadow-[0_18px_40px_rgba(0,0,0,0.45)]"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl border border-[#e2c977]/40 bg-white/5 text-[#e2c977] mb-4">
                  <stat.icon size={22} />
                </div>
                <p className="text-3xl sm:text-4xl font-extrabold text-white font-technical">
                  {stat.value}
                </p>
                <p className="text-[11px] uppercase tracking-[0.3em] text-[#9aa3b0] font-technical mt-2">
                  {stat.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Completed Projects Grid ── */}
      <section className="relative py-28 md:py-32 bg-[#f7f3ea] overflow-hidden">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-10 h-64 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/28 bg-[#e2c977]/10" />
          <div className="absolute -left-40 bottom-0 h-60 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/22 bg-[#d4af37]/8" />
          <div className="absolute inset-x-12 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/25 to-transparent" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-20"
          >
            <span className="inline-block text-xs md:text-sm font-bold uppercase tracking-[0.35em] text-[#b8963a] font-technical mb-4">
              Deployment Log
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-technical uppercase tracking-[0.2em] text-[#171b1f]">
              Completed <span className="text-[#b8963a]">Projects</span>
            </h2>
            <p className="mt-6 text-[#3c444b] max-w-2xl mx-auto text-sm md:text-base">
              A selection of recent installations, repairs, and system upgrades
              delivered across {COMPANY.areas}.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {PORTFOLIO_PROJECTS.map((project, i) => (
              <motion.div
                key={project.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="group relative overflow-hidden rounded-[1.8rem] border border-[#2d3a46] bg-gradient-to-br from-[#05070b] via-[#0f151c] to-[#020508] text-[#d6e0ec] shadow-[0_22px_60px_rgba(0,0,0,0.5)] hover:-translate-y-1 hover:shadow-[0_26px_70px_rgba(0,0,0,0.7)] transition-all duration-500"
              >
                {/* Project Image */}
                <div className="relative h-56 overflow-hidden">
                  <Image
                    src={project.image || "/images/central-heating.jpg"}
                    alt={project.title}
                    fill
                    className="object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                  {/* Category Badge */}
                  <div className="absolute top-4 left-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-[0.25em] border ${
                        categoryColor[project.category] ||
                        "border-white/20 bg-white/5 text-[#e2c977]"
                      }`}
                    >
                      {categoryIcon[project.category]}
                      {project.category}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <h3 className="text-lg font-bold font-technical uppercase tracking-wide text-white mb-1">
                    {project.title}
                  </h3>
                  <div className="flex items-center gap-1.5 text-[#9aa3b0] text-sm mb-4">
                    <MapPin size={14} className="text-[#e2c977]" />
                    {project.location}
                  </div>
                  <p className="text-[#b3c0d0] text-sm leading-relaxed mb-6">
                    {project.description}
                  </p>

                  {/* Stat Pills */}
                  <div className="flex gap-3">
                    {project.stats.map((stat) => (
                      <div
                        key={stat.label}
                        className="flex-1 rounded-xl px-3 py-2 text-center border border-white/18 bg-white/5"
                      >
                        <p className="text-base font-bold text-white font-technical">
                          {stat.value}
                        </p>
                        <p className="text-[11px] uppercase tracking-[0.28em] text-[#b3c0d0]">
                          {stat.label}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Featured Project Highlight ── */}
      <section className="relative py-28 md:py-32 bg-[#05080c] overflow-hidden">
        <div className="absolute inset-x-0 -top-10 h-10 bg-gradient-to-b from-[#f7f3ea] to-transparent opacity-70" />
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-8 h-64 w-72 rotate-6 border border-white/7 rounded-[3rem]" />
          <div className="absolute -left-36 bottom-0 h-56 w-80 -rotate-6 border border-[#e2c977]/25 rounded-[3rem]" />
          <div className="absolute inset-x-12 top-1/2 h-px bg-gradient-to-r from-transparent via-white/12 to-transparent" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left — Text */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 text-[11px] md:text-xs font-bold uppercase tracking-[0.3em] text-[#e2c977] font-technical mb-6">
                <Award size={16} />
                Featured Deployment
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-technical uppercase tracking-[0.18em] text-white mb-6">
                Commercial Plant{" "}
                <span className="text-[#e2c977]">Room Build</span>
              </h2>
              <p className="text-[#9aa3b0] text-base md:text-lg leading-relaxed mb-8">
                Full design and installation of a commercial heating plant room
                in central London. Twin cascade boilers, pressurisation unit,
                buffer vessel, and full BEMS integration — completed on schedule
                with zero disruption to tenants.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  { label: "System Output", value: "2.5Mwatt" },
                  { label: "Floors Heated", value: "6 floors" },
                  { label: "Duration", value: "5 months" },
                  { label: "Warranty", value: "10 years" },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 15 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 + i * 0.1, duration: 0.4 }}
                    className="bg-white/5 border border-white/12 rounded-xl px-4 py-3"
                  >
                    <p className="text-xl font-bold text-white font-technical">
                      {stat.value}
                    </p>
                    <p className="text-xs uppercase tracking-[0.28em] text-[#b3c0d0] font-technical">
                      {stat.label}
                    </p>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Right — Blueprint */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <BlueprintBillboard
                src="/images/blueprint-plant-room.png"
                alt="Commercial heating plant room schematic"
                theme="warm"
                versionText="PLANT_RM: V3.1"
                idHash="DPS-PLT-2024"
                statusText="COMMISSIONED"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section className="relative py-28 md:py-32 bg-[#05080c] overflow-hidden">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-8 h-60 w-80 rotate-6 rounded-[3rem] border border-white/10" />
          <div className="absolute -left-40 bottom-0 h-56 w-80 -rotate-6 rounded-[3rem] border border-[#e2c977]/30" />
          <div className="absolute inset-x-12 top-1/2 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />
        </div>

        {/* Heading */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12 md:mb-16"
          >
            <span className="inline-block text-xs md:text-sm font-bold uppercase tracking-[0.35em] text-[#e2c977] font-technical mb-4">
              Client Transmissions
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-technical uppercase tracking-[0.2em] text-white">
              What Our Clients <span className="text-[#e2c977]">Say</span>
            </h2>
          </motion.div>
        </div>

        {/* Full-width marquee rows */}
        <div className="relative mt-6">
          {/* Edge gradients */}
          <div className="pointer-events-none absolute inset-y-0 left-0 w-16 sm:w-24 bg-gradient-to-r from-[#05080c] via-[#05080c] to-transparent z-20 opacity-70" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-16 sm:w-24 bg-gradient-to-l from-[#05080c] via-[#05080c] to-transparent z-20 opacity-70" />

          <div className="space-y-6 relative z-10">
            <ReviewMarqueeRow direction="left" />
            <ReviewMarqueeRow direction="right" />
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <CTABanner backgroundImage="/images/blueprints/blueprint-8.png" />
    </div>
  );
}
