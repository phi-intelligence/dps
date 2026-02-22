"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { ICON_MAP, IconName } from "@/lib/icons";
import { useRef } from "react";

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
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"],
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <section
      ref={containerRef}
      className={`py-40 px-4 overflow-hidden ${dark ? "bg-brand-surface" : "bg-brand-steel"}`}
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
          {/* Central Vertical Line */}
          <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] bg-brand-card-border hidden lg:block">
            <motion.div
              className="absolute top-0 left-0 right-0 bg-brand-gradient origin-top"
              style={{ height: lineHeight }}
            />
          </div>

          <div className="space-y-24 lg:space-y-0 relative z-10">
            {steps.map((step, index) => {
              const Icon = ICON_MAP[step.icon];
              const isEven = index % 2 === 0;

              return (
                <div key={step.number} className="relative lg:flex items-center justify-between lg:h-80">
                  {/* Content Container */}
                  <div className={`lg:w-[45%] ${isEven ? "lg:text-right lg:order-1" : "lg:text-left lg:order-2"}`}>
                    <motion.div
                      initial={{ opacity: 0, x: isEven ? -50 : 50 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true, margin: "-100px" }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                      className="group p-8 rounded-3xl bg-brand-navy/30 border border-brand-card-border hover:border-brand-red/20 transition-all duration-500 premium-shadow"
                    >
                      <div className={`flex items-center gap-4 mb-6 ${isEven ? "lg:flex-row-reverse" : ""}`}>
                        <div className="w-16 h-16 shrink-0 bg-brand-surface border border-brand-card-border rounded-2xl flex items-center justify-center group-hover:border-brand-red/30 transition-all">
                          {Icon && <Icon size={24} className="text-brand-red" />}
                        </div>
                        <div className={isEven ? "lg:text-right" : ""}>
                          <p className="text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-1">Step {step.number}</p>
                          <h3 className="text-2xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
                            {step.title}
                          </h3>
                        </div>
                      </div>
                      <p className="text-sm leading-relaxed text-brand-muted font-light uppercase tracking-widest">
                        {step.description}
                      </p>
                    </motion.div>
                  </div>

                  {/* Circle Indicator on the line */}
                  <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-12 h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.2 }}
                      className="w-4 h-4 rounded-full bg-brand-red shadow-[0_0_15px_rgba(239,68,68,0.5)]"
                    />
                  </div>

                  {/* Empty space for alternating layout */}
                  <div className={`hidden lg:block lg:w-[45%] ${isEven ? "lg:order-2" : "lg:order-1"}`} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
