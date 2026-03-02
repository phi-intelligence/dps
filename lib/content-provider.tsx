"use client";

import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import type { Company, OpeningHours, NavLinkItem } from "@/lib/content";
import { COMPANY, OPENING_HOURS, NAV_LINKS } from "@/lib/constants";

interface SiteConfigState {
  company: Company;
  openingHours: OpeningHours;
}

interface ContentContextValue {
  site: SiteConfigState | null;
  nav: NavLinkItem[];
  company: Company;
  openingHours: OpeningHours;
}

const fallbackNav: NavLinkItem[] = [
  { label: "Home", href: "/" },
  {
    label: "Services",
    href: "/services",
    children: [
      { label: "Commercial Services", href: "/services/commercial" },
      { label: "Domestic Services", href: "/services/domestic" },
    ],
  },
  { label: "Portfolio", href: "/portfolio" },
  { label: "About Us", href: "/about" },
  { label: "Service Areas", href: "/service-areas" },
  { label: "Contact", href: "/contact" },
];

const ContentContext = createContext<ContentContextValue | null>(null);

export function ContentProvider({
  initialSite,
  initialNav,
  children,
}: {
  initialSite: { company: Company; openingHours: OpeningHours } | null;
  initialNav: NavLinkItem[] | null;
  children: ReactNode;
}) {
  const value = useMemo<ContentContextValue>(() => {
    const company = initialSite?.company ?? COMPANY as unknown as Company;
    const openingHours = initialSite?.openingHours ?? OPENING_HOURS as unknown as OpeningHours;
    const nav = initialNav && initialNav.length > 0 ? initialNav : fallbackNav;
    return {
      site: initialSite,
      nav,
      company,
      openingHours,
    };
  }, [initialSite, initialNav]);

  return (
    <ContentContext.Provider value={value}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent(): ContentContextValue {
  const ctx = useContext(ContentContext);
  if (!ctx) {
    return {
      site: null,
      nav: fallbackNav,
      company: COMPANY as unknown as Company,
      openingHours: OPENING_HOURS as unknown as OpeningHours,
    };
  }
  return ctx;
}
