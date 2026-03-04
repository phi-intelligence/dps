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
  /** Visual theme for this detail page. Use "luxury" for the new gold/charcoal aesthetic. */
  theme?: "legacy" | "luxury";
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
  theme = "legacy",
  accentColor = "red",
}: ServiceDetailLayoutProps) {
  const { openQuoteModal } = useQuoteModal();
  const isLuxury = theme === "luxury";
  const accentClass = isLuxury
    ? "text-[#b8963a]"
    : accentColor === "red"
    ? "text-brand-red"
    : "text-brand-blue";
  const accentBgClass = isLuxury
    ? "bg-[#e2c977]"
    : accentColor === "red"
    ? "bg-brand-red"
    : "bg-brand-blue";
  const accentBorderClass = isLuxury
    ? "border-[#e2c977]"
    : accentColor === "red"
    ? "border-brand-red"
    : "border-brand-blue";
  const lightSectionBg = isLuxury ? "bg-[#f7f3ea]" : "bg-brand-surface";
  const darkSectionBg = isLuxury ? "bg-[#05080c]" : "bg-brand-navy";

  return (
    <div className={isLuxury ? "bg-[#f2ede3] text-brand-text overflow-x-hidden min-h-screen" : "bg-brand-surface text-brand-text min-h-screen"}>
      <PageHero
        title={title}
        subtitle={subtitle}
        breadcrumbs={breadcrumbs}
        backgroundImage={backgroundImage}
        preselectedService={serviceValue}
        variant={isLuxury ? "luxury" : undefined}
        compact
      />

      {showGasSafeNote && (
        <section
          className={
            isLuxury
              ? "py-4 bg-[#05080c] border-y border-white/10"
              : "py-4 bg-brand-navy border-y border-brand-card-border"
          }
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-center gap-6">
            <div className="flex items-center gap-4">
              <div
                className={
                  isLuxury
                    ? "w-10 h-10 bg-[#e2c977]/10 border border-[#e2c977]/40 rounded-xl flex items-center justify-center shrink-0"
                    : "w-10 h-10 bg-brand-red/10 border border-brand-red/30 rounded-xl flex items-center justify-center shrink-0"
                }
              >
                <ShieldCheck size={20} className={isLuxury ? "text-[#e2c977]" : "text-brand-red"} />
              </div>
              <p
                className={
                  isLuxury
                    ? "text-[10px] text-[#b3c0d0] font-technical uppercase tracking-widest"
                    : "text-[10px] text-brand-muted font-technical uppercase tracking-widest"
                }
              >
                All gas work by Gas Safe registered engineers. Gas Safe Reg:{" "}
                <span className={`${accentClass} font-black`}>{COMPANY.gasSafeNumber}</span>
              </p>
            </div>
            <a
              href={`tel:${COMPANY.phone}`}
              className={
                isLuxury
                  ? "inline-flex items-center gap-2 text-white font-technical font-bold text-xs uppercase tracking-widest hover:text-[#e2c977] transition-colors"
                  : "inline-flex items-center gap-2 text-brand-text font-technical font-bold text-xs uppercase tracking-widest hover:text-brand-red transition-colors"
              }
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
                className={`relative py-20 md:py-28 ${i % 2 === 0 ? lightSectionBg : darkSectionBg}`}
              >
                {isLuxury && (
                  <div className="pointer-events-none absolute inset-0">
                    {i % 2 === 0 ? (
                      <>
                        <div className="absolute -right-32 top-8 h-52 w-64 rotate-3 rounded-[3rem] border border-[#e2c977]/24 bg-[#e2c977]/6" />
                        <div className="absolute -left-24 bottom-8 h-40 w-56 -rotate-6 rounded-[3rem] border border-[#d4af37]/18 bg-[#d4af37]/6" />
                      </>
                    ) : (
                      <>
                        <div className="absolute inset-x-16 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/26 to-transparent" />
                        <div className="absolute -right-40 bottom-0 h-64 w-72 -rotate-3 rounded-[3rem] border border-white/12 bg-white/5" />
                      </>
                    )}
                  </div>
                )}
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
                  <div className={`grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center`}>
                    <div className={!isImageLeft ? "lg:order-2" : ""}>
                      <div
                        className={
                          isLuxury
                            ? "relative aspect-[4/3] rounded-[1.75rem] overflow-hidden border border-white/10 bg-[#05080c] shadow-[0_26px_80px_rgba(0,0,0,0.5)]"
                            : "relative aspect-[4/3] rounded-[1.75rem] overflow-hidden border border-brand-card-border bg-brand-navy shadow-2xl"
                        }
                      >
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
                        <div className="absolute bottom-4 left-4 right-4 flex items-center gap-2">
                          <span
                            className={`w-8 h-8 rounded-lg ${accentBgClass} ${
                              isLuxury ? "bg-opacity-90" : "/90"
                            } flex items-center justify-center`}
                          >
                            <Check size={16} className="text-white" strokeWidth={2.5} />
                          </span>
                          <span className="text-white font-technical font-bold text-xs uppercase tracking-widest drop-shadow-md">{card.title}</span>
                        </div>
                      </div>
                    </div>
                    <div className={!isImageLeft ? "lg:order-1" : ""}>
                      <span
                        className={
                          isLuxury
                            ? "text-[9px] font-technical font-bold text-[#6b737b] uppercase tracking-[0.35em]"
                            : "text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]"
                        }
                      >
                        Service {String(i + 1).padStart(2, "0")}
                      </span>
                      <h2
                        className={
                          isLuxury && i % 2 !== 0
                            ? "text-2xl md:text-4xl font-technical font-extrabold text-white mt-2 mb-6 tracking-[0.24em] uppercase"
                            : isLuxury
                            ? "text-2xl md:text-4xl font-technical font-extrabold text-[#171b1f] mt-2 mb-6 tracking-[0.24em] uppercase"
                            : "text-2xl md:text-4xl font-technical font-extrabold text-brand-text mt-2 mb-6 tracking-widest uppercase"
                        }
                      >
                        {card.title}
                      </h2>
                      <p
                        className={
                          isLuxury && i % 2 !== 0
                            ? "text-[#d7dee6] text-sm font-technical uppercase tracking-wide leading-relaxed max-w-xl"
                            : isLuxury
                            ? "text-[#3c444b] text-sm font-technical uppercase tracking-wide leading-relaxed max-w-xl"
                            : "text-brand-muted text-sm font-technical uppercase tracking-wide leading-relaxed max-w-xl"
                        }
                      >
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
              <section
                className={`py-24 md:py-32 relative overflow-hidden ${
                  isLuxury ? "bg-[#f7f3ea]" : "bg-brand-surface"
                }`}
              >
                <div
                  className={
                    isLuxury
                      ? "absolute top-0 left-0 w-[500px] h-[500px] bg-[#e2c977]/20 blur-[140px] rounded-full pointer-events-none"
                      : "absolute top-0 left-0 w-[500px] h-[500px] bg-brand-red/5 blur-[120px] rounded-full pointer-events-none"
                  }
                />
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                  <div className="mb-16">
                    <span
                      className={
                        isLuxury
                          ? "text-[9px] font-technical font-bold text-[#6b737b] uppercase tracking-[0.35em]"
                          : "text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]"
                      }
                    >
                      What we offer
                    </span>
                    <h2
                      className={
                        isLuxury
                          ? "text-3xl md:text-5xl font-technical font-extrabold text-[#171b1f] mt-3 tracking-[0.26em] uppercase"
                          : "text-3xl md:text-5xl font-technical font-extrabold text-brand-text mt-3 tracking-widest uppercase"
                      }
                    >
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
                        className={
                          isLuxury
                            ? "group relative rounded-[1.5rem] border overflow-hidden bg-[#05080c]/95 backdrop-blur-sm border-white/10 hover:border-[#e2c977]/50 transition-colors"
                            : `group relative rounded-[1.5rem] border overflow-hidden bg-brand-navy/80 backdrop-blur-sm ${
                                accentColor === "red"
                                  ? "border-brand-card-border hover:border-brand-red/40"
                                  : "border-brand-card-border hover:border-brand-blue/40"
                              }`
                        }
                      >
                        <div
                          className={`absolute left-0 top-0 bottom-0 w-1 ${accentBgClass} ${
                            isLuxury ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                          } transition-opacity`}
                        />
                        <div className="p-8 md:p-10 flex items-start gap-6">
                          <div
                            className={
                              isLuxury
                                ? "w-12 h-12 rounded-xl border border-white/10 flex items-center justify-center shrink-0 bg-white/5"
                                : `w-12 h-12 rounded-xl border border-brand-card-border-hover flex items-center justify-center shrink-0 ${
                                    accentColor === "red"
                                      ? "bg-brand-red/10 group-hover:bg-brand-red/20"
                                      : "bg-brand-blue/10 group-hover:bg-brand-blue/20"
                                  }`
                            }
                          >
                            <Check size={22} className={accentClass} strokeWidth={2.5} />
                          </div>
                          <p
                            className={
                              isLuxury
                                ? "text-white text-sm font-technical font-semibold uppercase tracking-wide leading-snug pt-1"
                                : "text-brand-text text-sm font-technical font-semibold uppercase tracking-wide leading-snug pt-1"
                            }
                          >
                            {item}
                          </p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </section>
              {rest.length > 0 && (
                <section
                  className={
                    isLuxury
                      ? "py-20 md:py-28 bg-[#05080c] relative overflow-hidden"
                      : "py-20 md:py-28 bg-brand-navy relative overflow-hidden"
                  }
                >
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="mb-12">
                      <span
                        className={
                          isLuxury
                            ? "text-[9px] font-technical font-bold text-[#9aa3b0] uppercase tracking-[0.35em]"
                            : "text-[9px] font-technical font-bold text-brand-muted uppercase tracking-[0.35em]"
                        }
                      >
                        Full list
                      </span>
                      <h2
                        className={
                          isLuxury
                            ? "text-2xl md:text-4xl font-technical font-extrabold text-white mt-2 tracking-[0.26em] uppercase"
                            : "text-2xl md:text-4xl font-technical font-extrabold text-brand-text mt-2 tracking-widest uppercase"
                        }
                      >
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
                            className={
                              isLuxury
                                ? "flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 px-5 py-4 hover:border-[#e2c977]/50 transition-colors"
                                : "flex items-center gap-4 rounded-xl border border-brand-card-border bg-brand-surface/30 px-5 py-4 hover:border-brand-card-border-hover transition-colors"
                            }
                          >
                            <span
                              className={
                                isLuxury
                                  ? "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-[#e2c977]/10 border border-[#e2c977]/30"
                                  : `w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                                      accentColor === "red"
                                        ? "bg-brand-red/10 border border-brand-red/20"
                                        : "bg-brand-blue/10 border border-brand-blue/20"
                                    }`
                              }
                            >
                              <Check size={12} className={accentClass} strokeWidth={2.5} />
                            </span>
                            <span
                              className={
                                isLuxury
                                  ? "text-[#d7dee6] text-[10px] font-technical uppercase tracking-widest leading-snug"
                                  : "text-brand-muted text-[10px] font-technical uppercase tracking-widest leading-snug"
                              }
                            >
                              {item}
                            </span>
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
      <section
        className={
          isLuxury
            ? "py-32 md:py-40 relative overflow-hidden bg-[#0b1015]"
            : "py-40 relative overflow-hidden"
        }
      >
        <div
          className={
            isLuxury
              ? "absolute top-0 left-0 w-full h-full opacity-70 pointer-events-none"
              : "absolute top-0 left-0 w-full h-full opacity-[0.03] pointer-events-none"
          }
          style={
            isLuxury
              ? {
                  backgroundImage:
                    "radial-gradient(circle at top left, rgba(226,201,119,0.2), transparent 55%), radial-gradient(circle at bottom right, rgba(7,12,18,0.9), transparent 55%)",
                }
              : {
                  backgroundImage:
                    "linear-gradient(var(--color-brand-card-hover) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card-hover) 1px, transparent 1px)",
                  backgroundSize: "24px 24px",
                }
          }
        />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-24">
            <h2
              className={
                isLuxury
                  ? "text-4xl md:text-6xl font-technical font-black text-white mb-8 tracking-[0.26em] uppercase"
                  : "text-4xl md:text-7xl font-technical font-black text-brand-text mb-8 tracking-widest uppercase"
              }
            >
              Signs You May <span className={accentClass}>Need This</span>
            </h2>
            <p
              className={
                isLuxury
                  ? "text-[#9aa3b0] text-[11px] font-technical uppercase tracking-[0.4em] max-w-2xl mx-auto leading-loose"
                  : "text-brand-muted text-[11px] font-technical uppercase tracking-[0.4em] max-w-2xl mx-auto leading-loose"
              }
            >
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
                  className={
                    isLuxury
                      ? "bg-[#05080c] border border-white/10 rounded-[2.5rem] p-10 hover:border-[#e2c977]/40 transition-all group relative overflow-hidden"
                      : "bg-brand-navy border border-brand-card-border rounded-[2.5rem] p-10 hover:border-brand-red/30 transition-all group relative overflow-hidden"
                  }
                >
                  <div
                    className={
                      isLuxury
                        ? "absolute top-0 right-0 w-32 h-32 bg-[#e2c977]/20 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity"
                        : "absolute top-0 right-0 w-32 h-32 bg-brand-red/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity"
                    }
                  />

                  <div
                    className={
                      isLuxury
                        ? "w-16 h-16 bg-[#0b1015] border border-white/10 rounded-2xl flex items-center justify-center mb-8 group-hover:border-[#e2c977]/40 transition-all"
                        : "w-16 h-16 bg-brand-surface border border-brand-card-border-hover rounded-2xl flex items-center justify-center mb-8 group-hover:border-brand-red/30 transition-all"
                    }
                  >
                    {Icon && <Icon size={28} className={accentClass} />}
                  </div>
                  <h3
                    className={
                      isLuxury
                        ? "font-technical font-extrabold text-white mb-6 text-lg tracking-[0.24em] uppercase"
                        : "font-technical font-extrabold text-brand-text mb-6 text-lg tracking-widest uppercase"
                    }
                  >
                    {issue.title}
                  </h3>
                  <p
                    className={
                      isLuxury
                        ? "text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.2em] leading-loose"
                        : "text-brand-muted text-[10px] font-technical uppercase tracking-[0.2em] leading-loose"
                    }
                  >
                    {issue.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Process Pipeline */}
      <ProcessSteps steps={steps} title="How We Work" dark={true} />

      {/* Assurance */}
      <section
        className={
          isLuxury ? "py-32 md:py-40 bg-[#05080c] relative overflow-hidden" : "py-40 bg-brand-navy relative overflow-hidden"
        }
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-32">
            <h2
              className={
                isLuxury
                  ? "text-4xl md:text-6xl font-technical font-black text-white tracking-[0.26em] uppercase"
                  : "text-4xl md:text-7xl font-technical font-black text-brand-text tracking-widest uppercase"
              }
            >
              Quality <span className={accentClass}>Assurance</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-20">
            {trustPoints.map((point) => {
              const Icon = ICON_MAP[point.icon];
              return (
                <div key={point.title} className="text-center group">
                  <div
                    className={
                      isLuxury
                        ? "w-24 h-24 bg-[#0b1015] border border-white/10 rounded-[2rem] flex items-center justify-center mx-auto mb-10 group-hover:border-[#e2c977]/40 transition-all rotate-3 group-hover:rotate-0 shadow-2xl"
                        : "w-24 h-24 bg-brand-surface border border-brand-card-border rounded-[2rem] flex items-center justify-center mx-auto mb-10 group-hover:border-brand-red/30 transition-all rotate-3 group-hover:rotate-0 shadow-2xl"
                    }
                  >
                    {Icon && (
                      <Icon
                        size={36}
                        className={
                          isLuxury
                            ? "text-white group-hover:text-[#e2c977] transition-colors"
                            : "text-brand-text group-hover:text-brand-red transition-colors"
                        }
                      />
                    )}
                  </div>
                  <h3
                    className={
                      isLuxury
                        ? "text-xl font-technical font-extrabold text-white mb-6 tracking-[0.26em] uppercase"
                        : "text-xl font-technical font-extrabold text-brand-text mb-6 tracking-widest uppercase"
                    }
                  >
                    {point.title}
                  </h3>
                  <p
                    className={
                      isLuxury
                        ? "text-[#9aa3b0] text-[10px] font-technical uppercase tracking-[0.3em] leading-loose"
                        : "text-brand-muted text-[10px] font-technical uppercase tracking-[0.3em] leading-loose"
                    }
                  >
                    {point.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section
        className={
          isLuxury ? "py-32 md:py-40 bg-[#f7f3ea]" : "py-40 bg-brand-surface"
        }
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h2
              className={
                isLuxury
                  ? "text-4xl md:text-5xl font-technical font-extrabold text-[#171b1f] tracking-[0.26em] uppercase mb-4"
                  : "text-4xl md:text-6xl font-technical font-extrabold text-brand-text tracking-widest uppercase mb-4"
              }
            >
              Frequently Asked <span className={accentClass}>Questions</span>
            </h2>
            <p
              className={
                isLuxury
                  ? "text-[#6b737b] text-[10px] font-technical uppercase tracking-[0.4em]"
                  : "text-brand-muted text-[10px] font-technical uppercase tracking-[0.4em]"
              }
            >
              Common questions answered.
            </p>
          </div>
          <FAQAccordion faqs={faqs} />
        </div>
      </section>

      {/* Transmission Portal */}
      <section
        className={
          isLuxury ? "py-24 md:py-32 bg-[#0f1720]" : "py-40 bg-brand-steel"
        }
        id="quote"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="max-w-xl">
              <div
                className={
                  isLuxury
                    ? "inline-flex items-center gap-2 px-3 py-1 rounded-md border border-white/10 bg-white/5 mb-8"
                    : "inline-flex items-center gap-2 px-3 py-1 rounded-md border border-brand-card-border bg-brand-card mb-8"
                }
              >
                <span
                  className={
                    isLuxury
                      ? "text-white/90 text-[10px] font-technical font-bold uppercase tracking-[0.3em]"
                      : "text-brand-text/80 text-[10px] font-technical font-bold uppercase tracking-[0.3em]"
                  }
                >
                  Request a Quote
                </span>
              </div>
              <h2
                className={
                  isLuxury
                    ? "text-3xl md:text-4xl font-technical font-black text-white mb-6 tracking-[0.26em] uppercase leading-tight"
                    : "text-4xl md:text-7xl font-technical font-black text-brand-text mb-10 tracking-widest uppercase leading-tight"
                }
              >
                Ready to <span className={accentClass}>Book?</span>
              </h2>
              <p
                className={
                  isLuxury
                    ? "text-[#9aa3b0] font-technical text-xs uppercase tracking-[0.3em] leading-loose mb-16 max-w-xl"
                    : "text-brand-muted font-technical text-xs uppercase tracking-[0.3em] leading-loose mb-16 max-w-xl"
                }
              >
                Fill in the form and we will get back to you with a clear, no-obligation quote. Or call us directly to speak with our team.
              </p>

              <div
                className={
                  isLuxury
                    ? "bg-[#05080c] rounded-[2rem] p-6 md:p-8 border border-white/10 shadow-[0_18px_50px_rgba(0,0,0,0.6)] max-w-md"
                    : "bg-brand-card-hover rounded-[2.5rem] p-10 border border-brand-card-border shadow-inner"
                }
              >
                <div className="flex items-center gap-6">
                  <div
                    className={
                      isLuxury
                        ? "w-20 h-20 bg-[#e2c977] rounded-3xl flex items-center justify-center text-[#05080c] shrink-0 shadow-2xl shadow-[#e2c977]/40"
                        : "w-20 h-20 bg-brand-red rounded-3xl flex items-center justify-center text-white shrink-0 shadow-2xl shadow-brand-red/20"
                    }
                  >
                    <Phone size={32} />
                  </div>
                  <div>
                    <p
                      className={
                        isLuxury
                          ? "text-[10px] text-[#9aa3b0] uppercase font-technical font-bold tracking-[0.4em] mb-1"
                          : "text-[10px] text-brand-muted uppercase font-technical font-bold tracking-[0.4em] mb-2 text-right"
                      }
                    >
                      Call Us Directly
                    </p>
                    <p
                      className={
                        isLuxury
                          ? "text-3xl md:text-4xl font-technical font-black text-white tracking-tighter"
                          : "text-3xl md:text-4xl font-technical font-black text-brand-text tracking-tighter"
                      }
                    >
                      {COMPANY.phone}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className={
                isLuxury
                  ? "bg-[#05080c] rounded-[2.75rem] p-8 md:p-10 shadow-[0_22px_70px_rgba(0,0,0,0.85)] relative overflow-hidden border border-white/10 max-w-xl ml-auto"
                  : "bg-brand-navy rounded-[3.5rem] p-12 md:p-20 shadow-2xl relative overflow-hidden border border-brand-card-border"
              }
            >
              <div
                className={
                  isLuxury
                    ? "absolute top-0 right-0 w-[420px] h-[420px] bg-[#e2c977]/18 blur-[140px] rounded-full pointer-events-none"
                    : "absolute top-0 right-0 w-[500px] h-[500px] bg-brand-red/5 blur-[150px] rounded-full pointer-events-none"
                }
              />
              <QuoteForm preselectedService={serviceValue} />
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
}
