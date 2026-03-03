"use client";

import { Star } from "lucide-react";
import { motion } from "framer-motion";

interface ReviewCardProps {
  name: string;
  service: string;
  rating: number;
  quote: string;
  index?: number;
  variant?: "default" | "luxury";
}

export default function ReviewCard({
  name,
  service,
  rating,
  quote,
  index = 0,
  variant = "default",
}: ReviewCardProps) {
  const isLuxury = variant === "luxury";

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.15, duration: 0.5 }}
      className={
        isLuxury
          ? "bg-white/90 border border-[#e0d3b8] rounded-2xl p-8 shadow-[0_18px_50px_rgba(0,0,0,0.12)] backdrop-blur-md transition-all duration-500"
          : "bg-brand-steel border border-brand-card-border rounded-2xl p-8 premium-shadow hover:premium-shadow-hover transition-all duration-500"
      }
    >
      <div className="flex gap-1 mb-6" aria-label={`${rating} out of 5 stars`}>
        {Array.from({ length: rating }).map((_, i) => (
          <Star
            key={i}
            size={18}
            className={
              isLuxury
                ? "fill-[#e2c977] text-[#e2c977]"
                : "fill-brand-orange text-brand-orange"
            }
          />
        ))}
      </div>
      <blockquote
        className={`text-lg leading-relaxed mb-8 font-medium ${
          isLuxury ? "text-[#171b1f]" : "text-brand-text"
        }`}
      >
        &ldquo;{quote}&rdquo;
      </blockquote>
      <div className="flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${
            isLuxury
              ? "bg-[#05080c] border border-[#e0d3b8] text-[#e2c977]"
              : "bg-brand-navy border border-brand-card-border text-brand-red"
          }`}
        >
          {name.charAt(0)}
        </div>
        <div>
          <p
            className={`font-bold text-base ${
              isLuxury ? "text-[#171b1f]" : "text-brand-text"
            }`}
          >
            {name}
          </p>
          <p
            className={`text-sm font-medium ${
              isLuxury ? "text-[#5b6167]" : "text-brand-muted"
            }`}
          >
            {service}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
