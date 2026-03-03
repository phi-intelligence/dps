"use client";

import { Phone, Mail, Clock, MapPin, AlertTriangle, Zap } from "lucide-react";
import QuoteForm from "@/components/ui/QuoteForm";
import PageHero from "@/components/ui/PageHero";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";

export default function ContactPage() {
  return (
    <div className="bg-[#f2ede3] text-brand-text overflow-x-hidden min-h-screen">
      <PageHero
        title="Contact Us"
        subtitle="Get in touch for a free, no-obligation quote or to book a service. We aim to respond to all enquiries within one working day."
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Contact" }]}
        backgroundImage="/images/blueprints/blueprint-1.png"
        variant="luxury"
        darkHero
        compact
      />

      {/* Main Quote Form & Details — light band, luxury dark cards */}
      <section className="relative py-20 md:py-24 bg-[#f7f3ea] overflow-hidden" aria-label="Contact and quote request">
        {/* Geometric background */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-12 h-56 w-72 rotate-6 rounded-[3rem] border border-[#e2c977]/25 bg-[#e2c977]/5" />
          <div className="absolute -left-40 bottom-12 h-48 w-64 -rotate-6 rounded-[3rem] border border-[#e2c977]/20 bg-[#e2c977]/5" />
          <div className="absolute right-1/4 top-1/4 h-32 w-40 rotate-12 rounded-[2rem] border border-[#d4af37]/20" />
          <div className="absolute left-1/4 bottom-1/3 h-28 w-36 -rotate-6 rounded-[2rem] border border-[#e2c977]/15" />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-px w-full max-w-2xl bg-gradient-to-r from-transparent via-[#e2c977]/20 to-transparent" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12 lg:gap-16 items-start">

            {/* Left: Contact Info — two combined cards in a column */}
            <div className="lg:col-span-2 flex flex-col gap-8">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#0a0f14] to-[#0d1319] p-10 relative overflow-hidden"
              >
                <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-28 rotate-6 border border-white/10 rounded-[2rem] opacity-40" />
                <div className="flex items-center gap-3 mb-8">
                  <div className="w-16 h-16 rounded-2xl border border-[#e2c977]/40 bg-white/5 flex items-center justify-center shrink-0">
                    <Phone size={28} className="text-[#e2c977]" />
                  </div>
                  <div className="w-16 h-16 rounded-2xl border border-[#e2c977]/40 bg-white/5 flex items-center justify-center shrink-0">
                    <Mail size={28} className="text-[#e2c977]" />
                  </div>
                </div>
                <h2 className="font-technical font-extrabold text-white text-xl mb-6 tracking-[0.2em] uppercase">Call & Email</h2>
                <div className="space-y-6">
                  <div>
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mb-1">Call</p>
                    <a
                      href={`tel:${COMPANY.phone}`}
                      className="text-white font-technical font-extrabold text-2xl md:text-3xl hover:text-[#e2c977] transition-colors inline-block tracking-tight"
                    >
                      {COMPANY.phone}
                    </a>
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mt-1">Speak directly for urgent enquiries.</p>
                  </div>
                  <div className="border-t border-white/10 pt-6">
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mb-1">Email</p>
                    <a
                      href={`mailto:${COMPANY.email}`}
                      className="text-white font-technical font-extrabold text-lg hover:text-[#e2c977] transition-colors inline-block break-all tracking-wide"
                    >
                      {COMPANY.email}
                    </a>
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mt-1">We aim to reply within one working day.</p>
                  </div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#0a0f14] to-[#0d1319] p-10 relative overflow-hidden"
              >
                <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-28 rotate-6 border border-white/10 rounded-[2rem] opacity-40" />
                <div className="flex items-center gap-3 mb-8">
                  <div className="w-16 h-16 rounded-2xl border border-[#e2c977]/40 bg-white/5 flex items-center justify-center shrink-0">
                    <Clock size={28} className="text-[#e2c977]" />
                  </div>
                  <div className="w-16 h-16 rounded-2xl border border-[#e2c977]/40 bg-white/5 flex items-center justify-center shrink-0">
                    <MapPin size={28} className="text-[#e2c977]" />
                  </div>
                </div>
                <h2 className="font-technical font-extrabold text-white text-xl mb-6 tracking-[0.2em] uppercase">Hours & Location</h2>
                <div className="space-y-6">
                  <div>
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mb-1">Opening hours</p>
                    <p className="text-white font-technical font-extrabold text-2xl md:text-3xl tracking-tight">24/7</p>
                    <p className="text-[#9aa3b0] text-sm font-technical uppercase tracking-wider leading-relaxed mt-1">
                      Every day of the week — emergency callouts and enquiries welcome.
                    </p>
                  </div>
                  <div className="border-t border-white/10 pt-6">
                    <p className="text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] mb-1">Location</p>
                    <p className="text-white font-technical font-extrabold text-lg md:text-xl tracking-tight">
                      Across London, Kent, Essex and Surrey
                    </p>
                    <p className="text-[#9aa3b0] text-sm font-technical uppercase tracking-wider leading-relaxed mt-1">
                      Local engineers with fast response across our coverage area.
                    </p>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Right: Quote Form */}
            <div className="lg:col-span-3 rounded-[2.25rem] border border-white/10 bg-gradient-to-br from-[#0a0f14] to-[#0d1319] p-12 md:p-20 relative overflow-hidden">
              <div className="pointer-events-none absolute -right-20 -top-20 h-40 w-48 rotate-6 border border-white/10 rounded-[2rem] opacity-30" />

              <div className="relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#e2c977]/30 bg-[#e2c977]/10 mb-8">
                  <Zap size={12} className="text-[#e2c977]" />
                  <span className="text-[10px] font-technical font-bold text-[#e2c977] uppercase tracking-[0.25em]">Free Quote — No Obligation</span>
                </div>

                <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-6 tracking-[0.2em] uppercase leading-none">Request a Quote</h2>
                <p className="text-[#b3c0d0] text-sm leading-relaxed mb-16 uppercase tracking-wider max-w-xl">
                  Fill in the form below and we will get back to you with a clear, no-obligation quote as soon as possible.
                </p>

                <QuoteForm theme="luxury" />
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Urgent Enquiry Strip — dark band, gold CTA */}
      <section className="relative py-24 md:py-28 overflow-hidden" aria-label="Urgent enquiry">
        <div className="absolute inset-0 bg-[#0b1015]" />
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[#e2c977] to-transparent opacity-80" />
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute right-0 top-1/4 h-40 w-56 -rotate-6 rounded-[2rem] border border-[#e2c977]/10" />
          <div className="absolute left-0 bottom-1/4 h-36 w-48 rotate-6 rounded-[2rem] border border-white/5" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center justify-between gap-12">
          <div className="flex items-center gap-8">
            <div className="w-20 h-20 rounded-2xl border border-[#e2c977]/30 bg-white/5 flex items-center justify-center shrink-0">
              <AlertTriangle size={36} className="text-[#e2c977] animate-pulse" />
            </div>
            <div>
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-technical font-extrabold text-white tracking-[0.2em] uppercase mb-2">
                Urgent Issue?
              </h2>
              <p className="text-[#b3c0d0] text-sm font-technical font-bold uppercase tracking-[0.3em]">
                Call us directly for urgent heating and plumbing issues.
              </p>
            </div>
          </div>
          <a
            href={`tel:${COMPANY.phone}`}
            className="inline-flex items-center gap-3 bg-[#e2c977] text-[#0a0f14] px-12 py-6 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.3em] hover:bg-[#f5e9c6] transition-colors shadow-lg"
          >
            <Phone size={20} />
            {COMPANY.phone}
          </a>
        </div>
      </section>
    </div>
  );
}
