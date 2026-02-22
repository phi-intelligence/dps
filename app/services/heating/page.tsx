"use client";

import { Flame, Wrench, Settings, ArrowRight, Phone, ShieldCheck, Activity, Cpu } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ProcessSteps from "@/components/sections/ProcessSteps";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const heatingServices = [
  {
    icon: Wrench,
    title: "Boiler Repair",
    description: "Fast diagnosis and repair of all boiler faults. We aim for first-visit fixes across all major brands.",
    href: "/services/heating/boiler-repair",
    available: true,
  },
  {
    icon: Flame,
    title: "Boiler Installation",
    description: "New boiler supply and installation, including combi, system, and conventional boilers.",
    href: "/services/heating/boiler-installation",
    available: true,
  },
  {
    icon: Settings,
    title: "Boiler Servicing",
    description: "Annual boiler service to keep your system safe, efficient, and warranty compliant.",
    href: "/services/heating/boiler-servicing",
    available: true,
  },
  {
    icon: Flame,
    title: "Central Heating",
    description: "Full central heating system installation and upgrades for homes and commercial properties.",
    href: "/services/heating/central-heating",
    available: true,
  },
  {
    icon: Activity,
    title: "Radiator Services",
    description: "Radiator installation, replacement, balancing, and bleeding across all property types.",
    href: "/services/heating/radiators",
    available: true,
  },
  {
    icon: Cpu,
    title: "Power Flushing",
    description: "Professional power flushing to remove sludge and debris, restoring heating efficiency.",
    href: "/services/heating/power-flushing",
    available: true,
  },
];

export default function HeatingCategoryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Heating Services"
        subtitle="Professional boiler and heating services for homes and businesses across London. Gas Safe registered engineers."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Heating Services" },
        ]}
        backgroundImage="/images/9687b2e0-9aaf-4272-adc5-52162cb88115.jpeg"
        compact
      />

      {/* Intro */}
      <section className="py-24 relative overflow-hidden bg-brand-surface">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-brand-red/5 blur-[120px] rounded-full pointer-events-none" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-red/10 bg-brand-red/5 mb-8 shadow-sm"
          >
            <ShieldCheck size={14} className="text-brand-red" />
            <span className="text-[9px] font-technical font-bold text-brand-red uppercase tracking-[0.3em]">Gas Safe Registered Engineers</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase"
          >
            Heating You <br />Can Trust
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.4em] leading-loose max-w-2xl mx-auto"
          >
            DPS Heating Services Ltd specialises in boiler repair, installation, and servicing, as well as full central heating systems across {COMPANY.areas}. All engineers are Gas Safe registered (Reg: {COMPANY.gasSafeNumber}).
          </motion.p>
        </div>
      </section>

      {/* Technical Component Section */}
      <section className="py-32 bg-brand-steel" aria-label="Heating system components">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-8">
                <Cpu size={12} className="text-brand-muted" />
                <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.3em]">What We Work On</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-8 tracking-tighter uppercase leading-none">
                All Makes &amp; <br />Models
              </h2>
              <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose mb-12">
                Our engineers have hands-on experience with all major boiler brands and heating system types. We carry a wide range of parts to help fix problems on the first visit.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: "Worcester Bosch", id: "01" },
                  { label: "Vaillant", id: "02" },
                  { label: "Baxi", id: "03" },
                  { label: "Ideal & Viessmann", id: "04" },
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
                src="/images/blueprint-commercial-system.png"
                alt="Commercial boiler heating system schematic"
                theme="warm"
                versionText="HEATING SYSTEMS"
                idHash={`GAS SAFE: ${COMPANY.gasSafeNumber}`}
                statusText="GAS SAFE REGISTERED"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-40 bg-brand-steel" aria-label="Heating service options">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Our Heating <span className="text-brand-red">Services</span>
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
                className="bg-brand-navy rounded-[2.5rem] p-10 border border-brand-card-border hover:border-brand-red/30 hover:shadow-2xl transition-all relative overflow-hidden group"
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

                <Link
                  href={service.href}
                  className="inline-flex items-center gap-2 text-brand-red font-technical font-black text-[10px] uppercase tracking-[0.3em] hover:text-brand-text transition-colors"
                >
                  Find Out More <ArrowRight size={14} />
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <ProcessSteps
        title="How We Work"
        subtitle="A straightforward process from your first call to job completion."
      />

      <CTABanner />
    </div>
  );
}
