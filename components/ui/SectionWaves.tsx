"use client";

interface SectionWavesProps {
  variant?: "warm" | "cool" | "mixed";
  className?: string;
}

export default function SectionWaves({ variant = "warm", className = "" }: SectionWavesProps) {
  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`} aria-hidden="true">
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1440 800"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        {variant === "warm" && (
          <>
            {/* Large red-orange wave sweeping from bottom-left */}
            <path
              d="M-200 800 C100 600, 400 750, 700 500 C1000 250, 1200 400, 1500 200 L1500 800 Z"
              fill="url(#sw-warm-1)"
            />
            {/* Smaller accent wave */}
            <path
              d="M800 800 C900 650, 1100 700, 1300 550 C1400 450, 1440 500, 1500 400 L1500 800 Z"
              fill="url(#sw-warm-2)"
            />
            <defs>
              <linearGradient id="sw-warm-1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#EF4444" stopOpacity="0.08" />
                <stop offset="50%" stopColor="#F97316" stopOpacity="0.06" />
                <stop offset="100%" stopColor="#FBBF24" stopOpacity="0.02" />
              </linearGradient>
              <linearGradient id="sw-warm-2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#F97316" stopOpacity="0.06" />
                <stop offset="100%" stopColor="#EF4444" stopOpacity="0.10" />
              </linearGradient>
            </defs>
          </>
        )}

        {variant === "cool" && (
          <>
            {/* Blue wave from upper-right */}
            <path
              d="M500 0 C700 200, 1000 100, 1200 250 C1350 350, 1440 200, 1500 300 L1500 0 Z"
              fill="url(#sw-cool-1)"
            />
            {/* Teal accent from bottom-right */}
            <path
              d="M900 800 C1000 650, 1200 750, 1350 600 C1440 500, 1500 580, 1500 450 L1500 800 Z"
              fill="url(#sw-cool-2)"
            />
            <defs>
              <linearGradient id="sw-cool-1" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#2563EB" stopOpacity="0.02" />
                <stop offset="50%" stopColor="#2563EB" stopOpacity="0.07" />
                <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.05" />
              </linearGradient>
              <linearGradient id="sw-cool-2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.04" />
                <stop offset="100%" stopColor="#2563EB" stopOpacity="0.08" />
              </linearGradient>
            </defs>
          </>
        )}

        {variant === "mixed" && (
          <>
            {/* Warm wave from left */}
            <path
              d="M-200 800 C0 550, 300 700, 600 450 C900 200, 1000 350, 1200 150 L-200 150 Z"
              fill="url(#sw-mix-warm)"
            />
            {/* Cool wave from right */}
            <path
              d="M700 0 C900 200, 1100 80, 1300 250 C1440 380, 1500 280, 1500 350 L1500 0 Z"
              fill="url(#sw-mix-cool)"
            />
            {/* Blended ribbon through the middle */}
            <path
              d="M-100 400 C200 300, 500 500, 800 350 C1100 200, 1300 350, 1500 250"
              stroke="url(#sw-mix-ribbon)"
              strokeWidth="80"
              strokeLinecap="round"
              fill="none"
              opacity="0.5"
            />
            <defs>
              <linearGradient id="sw-mix-warm" x1="0%" y1="0%" x2="80%" y2="100%">
                <stop offset="0%" stopColor="#EF4444" stopOpacity="0.10" />
                <stop offset="60%" stopColor="#F97316" stopOpacity="0.07" />
                <stop offset="100%" stopColor="#FBBF24" stopOpacity="0.02" />
              </linearGradient>
              <linearGradient id="sw-mix-cool" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#2563EB" stopOpacity="0.02" />
                <stop offset="50%" stopColor="#2563EB" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.05" />
              </linearGradient>
              <linearGradient id="sw-mix-ribbon" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#EF4444" stopOpacity="0" />
                <stop offset="30%" stopColor="#EF4444" stopOpacity="0.12" />
                <stop offset="70%" stopColor="#2563EB" stopOpacity="0.10" />
                <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
              </linearGradient>
            </defs>
          </>
        )}
      </svg>
    </div>
  );
}
