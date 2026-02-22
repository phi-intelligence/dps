"use client";

import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

export interface FAQItem {
  question: string;
  answer: string;
}

export default function FAQAccordion({ faqs }: { faqs: FAQItem[] }) {
  return (
    <div className="space-y-3">
      {faqs.map((faq) => (
        <FAQItemComponent key={faq.question} {...faq} />
      ))}
    </div>
  );
}

function FAQItemComponent({ question, answer }: FAQItem) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [buttonRect, setButtonRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (open && buttonRef.current) {
      const updateRect = () => {
        if (buttonRef.current) setButtonRect(buttonRef.current.getBoundingClientRect());
      };
      updateRect();
      window.addEventListener("scroll", updateRect, { passive: true });
      window.addEventListener("resize", updateRect);
      return () => {
        window.removeEventListener("scroll", updateRect);
        window.removeEventListener("resize", updateRect);
      };
    }
    if (!open && buttonRect !== null) {
      const t = setTimeout(() => setButtonRect(null), 300);
      return () => clearTimeout(t);
    }
  }, [open, buttonRect]);

  const portaledContent =
    typeof document !== "undefined" &&
    buttonRect &&
    createPortal(
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden fixed left-0 right-0 z-[60] bg-brand-navy border-x border-b border-brand-card-border-hover rounded-b-xl shadow-sm"
            style={{
              top: buttonRect.bottom,
              left: buttonRect.left,
              width: buttonRect.width,
            }}
          >
            <p className="px-6 py-4 text-brand-muted text-sm leading-relaxed">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>,
      document.body
    );

  return (
    <div className="border border-brand-border rounded-xl overflow-hidden">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left bg-brand-navy hover:bg-brand-surface transition-colors"
        aria-expanded={open}
      >
        <span className="font-semibold text-brand-text">{question}</span>
        <ChevronDown
          size={20}
          className={`text-brand-muted shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {portaledContent}
    </div>
  );
}
