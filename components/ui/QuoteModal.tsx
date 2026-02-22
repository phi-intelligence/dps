"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  X,
  CheckCircle,
  Send,
  Cpu,
  Activity,
  ChevronRight,
  Zap,
  Flame,
  Wind,
  Wrench,
  Settings,
  ShieldCheck,
  ClipboardList,
  Thermometer,
} from "lucide-react";
import { useTheme } from "@/lib/theme-provider";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { inquiryService } from "@/lib/inquiry-service";
import { QUOTE_SERVICES } from "@/components/ui/QuoteForm";
import Image from "next/image";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

const inputClass =
  "quote-modal-input w-full border border-brand-card-border-hover rounded-xl px-6 py-5 text-brand-text text-[12px] font-technical uppercase tracking-widest placeholder-brand-muted/30 focus:outline-none focus:border-brand-red/50 transition-all shadow-2xl";

interface QuoteModalProps {
  open: boolean;
  onClose: () => void;
  preselectedService?: string;
}

function getFocusables(container: HTMLElement): HTMLElement[] {
  const selector =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  return Array.from(container.querySelectorAll<HTMLElement>(selector));
}

const SERVICE_METADATA: Record<string, { image: string; icon: any; category: string }> = {
  "boiler-repair": { image: "/images/boiler-repair.jpg", icon: Flame, category: "Heating" },
  "boiler-installation": { image: "/images/boiler-install.jpg", icon: Settings, category: "Heating" },
  "boiler-servicing": { image: "/images/boiler-modern.jpg", icon: Activity, category: "Heating" },
  "central-heating": { image: "/images/central-heating.jpg", icon: Thermometer, category: "Heating" },
  "radiators": { image: "/images/radiator-pipes.png", icon: Activity, category: "Heating" },
  "power-flushing": { image: "/images/plumbing-pipes.jpg", icon: Wrench, category: "Heating" },
  "ac-installation": { image: "/images/ac-installation.jpg", icon: Wind, category: "Climate" },
  "ac-servicing": { image: "/images/ac-unit-indoor.jpg", icon: Activity, category: "Climate" },
  "ac-repairs": { image: "/images/exploded-ac.png", icon: Wrench, category: "Climate" },
  "commercial-ac": { image: "/images/blueprint-commercial-system.png", icon: Cpu, category: "Climate" },
  "ac-maintenance": { image: "/images/team-professional.jpg", icon: ClipboardList, category: "Climate" },
  "other": { image: "/images/logo.jpg", icon: ShieldCheck, category: "General" },
};

export default function QuoteModal({
  open,
  onClose,
  preselectedService = "",
}: QuoteModalProps) {
  const [step, setStep] = useState(1);
  const [status, setStatus] = useState<"idle" | "loading" | "success">("idle");
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    service: preselectedService,
    message: "",
  });
  const panelRef = useRef<HTMLDivElement>(null);
  const previousActiveRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (preselectedService) setForm((f) => ({ ...f, service: preselectedService }));
  }, [preselectedService, open]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const selectService = (value: string) => {
    setForm((prev) => ({ ...prev, service: value }));
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step < 3) {
      setStep(step + 1);
      return;
    }
    setStatus("loading");
    // Persist inquiry data
    inquiryService.addInquiry({
      name: form.name,
      phone: form.phone,
      email: form.email,
      service: form.service,
      message: form.message,
    });
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setStatus("success");
  };

  const handleClose = useCallback(() => {
    setStep(1);
    setStatus("idle");
    setForm({ name: "", phone: "", email: "", service: preselectedService, message: "" });
    onClose();
  }, [onClose, preselectedService]);

  useEffect(() => {
    if (!open) return;
    previousActiveRef.current = document.activeElement as HTMLElement | null;
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
      if (previousActiveRef.current?.focus) previousActiveRef.current.focus();
    };
  }, [open, handleClose]);

  useEffect(() => {
    if (!open || !panelRef.current) return;
    const el = panelRef.current;
    const focusables = getFocusables(el);
    const first = focusables[0];
    if (first) first.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const focusables = getFocusables(el);
      if (focusables.length === 0) return;
      const i = focusables.indexOf(document.activeElement as HTMLElement);
      const next = e.shiftKey ? (i <= 0 ? focusables[focusables.length - 1] : focusables[i - 1]) : (i === -1 || i >= focusables.length - 1 ? focusables[0] : focusables[i + 1]);
      if (next) {
        e.preventDefault();
        next.focus();
      }
    };
    el.addEventListener("keydown", handleKeyDown);
    return () => el.removeEventListener("keydown", handleKeyDown);
  }, [open, step, status]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="quote-modal-overlay absolute inset-0"
            aria-hidden
            onClick={handleClose}
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="quote-modal-title"
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
            className={`quote-modal-opaque relative z-[101] w-full ${step === 1 ? 'max-w-6xl' : 'max-w-5xl'} max-h-[90vh] overflow-y-auto rounded-3xl bg-white dark:bg-brand-steel border border-brand-card-border shadow-2xl premium-shadow`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="absolute inset-0 opacity-30 pointer-events-none overflow-hidden rounded-3xl">
              <EnergyFlowBackground />
            </div>

            <div className="quote-modal-header sticky top-0 z-30 flex items-center justify-between px-8 py-6 bg-white/80 dark:bg-brand-steel/80 backdrop-blur-md border-b border-brand-card-border">
              <div>
                <h2
                  id="quote-modal-title"
                  className="text-2xl font-sans font-extrabold text-brand-text mb-1"
                >
                  Request a Quote
                </h2>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-brand-red animate-pulse" />
                  <span className="text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted">Step {step} of 3</span>
                </div>
              </div>
              <button
                type="button"
                onClick={handleClose}
                className="w-12 h-12 rounded-full flex items-center justify-center text-brand-muted hover:bg-brand-surface dark:hover:bg-brand-navy hover:text-brand-text transition-all premium-shadow"
                aria-label="Close"
              >
                <X size={24} />
              </button>
            </div>

            <div className="quote-modal-content p-6 md:p-8">
              <AnimatePresence mode="wait">
                {status === "success" ? (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center text-center gap-6 py-8"
                  >
                    <div className="w-16 h-16 rounded-full bg-brand-red/10 flex items-center justify-center">
                      <CheckCircle size={32} className="text-brand-red animate-pulse" />
                    </div>
                    <div>
                      <p className="font-technical font-extrabold text-xl tracking-[0.2em] uppercase text-brand-text">
                        Uplink Successful
                      </p>
                      <p className="text-[10px] text-brand-muted font-technical uppercase tracking-[0.2em] mt-4 leading-loose">
                        Data transmission complete. <br />
                        Engineering dispatch confirmed via primary channel.
                      </p>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-3 w-full">
                      <button
                        type="button"
                        onClick={handleClose}
                        className="flex-1 px-6 py-4 rounded-xl font-technical font-bold text-[12px] uppercase tracking-widest bg-brand-red text-white hover:bg-brand-red/90 transition-colors"
                      >
                        Close
                      </button>
                      <Link
                        href="/contact"
                        onClick={handleClose}
                        className="flex-1 text-center px-6 py-4 rounded-xl font-technical font-bold text-[12px] uppercase tracking-widest border border-brand-card-border-hover text-brand-text hover:bg-brand-card transition-colors"
                      >
                        Go to contact page
                      </Link>
                    </div>
                  </motion.div>
                ) : (
                  <motion.form
                    key={`step-${step}`}
                    initial={{ opacity: 0, x: step === 1 ? -10 : 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: step === 1 ? 10 : -10 }}
                    transition={{ duration: 0.2 }}
                    onSubmit={handleSubmit}
                    className="space-y-6"
                  >
                    {/* Step 1: Service Selection Grid */}
                    {step === 1 && (
                      <div className="space-y-12">
                        <div className="text-center max-w-2xl mx-auto mb-12">
                          <h3 className="text-3xl font-sans font-extrabold text-brand-text mb-4 tracking-tight">How can we help you today?</h3>
                          <p className="text-brand-muted font-medium text-lg leading-relaxed">Select the service you require to begin your custom quote transmission.</p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                          {QUOTE_SERVICES.filter(s => s.value !== "").map((s) => {
                            const meta = SERVICE_METADATA[s.value as keyof typeof SERVICE_METADATA] || SERVICE_METADATA["other"];
                            const MetaIcon = meta.icon;

                            return (
                              <motion.button
                                key={s.value}
                                type="button"
                                whileHover={{ y: -4 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => selectService(s.value)}
                                className={`group relative h-52 rounded-[2rem] overflow-hidden border transition-all duration-300 bg-slate-900 ${form.service === s.value
                                  ? "border-brand-red ring-2 ring-brand-red/30 shadow-lg shadow-brand-red/10"
                                  : "border-white/10 hover:border-brand-red/50"
                                  }`}
                              >
                                {/* Image — visible by default, full colour on hover */}
                                <Image
                                  src={meta.image}
                                  alt={s.label}
                                  fill
                                  className="object-cover opacity-55 grayscale group-hover:opacity-80 group-hover:grayscale-0 group-hover:scale-105 transition-all duration-600"
                                />
                                {/* Fixed dark scrim — works in both light & dark modal */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/35 to-black/5 z-10" />

                                <div className="absolute inset-0 z-20 p-6 flex flex-col justify-end items-start">
                                  <div className="w-11 h-11 rounded-xl bg-white/15 border border-white/20 backdrop-blur-sm flex items-center justify-center mb-3 group-hover:bg-brand-red group-hover:border-brand-red transition-all duration-300">
                                    <MetaIcon size={22} className="text-white transition-colors" />
                                  </div>
                                  <div className="text-left">
                                    <p className="text-[9px] font-sans font-bold text-brand-red uppercase tracking-[0.25em] mb-0.5">{meta.category}</p>
                                    <h4 className="text-base font-sans font-extrabold text-white leading-tight">{s.label}</h4>
                                  </div>
                                </div>
                              </motion.button>
                            );
                          })}
                        </div>
                        <div className="flex justify-center pt-8">
                          <p className="text-[10px] font-sans font-bold text-brand-muted uppercase tracking-[0.4em]">Proprietary Engineering Interface // DPS-QTS-2026</p>
                        </div>
                      </div>
                    )}

                    {/* Step 2: Details */}
                    {step === 2 && (
                      <div className="flex flex-col lg:flex-row gap-12">
                        <div className="lg:w-2/5">
                          <div className="relative h-64 lg:h-full min-h-[420px] rounded-3xl overflow-hidden border border-white/10 shadow-xl bg-slate-900">
                            {(() => {
                              const meta = SERVICE_METADATA[form.service as keyof typeof SERVICE_METADATA] || SERVICE_METADATA["other"];
                              const MetaIcon = meta.icon;
                              const serviceLabel = QUOTE_SERVICES.find(s => s.value === form.service)?.label || "Selected Service";

                              return (
                                <>
                                  {/* Image — clearly visible, no grayscale */}
                                  <Image
                                    src={meta.image}
                                    alt={serviceLabel}
                                    fill
                                    className="object-cover opacity-75 transition-all duration-700"
                                  />
                                  {/* Fixed dark scrim — same in both modes */}
                                  <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-black/10 z-10" />

                                  <div className="absolute inset-0 z-20 p-8 flex flex-col justify-end items-start">
                                    <div className="w-14 h-14 rounded-2xl bg-brand-red border border-brand-red/80 flex items-center justify-center mb-5 shadow-lg shadow-brand-red/25">
                                      <MetaIcon size={28} className="text-white" />
                                    </div>
                                    <div className="text-left bg-black/30 backdrop-blur-md p-4 rounded-2xl border border-white/15">
                                      <p className="text-[11px] font-sans font-bold text-brand-red uppercase tracking-[0.3em] mb-2">{meta.category}</p>
                                      <h4 className="text-2xl font-sans font-extrabold text-white leading-tight">{serviceLabel}</h4>
                                    </div>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>

                        <div className="lg:w-3/5 space-y-10 py-4">
                          <div className="mb-8">
                            <h3 className="text-4xl font-sans font-extrabold text-brand-text mb-4 tracking-tight">Your Details</h3>
                            <p className="text-brand-muted font-medium text-lg leading-relaxed">Tell us about yourself so we can establish a primary communication channel.</p>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div>
                              <div className="flex items-center gap-2 mb-3 ml-1">
                                <label htmlFor="modal-name" className="text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted">
                                  Full Name
                                </label>
                              </div>
                              <input
                                id="modal-name"
                                name="name"
                                type="text"
                                required
                                autoComplete="name"
                                value={form.name}
                                onChange={handleChange}
                                placeholder="John Doe"
                                className={`${inputClass} text-base py-4`}
                              />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 mb-3 ml-1">
                                <label htmlFor="modal-phone" className="text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted">
                                  Phone Number
                                </label>
                              </div>
                              <input
                                id="modal-phone"
                                name="phone"
                                type="tel"
                                required
                                autoComplete="tel"
                                value={form.phone}
                                onChange={handleChange}
                                placeholder="+44 20 7123 4567"
                                className={`${inputClass} text-base py-4`}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-3 ml-1">
                              <label htmlFor="modal-email" className="text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted">
                                Email Address
                              </label>
                            </div>
                            <input
                              id="modal-email"
                              name="email"
                              type="email"
                              required
                              autoComplete="email"
                              value={form.email}
                              onChange={handleChange}
                              placeholder="john@example.com"
                              className={`${inputClass} text-base py-4`}
                            />
                          </div>

                          <div className="flex gap-4 pt-8">
                            <button
                              type="button"
                              onClick={() => setStep(1)}
                              className="px-10 py-5 rounded-2xl font-sans font-extrabold text-sm uppercase tracking-widest border border-brand-card-border text-brand-muted hover:text-brand-text hover:bg-brand-surface transition-all"
                            >
                              Back
                            </button>
                            <button
                              type="submit"
                              className="group relative flex-1 bg-brand-gradient text-white py-5 rounded-2xl font-sans font-extrabold text-sm uppercase tracking-widest overflow-hidden transition-all shadow-xl shadow-brand-red/20"
                            >
                              <span className="relative z-10 flex items-center justify-center gap-2">
                                Continue <ChevronRight size={20} />
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {step === 3 && (
                      <div className="max-w-3xl mx-auto space-y-12 py-8">
                        <div className="text-center">
                          <h3 className="text-3xl font-sans font-extrabold text-brand-text mb-4 tracking-tight">What's the situation?</h3>
                          <p className="text-brand-muted font-medium text-lg leading-relaxed">Provide additional details or specific requirements for your quote.</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-2 mb-4 ml-1">
                            <label htmlFor="modal-message" className="text-[11px] font-sans font-bold uppercase tracking-widest text-brand-muted">
                              Technical Requirements / Symptoms
                            </label>
                          </div>
                          <textarea
                            id="modal-message"
                            name="message"
                            rows={8}
                            value={form.message}
                            onChange={handleChange}
                            placeholder="Please describe the work needed in detail..."
                            className={`${inputClass} text-base resize-none py-6 h-64 leading-relaxed`}
                          />
                        </div>

                        <div className="flex gap-4 pt-4">
                          <button
                            type="button"
                            onClick={() => setStep(2)}
                            className="px-10 py-5 rounded-2xl font-sans font-extrabold text-sm uppercase tracking-widest border border-brand-card-border text-brand-muted hover:text-brand-text hover:bg-brand-surface transition-all"
                          >
                            Back
                          </button>
                          <button
                            type="submit"
                            disabled={status === "loading"}
                            className="group relative flex-1 bg-brand-gradient text-white py-5 rounded-2xl font-sans font-extrabold text-sm uppercase tracking-widest overflow-hidden transition-all shadow-xl shadow-brand-red/20 disabled:opacity-50"
                          >
                            <div className="relative z-10 flex items-center justify-center gap-4 transition-colors">
                              {status === "loading" ? (
                                <>
                                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                  <span>Transmitting...</span>
                                </>
                              ) : (
                                <>
                                  <Send size={20} />
                                  <span>Submit Transmission</span>
                                </>
                              )}
                            </div>
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.form>
                )}
              </AnimatePresence>
            </div>

            <div className="px-8 py-4 flex items-center justify-center gap-3 bg-brand-surface dark:bg-brand-navy/30 border-t border-brand-card-border rounded-b-3xl">
              <Zap size={14} className="text-brand-red" />
              <span className="text-[10px] font-sans font-black text-brand-red uppercase tracking-[0.4em]">
                Proprietary Interface // Reliable Data Transmission // DPS Solutions
              </span>
            </div>
          </motion.div>
        </div >
      )
      }
    </AnimatePresence >
  );
}
