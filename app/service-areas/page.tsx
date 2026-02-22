import type { Metadata } from "next";
import Link from "next/link";
import { MapPin, Phone, ArrowRight, Cpu, Activity, Zap, Target } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import { COMPANY, SERVICE_AREAS } from "@/lib/constants";
import { motion } from "framer-motion";

export const metadata: Metadata = {
  title: "Operational Zones",
  description: `DPS Heating Services Ltd deployment matrix across ${COMPANY.areas} and surrounding coordinates. Local engineering presence guaranteed.`,
};

export default function ServiceAreasPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="Operational Zones"
        subtitle={`Systemic coverage across ${COMPANY.areas} and surrounding tactical sectors. Localized operative presence for rapid deployment.`}
        breadcrumbs={[{ label: "Core", href: "/" }, { label: "Zones" }]}
        compact
      />

      {/* Coverage Intro */}
      <section className="py-48 relative overflow-hidden">
        {/* Glow Element */}
        <div className="absolute top-1/2 left-0 w-[600px] h-[600px] bg-brand-red/5 blur-[200px] rounded-full -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-32 items-center">
            <div>
              <div className="inline-flex items-center gap-2 border border-brand-red/20 bg-brand-red/5 backdrop-blur-md rounded-md px-5 py-2 mb-10">
                <Target size={14} className="text-brand-red" />
                <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Deployment Radius
                </span>
              </div>

              <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text mb-10 tracking-widest leading-none uppercase">
                Zone: <br />
                <span className="text-brand-muted/40">{COMPANY.areas}</span>
              </h2>

              <div className="space-y-8 text-brand-muted font-light leading-relaxed text-sm uppercase tracking-wider max-w-xl">
                <p>
                  DPS Heating Services Ltd maintains an active engineering presence throughout the {COMPANY.areas} sector.
                  Our operational logistics are optimized for rapid hardware deployment and field diagnostics across both domestic and industrial infrastructures.
                </p>
                <p>
                  Our operatives are locally stationed, ensuring that SLA-driven response times are maintained across the entire deployment matrix.
                  Whether you require emergency breach containment or strategic system architecture, we are positioned for immediate activation.
                </p>
              </div>

              <div className="mt-16 bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <p className="text-[10px] text-brand-muted mb-4 font-mono tracking-widest">SIGNAL RECONNAISSANCE</p>
                <p className="text-brand-text text-xs font-technical tracking-wider uppercase leading-loose">
                  Postcode not visible in the matrix? Transmit your coordinates via our tactical uplink for coverage verification.
                </p>
                <div className="mt-10 flex flex-col sm:flex-row gap-6">
                  <a href={`tel:${COMPANY.phone}`} className="flex items-center gap-4 bg-white text-black px-8 py-4 rounded-full font-technical font-extrabold text-[10px] uppercase tracking-widest hover:bg-brand-red hover:text-white transition-all">
                    <Phone size={14} />
                    {COMPANY.phone}
                  </a>
                </div>
              </div>
            </div>

            {/* Target Coordinates Grid */}
            <div className="bg-brand-navy border border-brand-card-border rounded-[3rem] p-12 md:p-20 shadow-2xl relative overflow-hidden self-start">
              <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-brand-blue/5 blur-[120px] rounded-full pointer-events-none" />
              <div className="relative z-10">
                <h3 className="text-2xl font-technical font-extrabold text-brand-text mb-10 tracking-widest uppercase border-b border-brand-card-border-hover pb-6 flex items-center gap-4">
                  <Activity size={20} className="text-brand-red" />
                  Target Coordinates
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {SERVICE_AREAS.map((area) => (
                    <div
                      key={area}
                      className="flex items-center gap-4 bg-brand-card border border-brand-card-border text-brand-muted px-6 py-4 rounded-2xl text-[10px] font-technical font-bold uppercase tracking-widest group hover:border-brand-red/40 hover:text-brand-text transition-all"
                    >
                      <MapPin size={12} className="text-brand-red/40 group-hover:text-brand-red transition-colors" />
                      {area}
                    </div>
                  ))}
                </div>
                <p className="text-brand-muted text-[10px] mt-10 font-mono tracking-[0.2em] text-center uppercase">
                  + Surrounding Peripheral Sectors Monitoring
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Expansion Logic */}
      <section className="py-32 bg-brand-red relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-6 tracking-widest uppercase">
            Coordinate Not Found?
          </h2>
          <p className="text-white/80 text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-12">
            Our operative radius is expanding. Contact the uplink for current zone availability.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/contact"
              className="inline-flex items-center gap-4 bg-white text-brand-red px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.3em] hover:bg-white/90 transition-all shadow-xl"
            >
              Transmit Enquiry <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      <CTABanner />
    </div>
  );
}
