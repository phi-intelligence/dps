"use client";

import Link from "next/link";
import Image from "next/image";
import { Building2, ArrowRight, Phone } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import { COMPANY, COMMERCIAL_SERVICES } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { motion } from "framer-motion";

const COMMERCIAL_CARD_IMAGES: Record<string, string> = {
  "Commercial Boiler Servicing": "/images/boiler-modern.jpg",
  "Plant Room Maintenance": "/images/central-heating.jpg",
  "Gas Safety Inspections": "/images/boiler-repair.jpg",
  "PPM Contracts": "/images/central-heating.jpg",
  "Fault Finding & Diagnosis": "/images/boiler-repair.jpg",
  "Commercial Heating Systems": "/images/central-heating.jpg",
  "24 Hour Emergency Breakdowns": "/images/boiler-repair.jpg",
  "Commercial Facilities Management (3 Tier PPM Packages)": "/images/central-heating.jpg",
  "Commercial Facilities Management (Reactive & OOH Callouts)": "/images/plumbing-pipes.jpg",
};

export default function CommercialServicesPage() {
  const { openQuoteModal } = useQuoteModal();

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Commercial Services"
        subtitle={`Professional commercial gas, heating, and facilities management across ${COMPANY.areas}. PPM contracts, plant room maintenance, and 24/7 emergency support.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Commercial Services" },
        ]}
        backgroundImage="/images/blueprints/blueprint-8.png"
        compact
      />

      <section className="py-24 relative overflow-hidden bg-brand-steel">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 border border-brand-red/20 bg-brand-red/5 rounded-full px-5 py-2 mb-6">
              <Building2 size={14} className="text-brand-red" />
              <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                Commercial
              </span>
            </div>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-6">
              What We <span className="text-brand-red">Offer</span>
            </h2>
            <p className="text-brand-muted text-sm font-light uppercase tracking-wider max-w-2xl mx-auto">
              From planned preventative maintenance to 24-hour emergency breakdowns — we keep your commercial systems running safely and efficiently.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {COMMERCIAL_SERVICES.map((service, i) => (
              <motion.div
                key={service.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="group"
              >
                <Link
                  href={service.href}
                  className="relative block aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border shadow-lg hover:border-brand-red/30 transition-all duration-300"
                >
                  <Image
                    src={COMMERCIAL_CARD_IMAGES[service.label] ?? "/images/central-heating.jpg"}
                    alt=""
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-5 flex items-center justify-between gap-4">
                    <span className="text-white font-technical font-bold text-[10px] sm:text-xs uppercase tracking-widest leading-tight line-clamp-2">
                      {service.label}
                    </span>
                    <span className="shrink-0 w-10 h-10 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center group-hover:bg-brand-red group-hover:border-brand-red transition-all">
                      <ArrowRight size={18} className="text-white" />
                    </span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>

          <div className="mt-20 text-center">
            <button
              type="button"
              onClick={() => openQuoteModal()}
              className="inline-flex items-center gap-3 bg-brand-red text-white px-10 py-5 rounded-full font-technical font-extrabold text-[11px] uppercase tracking-widest hover:bg-brand-red/90 transition-all"
            >
              Get a Free Quote
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>

      <section className="py-24 bg-brand-red relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col sm:flex-row items-center justify-between gap-12">
          <div>
            <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-4 tracking-widest uppercase">
              Need Commercial Support?
            </h2>
            <p className="text-white/80 text-xs font-technical uppercase tracking-widest">
              Call us for PPM contracts, emergency breakdowns, or facilities management.
            </p>
          </div>
          <a
            href={`tel:${COMPANY.phone}`}
            className="flex items-center gap-4 bg-white text-brand-red px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-white/90 transition-all shadow-xl shrink-0"
          >
            <Phone size={18} />
            {COMPANY.phone}
          </a>
        </div>
      </section>

      <CTABanner />
    </div>
  );
}
