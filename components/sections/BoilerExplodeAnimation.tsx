"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { registerGSAP, gsap } from "@/components/animations/gsap-init";

const layers = [
  {
    id: "casing",
    label: "Main Logic",
    description: "Central processing unit of your heating infrastructure",
    color: "#334155",
    glow: "#0F172A",
    offsetY: 0,
    offsetX: 0,
    svgPath: "M30,10 L170,10 L180,20 L180,180 L170,190 L30,190 L20,180 L20,20 Z",
    labelPos: { x: "110%", y: "20%" },
  },
  {
    id: "heat-exchanger",
    label: "Thermal Exchanger",
    description: "High-efficiency thermal transfer protocols",
    color: "#F97316",
    glow: "rgba(249, 115, 22, 0.4)",
    offsetY: -15,
    offsetX: 15,
    svgPath: "M50,40 L150,40 L155,45 L155,90 L150,95 L50,95 L45,90 L45,45 Z",
    labelPos: { x: "-30%", y: "40%" },
  },
  {
    id: "burner",
    label: "Combustion Array",
    description: "Precision-controlled energy generation",
    color: "#F97316",
    glow: "rgba(249, 115, 22, 0.6)",
    offsetY: 15,
    offsetX: -15,
    svgPath: "M60,100 L140,100 L145,108 L140,120 L60,120 L55,108 Z",
    labelPos: { x: "110%", y: "60%" },
  },
  {
    id: "pump",
    label: "Fluid Dynamics",
    description: "Autonomous circulation and pressure management",
    color: "#38BDF8",
    glow: "rgba(56, 189, 248, 0.4)",
    offsetY: 20,
    offsetX: 20,
    svgPath: "M80,130 C80,120 120,120 120,130 L120,155 C120,165 80,165 80,155 Z",
    labelPos: { x: "-40%", y: "80%" },
  },
];

export default function BoilerExplodeAnimation() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const layerRefs = useRef<(SVGGElement | null)[]>([]);
  const labelRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    registerGSAP();
    const section = sectionRef.current;
    if (!section) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: section,
          start: "top center",
          end: "bottom center",
          scrub: 1,
        },
      });

      layers.forEach((layer, i) => {
        const el = layerRefs.current[i];
        const label = labelRefs.current[i];
        if (!el || !label) return;

        tl.to(
          el,
          {
            x: layer.offsetX * 2,
            y: layer.offsetY * 2,
            opacity: 1,
            duration: 1,
          },
          i * 0.2
        );
        tl.to(
          label,
          {
            opacity: 1,
            x: 0,
            duration: 0.5,
          },
          i * 0.2 + 0.2
        );
      });
    });

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="bg-[#070707] overflow-hidden py-32"
      aria-label="Boiler component exploded view animation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center justify-center gap-16">
        {/* Text */}
        <div className="lg:w-1/2 text-center lg:text-left">
          <span className="text-[#F97316] text-sm font-bold uppercase tracking-widest mb-4 block">
            System Architecture
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Engineered For Performance
          </h2>
          <p className="text-gray-400 text-lg leading-relaxed mb-8 max-w-lg font-light">
            We deconstruct the complexity of modern heating systems. Every component is optimized, monitored, and maintained with industrial precision.
          </p>
          <Link
            href="/services/heating"
            className="inline-flex items-center gap-3 text-white font-semibold hover:text-[#F97316] transition-all text-lg group"
          >
            Explore the Architecture 
            <ArrowRight size={20} className="transform group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* SVG Exploded Blueprint */}
        <div className="lg:w-1/2 relative flex items-center justify-center min-h-[400px]">
          <div className="absolute inset-0 bg-[#F97316]/5 blur-[100px] rounded-full pointer-events-none" />
          
          <div className="relative w-80 h-80 md:w-96 md:h-96">
            <svg
              viewBox="0 0 200 200"
              className="w-full h-full"
              style={{ filter: "drop-shadow(0 0 15px var(--color-brand-card-hover))" }}
              aria-hidden="true"
            >
              {layers.map((layer, i) => (
                <g
                  key={layer.id}
                  ref={(el) => { layerRefs.current[i] = el; }}
                  style={{ opacity: i === 0 ? 1 : 0 }}
                  className="transition-all duration-300"
                >
                  <path
                    d={layer.svgPath}
                    fill="transparent"
                    stroke={layer.color}
                    strokeWidth={1.5}
                    style={{ filter: `drop-shadow(0 0 8px ${layer.glow})` }}
                  />
                  {/* Internal Grid Lines for Tech Vibe */}
                  <path
                    d={layer.svgPath}
                    fill="url(#blueprintGrid)"
                    fillOpacity={0.1}
                    className="pointer-events-none"
                  />
                </g>
              ))}
              <defs>
                <pattern id="blueprintGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                  <path d="M 10 0 L 0 0 0 10" fill="none" style={{ stroke: "var(--color-brand-card-hover)" }} strokeWidth="0.5"/>
                </pattern>
              </defs>
            </svg>

            {/* Labels */}
            {layers.map((layer, i) => (
              <div
                key={layer.id + "-label"}
                ref={(el) => { labelRefs.current[i] = el; }}
                className="absolute pointer-events-none"
                style={{
                  top: `calc(${layer.labelPos.y})`,
                  left: `calc(${layer.labelPos.x})`,
                  opacity: 0,
                  transform: "translateX(-15px)",
                  whiteSpace: "nowrap",
                  zIndex: 10,
                }}
              >
                <div className="bg-[#0F172A]/80 backdrop-blur-md border border-white/10 rounded-xl px-4 py-3 shadow-2xl">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#F97316] animate-pulse shadow-[0_0_5px_#F97316]" />
                    <p className="text-white text-xs font-bold uppercase tracking-wider">{layer.label}</p>
                  </div>
                  <p className="text-gray-400 text-[10px] max-w-40 whitespace-normal font-light">
                    {layer.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
