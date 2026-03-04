"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

export interface FAQItem {
  question: string;
  answer: string;
}

export default function FAQAccordion({ faqs }: { faqs: FAQItem[] }) {
  return (
    <div className="space-y-4">
      {faqs.map((faq) => (
        <FAQItemComponent key={faq.question} {...faq} />
      ))}
    </div>
  );
}

function FAQItemComponent({ question, answer }: FAQItem) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-[#e0d3b8]/80 bg-white/70 shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left bg-transparent hover:bg-white transition-colors"
        aria-expanded={open}
      >
        <span className="font-technical font-semibold text-sm md:text-base tracking-[0.12em] uppercase text-[#171b1f]">
          {question}
        </span>
        <ChevronDown
          size={20}
          className={`text-[#b3c0d0] shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="overflow-hidden border-t border-[#e0d3b8]/70 bg-white/90"
          >
            <div className="px-6 py-4">
              <p className="text-sm md:text-[15px] leading-relaxed text-[#3c444b]">
                {answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
