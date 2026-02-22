"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useScroll, useMotionValueEvent, motion, AnimatePresence, type MotionValue } from "framer-motion";
import { useTheme } from "@/lib/theme-provider";

interface Callout {
  progress: number;
  title: string;
  description: string;
}

interface ScrollImageSequenceProps {
  pathPrefix: string;
  frameCount: number;
  fileExtension?: string;
  startIndex?: number;
  callouts?: Callout[];
  className?: string;
}

export default function ScrollImageSequence({
  pathPrefix,
  frameCount,
  fileExtension = "jpg",
  startIndex = 1,
  callouts = [],
  className = "",
}: ScrollImageSequenceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imagesRef = useRef<HTMLImageElement[]>([]);
  const loadedRef = useRef(0);
  const [loadedCount, setLoadedCount] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);
  const [activeCalloutIdx, setActiveCalloutIdx] = useState(-1);
  const { theme } = useTheme();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // ── Preload all frames ─────────────────────────────────────────────
  useEffect(() => {
    loadedRef.current = 0;
    setLoadedCount(0);
    setIsLoaded(false);
    imagesRef.current = [];

    const imgs: HTMLImageElement[] = new Array(frameCount);

    const onSettled = () => {
      loadedRef.current += 1;
      setLoadedCount(loadedRef.current);
      if (loadedRef.current >= frameCount) {
        imagesRef.current = imgs;
        setIsLoaded(true);
      }
    };

    for (let i = 0; i < frameCount; i++) {
      const img = new Image();
      img.src = `${pathPrefix}${String(i + startIndex).padStart(3, "0")}.${fileExtension}`;
      img.onload = onSettled;
      img.onerror = onSettled;
      imgs[i] = img;
    }

    return () => {
      imgs.forEach((img) => {
        img.onload = null;
        img.onerror = null;
      });
    };
  }, [pathPrefix, frameCount, startIndex, fileExtension]);

  // ── Draw a single frame ────────────────────────────────────────────
  const drawFrame = useCallback(
    (progress: number) => {
      const canvas = canvasRef.current;
      const imgs = imagesRef.current;
      if (!canvas || !imgs.length) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const pw = Math.round(rect.width * dpr);
      const ph = Math.round(rect.height * dpr);

      if (canvas.width !== pw || canvas.height !== ph) {
        canvas.width = pw;
        canvas.height = ph;
      }

      const idx = Math.max(0, Math.min(Math.round(progress * (frameCount - 1)), frameCount - 1));
      const img = imgs[idx];
      if (!img?.complete || !img.naturalWidth) return;

      ctx.clearRect(0, 0, pw, ph);

      // "contain" fit at physical pixel dimensions
      const scale = Math.min(pw / img.naturalWidth, ph / img.naturalHeight);
      const dw = img.naturalWidth * scale;
      const dh = img.naturalHeight * scale;
      ctx.drawImage(img, (pw - dw) / 2, (ph - dh) / 2, dw, dh);

      // Update active callout
      const ai = callouts.findIndex((c) => Math.abs(c.progress - progress) < 0.1);
      setActiveCalloutIdx(ai);
    },
    [frameCount, callouts]
  );

  // ── Scroll-driven frame updates ────────────────────────────────────
  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    if (isLoaded) drawFrame(latest);
  });

  // ── Draw first frame as soon as images are ready ───────────────────
  useEffect(() => {
    if (isLoaded) drawFrame(scrollYProgress.get());
  }, [isLoaded, drawFrame, scrollYProgress]);

  // ── Re-draw on canvas resize ───────────────────────────────────────
  useEffect(() => {
    if (!isLoaded) return;
    const ro = new ResizeObserver(() => drawFrame(scrollYProgress.get()));
    if (canvasRef.current) ro.observe(canvasRef.current);
    return () => ro.disconnect();
  }, [isLoaded, drawFrame, scrollYProgress]);

  const loadPercent = Math.round((loadedCount / frameCount) * 100);

  return (
    <div ref={containerRef} className={`relative h-[300vh] ${className}`}>
      <div className="sticky top-0 h-screen w-full overflow-hidden bg-brand-surface">

        {/* Grid background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(var(--color-brand-card) 1px, transparent 1px), linear-gradient(90deg, var(--color-brand-card) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
            opacity: 0.6,
          }}
        />

        {/* Canvas — theme-aware CSS class handles blend mode */}
        <canvas
          ref={canvasRef}
          className={`absolute inset-0 w-full h-full${theme === "dark" ? " sequence-canvas" : ""}`}
        />

        {/* Loading overlay */}
        <AnimatePresence>
          {!isLoaded && (
            <motion.div
              exit={{ opacity: 0, transition: { duration: 0.5 } }}
              className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-brand-surface gap-5"
            >
              <div className="w-56 h-px bg-brand-card-border rounded-full overflow-hidden relative">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-brand-red"
                  animate={{ width: `${loadPercent}%` }}
                  transition={{ duration: 0.1 }}
                />
              </div>
              <p className="text-[9px] font-technical uppercase tracking-[0.5em] text-brand-muted">
                LOADING — {loadPercent}%
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Callout pill — centred at bottom, fades in/out */}
        <AnimatePresence mode="wait">
          {isLoaded && activeCalloutIdx >= 0 && callouts[activeCalloutIdx] && (
            <motion.div
              key={activeCalloutIdx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="absolute bottom-16 inset-x-0 flex justify-center z-20 pointer-events-none"
            >
              <div className="flex items-center gap-3 bg-brand-navy/80 backdrop-blur-xl border border-brand-card-border px-6 py-2.5 rounded-full shadow-xl shadow-brand-red/5">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse shrink-0" />
                <span className="text-[9px] font-technical font-bold uppercase tracking-[0.4em] text-brand-red">
                  {callouts[activeCalloutIdx].title}
                </span>
                <span className="w-px h-3 bg-brand-card-border-hover shrink-0" />
                <span className="text-[9px] font-technical uppercase tracking-[0.25em] text-brand-muted">
                  {callouts[activeCalloutIdx].description}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* HUD overlay */}
        <div className="absolute inset-0 pointer-events-none">
          {/* Top-left badge */}
          <div className="absolute top-8 left-8 flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse" />
            <span className="text-[8px] font-technical uppercase tracking-[0.5em] text-brand-muted">
              ASSEMBLY_VIEW
            </span>
          </div>

          {/* Frame counter — isolated to prevent parent re-renders */}
          <FrameCounter scrollYProgress={scrollYProgress} frameCount={frameCount} />

          {/* Corner brackets */}
          <div className="absolute top-5 left-5 w-5 h-5 border-t border-l border-brand-red/20" />
          <div className="absolute top-5 right-5 w-5 h-5 border-t border-r border-brand-red/20" />
          <div className="absolute bottom-5 left-5 w-5 h-5 border-b border-l border-brand-red/20" />
          <div className="absolute bottom-5 right-5 w-5 h-5 border-b border-r border-brand-red/20" />
        </div>
      </div>
    </div>
  );
}

// Isolated sub-component — its setState doesn't trigger ScrollImageSequence re-renders
function FrameCounter({
  scrollYProgress,
  frameCount,
}: {
  scrollYProgress: MotionValue<number>;
  frameCount: number;
}) {
  const [frame, setFrame] = useState(1);

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    setFrame(Math.round(latest * (frameCount - 1)) + 1);
  });

  return (
    <div className="absolute top-8 right-8 hidden sm:block">
      <span className="text-[8px] font-technical uppercase tracking-[0.5em] text-brand-muted">
        {String(frame).padStart(2, "0")} / {String(frameCount).padStart(2, "0")}
      </span>
    </div>
  );
}
