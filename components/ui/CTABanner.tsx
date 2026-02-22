import Link from "next/link";
import { Phone, ArrowRight, Zap } from "lucide-react";
import { COMPANY } from "@/lib/constants";

interface CTABannerProps {
  title?: string;
  subtitle?: string;
  variant?: "orange" | "dark";
}

export default function CTABanner({
  title = "Get a Free Quote",
  subtitle = "Contact us today for a no-obligation quote. Gas Safe registered engineers ready to help.",
}: CTABannerProps) {
  return (
    <section
      className="relative py-48 overflow-hidden bg-brand-steel border-t border-brand-card-border"
      aria-label="Call to action"
    >
      {/* Background Gradient Blurs */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brand-red/20 to-transparent" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-brand-red/[0.02] rounded-full blur-[150px] pointer-events-none" />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 border border-brand-red/10 bg-brand-red/5 shadow-sm backdrop-blur-md rounded-full px-5 py-2 mb-12">
          <Zap size={14} className="text-brand-red animate-pulse" />
          <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
            Gas Safe Registered
          </span>
        </div>

        <h2 className="text-5xl md:text-8xl font-technical font-extrabold text-brand-text mb-10 tracking-widest uppercase leading-none">
          {title}
        </h2>

        <p className="text-brand-muted mb-16 max-w-2xl mx-auto font-light leading-relaxed uppercase tracking-[0.4em] text-sm">
          {subtitle}
        </p>

        <div className="flex flex-col sm:flex-row gap-8 justify-center items-center">
          <Link
            href="/contact"
            className="group relative bg-brand-red text-white px-12 py-6 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-[0.3em] transition-all overflow-hidden shadow-xl shadow-brand-red/20"
          >
            <span className="relative z-10 group-hover:text-white transition-colors">Get a Quote</span>
            <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
          </Link>

          <a
            href={`tel:${COMPANY.phone}`}
            className="inline-flex items-center gap-4 text-brand-text hover:text-brand-red transition-all font-technical font-bold text-[12px] uppercase tracking-[0.2em]"
            aria-label={`Call us on ${COMPANY.phone}`}
          >
            <Phone size={20} className="text-brand-red animate-pulse" />
            <span>{COMPANY.phone}</span>
          </a>
        </div>
      </div>

      {/* Bottom technical bar */}
      <div className="absolute bottom-10 left-10 opacity-20 hidden lg:block">
        <div className="flex items-center gap-4">
          <div className="w-10 h-[1px] bg-brand-text" />
          <span className="text-[8px] font-mono uppercase tracking-[0.5em] text-brand-text">DPS Heating Services Ltd</span>
        </div>
      </div>
    </section>
  );
}
