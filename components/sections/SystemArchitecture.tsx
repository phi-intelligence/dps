"use client";

import { useEffect, useRef } from "react";
import { registerGSAP, gsap } from "@/components/animations/gsap-init";
import BlueprintBillboard from "@/components/ui/BlueprintBillboard";

const labels = [
    { text: "Thermal Exchanger", position: { top: "10%", left: "-15%" }, color: "red" as const },
    { text: "Combustion Array", position: { top: "30%", right: "-15%" }, color: "blue" as const },
    { text: "Fluid Dynamics", position: { bottom: "25%", left: "-15%" }, color: "purple" as const },
    { text: "Neural Interface", position: { bottom: "10%", right: "-15%" }, color: "blue" as const },
];

export default function SystemArchitecture() {
    const sectionRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        registerGSAP();
        const el = sectionRef.current;
        if (!el) return;

        const ctx = gsap.context(() => {
            // Animating section reveal
            gsap.fromTo(
                el,
                { opacity: 0, y: 50 },
                {
                    opacity: 1,
                    y: 0,
                    duration: 1,
                    scrollTrigger: {
                        trigger: el,
                        start: "top 80%",
                        once: true,
                    },
                }
            );
        });

        return () => ctx.revert();
    }, []);

    return (
        <section
            ref={sectionRef}
            className="py-40 bg-brand-surface border-y border-brand-card-border relative overflow-hidden"
            aria-label="System Architecture"
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-24">
                    <span className="text-brand-red text-[10px] font-technical font-bold uppercase tracking-[0.4em] mb-4 block">
                        Internal Diagnostics
                    </span>
                    <h2 className="text-4xl md:text-7xl font-technical font-extrabold text-brand-text tracking-widest uppercase">
                        System <span className="text-brand-red">Architecture</span>
                    </h2>
                </div>

                {/* Enhanced Blueprint View */}
                <div className="max-w-2xl mx-auto">
                    <BlueprintBillboard
                        src="/images/blueprints/boiler-main.jpg"
                        alt="High integrity exploded boiler schematic"
                        theme="warm"
                        versionText="CORE_MODULE: V4.0"
                        idHash="SHA: 0xFE441DA6"
                        statusText="OPTIMAL"
                        labels={labels}
                    />
                </div>
            </div>
        </section>
    );
}
