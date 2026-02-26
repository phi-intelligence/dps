"use client";

import PageHero from "@/components/ui/PageHero";
import CTABanner from "@/components/ui/CTABanner";
import ReviewCard from "@/components/ui/ReviewCard";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";
import { COMPANY, REVIEWS, PORTFOLIO_PROJECTS } from "@/lib/constants";
import { motion } from "framer-motion";
import Image from "next/image";
import {
  Flame,
  Wrench,
  MapPin,
  Award,
  CheckCircle,
  Building2,
  Clock,
  Star,
} from "lucide-react";

const categoryIcon: Record<string, React.ReactNode> = {
  Heating: <Flame size={14} />,
  Plumbing: <Wrench size={14} />,
};

const categoryColor: Record<string, string> = {
  Heating: "bg-brand-red/20 text-brand-red border-brand-red/30",
  Plumbing: "bg-brand-blue/20 text-brand-blue border-brand-blue/30",
};

const stats = [
  { icon: CheckCircle, label: "Projects Completed", value: "500+" },
  { icon: Clock, label: "Years Experience", value: "10+" },
  { icon: Building2, label: "Areas Covered", value: "20+" },
  { icon: Star, label: "Customer Rating", value: "5.0" },
];

export default function PortfolioPage() {
  return (
    <div className="bg-brand-surface text-brand-text">
      {/* ── Hero ── */}
      <PageHero
        title="Portfolio"
        subtitle={`Completed projects across ${COMPANY.areas}. Heating and plumbing — delivered to the highest standard.`}
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Portfolio" }]}
        backgroundImage="/images/team-professional.jpg"
        compact
      />

      {/* ── Stats Strip ── */}
      <section className="relative bg-brand-navy py-16 overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='80' height='80' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h80v80H0z' fill='none' stroke='%23fff' stroke-width='0.5'/%3E%3C/svg%3E\")" }} />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-red/10 text-brand-red mb-4">
                  <stat.icon size={22} />
                </div>
                <p className="text-3xl sm:text-4xl font-extrabold text-brand-text font-technical">
                  {stat.value}
                </p>
                <p className="text-sm uppercase tracking-widest text-brand-muted font-technical mt-1">
                  {stat.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Completed Projects Grid ── */}
      <section className="relative py-32 bg-brand-surface overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-red/5 rounded-full blur-[200px] pointer-events-none" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-20"
          >
            <span className="inline-block text-xs font-bold uppercase tracking-[0.25em] text-brand-red font-technical mb-4">
              Deployment Log
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-technical uppercase tracking-tight">
              Completed{" "}
              <span className="text-brand-red">Projects</span>
            </h2>
            <p className="mt-6 text-brand-muted max-w-2xl mx-auto text-lg">
              A selection of recent installations, repairs, and system upgrades
              delivered across {COMPANY.areas}.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {PORTFOLIO_PROJECTS.map((project, i) => (
              <motion.div
                key={project.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="group relative bg-brand-steel border border-brand-card-border rounded-2xl overflow-hidden premium-shadow hover:premium-shadow-hover transition-all duration-500"
              >
                {/* Project Image */}
                <div className="relative h-56 overflow-hidden">
                  <Image
                    src={project.image || "/images/central-heating.jpg"}
                    alt={project.title}
                    fill
                    className="object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-brand-steel via-brand-steel/40 to-transparent" />

                  {/* Category Badge */}
                  <div className="absolute top-4 left-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${categoryColor[project.category] || "bg-brand-card text-brand-muted border-brand-card-border"}`}
                    >
                      {categoryIcon[project.category]}
                      {project.category}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <h3 className="text-lg font-bold font-technical uppercase tracking-wide text-brand-text mb-1">
                    {project.title}
                  </h3>
                  <div className="flex items-center gap-1.5 text-brand-muted text-sm mb-4">
                    <MapPin size={14} className="text-brand-red" />
                    {project.location}
                  </div>
                  <p className="text-brand-muted text-sm leading-relaxed mb-6">
                    {project.description}
                  </p>

                  {/* Stat Pills */}
                  <div className="flex gap-3">
                    {project.stats.map((stat) => (
                      <div
                        key={stat.label}
                        className="flex-1 bg-brand-navy/60 rounded-xl px-3 py-2 text-center border border-brand-card-border"
                      >
                        <p className="text-base font-bold text-brand-text font-technical">
                          {stat.value}
                        </p>
                        <p className="text-[11px] uppercase tracking-wider text-brand-muted">
                          {stat.label}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Featured Project Highlight ── */}
      <section className="relative py-32 bg-brand-navy overflow-hidden">
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-brand-blue/[0.03] rounded-full blur-[120px] pointer-events-none" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left — Text */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.25em] text-brand-red font-technical mb-6">
                <Award size={16} />
                Featured Deployment
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-technical uppercase tracking-tight mb-6">
                Commercial Plant{" "}
                <span className="text-brand-red">Room Build</span>
              </h2>
              <p className="text-brand-muted text-lg leading-relaxed mb-8">
                Full design and installation of a commercial heating plant room
                in central London. Twin cascade boilers, pressurisation unit,
                buffer vessel, and full BEMS integration — completed on schedule
                with zero disruption to tenants.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  { label: "System Output", value: "200 kW" },
                  { label: "Floors Heated", value: "6" },
                  { label: "Duration", value: "3 weeks" },
                  { label: "Warranty", value: "10 years" },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 15 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 + i * 0.1, duration: 0.4 }}
                    className="bg-brand-surface/5 border border-brand-card-border rounded-xl px-4 py-3"
                  >
                    <p className="text-xl font-bold text-brand-text font-technical">
                      {stat.value}
                    </p>
                    <p className="text-xs uppercase tracking-widest text-brand-muted font-technical">
                      {stat.label}
                    </p>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Right — Blueprint */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <BlueprintBillboard
                src="/images/blueprint-plant-room.png"
                alt="Commercial heating plant room schematic"
                theme="warm"
                versionText="PLANT_RM: V3.1"
                idHash="DPS-PLT-2024"
                statusText="COMMISSIONED"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section className="relative py-32 bg-brand-steel overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-brand-red/5 rounded-full blur-[200px] pointer-events-none" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-20"
          >
            <span className="inline-block text-xs font-bold uppercase tracking-[0.25em] text-brand-red font-technical mb-4">
              Client Transmissions
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-technical uppercase tracking-tight">
              What Our Clients{" "}
              <span className="text-brand-red">Say</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {REVIEWS.map((review, i) => (
              <ReviewCard
                key={review.name}
                name={review.name}
                service={review.service}
                rating={review.rating}
                quote={review.quote}
                index={i}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <CTABanner />
    </div>
  );
}
