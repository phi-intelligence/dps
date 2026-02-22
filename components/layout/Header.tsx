"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Phone, Menu, X, ChevronDown, Sun, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { COMPANY } from "@/lib/constants";
import { useTheme } from "@/lib/theme-provider";

const navLinks = [
  { label: "Home", href: "/" },
  {
    label: "Capabilities",
    href: "/services",
    children: [
      { label: "Heating Architecture", href: "/services/heating" },
      { label: "Plumbing Infrastructure", href: "/services/plumbing" },
      { label: "Climate Control", href: "/services/air-conditioning" },
    ],
  },
  { label: "About", href: "/about" },
  { label: "Coverage", href: "/service-areas" },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [servicesOpen, setServicesOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? "py-4" : "py-6"
        }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          className={`flex items-center justify-between transition-all duration-500 rounded-full px-6 md:px-8 py-3 ${scrolled ? "bg-brand-surface/80 backdrop-blur-xl border border-brand-card-border shadow-xl" : "bg-transparent border border-transparent"
            }`}
        >
          {/* Logo Section */}
          <Link href="/" className="flex items-center gap-4 group">
            <div className="relative w-10 h-10 flex items-center justify-center">
              <motion.div
                className="absolute inset-0 bg-gradient-to-br from-brand-red via-brand-purple to-brand-blue rounded-full opacity-10 group-hover:opacity-20 transition-opacity"
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              />
              <div className="w-9 h-9 rounded-full border border-brand-card-border-hover bg-brand-navy flex items-center justify-center relative z-10 overflow-hidden">
                <Image src="/images/logo.jpg" alt="DPS Heating" width={30} height={30} className="object-contain" />
              </div>
            </div>
            <div className="hidden sm:block">
              <span className="font-technical font-extrabold text-brand-text text-lg tracking-[0.2em] leading-none block uppercase">
                DPS <span className="text-brand-red">Heating</span>
              </span>
              <span className="text-[8px] font-mono text-brand-muted tracking-[0.4em] uppercase mt-1 block">
                Thermal Engineering
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8" aria-label="Main navigation">
            {navLinks.map((link) =>
              link.children ? (
                <div key={link.href} className="relative group">
                  <button
                    onMouseEnter={() => setServicesOpen(true)}
                    className="flex items-center gap-2 text-brand-muted hover:text-brand-text transition-all text-xs font-technical uppercase tracking-widest font-bold"
                  >
                    {link.label}
                    <ChevronDown
                      size={12}
                      className={`transition-transform duration-300 group-hover:rotate-180 text-brand-red`}
                    />
                  </button>
                  <AnimatePresence>
                    {servicesOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        onMouseLeave={() => setServicesOpen(false)}
                        className="absolute top-full left-0 mt-6 w-64 bg-brand-navy/95 backdrop-blur-2xl border border-brand-card-border rounded-2xl shadow-2xl overflow-hidden p-2"
                      >
                        {link.children.map((child) => (
                          <Link
                            key={child.href}
                            href={child.href}
                            className="flex items-center gap-3 px-4 py-3 text-[10px] text-brand-muted font-technical uppercase tracking-widest hover:text-brand-text hover:bg-brand-steel rounded-xl transition-all group/item"
                            onClick={() => setServicesOpen(false)}
                          >
                            <div className="w-1.5 h-1.5 rounded-full bg-brand-red/30 group-hover/item:bg-brand-red transition-colors" />
                            {child.label}
                          </Link>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-brand-muted hover:text-brand-text transition-all text-xs font-technical uppercase tracking-widest font-bold relative group"
                >
                  {link.label}
                  <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-brand-red transition-all group-hover:w-full" />
                </Link>
              )
            )}
          </nav>

          {/* Right: Theme Toggle + Phone + CTA */}
          <div className="hidden lg:flex items-center gap-6">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-full border border-brand-card-border bg-brand-card flex items-center justify-center text-brand-muted hover:text-brand-text hover:border-brand-card-border-hover transition-all"
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <a
              href={`tel:${COMPANY.phone}`}
              className="flex items-center gap-2 text-brand-muted hover:text-brand-text transition-all text-xs font-technical font-bold uppercase tracking-widest"
            >
              <Phone size={14} className="text-brand-red animate-pulse" />
              <span>{COMPANY.phone}</span>
            </a>
            <Link
              href="/contact"
              className="relative group bg-brand-red text-white px-6 py-2.5 rounded-full text-[10px] font-technical font-extrabold uppercase tracking-[0.2em] transition-all overflow-hidden shadow-lg shadow-brand-red/20"
            >
              <span className="relative z-10 transition-colors group-hover:text-white">Deploy Uplink</span>
              <div className="absolute inset-0 bg-brand-red/80 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="lg:hidden text-brand-text p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, x: "100%" }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: "100%" }}
            className="lg:hidden fixed inset-0 z-[60] bg-brand-surface p-8 flex flex-col"
          >
            <div className="flex justify-between items-center mb-12">
              <span className="font-technical font-bold text-lg tracking-widest uppercase text-brand-text">System Menu</span>
              <div className="flex items-center gap-4">
                <button
                  onClick={toggleTheme}
                  className="w-9 h-9 rounded-full border border-brand-card-border bg-brand-card flex items-center justify-center text-brand-muted hover:text-brand-text transition-all"
                  aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                >
                  {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                </button>
                <button onClick={() => setMobileOpen(false)} className="text-brand-text">
                  <X size={32} />
                </button>
              </div>
            </div>

            <nav className="flex flex-col gap-6">
              {navLinks.map((link) => (
                <div key={link.href} className="space-y-4">
                  <Link
                    href={link.href}
                    className="text-4xl font-technical font-bold uppercase tracking-tighter text-brand-text hover:text-brand-red transition-colors"
                    onClick={() => setMobileOpen(false)}
                  >
                    {link.label}
                  </Link>
                  {link.children && (
                    <div className="pl-6 border-l border-brand-red/20 flex flex-col gap-3">
                      {link.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          className="text-brand-muted hover:text-brand-text text-sm font-technical uppercase tracking-widest"
                          onClick={() => setMobileOpen(false)}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>

            <div className="mt-auto pt-12 border-t border-brand-card-border">
              <a
                href={`tel:${COMPANY.phone}`}
                className="flex items-center gap-4 text-2xl font-technical font-bold mb-8 text-brand-text"
              >
                <Phone size={24} className="text-brand-red" />
                {COMPANY.phone}
              </a>
              <Link
                href="/contact"
                className="block w-full text-center bg-brand-red text-white py-5 rounded-full font-technical font-extrabold uppercase tracking-widest shadow-xl shadow-brand-red/20"
                onClick={() => setMobileOpen(false)}
              >
                Initiate Request
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
