"use client";

import Link from "next/link";
import Image from "next/image";
import { Home, ArrowRight, Phone } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import { COMPANY, CORE_SERVICES_IMAGES, CORE_SERVICE_DOMESTIC_HREFS } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { motion } from "framer-motion";

export default function DomesticServicesPage() {
  const { openQuoteModal } = useQuoteModal();

  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-x-hidden min-h-screen">
      <PageHero
        title="Domestic Services"
        subtitle={`Boiler installation, servicing, repairs, plumbing, and landlord gas safety across ${COMPANY.areas}. Gas Safe registered engineers.`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Domestic Services" },
        ]}
        backgroundImage="/images/our-services-domestic.png"
        variant="luxury"
        compact
      />

      {/* Domestic overview + core services cards */}
      <section className="py-24 relative overflow-hidden bg-[#f7f3ea]">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-0 h-64 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/26 bg-[#e2c977]/10" />
          <div className="absolute -left-40 bottom-0 h-60 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/22 bg-[#d4af37]/10" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#b8963a]/22 to-transparent" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 border border-[#e0d3b8]/80 bg-white/80 rounded-full px-5 py-2 mb-6 shadow-sm">
              <Home size={14} className="text-[#b8963a]" />
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#6b737b]">
                Domestic
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-technical font-extrabold text-[#171b1f] tracking-[0.26em] uppercase mb-6">
              What We <span className="text-[#b8963a]">Offer</span>
            </h2>
            <p className="text-[#3c444b] text-sm md:text-base font-light tracking-wider max-w-2xl mx-auto">
              From boiler installation and servicing to plumbing repairs and landlord gas safety certificates — we keep your home safe and warm.
            </p>
          </motion.div>

          {/* Core services — Mechanical, Electrical, Gas only */}
          <div>
            <p className="text-[#b8963a] text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-6 text-center">
              Our core services
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
              {(["Mechanical Services", "Electrical Services", "Gas Services"] as const).map((label, i) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className="group"
                >
                  <Link
                    href={CORE_SERVICE_DOMESTIC_HREFS[label]}
                    className="relative block aspect-[4/3] min-h-[240px] sm:min-h-[280px] rounded-2xl overflow-hidden border border-[#e0d3b8] shadow-[0_22px_60px_rgba(0,0,0,0.22)] hover:border-[#e2c977]/60 transition-all duration-300"
                  >
                    <Image
                      src={CORE_SERVICES_IMAGES[label] ?? "/images/core-services/mechanical.png"}
                      alt={label}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                      sizes="(max-width: 640px) 100vw, 33vw"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/35 to-transparent" />
                    <div className="absolute bottom-0 left-0 right-0 p-6 flex items-center justify-between gap-4">
                      <span className="text-white font-technical font-bold text-xs sm:text-sm uppercase tracking-widest leading-tight line-clamp-2">
                        {label === "Mechanical Services" ? "Plumbing and mechanical" : label}
                      </span>
                      <span className="shrink-0 w-12 h-12 rounded-xl bg-white/10 border border-white/25 flex items-center justify-center group-hover:bg-[#e2c977] group-hover:border-[#e2c977] transition-all">
                        <ArrowRight size={20} className="text-white" />
                      </span>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="mt-16 text-center">
            <button
              type="button"
              onClick={() => openQuoteModal()}
              className="inline-flex items-center gap-3 bg-[#e2c977] text-[#0a0f14] px-10 py-5 rounded-full font-technical font-extrabold text-[11px] uppercase tracking-widest hover:bg-[#e8d07a] transition-all shadow-[0_18px_40px_rgba(0,0,0,0.3)]"
            >
              Get a Free Quote
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>

      {/* Need Domestic Help strip — dark luxury band */}
      <section className="py-24 bg-[#05080c] relative overflow-hidden">
        <div className="absolute inset-0 opacity-60">
          <div className="absolute -left-24 top-0 w-80 h-80 rounded-[3rem] border border-[#e2c977]/18" />
          <div className="absolute -right-24 bottom-0 w-80 h-80 rounded-[3rem] border border-white/10" />
        </div>
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#e2c977]/60 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col sm:flex-row items-center justify-between gap-12">
          <div>
            <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-4 tracking-[0.26em] uppercase">
              Need Domestic Help?
            </h2>
            <p className="text-[#b3c0d0] text-xs font-technical uppercase tracking-widest">
              Call us for boiler servicing, repairs, plumbing, or emergency callouts.
            </p>
          </div>
          <a
            href={`tel:${COMPANY.phone}`}
            className="flex items-center gap-4 bg-[#e2c977] text-[#0a0f14] px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.2em] hover:bg-[#e8d07a] transition-all shadow-xl shrink-0"
          >
            <Phone size={18} />
            {COMPANY.phone}
          </a>
        </div>
      </section>
    </div>
  );
}
