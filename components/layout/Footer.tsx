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
            <Link href="/" className="flex items-center gap-4 mb-8 group">
              <Image src="/images/logo.png" alt="DPS Heating" width={40} height={48} className="object-contain" style={{ width: "auto", height: "auto" }} />
              <div>
                <span className="font-technical font-extrabold text-brand-text text-xl tracking-[0.2em] uppercase block leading-none">
                  DPS <span className="text-brand-red">HEATING</span>
                </span>
                <span className="text-[8px] font-mono text-brand-muted tracking-[0.4em] uppercase mt-1 block">
                  DESIGN • ENGINEER • MAINTAIN
                </span>
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

            <div className="mt-10 p-6 bg-brand-steel border border-brand-card-border rounded-3xl flex items-center gap-4 premium-shadow">
              <div className="w-12 h-12 bg-brand-navy rounded-full border border-brand-red/10 flex items-center justify-center">
                <Shield size={24} className="text-brand-red" />
              </div>
              <div>
                <p className="text-brand-text text-xs font-extrabold uppercase tracking-tight mb-1">Gas Safe Registered</p>
                <p className="text-brand-muted text-xs font-medium">REG: {company.gasSafeNumber}</p>
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
