"use client";

import { ShieldCheck, BadgeCheck, MessageSquare, Clock } from "lucide-react";
import { motion } from "framer-motion";

const items = [
  { icon: ShieldCheck, label: "Gas Safe Registered" },
  { icon: BadgeCheck, label: "Fully Insured" },
  { icon: MessageSquare, label: "Free Quotes" },
  { icon: Clock, label: "Same-Day Service" },
];

export default function TrustBar() {
  return (
    <div className="w-full bg-transparent">
      <div className="py-6 px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {items.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + index * 0.1, duration: 0.4 }}
              className="flex items-center gap-4 group justify-center lg:justify-start"
            >
              <div className="w-10 h-10 rounded-xl bg-brand-steel dark:bg-brand-navy flex items-center justify-center border border-brand-card-border group-hover:bg-brand-red group-hover:border-brand-red transition-all duration-300 shadow-sm shadow-brand-red/5">
                <item.icon size={18} className="text-brand-red group-hover:text-white transition-colors" />
              </div>
              <span className="text-brand-text text-xs font-bold uppercase tracking-tight font-sans">{item.label}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
