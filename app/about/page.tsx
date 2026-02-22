"use client";

import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Shield, Award, Eye, Phone, Cpu, Activity, Zap } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";

const approach = [
  {
    icon: Shield,
    title: "Uncompromising Reliability",
    description: "SLA-driven arrival protocols. Clear communication. Every deployment executed with exact situational precision.",
  },
  {
    icon: Award,
    title: "Certified Engineering",
    description: "Gas Safe registered technicians possessing decades of cumulative infrastructure architecture experience.",
  },
  {
    icon: Eye,
    title: "Total Transparency",
    description: "Zero algorithmic pricing surprises. You receive a structured, fixed quote prior to system initiation.",
  },
];

export default function AboutPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="Engineering Philosophy"
        subtitle="Industrial-grade heating, plumbing and climate control specialists. Protocol-driven execution for absolute reliability."
        breadcrumbs={[{ label: "Core", href: "/" }, { label: "Philosophy" }]}
        compact
      />

      {/* Company Intro */}
      <section className="py-48 relative overflow-hidden">
        {/* Glow Element */}
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
                  Mission Parameters
                </span>
              </motion.div>

              <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text mb-10 tracking-widest leading-none uppercase">
                Precision <br />
                <span className="text-brand-muted/40">Guaranteed.</span>
              </h2>

              <div className="space-y-8 text-brand-muted font-light leading-relaxed text-sm uppercase tracking-wider">
                <p>
                  DPS Heating Services Ltd represents the apex of heating, plumbing and air conditioning
                  engineering across {COMPANY.areas}. We have spent over a decade refining our operational
                  logistics to deliver unparalleled system integrity.
                </p>
                <p>
                  Our certified engineering team specializes in deep infrastructure: boiler installation,
                  complex diagnostics, and comprehensive climate control maintenance. We don't just resolve faults;
                  we optimize systems for peak operational longevity.
                </p>
                <div className="border-l-2 border-brand-red pl-8 text-brand-text font-technical font-bold py-4 my-12 bg-brand-card">
                  <p className="tracking-widest uppercase">Gas Safe Registered ({COMPANY.gasSafeNumber})</p>
                  <p className="text-[10px] text-brand-muted mt-2 font-mono">STATUS: FULLY OPERATIONAL // INSURED</p>
                </div>
              </div>

              <div className="mt-16 grid grid-cols-2 gap-8">
                <div className="bg-brand-navy border border-brand-card-border rounded-[2rem] p-10 text-left relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-brand-red/5 blur-2xl group-hover:bg-brand-red/10 transition-colors" />
                  <p className="text-6xl font-technical font-extrabold text-brand-red mb-4 tracking-tighter">10+</p>
                  <p className="text-[9px] tracking-[0.4em] uppercase text-brand-muted font-bold font-technical">Years Active</p>
                </div>
                <div className="bg-brand-navy border border-brand-card-border rounded-[2rem] p-10 text-left relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-brand-blue/5 blur-2xl group-hover:bg-brand-blue/10 transition-colors" />
                  <p className="text-6xl font-technical font-extrabold text-brand-blue mb-4 tracking-tighter">500+</p>
                  <p className="text-[9px] tracking-[0.4em] uppercase text-brand-muted font-bold font-technical">Deployments</p>
                </div>
              </div>
            </div>

            {/* Darkened Tech Image */}
            <div className="relative h-[700px] rounded-[3rem] overflow-hidden border border-brand-card-border shadow-2xl group">
              <div className="absolute inset-0 bg-gradient-to-t from-brand-navy via-transparent to-transparent z-10" />
              <div className="absolute inset-0 bg-brand-red/5 mix-blend-overlay z-10" />
              <Image
                src="/images/engineer-working.jpg"
                alt="DPS Heating Services engineer working on complex architecture"
                fill
                className="object-cover grayscale contrast-125 brightness-75 group-hover:scale-105 transition-transform duration-1000"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
              <div className="absolute bottom-12 left-12 z-20">
                <div className="inline-flex items-center gap-4 bg-brand-navy/60 backdrop-blur-2xl border border-brand-card-border-hover px-8 py-5 rounded-2xl">
                  <Activity size={20} className="text-brand-red animate-pulse" />
                  <div className="flex flex-col">
                    <span className="text-brand-text text-xs font-technical font-extrabold tracking-widest uppercase">System Alpha-1</span>
                    <span className="text-[9px] text-brand-muted font-mono tracking-widest uppercase mt-1">Status: Monitoring</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Our Approach */}
      <section className="py-48 bg-brand-navy border-y border-brand-card-border relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[600px] bg-brand-blue/5 blur-[180px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Operational <span className="text-brand-red">Matrix</span>
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

      <CTABanner />
    </div>
  );
}
