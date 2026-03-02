"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { useRef } from "react";
import { Wrench, Zap, Flame, LucideIcon } from "lucide-react";
import ScrollSequenceSection from "@/components/sections/ScrollSequenceSection";
import { CAPABILITY_CORE_SERVICES, CORE_SERVICES_IMAGES, CORE_SERVICE_HREFS } from "@/lib/constants";

const SERVICE_ICONS: Record<string, LucideIcon> = {
  "Mechanical Services": Wrench,
  "Electrical Services": Zap,
  "Gas Services": Flame,
};

interface CoreServicesSectionProps {
  title?: string;
  subtitle?: string;
  dark?: boolean;
  frameDir?: string;
  frameCount?: number;
}

export default function CoreServicesSection({
  title = "Our Core Services",
  subtitle = "Mechanical, electrical, and gas solutions — installation, maintenance, and compliance across commercial and domestic projects.",
  dark = true,
  frameDir = "/images/how-we-work-frames/frame",
  frameCount = 145,
}: CoreServicesSectionProps) {
  const containerRef = useRef<HTMLElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"],
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  const hasSequence = Boolean(frameDir && frameCount > 0);

  const content = (
    <>
      <div className="relative pt-12 sm:pt-16 md:pt-24">
        <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[2px] bg-brand-card-border hidden lg:block">
          <motion.div
            className="absolute top-0 left-0 right-0 bg-brand-red origin-top"
            style={{ height: lineHeight }}
          />
        </div>

        <div className="space-y-8 sm:space-y-12 md:space-y-16 lg:space-y-0 relative z-10">
          {CAPABILITY_CORE_SERVICES.map((service, index) => {
            const Icon = SERVICE_ICONS[service.title];
            const isEven = index % 2 === 0;
            const imageSrc = CORE_SERVICES_IMAGES[service.title];
            const href = CORE_SERVICE_HREFS[service.title];

            return (
              <div key={service.title} className="relative lg:flex items-center justify-between lg:min-h-[320px]">
                <div className={`lg:w-[45%] ${isEven ? "lg:order-1" : "lg:order-2"}`}>
                  <Link href={href ?? "/services"} className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-red focus-visible:ring-offset-2 focus-visible:ring-offset-brand-surface rounded-2xl sm:rounded-3xl">
                    <motion.div
                      initial={{ opacity: 0, x: isEven ? -50 : 50 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true, margin: "-50px" }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                      className="group rounded-2xl sm:rounded-3xl overflow-hidden border border-brand-card-border bg-brand-navy/70 backdrop-blur-md hover:border-brand-red/20 transition-all duration-500 sequence-step-card"
                    >
                    {imageSrc && (
                      <div className="relative aspect-[16/9] w-full">
                        <Image
                          src={imageSrc}
                          alt={service.title}
                          fill
                          className="object-cover"
                          sizes="(max-width: 1024px) 100vw, 45vw"
                        />
                      </div>
                    )}
                    <div className="p-4 sm:p-6 md:p-8">
                      <div className="flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 shrink-0 bg-brand-surface/80 border border-brand-card-border rounded-xl sm:rounded-2xl flex items-center justify-center group-hover:border-brand-red/30 transition-all sequence-step-icon">
                          {Icon && <Icon size={20} className="sm:w-6 sm:h-6 text-brand-red" />}
                        </div>
                        <h3 className="text-lg sm:text-xl md:text-2xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
                          {service.title}
                        </h3>
                      </div>
                      <ul className="space-y-2 sm:space-y-3">
                        {service.items.map((item) => (
                          <li
                            key={item}
                            className="flex items-start gap-2 text-xs sm:text-sm text-brand-muted font-light uppercase tracking-widest leading-snug"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-red/60 shrink-0 mt-1.5" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                  </Link>
                </div>

                <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-brand-surface border-4 border-brand-steel z-20 items-center justify-center sequence-step-dot">
                  <motion.div
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-brand-red"
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
        frameDir={frameDir}
        frameCount={frameCount}
        className={`py-12 sm:py-24 md:py-32 lg:py-40 pl-[max(0.75rem,env(safe-area-inset-left))] pr-[max(0.75rem,env(safe-area-inset-right))] sm:px-4 ${dark ? "bg-brand-surface" : "bg-brand-steel"}`}
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
      className={`relative py-12 sm:py-24 md:py-32 lg:py-40 pl-[max(0.75rem,env(safe-area-inset-left))] pr-[max(0.75rem,env(safe-area-inset-right))] sm:px-4 ${dark ? "bg-brand-surface" : "bg-brand-steel"}`}
      aria-label={title}
    >
      <div className="max-w-7xl mx-auto relative z-10">{content}</div>
    </section>
  );
}
