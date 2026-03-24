import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type ApprovalsDashboardSummaryOut = {
  pending_total: number;
  pending_by_type: Record<string, number>;
  overdue_pending_count: number;
  assigned_to_me_pending: number;
  recently_decided: number;
  overdue_hours_threshold: number;
};

type ApprovalRequestOut = {
  id: string;
  approval_type: string;
  target_entity_type: string;
  target_entity_id: string;
  requested_by_user_id: string;
  assigned_to_user_id: string | null;
  status: string;
  reason: string;
  payload_json: Record<string, unknown> | null;
  created_at: string;
  decided_at: string | null;
  decided_by_user_id: string | null;
  decision_notes: string | null;
  execution_result_json: Record<string, unknown> | null;
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

export function ApprovalsHub({ apiBase, authHeaders }: Props) {
  const [summaryBusy, setSummaryBusy] = useState(false);
  const [summary, setSummary] = useState<ApprovalsDashboardSummaryOut | null>(null);
  const [summaryErr, setSummaryErr] = useState<string | null>(null);

  const [overdueHours, setOverdueHours] = useState(72.0);

  const [listBusy, setListBusy] = useState(false);
  const [listErr, setListErr] = useState<string | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequestOut[]>([]);

  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [approvalTypeFilter, setApprovalTypeFilter] = useState<string>("");
  const [assignedToFilter, setAssignedToFilter] = useState<string>("");
  const [targetEntityTypeFilter, setTargetEntityTypeFilter] = useState<string>("");
  const [targetEntityIdFilter, setTargetEntityIdFilter] = useState<string>("");

  const [selectedApprovalId, setSelectedApprovalId] = useState<string>("");
  const selectedApproval = useMemo(
    () => (selectedApprovalId ? approvals.find((a) => a.id === selectedApprovalId) ?? null : null),
    [approvals, selectedApprovalId],
  );

  const [decisionNotes, setDecisionNotes] = useState("");
  const [decisionBusy, setDecisionBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const approvalTypeOptions = useMemo(() => {
    if (!summary) return [];
    return Object.keys(summary.pending_by_type ?? {})
      .sort((a, b) => (summary.pending_by_type[a] ?? 0) - (summary.pending_by_type[b] ?? 0))
      .reverse();
  }, [summary]);

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  const loadSummary = useCallback(async () => {
    setSummaryBusy(true);
    setSummaryErr(null);
    try {
      const u = new URL(`${apiBase}/approvals/dashboard/summary`);
      u.searchParams.set("overdue_hours", String(overdueHours));
      const rows = await fetchJson<ApprovalsDashboardSummaryOut>(u.toString(), authHeaders);
      setSummary(rows);
    } catch (e) {
      setSummaryErr(e instanceof Error ? e.message : String(e));
      setSummary(null);
    } finally {
      setSummaryBusy(false);
    }
  }, [apiBase, authHeaders, overdueHours]);

  const loadList = useCallback(async () => {
    setListBusy(true);
    setListErr(null);
    try {
      const q = new URLSearchParams();
      if (statusFilter.trim()) q.set("status", statusFilter.trim());
      if (approvalTypeFilter.trim()) q.set("approval_type", approvalTypeFilter.trim());
      if (assignedToFilter.trim()) q.set("assigned_to_user_id", assignedToFilter.trim());
      if (targetEntityTypeFilter.trim()) q.set("target_entity_type", targetEntityTypeFilter.trim());
      if (targetEntityIdFilter.trim()) q.set("target_entity_id", targetEntityIdFilter.trim());
      q.set("limit", "100");
      q.set("offset", "0");

      const rows = await fetchJson<ApprovalRequestOut[]>(`${apiBase}/approvals?${q.toString()}`, authHeaders);
      setApprovals(rows);
      if (!selectedApprovalId && rows[0]?.id) setSelectedApprovalId(rows[0].id);
    } catch (e) {
      setListErr(e instanceof Error ? e.message : String(e));
      setApprovals([]);
    } finally {
      setListBusy(false);
    }
  }, [
    approvalTypeFilter,
    apiBase,
    authHeaders,
    assignedToFilter,
    selectedApprovalId,
    statusFilter,
    targetEntityIdFilter,
    targetEntityTypeFilter,
  ]);

  useEffect(() => {
    void loadSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedApproval) return;
    setDecisionNotes("");
  }, [selectedApprovalId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void loadList();
  }, [loadList]);

  const approve = useCallback(async () => {
    if (!selectedApproval) return;
    setDecisionBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      if (selectedApproval.status !== "pending") throw new Error("Approval is not pending.");
      const dn = decisionNotes.trim();
      await postJson<ApprovalRequestOut>(`${apiBase}/approvals/${encodeURIComponent(selectedApproval.id)}/approve`, authHeaders, {
        decision_notes: dn ? dn : null,
      });
      setBanner("Approval approved.");
      await loadSummary();
      await loadList();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDecisionBusy(false);
    }
  }, [apiBase, authHeaders, decisionNotes, loadList, loadSummary, selectedApproval]);

  const reject = useCallback(async () => {
    if (!selectedApproval) return;
    setDecisionBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      if (selectedApproval.status !== "pending") throw new Error("Approval is not pending.");
      const dn = decisionNotes.trim();
      await postJson<ApprovalRequestOut>(`${apiBase}/approvals/${encodeURIComponent(selectedApproval.id)}/reject`, authHeaders, {
        decision_notes: dn ? dn : null,
      });
      setBanner("Approval rejected.");
      await loadSummary();
      await loadList();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDecisionBusy(false);
    }
  }, [apiBase, authHeaders, decisionNotes, loadList, loadSummary, selectedApproval]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Approvals</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Review pending requests and approve or reject with decision notes.
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            Overdue threshold (hours)
            <input
              type="number"
              value={overdueHours}
              onChange={(e) => setOverdueHours(Number(e.target.value))}
              style={{ width: 120 }}
              step={1}
              min={1}
              max={720}
            />
          </label>
          <button type="button" className="secondary" onClick={() => void loadSummary()} disabled={summaryBusy || decisionBusy}>
            {summaryBusy ? "Loading…" : "Refresh summary"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadList()} disabled={listBusy || decisionBusy}>
            {listBusy ? "Loading…" : "Refresh list"}
          </button>
        </div>

        {summary ? (
          <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 10 }}>
            <div className="hub-sub">
              Pending: <strong>{summary.pending_total}</strong>
            </div>
            <div className="hub-sub">
              Overdue: <strong>{summary.overdue_pending_count}</strong>
            </div>
            <div className="hub-sub">
              Assigned to you: <strong>{summary.assigned_to_me_pending}</strong>
            </div>
            <div className="hub-sub">
              Recently decided (7d): <strong>{summary.recently_decided}</strong>
            </div>
          </div>
        ) : summaryErr ? (
          <div style={{ marginTop: 10, color: "#ffb4b4" }}>{summaryErr}</div>
        ) : null}

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

      <nav className="hub-toc" aria-label="Approvals sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#approvals-list">Approvals</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#approvals-review">Review</a>
        </div>
      </nav>

      <div id="approvals-list" className="card hub-panel hub-anchor">
        <h3>Approval requests</h3>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <label className="field" style={{ minWidth: 200 }}>
            <span className="hub-sub">Status</span>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} disabled={listBusy || decisionBusy}>
              <option value="pending">pending</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
              <option value="">any</option>
            </select>
          </label>

          <label className="field" style={{ minWidth: 220 }}>
            <span className="hub-sub">Type</span>
            <select
              value={approvalTypeFilter}
              onChange={(e) => setApprovalTypeFilter(e.target.value)}
              disabled={listBusy || decisionBusy}
            >
              <option value="">(any)</option>
              {approvalTypeOptions.map((t) => (
                <option value={t} key={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <div className="field" style={{ minWidth: 220 }}>
            <label className="hub-sub">Assigned to user id</label>
            <input
              value={assignedToFilter}
              onChange={(e) => setAssignedToFilter(e.target.value)}
              placeholder="e.g. 3d2f…"
              disabled={listBusy || decisionBusy}
            />
          </div>

          <div className="field" style={{ minWidth: 180 }}>
            <label className="hub-sub">Target entity type</label>
            <input
              value={targetEntityTypeFilter}
              onChange={(e) => setTargetEntityTypeFilter(e.target.value)}
              placeholder="invoice | contract | ..."
              disabled={listBusy || decisionBusy}
            />
          </div>

          <div className="field" style={{ minWidth: 200 }}>
            <label className="hub-sub">Target entity id</label>
            <input
              value={targetEntityIdFilter}
              onChange={(e) => setTargetEntityIdFilter(e.target.value)}
              placeholder="uuid / id"
              disabled={listBusy || decisionBusy}
            />
          </div>
        </div>

        {listErr ? <div style={{ marginTop: 12, color: "#ffb4b4" }}>{listErr}</div> : null}

        {!listErr && !approvals.length ? <div className="muted" style={{ marginTop: 12 }}>No approvals found.</div> : null}

        {approvals.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {approvals.map((a) => (
              <li key={a.id} style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  className={a.id === selectedApprovalId ? "" : "secondary"}
                  onClick={() => setSelectedApprovalId(a.id)}
                  disabled={decisionBusy}
                  style={{ textAlign: "left", width: "100%" }}
                >
                  <div>
                    <strong>{a.approval_type}</strong> · {a.target_entity_type} {a.target_entity_id.slice(0, 8)}…
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    {a.status} · {a.assigned_to_user_id ? `assigned ${a.assigned_to_user_id.slice(0, 8)}…` : "unassigned"} · created{" "}
                    {a.created_at ? String(a.created_at).slice(0, 16) : "—"}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div id="approvals-review" className="card hub-panel hub-anchor">
        <h3>Approve / reject</h3>

        {!selectedApproval ? <div className="muted">Select an approval request to review.</div> : null}

        {selectedApproval ? (
          <>
            <div className="hint" style={{ marginTop: 10 }}>
              <strong>{selectedApproval.approval_type}</strong> · {selectedApproval.target_entity_type} {selectedApproval.target_entity_id}
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 12 }}>
              <div className="hub-sub">
                Status: <strong>{selectedApproval.status}</strong>
              </div>
              <div className="hub-sub">
                Requested by: <strong>{selectedApproval.requested_by_user_id}</strong>
              </div>
              <div className="hub-sub">
                Assigned: <strong>{selectedApproval.assigned_to_user_id ?? "—"}</strong>
              </div>
            </div>

            <div className="divider" />

            <div className="field">
              <label>Reason</label>
              <textarea value={selectedApproval.reason} readOnly />
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>Payload JSON</label>
                <textarea value={selectedApproval.payload_json ? JSON.stringify(selectedApproval.payload_json, null, 2) : ""} readOnly />
              </div>
            </div>

            {selectedApproval.execution_result_json ? (
              <div className="field">
                <label>Execution result JSON</label>
                <textarea value={JSON.stringify(selectedApproval.execution_result_json, null, 2)} readOnly />
              </div>
            ) : null}

            <div className="divider" />

            <div className="field">
              <label>Decision notes (optional)</label>
              <textarea value={decisionNotes} onChange={(e) => setDecisionNotes(e.target.value)} placeholder="e.g. Approved after review of documents." />
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
              <button type="button" onClick={() => void approve()} disabled={decisionBusy || selectedApproval.status !== "pending"}>
                {decisionBusy ? "Working…" : "Approve"}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => void reject()}
                disabled={decisionBusy || selectedApproval.status !== "pending"}
              >
                {decisionBusy ? "Working…" : "Reject"}
              </button>
            </div>

            {selectedApproval.decided_at && selectedApproval.decision_notes ? (
              <div className="hint" style={{ marginTop: 10 }}>
                Decided {String(selectedApproval.decided_at).slice(0, 16)} by {selectedApproval.decided_by_user_id ?? "—"} · Notes:{" "}
                {selectedApproval.decision_notes}
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

