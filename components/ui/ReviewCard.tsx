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
      className="bg-brand-card backdrop-blur-xl border border-brand-card-border-hover rounded-2xl p-6"
    >
      <div className="flex gap-1 mb-4" aria-label={`${rating} out of 5 stars`}>
        {Array.from({ length: rating }).map((_, i) => (
          <Star key={i} size={16} className="fill-brand-red text-brand-red" />
        ))}
      </div>
      <blockquote className="text-brand-text text-sm leading-relaxed mb-4 italic">
        &ldquo;{quote}&rdquo;
      </blockquote>
      <div>
        <p className="font-semibold text-brand-text text-sm">{name}</p>
        <p className="text-brand-muted text-xs">{service}</p>
      </div>
    </motion.div>
  );
}
