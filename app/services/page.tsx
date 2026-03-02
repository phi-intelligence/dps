"use client";

import Image from "next/image";
import Link from "next/link";
import { Building2, Home, ArrowRight, Phone, Shield, Zap, Award, Activity } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, COMMERCIAL_SERVICES, DOMESTIC_SERVICES } from "@/lib/constants";
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
  return (
    <div className="bg-brand-surface">
      <PageHero
        title="Our Services"
        subtitle={`Commercial & domestic gas works across ${COMPANY.areas}. Heating, plumbing, PPM, and emergency support.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Services" }]}
        backgroundImage="/images/blueprint-commercial-system.png"
      />

      {/* Category Grid */}
      <section className="py-40 bg-brand-surface" aria-label="Service categories">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-32">
          {categories.map((cat, i) => (
            <motion.div
              key={cat.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className={`relative flex flex-col items-center gap-16 lg:gap-32 ${i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"}`}
            >
              {/* Image */}
              <div className="relative w-full lg:w-1/2 h-[500px] rounded-[3rem] overflow-hidden border border-brand-card-border shadow-2xl group">
                <div className="absolute inset-0 bg-brand-steel/10 mix-blend-multiply z-10" />
                <Image
                  src={cat.image}
                  alt={cat.title}
                  fill
                  className="object-cover grayscale contrast-125 brightness-75 group-hover:scale-105 transition-transform duration-1000"
                  sizes="(max-width: 1024px) 100vw, 50vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-brand-navy via-transparent to-transparent z-10" />

                <div className="absolute top-8 left-8 z-20">
                  <div className="px-4 py-2 bg-brand-navy/60 backdrop-blur-xl border border-brand-card-border-hover rounded-xl flex items-center gap-3">
                    <Activity size={14} className="text-brand-red" />
                    <span className="text-[10px] font-technical font-bold text-brand-text uppercase tracking-widest">{cat.title}</span>
                  </div>
                </div>
              </div>

              {/* Content Panel */}
              <div className="lg:w-1/2">
                <div className="inline-flex items-center gap-3 px-4 py-2 border border-brand-card-border-hover bg-brand-card rounded-full mb-8">
                  <cat.icon size={16} className="text-brand-red" />
                  <span className="text-[10px] font-technical font-bold text-brand-muted uppercase tracking-[0.3em]">Service 0{i + 1}</span>
                </div>

                <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase leading-none">
                  {cat.title}
                </h2>

                <p className="text-brand-muted text-sm font-light mb-12 leading-relaxed uppercase tracking-[0.15em] max-w-xl">
                  {cat.description}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-12 mb-16">
                  {cat.services.map((s) => (
                    <div key={s} className="flex items-center gap-4 group/item">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-red/30 group-hover/item:bg-brand-red transition-all" />
                      <span className="text-[10px] font-technical font-bold text-brand-muted group-hover/item:text-brand-text transition-colors uppercase tracking-widest">
                        {s}
                      </span>
                    </div>
                  ))}
                </div>

                <Link
                  href={cat.href}
                  className="group relative inline-flex items-center justify-center bg-brand-text text-white px-10 py-5 rounded-full font-technical font-extrabold text-[10px] uppercase tracking-[0.3em] overflow-hidden transition-all shadow-lg shadow-brand-text/10"
                >
                  <span className="relative z-10 group-hover:text-white transition-colors">{cat.ctaLabel}</span>
                  <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Need Help Now? Strip */}
      <section className="py-24 bg-brand-red relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-10 mix-blend-overlay"
          style={{
            backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/10 blur-[100px] rounded-full" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12 text-center lg:text-left">
            <div className="max-w-xl">
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-4 tracking-widest uppercase">
                Need Help Today?
              </h2>
              <p className="text-white/80 text-xs font-technical uppercase tracking-widest">Call us now for same-day service. Available for urgent heating and plumbing issues.</p>
            </div>

            <div className="flex flex-col sm:flex-row gap-6 shrink-0">
              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center justify-center gap-4 bg-white text-brand-red px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-white/90 transition-all shadow-xl"
              >
                <Phone size={18} />
                {COMPANY.phone}
              </a>
              <button
                type="button"
                onClick={() => openQuoteModal()}
                className="flex items-center justify-center gap-4 border border-white/30 bg-white/5 backdrop-blur-md text-white px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-white/10 transition-all"
              >
                Get a Free Quote
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Capability Blueprint */}
      <section className="py-40 bg-brand-surface relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-brand-red/[0.03] blur-[150px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              All Services
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Full <span className="text-brand-red">Coverage</span>
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
                    className="flex items-start gap-6 p-6 rounded-2xl border border-brand-card-border bg-brand-card hover:border-brand-red/20 transition-all group"
                  >
                    <div className="w-12 h-12 rounded-xl border border-brand-card-border bg-brand-navy flex items-center justify-center shrink-0 group-hover:border-brand-red/20 transition-all">
                      <cat.icon size={20} className="text-brand-red" />
                    </div>
                    <div>
                      <h3 className="text-[10px] font-technical font-extrabold text-brand-text uppercase tracking-widest mb-2">{cat.title}</h3>
                      <p className="text-[9px] font-technical text-brand-muted uppercase tracking-[0.2em] leading-relaxed">{cat.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose DPS */}
      <section className="py-40 bg-brand-steel relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-[800px] h-[400px] bg-brand-blue/[0.03] blur-[150px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Why Choose <span className="text-brand-red">DPS</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-16">
            {whyDPS.map((item, i) => (
              <div key={item.title} className="text-center group relative p-8">
                <div className="absolute inset-0 bg-brand-navy shadow-sm border border-brand-card-border rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-20 h-20 bg-brand-navy border border-brand-card-border rounded-3xl flex items-center justify-center mx-auto mb-10 group-hover:border-brand-red/10 transition-all duration-500">
                  <item.icon size={32} className="text-brand-red" />
                </div>
                <h3 className="text-lg font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className="text-brand-muted text-[10px] font-technical uppercase tracking-widest leading-relaxed">
                  {item.description}
                </p>

                <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-8xl font-technical font-black text-black/[0.02] pointer-events-none group-hover:text-brand-red/[0.03] transition-colors">
                  0{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABanner />
    </div>
  );
}
