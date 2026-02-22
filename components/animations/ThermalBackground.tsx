"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function ThermalBackground() {
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            setMousePos({
                x: (e.clientX / window.innerWidth) * 100,
                y: (e.clientY / window.innerHeight) * 100,
            });
        };
        window.addEventListener("mousemove", handleMouseMove);
        return () => window.removeEventListener("mousemove", handleMouseMove);
    }, []);

    return (
        <div className="fixed inset-0 z-0 overflow-hidden bg-brand-surface pointer-events-none">
            {/* Primary Heat Bloom */}
            <motion.div
                animate={{
                    x: `${mousePos.x - 50}%`,
                    y: `${mousePos.y - 50}%`,
                }}
                transition={{ type: "spring", damping: 50, stiffness: 200 }}
                className="absolute top-1/2 left-1/2 w-[800px] h-[800px] rounded-full bg-brand-red/5 blur-[120px]"
            />

            {/* Secondary Plasma Glow */}
            <motion.div
                animate={{
                    x: `${(100 - mousePos.x) - 50}%`,
                    y: `${(100 - mousePos.y) - 50}%`,
                }}
                transition={{ type: "spring", damping: 70, stiffness: 150 }}
                className="absolute top-1/2 left-1/2 w-[600px] h-[600px] rounded-full bg-brand-blue/5 blur-[100px]"
            />

            {/* Grid Pattern */}
            <div
                className="absolute inset-0 opacity-[0.05]"
                style={{
                    backgroundImage: `linear-gradient(to right, var(--color-brand-card) 1px, transparent 1px), linear-gradient(to bottom, var(--color-brand-card) 1px, transparent 1px)`,
                    backgroundSize: '100px 100px',
                }}
            />

            {/* Thermal Gradient Mesh */}
            <div className="absolute inset-0 bg-gradient-to-t from-brand-surface via-transparent to-brand-surface opacity-40" />
        </div>
    );
}
