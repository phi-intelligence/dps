"use client";

import Image from "next/image";
import { Phone, ShieldCheck, Check } from "lucide-react";
import PageHero from "@/components/ui/PageHero";
import ProcessSteps, { ProcessStep } from "@/components/sections/ProcessSteps";
import FAQAccordion, { FAQItem } from "@/components/ui/FAQAccordion";
import QuoteForm from "@/components/ui/QuoteForm";
import { COMPANY } from "@/lib/constants";
import { useQuoteModal } from "@/lib/quote-modal-context";
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

/** When provided, each service is rendered as its own card/section with image, title, and description. */
export interface ServiceCard {
  title: string;
  description: string;
  image: string;
  imageAlt?: string;
}

interface ServiceDetailLayoutProps {
  title: string;
  subtitle: string;
  backgroundImage: string;
  sideImage: string;
  sideImageAlt: string;
  introduction: string;
  included: string[];
  /** Optional: per-service cards with image and description. When set, replaces the default included list UI. */
  serviceCards?: ServiceCard[];
  issues: IssueCard[];
  steps: ProcessStep[];
  trustPoints: TrustPoint[];
  faqs: FAQItem[];
  breadcrumbs: { label: string; href?: string }[];
  serviceValue: string;
  showGasSafeNote?: boolean;
  accentColor?: "red" | "blue";
}

/** Splits included services into featured (first N) and rest for varied layout. */
function chunkServices(included: string[], featuredCount = 4): { featured: string[]; rest: string[] } {
  if (included.length <= featuredCount) return { featured: included, rest: [] };
  return { featured: included.slice(0, featuredCount), rest: included.slice(featuredCount) };
}

export default function ServiceDetailLayout({
  title,
  subtitle,
  backgroundImage,
  sideImage,
  sideImageAlt,
  introduction,
  included,
  serviceCards,
  issues,
  steps,
  trustPoints,
  faqs,
  breadcrumbs,
  serviceValue,
  showGasSafeNote = false,
  accentColor = "red",
}: ServiceDetailLayoutProps) {
  const { openQuoteModal } = useQuoteModal();
  const accentClass = accentColor === "red" ? "text-brand-red" : "text-brand-blue";
  const accentBgClass = accentColor === "red" ? "bg-brand-red" : "bg-brand-blue";
  const accentBorderClass = accentColor === "red" ? "border-brand-red" : "border-brand-blue";

  return (
    <div className="bg-brand-surface text-brand-text min-h-screen">
      <PageHero
        title={title}
        subtitle={subtitle}
        breadcrumbs={breadcrumbs}
        backgroundImage={backgroundImage}
        preselectedService={serviceValue}
        compact
      />

      {showGasSafeNote && (
        <section className="py-4 bg-brand-navy border-y border-brand-card-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-center gap-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-brand-red/10 border border-brand-red/30 rounded-xl flex items-center justify-center shrink-0">
                <ShieldCheck size={20} className="text-brand-red" />
              </div>
              <p className="text-[10px] text-brand-muted font-technical uppercase tracking-widest">
                All gas work by Gas Safe registered engineers. Gas Safe Reg: <span className="text-brand-red font-black">{COMPANY.gasSafeNumber}</span>
              </p>
            </div>
            <a
              href={`tel:${COMPANY.phone}`}
              className="inline-flex items-center gap-2 text-brand-text font-technical font-bold text-xs uppercase tracking-widest hover:text-brand-red transition-colors"
            >
              <Phone size={14} />
              Call for a quote
            </a>
          </div>
        </section>
      )}

      {/* Services: either per-service cards (image + description) or legacy included list */}
      {serviceCards && serviceCards.length > 0 ? (
        <section className="relative overflow-hidden">
          {serviceCards.map((card, i) => {
            const isImageLeft = i % 2 === 0;
            return (
              <motion.article
                key={i}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
                className={`relative py-20 md:py-28 ${i % 2 === 0 ? "bg-brand-surface" : "bg-brand-navy"}`}
              >
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className={`grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center`}>
                    <div className={!isImageLeft ? "lg:order-2" : ""}>
                      <div className="relative aspect-[4/3] rounded-[1.75rem] overflow-hidden border border-brand-card-border bg-brand-navy shadow-2xl">
                        {card.image ? (
                          <Image
                            src={card.image}
                            alt={card.imageAlt ?? card.title}
                            fill
                            className="object-cover"
                            sizes="(max-width: 1024px) 100vw, 50vw"
                          />
                        ) : (
                          <div className="absolute inset-0 bg-brand-navy flex items-center justify-center" aria-hidden />
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
                        <div className={`absolute bottom-4 left-4 right-4 flex items-center gap-2`}>
                          <span className={`w-8 h-8 rounded-lg ${accentBgClass}/90 flex items-center justify-center`}>
                            <Check size={16} className="text-white" strokeWidth={2.5} />
                          </span>
                          <span className="text-white font-technical font-bold text-xs uppercase tracking-widest drop-shadow-md">{card.title}</span>
                        </div>
                      </div>
                    </div>
                    <div className={!isImageLeft ? "lg:order-1" : ""}>
                      <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]">Service {String(i + 1).padStart(2, "0")}</span>
                      <h2 className="text-2xl md:text-4xl font-technical font-extrabold text-brand-text mt-2 mb-6 tracking-widest uppercase">
                        {card.title}
                      </h2>
                      <p className="text-brand-muted text-sm font-technical uppercase tracking-wide leading-relaxed max-w-xl">
                        {card.description}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.article>
            );
          })}
        </section>
      ) : (
        (() => {
          const { featured, rest } = chunkServices(included, 4);
          return (
            <>
              <section className="py-24 md:py-32 bg-brand-surface relative overflow-hidden">
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-brand-red/5 blur-[120px] rounded-full pointer-events-none" />
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                  <div className="mb-16">
                    <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]">What we offer</span>
                    <h2 className="text-3xl md:text-5xl font-technical font-extrabold text-brand-text mt-3 tracking-widest uppercase">
                      Core <span className={accentClass}>services</span>
                    </h2>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 md:gap-8">
                    {featured.map((item, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.08 }}
                        className={`group relative rounded-[1.5rem] border overflow-hidden bg-brand-navy/80 backdrop-blur-sm ${accentColor === "red" ? "border-brand-card-border hover:border-brand-red/40" : "border-brand-card-border hover:border-brand-blue/40"}`}
                      >
                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${accentBgClass} opacity-0 group-hover:opacity-100 transition-opacity`} />
                        <div className="p-8 md:p-10 flex items-start gap-6">
                          <div className={`w-12 h-12 rounded-xl border border-brand-card-border-hover flex items-center justify-center shrink-0 ${accentColor === "red" ? "bg-brand-red/10 group-hover:bg-brand-red/20" : "bg-brand-blue/10 group-hover:bg-brand-blue/20"}`}>
                            <Check size={22} className={accentClass} strokeWidth={2.5} />
                          </div>
                          <p className="text-brand-text text-sm font-technical font-semibold uppercase tracking-wide leading-snug pt-1">{item}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </section>
              {rest.length > 0 && (
                <section className="py-20 md:py-28 bg-brand-navy relative overflow-hidden">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="mb-12">
                      <span className="text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]">Full list</span>
                      <h2 className="text-2xl md:text-4xl font-technical font-extrabold text-brand-text mt-2 tracking-widest uppercase">
                        Also <span className={accentClass}>included</span>
                      </h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5 max-w-5xl">
                      {rest.map((item, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          whileInView={{ opacity: 1, y: 0 }}
                          viewport={{ once: true }}
                          transition={{ delay: i * 0.04 }}
                          className="flex items-center gap-4 rounded-xl border border-brand-card-border bg-brand-surface/30 px-5 py-4 hover:border-brand-card-border-hover transition-colors"
                        >
                          <span className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${accentColor === "red" ? "bg-brand-red/10 border border-brand-red/20" : "bg-brand-blue/10 border border-brand-blue/20"}`}>
                            <Check size={12} className={accentClass} strokeWidth={2.5} />
                          </span>
                          <span className="text-brand-muted text-[10px] font-technical uppercase tracking-widest leading-snug">{item}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </section>
              )}
            </>
          );
        })()
      )}

      {/* Anomaly Detection */}
      <section className="py-40 relative overflow-hidden">
        <div
          className="absolute top-0 left-0 w-full h-full opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
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
      <section className="py-40 bg-brand-navy relative overflow-hidden">
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
      <section className="py-40 bg-brand-surface">
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
