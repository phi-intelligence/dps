"use client";

import Image from "next/image";
import Link from "next/link";
import { ChevronRight, Phone, ArrowRight, Flame } from "lucide-react";
import { motion } from "framer-motion";
import { COMPANY } from "@/lib/constants";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeroProps {
  title: string;
  subtitle?: string;
  breadcrumbs: Breadcrumb[];
  backgroundImage?: string;
  showCTA?: boolean;
  ctaText?: string;
  ctaHref?: string;
  compact?: boolean;
}

export default function PageHero({
  title,
  subtitle,
  breadcrumbs,
  backgroundImage,
  showCTA = true,
  ctaText = "Get a Quote",
  ctaHref = "/contact",
  compact = false,
}: PageHeroProps) {
  return (
    <section
      className={`relative ${compact ? "pt-36 pb-20" : "pt-48 pb-32"} overflow-hidden bg-brand-surface border-b border-brand-card-border`}
      aria-label={`${title} page hero`}
    >
      {/* Background Image */}
      {backgroundImage && (
        <>
          <Image
            src={backgroundImage}
            alt=""
            fill
            className="object-cover object-center"
            sizes="100vw"
            priority
            aria-hidden="true"
          />
          {/* Dark overlay — keeps text readable */}
          <div className="absolute inset-0 bg-brand-surface/80" />
          {/* Gradient fade at bottom */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-brand-surface to-transparent" />
        </>
      )}

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 z-0 opacity-[0.04] pointer-events-none"
        style={{ backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)", backgroundSize: "80px 80px" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-12">
          <ol className="flex items-center gap-4 text-[10px] font-technical font-bold uppercase tracking-[0.3em] flex-wrap text-brand-muted">
            {breadcrumbs.map((crumb, i) => (
              <li key={i} className="flex items-center gap-4">
                {i > 0 && <span className="w-1.5 h-1.5 rounded-full bg-brand-red/30" />}
                {crumb.href ? (
                  <Link href={crumb.href} className="hover:text-brand-text transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-brand-text">{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>

        <div className="max-w-4xl">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-red/20 bg-brand-red/10 mb-8"
          >
            <Flame size={12} className="text-brand-red" />
            <span className="text-[10px] font-technical font-bold text-brand-red uppercase tracking-[0.2em]">
              Gas Safe Registered
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-5xl md:text-8xl font-technical font-extrabold text-brand-text mb-10 tracking-widest uppercase leading-none"
          >
            {title}
          </motion.h1>

          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-sm md:text-md text-brand-muted mb-16 max-w-2xl font-light leading-relaxed uppercase tracking-[0.4em]"
            >
              {subtitle}
            </motion.p>
          )}

          {showCTA && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="flex flex-col sm:flex-row gap-8 items-start sm:items-center"
            >
              <Link
                href={ctaHref}
                className="group relative bg-brand-red text-white px-12 py-5 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden shadow-xl shadow-brand-red/20"
              >
                <span className="relative z-10 group-hover:text-white transition-colors">{ctaText}</span>
                <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
              </Link>
              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center gap-4 text-brand-muted hover:text-brand-text transition-all font-technical font-bold text-[12px] uppercase tracking-[0.2em]"
              >
                <Phone size={18} className="text-brand-red animate-pulse" />
                <span>{COMPANY.phone}</span>
              </a>
            </motion.div>
          )}
        </div>
      </div>

      {/* Bottom rule */}
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-brand-red/10 via-brand-purple/10 to-brand-blue/10" />
    </section>
  );
}
