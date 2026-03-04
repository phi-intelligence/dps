"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { ICON_MAP, IconName } from "@/lib/icons";
import { useRef } from "react";
import ScrollSequenceSection from "@/components/sections/ScrollSequenceSection";

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
  /** Base path for frame images, e.g. "/images/how-we-work-frames/frame". Frames must be named frame-0001.webp, frame-0002.webp, ... */
  frameDir?: string;
  /** Total number of frames (1-based file index). */
  frameCount?: number;
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
  frameDir,
  frameCount = 0,
}: ProcessStepsProps) {
  const containerRef = useRef<HTMLElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"],
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  const count = frameCount > 0 ? frameCount : 0;
  const hasSequence = Boolean(frameDir && count > 0);

  const content = (
    <>
      <div className="text-center mb-12 sm:mb-16 md:mb-24 lg:mb-32 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className={`inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full mb-3 sm:mb-6 md:mb-8 ${
            dark
              ? "border border-[#e2c977]/40 bg-white/10"
              : "border border-brand-red/20 bg-brand-red/5"
          }`}
        >
          <div
            className={`w-1.5 h-1.5 rounded-full animate-pulse ${
              dark ? "bg-[#e2c977]" : "bg-brand-red"
            }`}
          />
          <span
            className={`text-[9px] sm:text-[10px] font-technical font-bold uppercase tracking-[0.35em] sm:tracking-[0.4em] ${
              dark ? "text-[#b8963a]" : "text-brand-red"
            }`}
          >
            Our Process
          </span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className={`text-xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-technical font-extrabold mb-3 sm:mb-6 md:mb-8 tracking-wider uppercase px-1 sm:px-2 ${
            dark ? "text-[#171b1f]" : "text-brand-text"
          }`}
        >
          {title}
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className={`text-[11px] sm:text-sm max-w-2xl mx-auto uppercase tracking-[0.15em] sm:tracking-[0.2em] px-1 sm:px-2 leading-snug ${
            dark ? "text-[#6b737b] font-medium" : "text-brand-muted font-light"
          }`}
        >
          {subtitle}
        </motion.p>
      </div>

      <div className="relative">
        <div
          className={`absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] hidden lg:block ${
            dark ? "bg-[#e2c977]/35" : "bg-brand-card-border"
          }`}
        >
          <motion.div
            className={`absolute top-0 left-0 right-0 origin-top ${
              dark ? "bg-[#e2c977]" : "bg-brand-red"
            }`}
            style={{ height: lineHeight }}
          />
        </div>

        <div className="space-y-8 sm:space-y-12 md:space-y-16 lg:space-y-0 relative z-10">
          {steps.map((step, index) => {
            const Icon = ICON_MAP[step.icon];
            const isEven = index % 2 === 0;

            return (
              <div key={step.number} className="relative lg:flex items-center justify-between lg:h-80">
                <div className={`lg:w-[45%] ${isEven ? "lg:text-right lg:order-1" : "lg:text-left lg:order-2"}`}>
                  <motion.div
                    initial={{ opacity: 0, x: isEven ? -50 : 50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true, margin: "-50px" }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className={`group p-4 sm:p-6 md:p-8 rounded-2xl sm:rounded-3xl backdrop-blur-md border transition-all duration-500 sequence-step-card ${
                      dark
                        ? "bg-white/80 border-[#e0d3b8] hover:border-[#e2c977]/70"
                        : "bg-brand-navy/70 border-brand-card-border hover:border-brand-red/20"
                    }`}
                  >
                    <div className={`flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6 ${isEven ? "lg:flex-row-reverse" : ""}`}>
                      <div
                        className={`w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 shrink-0 rounded-xl sm:rounded-2xl flex items-center justify-center transition-all sequence-step-icon ${
                          dark
                            ? "bg-white border border-[#e0d3b8]/80 group-hover:border-[#e2c977]"
                            : "bg-brand-surface/80 border border-brand-card-border group-hover:border-brand-red/30"
                        }`}
                      >
                        {Icon && (
                          <Icon
                            size={20}
                            className={`sm:w-6 sm:h-6 ${dark ? "text-[#b8963a]" : "text-brand-red"}`}
                          />
                        )}
                      </div>
                      <div className={isEven ? "lg:text-right" : ""}>
                        <p
                          className={`text-[9px] sm:text-[10px] font-technical font-bold uppercase tracking-widest mb-0.5 sm:mb-1 ${
                            dark ? "text-[#b8963a]" : "text-brand-red"
                          }`}
                        >
                          Step {step.number}
                        </p>
                        <h3
                          className={`text-lg sm:text-xl md:text-2xl font-technical font-extrabold tracking-widest uppercase ${
                            dark ? "text-[#171b1f]" : "text-brand-text"
                          }`}
                        >
                          {step.title}
                        </h3>
                      </div>
                    </div>
                    <p
                      className={`text-xs sm:text-sm leading-relaxed uppercase tracking-widest ${
                        dark ? "text-[#6b737b] font-medium" : "text-brand-muted font-light"
                      }`}
                    >
                      {step.description}
                    </p>
                  </motion.div>
                </div>

                <div
                  className={`hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full z-20 items-center justify-center sequence-step-dot ${
                    dark ? "bg-white border-4 border-[#e0d3b8]" : "bg-brand-surface border-4 border-brand-steel"
                  }`}
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className={`w-3 h-3 sm:w-4 sm:h-4 rounded-full ${
                      dark ? "bg-[#e2c977]" : "bg-brand-red"
                    }`}
                  />
                </div>

                <div className={`hidden lg:block lg:w-[45%] ${isEven ? "lg:order-2" : "lg:order-1"}`} />
              </div>
            );
          })}
        </div>
      </div>
    </>
  );

  if (hasSequence) {
    return (
      <ScrollSequenceSection
        ref={containerRef}
        frameDir={frameDir!}
        frameCount={count}
        className={`py-12 sm:py-24 md:py-32 lg:py-40 pl-[max(0.75rem,env(safe-area-inset-left))] pr-[max(0.75rem,env(safe-area-inset-right))] sm:px-4 ${
          dark ? "bg-[#f7f3ea]" : "bg-brand-steel"
        }`}
        contentClassName="max-w-7xl mx-auto relative z-10"
        aria-label={title}
      >
        {content}
      </ScrollSequenceSection>
    );
  }

  return (
    <section
      ref={containerRef}
      className={`relative py-12 sm:py-24 md:py-32 lg:py-40 pl-[max(0.75rem,env(safe-area-inset-left))] pr-[max(0.75rem,env(safe-area-inset-right))] sm:px-4 ${
        dark ? "bg-[#f7f3ea]" : "bg-brand-steel"
      }`}
      aria-label={title}
    >
      {dark && (
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-40 top-0 h-64 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/22 bg-[#e2c977]/8" />
          <div className="absolute -left-40 bottom-0 h-60 w-80 -rotate-6 rounded-[3rem] border border-[#d4af37]/20 bg-[#d4af37]/8" />
          <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#b8963a]/24 to-transparent" />
        </div>
      )}
      <div className="max-w-7xl mx-auto relative z-10">{content}</div>
    </section>
  );
}
