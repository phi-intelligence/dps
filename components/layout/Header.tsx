"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import Image from "next/image";
import { Menu, X, ChevronDown, Sun, Moon, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/lib/theme-provider";
import { COMPANY } from "@/lib/constants";

const navLinks = [
  { label: "Home", href: "/" },
  {
    label: "Services",
    href: "/services",
    children: [
      { label: "Commercial Services", href: "/services/commercial" },
      { label: "Domestic Services", href: "/services/domestic" },
    ],
  },
  { label: "About Us", href: "/about" },
  { label: "Portfolio", href: "/portfolio" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Contact", href: "/contact" },
  { label: "Admin", href: "/admin/login", admin: true },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [servicesOpen, setServicesOpen] = useState(false);
  const [mobileServicesOpen, setMobileServicesOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
      setMobileServicesOpen(false);
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <header
      className={`absolute top-0 left-0 right-0 z-[60] transition-all duration-500 py-4 sm:py-6 max-lg:bg-brand-surface max-lg:shadow-md ${scrolled || mobileOpen ? "bg-brand-surface/95 backdrop-blur-md shadow-lg" : "lg:py-6"}`}
    >
      <div className="w-full px-4 sm:px-6 lg:px-12">
        <div
          className={`flex items-center justify-between transition-all duration-500 rounded-xl md:rounded-2xl px-4 md:px-16 py-4 md:py-6 ${scrolled
              ? "bg-brand-surface/40 backdrop-blur-md shadow-lg"
              : "bg-transparent"
            } ${!scrolled && "lg:bg-transparent"} max-lg:!bg-brand-surface max-lg:rounded-none max-lg:shadow-none`}
        >
          {/* Logo Section — compact on mobile */}
          <Link href="/" className="flex items-center gap-2 sm:gap-3 group min-w-0">
            <Image src="/images/logo.png" alt={COMPANY.name} width={40} height={48} loading="eager" className="object-contain transition-transform group-hover:scale-105 duration-300 shrink-0" style={{ width: "auto", height: "auto", maxHeight: "40px" }} />
            <div className="min-w-0">
              <span className="font-technical font-extrabold text-brand-text text-base sm:text-xl md:text-2xl tracking-tight leading-none block uppercase truncate">
                {COMPANY.name}
              </span>
              <span className="hidden sm:block text-xs font-sans font-medium text-brand-muted tracking-tight mt-0.5">
                Commercial &amp; Domestic Gas Works
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8" aria-label="Main navigation">
            {navLinks.map((link) =>
              link.admin ? null : // Exclude admin link from main nav
                link.children ? (
                  <div
                    key={link.href}
                    className="relative group"
                    onMouseEnter={() => setServicesOpen(true)}
                    onMouseLeave={() => setServicesOpen(false)}
                  >
                    <Link
                      href={link.href}
                      className="flex items-center gap-2 text-brand-muted hover:text-brand-text transition-all text-sm font-technical uppercase tracking-widest font-bold"
                    >
                      {link.label}
                      <ChevronDown
                        size={14}
                        className={`transition-transform duration-300 group-hover:rotate-180 text-brand-red`}
                      />
                    </Link>
                    <AnimatePresence>
                      {servicesOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: 10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 10, scale: 0.95 }}
                          className="absolute top-full left-0 mt-6 w-64 bg-brand-navy/95 backdrop-blur-2xl border border-brand-card-border rounded-2xl shadow-2xl overflow-hidden p-2"
                        >
                          {link.children.map((child) => (
                            <Link
                              key={child.href}
                              href={child.href}
                              className="flex items-center gap-3 px-4 py-3 text-xs text-brand-muted font-technical uppercase tracking-widest hover:text-brand-text hover:bg-brand-steel rounded-xl transition-all group/item"
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
                    className="text-brand-muted hover:text-brand-text transition-all text-sm font-technical uppercase tracking-widest font-bold relative group"
                  >
                    {link.label}
                    <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-brand-red transition-all group-hover:w-full" />
                  </Link>
                )
            )}
          </nav>

          {/* Right: Theme Toggle + Admin */}
          <div className="hidden lg:flex items-center gap-6">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-full border border-brand-card-border bg-brand-card flex items-center justify-center text-brand-muted hover:text-brand-text hover:border-brand-card-border-hover transition-all"
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link
              href="/admin/login"
              className="w-9 h-9 rounded-xl border border-brand-card-border bg-brand-card flex items-center justify-center text-brand-muted hover:text-brand-red hover:border-brand-red transition-all"
              title="Admin Terminal"
            >
              <ShieldCheck size={16} />
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

      {/* Mobile Menu — portaled to body so it always sits on top, full viewport, opaque */}
      {mounted &&
        typeof document !== "undefined" &&
        createPortal(
          <AnimatePresence>
            {mobileOpen && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="lg:hidden fixed inset-0 bg-[#121417] text-[#F8FAFC]"
                style={{ zIndex: 9999 }}
                aria-modal
                aria-label="Main menu"
              >
                <div className="flex flex-col h-full overflow-hidden">
                  <div className="flex justify-between items-center shrink-0 px-4 py-4 border-b border-white/10">
                    <span className="font-technical font-bold text-lg tracking-widest uppercase text-[#F8FAFC]">
                      Menu
                    </span>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={toggleTheme}
                        className="w-10 h-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-[#94A3B8] hover:text-[#F8FAFC] transition-all"
                        aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                      >
                        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                      </button>
                      <button
                        onClick={() => setMobileOpen(false)}
                        className="w-10 h-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-[#F8FAFC] hover:text-[#d4af37] transition-all"
                        aria-label="Close menu"
                      >
                        <X size={22} />
                      </button>
                    </div>
                  </div>

                  <nav
                    className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-1 min-h-0"
                    aria-label="Main navigation"
                  >
                    {navLinks.filter((link) => !link.admin).map((link) => (
                      <div key={link.href} className="py-2">
                        {link.children ? (
                          <>
                            <button
                              type="button"
                              onClick={() => setMobileServicesOpen((open) => !open)}
                              className="flex items-center justify-between w-full py-3 text-xl font-technical font-bold uppercase tracking-tight text-[#F8FAFC] hover:text-[#d4af37] transition-colors"
                              aria-expanded={mobileServicesOpen}
                              aria-controls="mobile-services-dropdown"
                              id="mobile-services-trigger"
                            >
                              {link.label}
                              <ChevronDown
                                size={20}
                                className={`text-[#94A3B8] transition-transform duration-200 ${mobileServicesOpen ? "rotate-180" : ""}`}
                              />
                            </button>
                            <AnimatePresence>
                              {mobileServicesOpen && (
                                <motion.div
                                  id="mobile-services-dropdown"
                                  role="region"
                                  aria-labelledby="mobile-services-trigger"
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  transition={{ duration: 0.2 }}
                                  className="overflow-hidden"
                                >
                                  <div className="pl-4 mt-1 border-l-2 border-[#d4af37]/30 flex flex-col gap-1 pb-2">
                                    {link.children.map((child) => (
                                      <Link
                                        key={child.href}
                                        href={child.href}
                                        className="block py-2.5 text-base font-technical font-bold uppercase tracking-widest text-[#94A3B8] hover:text-[#F8FAFC] transition-colors"
                                        onClick={() => {
                                          setMobileServicesOpen(false);
                                          setMobileOpen(false);
                                        }}
                                      >
                                        {child.label}
                                      </Link>
                                    ))}
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </>
                        ) : (
                          <Link
                            href={link.href}
                            className="block py-3 text-xl font-technical font-bold uppercase tracking-tight text-[#F8FAFC] hover:text-[#d4af37] transition-colors"
                            onClick={() => setMobileOpen(false)}
                          >
                            {link.label}
                          </Link>
                        )}
                      </div>
                    ))}
                  </nav>
                </div>
              </motion.div>
            )}
          </AnimatePresence>,
          document.body
        )}
    </header>
  );
}
