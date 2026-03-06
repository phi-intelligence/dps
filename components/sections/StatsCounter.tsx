"use client";

import { useEffect, useRef } from "react";
import { registerGSAP, gsap, ScrollTrigger } from "@/components/animations/gsap-init";

const stats = [
  { value: 1000, suffix: "+", label: "Jobs Completed" },
  { value: 13, suffix: "+", label: "Years Experience" },
  { value: 5, suffix: "★", label: "Customer Rating" },
  { value: 100, suffix: "%", label: "Gas Safe Registered" },
];

export default function StatsCounter() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    registerGSAP();
    const el = containerRef.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      const counters = el.querySelectorAll<HTMLSpanElement>(".counter-num");
      counters.forEach((counter, i) => {
        const target = stats[i].value;
        const obj = { val: 0 };

        ScrollTrigger.create({
          trigger: counter,
          start: "top 85%",
          once: true,
          onEnter: () => {
            gsap.to(obj, {
              val: target,
              duration: 2.5,
              ease: "expo.out",
              onUpdate: () => {
                counter.textContent = Math.floor(obj.val).toString();
              },
            });
          },
        });
      });
    });

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="grid grid-cols-2 lg:grid-cols-4 gap-12">
      {stats.map((stat) => (
        <div key={stat.label} className="relative group">
          <div className="absolute -top-4 -left-4 w-8 h-8 border-t border-l border-brand-red/10 pointer-events-none group-hover:border-brand-red/30 transition-colors" />

          <div className="text-5xl font-technical font-extrabold text-brand-text mb-4 tracking-tighter flex items-center justify-center lg:justify-start">
            <span className="counter-num text-brand-red">0</span>
            <span className="text-brand-muted opacity-30 ml-1">{stat.suffix}</span>
          </div>

          <p className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-brand-muted group-hover:text-brand-text transition-colors text-center lg:text-left">
            {stat.label}
          </p>

          <div className="mt-4 h-[1px] w-12 bg-brand-card-border group-hover:w-full group-hover:bg-brand-red/20 transition-all duration-700" />
        </div>
      ))}
    </div>
  );
}
