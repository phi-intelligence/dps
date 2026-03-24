import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type SlaPolicy = {
  id: string;
  name: string;
  priority: string;
  response_target_minutes: number;
  attendance_target_minutes: number;
  resolution_target_minutes: number;
  service_window_json: string;
  warning_threshold_percent_json: string;
  escalation_notes: string | null;
  active: boolean;
  created_at: string;
};

type FetchState<T> = { data: T | null; error: string | null };

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

async function patchJson<T>(url: string, headers: Record<string, string>, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "PATCH",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
  return res.json() as Promise<T>;
}

function tryParseJson(v: string): boolean {
  try {
    const t = v.trim();
    if (!t) return true;
    JSON.parse(t);
    return true;
  } catch {
    return false;
  }
}

export function SlaPoliciesHub({ apiBase, authHeaders }: Props) {
  const [activeOnly, setActiveOnly] = useState(false);

  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [policiesState, setPoliciesState] = useState<FetchState<SlaPolicy[]>>({ data: null, error: null });
  const policies = policiesState.data ?? [];

  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const selectedPolicy = useMemo(
    () => (selectedPolicyId ? policies.find((p) => p.id === selectedPolicyId) ?? null : null),
    [policies, selectedPolicyId],
  );

  const [createForm, setCreateForm] = useState({
    name: "",
    priority: "",
    response_target_minutes: 60,
    attendance_target_minutes: 120,
    resolution_target_minutes: 480,
    service_window_json: "{}",
    warning_threshold_percent_json: "{}",
    escalation_notes: "",
    active: true,
  });

  const [patchForm, setPatchForm] = useState({
    name: "",
    priority: "",
    response_target_minutes: 60,
    attendance_target_minutes: 120,
    resolution_target_minutes: 480,
    service_window_json: "{}",
    warning_threshold_percent_json: "{}",
    escalation_notes: "",
    active: true,
  });

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  const loadPolicies = useCallback(async () => {
    setPoliciesState({ data: null, error: null });
    setBannerErr(null);
    try {
      const q = activeOnly ? "?active_only=1" : "?active_only=0";
      const rows = await fetchJson<SlaPolicy[]>(`${apiBase}/sla${"/policies"}${q}`, authHeaders);
      setPoliciesState({ data: rows, error: null });
      if (!selectedPolicyId && rows[0]?.id) setSelectedPolicyId(rows[0].id);
    } catch (e) {
      setPoliciesState({ data: null, error: e instanceof Error ? e.message : String(e) });
    }
  }, [activeOnly, apiBase, authHeaders, selectedPolicyId]);

  useEffect(() => {
    void loadPolicies();
  }, [loadPolicies]);

  useEffect(() => {
    if (!selectedPolicy) return;
    setPatchForm({
      name: selectedPolicy.name,
      priority: selectedPolicy.priority,
      response_target_minutes: selectedPolicy.response_target_minutes,
      attendance_target_minutes: selectedPolicy.attendance_target_minutes,
      resolution_target_minutes: selectedPolicy.resolution_target_minutes,
      service_window_json: selectedPolicy.service_window_json ?? "{}",
      warning_threshold_percent_json: selectedPolicy.warning_threshold_percent_json ?? "{}",
      escalation_notes: selectedPolicy.escalation_notes ?? "",
      active: selectedPolicy.active,
    });
  }, [selectedPolicyId]); // eslint-disable-line react-hooks/exhaustive-deps

  const createPolicy = useCallback(async () => {
    setBusy(true);
    setBannerErr(null);
    try {
      if (!createForm.name.trim()) throw new Error("Name is required.");
      if (!createForm.priority.trim()) throw new Error("Priority is required.");
      if (!tryParseJson(createForm.service_window_json)) throw new Error("service_window_json is not valid JSON.");
      if (!tryParseJson(createForm.warning_threshold_percent_json))
        throw new Error("warning_threshold_percent_json is not valid JSON.");

      await postJson<SlaPolicy>(`${apiBase}/sla/policies`, authHeaders, {
        name: createForm.name.trim(),
        priority: createForm.priority.trim(),
        response_target_minutes: createForm.response_target_minutes,
        attendance_target_minutes: createForm.attendance_target_minutes,
        resolution_target_minutes: createForm.resolution_target_minutes,
        service_window_json: createForm.service_window_json.trim() || "{}",
        warning_threshold_percent_json: createForm.warning_threshold_percent_json.trim() || "{}",
        escalation_notes: createForm.escalation_notes.trim() || null,
        active: createForm.active,
      });
      setBanner("SLA policy created.");
      setCreateForm({
        name: "",
        priority: "",
        response_target_minutes: 60,
        attendance_target_minutes: 120,
        resolution_target_minutes: 480,
        service_window_json: "{}",
        warning_threshold_percent_json: "{}",
        escalation_notes: "",
        active: true,
      });
      await loadPolicies();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, createForm, loadPolicies]);

  const patchPolicy = useCallback(async () => {
    if (!selectedPolicyId) return;
    setBusy(true);
    setBannerErr(null);
    try {
      if (!patchForm.name.trim()) throw new Error("Name is required.");
      if (!patchForm.priority.trim()) throw new Error("Priority is required.");
      if (!tryParseJson(patchForm.service_window_json)) throw new Error("service_window_json is not valid JSON.");
      if (!tryParseJson(patchForm.warning_threshold_percent_json))
        throw new Error("warning_threshold_percent_json is not valid JSON.");

      await patchJson<SlaPolicy>(`${apiBase}/sla/policies/${encodeURIComponent(selectedPolicyId)}`, authHeaders, {
        name: patchForm.name.trim(),
        priority: patchForm.priority.trim(),
        response_target_minutes: patchForm.response_target_minutes,
        attendance_target_minutes: patchForm.attendance_target_minutes,
        resolution_target_minutes: patchForm.resolution_target_minutes,
        service_window_json: patchForm.service_window_json.trim() || "{}",
        warning_threshold_percent_json: patchForm.warning_threshold_percent_json.trim() || "{}",
        escalation_notes: patchForm.escalation_notes.trim() || null,
        active: patchForm.active,
      });
      setBanner("SLA policy updated.");
      await loadPolicies();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadPolicies, patchForm, selectedPolicyId]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>SLA policies</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Manage response/attendance/resolution targets and JSON service-window + warning thresholds.
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
            Active only
          </label>
          <button type="button" className="secondary" onClick={() => void loadPolicies()} disabled={busy}>
            {busy ? "Loading…" : "Refresh"}
          </button>
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

      <nav className="hub-toc" aria-label="SLA sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#sla-list">Policies</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#sla-create">Create</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#sla-edit">Edit</a>
        </div>
      </nav>

      <div id="sla-list" className="card hub-panel hub-anchor">
        <h3>Policies</h3>
        {policiesState.error ? <div className="hub-err">{policiesState.error}</div> : null}
        {!policiesState.error && !policies.length ? <div className="muted">No SLA policies loaded.</div> : null}
        {policies.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {policies.map((p) => (
              <li key={p.id} style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  className={p.id === selectedPolicyId ? "" : "secondary"}
                  onClick={() => setSelectedPolicyId(p.id)}
                  style={{ textAlign: "left", width: "100%" }}
                >
                  <div>
                    <strong>{p.name}</strong> · priority {p.priority}
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    response {p.response_target_minutes}m · attendance {p.attendance_target_minutes}m · resolution {p.resolution_target_minutes}m
                    {p.active ? "" : " · inactive"}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div id="sla-create" className="card hub-panel hub-anchor">
        <h3>Create policy</h3>
        <div className="field">
          <label>Name</label>
          <input value={createForm.name} onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))} />
        </div>
        <div className="field">
          <label>Priority (string key)</label>
          <input value={createForm.priority} onChange={(e) => setCreateForm((f) => ({ ...f, priority: e.target.value }))} />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>Response target (minutes)</label>
            <input
              type="number"
              value={createForm.response_target_minutes}
              onChange={(e) => setCreateForm((f) => ({ ...f, response_target_minutes: Number(e.target.value) }))}
            />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>Attendance target (minutes)</label>
            <input
              type="number"
              value={createForm.attendance_target_minutes}
              onChange={(e) => setCreateForm((f) => ({ ...f, attendance_target_minutes: Number(e.target.value) }))}
            />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>Resolution target (minutes)</label>
            <input
              type="number"
              value={createForm.resolution_target_minutes}
              onChange={(e) => setCreateForm((f) => ({ ...f, resolution_target_minutes: Number(e.target.value) }))}
            />
          </div>
        </div>
        <div className="field">
          <label>service_window_json</label>
          <textarea value={createForm.service_window_json} onChange={(e) => setCreateForm((f) => ({ ...f, service_window_json: e.target.value }))} />
        </div>
        <div className="field">
          <label>warning_threshold_percent_json</label>
          <textarea
            value={createForm.warning_threshold_percent_json}
            onChange={(e) => setCreateForm((f) => ({ ...f, warning_threshold_percent_json: e.target.value }))}
          />
        </div>
        <div className="field">
          <label>Escalation notes (optional)</label>
          <textarea value={createForm.escalation_notes} onChange={(e) => setCreateForm((f) => ({ ...f, escalation_notes: e.target.value }))} />
        </div>
        <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={createForm.active} onChange={(e) => setCreateForm((f) => ({ ...f, active: e.target.checked }))} />
          <label>Active</label>
        </div>
        <button type="button" onClick={() => void createPolicy()} disabled={busy || !createForm.name.trim() || !createForm.priority.trim()}>
          {busy ? "Creating…" : "Create policy"}
        </button>
      </div>

      <div id="sla-edit" className="card hub-panel hub-anchor">
        <h3>Edit selected policy</h3>
        {!selectedPolicy ? <div className="muted">Select a policy from the list.</div> : null}
        {selectedPolicy ? (
          <>
            <div className="field">
              <label>Name</label>
              <input value={patchForm.name} onChange={(e) => setPatchForm((f) => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="field">
              <label>Priority</label>
              <input value={patchForm.priority} onChange={(e) => setPatchForm((f) => ({ ...f, priority: e.target.value }))} />
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>Response target (minutes)</label>
                <input
                  type="number"
                  value={patchForm.response_target_minutes}
                  onChange={(e) => setPatchForm((f) => ({ ...f, response_target_minutes: Number(e.target.value) }))}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>Attendance target (minutes)</label>
                <input
                  type="number"
                  value={patchForm.attendance_target_minutes}
                  onChange={(e) => setPatchForm((f) => ({ ...f, attendance_target_minutes: Number(e.target.value) }))}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>Resolution target (minutes)</label>
                <input
                  type="number"
                  value={patchForm.resolution_target_minutes}
                  onChange={(e) => setPatchForm((f) => ({ ...f, resolution_target_minutes: Number(e.target.value) }))}
                />
              </div>
            </div>
            <div className="field">
              <label>service_window_json</label>
              <textarea value={patchForm.service_window_json} onChange={(e) => setPatchForm((f) => ({ ...f, service_window_json: e.target.value }))} />
            </div>
            <div className="field">
              <label>warning_threshold_percent_json</label>
              <textarea
                value={patchForm.warning_threshold_percent_json}
                onChange={(e) => setPatchForm((f) => ({ ...f, warning_threshold_percent_json: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Escalation notes (optional)</label>
              <textarea value={patchForm.escalation_notes} onChange={(e) => setPatchForm((f) => ({ ...f, escalation_notes: e.target.value }))} />
            </div>
            <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={patchForm.active} onChange={(e) => setPatchForm((f) => ({ ...f, active: e.target.checked }))} />
              <label>Active</label>
            </div>
            <button type="button" className="secondary" onClick={() => void patchPolicy()} disabled={busy}>
              {busy ? "Saving…" : "Save policy"}
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}

