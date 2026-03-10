"use client";

import { motion } from "framer-motion";
import Image from "next/image";

export default function PageLoader() {
  return (
    <motion.div
      className="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-[#05080c]"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Geometric background */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-[32rem] w-[32rem] rotate-3 border border-white/10 rounded-[3rem]" />
        <div className="absolute -bottom-40 -left-40 h-[26rem] w-[26rem] -rotate-6 border border-[#e2c977]/20 rounded-[3rem]" />
        <div className="absolute inset-x-10 top-1/2 h-px bg-gradient-to-r from-transparent via-[#e2c977]/25 to-transparent" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative h-16 w-48 sm:h-20 sm:w-56 md:h-24 md:w-64"
        >
          <Image
            src="/imagesv2/logo_full_light_nobg.png"
            alt=""
            fill
            className="object-contain"
            sizes="256px"
            priority
          />
        </motion.div>

        <div className="flex flex-col items-center gap-4">
          <motion.div
            className="h-1 w-32 overflow-hidden rounded-full bg-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <motion.div
              className="h-full w-1/3 rounded-full bg-[#e2c977]"
              animate={{ x: ["0%", "200%"] }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </motion.div>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-[10px] font-technical font-bold uppercase tracking-[0.35em] text-[#b3c0d0]"
          >
            Loading
          </motion.p>
        </div>
      </div>
    </motion.div>
  );
}
