"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Briefcase,
  GripVertical,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Save,
  X,
} from "lucide-react";
import EnergyFlowBackground from "@/components/animations/EnergyFlowBackground";

interface PortfolioProject {
  id: string;
  title: string;
  category: string;
  location: string;
  description: string;
  images: string[];
  stats: { label: string; value: string }[];
  sortOrder: number;
  published: boolean;
}

interface Review {
  id: string;
  name: string;
  service: string;
  rating: number;
  quote: string;
  image?: string;
  sortOrder: number;
  published: boolean;
}

const PROJECT_CATEGORIES = ["gas", "mechanical", "electrical", "plumbing"] as const;

function fetchWithAuth(url: string, options?: RequestInit) {
  return fetch(url, { ...options, credentials: "include" });
}

export default function AdminPortfolioPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<PortfolioProject[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [expandedProject, setExpandedProject] = useState<string | "new" | null>(null);
  const [expandedReview, setExpandedReview] = useState<string | "new" | null>(null);
  const [draggedProjectId, setDraggedProjectId] = useState<string | null>(null);
  const [draggedReviewId, setDraggedReviewId] = useState<string | null>(null);

  const persistProjectOrder = useCallback(async (reordered: PortfolioProject[]) => {
    await Promise.all(
      reordered.map((p, i) =>
        fetchWithAuth(`/api/admin/portfolio/${p.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sortOrder: i }),
        })
      )
    );
  }, []);

  const persistReviewOrder = useCallback(async (reordered: Review[]) => {
    await Promise.all(
      reordered.map((r, i) =>
        fetchWithAuth(`/api/admin/reviews/${r.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sortOrder: i }),
        })
      )
    );
  }, []);

  const loadData = useCallback(async () => {
    const [projRes, revRes] = await Promise.all([
      fetchWithAuth("/api/admin/portfolio"),
      fetchWithAuth("/api/admin/reviews"),
    ]);
    if (projRes.status === 401 || revRes.status === 401) {
      router.push("/admin/login");
      return;
    }
    const projData = await projRes.json();
    const revData = await revRes.json();
    if (Array.isArray(projData)) setProjects(projData);
    else setProjects([]);
    if (Array.isArray(revData)) setReviews(revData);
    else setReviews([]);
  }, [router]);

  useEffect(() => {
    const isAuth = localStorage.getItem("dps_admin_auth") === "true";
    if (!isAuth) {
      router.push("/admin/login");
      return;
    }
    loadData().finally(() => setLoading(false));
  }, [router, loadData]);

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
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

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-brand-red/20 flex items-center justify-center">
            <Briefcase size={20} className="text-brand-red" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Portfolio</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Completed projects and customer reviews for the portfolio page.
            </p>
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

        {/* Completed Projects Section */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">
              Works
              <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-400">
                (drag to reorder)
              </span>
            </h2>
            <button
              onClick={() => setExpandedProject(expandedProject === "new" ? null : "new")}
              className="inline-flex items-center gap-2 rounded-xl border border-brand-red bg-brand-red/10 text-brand-red px-3 py-1.5 text-sm font-medium hover:bg-brand-red/20 transition-colors"
            >
              <Plus size={16} />
              Add work
            </button>
          </div>

          {expandedProject === "new" && (
            <ProjectForm
              onSave={async (data) => {
                const res = await fetchWithAuth("/api/admin/portfolio", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(data),
                });
                const json = await res.json();
                if (res.ok) {
                  setProjects((p) => [...p, json]);
                  setExpandedProject(null);
                  showMessage("success", "Project added.");
                  return null;
                } else {
                  showMessage("error", json.error ?? "Failed to add project.");
                  return json.error ?? "Failed to add project.";
                }
              }}
              onCancel={() => setExpandedProject(null)}
            />
          )}

          <div className="space-y-3">
            {projects.map((project) => (
              <div
                key={project.id}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = "move";
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  const fromId = e.dataTransfer.getData("text/plain");
                  const toId = project.id;
                  if (!fromId || fromId === toId) return;
                  const fromIdx = projects.findIndex((p) => p.id === fromId);
                  const toIdx = projects.findIndex((p) => p.id === toId);
                  if (fromIdx === -1 || toIdx === -1) return;
                  const next = [...projects];
                  const [removed] = next.splice(fromIdx, 1);
                  next.splice(toIdx, 0, removed);
                  setProjects(next);
                  persistProjectOrder(next).then(
                    () => showMessage("success", "Order updated."),
                    () => showMessage("error", "Failed to save order.")
                  );
                }}
                className={`flex gap-2 items-stretch transition-opacity ${
                  draggedProjectId === project.id ? "opacity-50" : ""
                }`}
              >
                <div
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/plain", project.id);
                    e.dataTransfer.effectAllowed = "move";
                    setDraggedProjectId(project.id);
                  }}
                  onDragEnd={() => setDraggedProjectId(null)}
                  className="flex cursor-grab active:cursor-grabbing items-center pl-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 shrink-0 touch-none"
                  title="Drag to reorder"
                >
                  <GripVertical size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <ProjectCard
                    project={project}
                    expanded={expandedProject === project.id}
                    onToggle={() =>
                      setExpandedProject(expandedProject === project.id ? null : project.id)
                    }
                    onSave={async (data) => {
                      const res = await fetchWithAuth(`/api/admin/portfolio/${project.id}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data),
                      });
                      const json = await res.json();
                      if (res.ok) {
                        setProjects((p) => p.map((x) => (x.id === project.id ? json : x)));
                        setExpandedProject(null);
                        showMessage("success", "Project updated.");
                        return null;
                      } else {
                        showMessage("error", json.error ?? "Failed to update.");
                        return json.error ?? "Failed to update.";
                      }
                    }}
                    onDelete={async () => {
                      if (!confirm("Delete this project?")) return;
                      const res = await fetchWithAuth(`/api/admin/portfolio/${project.id}`, {
                        method: "DELETE",
                      });
                      if (res.ok) {
                        setProjects((p) => p.filter((x) => x.id !== project.id));
                        setExpandedProject(null);
                        showMessage("success", "Project deleted.");
                      } else {
                        showMessage("error", "Failed to delete.");
                      }
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {projects.length === 0 && expandedProject !== "new" && (
            <p className="text-sm text-slate-500 dark:text-slate-400 py-6 text-center rounded-xl border border-dashed border-slate-300 dark:border-slate-600">
              No works yet. Click &quot;Add work&quot; to add one.
            </p>
          )}
        </section>

        {/* Reviews Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">
              Reviews
              <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-400">
                (drag to reorder)
              </span>
            </h2>
            <button
              onClick={() => setExpandedReview(expandedReview === "new" ? null : "new")}
              className="inline-flex items-center gap-2 rounded-xl border border-brand-red bg-brand-red/10 text-brand-red px-3 py-1.5 text-sm font-medium hover:bg-brand-red/20 transition-colors"
            >
              <Plus size={16} />
              Add review
            </button>
          </div>

          {expandedReview === "new" && (
            <ReviewForm
              onSave={async (data) => {
                const res = await fetchWithAuth("/api/admin/reviews", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(data),
                });
                const json = await res.json();
                if (res.ok) {
                  setReviews((r) => [...r, json]);
                  setExpandedReview(null);
                  showMessage("success", "Review added.");
                } else {
                  showMessage("error", json.error ?? "Failed to add review.");
                }
              }}
              onCancel={() => setExpandedReview(null)}
            />
          )}

          <div className="space-y-3">
            {reviews.map((review) => (
              <div
                key={review.id}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = "move";
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  const fromId = e.dataTransfer.getData("text/plain");
                  const toId = review.id;
                  if (!fromId || fromId === toId) return;
                  const fromIdx = reviews.findIndex((r) => r.id === fromId);
                  const toIdx = reviews.findIndex((r) => r.id === toId);
                  if (fromIdx === -1 || toIdx === -1) return;
                  const next = [...reviews];
                  const [removed] = next.splice(fromIdx, 1);
                  next.splice(toIdx, 0, removed);
                  setReviews(next);
                  persistReviewOrder(next).then(
                    () => showMessage("success", "Order updated."),
                    () => showMessage("error", "Failed to save order.")
                  );
                }}
                className={`flex gap-2 items-stretch transition-opacity ${
                  draggedReviewId === review.id ? "opacity-50" : ""
                }`}
              >
                <div
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/plain", review.id);
                    e.dataTransfer.effectAllowed = "move";
                    setDraggedReviewId(review.id);
                  }}
                  onDragEnd={() => setDraggedReviewId(null)}
                  className="flex cursor-grab active:cursor-grabbing items-center pl-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 shrink-0 touch-none"
                  title="Drag to reorder"
                >
                  <GripVertical size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <ReviewCard
                    review={review}
                    expanded={expandedReview === review.id}
                    onToggle={() =>
                      setExpandedReview(expandedReview === review.id ? null : review.id)
                    }
                    onSave={async (data) => {
                      const res = await fetchWithAuth(`/api/admin/reviews/${review.id}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data),
                      });
                      const json = await res.json();
                      if (res.ok) {
                        setReviews((r) => r.map((x) => (x.id === review.id ? json : x)));
                        setExpandedReview(null);
                        showMessage("success", "Review updated.");
                      } else {
                        showMessage("error", json.error ?? "Failed to update.");
                      }
                    }}
                    onDelete={async () => {
                      if (!confirm("Delete this review?")) return;
                      const res = await fetchWithAuth(`/api/admin/reviews/${review.id}`, {
                        method: "DELETE",
                      });
                      if (res.ok) {
                        setReviews((r) => r.filter((x) => x.id !== review.id));
                        setExpandedReview(null);
                        showMessage("success", "Review deleted.");
                      } else {
                        showMessage("error", "Failed to delete.");
                      }
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {reviews.length === 0 && expandedReview !== "new" && (
            <p className="text-sm text-slate-500 dark:text-slate-400 py-6 text-center rounded-xl border border-dashed border-slate-300 dark:border-slate-600">
              No reviews yet. Click &quot;Add review&quot; to add one.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}

/* ── Project form & card ──────────────────────────────────────────────────── */

interface ProjectFormProps {
  initial?: PortfolioProject | null;
  onSave: (data: Partial<PortfolioProject>) => Promise<string | null>;
  onCancel: () => void;
}

function ProjectForm({ initial, onSave, onCancel }: ProjectFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [category, setCategory] = useState(initial?.category ?? "gas");
  const [location, setLocation] = useState(initial?.location ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [images, setImages] = useState<string[]>(
    initial?.images?.length ? initial.images : []
  );
  const [stats, setStats] = useState<{ label: string; value: string }[]>(
    initial?.stats?.length ? initial.stats.slice(0, 4) : [{ label: "", value: "" }]
  );
  const [published, setPublished] = useState(initial?.published ?? true);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleImageUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const picked = Array.from(files);
    const overSize = picked.find((f) => f.size > 10 * 1024 * 1024);
    if (overSize) {
      alert(`"${overSize.name}" is larger than 10MB.`);
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      for (const file of picked) formData.append("files", file);
      const res = await fetchWithAuth("/api/admin/portfolio/upload", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Upload failed");
      setImages((prev) => [...prev, ...(Array.isArray(json.urls) ? json.urls : [])]);
    } catch (error) {
      alert(String(error));
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    if (images.length === 0) {
      alert("Please upload at least one image.");
      return;
    }
    setSaving(true);
    const error = await onSave({
      title,
      category,
      location,
      description,
      images,
      stats: stats
        .map((s) => ({ label: s.label.trim(), value: s.value.trim() }))
        .filter((s) => s.label || s.value),
      published,
    });
    if (error) setSubmitError(error);
    setSaving(false);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-4 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-4"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs font-medium text-slate-500 block mb-1">Title</span>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-slate-500 block mb-1">Category</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
          >
            {PROJECT_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="block">
        <span className="text-xs font-medium text-slate-500 block mb-1">Location</span>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          required
          className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
        />
      </label>
      <label className="block">
        <span className="text-xs font-medium text-slate-500 block mb-1">Description</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={4}
          className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
        />
      </label>
      <div>
        <div className="flex items-center justify-between mb-2 gap-3">
          <span className="text-xs font-medium text-slate-500">
            Images (max file size 10MB each, compressed before storing)
          </span>
          <label className="inline-flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-600 px-3 py-1.5 text-xs cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
            {uploading ? "Uploading..." : "Upload images"}
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp,image/heic,image/heif"
              multiple
              className="hidden"
              onChange={(e) => handleImageUpload(e.target.files)}
              disabled={uploading}
            />
          </label>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {images.map((img) => (
            <div key={img} className="relative rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={img} alt="" className="h-24 w-full object-cover" />
              <button
                type="button"
                onClick={() => setImages((prev) => prev.filter((x) => x !== img))}
                className="absolute top-1 right-1 rounded-full bg-black/70 text-white p-1"
                title="Remove image"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500">Stats (max 4)</span>
          <button
            type="button"
            onClick={() => {
              if (stats.length >= 4) return;
              setStats((prev) => [...prev, { label: "", value: "" }]);
            }}
            className="text-xs text-brand-red hover:underline disabled:opacity-50"
            disabled={stats.length >= 4}
          >
            + Add stat
          </button>
        </div>
        <div className="space-y-2">
          {stats.map((stat, idx) => (
            <div key={idx} className="grid grid-cols-[1fr_1fr_auto] gap-2">
              <input
                type="text"
                value={stat.label}
                onChange={(e) =>
                  setStats((prev) =>
                    prev.map((s, i) => (i === idx ? { ...s, label: e.target.value } : s))
                  )
                }
                placeholder="Label"
                className="rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm"
              />
              <input
                type="text"
                value={stat.value}
                onChange={(e) =>
                  setStats((prev) =>
                    prev.map((s, i) => (i === idx ? { ...s, value: e.target.value } : s))
                  )
                }
                placeholder="Value"
                className="rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={() =>
                  setStats((prev) =>
                    prev.length === 1 ? [{ label: "", value: "" }] : prev.filter((_, i) => i !== idx)
                  )
                }
                className="px-2 text-slate-400 hover:text-red-500"
                title="Remove stat"
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={published}
          onChange={(e) => setPublished(e.target.checked)}
        />
        <span className="text-sm text-slate-600 dark:text-slate-400">Published</span>
      </label>
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-600 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-red text-white text-sm disabled:opacity-50"
        >
          {saving ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Save size={16} />
          )}
          Save
        </button>
        {submitError && (
          <p className="self-center text-xs text-red-600 dark:text-red-400">
            {submitError}
          </p>
        )}
      </div>
    </form>
  );
}

function ProjectCard({
  project,
  expanded,
  onToggle,
  onSave,
  onDelete,
}: {
  project: PortfolioProject;
  expanded: boolean;
  onToggle: () => void;
  onSave: (data: Partial<PortfolioProject>) => Promise<string | null>;
  onDelete: () => Promise<void>;
}) {
  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div>
          <p className="font-medium text-slate-900 dark:text-slate-100">{project.title}</p>
          <p className="text-xs text-slate-500">
            {project.category} · {project.location} · {project.images?.length ?? 0} images
            {!project.published && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">(unpublished)</span>
            )}
          </p>
        </div>
        {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-5">
          <ProjectForm initial={project} onSave={onSave} onCancel={onToggle} />
          <button
            type="button"
            onClick={onDelete}
            className="mt-2 flex items-center gap-1.5 text-sm text-red-500 hover:text-red-600"
          >
            <Trash2 size={14} />
            Delete project
          </button>
        </div>
      )}
    </div>
  );
}

/* ── Review form & card ───────────────────────────────────────────────────── */

interface ReviewFormProps {
  initial?: Review | null;
  onSave: (data: Partial<Review>) => Promise<void>;
  onCancel: () => void;
}

function ReviewForm({ initial, onSave, onCancel }: ReviewFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [service, setService] = useState(initial?.service ?? "");
  const [rating, setRating] = useState(String(initial?.rating ?? 5));
  const [quote, setQuote] = useState(initial?.quote ?? "");
  const [published, setPublished] = useState(initial?.published ?? true);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave({
      name,
      service,
      rating: Math.min(5, Math.max(1, Number(rating) || 5)),
      quote,
      published,
    });
    setSaving(false);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-4 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-4"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs font-medium text-slate-500 block mb-1">Name</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-slate-500 block mb-1">Service / location</span>
          <input
            type="text"
            value={service}
            onChange={(e) => setService(e.target.value)}
            required
            placeholder="e.g. Boiler repair · Shadwell, London"
            className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
          />
        </label>
      </div>
      <label className="block">
        <span className="text-xs font-medium text-slate-500 block mb-1">Rating (1–5)</span>
        <select
          value={rating}
          onChange={(e) => setRating(e.target.value)}
          className="w-24 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="text-xs font-medium text-slate-500 block mb-1">Quote</span>
        <textarea
          value={quote}
          onChange={(e) => setQuote(e.target.value)}
          required
          rows={4}
          className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm"
        />
      </label>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={published}
          onChange={(e) => setPublished(e.target.checked)}
        />
        <span className="text-sm text-slate-600 dark:text-slate-400">Published</span>
      </label>
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-600 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-red text-white text-sm disabled:opacity-50"
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
  );
}

function ReviewCard({
  review,
  expanded,
  onToggle,
  onSave,
  onDelete,
}: {
  review: Review;
  expanded: boolean;
  onToggle: () => void;
  onSave: (data: Partial<Review>) => Promise<void>;
  onDelete: () => Promise<void>;
}) {
  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div>
          <p className="font-medium text-slate-900 dark:text-slate-100">{review.name}</p>
          <p className="text-xs text-slate-500">
            {review.service}
            {!review.published && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">(unpublished)</span>
            )}
          </p>
          <p className="text-xs text-slate-400 mt-1 line-clamp-1">&ldquo;{review.quote}&rdquo;</p>
        </div>
        {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-5">
          <ReviewForm initial={review} onSave={onSave} onCancel={onToggle} />
          <button
            type="button"
            onClick={onDelete}
            className="mt-2 flex items-center gap-1.5 text-sm text-red-500 hover:text-red-600"
          >
            <Trash2 size={14} />
            Delete review
          </button>
        </div>
      )}
    </div>
  );
}
