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
  variant?: "default" | "luxury";
  /** When true with variant="luxury", hero uses dark background and light/gold typography */
  darkHero?: boolean;
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
  variant = "default",
  darkHero = false,
  showCTA = true,
  ctaText = "Get a Quote",
  ctaHref = "/contact",
  preselectedService,
  compact = false,
}: PageHeroProps) {
  const { openQuoteModal } = useQuoteModal();
  const hasImage = !!backgroundImage;
  const isQuoteCTA = ctaHref === "/contact";
  const isLuxury = variant === "luxury";
  const luxuryWithImage = isLuxury && hasImage;
  const isDarkHero = isLuxury && darkHero;

  return (
    <section
      className={`relative overflow-hidden ${
        isDarkHero ? "bg-[#05080c]" : isLuxury ? "bg-[#f2ede3]" : "bg-brand-surface"
      } ${hasImage ? "min-h-[70vh]" : ""} ${
        compact ? "pt-36 pb-20" : "pt-48 pb-32"
      }`}
      aria-label={`${title} page hero`}
    >
      {/* Background image + overlay */}
      {hasImage && backgroundImage && (
        <>
          <div className="absolute inset-0">
            <Image
              src={backgroundImage}
              alt=""
              fill
              className={`object-cover object-center ${
                isLuxury ? "opacity-100" : "opacity-55 dark:opacity-60"
              }`}
              sizes="100vw"
              priority
              aria-hidden="true"
            />
          </div>
          <div
            className={`absolute inset-0 ${
              isDarkHero ? "bg-[#05080c]/85" : isLuxury ? "bg-[#f2ede3]/60" : "bg-brand-surface/55 dark:bg-black/40"
            }`}
          />
          <div
            className={`absolute bottom-0 left-0 right-0 h-40 ${
              isDarkHero
                ? "bg-gradient-to-t from-[#05080c] to-transparent"
                : isLuxury
                ? "bg-gradient-to-t from-[#f2ede3] to-transparent"
                : "bg-gradient-to-t from-brand-surface to-transparent"
            }`}
          />
        </>
      )}

      {/* Geometric / ambient layer — luxury: always show (subtle over image); darkHero: light borders on dark */}
      {isLuxury ? (
        <div className="pointer-events-none absolute inset-0">
          <div
            className={`absolute -right-40 -top-24 h-64 w-80 rotate-6 border rounded-[3rem] ${
              isDarkHero ? "border-white/10" : hasImage ? "border-[#5c4d2e]/55" : "border-[#e2c977]/40"
            }`}
          />
          <div
            className={`absolute -left-40 bottom-0 h-56 w-80 -rotate-6 border rounded-[3rem] ${
              isDarkHero ? "border-[#e2c977]/20" : hasImage ? "border-[#4a3d22]/50" : "border-[#d4af37]/28"
            }`}
          />
          <div
            className={`absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent ${
              isDarkHero ? "via-[#e2c977]/25" : hasImage ? "via-[#3d3320]/45" : "via-[#e2c977]/28"
            } to-transparent`}
          />
        </div>
      ) : (
        !hasImage && (
          <>
            <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-red/[0.03] blur-[120px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/3" />
            <div className="absolute bottom-0 left-0 w-[800px] h-[400px] bg-brand-blue/[0.03] blur-[150px] rounded-full pointer-events-none translate-y-1/2 -translate-x-1/4" />
          </>
        )
      )}

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 z-0 pointer-events-none opacity-[0.04]"
        style={{ backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)", backgroundSize: "80px 80px" }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-12">
          <ol className={`flex items-center gap-4 text-[10px] font-technical font-bold uppercase tracking-[0.3em] flex-wrap ${
            isDarkHero ? "text-white/70" : luxuryWithImage ? "text-[#3c3630]" : hasImage ? "text-white/60" : "text-brand-muted"
          }`}>
            {breadcrumbs.map((crumb, i) => (
              <li key={i} className="flex items-center gap-4">
                {i > 0 && <span className={`w-1.5 h-1.5 rounded-full ${isDarkHero ? "bg-[#e2c977]" : luxuryWithImage ? "bg-[#5c4d2e]" : "bg-brand-red/50"}`} />}
                {crumb.href ? (
                  <Link href={crumb.href} className={`transition-colors ${isDarkHero ? "hover:text-white" : luxuryWithImage ? "hover:text-[#171b1f]" : hasImage ? "hover:text-white" : "hover:text-brand-text"}`}>
                    {crumb.label}
                  </Link>
                ) : (
                  <span className={isDarkHero ? "text-white" : luxuryWithImage ? "text-[#171b1f]" : hasImage ? "text-white/90" : "text-brand-text"}>{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>

        <div className="max-w-4xl">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-md border mb-8 ${
              isDarkHero
                ? "border-white/20 bg-white/10"
                : luxuryWithImage
                ? "border-[#5c4d2e]/60 bg-[#f2ede3]/90"
                : hasImage
                ? "border-white/20 bg-white/10"
                : isLuxury
                ? "border-[#e2c977]/50 bg-white/70"
                : "border-brand-red/20 bg-brand-red/10"
            }`}
          >
            <Flame
              size={12}
              className={
                isDarkHero
                  ? "text-[#e2c977]"
                  : luxuryWithImage
                  ? "text-[#5c4d2e]"
                  : hasImage
                  ? "text-brand-red"
                  : isLuxury
                  ? "text-[#b8963a]"
                  : "text-brand-red"
              }
            />
            <span
              className={`text-[10px] font-technical font-bold uppercase tracking-[0.2em] ${
                isDarkHero
                  ? "text-white/90"
                  : luxuryWithImage
                  ? "text-[#3d3320]"
                  : hasImage
                  ? "text-white/80"
                  : isLuxury
                  ? "text-[#7b6b39]"
                  : "text-brand-red"
              }`}
            >
              Gas Safe Registered
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className={`text-5xl md:text-8xl font-technical font-extrabold mb-10 tracking-widest uppercase leading-none ${
              isDarkHero ||
              (luxuryWithImage &&
                (title === "Portfolio" ||
                  title === "About Us" ||
                  title === "Service Areas" ||
                  title === "Contact Us" ||
                  title === "Commercial Services" ||
                  title === "Domestic Services" ||
                  title === "Domestic Plumbing & Heating" ||
                  title === "Commercial Mechanical Services" ||
                  title === "Commercial Electrical Services" ||
                  title === "Commercial Gas Services" ||
                  title === "Domestic Gas Services" ||
                  title === "Domestic Electrical Services"))
                ? isDarkHero
                  ? "text-[#e2c977]"
                  : "text-[#b8963a]"
                : luxuryWithImage
                ? "text-[#171b1f]"
                : hasImage
                ? "text-white"
                : "text-brand-text"
            }`}
          >
            {title}
          </motion.h1>

          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className={`text-sm md:text-base mb-16 max-w-2xl leading-relaxed uppercase tracking-[0.35em] ${
                isDarkHero
                  ? "text-[#b3c0d0] font-medium"
                  : luxuryWithImage
                  ? "text-[#1f252b] font-bold"
                  : hasImage
                  ? "text-white/70 font-light"
                  : "text-brand-muted font-light"
              }`}
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
                  className={`group relative px-12 py-5 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden ${
                    isDarkHero
                      ? "bg-[#e2c977] text-[#0a0f14] shadow-lg hover:bg-[#f5e9c6]"
                      : "bg-brand-red text-white shadow-xl shadow-brand-red/20"
                  }`}
                >
                  <span className="relative z-10 transition-colors">{ctaText}</span>
                  {!isDarkHero && <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />}
                </button>
              ) : (
                <Link
                  href={ctaHref}
                  className={`group relative px-12 py-5 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden ${
                    isDarkHero
                      ? "bg-[#e2c977] text-[#0a0f14] shadow-lg hover:bg-[#f5e9c6]"
                      : "bg-brand-red text-white shadow-xl shadow-brand-red/20"
                  }`}
                >
                  <span className="relative z-10 transition-colors">{ctaText}</span>
                  {!isDarkHero && <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />}
                </Link>
              )}
              <a
                href={`tel:${COMPANY.phone}`}
                className={`flex items-center gap-4 transition-all font-technical font-bold text-[12px] uppercase tracking-[0.2em] ${
                  isDarkHero
                    ? "text-white/90 hover:text-[#e2c977]"
                    : luxuryWithImage
                    ? "text-[#2b3136] hover:text-[#171b1f]"
                    : hasImage
                    ? "text-white/70 hover:text-white"
                    : "text-brand-muted hover:text-brand-text"
                }`}
              >
                <Phone size={18} className={isDarkHero ? "text-[#e2c977] animate-pulse" : luxuryWithImage ? "text-[#5c4d2e] animate-pulse" : "text-brand-red animate-pulse"} />
                <span>{COMPANY.phone}</span>
              </a>
            </motion.div>
          )}
        </div>
      </div>

    </section>
  );
}
