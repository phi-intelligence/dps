"use client";

import { motion } from "framer-motion";
import { ICON_MAP, IconName } from "@/lib/icons";

export interface ProcessStep {
  icon: IconName;
  number: string;
  title: string;
  description: string;
}

interface ProcessStepsProps {
  steps?: ProcessStep[];
  title?: string;
  subtitle?: string;
  dark?: boolean;
}

const defaultSteps: ProcessStep[] = [
  {
    icon: "phone",
    number: "01",
    title: "Get in Touch",
    description: "Call us or fill in our online form. Tell us what you need and we will get back to you promptly.",
  },
  {
    icon: "search",
    number: "02",
    title: "Free Quote",
    description: "We assess the job and provide a clear, no-obligation quote before any work begins.",
  },
  {
    icon: "wrench",
    number: "03",
    title: "Work Carried Out",
    description: "Our qualified engineers complete the job efficiently and to a high standard.",
  },
  {
    icon: "checkCircle",
    number: "04",
    title: "Job Complete",
    description: "Everything is tested and signed off. You receive all relevant documentation.",
  },
];

export default function ProcessSteps({
  steps = defaultSteps,
  title = "How We Work",
  subtitle = "Simple, straightforward service from first contact to job completion.",
  dark = false,
}: ProcessStepsProps) {
  return (
    <section
      className={`py-40 px-4 ${dark ? "bg-brand-surface" : "bg-brand-steel"}`}
      aria-label={title}
    >
      <div className="max-w-7xl mx-auto relative">
        <div className="text-center mb-32 relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-brand-red/20 bg-brand-red/5 mb-8"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse" />
            <span className="text-[10px] font-technical font-bold uppercase tracking-[0.4em] text-brand-red">
              Our Process
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-6xl font-technical font-extrabold mb-8 text-brand-text tracking-wider uppercase"
          >
            {title}
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-brand-muted text-sm font-light max-w-2xl mx-auto uppercase tracking-[0.2em]"
          >
            {subtitle}
          </motion.p>
        </div>

        <div className="relative">
          {/* Technical Connecting Line */}
          <div className="hidden lg:block absolute top-[4.5rem] left-[10%] right-[10%] h-[1px] bg-brand-card-border z-0">
            <motion.div
              className="h-full bg-gradient-to-r from-brand-red via-brand-purple to-brand-blue origin-left"
              initial={{ scaleX: 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 2, ease: "circOut", delay: 0.2 }}
              style={{ boxShadow: "0 0 12px rgba(220,38,38,0.4), 0 0 24px rgba(37,99,235,0.2)" }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-16 relative z-10">
            {steps.map((step, index) => {
              const Icon = ICON_MAP[step.icon];
              return (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.2, duration: 0.5 }}
                  className="relative text-center group"
                >
                  <div className="relative z-10 w-24 h-24 mx-auto mb-10 bg-brand-navy border border-brand-card-border rounded-[2rem] flex items-center justify-center group-hover:border-brand-red/20 transition-all duration-500">
                    <div className="absolute inset-0 bg-gradient-to-br from-brand-red/5 to-transparent rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity" />
                    {Icon && <Icon size={32} className="text-brand-muted group-hover:text-brand-red transition-all duration-500 relative z-10" />}

                    {/* Phase Number Overlay */}
                    <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-brand-surface border border-brand-card-border-hover flex items-center justify-center text-[10px] font-technical font-bold text-brand-red">
                      {step.number}
                    </div>
                  </div>

                  <h3 className="text-xl font-technical font-extrabold mb-4 text-brand-text tracking-widest uppercase">
                    {step.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-brand-muted font-light px-4 uppercase tracking-widest">
                    {step.description}
                  </p>

                  {/* Background index number */}
                  <span className="absolute top-0 left-1/2 -translate-x-1/2 text-[8rem] font-technical font-black text-white/[0.02] pointer-events-none -z-10 group-hover:text-brand-red/[0.03] transition-colors">
                    {step.number}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
