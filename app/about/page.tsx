"use client";

import Image from "next/image";
import Link from "next/link";
import { Shield, Award, Eye, Phone, Cpu } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";

const approach = [
  {
    icon: Shield,
    title: "Reliability You Can Count On",
    description: "We arrive on time, communicate clearly, and complete every job to a high standard — no exceptions.",
  },
  {
    icon: Award,
    title: "Fully Qualified Engineers",
    description: "Gas Safe registered engineers with years of hands-on experience across all makes and models.",
  },
  {
    icon: Eye,
    title: "Honest, Transparent Pricing",
    description: "You receive a clear, fixed quote before any work begins. No hidden charges, no surprises.",
  },
];

export default function AboutPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="About Us"
        subtitle="DPS Heating Services Ltd — professional heating and air conditioning engineers serving London and the surrounding areas."
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "About Us" }]}
        backgroundImage="/images/76d6f0b9-2287-4edd-a9d8-cd30b63806ee.jpeg"
        compact
      />

      {/* Company Intro */}
      <section className="py-48 relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-[600px] h-[600px] bg-brand-red/5 blur-[200px] rounded-full -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-32 items-center">
            <div>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="inline-flex items-center gap-2 border border-brand-red/20 bg-brand-red/5 backdrop-blur-md rounded-md px-5 py-2 mb-10"
              >
                <Cpu size={14} className="text-brand-red" />
                <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Gas Safe Registered
                </span>
              </motion.div>

              <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text mb-10 tracking-widest leading-none uppercase">
                Who We <br />
                <span className="text-brand-muted/40">Are.</span>
              </h2>

              <div className="space-y-8 text-brand-muted font-light leading-relaxed text-sm uppercase tracking-wider">
                <p>
                  DPS Heating Services Ltd is a professional heating and air conditioning company
                  serving {COMPANY.areas}. With over a decade of experience, we provide reliable,
                  high-quality services to both domestic and commercial customers.
                </p>
                <p>
                  Our team specialises in boiler installation, repair and servicing, central heating
                  systems, and air conditioning — ensuring your home or business stays comfortable
                  all year round.
                </p>
                <div className="border-l-2 border-brand-red pl-8 text-brand-text font-technical font-bold py-4 my-12 bg-brand-card">
                  <p className="tracking-widest uppercase">Gas Safe Registered ({COMPANY.gasSafeNumber})</p>
                  <p className="text-[10px] text-brand-muted mt-2 font-mono">FULLY INSURED // QUALIFIED ENGINEERS</p>
                </div>
              </div>

              <div className="mt-16 grid grid-cols-2 gap-8">
                <div className="bg-brand-navy border border-brand-card-border rounded-[2rem] p-10 text-left relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-brand-red/5 blur-2xl group-hover:bg-brand-red/10 transition-colors" />
                  <p className="text-6xl font-technical font-extrabold text-brand-red mb-4 tracking-tighter">10+</p>
                  <p className="text-[9px] tracking-[0.4em] uppercase text-brand-muted font-bold font-technical">Years Experience</p>
                </div>
                <div className="bg-brand-navy border border-brand-card-border rounded-[2rem] p-10 text-left relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-brand-blue/5 blur-2xl group-hover:bg-brand-blue/10 transition-colors" />
                  <p className="text-6xl font-technical font-extrabold text-brand-blue mb-4 tracking-tighter">500+</p>
                  <p className="text-[9px] tracking-[0.4em] uppercase text-brand-muted font-bold font-technical">Jobs Completed</p>
                </div>
              </div>
            </div>

            {/* Engineering Schematic */}
            <BlueprintBillboard
              src="/images/blueprint-boiler-exploded.png"
              alt="DPS Heating Services — boiler system exploded diagram"
              theme="tech"
              versionText="GAS SAFE REGISTERED"
              idHash={`REG: ${COMPANY.gasSafeNumber}`}
              statusText="OPERATIONAL"
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* Our Approach */}
      <section className="py-48 bg-brand-navy relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[600px] bg-brand-blue/5 blur-[180px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              The <span className="text-brand-red">DPS Promise</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {approach.map((item, i) => (
              <div key={item.title} className="bg-brand-surface rounded-[2.5rem] p-12 text-center border border-brand-card-border shadow-2xl hover:border-brand-red/30 transition-all duration-500 group relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="w-24 h-24 bg-brand-navy border border-brand-card-border rounded-3xl flex items-center justify-center mx-auto mb-10 group-hover:bg-brand-red/10 group-hover:border-brand-red/30 transition-all duration-500 relative">
                  <item.icon size={40} className="text-brand-text/20 group-hover:text-brand-red transition-all duration-500 relative z-10" />
                </div>
                <h3 className="text-xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className="text-brand-muted text-xs leading-relaxed font-light uppercase tracking-wider">
                  {item.description}
                </p>

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-red/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Engineers at Work Photo Section */}
      <section className="py-48 bg-brand-surface overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-24"
          >
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
              Our Engineers
            </span>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Experienced. <span className="text-brand-muted/40">Qualified.</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative overflow-hidden rounded-3xl border border-brand-card-border group"
            >
              <Image
                src="/images/engineers-at-work.png"
                alt="DPS engineers working on commercial heating installation"
                width={600}
                height={450}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black/70 to-transparent">
                <p className="text-white text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Commercial Heating Installation
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative overflow-hidden rounded-3xl border border-brand-card-border group"
            >
              <Image
                src="/images/9687b2e0-9aaf-4272-adc5-52162cb88115.jpeg"
                alt="DPS engineer team installing copper heating pipework"
                width={600}
                height={450}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black/70 to-transparent">
                <p className="text-white text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Central Heating Pipework
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <CTABanner
        title="Get in Touch"
        subtitle="Ready to book a service or get a free quote? Call us today or use our online form."
      />
    </div>
  );
}
