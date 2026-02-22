"use client";

import Link from "next/link";
import { ArrowRight, LucideIcon, Cpu } from "lucide-react";
import { motion } from "framer-motion";

interface ServiceCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  subservices: string[];
  href: string;
  index: number;
}

export default function ServiceCard({
  icon: Icon,
  title,
  description,
  subservices,
  href,
  index,
}: ServiceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="group relative bg-brand-card backdrop-blur-xl border border-brand-card-border-hover rounded-[2rem] p-10 hover:border-brand-red/20 transition-all duration-500 overflow-hidden hover:shadow-xl hover:shadow-brand-red/5"
    >
      {/* Decorative Gradient Background */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-brand-red/5 via-brand-purple/5 to-transparent blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

      {/* Technical Data Overlay */}
      <div className="absolute top-6 right-8 opacity-10 pointer-events-none">
        <Cpu size={14} className="text-brand-red" />
      </div>

      <div className="w-14 h-14 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center justify-center mb-10 group-hover:bg-brand-red/5 group-hover:border-brand-red/10 transition-all duration-500">
        <Icon size={28} className="text-brand-red group-hover:animate-pulse" />
      </div>

      <h3 className="text-2xl font-technical font-extrabold text-brand-text mb-4 tracking-wider uppercase">{title}</h3>
      <p className="text-brand-muted font-light leading-relaxed mb-10 text-sm uppercase tracking-widest">{description}</p>

      <div className="space-y-4 mb-12">
        {subservices.map((sub, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-red opacity-20 group-hover:opacity-100 group-hover:shadow-[0_0_8px_rgba(220,38,38,0.5)] transition-all" />
            <span className="text-[11px] font-technical font-bold uppercase tracking-[0.2em] text-brand-muted group-hover:text-brand-text transition-colors">
              {sub}
            </span>
          </div>
        ))}
      </div>

      <Link
        href={href}
        className="inline-flex items-center gap-3 text-[10px] font-technical font-extrabold uppercase tracking-[0.3em] text-brand-red hover:text-brand-text transition-all group/link"
      >
        <span>Initialize Interface</span>
        <ArrowRight size={14} className="transform group-hover/link:translate-x-2 transition-transform" />
      </Link>

      {/* Modern Border Bottom Glow */}
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-brand-red to-transparent scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
    </motion.div>
  );
}
