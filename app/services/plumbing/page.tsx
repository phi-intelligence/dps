"use client";

import { Droplets, Wrench, ArrowRight, Phone, Activity, Zap, ShieldCheck, Cpu } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ProcessSteps from "@/components/sections/ProcessSteps";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";

const plumbingServices = [
  {
    icon: Wrench,
    title: "Hydraulic Repair",
    description: "Rapid resolution of structural leaks, pressure anomalies, and valve failures.",
    href: "/services/plumbing/plumbing-repairs",
    available: true,
  },
  {
    icon: Droplets,
    title: "General Architecture",
    description: "High-integrity fixture deployment and planned system pipework optimization.",
    href: "/services/plumbing/general-plumbing",
    available: true,
  },
  {
    icon: Activity,
    title: "Leak Diagnostics",
    description: "Precision ultrasound and thermal leak identification and node resolution.",
    href: "#",
    available: false,
  },
  {
    icon: Droplets,
    title: "Aqueous Design",
    description: "Complete bathroom architecture integration and technical plumbing.",
    href: "#",
    available: false,
  },
  {
    icon: Droplets,
    title: "Infrastructure Feed",
    description: "Appliance synchronization, sink integration, and technical pipework.",
    href: "#",
    available: false,
  },
  {
    icon: ShieldCheck,
    title: "Pipework Integrity",
    description: "Structural repair and reinforcement of damaged hydraulic pathways.",
    href: "#",
    available: false,
  },
];

const plumbingSteps = [
  {
    icon: "phone" as const,
    number: "01",
    title: "Signal Uplink",
    description: "Transmit your system anomaly or requirements via the secure portal.",
  },
  {
    icon: "search" as const,
    number: "02",
    title: "Engineer Deployment",
    description: "A specialized operative is routed to your coordinates for triage.",
  },
  {
    icon: "wrench" as const,
    number: "03",
    title: "Node Resolution",
    description: "Precision diagnostics and tactical repair of the hydraulic breach.",
  },
  {
    icon: "checkCircle" as const,
    number: "04",
    title: "System Optimized",
    description: "Integrity verification and structural testing before sign-off.",
  },
];

export default function PlumbingCategoryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Hydraulic Engineering"
        subtitle="Uncompromising aqueous infrastructure and rapid-response plumbing architecture."
        breadcrumbs={[
          { label: "Core", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Hydraulic Engineering" },
        ]}
        compact
      />

      {/* Intro */}
      <section className="py-24 border-b border-brand-card-border relative overflow-hidden bg-brand-surface">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-blue/[0.03] blur-[120px] rounded-full pointer-events-none" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-blue/10 bg-brand-blue/5 mb-8 shadow-sm"
          >
            <Activity size={14} className="text-brand-blue" />
            <span className="text-[9px] font-technical font-bold text-brand-blue uppercase tracking-[0.3em]">Operational Flow Active</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase"
          >
            Hydraulic <br />Resolution
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.4em] leading-loose max-w-2xl mx-auto"
          >
            From emergency breaches to structural architecture, DPS Heating Services Ltd provides advanced hydraulic solutions across {COMPANY.areas}. Our engineers are technically equipped for first-visit resolution of critical system failures.
          </motion.p>
        </div>
      </section>

      {/* Urgency technical strip */}
      <section className="py-24 bg-brand-red border-y border-black/10 relative overflow-hidden" aria-label="Urgent hydraulic breach">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center justify-between gap-12 relative z-10">
          <div className="flex items-center gap-8">
            <div className="w-16 h-16 bg-black/20 backdrop-blur-xl rounded-xl flex items-center justify-center border border-white/10 shadow-2xl">
              <Zap size={28} className="text-white animate-pulse" />
            </div>
            <div>
              <h2 className="text-2xl md:text-4xl font-technical font-black text-white tracking-widest uppercase mb-1 drop-shadow-lg">
                Aqueous Breach?
              </h2>
              <p className="text-white/80 text-[9px] font-technical font-bold uppercase tracking-[0.4em]">
                Immediate deployment recommended. Bypassing standard queues now.
              </p>
            </div>
          </div>
          <a
            href={`tel:${COMPANY.phone}`}
            className="group relative bg-white text-black px-12 py-6 rounded-xl font-technical font-black text-[12px] uppercase tracking-[0.3em] overflow-hidden shadow-2xl transition-all hover:scale-105"
          >
            <span className="relative z-10 transition-colors group-hover:text-brand-red flex items-center gap-4">
              <Phone size={18} className="animate-pulse" />
              {COMPANY.phone}
            </span>
          </a>
        </div>
      </section>

      {/* Technical Component Map */}
      <section className="py-40 bg-brand-surface border-b border-brand-card-border relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-blue/[0.03] blur-[120px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div className="space-y-10 order-2 lg:order-1">
              <div>
                <span className="text-brand-blue text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
                  Hydraulic Infrastructure Map
                </span>
                <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase leading-none">
                  Pipe <span className="text-brand-blue">Architecture</span>
                </h2>
              </div>
              <div className="space-y-6">
                {[
                  { label: "Supply Lines", detail: "Cold & hot water distribution network" },
                  { label: "Waste Systems", detail: "Drainage and sewage routing infrastructure" },
                  { label: "Pressure Nodes", detail: "Booster pumps and pressure regulation" },
                  { label: "Valve Matrix", detail: "Isolation, check and gate valve arrays" },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-5 group">
                    <div className="w-1.5 h-1.5 rounded-full bg-brand-blue/40 group-hover:bg-brand-blue mt-1.5 shrink-0 transition-colors" />
                    <div>
                      <p className="text-[10px] font-technical font-extrabold text-brand-text uppercase tracking-widest mb-1">{item.label}</p>
                      <p className="text-[9px] font-technical text-brand-muted uppercase tracking-[0.2em]">{item.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <BlueprintBillboard
                src="/images/radiator-pipes.png"
                alt="Hydraulic pipe infrastructure schematic"
                theme="cool"
                versionText="HYDRAULIC_ARCH: V2.0"
                idHash="SHA: 0xC3F0259F"
                statusText="FLOW ACTIVE"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Services grid */}
      <section className="py-40 border-b border-brand-card-border bg-brand-steel" aria-label="Plumbing service options">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-6">
              <Cpu size={12} className="text-brand-muted" />
              <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.3em]">Module: Flow Architecture</span>
            </div>
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Operational <span className="text-brand-blue">Nodes</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {plumbingServices.map((service, i) => (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`bg-brand-card backdrop-blur-xl rounded-[2.5rem] p-12 border transition-all group relative overflow-hidden hover:shadow-xl hover:shadow-brand-blue/5 ${service.available
                  ? "border-brand-card-border hover:border-brand-blue/20"
                  : "border-brand-card-border opacity-50 grayscale"
                  }`}
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-blue/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-16 h-16 bg-brand-steel border border-brand-card-border rounded-2xl flex items-center justify-center mb-10 group-hover:border-brand-blue/10 transition-all shadow-sm">
                  <service.icon size={28} className="text-brand-blue" />
                </div>

                <h3 className="text-xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                  {service.title}
                </h3>

                <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em] leading-loose mb-10">
                  {service.description}
                </p>

                {service.available ? (
                  <Link
                    href={service.href}
                    className="inline-flex items-center gap-2 text-brand-blue font-technical font-black text-[10px] uppercase tracking-[0.3em] hover:text-brand-text transition-colors"
                  >
                    Initiate Deployment <ArrowRight size={14} />
                  </Link>
                ) : (
                  <span className="text-brand-muted font-technical font-black text-[9px] uppercase tracking-[0.3em]">System Offline</span>
                )}

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-blue/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <ProcessSteps steps={plumbingSteps} title="Operational Protocol" />

      <CTABanner />
    </div>
  );
}
