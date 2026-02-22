import Image from "next/image";
import Link from "next/link";
import { Phone, ArrowRight, Activity, Zap, ShieldCheck, Cpu, Database } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import ProcessSteps, { ProcessStep } from "@/components/sections/ProcessSteps";
import FAQAccordion, { FAQItem } from "@/components/ui/FAQAccordion";
import QuoteForm from "@/components/ui/QuoteForm";
import { COMPANY } from "@/lib/constants";
import { ICON_MAP, IconName } from "@/lib/icons";
import { motion } from "framer-motion";

interface IssueCard {
  icon: IconName;
  title: string;
  description: string;
}

interface TrustPoint {
  icon: IconName;
  title: string;
  description: string;
}

interface ServiceDetailLayoutProps {
  title: string;
  subtitle: string;
  backgroundImage: string;
  sideImage: string;
  sideImageAlt: string;
  introduction: string;
  included: string[];
  issues: IssueCard[];
  steps: ProcessStep[];
  trustPoints: TrustPoint[];
  faqs: FAQItem[];
  breadcrumbs: { label: string; href?: string }[];
  serviceValue: string;
  showGasSafeNote?: boolean;
  accentColor?: "red" | "blue";
}

export default function ServiceDetailLayout({
  title,
  subtitle,
  sideImage,
  sideImageAlt,
  introduction,
  included,
  issues,
  steps,
  trustPoints,
  faqs,
  breadcrumbs,
  serviceValue,
  showGasSafeNote = false,
  accentColor = "red",
}: ServiceDetailLayoutProps) {
  const accentClass = accentColor === "red" ? "text-brand-red" : "text-brand-blue";
  const accentBgClass = accentColor === "red" ? "bg-brand-red" : "bg-brand-blue";
  const accentBorderClass = accentColor === "red" ? "border-brand-red" : "border-brand-blue";

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title={title}
        subtitle={subtitle}
        breadcrumbs={breadcrumbs}
        compact
      />

      {/* Strategic Overview */}
      <section className="py-32 relative overflow-hidden border-b border-brand-card-border">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-red/5 blur-[150px] rounded-full pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className={`inline-flex items-center gap-2 border border-brand-card-border-hover bg-brand-card backdrop-blur-md rounded-md px-4 py-1.5 mb-8`}>
                <div className={`w-1.5 h-1.5 rounded-full ${accentBgClass} animate-pulse`} />
                <span className="text-brand-text/80 text-[10px] font-technical font-bold uppercase tracking-[0.3em]">
                  Service Overview
                </span>
              </div>

              <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-10 tracking-widest uppercase leading-tight">
                Professional <br /> <span className={accentClass}>Service.</span>
              </h2>

              <p className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.3em] leading-loose mb-12">
                {introduction}
              </p>

              {showGasSafeNote && (
                <div className="bg-brand-navy border border-brand-card-border rounded-3xl p-8 mb-12 shadow-2xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl" />
                  <div className="flex items-center gap-6 mb-4">
                    <div className="w-12 h-12 bg-brand-red/10 border border-brand-red/30 rounded-xl flex items-center justify-center">
                      <ShieldCheck size={24} className="text-brand-red" />
                    </div>
                    <h3 className="text-brand-text font-technical font-extrabold text-sm uppercase tracking-widest">Gas Safe Registration</h3>
                  </div>
                  <p className="text-[10px] text-brand-muted font-technical uppercase tracking-widest leading-loose">
                    All work is carried out by Gas Safe registered engineers. Gas Safe Reg: <span className="text-brand-red font-black">{COMPANY.gasSafeNumber}</span>
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-6">
                <Link
                  href="/contact"
                  className={`inline-flex items-center gap-4 bg-white text-black px-10 py-5 rounded-xl font-technical font-black text-[11px] uppercase tracking-[0.3em] transition-all hover:scale-105 shadow-2xl group`}
                >
                  Get a Quote
                  <ArrowRight size={16} className="transform group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href={`tel:${COMPANY.phone}`}
                  className="inline-flex items-center gap-4 bg-transparent border border-brand-card-border-hover hover:bg-brand-card text-brand-text px-10 py-5 rounded-xl font-technical font-black text-[11px] uppercase tracking-[0.3em] transition-all"
                >
                  <Phone size={16} className={accentClass} />
                  Call Us
                </a>
              </div>
            </motion.div>

            {/* Technical Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="relative h-[600px] rounded-[3rem] overflow-hidden shadow-2xl border border-brand-card-border bg-brand-navy group"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-brand-navy via-transparent to-transparent z-10" />
              <div className="absolute inset-0 z-20 opacity-10" style={{ backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)", backgroundSize: "30px 30px" }} />

              <Image
                src={sideImage}
                alt={sideImageAlt}
                fill
                className="object-cover grayscale opacity-40 group-hover:opacity-60 transition-opacity duration-700"
                sizes="(max-width: 1024px) 100vw, 50vw"
              />

              <div className="absolute top-10 left-10 z-30 p-4 border-l border-brand-red/50 bg-black/20 backdrop-blur-md rounded-r-xl">
                <p className="text-[8px] font-technical text-brand-red uppercase tracking-[0.4em]">DPS Heating Services</p>
              </div>

              <div className="absolute bottom-10 left-10 right-10 z-30">
                <div className="bg-brand-surface/80 backdrop-blur-2xl border border-brand-card-border-hover p-8 rounded-[2rem] flex items-center justify-between">
                  <div>
                    <p className="text-[9px] text-brand-muted uppercase tracking-[0.4em] font-bold mb-2">Gas Safe Registered</p>
                    <p className="text-brand-text font-technical font-extrabold text-sm uppercase tracking-widest">Ready to Help</p>
                  </div>
                  <div className={`w-14 h-14 rounded-xl border border-brand-card-border-hover bg-brand-card flex items-center justify-center transition-all group-hover:${accentBorderClass}/50`}>
                    <Activity size={24} className={accentClass} />
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Operational Parameters */}
      <section className="py-32 bg-brand-navy border-b border-brand-card-border relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-24">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border-hover bg-brand-card mb-6">
              <Database size={12} className="text-brand-muted" />
              <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.3em]">What&apos;s Included</span>
            </div>
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
              What&apos;s <span className={accentClass}>Included</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {included.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="bg-brand-surface border border-brand-card-border rounded-2xl p-8 flex items-center gap-6 hover:border-brand-red/30 transition-all group shadow-xl"
              >
                <div className={`w-8 h-8 rounded-lg bg-brand-card border border-brand-card-border-hover flex items-center justify-center shrink-0 group-hover:${accentBorderClass}/30 transition-colors`}>
                  <Zap size={14} className={accentClass} />
                </div>
                <p className="text-brand-muted text-[10px] font-technical uppercase tracking-widest leading-loose">{item}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Anomaly Detection */}
      <section className="py-40 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('/images/grid-pattern.png')] opacity-[0.03] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text mb-8 tracking-widest uppercase">
              Signs You May <span className="text-brand-red">Need This</span>
            </h2>
            <p className="text-brand-muted text-[11px] font-technical uppercase tracking-[0.4em] max-w-2xl mx-auto leading-loose">
              If you are experiencing any of the following, get in touch and we will advise on the best course of action.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
            {issues.map((issue, i) => {
              const Icon = ICON_MAP[issue.icon];
              return (
                <motion.div
                  key={issue.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 hover:border-brand-red/30 transition-all group relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />

                  <div className="w-16 h-16 bg-brand-surface border border-brand-card-border-hover rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-red/30 transition-all">
                    {Icon && <Icon size={28} className="text-brand-red" />}
                  </div>
                  <h3 className="font-technical font-extrabold text-brand-text mb-6 text-lg tracking-widest uppercase">{issue.title}</h3>
                  <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em] leading-loose">{issue.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Process Pipeline */}
      <ProcessSteps steps={steps} title="How We Work" dark={true} />

      {/* Assurance */}
      <section className="py-40 bg-brand-navy border-y border-brand-card-border relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase">
              Quality <span className={accentClass}>Assurance</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-20">
            {trustPoints.map((point) => {
              const Icon = ICON_MAP[point.icon];
              return (
                <div key={point.title} className="text-center group">
                  <div className="w-24 h-24 bg-brand-surface border border-brand-card-border rounded-[2rem] flex items-center justify-center mx-auto mb-10 group-hover:border-brand-red/30 transition-all rotate-3 group-hover:rotate-0 shadow-2xl">
                    {Icon && <Icon size={36} className="text-brand-text group-hover:text-brand-red transition-colors" />}
                  </div>
                  <h3 className="text-xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase">
                    {point.title}
                  </h3>
                  <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose">{point.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-40 bg-brand-surface border-b border-brand-card-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4">
              Frequently Asked <span className="text-brand-red">Questions</span>
            </h2>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-[0.4em]">Common questions answered.</p>
          </div>
          <FAQAccordion faqs={faqs} />
        </div>
      </section>

      {/* Transmission Portal */}
      <section className="py-40 bg-brand-steel" id="quote">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border bg-brand-card mb-8">
                <span className="text-brand-text/80 text-[10px] font-technical font-bold uppercase tracking-[0.3em]">
                  Request a Quote
                </span>
              </div>
              <h2 className="text-4xl md:text-7xl font-technical font-black text-brand-text mb-10 tracking-widest uppercase leading-tight">
                Ready to <br /> <span className="text-brand-red">Book?</span>
              </h2>
              <p className="text-brand-muted font-technical text-xs uppercase tracking-[0.3em] leading-loose mb-16 max-w-xl">
                Fill in the form and we will get back to you with a clear, no-obligation quote. Or call us directly to speak with our team.
              </p>

              <div className="bg-brand-card-hover rounded-[2.5rem] p-10 border border-brand-card-border shadow-inner">
                <div className="flex items-center gap-8">
                  <div className="w-20 h-20 bg-brand-red rounded-3xl flex items-center justify-center text-white shrink-0 shadow-2xl shadow-brand-red/20">
                    <Phone size={32} />
                  </div>
                  <div>
                    <p className="text-[10px] text-brand-muted uppercase font-technical font-bold tracking-[0.4em] mb-2 text-right">Call Us</p>
                    <p className="text-3xl md:text-4xl font-technical font-black text-brand-text tracking-tighter">{COMPANY.phone}</p>
                  </div>
                </div>
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="bg-brand-navy rounded-[3.5rem] p-12 md:p-20 shadow-2xl relative overflow-hidden border border-brand-card-border"
            >
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-red/5 blur-[150px] rounded-full pointer-events-none" />
              <QuoteForm preselectedService={serviceValue} />
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
}
