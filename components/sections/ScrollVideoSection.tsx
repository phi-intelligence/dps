"use client";

import { useRef, useEffect, forwardRef } from "react";
import { registerGSAP, gsap, ScrollTrigger } from "@/components/animations/gsap-init";

export interface ScrollVideoSectionProps {
  /** Path to video file, e.g. "/videos/capability-bg.mp4" */
  videoSrc: string;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
  /** Video layer opacity (default: opacity-30) */
  videoOpacity?: string;
  /** Overlay (default: bg-brand-surface/55 dark:bg-brand-surface/85) */
  overlayClassName?: string;
  "aria-label"?: string;
}

const ScrollVideoSection = forwardRef<HTMLElement, ScrollVideoSectionProps>(
  (
    {
      videoSrc,
      children,
      className = "",
      contentClassName = "max-w-7xl mx-auto relative z-10",
      videoOpacity = "opacity-30",
      overlayClassName = "bg-brand-surface/55 dark:bg-brand-surface/85",
      "aria-label": ariaLabel,
    },
    ref
  ) => {
    const sectionRef = useRef<HTMLElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
      if (typeof window === "undefined" || !videoSrc) return;

      registerGSAP();

      const section = sectionRef.current ?? (ref as React.RefObject<HTMLElement>)?.current;
      const video = videoRef.current;
      if (!section || !video) return;

      const onLoadedMetadata = () => {
        gsap.fromTo(
          video,
          { currentTime: 0 },
          {
            currentTime: video.duration,
            ease: "none",
            scrollTrigger: {
              trigger: section,
              start: "top bottom",
              end: "bottom top",
              scrub: true,
            },
          }
        );
        if (typeof ScrollTrigger !== "undefined") {
          ScrollTrigger.refresh();
        }
      };

      if (video.duration && !isNaN(video.duration)) {
        onLoadedMetadata();
      } else {
        video.addEventListener("loadedmetadata", onLoadedMetadata);
        return () => video.removeEventListener("loadedmetadata", onLoadedMetadata);
      }

      return () => {
        gsap.killTweensOf(video);
      };
    }, [videoSrc, ref]);

    const setRefs = (el: HTMLElement | null) => {
      sectionRef.current = el;
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLElement | null>).current = el;
    };

    return (
      <section
        ref={setRefs}
        data-scroll-video-section
        className={`relative ${className}`}
        style={{ clipPath: "inset(0)" }}
        aria-label={ariaLabel}
      >
        <div className="fixed inset-0 z-0 w-full min-h-[100vh] min-h-[100dvh] pointer-events-none" aria-hidden>
          <div className={`absolute inset-0 ${videoOpacity}`}>
            <video
              ref={videoRef}
              src={videoSrc}
              className="w-full h-full object-cover"
              style={{ objectFit: "cover" }}
              muted
              playsInline
              preload="metadata"
            />
          </div>
          <div className={`absolute inset-0 ${overlayClassName}`} />
        </div>

        <div className={contentClassName}>{children}</div>
      </section>
    );
  }
);

ScrollVideoSection.displayName = "ScrollVideoSection";

export default ScrollVideoSection;
