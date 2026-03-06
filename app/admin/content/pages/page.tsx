"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileText, ExternalLink } from "lucide-react";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

interface ManagedPage {
  id: string;
  label: string;
  description: string;
  path: string;
  adminPath: string;
}

const PAGES: ManagedPage[] = [
  {
    id: "home",
    label: "Home",
    description: "Hero, core services, sectors and contact funnels.",
    path: "/",
    adminPath: "/admin/content/pages/home",
  },
  {
    id: "about",
    label: "About Us",
    description: "Company story, values and credentials.",
    path: "/about",
    adminPath: "/admin/content/pages/about",
  },
  {
    id: "portfolio",
    label: "Portfolio",
    description: "Selected projects and case studies.",
    path: "/portfolio",
    adminPath: "/admin/content/pages/portfolio",
  },
];

export default function AdminContentPages() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const isAuth = localStorage.getItem("dps_admin_auth") === "true";
    if (!isAuth) {
      router.push("/admin/login");
      return;
    }
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-red border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-40 dark:opacity-100">
        <EnergyFlowBackground />
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/admin/dashboard"
            className="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Dashboard
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-brand-red/20 flex items-center justify-center">
            <FileText size={20} className="text-brand-red" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Content Management
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Quick overview of key marketing pages for future editing.
            </p>
          </div>
        </div>

        <div className="grid gap-4">
          {PAGES.map((page) => (
            <div
              key={page.id}
              className="flex items-center justify-between gap-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-5 py-4"
            >
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {page.label}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {page.description}
                </p>
                <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
                  Path: <span className="font-mono">{page.path}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  href={page.path}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-600 px-3 py-1.5 text-[11px] text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <ExternalLink size={12} />
                  View page
                </Link>
                <Link
                  href={page.adminPath}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-brand-red text-white px-3 py-1.5 text-[11px] hover:bg-brand-red/90 transition-colors"
                >
                  Manage page
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

