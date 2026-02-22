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
      className="group relative bg-brand-steel border border-brand-card-border rounded-3xl p-8 transition-all duration-500 premium-shadow hover:premium-shadow-hover"
    >
      <div className="flex items-center gap-6 mb-8">
        <div className="w-16 h-16 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center justify-center group-hover:bg-brand-red group-hover:border-brand-red transition-all duration-500">
          <Icon size={32} className="text-brand-red group-hover:text-white transition-colors" />
        </div>
        <h3 className="text-2xl font-sans font-extrabold text-brand-text tracking-tight">{title}</h3>
      </div>

      <p className="text-brand-muted font-medium leading-relaxed mb-10 text-base">{description}</p>

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
        className="inline-flex items-center gap-3 text-sm font-bold text-brand-text hover:text-brand-red transition-all group/link"
      >
        <span>Learn More</span>
        <ArrowRight size={16} className="transform group-hover/link:translate-x-2 transition-transform" />
      </Link>

    </motion.div>
  );
}
