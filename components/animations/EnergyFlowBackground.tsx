"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function EnergyFlowBackground() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1440 900"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Primary warm wave — large red-orange sweep from bottom-left to upper-right */}
        <motion.path
          d="M-200 900 C200 700, 500 850, 800 600 C1100 350, 1300 500, 1600 300 L1600 900 Z"
          fill="url(#wave-warm)"
          initial={{ opacity: 0, x: -40 }}
          animate={{
            opacity: 1,
            x: 0,
            d: [
              "M-200 900 C200 700, 500 850, 800 600 C1100 350, 1300 500, 1600 300 L1600 900 Z",
              "M-200 900 C180 720, 520 830, 820 580 C1120 330, 1280 520, 1600 320 L1600 900 Z",
              "M-200 900 C200 700, 500 850, 800 600 C1100 350, 1300 500, 1600 300 L1600 900 Z",
            ],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Secondary cool wave — blue sweep from upper-right */}
        <motion.path
          d="M600 0 C800 150, 1000 50, 1200 200 C1400 350, 1500 200, 1600 250 L1600 0 Z"
          fill="url(#wave-cool)"
          initial={{ opacity: 0, x: 40 }}
          animate={{
            opacity: 1,
            x: 0,
            d: [
              "M600 0 C800 150, 1000 50, 1200 200 C1400 350, 1500 200, 1600 250 L1600 0 Z",
              "M580 0 C780 130, 1020 70, 1220 180 C1420 330, 1480 220, 1600 270 L1600 0 Z",
              "M600 0 C800 150, 1000 50, 1200 200 C1400 350, 1500 200, 1600 250 L1600 0 Z",
            ],
          }}
          transition={{ duration: 22, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
        />

        {/* Tertiary warm accent — smaller orange ribbon in the middle */}
        <motion.path
          d="M-100 500 C200 350, 500 550, 800 400 C1100 250, 1400 380, 1700 280"
          stroke="url(#ribbon-orange)"
          strokeWidth="100"
          strokeLinecap="round"
          fill="none"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{
            pathLength: 1,
            opacity: 0.6,
            d: [
              "M-100 500 C200 350, 500 550, 800 400 C1100 250, 1400 380, 1700 280",
              "M-100 480 C220 370, 520 530, 820 380 C1120 230, 1380 400, 1700 300",
              "M-100 500 C200 350, 500 550, 800 400 C1100 250, 1400 380, 1700 280",
            ],
          }}
          transition={{ duration: 28, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
        />

        <defs>
          {/* Warm wave gradient: red → orange with soft edges */}
          <linearGradient id="wave-warm" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EF4444" stopOpacity="0.12" />
            <stop offset="40%" stopColor="#F97316" stopOpacity="0.10" />
            <stop offset="70%" stopColor="#FBBF24" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#FBBF24" stopOpacity="0" />
          </linearGradient>

          {/* Cool wave gradient: blue → teal */}
          <linearGradient id="wave-cool" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0" />
            <stop offset="30%" stopColor="#2563EB" stopOpacity="0.08" />
            <stop offset="60%" stopColor="#06B6D4" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.04" />
          </linearGradient>

          {/* Orange ribbon gradient */}
          <linearGradient id="ribbon-orange" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EF4444" stopOpacity="0" />
            <stop offset="20%" stopColor="#EF4444" stopOpacity="0.15" />
            <stop offset="50%" stopColor="#F97316" stopOpacity="0.20" />
            <stop offset="80%" stopColor="#FBBF24" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#FBBF24" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>

      {/* Soft blur to diffuse the shapes */}
      <div className="absolute inset-0 backdrop-blur-[30px] pointer-events-none" />
    </div>
  );
}
