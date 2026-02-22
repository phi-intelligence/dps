import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { MapPin, Phone, ArrowRight, Activity } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, SERVICE_AREAS } from "@/lib/constants";

export const metadata: Metadata = {
  title: "Service Areas",
  description: `DPS Heating Services Ltd covers ${COMPANY.areas} and surrounding areas. Professional heating and air conditioning engineers near you.`,
};

export default function ServiceAreasPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      <PageHero
        title="Service Areas"
        subtitle={`We provide heating and air conditioning services across ${COMPANY.areas}. Local engineers, fast response times.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Service Areas" }]}
        backgroundImage="/images/service-area-map.jpg"
        compact
      />

      {/* Coverage Intro */}
      <section className="py-48 relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-[600px] h-[600px] bg-brand-red/5 blur-[200px] rounded-full -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-32 items-center">
            <div>
              <div className="inline-flex items-center gap-2 border border-brand-red/20 bg-brand-red/5 backdrop-blur-md rounded-md px-5 py-2 mb-10">
                <MapPin size={14} className="text-brand-red" />
                <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em]">
                  Coverage Area
                </span>
              </div>

              <h2 className="text-5xl md:text-7xl font-technical font-extrabold text-brand-text mb-10 tracking-widest leading-none uppercase">
                Where We <br />
                <span className="text-brand-muted/40">Work.</span>
              </h2>

              <div className="space-y-8 text-brand-muted font-light leading-relaxed text-sm uppercase tracking-wider max-w-xl">
                <p>
                  DPS Heating Services Ltd operates throughout {COMPANY.areas}, covering both domestic
                  and commercial customers. Our engineers are locally based, allowing us to offer fast
                  response times across our entire coverage area.
                </p>
                <p>
                  Whether you need a boiler repaired, a heating system installed, or an air conditioning
                  unit serviced, we have engineers ready to help. Same-day and next-day appointments are
                  available for most services.
                </p>
              </div>

              <div className="mt-16 bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <p className="text-[10px] text-brand-muted mb-4 font-mono tracking-widest">NOT SURE IF WE COVER YOUR AREA?</p>
                <p className="text-brand-text text-xs font-technical tracking-wider uppercase leading-loose">
                  Give us a call or drop us an email — we are happy to confirm coverage and get you booked in.
                </p>
                <div className="mt-10 flex flex-col sm:flex-row gap-6">
                  <a href={`tel:${COMPANY.phone}`} className="flex items-center gap-4 bg-white text-black px-8 py-4 rounded-full font-technical font-extrabold text-[10px] uppercase tracking-widest hover:bg-brand-red hover:text-white transition-all">
                    <Phone size={14} />
                    {COMPANY.phone}
                  </a>
                </div>
              </div>
            </div>

            {/* Areas Grid */}
            <div className="bg-brand-navy border border-brand-card-border rounded-[3rem] p-12 md:p-20 shadow-2xl relative overflow-hidden self-start">
              <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-brand-blue/5 blur-[120px] rounded-full pointer-events-none" />
              <div className="relative z-10">
                <h3 className="text-2xl font-technical font-extrabold text-brand-text mb-10 tracking-widest uppercase border-b border-brand-card-border-hover pb-6 flex items-center gap-4">
                  <Activity size={20} className="text-brand-red" />
                  Areas We Cover
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
                  + Surrounding Areas — Call to Confirm
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Coverage Network Section */}
      <section className="py-40 bg-brand-navy relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-brand-blue/[0.03] blur-[150px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div className="space-y-10">
              <div>
                <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
                  Local Coverage
                </span>
                <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase leading-none">
                  Always <span className="text-brand-red">Nearby</span>
                </h2>
              </div>
              <p className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.3em] leading-loose">
                Our engineers cover {COMPANY.areas} and surrounding areas. Being locally based means
                we can offer prompt service and respond quickly when you need us most.
              </p>
              <div className="grid grid-cols-2 gap-6">
                {[
                  { stat: SERVICE_AREAS.length + "+", label: "Areas Covered" },
                  { stat: "Same Day", label: "Available" },
                  { stat: "10+", label: "Years Serving London" },
                  { stat: "100%", label: "Gas Safe Registered" },
                ].map((item) => (
                  <div key={item.label} className="bg-brand-surface border border-brand-card-border rounded-2xl p-6">
                    <p className="text-3xl font-technical font-extrabold text-brand-red mb-1 tracking-tighter">{item.stat}</p>
                    <p className="text-[9px] font-technical text-brand-muted uppercase tracking-[0.3em]">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <BlueprintBillboard
              src="/images/blueprint-plant-room.png"
              alt="Commercial heating plant room — London service coverage"
              theme="tech"
              versionText="COVERAGE: LONDON & SURROUNDS"
              idHash={`GAS SAFE: ${COMPANY.gasSafeNumber}`}
              statusText="OPERATIONAL"
              className="w-full"
            />
          </div>
        </div>
      </section>

      {/* London Aerial Photo */}
      <section className="relative h-[420px] overflow-hidden">
        <Image
          src="/images/service-area-map.jpg"
          alt="Aerial view of London — DPS Heating Services coverage area"
          fill
          className="object-cover object-center"
          sizes="100vw"
        />
        <div className="absolute inset-0 bg-brand-surface/70" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-4">
            <p className="text-[10px] font-technical font-bold uppercase tracking-[0.5em] text-brand-red mb-4">
              Coverage Area
            </p>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
              Across <span className="text-brand-red">London</span>
            </h2>
            <p className="mt-6 text-brand-muted text-xs font-technical uppercase tracking-[0.3em]">
              {SERVICE_AREAS.length}+ areas covered · Same-day service available
            </p>
          </div>
        </div>
      </section>

      {/* Not in Our Area? */}
      <section className="py-32 bg-brand-red relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/grid-pattern.png')] opacity-10 mix-blend-overlay" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-white mb-6 tracking-widest uppercase">
            Don&apos;t See Your Area?
          </h2>
          <p className="text-white/80 text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-12">
            We may still be able to help. Contact us to check availability in your area.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/contact"
              className="inline-flex items-center gap-4 bg-white text-brand-red px-10 py-5 rounded-full font-technical font-extrabold text-xs uppercase tracking-[0.3em] hover:bg-white/90 transition-all shadow-xl"
            >
              Get in Touch <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      <CTABanner />
    </div>
  );
}
