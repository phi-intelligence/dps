"use client";

import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  Flame,
  Droplets,
  Wind,
  Phone,
  ArrowRight,
  Zap,
  Shield,
  Clock,
  Star,
} from "lucide-react";
import TrustBar from "@/components/ui/TrustBar";
import ServiceCard from "@/components/ui/ServiceCard";
import ReviewCard from "@/components/ui/ReviewCard";
import CTABanner from "@/components/ui/CTABanner";
import StatsCounter from "@/components/sections/StatsCounter";
import ProcessSteps from "@/components/sections/ProcessSteps";
import SystemArchitecture from "@/components/sections/SystemArchitecture";
import ThermalBackground from "@/components/animations/ThermalBackground";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, REVIEWS } from "@/lib/constants";
import { registerGSAP, gsap } from "@/components/animations/gsap-init";

const services = [
  {
    icon: Flame,
    title: "Heating",
    description: "Expert boiler and heating system services for domestic and commercial properties.",
    subservices: ["Boiler Repair", "Boiler Installation", "Boiler Servicing"],
    href: "/services/heating",
  },
  {
    icon: Droplets,
    title: "Plumbing",
    description: "Fast, reliable plumbing repairs and installations across the region.",
    subservices: ["Plumbing Repairs", "General Plumbing", "Leak Repairs"],
    href: "/services/plumbing",
  },
  {
    icon: Wind,
    title: "Air Conditioning",
    description: "Professional AC installation and servicing for homes and businesses.",
    subservices: ["AC Installation", "AC Servicing", "Commercial AC"],
    href: "/services/air-conditioning",
  },
];

const trustPoints = [
  {
    icon: Zap,
    title: "Fast Response",
    description: "We respond quickly and aim for same-day appointments for urgent work.",
  },
  {
    icon: Shield,
    title: "Qualified Engineers",
    description: "All engineers are Gas Safe registered and fully trained.",
  },
  {
    icon: Star,
    title: "Clean & Tidy Work",
    description: "We respect your home — always leaving the work area clean.",
  },
  {
    icon: Clock,
    title: "Transparent Pricing",
    description: "Clear quotes upfront — no hidden charges, ever.",
  },
];

export default function HomePage() {
  useEffect(() => {
    registerGSAP();
  }, []);

  return (
    <div className="bg-brand-surface text-brand-text overflow-hidden relative">
      <ThermalBackground />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-32 pb-20 bg-brand-surface" aria-label="Hero">
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center gap-2 border border-brand-red/10 bg-brand-red/5 backdrop-blur-md rounded-full px-4 py-1.5 mb-8"
              >
                <div className="w-2 h-2 rounded-full bg-brand-red animate-pulse" />
                <span className="text-brand-red text-sm font-technical tracking-widest uppercase">
                  Gas Safe Registered // {COMPANY.areas}
                </span>
              </motion.div>

              <div className="flex items-center gap-5 mb-6">
                <Image
                  src="/images/logo.jpg"
                  alt="DPS Heating Services"
                  width={80}
                  height={80}
                  className="rounded-2xl shadow-lg shadow-brand-red/10"
                />
                <h1 className="text-6xl md:text-8xl font-technical font-bold text-brand-text leading-[1.05] tracking-tighter uppercase glow-text">
                  DPS<br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-red via-brand-purple to-brand-blue animate-gradient-x">
                    Heating.
                  </span>
                </h1>
              </div>

              <p className="text-xl md:text-2xl text-brand-muted mb-10 max-w-xl leading-relaxed font-light uppercase tracking-wider">
                Professional heating, plumbing &amp; air conditioning services across {COMPANY.areas}. Gas Safe registered engineers you can trust.
              </p>

              <div className="flex flex-col sm:flex-row gap-5">
                <Link
                  href="/contact"
                  className="group relative inline-flex items-center justify-center gap-2 bg-brand-red text-white px-8 py-4 rounded-full font-bold text-lg transition-all hover:bg-brand-red/80 overflow-hidden shadow-xl shadow-brand-red/20"
                >
                  <span className="relative z-10">Deploy Service</span>
                  <ArrowRight size={20} className="relative z-10 group-hover:translate-x-1 transition-transform" />
                  <div className="absolute inset-0 bg-brand-card-hover scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
                </Link>
                <a
                  href={`tel:${COMPANY.phone}`}
                  className="inline-flex items-center justify-center gap-2 bg-transparent border border-brand-card-border-hover hover:border-brand-blue/50 hover:bg-brand-blue/5 text-brand-text px-8 py-4 rounded-full font-technical font-bold text-base tracking-widest uppercase transition-all"
                >
                  <Phone size={18} className="text-brand-blue" />
                  Request Uplink
                </a>
              </div>
            </motion.div>

            {/* Right Column: Blueprint Schematic 2.0 */}
            {/* Right Column: Blueprint Schematic 2.0 Billboard */}
            <BlueprintBillboard
              src="/images/hero-blueprint.jpg"
              alt="Tactical Boiler Infrastructure Schematic"
              theme="cool"
              versionText="CORE_ANALYSIS: V2.4"
              idHash="ID_HASH: 0x7C1864DF"
              statusText="OPERATIONAL"
              className="w-full"
            />
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 hidden md:block"
          aria-hidden="true"
        >
          <div className="w-5 h-8 border border-brand-card-border-hover rounded-full flex items-start justify-center pt-2">
            <motion.div
              animate={{ y: [0, 10, 0], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-1 h-1 bg-brand-red rounded-full shadow-[0_0_8px_rgba(220,38,38,0.5)]"
            />
          </div>
        </motion.div>
      </section>

      {/* Trust Bar - Floating Glassmorphism */}
      <div className="relative z-20 -mt-10 px-4">
        <div className="max-w-6xl mx-auto glass-panel rounded-2xl p-2 shadow-2xl shadow-brand-red/5">
          <TrustBar />
        </div>
      </div>

      {/* Services Overview */}
      <section className="py-48 relative z-10 bg-brand-steel" aria-label="Services overview">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-24 text-center"
          >
            <span className="text-brand-red text-sm font-bold uppercase tracking-[0.4em] mb-4 block">
              Core Capabilities
            </span>
            <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Operational <span className="text-brand-red">Excellence</span>
            </h2>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {services.map((service, i) => (
              <ServiceCard key={service.title} {...service} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* System Architecture — Holographic Exploded View */}
      <SystemArchitecture />

      {/* Process Steps */}
      <ProcessSteps
        title="Autonomous Logistics."
        subtitle="We streamline your service requests with precision routing and real-time fault tracking."
        dark
      />

      {/* Why Choose DPS */}
      <section className="py-48 bg-brand-steel border-t border-brand-card-border relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-brand-red/5 rounded-full blur-[150px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-40"
          >
            <h2 className="text-4xl md:text-7xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase">
              System <span className="text-brand-red">Architecture</span>
            </h2>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.6em]">
              High-Perfomance Thermal Engineering
            </p>
          </motion.div>

          <div className="mb-48">
            <StatsCounter />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-16">
            {trustPoints.map((point, i) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="group relative"
              >
                <div className="relative z-10">
                  <div className="w-16 h-16 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-red/20 group-hover:bg-brand-red/5 transition-all duration-500">
                    <point.icon size={28} className="text-brand-red group-hover:scale-110 transition-transform" />
                  </div>
                  <h3 className="text-brand-text text-lg font-technical font-extrabold mb-4 tracking-widest uppercase">{point.title}</h3>
                  <p className="text-brand-muted text-[10px] font-technical leading-relaxed uppercase tracking-widest">{point.description}</p>
                </div>

                {/* Background number */}
                <span className="absolute -top-6 -left-4 text-7xl font-technical font-black text-white/[0.02] group-hover:text-brand-red/[0.04] transition-colors pointer-events-none">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <CTABanner
        title="Start Your Journey"
        subtitle={`Experience the future of intelligent home services today. Our engineers are ready.`}
      />
    </div>
  );
}
