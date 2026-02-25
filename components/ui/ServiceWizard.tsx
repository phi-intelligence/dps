"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Building2, Home, ArrowRight } from "lucide-react";
import { SERVICE_MAP } from "@/lib/chat-config";
import type { ServiceCategory, ServiceItem } from "@/lib/chat-config";

const categories = [
  { key: "commercial" as const, label: "Commercial", icon: Building2 },
  { key: "domestic" as const, label: "Domestic", icon: Home },
];

export default function ServiceWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState<ServiceCategory | null>(null);
  const [service, setService] = useState<ServiceItem | null>(null);

  const handleCategorySelect = (key: keyof typeof SERVICE_MAP) => {
    setCategory(SERVICE_MAP[key] ?? null);
    setStep(2);
  };

  const handleServiceSelect = (s: ServiceItem) => {
    setService(s);
    setStep(3);
  };

  const handleViewDetails = () => {
    if (service?.href) router.push(service.href);
  };

  const handleBack = () => {
    if (step === 2) {
      setCategory(null);
      setService(null);
      setStep(1);
    } else if (step === 3) {
      setService(null);
      setStep(2);
    }
  };

  return (
    <div className="rounded-3xl border border-brand-card-border bg-brand-card p-8 md:p-12">
      <div className="flex justify-center gap-2 mb-10">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`w-2.5 h-2.5 rounded-full transition-colors ${
              s === step ? "bg-brand-red" : "bg-brand-card-border"
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
              Choose category
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {categories.map((cat) => (
                <button
                  key={cat.key}
                  type="button"
                  onClick={() => handleCategorySelect(cat.key)}
                  className="flex items-center gap-4 p-6 rounded-2xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-red/30 hover:bg-brand-red/5 transition-all text-left group"
                >
                  <cat.icon size={32} className="text-brand-red shrink-0" />
                  <span className="font-technical font-bold text-brand-text uppercase tracking-wider group-hover:text-brand-red transition-colors">
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
              onClick={handleBack}
              className="text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest"
            >
              ← Back
            </button>
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Select service
            </h3>
            <ul className="space-y-2">
              {category.services.map((s) => (
                <li key={s.slug}>
                  <button
                    type="button"
                    onClick={() => handleServiceSelect(s)}
                    className="w-full flex items-center justify-between gap-4 p-4 rounded-xl border border-brand-card-border-hover bg-brand-navy hover:border-brand-red/20 text-left group transition-all"
                  >
                    <span className="font-technical font-bold text-brand-text text-sm uppercase tracking-wider">
                      {s.label}
                    </span>
                    <ArrowRight size={18} className="text-brand-red shrink-0 group-hover:translate-x-1 transition-transform" />
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
              onClick={handleBack}
              className="text-brand-muted hover:text-brand-text text-[10px] font-technical uppercase tracking-widest"
            >
              ← Back
            </button>
            <h3 className="text-xl font-technical font-extrabold text-brand-text uppercase tracking-widest">
              Ready to view?
            </h3>
            <p className="text-brand-muted text-sm font-technical uppercase tracking-wider">
              {service.label}
            </p>
            <button
              type="button"
              onClick={handleViewDetails}
              className="w-full flex items-center justify-center gap-2 bg-brand-red text-white py-4 rounded-full font-technical font-extrabold text-[12px] uppercase tracking-widest hover:bg-brand-red/90 transition-colors"
            >
              View Service Details
              <ArrowRight size={18} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
