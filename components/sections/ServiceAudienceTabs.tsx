"use client";

import { useState } from "react";
import Image from "next/image";

type Audience = "commercial" | "domestic";

interface ServiceCardItem {
  title: string;
  description: string;
  image: string;
  imageAlt: string;
}

interface ServiceAudienceTabsProps {
  commercialTitle: string;
  domesticTitle: string;
  commercialServices: string[];
  domesticServices: string[];
  commercialCards: ServiceCardItem[];
  domesticCards: ServiceCardItem[];
}

export default function ServiceAudienceTabs({
  commercialTitle,
  domesticTitle,
  commercialServices,
  domesticServices,
  commercialCards,
  domesticCards,
}: ServiceAudienceTabsProps) {
  const [activeTab, setActiveTab] = useState<Audience>("commercial");

  const isCommercial = activeTab === "commercial";
  const currentTitle = isCommercial ? commercialTitle : domesticTitle;
  const currentServices = isCommercial ? commercialServices : domesticServices;
  const currentCards = isCommercial ? commercialCards : domesticCards;

  return (
    <section className="py-16 md:py-24 bg-brand-steel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center mb-8">
          <div className="inline-flex rounded-full border border-brand-card-border bg-brand-card p-1">
            <button
              type="button"
              onClick={() => setActiveTab("commercial")}
              className={`px-5 py-2 rounded-full text-xs font-technical font-bold uppercase tracking-[0.2em] transition-colors ${
                isCommercial ? "bg-brand-red text-white" : "text-brand-muted hover:text-brand-text"
              }`}
            >
              Commercial
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("domestic")}
              className={`px-5 py-2 rounded-full text-xs font-technical font-bold uppercase tracking-[0.2em] transition-colors ${
                !isCommercial ? "bg-brand-red text-white" : "text-brand-muted hover:text-brand-text"
              }`}
            >
              Domestic
            </button>
          </div>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.2em] text-brand-text">
            {currentTitle}
          </h2>
        </div>

        <div className="rounded-2xl border border-brand-card-border bg-brand-card p-6 mb-8">
          <p className="text-xs font-technical font-bold uppercase tracking-[0.25em] text-brand-muted mb-4">
            Included services
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-3">
            {currentServices.map((item) => (
              <div key={item} className="flex items-start gap-2 text-sm text-brand-muted">
                <span className="mt-2 h-1.5 w-1.5 rounded-full bg-brand-red/70" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {currentCards.map((card) => (
            <article key={card.title} className="rounded-2xl border border-brand-card-border bg-brand-card overflow-hidden">
              <div className="relative aspect-[16/10]">
                <Image
                  src={card.image}
                  alt={card.imageAlt}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, 33vw"
                />
              </div>
              <div className="p-5">
                <h3 className="text-sm font-technical font-extrabold uppercase tracking-[0.16em] text-brand-text mb-2">
                  {card.title}
                </h3>
                <p className="text-sm text-brand-muted leading-relaxed">{card.description}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
