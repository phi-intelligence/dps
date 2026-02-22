"use client";

import { Phone, Mail, Clock, AlertTriangle, Zap } from "lucide-react";
import QuoteForm from "@/components/ui/QuoteForm";
import PageHero from "@/components/ui/PageHero";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";

export default function ContactPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Contact Us"
        subtitle="Get in touch for a free, no-obligation quote or to book a service. We aim to respond to all enquiries within one working day."
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Contact" }]}
        backgroundImage="/images/hero-bg.jpg"
        compact
      />

      {/* Main Quote Form & Details */}
      <section className="py-24" aria-label="Contact and quote request">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-24 items-start">

            {/* Left: Contact Info */}
            <div className="lg:col-span-2 space-y-10">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="w-16 h-16 bg-brand-card border border-brand-card-border-hover rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-red/30 transition-all">
                  <Phone size={28} className="text-brand-red" />
                </div>
                <h2 className="font-technical font-extrabold text-brand-text text-xl mb-4 tracking-widest uppercase">Call Us</h2>
                <a
                  href={`tel:${COMPANY.phone}`}
                  className="text-brand-text font-technical font-extrabold text-3xl hover:text-brand-red transition-colors inline-block mb-6 tracking-tighter"
                >
                  {COMPANY.phone}
                </a>
                <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em]">Speak directly with our team for urgent enquiries.</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-blue/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="w-16 h-16 bg-brand-card border border-brand-card-border-hover rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-blue/30 transition-all">
                  <Mail size={28} className="text-brand-blue" />
                </div>
                <h2 className="font-technical font-extrabold text-brand-text text-xl mb-4 tracking-widest uppercase">Email Us</h2>
                <a
                  href={`mailto:${COMPANY.email}`}
                  className="text-brand-text font-technical font-extrabold text-lg hover:text-brand-blue transition-colors inline-block mb-6 break-all tracking-widest"
                >
                  {COMPANY.email}
                </a>
                <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em]">We aim to reply within one working day.</p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-purple/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="w-16 h-16 bg-brand-card border border-brand-card-border-hover rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-purple/30 transition-all">
                  <Clock size={28} className="text-brand-purple" />
                </div>
                <h2 className="font-technical font-extrabold text-brand-text text-xl mb-6 tracking-widest uppercase">Opening Hours</h2>
                <div className="space-y-4 text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-brand-muted">
                  <div className="flex justify-between border-b border-brand-card-border pb-3">
                    <span>Mon–Fri</span>
                    <span className="text-brand-text">08:00 – 18:00</span>
                  </div>
                  <div className="flex justify-between border-b border-brand-card-border pb-3">
                    <span>Saturday</span>
                    <span className="text-brand-text">09:00 – 13:00</span>
                  </div>
                  <div className="flex justify-between text-brand-muted">
                    <span>Sunday</span>
                    <span>Closed</span>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Right: Quote Form */}
            <div className="lg:col-span-3 bg-brand-navy rounded-[3rem] p-12 md:p-20 shadow-2xl border border-brand-card-border relative overflow-hidden">
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-red/5 blur-[150px] rounded-full pointer-events-none" />

              <div className="relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-red/20 bg-brand-red/5 mb-8">
                  <Zap size={12} className="text-brand-red" />
                  <span className="text-[9px] font-technical font-bold text-brand-red uppercase tracking-[0.3em]">Free Quote — No Obligation</span>
                </div>

                <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase leading-none">Request a Quote</h2>
                <p className="text-brand-muted text-xs font-light leading-relaxed mb-16 uppercase tracking-wider max-w-xl">
                  Fill in the form below and we will get back to you with a clear, no-obligation quote as soon as possible.
                </p>

                <QuoteForm />
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Urgent Enquiry Strip */}
      <section className="py-24 bg-brand-red border-y border-white/10 relative overflow-hidden" aria-label="Urgent enquiry">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center justify-between gap-12">
          <div className="flex items-center gap-8">
            <div className="w-20 h-20 bg-black/20 backdrop-blur-xl border border-white/10 rounded-2xl flex items-center justify-center shrink-0">
              <AlertTriangle size={36} className="text-white animate-pulse" />
            </div>
            <div>
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white tracking-widest uppercase mb-2">
                Urgent Issue?
              </h2>
              <p className="text-white/80 text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                Call us directly for urgent heating and air conditioning issues.
              </p>
            </div>
          </div>
          <a
            href={`tel:${COMPANY.phone}`}
            className="group relative bg-white text-black px-12 py-6 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.3em] overflow-hidden shadow-2xl transition-all hover:scale-105"
          >
            <span className="relative z-10 transition-colors group-hover:text-brand-red flex items-center gap-4">
              <Phone size={20} className="animate-pulse" />
              {COMPANY.phone}
            </span>
          </a>
        </div>
      </section>
    </div>
  );
}
