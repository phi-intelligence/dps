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
      <div className="py-4 px-4 sm:px-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {items.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + index * 0.1, duration: 0.4 }}
              className="flex items-center gap-3 group justify-center lg:justify-start"
            >
              <div className="w-9 h-9 rounded-full bg-white/60 flex items-center justify-center border border-[#e0d3b8] group-hover:bg-[#b8963a] group-hover:border-[#b8963a] transition-all duration-300">
                <item.icon size={18} className="text-brand-red group-hover:text-white transition-colors" />
              </div>
              <span className="text-[#2b3136] text-[11px] sm:text-xs font-bold uppercase tracking-[0.25em] font-sans">
                {item.label}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
