"use client";

import Link from "next/link";
import Image from "next/image";
import { Phone, Mail, Shield, Cpu, Zap, Activity, Wrench } from "lucide-react";
import { COMMERCIAL_SERVICES, DOMESTIC_SERVICES } from "@/lib/constants";
import { useContent } from "@/lib/content-provider";

const quickLinks = [
  { label: "Portfolio", href: "/portfolio" },
  { label: "About Us", href: "/about" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Contact Us", href: "/contact" },
];

export default function Footer() {
  const { company } = useContent();
  return (
    <footer className="bg-brand-steel text-brand-muted relative overflow-hidden">
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-brand-red/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center mb-8 group">
              <div className="relative h-14 sm:h-10 md:h-20 w-auto">
                <Image
                  src="/imagesV2/logo_full_light_nobg.png"
                  alt={company.name}
                  width={210}
                  height={48}
                  className="h-full w-auto object-contain transition-transform duration-300 group-hover:scale-[1.03]"
                />
              </div>
            </Link>

            <p className="text-sm font-light leading-relaxed mb-10 max-w-sm text-brand-muted uppercase tracking-wider">
              Professional heating and plumbing services for homes and businesses across {company.areas}. Gas Safe registered engineers.
            </p>

            <div className="space-y-4">
              <a href={`tel:${company.phone}`} className="flex items-center gap-4 group text-sm font-bold text-brand-text hover:text-brand-red transition-colors">
                <div className="w-11 h-11 rounded-xl bg-brand-navy border border-brand-card-border flex items-center justify-center group-hover:bg-brand-red group-hover:border-brand-red transition-all shadow-sm">
                  <Phone size={18} className="text-brand-red group-hover:text-white transition-colors" />
                </div>
                {company.phone}
              </a>
              <a href={`mailto:${company.email}`} className="flex items-center gap-4 group text-sm font-bold text-brand-text hover:text-brand-blue transition-colors">
                <div className="w-11 h-11 rounded-xl bg-brand-navy border border-brand-card-border flex items-center justify-center group-hover:bg-brand-blue group-hover:border-brand-blue transition-all shadow-sm">
                  <Mail size={18} className="text-brand-blue group-hover:text-white transition-colors" />
                </div>
                {company.email}
              </a>
            </div>
          </div>

          {/* Column 2: Commercial */}
          <div className="lg:pl-8">
            <h3 className="font-technical font-bold text-[10px] text-brand-red mb-8 uppercase tracking-[0.3em] flex items-center gap-2">
              <Activity size={12} />
              Commercial
            </h3>
            <ul className="space-y-4">
              {COMMERCIAL_SERVICES.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-[10px] font-technical uppercase tracking-widest hover:text-brand-red hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3: Domestic */}
          <div>
            <h3 className="font-technical font-bold text-[10px] text-brand-blue mb-8 uppercase tracking-[0.3em] flex items-center gap-2">
              <Wrench size={12} />
              Domestic
            </h3>
            <ul className="space-y-4">
              {DOMESTIC_SERVICES.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-[10px] font-technical uppercase tracking-widest hover:text-brand-blue hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-sans font-extrabold text-sm text-brand-text mb-8 uppercase tracking-widest">
              Quick Links
            </h3>
            <ul className="space-y-4">
              {quickLinks.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-sm font-medium hover:text-brand-red hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="mt-10 px-5 py-4 md:px-6 md:py-5 bg-[#05080c] border border-white/25 rounded-[2rem] flex items-center justify-between gap-4 premium-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 md:w-11 md:h-11 bg-brand-navy rounded-xl border border-[#e2c977]/40 flex items-center justify-center">
                  <Shield size={20} className="text-[#e2c977]" />
                </div>
                <p className="text-xs md:text-sm font-technical font-extrabold uppercase tracking-[0.28em] text-white">
                  Gas Safe Registered
                </p>
              </div>
              <div className="relative w-12 h-10 sm:w-16 sm:h-12">
                <Image
                  src="/imagesV2/gas_safe_logo.jpeg"
                  alt="Gas Safe Register"
                  fill
                  className="object-contain"
                  sizes="80px"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-24 pt-8 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6">
            <p className="text-[10px] font-technical uppercase tracking-widest text-brand-muted">
              &copy; {new Date().getFullYear()} {company.name}
            </p>
          </div>

          <div className="flex gap-10 text-[10px] font-technical uppercase tracking-[0.2em]">
            <Link href="/privacy" className="text-brand-muted hover:text-brand-text transition-colors">Privacy Policy</Link>
            <Link href="/terms" className="text-brand-muted hover:text-brand-text transition-colors">Terms &amp; Conditions</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
