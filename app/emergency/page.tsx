"use client";

import { Phone, AlertTriangle, Flame, ShieldAlert } from "lucide-react";
import QuoteForm from "@/components/ui/QuoteForm";
import PageHero from "@/components/ui/PageHero";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";

const urgentIssues = [
  {
    icon: Flame,
    title: "Boiler Breakdown",
    description: "No heat or hot water? Call us to discuss the problem and arrange a prompt appointment.",
  },
  {
    icon: AlertTriangle,
    title: "Heating Fault",
    description: "Cold radiators, pressure loss, or strange noises from your heating system need prompt attention.",
  },
  {
    icon: ShieldAlert,
    title: "Gas Emergency — 0800 111 999",
    description: "If you smell gas, leave the property, do not use light switches, open windows, and call the National Gas Emergency line immediately.",
  },
];

export default function UrgentEnquiryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Urgent Enquiries"
        subtitle="For urgent heating and air conditioning problems, call us directly. We will do our best to help as quickly as possible."
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Urgent Enquiries" }]}
        backgroundImage="/images/de580d83-e113-4fa5-8635-779e1377cae6.jpg"
        compact
      />

      {/* Phone CTA */}
      <section className="py-24 bg-brand-red relative overflow-hidden" aria-label="Call us for urgent help">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <p className="text-white/80 text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-6">
            For urgent issues, call us directly
          </p>
          <a
            href={`tel:${COMPANY.phone}`}
            className="group relative inline-flex items-center gap-6 bg-white text-brand-red px-16 py-8 rounded-full font-technical font-extrabold text-2xl transition-all shadow-xl hover:scale-105"
          >
            <Phone size={36} className="animate-pulse" />
            <span>{COMPANY.phone}</span>
          </a>
          <p className="text-white/60 text-[9px] font-technical uppercase tracking-[0.3em] mt-8">
            Mon–Fri 08:00–18:00 // Sat 09:00–13:00
          </p>
        </div>
      </section>

      {/* Issue Types */}
      <section className="py-48 bg-brand-navy relative z-10" aria-label="Common urgent issues">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Common <span className="text-brand-red">Urgent Issues</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {urgentIssues.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`rounded-[2.5rem] p-12 border backdrop-blur-md transition-all group relative overflow-hidden ${item.title.includes("Gas Emergency")
                  ? "border-brand-red/50 bg-brand-red/5"
                  : "border-brand-card-border bg-brand-surface hover:border-brand-red/30"
                  }`}
              >
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-10 border transition-all bg-brand-navy border-brand-card-border-hover">
                  <item.icon
                    size={28}
                    className={item.title.includes("Gas Emergency") ? "text-brand-red animate-pulse" : "text-brand-red"}
                  />
                </div>
                <h3 className="text-2xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className={`font-light leading-relaxed text-xs uppercase tracking-widest ${item.title.includes("Gas Emergency") ? "text-brand-red/80 font-bold" : "text-brand-muted"}`}>
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Form for non-critical issues */}
      <section className="py-48 bg-brand-surface border-t border-brand-card-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h3 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
              Not Urgent?
            </h3>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.4em] leading-relaxed max-w-xl mx-auto">
              If the issue is not urgent, fill in the form below and we will get back to you promptly.
            </p>
          </div>
          <div className="bg-brand-navy border border-brand-card-border rounded-[3rem] p-12 md:p-20 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-blue/5 blur-3xl" />
            <QuoteForm />
          </div>
        </div>
      </section>
    </div>
  );
}
