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
  Wrench,
  Settings,
  ShieldCheck,
  ClipboardList,
  Thermometer,
  Building2,
  Home,
} from "lucide-react";
import { useTheme } from "@/lib/theme-provider";
import { useQuoteModal } from "@/lib/quote-modal-context";
import { inquiryService } from "@/lib/inquiry-service";
import { QUOTE_SERVICES } from "@/components/ui/QuoteForm";
import { CORE_SERVICES_IMAGES } from "@/lib/constants";
import Image from "next/image";

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
  // Commercial
  "commercial-boiler-servicing": { image: "/images/boiler-modern.jpg", icon: Building2, category: "Commercial" },
  "plant-room-maintenance": { image: "/images/central-heating.jpg", icon: Building2, category: "Commercial" },
  "gas-safety-inspections": { image: "/images/boiler-repair.jpg", icon: Building2, category: "Commercial" },
  "ppm-contracts": { image: "/images/central-heating.jpg", icon: Building2, category: "Commercial" },
  "fault-finding-diagnosis": { image: "/images/boiler-repair.jpg", icon: Building2, category: "Commercial" },
  "commercial-heating-systems": { image: "/images/central-heating.jpg", icon: Building2, category: "Commercial" },
  "emergency-breakdowns": { image: "/images/boiler-repair.jpg", icon: Building2, category: "Commercial" },
  "fm-ppm-packages": { image: "/images/central-heating.jpg", icon: Building2, category: "Commercial" },
  "fm-reactive-ooh": { image: "/images/central-heating.jpg", icon: Building2, category: "Commercial" },
  // Domestic
  "boiler-installation-servicing-repairs": { image: "/images/boiler-install.jpg", icon: Home, category: "Domestic" },
  "system-diagnosis": { image: "/images/boiler-repair.jpg", icon: Home, category: "Domestic" },
  "landlord-gas-safety-cp12": { image: "/images/boiler-modern.jpg", icon: Home, category: "Domestic" },
  "plumbing-repairs": { image: "/images/plumbing-repairs.jpg", icon: Wrench, category: "Domestic" },
  "emergency-callouts": { image: "/images/boiler-repair.jpg", icon: Home, category: "Domestic" },
  // Legacy (for preselection from detail pages)
  "boiler-repair": { image: "/images/boiler-repair.jpg", icon: Flame, category: "Heating" },
  "boiler-installation": { image: "/images/boiler-install.jpg", icon: Settings, category: "Heating" },
  "boiler-servicing": { image: "/images/boiler-modern.jpg", icon: Activity, category: "Heating" },
  "central-heating": { image: "/images/central-heating.jpg", icon: Thermometer, category: "Heating" },
  "general-plumbing": { image: "/images/kitchen-plumbing.jpg", icon: Wrench, category: "Plumbing" },
  "other": { image: "/images/logo.png", icon: ShieldCheck, category: "General" },
  // Sector + core service (Commercial/Domestic → Mechanical, Electrical, Gas)
  "commercial-mechanical": { image: "/images/core-services/mechanical.png", icon: Wrench, category: "Commercial" },
  "commercial-electrical": { image: "/images/core-services/electrical.png", icon: Zap, category: "Commercial" },
  "commercial-gas": { image: "/images/core-services/gas.png", icon: Flame, category: "Commercial" },
  "domestic-mechanical": { image: "/images/core-services/mechanical.png", icon: Wrench, category: "Domestic" },
  "domestic-electrical": { image: "/images/core-services/electrical.png", icon: Zap, category: "Domestic" },
  "domestic-gas": { image: "/images/core-services/gas.png", icon: Flame, category: "Domestic" },
};

const SECTOR_OPTIONS = [
  { value: "commercial" as const, label: "Commercial Services", image: "/images/our-services-commercial.png", icon: Building2, description: "PPM contracts, plant room maintenance, 24-hour emergency support." },
  { value: "domestic" as const, label: "Domestic Services", image: "/images/our-services-domestic.png", icon: Home, description: "Boiler installation, servicing, CP12, plumbing, and emergency callouts." },
];

const CORE_SERVICE_OPTIONS = [
  { value: "mechanical" as const, label: "Mechanical Services", imageKey: "Mechanical Services", icon: Wrench },
  { value: "electrical" as const, label: "Electrical Services", imageKey: "Electrical Services", icon: Zap },
  { value: "gas" as const, label: "Gas Services", imageKey: "Gas Services", icon: Flame },
];

const TOTAL_STEPS = 4;

export default function QuoteModal({
  open,
  onClose,
  preselectedService = "",
}: QuoteModalProps) {
  const [step, setStep] = useState(1);
  const [status, setStatus] = useState<"idle" | "loading" | "success">("idle");
  const [form, setForm] = useState({
    sector: "" as "" | "commercial" | "domestic",
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

  const selectSector = (value: "commercial" | "domestic") => {
    setForm((prev) => ({ ...prev, sector: value, service: "" }));
    setStep(2);
  };

  const selectService = (value: string) => {
    setForm((prev) => ({ ...prev, service: value }));
    setStep(3);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step < TOTAL_STEPS) {
      setStep(step + 1);
      return;
    }
    setStatus("loading");
    const sectorLabel = form.sector ? `[Sector: ${form.sector === "commercial" ? "Commercial" : "Domestic"}]\n\n` : "";
    inquiryService.addInquiry({
      name: form.name,
      phone: form.phone,
      email: form.email,
      service: form.service,
      message: sectorLabel + form.message,
    });
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setStatus("success");
  };

  const handleClose = useCallback(() => {
    setStep(1);
    setStatus("idle");
    setForm({ sector: "", name: "", phone: "", email: "", service: preselectedService, message: "" });
    onClose();
  }, [onClose, preselectedService]);

  const isCoreServiceValue = (v: string) =>
    ["commercial-mechanical", "commercial-electrical", "commercial-gas", "domestic-mechanical", "domestic-electrical", "domestic-gas"].includes(v);

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
            className={`quote-modal-opaque relative z-[101] w-full ${step === 1 ? "max-w-5xl" : step === 2 ? "max-w-6xl" : "max-w-5xl"} max-h-[90vh] overflow-y-auto rounded-3xl bg-brand-surface dark:bg-brand-steel border border-brand-card-border shadow-2xl premium-shadow`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="quote-modal-header sticky top-0 z-30 flex items-center justify-between px-8 py-6 bg-brand-surface/95 dark:bg-brand-steel/95 backdrop-blur-md border-b border-brand-card-border">
              <div>
                <h2
                  id="quote-modal-title"
                  className="text-xl md:text-2xl font-technical font-extrabold text-brand-text mb-1 uppercase tracking-wider"
                >
                  Request a Quote
                </h2>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-brand-red animate-pulse" />
                  <span className="text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted">Step {step} of {TOTAL_STEPS}</span>
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
                    {/* Step 1: Commercial or Domestic */}
                    {step === 1 && (
                      <div className="space-y-10">
                        <div className="text-center max-w-2xl mx-auto">
                          <h3 className="text-2xl md:text-3xl font-technical font-extrabold text-brand-text mb-3 tracking-tight uppercase">Choose your sector</h3>
                          <p className="text-brand-muted text-sm font-technical uppercase tracking-wider">Select Commercial or Domestic to request a quote for the right type of work.</p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 max-w-4xl mx-auto">
                          {SECTOR_OPTIONS.map((opt) => {
                            const Icon = opt.icon;
                            return (
                              <motion.button
                                key={opt.value}
                                type="button"
                                whileHover={{ y: -4 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => selectSector(opt.value)}
                                className="group relative aspect-[4/3] min-h-[220px] rounded-2xl overflow-hidden border-2 border-brand-card-border hover:border-brand-red/50 transition-all duration-300 bg-brand-navy shadow-xl"
                              >
                                <Image
                                  src={opt.image}
                                  alt={opt.label}
                                  fill
                                  className="object-cover opacity-80 group-hover:scale-105 transition-transform duration-500"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
                                <div className="absolute inset-0 flex flex-col justify-end p-6 text-left">
                                  <div className="w-12 h-12 rounded-xl bg-brand-red/20 border border-brand-red/40 flex items-center justify-center mb-4 backdrop-blur-sm group-hover:bg-brand-red/30 transition-colors">
                                    <Icon size={24} className="text-brand-red" />
                                  </div>
                                  <h4 className="text-lg font-technical font-extrabold text-white uppercase tracking-widest mb-1">{opt.label}</h4>
                                  <p className="text-white/80 text-[11px] font-technical uppercase tracking-wider">{opt.description}</p>
                                </div>
                              </motion.button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Step 2: Mechanical, Electrical, or Gas (core services) */}
                    {step === 2 && form.sector && (
                      <div className="space-y-10">
                        <div className="flex items-center justify-between flex-wrap gap-4">
                          <div>
                            <h3 className="text-2xl md:text-3xl font-technical font-extrabold text-brand-text tracking-tight uppercase">Select service type</h3>
                            <p className="text-brand-muted text-xs font-technical uppercase tracking-wider mt-1">
                              {form.sector === "commercial" ? "Commercial" : "Domestic"} — choose Mechanical, Electrical, or Gas.
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => setStep(1)}
                            className="text-[10px] font-technical font-bold uppercase tracking-widest text-brand-muted hover:text-brand-red transition-colors"
                          >
                            ← Change sector
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-4xl mx-auto">
                          {CORE_SERVICE_OPTIONS.map((opt) => {
                            const value = `${form.sector}-${opt.value}`;
                            const Icon = opt.icon;
                            const imgSrc = CORE_SERVICES_IMAGES[opt.imageKey] ?? "/images/core-services/mechanical.png";
                            return (
                              <motion.button
                                key={value}
                                type="button"
                                whileHover={{ y: -4 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => selectService(value)}
                                className={`group relative aspect-[4/3] min-h-[200px] rounded-2xl overflow-hidden border-2 transition-all duration-300 bg-brand-navy shadow-xl ${form.service === value
                                  ? "border-brand-red ring-2 ring-brand-red/30 shadow-brand-red/10"
                                  : "border-brand-card-border hover:border-brand-red/50"
                                }`}
                              >
                                <Image
                                  src={imgSrc}
                                  alt={opt.label}
                                  fill
                                  className="object-cover opacity-75 group-hover:scale-105 transition-transform duration-500"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
                                <div className="absolute inset-0 flex flex-col justify-end p-6 text-left">
                                  <div className="w-12 h-12 rounded-xl bg-brand-red/20 border border-brand-red/40 flex items-center justify-center mb-4 backdrop-blur-sm group-hover:bg-brand-red/30 transition-colors">
                                    <Icon size={24} className="text-brand-red" />
                                  </div>
                                  <h4 className="text-base font-technical font-extrabold text-white uppercase tracking-widest">{opt.label}</h4>
                                </div>
                              </motion.button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Step 3: Details */}
                    {step === 3 && (
                      <div className="flex flex-col lg:flex-row gap-12">
                        <div className="lg:w-2/5">
                          <div className="relative h-64 lg:h-full min-h-[320px] rounded-2xl overflow-hidden border border-brand-card-border shadow-xl bg-brand-navy">
                            {(() => {
                              const meta = SERVICE_METADATA[form.service as keyof typeof SERVICE_METADATA] || SERVICE_METADATA["other"];
                              const MetaIcon = meta.icon;
                              const sectorLabel = form.sector === "commercial" ? "Commercial" : form.sector === "domestic" ? "Domestic" : "";
                              const serviceLabel = isCoreServiceValue(form.service)
                                ? `${sectorLabel} - ${form.service.endsWith("mechanical") ? "Mechanical Services" : form.service.endsWith("electrical") ? "Electrical Services" : "Gas Services"}`
                                : QUOTE_SERVICES.find(s => s.value === form.service)?.label || "Selected Service";

                              return (
                                <>
                                  <Image
                                    src={meta.image}
                                    alt={serviceLabel}
                                    fill
                                    className="object-cover opacity-75 transition-all duration-700"
                                  />
                                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent z-10" />
                                  <div className="absolute inset-0 z-20 p-6 flex flex-col justify-end items-start">
                                    <div className="w-12 h-12 rounded-xl bg-brand-red/90 border border-brand-red flex items-center justify-center mb-4">
                                      <MetaIcon size={24} className="text-white" />
                                    </div>
                                    <div className="text-left bg-black/40 backdrop-blur-md p-4 rounded-xl border border-white/10 w-full">
                                      <p className="text-[10px] font-technical font-bold text-brand-red uppercase tracking-widest mb-1">{sectorLabel}</p>
                                      <h4 className="text-lg font-technical font-extrabold text-white leading-tight uppercase tracking-wider">{serviceLabel}</h4>
                                    </div>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>

                        <div className="lg:w-3/5 space-y-8 py-4">
                          <div>
                            <h3 className="text-2xl md:text-3xl font-technical font-extrabold text-brand-text mb-2 tracking-tight uppercase">Your details</h3>
                            <p className="text-brand-muted text-xs font-technical uppercase tracking-wider">Tell us how we can contact you.</p>
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
                              onClick={() => setStep(2)}
                              className="px-10 py-5 rounded-2xl font-technical font-extrabold text-[11px] uppercase tracking-widest border border-brand-card-border text-brand-muted hover:text-brand-text hover:bg-brand-card transition-all"
                            >
                              Back
                            </button>
                            <button
                              type="submit"
                              className="group relative flex-1 bg-brand-red text-white py-5 rounded-2xl font-technical font-extrabold text-[11px] uppercase tracking-widest overflow-hidden transition-all shadow-xl shadow-brand-red/20 hover:bg-brand-red/90"
                            >
                              <span className="relative z-10 flex items-center justify-center gap-2">
                                Continue <ChevronRight size={20} />
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {step === 4 && (
                      <div className="max-w-3xl mx-auto space-y-10 py-8">
                        <div className="text-center">
                          <h3 className="text-2xl md:text-3xl font-technical font-extrabold text-brand-text mb-3 tracking-tight uppercase">Additional details</h3>
                          <p className="text-brand-muted text-xs font-technical uppercase tracking-wider">Describe the work or situation so we can prepare your quote.</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-2 mb-4 ml-1">
                            <label htmlFor="modal-message" className="text-[11px] font-technical font-bold uppercase tracking-widest text-brand-muted">
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
                            onClick={() => setStep(3)}
                            className="px-10 py-5 rounded-2xl font-technical font-extrabold text-[11px] uppercase tracking-widest border border-brand-card-border text-brand-muted hover:text-brand-text hover:bg-brand-card transition-all"
                          >
                            Back
                          </button>
                          <button
                            type="submit"
                            disabled={status === "loading"}
                            className="group relative flex-1 bg-brand-red text-white py-5 rounded-2xl font-technical font-extrabold text-[11px] uppercase tracking-widest overflow-hidden transition-all shadow-xl shadow-brand-red/20 hover:bg-brand-red/90 disabled:opacity-50"
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

            <div className="px-8 py-4 flex items-center justify-center gap-3 bg-brand-navy/50 dark:bg-brand-navy/50 border-t border-brand-card-border rounded-b-3xl">
              <Zap size={14} className="text-brand-red" />
              <span className="text-[10px] font-technical font-bold text-brand-red uppercase tracking-[0.4em]">
                Get a quote — Commercial &amp; Domestic
              </span>
            </div>
          </motion.div>
        </div >
      )
      }
    </AnimatePresence >
  );
}
