import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type RecommendationOut = {
  id: string;
  recommendation_type: string;
  category: string;
  severity: string;
  confidence: string;
  title: string;
  summary: string;
  entity_type: string;
  entity_id: string;
  status: string;
  recommendation_key: string;
  created_at: string;
  updated_at: string;
  suppressed_until?: string | null;
};

type RecommendationSummaryOut = {
  open_by_severity: Record<string, number>;
  open_by_category: Record<string, number>;
  stale_acknowledged_count: number;
};

type DashboardActionsSummaryOut = {
  open_recommendations: number;
  recommendations_with_available_actions: number;
  pending_confirmations: number;
  recently_rejected: number;
  recently_executed_success: number;
  failed_executions: number;
  action_decisions_last_7d_by_type: Record<string, number>;
  window_start: string;
};

type ApprovalsDashboardSummaryOut = {
  pending_total: number;
  pending_by_type: Record<string, number>;
  overdue_pending_count: number;
  assigned_to_me_pending: number;
  recently_decided: number;
  overdue_hours_threshold: number;
};

type RecommendationSuppressionOut = {
  id: string;
  recommendation_key: string | null;
  category: string | null;
  contract_id: string | null;
  site_id: string | null;
  suppressed_until: string;
  notes: string | null;
  created_by_user_id: string | null;
  created_at: string;
};

async function fetchJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(url: string, headers: Record<string, string>, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
  return res.json() as Promise<T>;
}

async function deleteReq(url: string, headers: Record<string, string>): Promise<void> {
  const res = await fetch(url, { method: "DELETE", headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
}

export function OpsHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [summary, setSummary] = useState<RecommendationSummaryOut | null>(null);
  const [actionsSummary, setActionsSummary] = useState<DashboardActionsSummaryOut | null>(null);
  const [approvalsSummary, setApprovalsSummary] = useState<ApprovalsDashboardSummaryOut | null>(null);
  const [summaryErr, setSummaryErr] = useState<string | null>(null);

  const [recsBusy, setRecsBusy] = useState(false);
  const [recommendations, setRecommendations] = useState<RecommendationOut[]>([]);
  const [recsErr, setRecsErr] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [includeSuppressed, setIncludeSuppressed] = useState(false);

  const [selectedRecId, setSelectedRecId] = useState("");
  const selectedRec = useMemo(
    () => (selectedRecId ? recommendations.find((r) => r.id === selectedRecId) ?? null : null),
    [recommendations, selectedRecId],
  );

  const [actionNotes, setActionNotes] = useState("");
  const [snoozeHours, setSnoozeHours] = useState("24");

  const [suppressions, setSuppressions] = useState<RecommendationSuppressionOut[]>([]);
  const [suppressionsBusy, setSuppressionsBusy] = useState(false);
  const [suppressionsErr, setSuppressionsErr] = useState<string | null>(null);
  const [suppressionForm, setSuppressionForm] = useState({
    recommendation_key: "",
    category: "",
    contract_id: "",
    site_id: "",
    hours: "24",
    notes: "",
  });

  useEffect(() => {
    if (!banner && !bannerErr) return;
    const t = window.setTimeout(() => {
      setBanner(null);
      setBannerErr(null);
    }, 4000);
    return () => window.clearTimeout(t);
  }, [banner, bannerErr]);

  const loadSummaries = useCallback(async () => {
    setSummaryErr(null);
    try {
      const [a, b, c] = await Promise.all([
        fetchJson<RecommendationSummaryOut>(`${apiBase}/ops/dashboard/recommendations/summary`, authHeaders),
        fetchJson<DashboardActionsSummaryOut>(`${apiBase}/ops/dashboard/actions/summary`, authHeaders),
        fetchJson<ApprovalsDashboardSummaryOut>(`${apiBase}/ops/dashboard/pending-approvals`, authHeaders),
      ]);
      setSummary(a);
      setActionsSummary(b);
      setApprovalsSummary(c);
    } catch (e) {
      setSummary(null);
      setActionsSummary(null);
      setApprovalsSummary(null);
      setSummaryErr(e instanceof Error ? e.message : String(e));
    }
  }, [apiBase, authHeaders]);

  const loadRecommendations = useCallback(async () => {
    setRecsBusy(true);
    setRecsErr(null);
    try {
      const q = new URLSearchParams();
      if (statusFilter.trim()) q.set("status", statusFilter.trim());
      if (categoryFilter.trim()) q.set("category", categoryFilter.trim());
      if (severityFilter.trim()) q.set("severity", severityFilter.trim());
      q.set("include_suppressed", includeSuppressed ? "true" : "false");
      q.set("limit", "100");
      q.set("offset", "0");
      const rows = await fetchJson<RecommendationOut[]>(`${apiBase}/ops/recommendations?${q.toString()}`, authHeaders);
      setRecommendations(rows);
      if (!selectedRecId && rows[0]?.id) setSelectedRecId(rows[0].id);
    } catch (e) {
      setRecommendations([]);
      setRecsErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRecsBusy(false);
    }
  }, [apiBase, authHeaders, categoryFilter, includeSuppressed, selectedRecId, severityFilter, statusFilter]);

  const loadSuppressions = useCallback(async () => {
    setSuppressionsBusy(true);
    setSuppressionsErr(null);
    try {
      const rows = await fetchJson<RecommendationSuppressionOut[]>(
        `${apiBase}/ops/recommendations/suppressions?active_only=true`,
        authHeaders,
      );
      setSuppressions(rows);
    } catch (e) {
      setSuppressions([]);
      setSuppressionsErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSuppressionsBusy(false);
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    void loadSummaries();
    void loadRecommendations();
    void loadSuppressions();
  }, [loadRecommendations, loadSummaries, loadSuppressions]);

  const runScan = useCallback(async () => {
    setBusy(true);
    setBanner(null);
    setBannerErr(null);
    try {
      await postJson<{ keys_active: number; auto_resolved: number }>(`${apiBase}/ops/recommendations/run-scan`, authHeaders, {});
      setBanner("Recommendation scan completed.");
      await loadSummaries();
      await loadRecommendations();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadRecommendations, loadSummaries]);

  const actOnRecommendation = useCallback(
    async (action: "acknowledge" | "resolve" | "dismiss" | "reopen") => {
      if (!selectedRec) return;
      setBusy(true);
      setBanner(null);
      setBannerErr(null);
      try {
        await postJson<RecommendationOut>(
          `${apiBase}/ops/recommendations/${encodeURIComponent(selectedRec.id)}/${action}`,
          authHeaders,
          { notes: actionNotes.trim() || null },
        );
        setBanner(`Recommendation ${action}d.`);
        await loadSummaries();
        await loadRecommendations();
      } catch (e) {
        setBannerErr(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [actionNotes, apiBase, authHeaders, loadRecommendations, loadSummaries, selectedRec],
  );

  const snoozeRecommendation = useCallback(async () => {
    if (!selectedRec) return;
    const hrs = Number(snoozeHours);
    if (!Number.isFinite(hrs) || hrs <= 0) {
      setBannerErr("Snooze hours must be greater than 0.");
      return;
    }
    setBusy(true);
    setBanner(null);
    setBannerErr(null);
    try {
      await postJson<RecommendationOut>(
        `${apiBase}/ops/recommendations/${encodeURIComponent(selectedRec.id)}/snooze`,
        authHeaders,
        { hours: hrs, notes: actionNotes.trim() || null },
      );
      setBanner("Recommendation snoozed.");
      await loadRecommendations();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadRecommendations, selectedRec, snoozeHours, actionNotes]);

  const createSuppression = useCallback(async () => {
    const hasKeyOrCategory = suppressionForm.recommendation_key.trim() || suppressionForm.category.trim();
    if (!hasKeyOrCategory) {
      setBannerErr("Set recommendation_key or category for suppression.");
      return;
    }
    const hours = Number(suppressionForm.hours);
    if (!Number.isFinite(hours) || hours <= 0) {
      setBannerErr("Suppression hours must be greater than 0.");
      return;
    }

    setBusy(true);
    setBanner(null);
    setBannerErr(null);
    try {
      await postJson<RecommendationSuppressionOut>(`${apiBase}/ops/recommendations/suppressions`, authHeaders, {
        recommendation_key: suppressionForm.recommendation_key.trim() || null,
        category: suppressionForm.category.trim() || null,
        contract_id: suppressionForm.contract_id.trim() || null,
        site_id: suppressionForm.site_id.trim() || null,
        hours,
        notes: suppressionForm.notes.trim() || null,
      });
      setBanner("Suppression created.");
      setSuppressionForm({
        recommendation_key: "",
        category: "",
        contract_id: "",
        site_id: "",
        hours: "24",
        notes: "",
      });
      await loadSuppressions();
      await loadRecommendations();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadRecommendations, loadSuppressions, suppressionForm]);

  const deleteSuppression = useCallback(
    async (suppressionId: string) => {
      setBusy(true);
      setBanner(null);
      setBannerErr(null);
      try {
        await deleteReq(`${apiBase}/ops/recommendations/suppressions/${encodeURIComponent(suppressionId)}`, authHeaders);
        setBanner("Suppression removed.");
        await loadSuppressions();
      } catch (e) {
        setBannerErr(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [apiBase, authHeaders, loadSuppressions],
  );

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Ops</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Recommendations dashboard, workflow actions, scans, and suppressions.
        </p>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button type="button" className="secondary" onClick={() => void runScan()} disabled={busy}>
            {busy ? "Working…" : "Run full scan"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadSummaries()} disabled={busy}>
            Refresh summaries
          </button>
          <button type="button" className="secondary" onClick={() => void loadRecommendations()} disabled={busy}>
            Refresh recommendations
          </button>
        </div>
        {banner ? <div style={{ marginTop: 10, color: "#86efac" }}>{banner}</div> : null}
        {bannerErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{bannerErr}</div> : null}
      </div>

      <div className="card hub-panel">
        <h3>Dashboard summary</h3>
        {summaryErr ? <div className="hub-err">{summaryErr}</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 10 }}>
          <li>Open recommendations: {actionsSummary?.open_recommendations ?? 0}</li>
          <li>Recommendations with available actions: {actionsSummary?.recommendations_with_available_actions ?? 0}</li>
          <li>Pending confirmations: {actionsSummary?.pending_confirmations ?? 0}</li>
          <li>Failed executions: {actionsSummary?.failed_executions ?? 0}</li>
          <li>Stale acknowledged count: {summary?.stale_acknowledged_count ?? 0}</li>
          <li>Pending approvals: {approvalsSummary?.pending_total ?? 0}</li>
        </ul>
      </div>

      <div className="card hub-panel">
        <h3>Recommendations</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <input value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} placeholder="status (open/acknowledged/...)" />
          <input value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} placeholder="category" />
          <input value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} placeholder="severity" />
          <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={includeSuppressed} onChange={(e) => setIncludeSuppressed(e.target.checked)} />
            include suppressed
          </label>
          <button type="button" className="secondary" onClick={() => void loadRecommendations()} disabled={recsBusy}>
            {recsBusy ? "Loading…" : "Apply filters"}
          </button>
        </div>
        {recsErr ? <div className="hub-err" style={{ marginTop: 8 }}>{recsErr}</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 10, maxHeight: 300, overflow: "auto" }}>
          {recommendations.map((r) => (
            <li key={r.id} style={{ marginBottom: 10 }}>
              <button
                type="button"
                className={selectedRecId === r.id ? "" : "secondary"}
                onClick={() => setSelectedRecId(r.id)}
                style={{ width: "100%", textAlign: "left" }}
              >
                <div>
                  <strong>{r.title}</strong> · {r.severity} · {r.status}
                </div>
                <div className="hub-sub">{r.category} · {r.entity_type} {String(r.entity_id).slice(0, 8)}…</div>
              </button>
            </li>
          ))}
          {!recommendations.length ? <li className="muted">No recommendations loaded.</li> : null}
        </ul>
      </div>

      <div className="card hub-panel">
        <h3>Recommendation actions</h3>
        {!selectedRec ? <div className="muted">Select a recommendation first.</div> : null}
        {selectedRec ? (
          <>
            <div className="hint" style={{ marginTop: 8 }}>
              <strong>{selectedRec.title}</strong> · key {selectedRec.recommendation_key}
            </div>
            <div className="field" style={{ marginTop: 8 }}>
              <label>Notes</label>
              <textarea value={actionNotes} onChange={(e) => setActionNotes(e.target.value)} />
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <button type="button" onClick={() => void actOnRecommendation("acknowledge")} disabled={busy}>Acknowledge</button>
              <button type="button" onClick={() => void actOnRecommendation("resolve")} disabled={busy}>Resolve</button>
              <button type="button" className="secondary" onClick={() => void actOnRecommendation("dismiss")} disabled={busy}>Dismiss</button>
              <button type="button" className="secondary" onClick={() => void actOnRecommendation("reopen")} disabled={busy}>Reopen</button>
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <input value={snoozeHours} onChange={(e) => setSnoozeHours(e.target.value)} placeholder="snooze hours" />
              <button type="button" className="secondary" onClick={() => void snoozeRecommendation()} disabled={busy}>Snooze</button>
            </div>
          </>
        ) : null}
      </div>

      <div className="card hub-panel">
        <h3>Suppressions</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <button type="button" className="secondary" onClick={() => void loadSuppressions()} disabled={suppressionsBusy}>
            {suppressionsBusy ? "Loading…" : "Refresh suppressions"}
          </button>
        </div>
        {suppressionsErr ? <div className="hub-err" style={{ marginTop: 8 }}>{suppressionsErr}</div> : null}
        <div className="divider" />
        <h4 style={{ fontSize: 13, marginTop: 0 }}>Create suppression</h4>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <input
            value={suppressionForm.recommendation_key}
            onChange={(e) => setSuppressionForm((f) => ({ ...f, recommendation_key: e.target.value }))}
            placeholder="recommendation_key"
          />
          <input
            value={suppressionForm.category}
            onChange={(e) => setSuppressionForm((f) => ({ ...f, category: e.target.value }))}
            placeholder="category"
          />
          <input value={suppressionForm.hours} onChange={(e) => setSuppressionForm((f) => ({ ...f, hours: e.target.value }))} placeholder="hours" />
          <button type="button" onClick={() => void createSuppression()} disabled={busy}>Create</button>
        </div>
        <div className="field" style={{ marginTop: 8 }}>
          <label>Notes</label>
          <textarea value={suppressionForm.notes} onChange={(e) => setSuppressionForm((f) => ({ ...f, notes: e.target.value }))} />
        </div>
        <ul className="hub-list-compact" style={{ marginTop: 10, maxHeight: 220, overflow: "auto" }}>
          {suppressions.map((s) => (
            <li key={s.id} style={{ marginBottom: 10 }}>
              <div>
                <strong>{s.recommendation_key ?? s.category ?? "suppression"}</strong> · until {String(s.suppressed_until).slice(0, 16)}
              </div>
              {s.notes ? <div className="hub-sub">{s.notes}</div> : null}
              <button type="button" className="secondary" onClick={() => void deleteSuppression(s.id)} disabled={busy}>
                Delete
              </button>
            </li>
          ))}
          {!suppressions.length ? <li className="muted">No active suppressions.</li> : null}
        </ul>
      </div>
    </div>
  );
}

