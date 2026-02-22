import Link from "next/link";
import Image from "next/image";
import { Phone, Mail, MapPin, Shield, Cpu, Zap, Activity } from "lucide-react";
import { COMPANY } from "@/lib/constants";

const heatingLinks = [
  { label: "Boiler Architecture", href: "/services/heating" },
  { label: "System Deployment", href: "/services/heating/boiler-installation" },
  { label: "Annual Diagnostics", href: "/services/heating/boiler-servicing" },
  { label: "Thermal Operations", href: "/services/heating" },
];

const plumbingLinks = [
  { label: "Emergency Resolution", href: "/services/plumbing/plumbing-repairs" },
  { label: "Infrastructure Maintenance", href: "/services/plumbing/general-plumbing" },
  { label: "Hydraulic Systems", href: "/services/plumbing" },
];

const quickLinks = [
  { label: "Engineering Philosophy", href: "/about" },
  { label: "Field Coverage", href: "/service-areas" },
  { label: "Rapid Dispatch", href: "/emergency" },
  { label: "Initiate Uplink", href: "/contact" },
];

export default function Footer() {
  return (
    <footer className="bg-brand-steel border-t border-brand-card-border text-brand-muted relative overflow-hidden">
      {/* Thermal Gradient Section Base */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-brand-red to-transparent opacity-20" />

      {/* Decorative logo geometry element */}
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-brand-red/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8">
          {/* Brand/System Column */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-4 mb-8 group">
              <div className="w-12 h-12 rounded-full border border-brand-card-border-hover bg-brand-navy flex items-center justify-center relative overflow-hidden group-hover:border-brand-red/30 transition-all">
                <Image src="/images/logo.jpg" alt="DPS Heating" width={40} height={40} className="object-contain" />
              </div>
              <div>
                <span className="font-technical font-extrabold text-brand-text text-xl tracking-[0.2em] uppercase block leading-none">
                  DPS <span className="text-brand-red">HEATING</span>
                </span>
                <span className="text-[8px] font-mono text-brand-muted tracking-[0.4em] uppercase mt-1 block">
                  Precision Thermal Systems
                </span>
              </div>
            </Link>

            <p className="text-sm font-light leading-relaxed mb-10 max-w-sm text-brand-muted uppercase tracking-wider">
              Providing industrial-grade heating and plumbing infrastructure for domestic and commercial properties across {COMPANY.areas}.
              All systems engineered to the highest Gas Safe standards.
            </p>

            <div className="space-y-4">
              <a href={`tel:${COMPANY.phone}`} className="flex items-center gap-4 group text-[10px] font-technical tracking-widest uppercase hover:text-brand-text transition-colors">
                <div className="w-10 h-10 rounded-xl bg-brand-navy border border-brand-card-border flex items-center justify-center group-hover:bg-brand-red/5 group-hover:border-brand-red/20 transition-all">
                  <Phone size={14} className="text-brand-red" />
                </div>
                {COMPANY.phone}
              </a>
              <a href={`mailto:${COMPANY.email}`} className="flex items-center gap-4 group text-[10px] font-technical tracking-widest uppercase hover:text-brand-text transition-colors">
                <div className="w-10 h-10 rounded-xl bg-brand-navy border border-brand-card-border flex items-center justify-center group-hover:bg-brand-blue/5 group-hover:border-brand-blue/20 transition-all">
                  <Mail size={14} className="text-brand-blue" />
                </div>
                {COMPANY.email}
              </a>
            </div>
          </div>

          {/* Column 2: Operations */}
          <div className="lg:pl-8">
            <h3 className="font-technical font-bold text-[10px] text-brand-red mb-8 uppercase tracking-[0.3em] flex items-center gap-2">
              <Activity size={12} />
              Heating Ops
            </h3>
            <ul className="space-y-4">
              {heatingLinks.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-[10px] font-technical uppercase tracking-widest hover:text-brand-red hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3: Maintenance */}
          <div>
            <h3 className="font-technical font-bold text-[10px] text-brand-blue mb-8 uppercase tracking-[0.3em] flex items-center gap-2">
              <Zap size={12} />
              Plumbing Ops
            </h3>
            <ul className="space-y-4">
              {plumbingLinks.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-[10px] font-technical uppercase tracking-widest hover:text-brand-blue hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 4: System Integration */}
          <div>
            <h3 className="font-technical font-bold text-[10px] text-brand-text mb-8 uppercase tracking-[0.3em] flex items-center gap-2">
              <Cpu size={12} />
              System Links
            </h3>
            <ul className="space-y-4">
              {quickLinks.map((link) => (
                <li key={link.label}>
                  <Link href={link.href} className="text-[10px] font-technical uppercase tracking-widest hover:text-brand-text hover:pl-2 transition-all block text-brand-muted">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>

            <div className="mt-10 p-5 bg-brand-navy border border-brand-card-border rounded-2xl flex items-center gap-4">
              <div className="w-10 h-10 bg-brand-surface rounded-full border border-brand-red/20 flex items-center justify-center animate-pulse">
                <Shield size={20} className="text-brand-red" />
              </div>
              <div>
                <p className="text-brand-text text-[10px] font-technical font-bold tracking-[0.2em] uppercase leading-none mb-1">Gas Safe Cert.</p>
                <p className="text-brand-muted text-[10px] font-mono leading-none">REG: {COMPANY.gasSafeNumber}</p>
              </div>
            </div>
          </div>
        </div>

        {/* System Status / Bottom bar */}
        <div className="mt-24 pt-8 border-t border-brand-card-border flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6">
            <p className="text-[10px] font-technical uppercase tracking-widest text-brand-muted">
              &copy; {new Date().getFullYear()} dps heating architecture
            </p>
            <div className="flex items-center gap-2 text-[10px] font-mono text-green-600/80">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              ALL SYSTEMS NOMINAL
            </div>
          </div>

          <div className="flex gap-10 text-[10px] font-technical uppercase tracking-[0.2em]">
            <Link href="/privacy" className="text-brand-muted hover:text-brand-text transition-colors">Data Privacy</Link>
            <Link href="/terms" className="text-brand-muted hover:text-brand-text transition-colors">System Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
