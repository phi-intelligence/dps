"use client";

import Image from "next/image";
import { Phone } from "lucide-react";
import { COMPANY } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

interface CTABannerProps {
  title?: string;
  subtitle?: string;
  variant?: "orange" | "dark";
  /** Optional full-bleed background image (e.g. blueprint). When set, shown behind content with overlay. */
  backgroundImage?: string;
}

export default function CTABanner({
  title = "Get a Free Quote",
  subtitle = "Contact us today for a no-obligation quote. Gas Safe registered engineers ready to help.",
  backgroundImage,
}: CTABannerProps) {
  const { openQuoteModal } = useQuoteModal();
  return (
    <section
      className="relative py-32 px-4 overflow-hidden"
      aria-label="Call to action"
    >
      {backgroundImage ? (
        <>
          <div className="absolute inset-0 z-0" aria-hidden>
            <Image
              src={backgroundImage}
              alt=""
              fill
              className="object-cover object-center opacity-25 dark:opacity-20"
              sizes="100vw"
            />
            <div className="absolute inset-0 bg-brand-surface/70 dark:bg-brand-surface/85" />
          </div>
        </>
      ) : (
        <div className="absolute inset-0 opacity-50 pointer-events-none">
          <EnergyFlowBackground />
        </div>
      )}
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="bg-brand-surface dark:bg-brand-steel rounded-[2rem] p-12 md:p-24 relative overflow-hidden premium-shadow">
          {/* Decorative Gradient Glows - Refined for geometric look */}
          <div className="absolute -top-32 -right-32 w-[30rem] h-[30rem] bg-brand-red/5 rounded-full blur-[120px] pointer-events-none" />
          <div className="absolute -bottom-32 -left-32 w-[30rem] h-[30rem] bg-brand-orange/5 rounded-full blur-[120px] pointer-events-none" />
          <div className="relative z-10 max-w-4xl mx-auto text-center">
            <h2 className="text-4xl md:text-7xl font-sans font-extrabold text-brand-text mb-8 tracking-tight">
              {title}
            </h2>

            <p className="text-brand-muted mb-12 max-w-2xl mx-auto font-medium leading-relaxed text-lg md:text-xl">
              {subtitle}
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <button
                type="button"
                onClick={() => openQuoteModal()}
                className="group relative bg-brand-gradient text-white px-10 py-5 rounded-full font-bold text-lg transition-all shadow-xl shadow-brand-red/10 hover:shadow-brand-red/20 active:scale-95 duration-200 overflow-hidden"
              >
                <span className="relative z-10">Get a Free Estimate</span>
                <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>

              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center gap-3 text-brand-text hover:text-brand-red transition-all font-bold text-lg"
              >
                <Phone size={24} className="text-brand-red" />
                <span>{COMPANY.phone}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
