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
} from "lucide-react";
import { QUOTE_SERVICES } from "@/components/ui/QuoteForm";

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step < 3) {
      setStep(step + 1);
      return;
    }
    setStatus("loading");
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
            transition={{ duration: 0.2 }}
            className="quote-modal-opaque relative z-[101] w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-[2rem] border border-brand-card-border shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="quote-modal-header sticky top-0 z-10 flex items-center justify-between px-6 py-4">
              <h2
                id="quote-modal-title"
                className="text-lg font-technical font-extrabold uppercase tracking-widest text-brand-text"
              >
                Get a Quote
              </h2>
              <button
                type="button"
                onClick={handleClose}
                className="rounded-full p-2 text-brand-muted hover:bg-brand-card hover:text-brand-text transition-colors"
                aria-label="Close"
              >
                <X size={20} />
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
                    {/* Step 1: Service */}
                    {step === 1 && (
                      <div className="space-y-6">
                        <div className="flex items-center gap-2 mb-3">
                          <Cpu size={12} className="text-brand-red" />
                          <label htmlFor="modal-service" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                            SYSTEM_DIRECTIVE
                          </label>
                        </div>
                        <div className="relative">
                          <select
                            id="modal-service"
                            name="service"
                            required
                            value={form.service}
                            onChange={handleChange}
                            className={`${inputClass} appearance-none cursor-pointer`}
                          >
                            {QUOTE_SERVICES.map((s) => (
                              <option key={s.value} value={s.value} className="bg-brand-steel text-brand-text uppercase text-[10px]">
                                {s.label}
                              </option>
                            ))}
                          </select>
                          <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                            <Cpu size={14} className="text-brand-text" />
                          </div>
                        </div>
                        <button
                          type="submit"
                          className="group relative w-full bg-white text-black py-5 rounded-xl font-technical font-extrabold text-[12px] uppercase tracking-[0.4em] overflow-hidden transition-all shadow-2xl"
                        >
                          <span className="relative z-10 flex items-center justify-center gap-2">
                            Next: Your details <ChevronRight size={16} />
                          </span>
                        </button>
                      </div>
                    )}

                    {/* Step 2: Details */}
                    {step === 2 && (
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Cpu size={12} className="text-brand-red" />
                              <label htmlFor="modal-name" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                                IDENT: FULL_NAME
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
                              placeholder="ENTER LEGAL IDENTITY"
                              className={inputClass}
                            />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Activity size={12} className="text-brand-red" />
                              <label htmlFor="modal-phone" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                                COMM_LINK: PRIMARY
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
                              placeholder="+44 0000 000000"
                              className={inputClass}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Send size={12} className="text-brand-red" />
                            <label htmlFor="modal-email" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                              UPLINK_NODE: SMTP
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
                            placeholder="NODENAME@DOMAIN.SYS"
                            className={inputClass}
                          />
                        </div>
                        <div className="flex gap-3">
                          <button
                            type="button"
                            onClick={() => setStep(1)}
                            className="px-6 py-4 rounded-xl font-technical font-bold text-[12px] uppercase tracking-widest border border-brand-card-border-hover text-brand-muted hover:text-brand-text transition-colors"
                          >
                            Back
                          </button>
                          <button
                            type="submit"
                            className="group relative flex-1 bg-white text-black py-5 rounded-xl font-technical font-extrabold text-[12px] uppercase tracking-[0.4em] overflow-hidden transition-all shadow-2xl"
                          >
                            <span className="relative z-10 flex items-center justify-center gap-2">
                              Next: Message <ChevronRight size={16} />
                            </span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Step 3: Message & submit */}
                    {step === 3 && (
                      <div className="space-y-6">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Activity size={12} className="text-brand-red" />
                            <label htmlFor="modal-message" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                              DIAGNOSTIC_SYMPTOMS
                            </label>
                          </div>
                          <textarea
                            id="modal-message"
                            name="message"
                            rows={4}
                            value={form.message}
                            onChange={handleChange}
                            placeholder="INPUT ANOMALY PARAMETERS OR ARCHITECTURAL REQUIREMENTS..."
                            className={`${inputClass} resize-none`}
                          />
                        </div>
                        <div className="flex gap-3">
                          <button
                            type="button"
                            onClick={() => setStep(2)}
                            className="px-6 py-4 rounded-xl font-technical font-bold text-[12px] uppercase tracking-widest border border-brand-card-border-hover text-brand-muted hover:text-brand-text transition-colors"
                          >
                            Back
                          </button>
                          <button
                            type="submit"
                            disabled={status === "loading"}
                            className="group relative flex-1 bg-white text-black py-5 rounded-xl font-technical font-extrabold text-[12px] uppercase tracking-[0.4em] overflow-hidden transition-all shadow-2xl disabled:opacity-50"
                          >
                            <div className="relative z-10 flex items-center justify-center gap-4 group-hover:text-white transition-colors">
                              {status === "loading" ? (
                                <>
                                  <div className="w-4 h-4 border-2 border-brand-red border-t-transparent rounded-full animate-spin" />
                                  <span>Transmitting Data</span>
                                </>
                              ) : (
                                <>
                                  <Send size={14} />
                                  <span>Deploy Command</span>
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

            <div className="px-6 py-3 flex items-center justify-center gap-2">
              <Zap size={12} className="text-brand-red" />
              <span className="text-[9px] font-technical font-bold text-brand-red uppercase tracking-[0.3em]">
                Free Quote — No Obligation
              </span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
