"use client";

import { useRef, useEffect, useState, forwardRef } from "react";
import { registerGSAP, gsap, ScrollTrigger } from "@/components/animations/gsap-init";

function buildFrameUrls(basePath: string, count: number): string[] {
  return Array.from({ length: count }, (_, i) => {
    const num = (i + 1).toString().padStart(4, "0");
    return `${basePath}-${num}.webp`;
  });
}

export interface ScrollSequenceSectionProps {
  /** Base path for frame images, e.g. "/images/about-who-we-are-frames/frame". Frames must be named frame-0001.webp, frame-0002.webp, ... */
  frameDir: string;
  /** Total number of frames. */
  frameCount: number;
  children: React.ReactNode;
  className?: string;
  /** Class for the content wrapper (default: max-w-7xl mx-auto relative z-10) */
  contentClassName?: string;
  /** Canvas opacity wrapper (default: opacity-30 dark:opacity-20) */
  canvasOpacity?: string;
  /** Overlay background (default: bg-brand-surface/55 dark:bg-brand-surface/85) */
  overlayClassName?: string;
  /** Accessible label for the section */
  "aria-label"?: string;
}

const ScrollSequenceSection = forwardRef<HTMLElement, ScrollSequenceSectionProps>(
  (
    {
      frameDir,
      frameCount,
      children,
      className = "",
      contentClassName = "max-w-7xl mx-auto relative z-10",
      canvasOpacity = "opacity-30 dark:opacity-20",
      overlayClassName = "bg-brand-surface/55 dark:bg-brand-surface/85",
      "aria-label": ariaLabel,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imagesRef = useRef<HTMLImageElement[]>([]);
    const [imagesLoaded, setImagesLoaded] = useState(false);
    const count = frameCount > 0 ? frameCount : 0;
    const sectionRef = useRef<HTMLElement>(null);

    useEffect(() => {
      if (typeof window === "undefined" || !frameDir || count === 0) return;

      registerGSAP();

      const urls = buildFrameUrls(frameDir, count);
      const images: HTMLImageElement[] = [];
      let loaded = 0;

      const onLoad = () => {
        loaded++;
        if (loaded === count) {
          imagesRef.current = images;
          setImagesLoaded(true);
        }
      };

      urls.forEach((src) => {
        const img = new Image();
        img.onload = onLoad;
        img.onerror = onLoad;
        img.src = src;
        images.push(img);
      });

      return () => {
        images.forEach((img) => {
          img.onload = null;
          img.onerror = null;
          img.src = "";
        });
        imagesRef.current = [];
      };
    }, [frameDir, count]);

    useEffect(() => {
      if (!imagesLoaded || !canvasRef.current) return;

      const section = sectionRef.current ?? canvasRef.current.closest("section");
      if (!section) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const images = imagesRef.current;
      if (!ctx || !images.length) return;

      const playhead = { frame: 0 };

      const updateImage = () => {
        const idx = Math.round(playhead.frame);
        const img = images[Math.min(idx, images.length - 1)];
        if (img && img.complete && img.naturalWidth) {
          const cw = canvas.width;
          const ch = canvas.height;
          const iw = img.naturalWidth;
          const ih = img.naturalHeight;
          const scale = Math.max(cw / iw, ch / ih);
          const sw = iw * scale;
          const sh = ih * scale;
          const sx = (cw - sw) / 2;
          const sy = (ch - sh) / 2;
          ctx.drawImage(img, sx, sy, sw, sh);
        }
      };

      const resize = () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const dpr = Math.min(window.devicePixelRatio ?? 1, 2);
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;
        updateImage();
        if (typeof ScrollTrigger !== "undefined") {
          ScrollTrigger.refresh();
        }
      };

      resize();
      window.addEventListener("resize", resize);

      const tween = gsap.to(playhead, {
        frame: count - 1,
        ease: "none",
        onUpdate: updateImage,
        scrollTrigger: {
          trigger: section,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      });

      updateImage();

      return () => {
        window.removeEventListener("resize", resize);
        tween.kill();
      };
    }, [imagesLoaded, frameDir, count]);

    const setRefs = (el: HTMLElement | null) => {
      sectionRef.current = el;
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLElement | null>).current = el;
    };

    return (
      <section
        ref={setRefs}
        data-scroll-sequence-section
        className={`relative ${className}`}
        style={{ clipPath: "inset(0)" }}
        aria-label={ariaLabel}
      >
        <div className="fixed inset-0 z-0 w-full min-h-[100vh] min-h-[100dvh] pointer-events-none" aria-hidden>
          <div className={`absolute inset-0 ${canvasOpacity}`}>
            <canvas
              ref={canvasRef}
              className="sequence-canvas w-full h-full object-cover"
              style={{ objectFit: "cover" }}
            />
          </div>
          <div className={`absolute inset-0 ${overlayClassName}`} />
        </div>

        <div className={contentClassName}>{children}</div>
      </section>
    );
  }
);

ScrollSequenceSection.displayName = "ScrollSequenceSection";

export default ScrollSequenceSection;
