"use client";

import { useRef, useState, useCallback } from "react";

interface SpotlightCardProps {
    children: React.ReactNode;
    className?: string;
    spotlightColor?: string;
}

export default function SpotlightCard({
    children,
    className = "",
    spotlightColor = "rgba(37,99,235,0.06)",
}: SpotlightCardProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isHovered, setIsHovered] = useState(false);

    const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        setPosition({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        });
    }, []);

    return (
        <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`relative overflow-hidden ${className}`}
            style={{
                background: isHovered
                    ? `radial-gradient(300px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent)`
                    : undefined,
            }}
        >
            {children}
        </div>
    );
}
