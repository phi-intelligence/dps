"use client";

import { AnimatePresence } from "framer-motion";
import { usePageReady } from "@/lib/use-page-ready";
import PageLoader from "./PageLoader";

interface PageLoadGuardProps {
  children: React.ReactNode;
}

/**
 * Delays rendering children until the page is fully ready (load event, fonts, min time).
 * This ensures scroll-triggered animations only fire when the user scrolls, not during loading.
 */
export default function PageLoadGuard({ children }: PageLoadGuardProps) {
  const ready = usePageReady();

  return (
    <AnimatePresence mode="wait">
      {!ready ? (
        <PageLoader key="loader" />
      ) : (
        <div key="content">{children}</div>
      )}
    </AnimatePresence>
  );
}
