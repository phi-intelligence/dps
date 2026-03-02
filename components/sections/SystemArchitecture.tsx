"use client";

import { motion } from "framer-motion";
import ScrollImageSequence from "@/components/ui/ScrollImageSequence";

const callouts = [
  { progress: 0.15, title: "Outer Casing",     description: "Precision-engineered housing" },
  { progress: 0.40, title: "Heat Exchanger",   description: "98.7% thermal transfer efficiency" },
  { progress: 0.65, title: "Combustion Array", description: "High-velocity burner assembly" },
  { progress: 0.88, title: "Control Interface",description: "Digital management substrate" },
];

export default function SystemArchitecture() {
  return (
    <section aria-label="System Architecture" className="bg-brand-surface">

      {/* Section heading — normal scroll flow, seen before the animation starts */}
      <div className="py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
            Internal Diagnostics
          </span>
          <h2 className="text-4xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
            System <span className="text-brand-red">Architecture</span>
          </h2>
          <p className="mt-6 text-[10px] font-technical uppercase tracking-[0.4em] text-brand-muted">
            Scroll to disassemble — component-level inspection mode
          </p>
        </motion.div>
      </div>

      {/* Scroll-driven image sequence */}
      <ScrollImageSequence
        pathPrefix="/images/sequences/boiler-assembly/ezgif-frame-"
        frameCount={31}
        callouts={callouts}
      />
    </section>
  );
}
