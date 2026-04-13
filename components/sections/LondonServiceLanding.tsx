"use client";

import Link from "next/link";
import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import { ArrowRight, Building2, CheckCircle2, MapPin, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";

interface ContentSection {
  heading: string;
  paragraphs: string[];
}

interface LondonServiceLandingProps {
  title: string;
  subtitle: string;
  breadcrumbs: { label: string; href?: string }[];
  serviceName: string;
  intro: string;
  sections: ContentSection[];
}

export default function LondonServiceLanding({
  title,
  subtitle,
  breadcrumbs,
  serviceName,
  intro,
  sections,
}: LondonServiceLandingProps) {
  const trustItems = [
    "Gas Safe registered",
    "Commercial gas qualified",
    "Fully insured",
    "Trusted by facilities management companies",
  ];

  return (
    <div className="bg-[#f2ede3] text-brand-text">
      <PageHero
        title={title}
        subtitle={subtitle}
        breadcrumbs={breadcrumbs}
        backgroundImage="/images/blueprint-commercial-system.png"
        variant="luxury"
        darkHero
        compact
      />

      <section className="relative bg-[#f7f3ea] py-14 md:py-18 overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-32 top-6 h-52 w-80 rotate-6 rounded-[3rem] border border-[#e2c977]/24 bg-[#e2c977]/8" />
          <div className="absolute -left-28 bottom-0 h-44 w-72 -rotate-6 rounded-[3rem] border border-[#d4af37]/20 bg-[#d4af37]/8" />
        </div>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45 }}
            className="rounded-[2.2rem] border border-[#e0d3b8] bg-white/92 px-6 py-8 md:px-10 md:py-10 shadow-[0_18px_55px_rgba(0,0,0,0.08)]"
          >
            <div className="grid gap-7 lg:grid-cols-[1.2fr_0.8fr]">
              <div>
                <span className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#b8963a]">
                  London And South East Coverage
                </span>
                <h2 className="mt-3 text-2xl md:text-3xl font-technical font-extrabold uppercase tracking-[0.2em] text-[#171b1f]">
                  {serviceName}
                </h2>
                <p className="mt-5 text-sm md:text-base leading-relaxed text-[#2f3740]">
                  {intro}
                </p>
              </div>

              <div className="rounded-2xl border border-[#e0d3b8] bg-[#f8f4eb] px-5 py-5">
                <h3 className="text-[10px] font-technical font-extrabold uppercase tracking-[0.3em] text-[#7a6629] mb-3">
                  At A Glance
                </h3>
                <ul className="space-y-3 text-sm text-[#2f3740]">
                  <li className="flex items-start gap-2">
                    <MapPin size={14} className="mt-0.5 text-[#b8963a]" />
                    Covering London, Kent, Essex and the South East
                  </li>
                  <li className="flex items-start gap-2">
                    <Building2 size={14} className="mt-0.5 text-[#b8963a]" />
                    Commercial and high-end residential delivery
                  </li>
                  <li className="flex items-start gap-2">
                    <ShieldCheck size={14} className="mt-0.5 text-[#b8963a]" />
                    Compliance-first engineering and reporting
                  </li>
                </ul>
                <Link
                  href="/contact"
                  className="mt-5 inline-flex items-center gap-2 rounded-full border border-[#c9b47a] bg-white px-4 py-2 text-[10px] font-technical font-extrabold uppercase tracking-[0.22em] text-[#1f252b] hover:bg-[#fff9e8] transition-all hover:-translate-y-0.5"
                >
                  Book Site Visit
                  <ArrowRight size={13} className="text-[#b8963a]" />
                </Link>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
                We support maintenance and project delivery with the same disciplined engineering standard, whether the requirement is reactive fault attendance, planned servicing, compliance checks, or lifecycle upgrades. Clients that need one accountable partner for both city and regional coverage value our ability to keep communication clear, provide practical recommendations, and deliver work safely in live environments.
              </p>
              <p className="text-sm md:text-base leading-relaxed text-[#2f3740]">
                Covering London, Kent, Essex and the South East, our teams regularly assist organisations seeking dependable Gas Engineer Kent / South East support alongside London-first response. That regional continuity helps facilities teams maintain consistent standards across multi-site portfolios and reduces complexity when scheduling planned and emergency works.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="relative bg-[#0b1015] py-14 md:py-16 overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 md:p-8">
            <h3 className="text-lg md:text-xl font-technical font-extrabold uppercase tracking-[0.2em] text-white mb-5">
              Why Facilities Teams Choose DPS
            </h3>
            <ul className="grid gap-3 sm:grid-cols-2">
              {trustItems.map((item) => (
                <li
                  key={item}
                  className="rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-sm text-[#d6dde7] flex items-center gap-2"
                >
                  <CheckCircle2 size={14} className="text-[#e2c977] shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="relative bg-[#f7f3ea] py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-7">
          {sections.map((section, idx) => (
            <motion.article
              key={section.heading}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.42 }}
              whileHover={{ y: -2 }}
              className={`rounded-[1.8rem] border border-[#e0d3b8] px-6 py-6 md:px-8 md:py-8 shadow-[0_14px_36px_rgba(0,0,0,0.06)] ${
                idx % 2 === 0 ? "bg-white/90" : "bg-[#f3ecdf]"
              }`}
            >
              <h3 className="text-xl md:text-2xl font-technical font-extrabold uppercase tracking-[0.16em] text-[#171b1f] mb-4">
                {section.heading}
              </h3>
              {section.paragraphs.map((paragraph, idx) => (
                <p
                  key={`${section.heading}-${idx}`}
                  className="text-sm md:text-base leading-relaxed text-[#2f3740] mb-4 last:mb-0"
                >
                  {paragraph}
                </p>
              ))}
            </motion.article>
          ))}
        </div>
      </section>

      <CTABanner
        title="Need A Commercial Engineer Fast?"
        subtitle="Covering London, Kent, Essex and the South East for planned works, compliance, and emergency support."
        backgroundImage="/images/blueprints/blueprint-8.png"
      />
    </div>
  );
}
