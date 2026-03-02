"use client";

import { Star } from "lucide-react";
import { motion } from "framer-motion";

interface ReviewCardProps {
  name: string;
  service: string;
  rating: number;
  quote: string;
  index?: number;
}

export default function ReviewCard({ name, service, rating, quote, index = 0 }: ReviewCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.15, duration: 0.5 }}
      className="bg-brand-steel border border-brand-card-border rounded-2xl p-8 premium-shadow hover:premium-shadow-hover transition-all duration-500"
    >
      <div className="flex gap-1 mb-6" aria-label={`${rating} out of 5 stars`}>
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} size={18} className="fill-brand-orange text-brand-orange" />
        ))}
      </div>
      <blockquote className="text-brand-text text-lg leading-relaxed mb-8 font-medium">
        &ldquo;{quote}&rdquo;
      </blockquote>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-brand-navy border border-brand-card-border flex items-center justify-center font-bold text-brand-red">
          {name.charAt(0)}
        </div>
        <div>
          <p className="font-bold text-brand-text text-base">{name}</p>
          <p className="text-brand-muted text-sm font-medium">{service}</p>
        </div>
      </div>
    </motion.div>
  );
}
