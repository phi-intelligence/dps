"use client";

import { useEffect, useRef, useState } from "react";

interface LazyViewportProps {
  children: React.ReactNode;
  /** Root margin for IntersectionObserver (default: 200px) */
  rootMargin?: string;
  /** Minimum ratio of element visibility to trigger (default: 0.01) */
  threshold?: number;
  /** Placeholder shown before content loads */
  fallback?: React.ReactNode;
  /** Min height to reserve before load (avoids layout shift) */
  minHeight?: string | number;
}

const defaultFallback = (
  <div className="flex min-h-[320px] w-full items-center justify-center rounded-2xl bg-brand-navy/50">
    <div className="h-8 w-8 animate-pulse rounded-full border-2 border-[#e2c977]/40 border-t-transparent" />
  </div>
);

/**
 * Renders children only when the wrapper enters the viewport.
 * Use for heavy components (scroll sequences, maps, etc.) so they load lazily on scroll.
 */
export default function LazyViewport({
  children,
  rootMargin = "200px",
  threshold = 0.01,
  fallback = defaultFallback,
  minHeight,
}: LazyViewportProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) setInView(true);
      },
      { rootMargin, threshold }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return (
    <div
      ref={ref}
      style={minHeight ? { minHeight: typeof minHeight === "number" ? `${minHeight}px` : minHeight } : undefined}
    >
      {inView ? children : fallback}
    </div>
  );
}
