"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Settings } from "lucide-react";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

interface SiteConfigForm {
  name: string;
  legalName: string;
  phone: string;
  email: string;
  address: string;
  gasSafeNumber: string;
  areas: string;
  liabilityInsurance: boolean;
  indemnityInsurance: boolean;
  founded: string;
  founder: string;
  industryExperience: string;
  mission: string;
  vision: string;
  openingHoursWeekday: string;
  openingHoursSaturday: string;
  openingHoursSunday: string;
  defaultMetaTitle: string;
  defaultMetaDescription: string;
}

const emptyForm: SiteConfigForm = {
  name: "",
  legalName: "",
  phone: "",
  email: "",
  address: "",
  gasSafeNumber: "",
  areas: "",
  liabilityInsurance: true,
  indemnityInsurance: true,
  founded: "",
  founder: "",
  industryExperience: "",
  mission: "",
  vision: "",
  openingHoursWeekday: "",
  openingHoursSaturday: "",
  openingHoursSunday: "",
  defaultMetaTitle: "",
  defaultMetaDescription: "",
};

export default function AdminSiteConfigPage() {
  const router = useRouter();
  const [form, setForm] = useState<SiteConfigForm>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    const isAuth = localStorage.getItem("dps_admin_auth") === "true";
    if (!isAuth) {
      router.push("/admin/login");
      return;
    }
    fetch("/api/admin/site", { credentials: "include" })
      .then((res) => {
        if (res.status === 401) {
          router.push("/admin/login");
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (data) {
          setForm({
            name: data.name ?? "",
            legalName: data.legalName ?? "",
            phone: data.phone ?? "",
            email: data.email ?? "",
            address: data.address ?? "",
            gasSafeNumber: data.gasSafeNumber ?? "",
            areas: data.areas ?? "",
            liabilityInsurance: Boolean(data.liabilityInsurance),
            indemnityInsurance: Boolean(data.indemnityInsurance),
            founded: data.founded ?? "",
            founder: data.founder ?? "",
            industryExperience: data.industryExperience ?? "",
            mission: data.mission ?? "",
            vision: data.vision ?? "",
            openingHoursWeekday: data.openingHoursWeekday ?? "",
            openingHoursSaturday: data.openingHoursSaturday ?? "",
            openingHoursSunday: data.openingHoursSunday ?? "",
            defaultMetaTitle: data.defaultMetaTitle ?? "",
            defaultMetaDescription: data.defaultMetaDescription ?? "",
          });
        }
      })
      .catch(() => setMessage({ type: "error", text: "Failed to load config" }))
      .finally(() => setLoading(false));
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch("/api/admin/site", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setMessage({ type: "success", text: "Site config saved." });
      } else {
        setMessage({ type: "error", text: data.error ?? "Failed to save" });
      }
    } catch {
      setMessage({ type: "error", text: "Failed to save" });
    } finally {
      setSaving(false);
    }
  };

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

      <div className="max-w-3xl mx-auto px-4 py-8">
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
            <Settings size={20} className="text-brand-red" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Site Config</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Company info, opening hours, mission & vision</p>
          </div>
        </div>

        {message && (
          <div
            className={`mb-6 px-4 py-3 rounded-xl text-sm ${
              message.type === "success"
                ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
                : "bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/20"
            }`}
          >
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <fieldset className="space-y-4 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
            <legend className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Company
            </legend>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Company name</span>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Legal name</span>
                <input
                  type="text"
                  value={form.legalName}
                  onChange={(e) => setForm((f) => ({ ...f, legalName: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Phone</span>
                <input
                  type="text"
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Email</span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
            </div>
            <label className="block">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Address</span>
              <input
                type="text"
                value={form.address}
                onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Gas Safe number</span>
                <input
                  type="text"
                  value={form.gasSafeNumber}
                  onChange={(e) => setForm((f) => ({ ...f, gasSafeNumber: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Areas (e.g. London, Kent)</span>
                <input
                  type="text"
                  value={form.areas}
                  onChange={(e) => setForm((f) => ({ ...f, areas: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Founded</span>
                <input
                  type="text"
                  value={form.founded}
                  onChange={(e) => setForm((f) => ({ ...f, founded: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Founder</span>
                <input
                  type="text"
                  value={form.founder}
                  onChange={(e) => setForm((f) => ({ ...f, founder: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Industry experience</span>
                <input
                  type="text"
                  value={form.industryExperience}
                  onChange={(e) => setForm((f) => ({ ...f, industryExperience: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
            </div>
            <label className="block">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Mission</span>
              <textarea
                value={form.mission}
                onChange={(e) => setForm((f) => ({ ...f, mission: e.target.value }))}
                rows={2}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Vision</span>
              <textarea
                value={form.vision}
                onChange={(e) => setForm((f) => ({ ...f, vision: e.target.value }))}
                rows={2}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
              />
            </label>
          </fieldset>

          <fieldset className="space-y-4 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
            <legend className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Opening hours
            </legend>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Weekday</span>
                <input
                  type="text"
                  value={form.openingHoursWeekday}
                  onChange={(e) => setForm((f) => ({ ...f, openingHoursWeekday: e.target.value }))}
                  placeholder="08:00 - 18:00"
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Saturday</span>
                <input
                  type="text"
                  value={form.openingHoursSaturday}
                  onChange={(e) => setForm((f) => ({ ...f, openingHoursSaturday: e.target.value }))}
                  placeholder="09:00 - 13:00"
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Sunday</span>
                <input
                  type="text"
                  value={form.openingHoursSunday}
                  onChange={(e) => setForm((f) => ({ ...f, openingHoursSunday: e.target.value }))}
                  placeholder="Closed"
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
                />
              </label>
            </div>
          </fieldset>

          <div className="flex justify-end gap-3">
            <Link
              href="/admin/dashboard"
              className="px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-red text-white text-sm font-medium hover:bg-brand-red/90 disabled:opacity-50 transition-colors"
            >
              {saving ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Save size={16} />
              )}
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
