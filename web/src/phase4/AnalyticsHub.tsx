import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type EtlRunOut = {
  snapshot_id: string;
  snapshot_date: string;
};

type DashboardOut = {
  snapshot_date: string | null;
  data: Record<string, unknown>;
};

type JobMarginSummaryOut = {
  job_id: string;
  customer_id: string | null;
  currency: string;
  estimated_material_cost: number;
  actual_material_cost: number;
  variance_amount: number;
  variance_percent: number | null;
  unreconciled_costing_flag: boolean;
  invoice_generated_flag: boolean;
  costing_status: string | null;
  snapshot_id: string | null;
  invoice_before_snapshot_flag: boolean;
};

type JobCostVarianceRowOut = {
  job_id: string;
  customer_id: string | null;
  job_status: string;
  estimated_material_cost: number;
  actual_material_cost: number;
  variance_amount: number;
  costing_status: string;
  has_snapshot: boolean;
  invoice_id: string | null;
  flags: string[];
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

function formatMaybePercent(v: number | null): string {
  if (v == null) return "—";
  return `${v.toFixed(2)}%`;
}

export function AnalyticsHub({ apiBase, authHeaders }: Props) {
  const [etlBusy, setEtlBusy] = useState(false);
  const [etlDate, setEtlDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [etlResult, setEtlResult] = useState<EtlRunOut | null>(null);
  const [etlErr, setEtlErr] = useState<string | null>(null);

  const [dashBusy, setDashBusy] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardOut | null>(null);
  const [dashErr, setDashErr] = useState<string | null>(null);

  const [marginJobId, setMarginJobId] = useState("");
  const [marginBusy, setMarginBusy] = useState(false);
  const [marginOut, setMarginOut] = useState<JobMarginSummaryOut | null>(null);
  const [marginErr, setMarginErr] = useState<string | null>(null);

  const [varianceBusy, setVarianceBusy] = useState(false);
  const [varianceErr, setVarianceErr] = useState<string | null>(null);
  const [varianceStatus, setVarianceStatus] = useState("completed");
  const [varianceRows, setVarianceRows] = useState<JobCostVarianceRowOut[]>([]);

  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  useEffect(() => {
    if (!banner && !bannerErr) return;
    const t = window.setTimeout(() => {
      setBanner(null);
      setBannerErr(null);
    }, 4000);
    return () => window.clearTimeout(t);
  }, [banner, bannerErr]);

  const loadDashboard = useCallback(async () => {
    setDashBusy(true);
    setDashErr(null);
    try {
      const rows = await fetchJson<DashboardOut>(`${apiBase}/analytics/dashboard`, authHeaders);
      setDashboard(rows);
    } catch (e) {
      setDashboard(null);
      setDashErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDashBusy(false);
    }
  }, [apiBase, authHeaders]);

  const runEtl = useCallback(async () => {
    setEtlBusy(true);
    setEtlErr(null);
    setEtlResult(null);
    try {
      const q = new URLSearchParams();
      if (etlDate.trim()) q.set("date", etlDate.trim());
      const rows = await postJson<EtlRunOut>(`${apiBase}/analytics/etl/run?${q.toString()}`, authHeaders, {});
      setEtlResult(rows);
      setBanner("Analytics ETL run completed.");
      await loadDashboard();
    } catch (e) {
      setEtlErr(e instanceof Error ? e.message : String(e));
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setEtlBusy(false);
    }
  }, [apiBase, authHeaders, etlDate, loadDashboard]);

  const loadMarginSummary = useCallback(async () => {
    const jid = marginJobId.trim();
    if (!jid) return;
    setMarginBusy(true);
    setMarginErr(null);
    try {
      const rows = await fetchJson<JobMarginSummaryOut>(`${apiBase}/analytics/jobs/${encodeURIComponent(jid)}/margin-summary`, authHeaders);
      setMarginOut(rows);
    } catch (e) {
      setMarginOut(null);
      setMarginErr(e instanceof Error ? e.message : String(e));
    } finally {
      setMarginBusy(false);
    }
  }, [apiBase, authHeaders, marginJobId]);

  const loadVariance = useCallback(async () => {
    setVarianceBusy(true);
    setVarianceErr(null);
    try {
      const q = new URLSearchParams();
      if (varianceStatus.trim()) q.set("job_status", varianceStatus.trim());
      q.set("limit", "50");
      const rows = await fetchJson<JobCostVarianceRowOut[]>(
        `${apiBase}/analytics/dashboard/job-cost-variance?${q.toString()}`,
        authHeaders,
      );
      setVarianceRows(rows);
    } catch (e) {
      setVarianceRows([]);
      setVarianceErr(e instanceof Error ? e.message : String(e));
    } finally {
      setVarianceBusy(false);
    }
  }, [apiBase, authHeaders, varianceStatus]);

  useEffect(() => {
    void loadDashboard();
    void loadVariance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const dashboardJson = useMemo(() => {
    if (!dashboard) return "";
    return JSON.stringify(dashboard, null, 2);
  }, [dashboard]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Analytics</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Run the analytics ETL, inspect the latest snapshot dashboard, and review job margin + cost variance.
        </p>

        <div className="card" style={{ marginTop: 14 }}>
          <h3 style={{ marginTop: 0, fontSize: 14 }}>ETL run</h3>
          <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            <div className="field" style={{ flex: 1, minWidth: 220 }}>
              <label>Date (optional)</label>
              <input type="date" value={etlDate} onChange={(e) => setEtlDate(e.target.value)} />
            </div>
            <button type="button" className="secondary" onClick={() => void runEtl()} disabled={etlBusy}>
              {etlBusy ? "Running…" : "Run ETL"}
            </button>
          </div>
          {etlErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{etlErr}</div> : null}
          {etlResult ? (
            <div className="hint" style={{ marginTop: 10 }}>
              Snapshot id: <code>{etlResult.snapshot_id}</code> · snapshot date: <b>{etlResult.snapshot_date}</b>
            </div>
          ) : null}
        </div>

        {banner ? (
          <div
            style={{
              marginTop: 10,
              padding: "10px 16px",
              borderRadius: 8,
              border: "1px solid rgba(34,197,94,0.35)",
              background: "rgba(34,197,94,0.15)",
              color: "#86efac",
            }}
          >
            {banner}
          </div>
        ) : null}
        {bannerErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{bannerErr}</div> : null}
      </div>

      <nav className="hub-toc" aria-label="Analytics sections">
        <p className="hub-toc-title">Jump to</p>
        <div className="hub-toc-links">
          <a href="#analytics-dashboard">Dashboard</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#analytics-margin">Margin summary</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#analytics-variance">Job cost variance</a>
        </div>
      </nav>

      <div id="analytics-dashboard" className="card hub-panel hub-anchor">
        <h3>Latest dashboard snapshot</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button type="button" className="secondary" onClick={() => void loadDashboard()} disabled={dashBusy}>
            {dashBusy ? "Loading…" : "Refresh"}
          </button>
          {dashboard?.snapshot_date ? <div className="hub-sub">Snapshot date: <b>{dashboard.snapshot_date}</b></div> : null}
        </div>
        {dashErr ? <div className="hub-err" style={{ marginTop: 10 }}>{dashErr}</div> : null}
        <textarea value={dashboardJson} readOnly rows={12} style={{ marginTop: 10, width: "100%" }} />
      </div>

      <div id="analytics-margin" className="card hub-panel hub-anchor">
        <h3>Job margin summary</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>Job id</label>
            <input value={marginJobId} onChange={(e) => setMarginJobId(e.target.value)} placeholder="Paste job UUID/id" />
          </div>
          <button type="button" className="secondary" onClick={() => void loadMarginSummary()} disabled={marginBusy || !marginJobId.trim()}>
            {marginBusy ? "Loading…" : "Load"}
          </button>
        </div>

        {marginErr ? <div className="hub-err" style={{ marginTop: 10 }}>{marginErr}</div> : null}

        {marginOut ? (
          <div className="hint" style={{ marginTop: 12 }}>
            Job <code>{marginOut.job_id}</code> · status <b>{marginOut.costing_status ?? "—"}</b> · snapshot{" "}
            <b>{marginOut.snapshot_id ?? "—"}</b>
            <div className="hub-sub" style={{ marginTop: 8 }}>
              Estimated material: {marginOut.estimated_material_cost} · actual material: {marginOut.actual_material_cost}
              <br />
              Variance: {marginOut.variance_amount} ({formatMaybePercent(marginOut.variance_percent)})
            </div>
            <div className="hub-sub" style={{ marginTop: 6 }}>
              Invoice generated: {marginOut.invoice_generated_flag ? "yes" : "no"} · invoice before snapshot:{" "}
              {marginOut.invoice_before_snapshot_flag ? "yes" : "no"}
            </div>
          </div>
        ) : null}
      </div>

      <div id="analytics-variance" className="card hub-panel hub-anchor">
        <h3>Job cost variance</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>job_status</label>
            <input value={varianceStatus} onChange={(e) => setVarianceStatus(e.target.value)} placeholder="e.g. completed" />
          </div>
          <button type="button" className="secondary" onClick={() => void loadVariance()} disabled={varianceBusy}>
            {varianceBusy ? "Loading…" : "Refresh"}
          </button>
        </div>
        {varianceErr ? <div className="hub-err" style={{ marginTop: 10 }}>{varianceErr}</div> : null}
        {!varianceErr && !varianceRows.length ? <div className="muted" style={{ marginTop: 12 }}>No variance rows.</div> : null}

        {varianceRows.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {varianceRows.map((r) => (
              <li key={r.job_id} style={{ marginBottom: 10 }}>
                <div>
                  <strong>{r.job_id}</strong> · {r.job_status} · costing {r.costing_status} · snapshot{" "}
                  {r.has_snapshot ? "yes" : "no"}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  est {r.estimated_material_cost} · actual {r.actual_material_cost} · var {r.variance_amount}
                  {r.flags?.length ? ` · flags: ${r.flags.slice(0, 3).join(", ")}${r.flags.length > 3 ? "…" : ""}` : ""}
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

