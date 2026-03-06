"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, AlertCircle, Send, Cpu, Activity } from "lucide-react";
import { inquiryService } from "@/lib/inquiry-service";

export const QUOTE_SERVICES = [
  { value: "", label: "Select service..." },
  // Commercial
  { value: "commercial-boiler-servicing", label: "Commercial Boiler Servicing" },
  { value: "plant-room-maintenance", label: "Plant Room Maintenance" },
  { value: "gas-safety-inspections", label: "Gas Safety Inspections" },
  { value: "ppm-contracts", label: "PPM Contracts" },
  { value: "fault-finding-diagnosis", label: "Fault Finding & Diagnosis" },
  { value: "commercial-heating-systems", label: "Commercial Heating Systems" },
  { value: "emergency-breakdowns", label: "24 Hour Emergency Breakdowns" },
  { value: "fm-ppm-packages", label: "Facilities Management (3 Tier PPM)" },
  { value: "fm-reactive-ooh", label: "Facilities Management (Reactive & OOH)" },
  // Domestic
  { value: "boiler-installation-servicing-repairs", label: "Boiler Installation, Servicing & Repairs" },
  { value: "system-diagnosis", label: "System Diagnosis" },
  { value: "landlord-gas-safety-cp12", label: "Landlord Gas Safety (CP12)" },
  { value: "plumbing-repairs", label: "Plumbing Repairs" },
  { value: "emergency-callouts", label: "Emergency Call outs" },
  // Legacy (for preselection from detail pages — avoid duplicating values already in Commercial/Domestic)
  { value: "boiler-repair", label: "Boiler Repair" },
  { value: "boiler-installation", label: "Boiler Installation" },
  { value: "boiler-servicing", label: "Boiler Servicing" },
  { value: "central-heating", label: "Central Heating" },
  { value: "general-plumbing", label: "General Plumbing" },
  { value: "other", label: "Other" },
];

interface QuoteFormProps {
  preselectedService?: string;
  compact?: boolean;
  /** When "luxury", inputs and success state use gold/dark theme for use on dark cards */
  theme?: "default" | "luxury";
}

export default function QuoteForm({ preselectedService = "", compact = false, theme = "default" }: QuoteFormProps) {
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    service: preselectedService,
    message: "",
    contactMethod: "phone",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    await inquiryService.addInquiry({
      name: form.name,
      phone: form.phone,
      email: form.email,
      service: form.service,
      message: form.message,
    });
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setStatus("success");
  };

  const isLuxury = theme === "luxury";
  const inputClass = isLuxury
    ? "w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 sm:px-6 sm:py-5 text-white text-[14px] font-sans font-medium placeholder-white/40 focus:outline-none focus:border-[#e2c977]/50 transition-all"
    : "w-full bg-white dark:bg-brand-navy border border-brand-card-border-hover rounded-xl px-5 py-4 sm:px-6 sm:py-5 text-brand-text text-[14px] font-sans font-medium placeholder-brand-muted/30 focus:outline-none focus:border-brand-red/50 transition-all shadow-sm";
  const labelClass = isLuxury ? "text-[10px] font-sans font-bold uppercase tracking-widest text-[#9aa3b0]" : "text-[10px] font-sans font-bold uppercase tracking-widest text-brand-muted";
  const successClass = isLuxury
    ? "absolute inset-0 z-50 border border-[#e2c977]/30 text-white px-8 py-10 rounded-2xl shadow-2xl flex flex-col items-center justify-center text-center gap-6 backdrop-blur-xl bg-[#0a0f14]/95"
    : "absolute inset-0 z-50 bg-brand-navy border border-brand-red/30 text-brand-text px-8 py-10 rounded-2xl shadow-2xl flex flex-col items-center justify-center text-center gap-6 backdrop-blur-xl";
  const successIconClass = isLuxury ? "w-16 h-16 rounded-full bg-[#e2c977]/20 flex items-center justify-center" : "w-16 h-16 rounded-full bg-brand-red/10 flex items-center justify-center";
  const successCheckClass = isLuxury ? "text-[#e2c977] animate-pulse" : "text-brand-red animate-pulse";
  const resetBtnClass = isLuxury ? "mt-4 text-[10px] font-technical font-bold text-[#e2c977] hover:text-white transition-colors uppercase tracking-widest" : "mt-4 text-[10px] font-technical font-bold text-brand-red hover:text-brand-text transition-colors uppercase tracking-widest";
  const submitBtnClass = isLuxury
    ? "group relative w-full bg-[#e2c977] text-[#0a0f14] py-5 sm:py-6 rounded-full font-sans font-extrabold text-[11px] sm:text-sm uppercase tracking-[0.18em] sm:tracking-[0.24em] overflow-hidden transition-all shadow-lg hover:bg-[#f5e9c6] disabled:opacity-50"
    : "group relative w-full bg-brand-gradient text-white py-5 sm:py-6 rounded-full font-sans font-extrabold text-[11px] sm:text-sm uppercase tracking-[0.18em] sm:tracking-[0.24em] overflow-hidden transition-all shadow-xl shadow-brand-red/10 disabled:opacity-50";

  return (
    <div className="relative">
      <AnimatePresence>
        {status === "success" && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0 }}
            className={successClass}
            role="alert"
          >
            <div className={successIconClass}>
              <CheckCircle size={32} className={successCheckClass} />
            </div>
            <div>
              <p className="font-technical font-extrabold text-xl tracking-[0.2em] uppercase">Uplink Successful</p>
              <p className="text-[10px] text-brand-muted font-technical uppercase tracking-[0.2em] mt-4 leading-loose">
                Data transmission complete. <br />
                Engineering dispatch confirmed via primary channel.
              </p>
            </div>
            <button
              onClick={() => setStatus("idle")}
              className={resetBtnClass}
            >
              Reset Terminal
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <form
        onSubmit={handleSubmit}
        className={`space-y-6 sm:space-y-8 ${
          status === "success" ? "opacity-10 pointer-events-none filter blur-md transition-all" : ""
        }`}
        noValidate
      >
        <div className={`grid gap-8 ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"}`}>
          <div>
            <div className="flex items-center gap-2 mb-3 ml-1">
              <label htmlFor="name" className={labelClass}>
                Full Name
              </label>
            </div>
            <input
              id="name"
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
            <div className="flex items-center gap-2 mb-3 ml-1">
              <label htmlFor="phone" className={labelClass}>
                Phone Number
              </label>
            </div>
            <input
              id="phone"
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
          <div className="flex items-center gap-2 mb-3 ml-1">
            <label htmlFor="email" className={labelClass}>
              Email Address
            </label>
          </div>
          <input
            id="email"
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

        <div>
          <div className="flex items-center gap-2 mb-3 ml-1">
            <label htmlFor="service" className={labelClass}>
              Required Service
            </label>
          </div>
          <div className="relative">
            <select
              id="service"
              name="service"
              required
              value={form.service}
              onChange={handleChange}
              className={`${inputClass} appearance-none cursor-pointer`}
            >
              {QUOTE_SERVICES.map((s) => (
                <option key={s.value} value={s.value} className={isLuxury ? "bg-[#0d1319] text-white uppercase text-[10px]" : "bg-brand-navy text-brand-text uppercase text-[10px]"}>
                  {s.label}
                </option>
              ))}
            </select>
            <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
              <Cpu size={14} className={isLuxury ? "text-[#e2c977]" : "text-brand-text"} />
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-3 ml-1">
            <label htmlFor="message" className={labelClass}>
              Additional Details
            </label>
          </div>
          <textarea
            id="message"
            name="message"
            rows={compact ? 4 : 6}
            value={form.message}
            onChange={handleChange}
            placeholder="INPUT ANOMALY PARAMETERS OR ARCHITECTURAL REQUIREMENTS..."
            className={`${inputClass} resize-none`}
          />
        </div>

        <button
          type="submit"
          disabled={status === "loading"}
          className={submitBtnClass}
        >
          <div className="relative z-10 flex items-center justify-center gap-4 transition-colors">
            {status === "loading" ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Transmitting Data</span>
              </>
            ) : (
              <>
                <Send size={18} />
                <span>Request Custom Quote</span>
              </>
            )}
          </div>
        </button>
      </form>
    </div>
  );
}
