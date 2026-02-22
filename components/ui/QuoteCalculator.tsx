"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Flame, Wind, Home, Building2, ArrowRight, Phone, RotateCcw } from "lucide-react";
import { COMPANY } from "@/lib/constants";
import { SERVICE_MAP, URGENCY_MULTIPLIER } from "@/lib/chat-config";
import type { ServiceCategory, ServiceItem } from "@/lib/chat-config";

const categories = [
  { key: "heating" as const, label: "Heating", icon: Flame },
  { key: "air-conditioning" as const, label: "Air Conditioning", icon: Wind },
];

const propertyTypes = [
  { key: "domestic" as const, label: "Domestic", icon: Home },
  { key: "commercial" as const, label: "Commercial", icon: Building2 },
];

const urgencyOptions = [
  { key: "standard" as const, label: "Standard", desc: "Normal lead time", mult: URGENCY_MULTIPLIER.standard },
  { key: "urgent" as const, label: "Urgent", desc: "Faster scheduling", mult: URGENCY_MULTIPLIER.urgent },
  { key: "emergency" as const, label: "Emergency", desc: "Same-day where possible", mult: URGENCY_MULTIPLIER.emergency },
] as const;

export default function QuoteCalculator() {
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState<ServiceCategory | null>(null);
  const [service, setService] = useState<ServiceItem | null>(null);
  const [propertyType, setPropertyType] = useState<"domestic" | "commercial" | null>(null);
  const [urgency, setUrgency] = useState<keyof typeof URGENCY_MULTIPLIER | null>(null);

  const handleCategorySelect = (key: keyof typeof SERVICE_MAP) => {
    setCategory(SERVICE_MAP[key] ?? null);
    setService(null);
    setPropertyType(null);
    setUrgency(null);
    setStep(2);
  };

  const handleServiceSelect = (s: ServiceItem) => {
    setService(s);
    setStep(3);
  };

  const handlePropertySelect = (p: "domestic" | "commercial") => {
    setPropertyType(p);
    setStep(4);
  };

  const handleUrgencySelect = (u: keyof typeof URGENCY_MULTIPLIER) => {
    setUrgency(u);
    setStep(5);
  };

  const handleStartOver = () => {
    setStep(1);
    setCategory(null);
    setService(null);
    setPropertyType(null);
    setUrgency(null);
  };

  const priceRange = (() => {
    if (!service || !propertyType || !urgency) return null;
    const range = service.priceRange[propertyType];
    const mult = URGENCY_MULTIPLIER[urgency];
    return [Math.round(range[0] * mult), Math.round(range[1] * mult)] as [number, number];
  })();

  return (
    <div className="rounded-3xl border border-brand-card-border bg-brand-card p-8 md:p-12">
      <div className="flex justify-center gap-2 mb-10">
        {[1, 2, 3, 4, 5].map((s) => (
          <div
            key={s}
            className={`w-2.5 h-2.5 rounded-full transition-colors ${
              s === step ? "bg-brand-blue" : "bg-brand-card-border"
            }`}
          />
        ))}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-8"
          >
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Category
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {categories.map((cat) => (
                <button
                  key={cat.key}
                  type="button"
                  onClick={() => handleCategorySelect(cat.key)}
                  className="flex items-center gap-4 p-6 rounded-2xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-blue/30 hover:bg-brand-blue/5 transition-all text-left group"
                >
                  <cat.icon size={32} className="text-brand-blue shrink-0" />
                  <span className="font-technical font-bold text-brand-text uppercase tracking-wider group-hover:text-brand-blue transition-colors">
                    {cat.label}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {step === 2 && category && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-8"
          >
            <button
              type="button"
              onClick={() => setStep(1)}
              className="text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest"
            >
              ← Back
            </button>
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Service
            </h3>
            <ul className="space-y-2">
              {category.services.map((s) => (
                <li key={s.slug}>
                  <button
                    type="button"
                    onClick={() => handleServiceSelect(s)}
                    className="w-full flex items-center justify-between gap-4 p-4 rounded-xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-blue/20 text-left group transition-all"
                  >
                    <span className="font-technical font-bold text-brand-text text-sm uppercase tracking-wider">
                      {s.label}
                    </span>
                    <ArrowRight size={18} className="text-brand-blue shrink-0 group-hover:translate-x-1 transition-transform" />
                  </button>
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {step === 3 && service && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-8"
          >
            <button
              type="button"
              onClick={() => setStep(2)}
              className="text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest"
            >
              ← Back
            </button>
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Property type
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {propertyTypes.map((p) => (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => handlePropertySelect(p.key)}
                  className="flex items-center gap-4 p-6 rounded-2xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-blue/30 transition-all text-left group"
                >
                  <p.icon size={32} className="text-brand-blue shrink-0" />
                  <span className="font-technical font-bold text-brand-text uppercase tracking-wider">
                    {p.label}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {step === 4 && propertyType && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-8"
          >
            <button
              type="button"
              onClick={() => setStep(3)}
              className="text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest"
            >
              ← Back
            </button>
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Urgency
            </h3>
            <ul className="space-y-2">
              {urgencyOptions.map((u) => (
                <li key={u.key}>
                  <button
                    type="button"
                    onClick={() => handleUrgencySelect(u.key)}
                    className="w-full flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-4 rounded-xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-blue/20 text-left transition-all"
                  >
                    <span className="font-technical font-bold text-brand-text text-sm uppercase tracking-wider">
                      {u.label}
                    </span>
                    <span className="text-brand-muted text-[10px] font-technical uppercase tracking-wider">
                      {u.desc} {u.mult !== 1 ? `(×${u.mult})` : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {step === 5 && priceRange !== null && (
          <motion.div
            key="step5"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-8"
          >
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Estimated range
            </h3>
            <div className="text-4xl md:text-5xl font-technical font-black text-brand-text tracking-tight">
              £{priceRange[0].toLocaleString()} – £{priceRange[1].toLocaleString()}
            </div>
            <p className="text-brand-muted text-[10px] font-technical uppercase tracking-wider">
              This is an indicative range. For an exact quote, please contact us with your requirements.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/contact"
                className="flex items-center justify-center gap-2 bg-brand-red text-white py-4 px-8 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-widest hover:bg-brand-red/90 transition-colors"
              >
                Get Exact Quote
                <ArrowRight size={18} />
              </Link>
              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center justify-center gap-2 border border-brand-card-border-hover bg-brand-navy text-brand-text py-4 px-8 rounded-full font-technical font-bold text-[12px] uppercase tracking-widest hover:border-brand-blue/30 transition-all"
              >
                <Phone size={18} className="text-brand-blue" />
                Call Us
              </a>
            </div>
            <button
              type="button"
              onClick={handleStartOver}
              className="flex items-center gap-2 text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest transition-colors"
            >
              <RotateCcw size={14} />
              Start Over
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
