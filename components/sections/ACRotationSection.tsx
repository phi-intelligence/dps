"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { Snowflake, Flame, Wind } from "lucide-react";
import { registerGSAP, gsap, ScrollTrigger } from "@/components/animations/gsap-init";

const features = [
  { icon: Snowflake, label: "Cooling Mode", description: "Efficient cooling down to 16°C" },
  { icon: Flame, label: "Heating Mode", description: "Reverse cycle heating for winter" },
  { icon: Wind, label: "Fan Only", description: "Circulate air without temperature change" },
];

export default function ACRotationSection() {
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    registerGSAP();
    const el = imgRef.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        { rotateY: 15, scale: 0.95 },
        {
          rotateY: -15,
          scale: 1.05,
          ease: "none",
          scrollTrigger: {
            trigger: el,
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          },
        }
      );
    });

    return () => ctx.revert();
  }, []);

  return (
    <section
      className="py-40 bg-brand-steel overflow-hidden"
      aria-label="Air conditioning unit features"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-24">
          <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-3 block">
            Climate Control
          </span>
          <h2
            className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-8 tracking-widest uppercase"
          >
            Climate Control You Can Rely On
          </h2>
          <p className="text-brand-muted text-sm font-light max-w-xl mx-auto uppercase tracking-[0.2em] leading-loose">
            Modern air conditioning does more than cool — it heats, dehumidifies, and improves your
            air quality year-round.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row items-center gap-12">
          {/* Rotating image */}
          <div className="lg:w-1/2 flex justify-center" style={{ perspective: "1000px" }}>
            <div
              ref={imgRef}
              className="relative w-80 h-80 md:w-[500px] md:h-80 rounded-[3rem] overflow-hidden shadow-2xl border border-brand-card-border"
              style={{ transformStyle: "preserve-3d" }}
            >
              <Image
                src="/images/ac-unit-indoor.jpg"
                alt="Modern air conditioning unit"
                fill
                className="object-cover grayscale brightness-110 contrast-110"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />
              <div className="absolute inset-0 bg-gradient-to-br from-brand-blue/[0.05] to-transparent z-10" />
            </div>
          </div>

          {/* Feature cards */}
          <div className="lg:w-1/2 space-y-6">
            {features.map((feat, i) => (
              <div
                key={feat.label}
                className="flex items-start gap-4 bg-brand-card backdrop-blur-xl rounded-2xl p-6 border border-brand-card-border-hover hover:shadow-xl hover:shadow-brand-blue/5 transition-all duration-500"
              >
                <div className="w-12 h-12 bg-brand-red/5 rounded-xl flex items-center justify-center shrink-0 border border-brand-red/10">
                  <feat.icon size={24} className="text-brand-red" />
                </div>
                <div>
                  <h3
                    className="text-brand-text font-technical font-extrabold uppercase tracking-widest mb-1"
                  >
                    {feat.label}
                  </h3>
                  <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em] font-light">{feat.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
