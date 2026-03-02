"use client";

import { useEffect, useRef } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";

export default function BackgroundBeams() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  const pathLength = useTransform(smoothProgress, [0, 1], [0, 1]);
  const yOffset = useTransform(smoothProgress, [0, 1], [0, 1000]);

  return (
    <div ref={ref} className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-50">
      <div className="absolute inset-0" style={{ maskImage: "radial-gradient(circle at center, black, transparent 80%)", WebkitMaskImage: "radial-gradient(circle at center, black, transparent 80%)" }}>
        <svg width="100%" height="200%" viewBox="0 0 1000 2000" preserveAspectRatio="none" className="absolute top-0 left-0 w-full h-[200vh]">
          {/* Grid lines */}
          <path d="M 200 0 L 200 2000 M 500 0 L 500 2000 M 800 0 L 800 2000" style={{ stroke: "var(--color-brand-card)" }} strokeWidth="1" strokeDasharray="4 4" fill="none" />
          <path d="M 0 500 L 1000 500 M 0 1000 L 1000 1000 M 0 1500 L 1000 1500" style={{ stroke: "var(--color-brand-card)" }} strokeWidth="1" strokeDasharray="4 4" fill="none" />

          {/* Diagonal connecting lines */}
          <path d="M 200 500 L 500 1000 L 800 1500" style={{ stroke: "var(--color-brand-card-hover)" }} strokeWidth="2" strokeDasharray="6 6" fill="none" />
          <path d="M 800 500 L 500 1000 L 200 1500" style={{ stroke: "var(--color-brand-card-hover)" }} strokeWidth="2" strokeDasharray="6 6" fill="none" />

          {/* Glowing Beams */}
          <motion.path
            d="M 200 500 L 500 1000 L 800 1500"
            stroke="#d4af37"
            strokeWidth="3"
            strokeLinecap="round"
            fill="none"
            strokeDasharray="1 1000"
            style={{
              pathLength: pathLength,
              filter: "drop-shadow(0 0 12px #d4af37)"
            }}
          />
          <motion.path
            d="M 800 500 L 500 1000 L 200 1500"
            stroke="#2563EB"
            strokeWidth="3"
            strokeLinecap="round"
            fill="none"
            strokeDasharray="1 1000"
            style={{
              pathLength: pathLength,
              filter: "drop-shadow(0 0 12px #2563EB)"
            }}
          />
        </svg>
      </div>
    </div>
  );
}
