"use client";

import { Phone, AlertTriangle, Droplets, Volume2, Flame, ShieldAlert, Radio, Activity, Zap, Cpu, Boxes } from "lucide-react";
import QuoteForm from "@/components/ui/QuoteForm";
import { COMPANY } from "@/lib/constants";
import { motion } from "framer-motion";
import Image from "next/image";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const emergencies = [
  {
    icon: Flame,
    title: "Thermal Failure",
    description: "Complete loss of heat generation or hydraulic hot water supply. Critical priority override required.",
  },
  {
    icon: Droplets,
    title: "Catastrophic Leak",
    description: "Uncontrolled water escape causing structural compromise. Requires immediate tactical isolation.",
  },
  {
    icon: Volume2,
    title: "Acoustic Anomaly",
    description: "Severe banging or explosive sounds from the primary boiler unit indicating pressure architecture failure.",
  },
  {
    icon: ShieldAlert,
    title: "Gas Breach",
    description:
      "IMPORTANT: If gas smell detected, isolate supply, open windows, and call National Gas Emergency (0800 111 999) before activating DPS bypass.",
  },
];

export default function EmergencyPage() {
  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      {/* Emergency Hero — Stark, Red/Orange Alert Theme */}
      <section
        className="min-h-[80vh] relative flex items-center justify-center overflow-hidden border-b border-brand-red/20"
        aria-label="Emergency services hero"
      >
        <div className="absolute inset-0 bg-[url('/images/hero-bg.jpg')] opacity-5 grayscale brightness-[0.2] bg-cover bg-center" />

        {/* Pulsing Alert Glows */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand-red/10 blur-[150px] rounded-full animate-pulse-slow pointer-events-none" />
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brand-red/50 to-transparent shadow-[0_0_20px_#DC2626]" />

        {/* Technical Grid */}
        <div
          className="absolute inset-0 z-0 opacity-10 pointer-events-none"
          style={{ backgroundImage: "linear-gradient(rgba(220,38,38,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(220,38,38,0.1) 1px, transparent 1px)", backgroundSize: "40px 40px" }}
        />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center pt-40 pb-24">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="inline-flex items-center gap-3 bg-brand-red/10 border border-brand-red/30 text-brand-red px-6 py-3 rounded-md mb-12 shadow-[0_0_30px_rgba(220,38,38,0.2)]"
          >
            <Radio size={20} className="animate-pulse" />
            <span className="text-xs font-technical font-bold uppercase tracking-[0.4em]">Primary Priority Override</span>
          </motion.div>

          <motion.h1
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-6xl md:text-8xl lg:text-[10rem] font-technical font-black text-brand-text mb-12 tracking-tighter leading-none uppercase"
          >
            Critical <br />
            <span className="text-brand-red drop-shadow-[0_0_30px_rgba(220,38,38,0.6)]">Failure.</span>
          </motion.h1>

          <motion.p
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-sm md:text-md text-brand-muted mb-16 max-w-2xl mx-auto font-technical font-bold uppercase tracking-[0.3em] leading-loose"
          >
            Immediate engineering response required. <br />
            Do not attempt manual bypass. Contact operations center immediately.
          </motion.p>

          <motion.a
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            href={`tel:${COMPANY.phone}`}
            className="group relative inline-flex items-center gap-6 bg-brand-red text-white px-16 py-8 rounded-full font-technical font-extrabold text-2xl transition-all shadow-[0_0_50px_rgba(220,38,38,0.4)] hover:shadow-[0_0_80px_rgba(220,38,38,0.7)] hover:scale-105"
            aria-label={`Emergency call: ${COMPANY.phone}`}
          >
            <AlertTriangle size={36} className="animate-pulse" />
            <span>ACTIVATE HOTLINE</span>
          </motion.a>
        </div>
      </section>

      {/* Holographic Diagnostic Section */}
      <section className="py-32 bg-brand-surface relative overflow-hidden" aria-label="System diagnostics">
        <div className="absolute inset-0 bg-brand-red/10 blur-[80px] rounded-full animate-pulse pointer-events-none" />
        <div className="max-w-4xl mx-auto px-4 relative z-10">
          <div className="text-center mb-12">
            <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
              System Diagnostic View
            </span>
          </div>
          <div className="max-w-2xl mx-auto">
            <BlueprintBillboard
              src="/images/blueprints/radiator-main.jpg"
              alt="Holographic diagnostic view of radiator piping"
              theme="urgent"
              versionText="PRIORITY: OVERRIDE"
              idHash="SHA: 0x34896B48"
              statusText="CRITICAL_FAULT"
              labels={[
                { text: "Pressure Breach", position: { top: "10%", right: "-20%" }, color: "red" },
                { text: "Thermal Runway", position: { bottom: "20%", left: "-20%" }, color: "red" },
              ]}
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* Emergency Classification Grid */}
      <section className="py-48 bg-brand-navy relative z-10" aria-label="Emergency types">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-end gap-12 mb-24">
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-red/20 bg-brand-red/5 mb-6">
                <Activity size={12} className="text-brand-red" />
                <span className="text-[9px] font-technical font-bold text-brand-red uppercase tracking-[0.3em]">Module: Triage</span>
              </div>
              <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">
                Failure Matrix
              </h2>
              <p className="text-brand-muted text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                Identify system anomaly. Bypass portal if matching parameters.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {emergencies.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className={`rounded-[2.5rem] p-12 border backdrop-blur-md transition-all group relative overflow-hidden ${item.title === "Gas Breach"
                  ? "border-brand-red/50 bg-brand-red/5 shadow-[0_0_40px_rgba(220,38,38,0.1)]"
                  : "border-brand-card-border bg-brand-surface hover:border-brand-red/30 shadow-2xl"
                  }`}
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                <div
                  className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-10 border transition-all ${item.title === "Gas Breach"
                    ? "bg-brand-red/20 border-brand-red/50"
                    : "bg-brand-navy border-brand-card-border-hover group-hover:border-brand-red/30"
                    }`}
                >
                  <item.icon
                    size={28}
                    className={item.title === "Gas Breach" ? "text-brand-red animate-pulse" : "text-brand-red"}
                  />
                </div>
                <h3 className="text-2xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                  {item.title}
                </h3>
                <p className={`font-light leading-relaxed text-xs uppercase tracking-widest ${item.title === "Gas Breach" ? "text-brand-red/80 font-bold" : "text-brand-muted"}`}>
                  {item.description}
                </p>

                <span className="absolute -bottom-4 -right-4 text-8xl font-technical font-black text-white/[0.02] pointer-events-none group-hover:text-brand-red/[0.05] transition-colors">
                  0{i + 1}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Deployment Protocol */}
      <section className="py-48 bg-brand-surface border-y border-brand-card-border relative overflow-hidden" aria-label="Emergency response process">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-red/5 blur-[150px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase leading-none">
              Rapid Deployment <br />
              <span className="text-brand-red">Protocol</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-16 relative">
            {/* Connecting line for desktop */}
            <div className="hidden md:block absolute top-[60px] left-32 right-32 h-[1px] bg-brand-red/20 z-0" />

            {[
              { step: "01", title: "SOS Received", desc: "Instant triage and priority assignment via direct audio uplink." },
              { step: "02", title: "Task Dispatched", desc: "Nearest specialized engineer routed with real-time ETA tracking." },
              { step: "03", title: "Restore Integrity", desc: "System made safe, failure isolated, and core functions repaired." },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative z-10 bg-brand-navy rounded-[2.5rem] p-12 border border-brand-card-border text-center shadow-2xl group"
              >
                <div className="w-24 h-24 bg-brand-navy border border-brand-red/30 rounded-full flex items-center justify-center font-technical font-black text-brand-red text-3xl mx-auto mb-10 shadow-[0_0_30px_rgba(220,38,38,0.2)] group-hover:scale-110 transition-transform">
                  {item.step}
                </div>
                <h3 className="text-brand-text text-xl font-technical font-extrabold mb-6 tracking-widest uppercase">{item.title}</h3>
                <p className="text-brand-muted font-light text-[10px] leading-loose uppercase tracking-widest">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Non-Urgent Form */}
      <section className="py-48 bg-brand-navy">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 border border-brand-card-border-hover bg-brand-card px-4 py-2 rounded-full mb-8">
              <Boxes size={14} className="text-brand-muted" />
              <span className="text-[10px] font-technical font-bold text-brand-muted uppercase tracking-[0.4em]">Secondary Intake</span>
            </div>
            <h3 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
              Stable Anomaly?
            </h3>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.4em] leading-relaxed max-w-xl mx-auto">
              If the situation is stable and does not pose an immediate threat, log a standard request via the portal below.
            </p>
          </div>
          <div className="bg-brand-surface border border-brand-card-border rounded-[3rem] p-12 md:p-20 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-blue/5 blur-3xl" />
            <QuoteForm preselectedService="emergency" compact />
          </div>
        </div>
      </section>
    </div>
  );
}
