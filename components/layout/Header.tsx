"use client";

import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import Image from "next/image";
import { Menu, X, ChevronDown, Sun, Moon, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/lib/theme-provider";
import { useContent } from "@/lib/content-provider";

export default function Header() {
  const { company, nav: navLinks } = useContent();
  const [scrolled, setScrolled] = useState(false);
  const [showHeader, setShowHeader] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [servicesOpen, setServicesOpen] = useState(false);
  const [mobileServicesOpen, setMobileServicesOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const lastScrollYRef = useRef(0);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    const onScroll = () => {
      const current = window.scrollY || 0;
      const last = lastScrollYRef.current;
      const heroThreshold = window.innerHeight * 0.6;

      setScrolled(current > 20);

      const scrollingDown = current > last + 4;
      const scrollingUp = current < last - 4;

      if (current < heroThreshold) {
        // Always show header while within hero region
        setShowHeader(true);
      } else if (scrollingUp) {
        // Reveal on slight upward scroll after hero
        setShowHeader(true);
      } else if (scrollingDown && !mobileOpen) {
        // Hide when scrolling down past hero (unless menu is open)
        setShowHeader(false);
      }

      lastScrollYRef.current = current;
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [mobileOpen]);

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
      className={`fixed top-0 left-0 right-0 z-[70] transform transition-transform duration-400 py-3 sm:py-4 backdrop-blur-xl border-b border-white/10 ${
        scrolled || mobileOpen
          ? "bg-[#05080c]/95 shadow-lg"
          : "bg-[#05080c]/85 shadow-md"
      } ${showHeader || mobileOpen ? "translate-y-0" : "-translate-y-full"}`}
    >
      <div className="w-full px-4 sm:px-6 lg:px-12">
        <div
          className="flex items-center justify-between transition-all duration-500 rounded-xl md:rounded-2xl px-4 md:px-16 py-3 md:py-4 bg-transparent"
        >
          {/* Logo Section — flame + two-line name + tagline; sizes balanced to fit a compact rectangle */}
          <Link href="/" className="flex items-center gap-2 sm:gap-2.5 group min-w-0">
            <Image
              src="/images/logo.png"
              alt={company.name}
              width={32}
              height={40}
              loading="eager"
              className="object-contain transition-transform group-hover:scale-105 duration-300 shrink-0 h-8 sm:h-9 md:h-10 w-auto"
            />
            <div className="min-w-0 flex flex-col justify-center py-0.5">
              <span className="font-technical font-bold text-[11px] sm:text-xs md:text-sm tracking-tight leading-tight uppercase text-white block">
                DPS HEATING
              </span>
              <span className="font-technical font-bold text-[11px] sm:text-xs md:text-sm tracking-tight leading-tight uppercase text-white block">
                SERVICES LTD
              </span>
              <span className="hidden sm:block h-px bg-white/30 my-0.5 w-full max-w-[100px] md:max-w-[110px]" aria-hidden />
              <span className="hidden sm:block text-[9px] sm:text-[10px] font-technical font-medium uppercase tracking-[0.18em] text-white/80 leading-tight">
                DESIGN • ENGINEER • MAINTAIN
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8" aria-label="Main navigation">
            {navLinks.map((link) =>
              link.children ? (
                  <div
                    key={link.href}
                    className="relative group"
                    onMouseEnter={() => setServicesOpen(true)}
                    onMouseLeave={() => setServicesOpen(false)}
                  >
                    <Link
                      href={link.href}
                      className="flex items-center gap-2 text-[#e5edf7] hover:text-white transition-all text-sm font-technical uppercase tracking-widest font-bold"
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
                    className="text-[#e5edf7] hover:text-white transition-all text-sm font-technical uppercase tracking-widest font-bold relative group"
                  >
                    {link.label}
                    <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-brand-red transition-all group-hover:w-full" />
                  </Link>
                )
            )}
          </nav>

          {/* Right: Theme Toggle + Admin */}
          <div className="hidden lg:flex items-center gap-6">
            {/* Theme toggle temporarily hidden */}
            {false && (
              <button
                onClick={toggleTheme}
                className="w-9 h-9 rounded-full border border-white/15 bg-white/5 flex items-center justify-center text-[#e5edf7] hover:text-[#facc6b] hover:border-[#facc6b]/70 transition-all"
                aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              >
                {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              </button>
            )}
            <Link
              href="/admin/login"
              className="w-9 h-9 rounded-xl border border-white/15 bg-white/5 flex items-center justify-center text-[#e5edf7] hover:text-[#facc6b] hover:border-[#facc6b]/70 transition-all"
              title="Admin Terminal"
            >
              <ShieldCheck size={16} />
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="lg:hidden text-white p-2"
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
                      {/* Mobile theme toggle temporarily hidden */}
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
                    {navLinks.map((link) => (
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
