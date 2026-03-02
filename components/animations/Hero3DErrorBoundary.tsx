"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import Image from "next/image";

interface Props {
  children: ReactNode;
  /** Optional className for the fallback container (e.g. match Hero3DScene wrapper) */
  className?: string;
}

interface State {
  hasError: boolean;
}

/**
 * Error boundary for the Home 3D hero (WebGL/Canvas).
 * Catches errors during render or unmount (e.g. WebGL context lost, missing .glb) so the app and navigation stay usable.
 * Fallback shows the site logo image when the 3D model is unavailable.
 */
export default class Hero3DErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[Hero3DErrorBoundary]", error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className={this.props.className ?? "w-full aspect-square max-h-[min(85vh,680px)] min-h-[320px] overflow-hidden rounded-2xl bg-brand-navy/40 border border-brand-card-border flex items-center justify-center"}
          aria-hidden
        >
          <div className="relative w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80">
            <Image
              src="/images/logo.png"
              alt="DPS Heating Services"
              fill
              className="object-contain drop-shadow-[0_0_24px_rgba(212,175,55,0.3)]"
              sizes="(max-width: 640px) 192px, (max-width: 768px) 256px, 320px"
            />
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
