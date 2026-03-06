"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";
import { getPageConfig, PageConfig } from "@/app/admin/content/pages/page-config";

type ActiveTab = "form" | "preview";

interface ValuesState {
  [key: string]: string;
}

export default function AdminManagePage() {
  const params = useParams();
  const router = useRouter();
  const [authLoading, setAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ActiveTab>("form");
  const [values, setValues] = useState<ValuesState>({});

  const id =
    typeof params.id === "string"
      ? params.id
      : Array.isArray(params.id)
      ? params.id[0]
      : "";

  const pageConfig: PageConfig | undefined = useMemo(
    () => (typeof id === "string" ? getPageConfig(id) : undefined),
    [id]
  );

  useEffect(() => {
    const isAuth = localStorage.getItem("dps_admin_auth") === "true";
    if (!isAuth) {
      router.push("/admin/login");
      return;
    }
    setAuthLoading(false);
  }, [router]);

  useEffect(() => {
    if (!pageConfig) return;
    setValues(
      pageConfig.fields.reduce<ValuesState>((acc, field) => {
        acc[field.id] = field.defaultValue ?? "";
        return acc;
      }, {})
    );
    setActiveTab("form");
  }, [pageConfig]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-red border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!pageConfig) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-40 dark:opacity-100">
          <EnergyFlowBackground />
        </div>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-8">
            <Link
              href="/admin/content/pages"
              className="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
            >
              <ArrowLeft size={20} />
              Back to Content
            </Link>
          </div>
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-5 py-6">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              This page is not yet configured for content management.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleFieldChange = (fieldId: string, value: string) => {
    setValues((prev) => ({
      ...prev,
      [fieldId]: value,
    }));
  };

  const getValue = (fieldId: string) => values[fieldId] ?? "";

  const renderPreview = () => {
    if (pageConfig.id === "home") {
      const heroTitle = getValue("heroTitle") || "Hero title";
      const heroSubtitle =
        getValue("heroSubtitle") ||
        "Short hero description for the homepage.";
      const primaryCta = getValue("heroPrimaryCta") || "Primary CTA";
      const secondaryCta = getValue("heroSecondaryCta") || "Secondary CTA";
       const operationalHeading =
        getValue("operationalSnapshotHeading") ||
        "Operational snapshot heading";
      const servicesHeading =
        getValue("servicesHeading") || "Mechanical, Electrical & Gas";
      const servicesIntro =
        getValue("servicesIntro") ||
        "Three clear paths into how we work with clients.";
      const howWeWorkHeading =
        getValue("howWeWorkHeading") || "Engineered From First Sketch";
      const sectorsHeading =
        getValue("sectorsHeading") || "Sectors We Partner With";
      const aboutBandHeading =
        getValue("aboutBandHeading") || "Disciplined Engineers. Clean Installs.";
      const aboutBandIntro =
        getValue("aboutBandIntro") ||
        "Short overview copy for the About band on the homepage.";

      return (
        <div className="space-y-6">
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-6">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">
              Hero
            </p>
            <div className="h-8 w-40 rounded-full bg-slate-200/70 dark:bg-slate-800/70 mb-4" />
            <p className="text-lg font-semibold text-slate-800 dark:text-slate-50 mb-2">
              {heroTitle}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              {heroSubtitle}
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center rounded-full bg-slate-900 text-white text-xs px-3 py-1.5">
                {primaryCta}
              </span>
              <span className="inline-flex items-center rounded-full border border-slate-300 dark:border-slate-600 text-xs px-3 py-1.5 text-slate-700 dark:text-slate-200">
                {secondaryCta}
              </span>
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-2">
              Operational snapshot
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50 mb-3">
              {operationalHeading}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <div className="h-3 w-4/5 rounded-full bg-slate-200/80 dark:bg-slate-700/80" />
                <div className="h-3 w-2/3 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
              </div>
              <div className="space-y-2">
                <div className="h-3 w-3/4 rounded-full bg-slate-200/80 dark:bg-slate-700/80" />
                <div className="h-3 w-1/2 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Services band
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
              {servicesHeading}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {servicesIntro}
            </p>
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="h-20 rounded-xl bg-slate-200/70 dark:bg-slate-800/70" />
              <div className="h-20 rounded-xl bg-slate-200/70 dark:bg-slate-800/70" />
              <div className="h-20 rounded-xl bg-slate-200/70 dark:bg-slate-800/70" />
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              How we work (scroll sequence)
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
              {howWeWorkHeading}
            </p>
            <div className="h-24 rounded-xl bg-slate-200/70 dark:bg-slate-800/70" />
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Sectors
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
              {sectorsHeading}
            </p>
            <div className="grid grid-cols-3 gap-3">
              {Array.from({ length: 3 }).map((_, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-dashed border-slate-300/70 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-900 px-3 py-3"
                >
                  <div className="h-16 rounded-lg bg-slate-200/70 dark:bg-slate-800/70 mb-2" />
                  <div className="h-3 w-3/4 rounded-full bg-slate-200/80 dark:bg-slate-700/80" />
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              About band
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
              {aboutBandHeading}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {aboutBandIntro}
            </p>
            <div className="h-20 rounded-xl bg-slate-200/70 dark:bg-slate-800/70" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-dashed border-slate-300/70 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-900 px-3 py-4"
              >
                <div className="h-16 rounded-lg bg-slate-200/70 dark:bg-slate-800/70 mb-3" />
                <div className="h-3 w-3/4 rounded-full bg-slate-200/80 dark:bg-slate-700/80 mb-1.5" />
                <div className="h-3 w-1/2 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (pageConfig.id === "about") {
      const heading = getValue("aboutHeading") || "About heading";
      const intro =
        getValue("aboutIntro") ||
        "Intro copy for the About page goes here.";
      const missionHeading =
        getValue("aboutMissionHeading") || "Our Mission";
      const missionBody =
        getValue("aboutMissionBody") ||
        "Explain what drives the company and how projects are treated as engineered infrastructure.";
      const visionHeading = getValue("aboutVisionHeading") || "Our Vision";
      const visionBody =
        getValue("aboutVisionBody") ||
        "Describe where the company is heading and how clients should experience working with DPS.";
      const statsHeading =
        getValue("aboutStatsHeading") || "Numbers that back the work";

      return (
        <div className="space-y-5">
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-6">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">
              Top section
            </p>
            <p className="text-lg font-semibold text-slate-800 dark:text-slate-50 mb-2">
              {heading}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              {intro}
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-24 rounded-lg bg-slate-200/70 dark:bg-slate-800/70" />
              <div className="space-y-2">
                <div className="h-3 w-5/6 rounded-full bg-slate-200/80 dark:bg-slate-700/80" />
                <div className="h-3 w-4/5 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
                <div className="h-3 w-2/3 rounded-full bg-slate-200/60 dark:bg-slate-800/60" />
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-6 space-y-4">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Mission & vision
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-50 mb-1.5">
                  {missionHeading}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {missionBody}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-50 mb-1.5">
                  {visionHeading}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {visionBody}
                </p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Stats / credentials band
            </p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-50">
              {statsHeading}
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-dashed border-slate-300/70 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-900 px-3 py-3 space-y-2"
                >
                  <div className="h-6 w-6 rounded-full bg-slate-200/80 dark:bg-slate-800/80" />
                  <div className="h-3 w-3/4 rounded-full bg-slate-200/80 dark:bg-slate-700/80" />
                  <div className="h-3 w-1/2 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (pageConfig.id === "portfolio") {
      const heading = getValue("portfolioHeading") || "Portfolio heading";
      const intro =
        getValue("portfolioIntro") ||
        "Intro copy for the portfolio or projects page.";
      const featuredTitle =
        getValue("portfolioFeaturedTitle") || "Featured project heading";
      const featuredSummary =
        getValue("portfolioFeaturedSummary") ||
        "Short summary of a flagship installation or contract.";
      const gridHeading =
        getValue("portfolioGridHeading") || "Recent work";

      return (
        <div className="space-y-5">
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-6">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">
              Header
            </p>
            <p className="text-lg font-semibold text-slate-800 dark:text-slate-50 mb-2">
              {heading}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              {intro}
            </p>
          </div>
          <div className="rounded-2xl border border-dashed border-slate-300/80 dark:border-slate-600/80 bg-slate-50 dark:bg-slate-900 px-5 py-5 space-y-3">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Featured project
            </p>
            <div className="grid grid-cols-1 md:grid-cols-[1.4fr_1fr] gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-50 mb-1.5">
                  {featuredTitle}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                  {featuredSummary}
                </p>
                <div className="h-8 w-28 rounded-full bg-slate-200/80 dark:bg-slate-800/80" />
              </div>
              <div className="h-28 rounded-xl bg-slate-200/80 dark:bg-slate-800/80" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="col-span-full flex items-center justify-between mb-1 px-0.5">
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                Projects grid
              </p>
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                {gridHeading}
              </p>
            </div>
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-dashed border-slate-300/70 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-900 px-3 py-3"
              >
                <div className="h-16 rounded-lg bg-slate-200/70 dark:bg-slate-800/70 mb-2" />
                <div className="h-3 w-3/4 rounded-full bg-slate-200/80 dark:bg-slate-700/80 mb-1.5" />
                <div className="h-3 w-2/3 rounded-full bg-slate-200/70 dark:bg-slate-800/70" />
              </div>
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-40 dark:opacity-100">
        <EnergyFlowBackground />
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/admin/content/pages"
            className="flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Content
          </Link>
        </div>

        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-red/20 flex items-center justify-center">
              <FileText size={20} className="text-brand-red" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Manage {pageConfig.label}
              </h1>
              {pageConfig.description && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {pageConfig.description}
                </p>
              )}
            </div>
          </div>

          <p className="hidden sm:block text-[11px] text-slate-400 dark:text-slate-500">
            Values here are not yet saved anywhere – UI only.
          </p>
        </div>

        <div className="mb-5 inline-flex rounded-xl border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 p-1 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("form")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              activeTab === "form"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "text-slate-600 dark:text-slate-300"
            }`}
          >
            Form
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("preview")}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              activeTab === "preview"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "text-slate-600 dark:text-slate-300"
            }`}
          >
            Preview
          </button>
        </div>

        {activeTab === "form" ? (
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-5 py-6 space-y-5">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Adjust the labels and copy for this page. These values are held
              only in this screen for now.
            </p>
            <div className="space-y-4">
              {pageConfig.fields.map((field) => (
                <label key={field.id} className="block space-y-1.5">
                  <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                    {field.label}
                  </span>
                  {field.description && (
                    <span className="block text-[11px] text-slate-400 dark:text-slate-500">
                      {field.description}
                    </span>
                  )}
                  {field.type === "textarea" ? (
                    <textarea
                      value={getValue(field.id)}
                      onChange={(e) =>
                        handleFieldChange(field.id, e.target.value)
                      }
                      placeholder={field.placeholder}
                      rows={field.multiline ? 3 : 2}
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                    />
                  ) : (
                    <input
                      type="text"
                      value={getValue(field.id)}
                      onChange={(e) =>
                        handleFieldChange(field.id, e.target.value)
                      }
                      placeholder={field.placeholder}
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                    />
                  )}
                </label>
              ))}
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-dashed border-slate-200 dark:border-slate-700">
              <p className="text-[11px] text-slate-400 dark:text-slate-500">
                Saving will be wired to real content later – no changes are
                persisted yet.
              </p>
              <button
                type="button"
                disabled
                className="inline-flex items-center gap-2 rounded-xl bg-slate-200/70 dark:bg-slate-800/70 text-slate-500 dark:text-slate-400 px-4 py-1.5 text-xs cursor-not-allowed"
              >
                Save (coming soon)
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-5 py-6">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Lightweight wireframe of the page layout using the content from
              the form tab.
            </p>
            {renderPreview()}
          </div>
        )}
      </div>
    </div>
  );
}

