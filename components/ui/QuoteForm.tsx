"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, AlertCircle, Send, Cpu, Activity } from "lucide-react";

const services = [
  { value: "", label: "Select service..." },
  { value: "boiler-repair", label: "Boiler Repair" },
  { value: "boiler-installation", label: "Boiler Installation" },
  { value: "boiler-servicing", label: "Boiler Servicing" },
  { value: "central-heating", label: "Central Heating" },
  { value: "radiators", label: "Radiators" },
  { value: "power-flushing", label: "Power Flushing" },
  { value: "ac-installation", label: "AC Installation" },
  { value: "ac-servicing", label: "AC Servicing" },
  { value: "ac-repairs", label: "AC Repairs" },
  { value: "commercial-ac", label: "Commercial AC" },
  { value: "ac-maintenance", label: "Maintenance Contracts" },
  { value: "other", label: "Other" },
];

interface QuoteFormProps {
  preselectedService?: string;
  compact?: boolean;
}

export default function QuoteForm({ preselectedService = "", compact = false }: QuoteFormProps) {
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
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setStatus("success");
  };

  const inputClass =
    "w-full bg-brand-navy border border-brand-card-border-hover rounded-xl px-6 py-5 text-brand-text text-[12px] font-technical uppercase tracking-widest placeholder-brand-muted/30 focus:outline-none focus:border-brand-red/50 transition-all shadow-2xl";

  return (
    <div className="relative">
      <AnimatePresence>
        {status === "success" && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-brand-navy border border-brand-red/30 text-brand-text px-8 py-10 rounded-2xl shadow-2xl flex flex-col items-center justify-center text-center gap-6 backdrop-blur-xl"
            role="alert"
          >
            <div className="w-16 h-16 rounded-full bg-brand-red/10 flex items-center justify-center">
              <CheckCircle size={32} className="text-brand-red animate-pulse" />
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
              className="mt-4 text-[10px] font-technical font-bold text-brand-red hover:text-brand-text transition-colors uppercase tracking-widest"
            >
              Reset Terminal
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handleSubmit} className={`space-y-8 ${status === "success" ? "opacity-10 pointer-events-none filter blur-md transition-all" : ""}`} noValidate>
        <div className={`grid gap-8 ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2"}`}>
          <div>
            <div className="flex items-center gap-2 mb-3 ml-1">
              <Cpu size={12} className="text-brand-red" />
              <label htmlFor="name" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                IDENT: FULL_NAME
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
              <Activity size={12} className="text-brand-red" />
              <label htmlFor="phone" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
                COMM_LINK: PRIMARY
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
            <Send size={12} className="text-brand-red" />
            <label htmlFor="email" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
              UPLINK_NODE: SMTP
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
            <Cpu size={12} className="text-brand-red" />
            <label htmlFor="service" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
              SYSTEM_DIRECTIVE
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
              {services.map((s) => (
                <option key={s.value} value={s.value} className="bg-brand-navy text-brand-text uppercase text-[10px]">
                  {s.label}
                </option>
              ))}
            </select>
            <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
              <Cpu size={14} className="text-brand-text" />
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-3 ml-1">
            <Activity size={12} className="text-brand-red" />
            <label htmlFor="message" className="text-[9px] font-technical font-black uppercase tracking-[0.4em] text-brand-muted">
              DIAGNOSTIC_SYMPTOMS
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
          className="group relative w-full bg-white text-black py-6 rounded-xl font-technical font-extrabold text-[12px] uppercase tracking-[0.4em] overflow-hidden transition-all shadow-2xl disabled:opacity-50"
        >
          <div className="absolute inset-0 bg-brand-red scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500" />
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
      </form>
    </div>
  );
}
