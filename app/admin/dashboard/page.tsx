"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import {
  Users,
  Search,
  Trash2,
  CheckCircle,
  Clock,
  ShieldCheck,
  LogOut,
  LayoutDashboard,
  ExternalLink,
  MessageSquare,
  Menu,
  X,
  Phone,
  Mail,
  Settings,
} from "lucide-react";
import type { Inquiry } from "@/lib/inquiry-service";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

/* ── Status badge config ──────────────────────────────── */
const statusConfig = {
  pending: {
    label: "Pending",
    dot: "bg-amber-400 animate-pulse",
    badge: "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-400/10 dark:border-amber-400/40 dark:text-amber-300",
  },
  contacted: {
    label: "Contacted",
    dot: "bg-blue-400",
    badge: "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-400/10 dark:border-blue-400/40 dark:text-blue-300",
  },
  completed: {
    label: "Completed",
    dot: "bg-emerald-400",
    badge: "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-400/10 dark:border-emerald-400/40 dark:text-emerald-300",
  },
  archived: {
    label: "Archived",
    dot: "bg-slate-400",
    badge: "bg-slate-100 border-slate-200 text-slate-500 dark:bg-slate-700/40 dark:border-slate-600 dark:text-slate-400",
  },
};

/* ── Sidebar content ──────────────────────────────────── */
function SidebarContent({
  onNavigate,
  onLogout,
}: {
  onNavigate: () => void;
  onLogout: () => void;
}) {
  const router = useRouter();
  return (
    <>
      {/* Brand */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-red flex items-center justify-center shadow-lg shadow-brand-red/30">
            <ShieldCheck size={18} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-sm text-white tracking-tight">DPS Admin</p>
            <p className="text-[10px] text-white/50">Heating Services</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        <button
          onClick={() => {
            router.push("/admin/dashboard");
            onNavigate();
          }}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-white/60 hover:bg-white/10 hover:text-white font-medium text-sm transition-all"
        >
          <LayoutDashboard size={16} />
          Inquiries
        </button>
        <button
          onClick={() => {
            router.push("/admin/content/site");
            onNavigate();
          }}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-white/60 hover:bg-white/10 hover:text-white font-medium text-sm transition-all"
        >
          <Settings size={16} />
          Site Config
        </button>
        <button
          onClick={() => {
            router.push("/");
            onNavigate();
          }}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-white/60 hover:bg-white/10 hover:text-white font-medium text-sm transition-all"
        >
          <ExternalLink size={16} />
          View Website
        </button>
      </nav>

      {/* Sign out */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-white/60 hover:bg-red-500/25 hover:text-red-300 font-medium text-sm transition-all"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </>
  );
}

/* ── Dashboard ────────────────────────────────────────── */
export default function AdminDashboardPage() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const isAuth = localStorage.getItem("dps_admin_auth") === "true";
    if (!isAuth) {
      router.push("/admin/login");
      return;
    }
    fetch("/api/admin/inquiries", { credentials: "include" })
      .then((res) => {
        if (res.status === 401) {
          localStorage.removeItem("dps_admin_auth");
          router.push("/admin/login");
          return [];
        }
        return res.json();
      })
      .then((data: Inquiry[]) => {
        if (Array.isArray(data)) setInquiries(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("dps_admin_auth");
    fetch("/api/admin/logout", { method: "POST", credentials: "include" }).catch(() => {});
    router.push("/admin/login");
  };

  const updateStatus = (id: string, status: Inquiry["status"]) => {
    fetch(`/api/admin/inquiries/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
      credentials: "include",
    })
      .then((res) => res.ok && res.json())
      .then(() => {
        setInquiries((prev) =>
          prev.map((i) => (i.id === id ? { ...i, status } : i))
        );
      });
  };

  const deleteInquiry = (id: string) => {
    if (!confirm("Permanently delete this inquiry?")) return;
    fetch(`/api/admin/inquiries/${id}`, {
      method: "DELETE",
      credentials: "include",
    })
      .then((res) => res.ok)
      .then((ok) => {
        if (ok) setInquiries((prev) => prev.filter((i) => i.id !== id));
      });
  };

  const filteredInquiries = inquiries.filter(
    (inq) =>
      inq.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inq.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inq.service.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return null;

  const stats = [
    {
      label: "Total Inquiries",
      value: inquiries.length,
      icon: MessageSquare,
      iconClass: "text-brand-red",
      bgClass: "bg-red-50 border-red-100 dark:bg-red-500/10 dark:border-red-500/20",
    },
    {
      label: "Pending",
      value: inquiries.filter((i) => i.status === "pending").length,
      icon: Clock,
      iconClass: "text-amber-500",
      bgClass: "bg-amber-50 border-amber-100 dark:bg-amber-400/10 dark:border-amber-400/20",
    },
    {
      label: "Contacted",
      value: inquiries.filter((i) => i.status === "contacted").length,
      icon: Users,
      iconClass: "text-blue-500",
      bgClass: "bg-blue-50 border-blue-100 dark:bg-blue-400/10 dark:border-blue-400/20",
    },
    {
      label: "Completed",
      value: inquiries.filter((i) => i.status === "completed").length,
      icon: CheckCircle,
      iconClass: "text-emerald-500",
      bgClass: "bg-emerald-50 border-emerald-100 dark:bg-emerald-400/10 dark:border-emerald-400/20",
    },
  ];

  return (
    /* Page root — slate-50 light, slate-950 dark */
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">

      {/* Energy wave background */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-40 dark:opacity-100">
        <EnergyFlowBackground />
      </div>

      {/* ── Desktop sidebar ─────────────────────────────── */}
      <aside className="fixed left-0 top-0 bottom-0 w-64 hidden lg:flex flex-col z-50 overflow-hidden border-r border-white/10">
        <Image
          src="/images/blueprint-plant-room.png"
          alt=""
          fill
          className="object-cover object-center"
          aria-hidden
        />
        <div className="absolute inset-0 bg-slate-900/88" />
        <div className="relative z-10 flex flex-col h-full">
          <SidebarContent onNavigate={() => {}} onLogout={handleLogout} />
        </div>
      </aside>

      {/* ── Mobile sidebar overlay ───────────────────────── */}
      <AnimatePresence>
        {mobileNavOpen && (
          <motion.div
            initial={{ opacity: 0, x: "-100%" }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: "-100%" }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-[60] flex"
          >
            <div className="relative w-64 flex flex-col h-full shadow-2xl overflow-hidden">
              <Image
                src="/images/blueprint-plant-room.png"
                alt=""
                fill
                className="object-cover object-center"
                aria-hidden
              />
              <div className="absolute inset-0 bg-slate-900/88" />
              <button
                onClick={() => setMobileNavOpen(false)}
                className="absolute top-4 right-4 z-20 p-2 rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
              >
                <X size={20} />
              </button>
              <div className="relative z-10 flex flex-col h-full">
                <SidebarContent
                  onNavigate={() => setMobileNavOpen(false)}
                  onLogout={handleLogout}
                />
              </div>
            </div>
            <div className="flex-1 bg-black/50" onClick={() => setMobileNavOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main content ─────────────────────────────────── */}
      <div className="lg:pl-64 min-h-screen flex flex-col">

        {/* Top bar */}
        <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-b border-slate-200 dark:border-slate-700/60 px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setMobileNavOpen(true)}
                className="lg:hidden p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-all"
              >
                <Menu size={20} />
              </button>
              <div>
                <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  Inquiries
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
                  {inquiries.length} total ·{" "}
                  {inquiries.filter((i) => i.status === "pending").length} pending
                </p>
              </div>
            </div>

            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500"
              />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-brand-red/50 transition-all w-40 sm:w-56"
              />
            </div>
          </div>
        </header>

        {/* Body */}
        <div className="p-6 lg:p-8 space-y-6 flex-1">

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 backdrop-blur-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2">
                      {stat.label}
                    </p>
                    <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                      {stat.value}
                    </p>
                  </div>
                  <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${stat.bgClass}`}>
                    <stat.icon size={18} className={stat.iconClass} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Table */}
          <div className="bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-2xl overflow-hidden backdrop-blur-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left min-w-[700px]">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/60">
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Date
                    </th>
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Customer
                    </th>
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Service
                    </th>
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Status
                    </th>
                    <th className="px-6 py-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
                  {filteredInquiries.length > 0 ? (
                    filteredInquiries.map((inq) => {
                      const sc = statusConfig[inq.status] ?? statusConfig.pending;
                      const nextStatus: Inquiry["status"] =
                        inq.status === "pending"
                          ? "contacted"
                          : inq.status === "contacted"
                          ? "completed"
                          : "pending";

                      return (
                        <tr
                          key={inq.id}
                          className="hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors group"
                        >
                          <td className="px-6 py-5">
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                              {new Date(inq.timestamp).toLocaleDateString("en-GB", {
                                day: "numeric",
                                month: "short",
                                year: "numeric",
                              })}
                            </p>
                            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                              {new Date(inq.timestamp).toLocaleTimeString("en-GB", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                              {inq.name}
                            </p>
                            <a
                              href={`mailto:${inq.email}`}
                              className="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 hover:text-brand-red transition-colors mt-0.5"
                            >
                              <Mail size={10} />
                              {inq.email}
                            </a>
                            {inq.phone && (
                              <a
                                href={`tel:${inq.phone}`}
                                className="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 hover:text-brand-red transition-colors mt-0.5"
                              >
                                <Phone size={10} />
                                {inq.phone}
                              </a>
                            )}
                            {inq.message && (
                              <p className="mt-2 text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed max-w-[220px] line-clamp-2 italic">
                                &ldquo;{inq.message}&rdquo;
                              </p>
                            )}
                          </td>
                          <td className="px-6 py-5">
                            <span className="inline-block px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-[11px] font-medium text-slate-700 dark:text-slate-300 capitalize">
                              {inq.service.replace(/-/g, " ")}
                            </span>
                          </td>
                          <td className="px-6 py-5">
                            <span
                              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold border ${sc.badge}`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                              {sc.label}
                            </span>
                          </td>
                          <td className="px-6 py-5 text-right">
                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => updateStatus(inq.id, nextStatus)}
                                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-600 text-slate-400 dark:text-slate-500 hover:text-brand-red hover:border-brand-red/40 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all"
                                title={`Mark as ${nextStatus}`}
                              >
                                <CheckCircle size={15} />
                              </button>
                              <button
                                onClick={() => deleteInquiry(inq.id)}
                                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-600 text-slate-400 dark:text-slate-500 hover:text-red-500 hover:border-red-400/40 hover:bg-red-50 dark:hover:bg-red-500/10 transition-all"
                                title="Delete inquiry"
                              >
                                <Trash2 size={15} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-6 py-20 text-center">
                        <MessageSquare
                          size={40}
                          className="text-slate-300 dark:text-slate-600 mx-auto mb-4"
                        />
                        <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">
                          No inquiries yet
                        </p>
                        <p className="text-xs text-slate-400 dark:text-slate-500">
                          {searchTerm
                            ? "No results match your search."
                            : "When customers submit inquiries, they will appear here."}
                        </p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
