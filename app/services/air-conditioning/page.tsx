"use client";

import { Wind, Snowflake, ArrowRight, Activity, Cpu, ShieldCheck, Thermometer } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ProcessSteps from "@/components/sections/ProcessSteps";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Link from "next/link";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const acServices = [
  {
    icon: Wind,
    title: "AC Installation",
    description: "Supply and installation of air conditioning systems for homes and businesses. All major brands available.",
    href: "/services/air-conditioning/ac-installation",
    available: true,
  },
  {
    icon: Snowflake,
    title: "AC Servicing",
    description: "Annual service to keep your air conditioning running efficiently and extend its lifespan.",
    href: "/services/air-conditioning/ac-servicing",
    available: true,
  },
  {
    icon: Activity,
    title: "AC Repairs",
    description: "Fast diagnosis and repair of air conditioning faults across all makes and models.",
    href: "/services/air-conditioning/ac-repairs",
    available: true,
  },
  {
    icon: Cpu,
    title: "Commercial AC",
    description: "Industrial and commercial air conditioning solutions for offices, retail, and large premises.",
    href: "/services/air-conditioning/commercial-ac",
    available: true,
  },
  {
    icon: ShieldCheck,
    title: "Maintenance Contracts",
    description: "Scheduled maintenance plans to keep your systems running all year round.",
    href: "/services/air-conditioning/ac-maintenance",
    available: true,
  },
];

export default function ACCategoryPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title="Air Conditioning"
        subtitle="Professional air conditioning installation, servicing, and repairs for homes and businesses across London."
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Services", href: "/services" },
          { label: "Air Conditioning" },
        ]}
        backgroundImage="/images/blueprint-ac-exploded.png"
        compact
      />

      {/* Intro Section */}
      <section className="py-32 bg-brand-steel" aria-label="Air conditioning overview">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-8">
                <Cpu size={12} className="text-brand-blue" />
                <span className="text-[9px] font-technical font-bold text-brand-blue uppercase tracking-[0.3em]">F-Gas Certified Engineers</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-8 tracking-tighter uppercase leading-none">
                AC Systems <br />Done Right
              </h2>
              <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose mb-12">
                Whether you need a single-room split system or a full multi-zone installation for a commercial building, our engineers have the experience and qualifications to get the job done properly.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: "Mitsubishi Electric", id: "01" },
                  { label: "Daikin", id: "02" },
                  { label: "LG & Samsung", id: "03" },
                  { label: "Fujitsu & Panasonic", id: "04" },
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
                src="/images/blueprint-ac-exploded.png"
                alt="AC outdoor unit exploded technical diagram"
                theme="cool"
                versionText="AC SYSTEMS"
                idHash="F-GAS CERTIFIED"
                statusText="OPERATIONAL"
                className="w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-40 bg-brand-steel" aria-label="Air conditioning services">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-6">
              <Thermometer size={12} className="text-brand-blue" />
              <span className="text-[9px] font-technical font-bold text-brand-blue uppercase tracking-[0.3em]">All AC Services</span>
            </div>
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Our AC <span className="text-brand-blue">Services</span>
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
                className="bg-brand-card backdrop-blur-xl rounded-[2.5rem] p-12 border border-brand-card-border-hover hover:border-brand-blue/20 transition-all group relative overflow-hidden hover:shadow-xl hover:shadow-brand-blue/5"
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

                <Link
                  href={service.href}
                  className="inline-flex items-center gap-2 text-brand-blue font-technical font-black text-[10px] uppercase tracking-[0.3em] hover:text-brand-text transition-colors"
                >
                  Find Out More <ArrowRight size={14} />
                </Link>

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-blue/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Domestic & Commercial */}
      <section className="py-40 bg-brand-surface border-y border-brand-card-border relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-5" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-24">
            <h2 className="text-3xl md:text-6xl font-technical font-extrabold text-brand-text mb-4 tracking-widest uppercase">
              Domestic &amp; <span className="text-brand-blue">Commercial</span>
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
                We install and service air conditioning systems for homes across London — from a single bedroom unit to whole-house multi-split systems. Quiet, efficient, and professionally fitted.
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
                From offices and retail units to larger commercial premises, we design and install effective air conditioning solutions that keep your staff and customers comfortable.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      <ProcessSteps title="How It Works" dark />

      <CTABanner />
    </div>
  );
}
