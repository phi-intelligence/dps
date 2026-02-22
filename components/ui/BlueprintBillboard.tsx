"use client";

import Image from "next/image";
import { motion } from "framer-motion";

interface BlueprintBillboardProps {
    src: string;
    alt: string;
    theme?: "cool" | "warm" | "urgent" | "tech";
    className?: string;
    labels?: Array<{
        text: string;
        position: { top?: string; bottom?: string; left?: string; right?: string };
        color?: "red" | "blue" | "purple";
    }>;
    statusText?: string;
    versionText?: string;
    idHash?: string;
}

export default function BlueprintBillboard({
    src,
    alt,
    theme = "cool",
    className = "",
    labels = [],
    statusText = "OPERATIONAL",
    versionText = "V2.4",
    idHash,
}: BlueprintBillboardProps) {
    const themeClass = {
        cool: "theme-cool",
        warm: "theme-warm",
        urgent: "theme-urgent",
        tech: "", // default
    }[theme];

    const labelColorClass = {
        red: "bg-brand-red",
        blue: "bg-brand-blue",
        purple: "bg-brand-purple",
    };

    const accentColorClass = {
        cool: "text-brand-blue border-brand-blue/40",
        warm: "text-brand-red border-brand-red/40",
        urgent: "text-brand-red border-brand-red/60",
        tech: "text-brand-purple border-brand-purple/40",
    }[theme];

    const accentGlow = {
        cool: "bg-brand-blue/10",
        warm: "bg-brand-red/10",
        urgent: "bg-brand-red/20",
        tech: "bg-brand-purple/10",
    }[theme];

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: "easeOut" }}
            className={`relative aspect-square flex items-center justify-center group ${className} ${themeClass}`}
        >
            {/* Outer Glow */}
            <div className={`absolute inset-0 ${accentGlow} blur-[100px] rounded-full group-hover:opacity-100 transition-opacity duration-700`} />

            {/* Blueprint Container - Now invisible/floating */}
            <div className="relative w-full h-full overflow-hidden animate-flicker">
                {/* Visual Scanning Line */}
                <div className="scan-line" />

                {/* The Image */}
                <div className="relative w-full h-full p-8 flex items-center justify-center group-hover:scale-105 transition-transform duration-1000">
                    <Image
                        src={src}
                        alt={alt}
                        fill
                        className="hologram-v2 object-contain scale-110"
                        priority
                    />
                </div>

                {/* HUD Labels - Now truly floating */}
                <div className={`absolute top-4 right-4 p-2 border-r border-t ${accentColorClass} bg-transparent`}>
                    <p className="text-[8px] font-technical uppercase tracking-[0.2em] font-bold">
                        ARCH_LOG: {versionText}
                    </p>
                </div>

                {idHash && (
                    <div className="absolute top-4 left-4 p-2 border-l border-t border-white/5 bg-transparent">
                        <p className="text-[8px] font-mono text-white/40 uppercase tracking-[0.1em]">
                            {idHash}
                        </p>
                    </div>
                )}

                <div className={`absolute bottom-4 left-4 p-2 border-l border-b ${accentColorClass} bg-transparent`}>
                    <div className="flex items-center gap-2">
                        <div className={`w-1 h-1 rounded-full animate-pulse ${theme === "urgent" ? "bg-brand-red" : "bg-brand-blue"}`} />
                        <p className="text-[8px] font-technical uppercase tracking-[0.2em] font-bold">
                            STATUS: {statusText}
                        </p>
                    </div>
                </div>
            </div>

            {/* External Exploded Labels (GSAP would handle complex ones, but simple ones here) */}
            {labels.map((label, i) => (
                <motion.div
                    key={label.text}
                    initial={{ opacity: 0, x: label.position.left ? -20 : 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className="absolute glass-panel rounded-lg px-4 py-2 z-20 pointer-events-none"
                    style={{
                        ...label.position,
                    }}
                >
                    <div className="flex items-center gap-2 whitespace-nowrap">
                        <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${labelColorClass[label.color || "blue"]}`} />
                        <span className="text-[9px] font-technical font-bold text-white uppercase tracking-[0.2em]">
                            {label.text}
                        </span>
                    </div>
                </motion.div>
            ))}

            {/* Decorative corners for the whole group */}
            <div className={`absolute top-0 left-0 w-8 h-8 border-l border-t ${accentColorClass} opacity-20`} />
            <div className={`absolute bottom-0 right-0 w-8 h-8 border-r border-b ${accentColorClass} opacity-20`} />
        </motion.div>
    );
}
