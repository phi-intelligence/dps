"use client";

import { Wind, Snowflake, ArrowRight, Activity, Cpu, Zap, ShieldCheck, Thermometer } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ProcessSteps from "@/components/sections/ProcessSteps";
import ACRotationSection from "@/components/sections/ACRotationSection";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const acServices = [
  {
    icon: Wind,
    title: "Primary Installation",
    description: "Full-scale climate control architecture deployment for domestic and commercial sectors.",
    href: "/services/air-conditioning/ac-installation",
    available: true,
  },
  {
    icon: Snowflake,
    title: "Thermal Optimization",
    description: "Precision annual calibration to maintain system equilibrium and operational longevity.",
    href: "/services/air-conditioning/ac-servicing",
    available: true,
  },
  {
    icon: Activity,
    title: "Diagnostic Repair",
    description: "Rapid fault isolation and tactical restoration of climate management modules.",
    href: "#",
    available: false,
  },
  {
    icon: Cpu,
    title: "Structural AC",
    description: "Industrial-grade climate control systems designed for complex commercial environments.",
    href: "#",
    available: false,
  },
  {
    icon: ShieldCheck,
    title: "Sustained Maintenance",
    description: "Continuous integrity monitoring and tactical support contracts for critical systems.",
    href: "#",
    available: false,
  },
];

export default function ACCategoryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Climate Engineering"
        subtitle="Uncompromising thermal management and high-precision air conditioning architecture."
        breadcrumbs={[
          { label: "Core", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Climate Engineering" },
        ]}
        compact
      />

      {/* Technical Component Map - Ported from Heating style */}
      <section className="py-32 bg-brand-steel" aria-label="AC system architecture">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-8">
                <Cpu size={12} className="text-brand-blue" />
                <span className="text-[9px] font-technical font-bold text-brand-blue uppercase tracking-[0.3em]">Module: Climate Matrix</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-8 tracking-tighter uppercase leading-none">
                Precision <br />Cooling Core
              </h2>
              <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose mb-12">
                Our AC infrastructure utilizes multi-stage compression and intelligent thermal feedback nodes to maintain precise climate equilibrium in any environment.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: "Variable Compressor", id: "01" },
                  { label: "Evaporator Array", id: "02" },
                  { label: "Thermal Sensor Node", id: "03" },
                  { label: "High-Flow Fan", id: "04" },
                ].map((item) => (
                  <div key={item.id} className="flex items-center gap-4 bg-brand-card backdrop-blur-xl border border-brand-card-border-hover p-5 rounded-xl group hover:border-brand-blue/20 transition-all">
                    <span className="text-[10px] font-technical font-black text-brand-blue opacity-30 group-hover:opacity-80 transition-opacity">{item.id}</span>
                    <span className="text-[10px] font-technical font-bold uppercase tracking-widest text-brand-text group-hover:text-brand-blue transition-colors">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <BlueprintBillboard
                src="/images/blueprints/ac-main.jpg"
                alt="Exploded AC schematic"
                theme="cool"
                versionText="MOD: CLIMATE_V2"
                idHash="SHA: 0xA4FA627F"
                labels={[
                  { text: "Intake Fan", position: { top: "5%", right: "-10%" }, color: "blue" },
                  { text: "Thermal Interface", position: { bottom: "15%", left: "-15%" }, color: "purple" },
                ]}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-40 bg-brand-steel" aria-label="AC services">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-6">
              <Thermometer size={12} className="text-brand-blue" />
              <span className="text-[9px] font-technical font-bold text-brand-blue uppercase tracking-[0.3em]">Module: Thermal Equilibrium</span>
            </div>
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Management <span className="text-brand-blue">Nodes</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {acServices.map((service, i) => (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`bg-brand-card backdrop-blur-xl rounded-[2.5rem] p-12 border transition-all group relative overflow-hidden hover:shadow-xl hover:shadow-brand-blue/5 ${service.available ? "border-brand-card-border-hover hover:border-brand-blue/20" : "border-brand-card-border opacity-50 grayscale"
                  }`}
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-blue/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-16 h-16 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center justify-center mb-10 group-hover:border-brand-blue/10 transition-all">
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
                  <span className="text-brand-muted font-technical font-black text-[9px] uppercase tracking-[0.3em]">Offline Module</span>
                )}

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-blue/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Sector Specialization */}
      <section className="py-40 bg-brand-surface border-y border-brand-card-border relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-5" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-24">
            <h2 className="text-3xl md:text-6xl font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
              Sector <span className="text-brand-blue">Specialization</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-brand-navy rounded-[3rem] p-16 border border-brand-card-border shadow-2xl relative overflow-hidden group"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-brand-blue/5 blur-[100px]" />
              <h3 className="text-2xl md:text-4xl font-technical font-black text-brand-text mb-8 tracking-tighter uppercase">Domestic</h3>
              <p className="text-brand-muted text-xs font-technical uppercase tracking-[0.2em] leading-loose">
                Architectural climate control for the modern residence. We deploy high-efficiency split systems engineered for precise thermal equilibrium and minimal acoustic signature.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-brand-steel rounded-[3rem] p-16 border border-brand-blue/10 shadow-2xl relative overflow-hidden group"
            >
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-brand-blue/5 blur-[100px]" />
              <h3 className="text-2xl md:text-4xl font-technical font-black text-brand-text mb-8 tracking-tighter uppercase">Commercial</h3>
              <p className="text-brand-muted text-xs font-technical uppercase tracking-[0.2em] leading-loose">
                Enterprise-grade thermal management for corporate, retail, and industrial infrastructure. Our engineering team designs high-capacity architecture for sustained operational cooling.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      <ProcessSteps title="Operational Protocol" dark />

      <CTABanner />
    </div>
  );
}
