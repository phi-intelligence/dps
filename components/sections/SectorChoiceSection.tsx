"use client";

import Link from "next/link";
import Image from "next/image";
import { Building2, Home, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { CORE_SERVICES_IMAGES } from "@/lib/constants";
import type { CoreServiceSlug } from "@/lib/constants";

const SECTOR_LABELS: Record<CoreServiceSlug, { commercial: string; domestic: string }> = {
  mechanical: { commercial: "Commercial Mechanical Services", domestic: "Domestic Mechanical Services" },
  electrical: { commercial: "Commercial Electrical Services", domestic: "Domestic Electrical Services" },
  gas: { commercial: "Commercial Gas Services", domestic: "Domestic Gas Services" },
};

interface SectorChoiceSectionProps {
  /** Slug for route: mechanical | electrical | gas */
  basePath: CoreServiceSlug;
  /** Key for CORE_SERVICES_IMAGES e.g. "Mechanical Services" */
  serviceImageKey: string;
}

export default function SectorChoiceSection({ basePath, serviceImageKey }: SectorChoiceSectionProps) {
  const imageSrc = CORE_SERVICES_IMAGES[serviceImageKey] ?? "/images/core-services/mechanical.png";
  const labels = SECTOR_LABELS[basePath];

  const sectors = [
    {
      slug: "commercial" as const,
      href: `/services/${basePath}/commercial`,
      label: labels.commercial,
      icon: Building2,
      badge: "Commercial",
    },
    {
      slug: "domestic" as const,
      href: `/services/${basePath}/domestic`,
      label: labels.domestic,
      icon: Home,
      badge: "Domestic",
    },
  ];

  return (
    <section className="py-16 md:py-24 relative overflow-hidden bg-brand-steel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">
            Choose your <span className="text-brand-red">sector</span>
          </h2>
          <p className="text-brand-muted text-sm font-light uppercase tracking-wider max-w-xl mx-auto">
            Select commercial or domestic to see all services we offer in this area.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {sectors.map((sector, i) => (
            <motion.div
              key={sector.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="group"
            >
              <Link
                href={sector.href}
                className="relative block aspect-[4/3] rounded-2xl overflow-hidden border border-brand-card-border shadow-lg hover:border-brand-red/30 transition-all duration-300"
              >
                <Image
                  src={imageSrc}
                  alt={sector.label}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />
                <div className="absolute top-4 left-4">
                  <span className="inline-flex items-center gap-2 border border-brand-red/30 bg-brand-red/10 rounded-full px-3 py-1.5 text-brand-red text-[10px] font-technical font-bold uppercase tracking-widest">
                    <sector.icon size={12} />
                    {sector.badge}
                  </span>
                </div>
                <div className="absolute bottom-0 left-0 right-0 p-6 flex items-center justify-between gap-4">
                  <span className="text-white font-technical font-bold text-sm sm:text-base uppercase tracking-widest leading-tight">
                    {sector.label}
                  </span>
                  <span className="shrink-0 w-10 h-10 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center group-hover:bg-brand-red group-hover:border-brand-red transition-all">
                    <ArrowRight size={18} className="text-white" />
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
