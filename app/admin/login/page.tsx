"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Image from "next/image";
import { Lock, User, ArrowRight, ShieldCheck } from "lucide-react";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

const inputClass =
  "w-full bg-white/10 border border-white/20 rounded-xl px-5 py-4 text-white text-sm font-sans placeholder-white/40 focus:outline-none focus:border-brand-red/70 focus:bg-white/15 transition-all backdrop-blur-sm";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
        credentials: "include",
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        if (typeof window !== "undefined") {
          window.localStorage.setItem("dps_admin_auth", "true");
          window.location.href = "/admin/dashboard";
          return;
        }
        router.push("/admin/dashboard");
      } else {
        setError(data.error ?? "Invalid username or password.");
      }
    } catch {
      setError("Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center p-4 overflow-hidden bg-brand-navy">
      {/* Background photo */}
      <Image
        src="/images/hero-bg.jpg"
        alt=""
        fill
        className="object-cover object-center"
        priority
        aria-hidden
      />
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/65" />
      {/* Gradient vignette */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-navy/40 via-transparent to-brand-navy/60" />
      {/* Energy flow waves on top */}
      <EnergyFlowBackground />

      {/* Login card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative z-10 w-full max-w-sm"
      >
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 shadow-2xl shadow-black/40">
          {/* Header */}
          <div className="flex flex-col items-center mb-8 text-center">
            <div className="w-14 h-14 rounded-xl bg-brand-red/20 border border-brand-red/40 flex items-center justify-center mb-4 shadow-lg shadow-brand-red/10">
              <ShieldCheck size={28} className="text-white" />
            </div>
            <h1 className="text-xl font-sans font-bold text-white tracking-tight mb-1">
              Admin Login
            </h1>
            <p className="text-white/50 text-xs">
              DPS Heating Services — Admin Area
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-white/60 mb-2">
                <User size={12} className="text-brand-red" />
                Username
              </label>
              <input
                type="text"
                autoComplete="username"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={inputClass}
                required
              />
            </div>

            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-white/60 mb-2">
                <Lock size={12} className="text-brand-red" />
                Password
              </label>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
                required
              />
            </div>

            {error && (
              <p className="text-xs text-red-400 text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group w-full bg-brand-red text-white py-4 rounded-xl font-sans font-bold text-sm tracking-wide transition-all hover:bg-brand-red/90 disabled:opacity-50 flex items-center justify-center gap-2 mt-2 shadow-lg shadow-brand-red/20"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-[11px] text-white/30">
            Default: <span className="font-mono text-white/50">admin / admin</span> (set ADMIN_USERNAME / ADMIN_PASSWORD to override)
          </p>
        </div>
      </motion.div>
    </div>
  );
}
