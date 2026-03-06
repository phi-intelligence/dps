"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { Phone, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import { COMPANY, SERVICE_AREAS } from "@/lib/constants";

const ServiceAreasMap = dynamic(
  () => import("@/components/ui/ServiceAreasMap"),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-[#0a0f14] animate-pulse rounded-[2rem]" />
    ),
  }
);

export default function ServiceAreasPage() {
  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-x-hidden">
      <PageHero
        title="Service Areas"
        subtitle={`We provide heating and plumbing services across ${COMPANY.areas}. Local engineers, fast response times.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Service Areas" }]}
        backgroundImage="/images/service-area-map.jpg"
        variant="luxury"
        compact
      />

      {/* Where We Work — light band, copy left + map right */}
      <section
        className="relative py-20 md:py-28 bg-[#f7f3ea] overflow-hidden"
        aria-label="Where we work — coverage and map"
      >
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-12 h-56 w-72 rotate-6 rounded-[3rem] border border-[#e2c977]/20" />
          <div className="absolute -left-40 bottom-12 h-48 w-64 -rotate-6 rounded-[3rem] border border-[#e2c977]/15" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <span className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4 block">
                Coverage Area
              </span>
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-technical font-extrabold text-[#171b1f] mb-8 tracking-[0.2em] leading-tight uppercase">
                Where We <span className="text-[#b8963a]">Work</span>
              </h2>
              <div className="space-y-6 text-[#2b3136] text-sm md:text-base leading-relaxed max-w-xl">
                <p>
                  DPS Heating Services Ltd operates throughout{" "}
                  {COMPANY.areas}, covering both domestic and commercial
                  customers. Our engineers are locally based, allowing us to
                  offer fast response times across our entire coverage area.
                </p>
                <p>
                  Whether you need a boiler repaired, a heating system
                  installed, or plumbing work completed, we have
                  engineers ready to help. Same-day and next-day appointments
                  are available for most services.
                </p>
              </div>
              <div className="mt-14 rounded-[2rem] border-2 border-[#e2c977]/25 bg-[#0a0f14] p-8 md:p-10 relative overflow-hidden">
                <div className="pointer-events-none absolute -right-20 -top-20 h-32 w-40 rotate-6 border border-white/10 rounded-[2rem] opacity-40" />
                <p className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-[#e2c977] mb-3">
                  Not sure if we cover your area?
                </p>
                <p className="text-[#b3c0d0] text-xs md:text-sm font-technical tracking-wide leading-relaxed mb-8">
                  Give us a call or drop us an email — we are happy to confirm
                  coverage and get you booked in.
                </p>
                <a
                  href={`tel:${COMPANY.phone}`}
                  className="inline-flex items-center gap-3 bg-[#e2c977] text-[#0a0f14] px-8 py-4 rounded-full font-technical font-extrabold text-[10px] uppercase tracking-[0.3em] hover:bg-[#f5e9c6] transition-colors"
                >
                  <Phone size={16} />
                  {COMPANY.phone}
                </a>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="relative rounded-[2rem] overflow-hidden border-2 border-[#e2c977]/25 shadow-[0_24px_56px_rgba(0,0,0,0.12)] h-[400px] md:min-h-[480px] lg:h-[520px] min-h-[320px]"
            >
              <ServiceAreasMap />
              <div className="pointer-events-none absolute inset-0 rounded-[2rem] ring-1 ring-inset ring-[#e2c977]/10" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Coverage / stats — dark band, Always Nearby */}
      <section
        className="relative py-24 md:py-32 overflow-hidden"
        aria-label="Coverage and stats"
      >
        <div className="absolute inset-0 bg-[#05080c]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-80" />
        <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977]/60 to-transparent opacity-70" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[60%] w-[80%] max-w-2xl rounded-full border border-[#e2c977]/10 opacity-50" />
          <div className="absolute right-0 top-1/4 h-48 w-64 -rotate-6 rounded-[2rem] border border-white/5" />
          <div className="absolute left-0 bottom-1/4 h-40 w-56 rotate-6 rounded-[2rem] border border-[#e2c977]/10" />
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <span className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4 block">
            Local coverage
          </span>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white tracking-[0.2em] uppercase mb-4">
            Always <span className="text-[#e2c977]">Nearby</span>
          </h2>
          <p className="text-[#9aa3b0] text-sm md:text-base max-w-2xl mx-auto mb-14">
            Our engineers cover {COMPANY.areas} and surrounding areas. Being locally based means we can offer prompt service and respond quickly when you need us most.
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {[
              { stat: `${SERVICE_AREAS.length}+`, label: "Areas Covered" },
              { stat: "Same Day", label: "Available" },
              { stat: "13+", label: "Years Serving London" },
              { stat: "100%", label: "Gas Safe Registered" },
            ].map((item) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4 }}
                className="rounded-2xl border border-white/10 bg-white/5 px-6 py-6 text-center"
              >
                <p className="text-2xl md:text-3xl font-technical font-extrabold text-[#e2c977] mb-1 tracking-tight">
                  {item.stat}
                </p>
                <p className="text-[10px] font-technical text-[#9aa3b0] uppercase tracking-[0.3em]">
                  {item.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* London Aerial — full-bleed with luxury overlay */}
      <section className="relative h-[420px] overflow-hidden" aria-label="Coverage across London">
        <Image
          src="/images/service-area-map.jpg"
          alt="Aerial view of London — DPS Heating Services coverage area"
          fill
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-[#05080c]/75" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-4">
            <p className="text-[10px] font-technical font-bold uppercase tracking-[0.45em] text-[#e2c977] mb-4">
              Coverage Area
            </p>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-technical font-extrabold text-white tracking-[0.2em] uppercase">
              Across <span className="text-[#e2c977]">London</span>
            </h2>
            <p className="mt-6 text-[#b3c0d0] text-xs md:text-sm font-technical uppercase tracking-[0.3em]">
              {SERVICE_AREAS.length} regions covered · Same-day service available
            </p>
          </div>
        </div>
      </section>

      {/* Not in Our Area? — dark band, gold CTA */}
      <section
        className="relative py-24 md:py-28 overflow-hidden"
        aria-label="Contact if not in area"
      >
        <div className="absolute inset-0 bg-[#0b1015]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-80" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute right-0 top-1/4 h-40 w-56 -rotate-6 rounded-[2rem] border border-[#e2c977]/10" />
          <div className="absolute left-0 bottom-1/4 h-36 w-48 rotate-6 rounded-[2rem] border border-white/5" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white mb-4 tracking-[0.2em] uppercase">
            Don&apos;t See Your Area?
          </h2>
          <p className="text-[#b3c0d0] text-sm md:text-base mb-10 max-w-xl mx-auto">
            We may still be able to help. Contact us to check availability in your area.
          </p>
          <Link
            href="/contact"
            className="inline-flex items-center gap-3 bg-[#e2c977] text-[#0a0f14] px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.3em] hover:bg-[#f5e9c6] transition-colors shadow-lg"
          >
            Get in Touch <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      <CTABanner backgroundImage="/images/blueprints/blueprint-8.png" />
    </div>
  );
}
