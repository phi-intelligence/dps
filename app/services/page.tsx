"use client";

import Image from "next/image";
import Link from "next/link";
import { Building2, Home, ArrowRight, Phone, Shield, Zap, Award, Activity, Wrench, Flame } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, COMMERCIAL_SERVICES, DOMESTIC_SERVICES, KEY_STRENGTHS } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { motion } from "framer-motion";

const categories = [
  {
    icon: Building2,
    title: "Commercial Services",
    description:
      "Commercial boiler servicing, plant room maintenance, PPM contracts, fault finding, commercial heating systems, 24-hour emergency breakdowns, and facilities management across London, Kent, Essex and Surrey.",
    image: "/images/central-heating.jpg",
    services: COMMERCIAL_SERVICES.map((s) => s.label),
    href: "/services/commercial",
    ctaLabel: "View Commercial Services",
    accent: "brand-red",
  },
  {
    icon: Home,
    title: "Domestic Services",
    description:
      "Boiler installation, servicing and repairs, system diagnosis, landlord gas safety certification (CP12), plumbing repairs, and emergency callouts. Gas Safe registered engineers.",
    image: "/images/plumbing-pipes.jpg",
    services: DOMESTIC_SERVICES.map((s) => s.label),
    href: "/services/domestic",
    ctaLabel: "View Domestic Services",
    accent: "brand-blue",
  },
];

const whyDPS = [
  {
    icon: Shield,
    title: "Gas Safe Registered",
    description: "All heating work carried out by certified Gas Safe registered engineers.",
  },
  {
    icon: Zap,
    title: "Fast Response",
    description: "Same-day appointments available for urgent heating and plumbing problems.",
  },
  {
    icon: Award,
    title: "Over a Decade of Experience",
    description: `Trusted by customers across ${COMPANY.areas} for reliable, quality work.`,
  },
];

export default function ServicesPage() {
  const { openQuoteModal } = useQuoteModal();
  const keyHighlights = KEY_STRENGTHS.slice(0, 6);

  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-x-hidden min-h-screen">
      <PageHero
        title="Services"
        subtitle={`Mechanical, electrical and gas services for commercial estates and domestic homes across ${COMPANY.areas}. Heating, plumbing, compliance and emergency support.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Services" }]}
        backgroundImage="/images/blueprint-commercial-system.png"
        variant="luxury"
        darkHero
      />


      {/* Key service highlights (moved below Why Choose DPS) */}

      {/* Category Grid (commercial & domestic detail — preserved content, luxury styling) */}
      <section
        className="relative py-24 md:py-32 bg-[#f7f3ea] overflow-hidden"
        aria-label="Service categories"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-32 top-6 h-52 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/26 bg-[#e2c977]/10" />
          <div className="absolute -left-32 bottom-0 h-60 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/22 bg-[#d4af37]/10" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#b8963a]/20 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-24 md:space-y-32 z-10">
          {categories.map((cat, i) => (
            <motion.div
              key={cat.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className={`relative flex flex-col items-center gap-16 lg:gap-32 ${i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"}`}
            >
              {/* Image */}
              <div className="relative w-full lg:w-1/2 h-[420px] sm:h-[460px] md:h-[500px] rounded-[3rem] overflow-hidden border border-[#e0d3b8] shadow-[0_30px_80px_rgba(0,0,0,0.18)] group">
                <div className="absolute inset-0 bg-[#05080c]/10 mix-blend-multiply z-10" />
                <Image
                  src={cat.image}
                  alt={cat.title}
                  fill
                  className="object-cover grayscale contrast-125 brightness-75 group-hover:scale-105 transition-transform duration-1000"
                  sizes="(max-width: 1024px) 100vw, 50vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#05080c] via-transparent to-transparent z-10" />

                <div className="absolute top-8 left-8 z-20">
                  <div className="px-4 py-2 bg-[#05080c]/80 backdrop-blur-xl border border-white/20 rounded-xl flex items-center gap-3">
                    <Activity size={14} className="text-[#e2c977]" />
                    <span className="text-[10px] font-technical font-bold text-white uppercase tracking-widest">
                      {cat.title}
                    </span>
                  </div>
                </div>
              </div>

              {/* Content Panel */}
              <div className="lg:w-1/2">
                <div className="inline-flex items-center gap-3 px-4 py-2 border border-[#e0d3b8]/70 bg-white/80 rounded-full mb-8 shadow-sm">
                  <cat.icon size={16} className="text-[#b8963a]" />
                  <span className="text-[10px] font-technical font-bold text-[#6b737b] uppercase tracking-[0.3em]">
                    Service 0{i + 1}
                  </span>
                </div>

                <h2 className="text-3xl md:text-5xl lg:text-6xl font-technical font-extrabold text-[#171b1f] mb-8 tracking-[0.26em] uppercase leading-tight">
                  {cat.title}
                </h2>

                <p className="text-[#3c444b] text-sm md:text-base font-light mb-10 leading-relaxed max-w-xl">
                  {cat.description}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-12 mb-16">
                  {cat.services.map((s) => (
                    <div key={s} className="flex items-center gap-4 group/item">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#e2c977]/50 group-hover/item:bg-[#e2c977] transition-all" />
                      <span className="text-[10px] font-technical font-bold text-[#4e555c] group-hover/item:text-[#171b1f] transition-colors uppercase tracking-widest">
                        {s}
                      </span>
                    </div>
                  ))}
                </div>

                <Link
                  href={cat.href}
                  className="group relative inline-flex items-center justify-center bg-[#e2c977] text-[#0a0f14] px-10 py-5 rounded-full font-technical font-extrabold text-[10px] uppercase tracking-[0.3em] overflow-hidden transition-all shadow-[0_18px_40px_rgba(0,0,0,0.35)]"
                >
                  <span className="relative z-10 group-hover:text-[#0a0f14] transition-colors">{cat.ctaLabel}</span>
                  <div className="absolute inset-[1px] rounded-full bg-gradient-to-r from-[#fff9e6] via-[#f7f3ea] to-[#f0e6cf] opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Need Help Now? Strip (preserved content, luxury styling) */}
      <section className="py-24 bg-[#05080c] relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-60"
          style={{
            backgroundImage:
              "radial-gradient(circle at top left, rgba(226,201,119,0.14), transparent 55%), radial-gradient(circle at bottom right, rgba(180,150,58,0.16), transparent 55%)",
          }}
        />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#e2c977]/60 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12 text-center lg:text-left">
            <div className="max-w-xl">
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-4 tracking-widest uppercase">
                Need Help Today?
              </h2>
              <p className="text-[#b3c0d0] text-xs font-technical uppercase tracking-widest">
                Call us now for same-day service. Available for urgent heating and plumbing issues.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-6 shrink-0">
              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center justify-center gap-4 bg-[#e2c977] text-[#0a0f14] px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-[#e8d07a] transition-all shadow-xl"
              >
                <Phone size={18} />
                {COMPANY.phone}
              </a>
              <button
                type="button"
                onClick={() => openQuoteModal()}
                className="flex items-center justify-center gap-4 border border-[#e2c977]/50 bg-transparent backdrop-blur-md text-white px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-white/5 transition-all"
              >
                Get a Free Quote
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Capability Blueprint (preserved content, luxury styling) */}
      <section className="py-40 bg-[#05080c] relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-[#e2c977]/[0.08] blur-[160px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <span className="text-[#e2c977] text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              All Services
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-white tracking-widest uppercase">
              Full <span className="text-[#e2c977]">Coverage</span>
            </h2>
          </motion.div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <BlueprintBillboard
              src="/images/exploded-boiler.png"
              alt="Full heating and plumbing system schematic"
              theme="warm"
              versionText="HEATING & PLUMBING"
              idHash={`GAS SAFE: ${COMPANY.gasSafeNumber}`}
              statusText="ALL SYSTEMS OPERATIONAL"
              className="w-full"
            />
            <div className="space-y-10">
              <div className="space-y-6">
                {categories.map((cat, i) => (
                  <motion.div
                    key={cat.title}
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-6 p-6 rounded-2xl border border-white/10 bg-white/5 hover:border-[#e2c977]/35 transition-all group"
                  >
                    <div className="w-12 h-12 rounded-xl border border-white/15 bg-[#05080c] flex items-center justify-center shrink-0 group-hover:border-[#e2c977]/40 transition-all">
                      <cat.icon size={20} className="text-[#e2c977]" />
                    </div>
                    <div>
                      <h3 className="text-[10px] font-technical font-extrabold text-white uppercase tracking-widest mb-2">
                        {cat.title}
                      </h3>
                      <p className="text-[9px] font-technical text-[#b3c0d0] uppercase tracking-[0.2em] leading-relaxed">
                        {cat.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose DPS (preserved content, luxury styling) */}
      <section className="py-40 bg-[#0b1015] relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-[800px] h-[400px] bg-[#e2c977]/[0.06] blur-[150px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-white tracking-widest uppercase">
              Why Choose <span className="text-[#e2c977]">DPS</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-16">
            {whyDPS.map((item, i) => (
              <div key={item.title} className="text-center group relative p-8">
                <div className="absolute inset-0 bg-[#05080c] shadow-sm border border-white/10 rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-20 h-20 bg-[#05080c] border border-white/10 rounded-3xl flex items-center justify-center mx-auto mb-10 group-hover:border-[#e2c977]/30 transition-all duration-500">
                  <item.icon size={32} className="text-[#e2c977]" />
                </div>
                <h3 className="text-lg font-technical font-extrabold text-white mb-4 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className="text-[#b3c0d0] text-[10px] font-technical uppercase tracking-widest leading-relaxed">
                  {item.description}
                </p>

                <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-[#e2c977]/[0.06] transition-colors">
                  0{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key service highlights (now below Why Choose DPS) */}
      <section
        className="relative bg-[#f2ede3] py-20 md:py-24 overflow-hidden"
        aria-label="Key service highlights"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-32 top-10 h-56 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/24 bg-[#e2c977]/10" />
          <div className="absolute -left-32 bottom-0 h-60 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/22 bg-[#d4af37]/8" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#b8963a]/22 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-10 md:mb-14"
          >
            <span className="inline-block text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#b8963a] mb-3">
              Highlights
            </span>
            <h2 className="text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.24em] text-[#171b1f] mb-3">
              Services Clients Rely On
            </h2>
            <p className="max-w-2xl mx-auto text-sm text-[#3c444b]">
              A snapshot of the kinds of work we deliver every week across mechanical, electrical and gas.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {keyHighlights.map((item, index) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ delay: index * 0.05 }}
                className="rounded-2xl border border-[#e0d3b8] bg-white/90 px-5 py-6 shadow-[0_18px_50px_rgba(0,0,0,0.06)]"
              >
                <p className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#b8963a] mb-3">
                  0{index + 1}
                </p>
                <p className="text-sm text-[#2b3136] leading-relaxed">{item}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
