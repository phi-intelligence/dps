"use client";

import { ShieldCheck, BadgeCheck, MessageSquare, Clock } from "lucide-react";
import { motion } from "framer-motion";

const items = [
  { icon: ShieldCheck, label: "Gas Safe Registered" },
  { icon: BadgeCheck, label: "Fully Insured" },
  { icon: MessageSquare, label: "Free Quotes" },
  { icon: Clock, label: "Available 24/7" },
];

export default function TrustBar() {
  return (
    <div className="w-full bg-transparent">
      <div className="py-4 px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center md:text-left">
          {items.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + index * 0.1, duration: 0.4 }}
              className="flex items-center justify-center md:justify-start gap-3"
            >
              <item.icon size={20} className="text-brand-red shrink-0" />
              <span className="text-brand-text text-sm font-technical font-bold uppercase tracking-widest">{item.label}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
