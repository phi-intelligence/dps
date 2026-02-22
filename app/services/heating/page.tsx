"use client";

import { Flame, Wrench, Settings, ArrowRight, Phone, Cpu, Activity, Zap, ShieldCheck } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ProcessSteps from "@/components/sections/ProcessSteps";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const heatingServices = [
  {
    icon: Wrench,
    title: "Thermodynamic Repair",
    description: "Real-time fault isolation and tactical restoration of heat exchange modules.",
    href: "/services/heating/boiler-repair",
    available: true,
  },
  {
    icon: Flame,
    title: "Core Installation",
    description: "High-integrity boiler replacement and next-gen system architecture deployment.",
    href: "/services/heating/boiler-installation",
    available: true,
  },
  {
    icon: Settings,
    title: "System Certification",
    description: "Exhaustive annual diagnostics and safety compliance verification.",
    href: "/services/heating/boiler-servicing",
    available: true,
  },
  {
    icon: Flame,
    title: "Hydraulic Distribution",
    description: "Centralized heating architecture design and multi-zone installation.",
    href: "#",
    available: false,
  },
  {
    icon: Flame,
    title: "Thermal Output Nodes",
    description: "Radiator integration, pressure balancing, and smart control nodes.",
    href: "#",
    available: false,
  },
  {
    icon: Activity,
    title: "System Cleansing",
    description: "High-pressure power flushing to eliminate structural contamination.",
    href: "#",
    available: false,
  },
];

export default function HeatingCategoryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Thermal Engineering"
        subtitle="Precision-calibrated heating solutions for high-performance residential and commercial infrastructure."
        breadcrumbs={[
          { label: "Core", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Thermal Engineering" },
        ]}
        compact
      />

      {/* Ident/Intro */}
      <section className="py-24 border-b border-brand-card-border relative overflow-hidden bg-brand-surface">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-brand-red/5 blur-[120px] rounded-full pointer-events-none" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-red/10 bg-brand-red/5 mb-8 shadow-sm"
          >
            <ShieldCheck size={14} className="text-brand-red" />
            <span className="text-[9px] font-technical font-bold text-brand-red uppercase tracking-[0.3em]">Gas Safe Certified engineers</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase"
          >
            System <br />Optimization
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.4em] leading-loose max-w-2xl mx-auto"
          >
            DPS Heating Services Ltd specializes in high-integrity thermal architecture. Our Gas Safe operatives (Reg: {COMPANY.gasSafeNumber}) deploy advanced diagnostics to ensure your heating infrastructure maintains peak operational efficiency and structural safety across {COMPANY.areas}.
          </motion.p>
        </div>
      </section>

      {/* Technical Component Map */}
      <section className="py-32 bg-brand-steel" aria-label="Heating system components">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-8">
                <Cpu size={12} className="text-brand-muted" />
                <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.3em]">Module: Diagnostics</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-8 tracking-tighter uppercase leading-none">
                Deep-Layer <br />Architecture
              </h2>
              <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose mb-12">
                We analyze every critical interface within your thermal core. From heat exchange efficiency to electronic control synchronization, our engineers ensure total system integrity.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: "Heat Exchange Unit", id: "01" },
                  { label: "Hydraulic Pump", id: "02" },
                  { label: "Combustion Control", id: "03" },
                  { label: "Exhaust Systems", id: "04" },
                ].map((item) => (
                  <div key={item.id} className="flex items-center gap-4 bg-brand-card backdrop-blur-xl border border-brand-card-border-hover p-5 rounded-xl group hover:border-brand-red/20 transition-all">
                    <span className="text-[10px] font-technical font-black text-brand-red opacity-30 group-hover:opacity-80 transition-opacity">{item.id}</span>
                    <span className="text-[10px] font-technical font-bold uppercase tracking-widest text-brand-text group-hover:text-brand-red transition-colors">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <BlueprintBillboard
                src="/images/blueprints/boiler-main.jpg"
                alt="Exploded boiler schematic"
                theme="warm"
                versionText="MOD: DIAGNOSTIC_V4"
                idHash="SHA: 0xFE441DA6"
                labels={[
                  { text: "Heat Exchange Unit", position: { top: "10%", left: "-20%" }, color: "red" },
                  { text: "Fluid Circulator", position: { bottom: "20%", right: "-20%" }, color: "blue" },
                ]}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Service Selection Grid */}
      <section className="py-40 border-t border-brand-card-border bg-brand-steel" aria-label="Heating service options">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Tactical <span className="text-brand-red">Deployments</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {heatingServices.map((service, i) => (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`bg-brand-navy rounded-[2.5rem] p-10 border transition-all relative overflow-hidden group ${service.available ? "border-brand-card-border hover:border-brand-red/30 hover:shadow-2xl" : "border-brand-card-border opacity-50 grayscale"
                  }`}
              >
                <div className="w-16 h-16 bg-brand-steel border border-brand-card-border rounded-2xl flex items-center justify-center mb-8 group-hover:bg-brand-red/5 group-hover:border-brand-red/10 transition-all shadow-sm">
                  <service.icon size={28} className="text-brand-red" />
                </div>

                <h3 className="text-xl font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
                  {service.title}
                </h3>

                <p className="text-brand-muted text-[10px] uppercase font-technical leading-loose tracking-[0.2em] mb-10">
                  {service.description}
                </p>

                {service.available ? (
                  <Link
                    href={service.href}
                    className="inline-flex items-center gap-2 text-brand-red font-technical font-black text-[10px] uppercase tracking-[0.3em] hover:text-brand-text transition-colors"
                  >
                    Initiate Uplink <ArrowRight size={14} />
                  </Link>
                ) : (
                  <span className="text-brand-muted font-technical font-black text-[9px] uppercase tracking-[0.3em]">Module Pending Deployment</span>
                )}

                {!service.available && (
                  <div className="absolute top-6 right-6">
                    <Zap size={12} className="text-brand-muted opacity-30" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <ProcessSteps
        title="Engineering Protocol"
        subtitle="A high-integrity framework from initial diagnostics to final system verification."
      />

      <CTABanner />
    </div>
  );
}
