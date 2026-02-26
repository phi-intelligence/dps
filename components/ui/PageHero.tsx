"use client";

import Image from "next/image";
import Link from "next/link";
import { Phone, Flame } from "lucide-react";
import { motion } from "framer-motion";
import { COMPANY } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";

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
  preselectedService?: string;
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
  preselectedService,
  compact = false,
}: PageHeroProps) {
  const { openQuoteModal } = useQuoteModal();
  const hasImage = !!backgroundImage;
  const isQuoteCTA = ctaHref === "/contact";

  return (
    <section
      className={`relative overflow-hidden bg-brand-surface ${hasImage ? "min-h-[70vh]" : ""} ${compact ? "pt-36 pb-20" : "pt-48 pb-32"}`}
      aria-label={`${title} page hero`}
    >
      {/* Background image + overlay — light in light mode, dark in dark mode (like homepage hero) */}
      {hasImage && backgroundImage && (
        <>
          <div className="absolute inset-0">
            <Image
              src={backgroundImage}
              alt=""
              fill
              className="object-cover object-center opacity-35 dark:opacity-30"
              sizes="100vw"
              priority
              aria-hidden="true"
            />
          </div>
          <div className="absolute inset-0 bg-brand-surface/55 dark:bg-black/40" />
          <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-brand-surface to-transparent" />
        </>
      )}

      {/* Ambient gradients (only without image, otherwise they'd fight the overlay) */}
      {!hasImage && (
        <>
          <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-red/[0.03] blur-[120px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/3" />
          <div className="absolute bottom-0 left-0 w-[800px] h-[400px] bg-brand-blue/[0.03] blur-[150px] rounded-full pointer-events-none translate-y-1/2 -translate-x-1/4" />
        </>
      )}

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 z-0 pointer-events-none opacity-[0.04]"
        style={{ backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)", backgroundSize: "80px 80px" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-12">
          <ol className={`flex items-center gap-4 text-[10px] font-technical font-bold uppercase tracking-[0.3em] flex-wrap ${hasImage ? "text-white/60" : "text-brand-muted"}`}>
            {breadcrumbs.map((crumb, i) => (
              <li key={i} className="flex items-center gap-4">
                {i > 0 && <span className="w-1.5 h-1.5 rounded-full bg-brand-red/50" />}
                {crumb.href ? (
                  <Link href={crumb.href} className={`transition-colors ${hasImage ? "hover:text-white" : "hover:text-brand-text"}`}>
                    {crumb.label}
                  </Link>
                ) : (
                  <span className={hasImage ? "text-white/90" : "text-brand-text"}>{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>

        <div className="max-w-4xl">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-md border mb-8 ${hasImage ? "border-white/20 bg-white/10" : "border-brand-red/20 bg-brand-red/10"}`}
          >
            <Flame size={12} className="text-brand-red" />
            <span className={`text-[10px] font-technical font-bold uppercase tracking-[0.2em] ${hasImage ? "text-white/80" : "text-brand-red"}`}>
              Gas Safe Registered
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className={`text-5xl md:text-8xl font-technical font-extrabold mb-10 tracking-widest uppercase leading-none ${hasImage ? "text-white" : "text-brand-text"}`}
          >
            {title}
          </motion.h1>

          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className={`text-sm md:text-md mb-16 max-w-2xl font-light leading-relaxed uppercase tracking-[0.4em] ${hasImage ? "text-white/70" : "text-brand-muted"}`}
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
              {isQuoteCTA ? (
                <button
                  type="button"
                  onClick={() => openQuoteModal({ preselectedService })}
                  className="group relative bg-brand-red text-white px-12 py-5 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden shadow-xl shadow-brand-red/20"
                >
                  <span className="relative z-10 group-hover:text-white transition-colors">{ctaText}</span>
                  <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
                </button>
              ) : (
                <Link
                  href={ctaHref}
                  className="group relative bg-brand-red text-white px-12 py-5 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden shadow-xl shadow-brand-red/20"
                >
                  <span className="relative z-10 group-hover:text-white transition-colors">{ctaText}</span>
                  <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
                </Link>
              )}
              <a
                href={`tel:${COMPANY.phone}`}
                className={`flex items-center gap-4 transition-all font-technical font-bold text-[12px] uppercase tracking-[0.2em] ${hasImage ? "text-white/70 hover:text-white" : "text-brand-muted hover:text-brand-text"}`}
              >
                <Phone size={18} className="text-brand-red animate-pulse" />
                <span>{COMPANY.phone}</span>
              </a>
            </motion.div>
          )}
        </div>
      </div>

    </section>
  );
}
