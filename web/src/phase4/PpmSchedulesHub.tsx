import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type Contract = {
  id: string;
  contract_code: string;
  name: string;
  site_id: string | null;
  created_at: string;
};

type Site = {
  id: string;
  name: string;
  address_line1: string;
  active: boolean;
  created_at: string;
};

type Asset = {
  id: string;
  asset_code: string;
  name: string;
  site_id: string | null;
  contract_id: string | null;
  created_at: string;
};

type PpmScheduleOut = {
  id: string;
  contract_id: string;
  site_id: string;
  asset_id: string | null;
  title: string;
  frequency_value: number;
  frequency_unit: string; // day|week|month|year
  recurrence_rule: string | null;
  next_due_date: string;
  planning_window_days: number;
  estimated_duration_minutes: number | null;
  checklist_template_ref: string | null;
  compliance_template_ref: string | null;
  required_competencies_json: string;
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

function isoToDatetimeLocal(v: string | null | undefined): string {
  if (!v) return new Date().toISOString().slice(0, 16);
  return new Date(v).toISOString().slice(0, 16);
}

function datetimeLocalToIso(v: string): string {
  return new Date(v).toISOString();
}

export function PpmSchedulesHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [contracts, setContracts] = useState<Contract[]>([]);
  const [contractsBusy, setContractsBusy] = useState(false);

  const [sites, setSites] = useState<Site[]>([]);
  const [sitesBusy, setSitesBusy] = useState(false);

  const [assets, setAssets] = useState<Asset[]>([]);
  const [assetsBusy, setAssetsBusy] = useState(false);

  const [filterContractId, setFilterContractId] = useState("");
  const [filterSiteId, setFilterSiteId] = useState("");

  const [schedulesState, setSchedulesState] = useState<FetchState<PpmScheduleOut[]>>({ data: null, error: null });
  const schedules = schedulesState.data ?? [];

  const [selectedScheduleId, setSelectedScheduleId] = useState<string>("");
  const selectedSchedule = useMemo(
    () => (selectedScheduleId ? schedules.find((s) => s.id === selectedScheduleId) ?? null : null),
    [schedules, selectedScheduleId],
  );

  const [createForm, setCreateForm] = useState({
    contract_id: "",
    site_id: "",
    asset_id: "",
    title: "",
    frequency_value: 1,
    frequency_unit: "month",
    recurrence_rule: "",
    next_due_date: new Date().toISOString().slice(0, 16),
    planning_window_days: 30,
    estimated_duration_minutes: "",
    checklist_template_ref: "",
    compliance_template_ref: "",
    required_competencies_json: "[]",
    active: true,
  });

  const [patchForm, setPatchForm] = useState({
    title: "",
    frequency_value: 1,
    frequency_unit: "month",
    recurrence_rule: "",
    next_due_date: new Date().toISOString().slice(0, 16),
    planning_window_days: 30,
    estimated_duration_minutes: "",
    checklist_template_ref: "",
    compliance_template_ref: "",
    required_competencies_json: "[]",
    active: true,
  });

  const [runBusy, setRunBusy] = useState(false);
  const [runForm, setRunForm] = useState({
    run_date: new Date().toISOString().slice(0, 16),
    planning_window_days: 30,
  });

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  const loadContracts = useCallback(async () => {
    setContractsBusy(true);
    setContracts([]);
    try {
      const rows = await fetchJson<Contract[]>(`${apiBase}/contracts`, authHeaders);
      setContracts(rows);
      if (!createForm.contract_id && rows[0]?.id) setCreateForm((f) => ({ ...f, contract_id: rows[0].id }));
      if (!filterContractId && rows[0]?.id) setFilterContractId(rows[0].id);
    } catch (e) {
      // Intentionally silent; schedules load handles its own errors.
    } finally {
      setContractsBusy(false);
    }
  }, [apiBase, authHeaders, createForm.contract_id, filterContractId]);

  const loadSites = useCallback(async () => {
    setSitesBusy(true);
    setSites([]);
    try {
      const rows = await fetchJson<Site[]>(`${apiBase}/sites?limit=500&offset=0`, authHeaders);
      setSites(rows);
      if (!createForm.site_id && rows[0]?.id) setCreateForm((f) => ({ ...f, site_id: rows[0].id }));
      if (!filterSiteId && rows[0]?.id) setFilterSiteId(rows[0].id);
    } catch {
      // Intentionally silent; schedules load handles its own errors.
    } finally {
      setSitesBusy(false);
    }
  }, [apiBase, authHeaders, createForm.site_id, filterSiteId]);

  const loadAssetsForSite = useCallback(
    async (siteId: string) => {
      if (!siteId.trim()) {
        setAssets([]);
        return;
      }
      setAssetsBusy(true);
      try {
        const q = new URLSearchParams();
        q.set("limit", "200");
        q.set("site_id", siteId.trim());
        const rows = await fetchJson<Asset[]>(`${apiBase}/assets?${q.toString()}`, authHeaders);
        setAssets(rows);
      } catch {
        setAssets([]);
      } finally {
        setAssetsBusy(false);
      }
    },
    [apiBase, authHeaders],
  );

  const loadSchedules = useCallback(async () => {
    setSchedulesState({ data: null, error: null });
    setBannerErr(null);
    try {
      const q = new URLSearchParams();
      if (filterContractId.trim()) q.set("contract_id", filterContractId.trim());
      if (filterSiteId.trim()) q.set("site_id", filterSiteId.trim());
      const rows = await fetchJson<PpmScheduleOut[]>(`${apiBase}/ppm/schedules?${q.toString()}`, authHeaders);
      setSchedulesState({ data: rows, error: null });
      if (!selectedScheduleId && rows[0]?.id) setSelectedScheduleId(rows[0].id);
    } catch (e) {
      setSchedulesState({ data: null, error: e instanceof Error ? e.message : String(e) });
    }
  }, [apiBase, authHeaders, filterContractId, filterSiteId, selectedScheduleId]);

  useEffect(() => {
    void loadContracts();
    void loadSites();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!createForm.contract_id.trim()) return;
    const c = contracts.find((x) => x.id === createForm.contract_id) ?? null;
    const siteId = c?.site_id ?? "";
    if (!siteId) return;
    // If user hasn't explicitly chosen a site yet, default from contract.
    setCreateForm((f) => (f.site_id ? f : { ...f, site_id: siteId }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [createForm.contract_id, contracts]);

  useEffect(() => {
    if (!createForm.site_id.trim()) return;
    void loadAssetsForSite(createForm.site_id.trim());
  }, [createForm.site_id, loadAssetsForSite]);

  useEffect(() => {
    void loadSchedules();
  }, [loadSchedules]);

  useEffect(() => {
    if (!selectedSchedule) return;
    setPatchForm({
      title: selectedSchedule.title,
      frequency_value: selectedSchedule.frequency_value,
      frequency_unit: selectedSchedule.frequency_unit,
      recurrence_rule: selectedSchedule.recurrence_rule ?? "",
      next_due_date: isoToDatetimeLocal(selectedSchedule.next_due_date),
      planning_window_days: selectedSchedule.planning_window_days,
      estimated_duration_minutes: selectedSchedule.estimated_duration_minutes != null ? String(selectedSchedule.estimated_duration_minutes) : "",
      checklist_template_ref: selectedSchedule.checklist_template_ref ?? "",
      compliance_template_ref: selectedSchedule.compliance_template_ref ?? "",
      required_competencies_json: selectedSchedule.required_competencies_json ?? "[]",
      active: selectedSchedule.active,
    });
  }, [selectedScheduleId]); // eslint-disable-line react-hooks/exhaustive-deps

  const createSchedule = useCallback(async () => {
    setBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      if (!createForm.contract_id.trim()) throw new Error("Select a contract.");
      if (!createForm.site_id.trim()) throw new Error("Select a site.");
      if (!createForm.title.trim()) throw new Error("Title is required.");
      if (!createForm.next_due_date.trim()) throw new Error("Next due date is required.");
      if (!tryParseJson(createForm.required_competencies_json)) throw new Error("required_competencies_json is not valid JSON.");

      const estimatedDuration = createForm.estimated_duration_minutes.trim()
        ? Number(createForm.estimated_duration_minutes.trim())
        : null;
      if (estimatedDuration != null && (!Number.isFinite(estimatedDuration) || estimatedDuration < 0)) {
        throw new Error("estimated_duration_minutes must be a non-negative number.");
      }

      await postJson<PpmScheduleOut>(`${apiBase}/ppm/schedules`, authHeaders, {
        contract_id: createForm.contract_id.trim(),
        site_id: createForm.site_id.trim(),
        asset_id: createForm.asset_id.trim() || null,
        title: createForm.title.trim(),
        frequency_value: createForm.frequency_value,
        frequency_unit: createForm.frequency_unit,
        recurrence_rule: createForm.recurrence_rule.trim() || null,
        next_due_date: datetimeLocalToIso(createForm.next_due_date),
        planning_window_days: createForm.planning_window_days,
        estimated_duration_minutes: estimatedDuration,
        checklist_template_ref: createForm.checklist_template_ref.trim() || null,
        compliance_template_ref: createForm.compliance_template_ref.trim() || null,
        required_competencies_json: createForm.required_competencies_json.trim() || "[]",
        active: createForm.active,
      });

      setBanner("PPM schedule created.");
      setCreateForm((f) => ({
        ...f,
        title: "",
        recurrence_rule: "",
        estimated_duration_minutes: "",
        checklist_template_ref: "",
        compliance_template_ref: "",
        required_competencies_json: "[]",
        active: true,
      }));
      await loadSchedules();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, createForm, loadSchedules]);

  const patchSchedule = useCallback(async () => {
    if (!selectedScheduleId) return;
    setBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      if (!patchForm.title.trim()) throw new Error("Title is required.");
      if (!patchForm.next_due_date.trim()) throw new Error("Next due date is required.");
      if (!tryParseJson(patchForm.required_competencies_json)) throw new Error("required_competencies_json is not valid JSON.");

      const estimatedDuration = patchForm.estimated_duration_minutes.trim() ? Number(patchForm.estimated_duration_minutes.trim()) : null;
      if (estimatedDuration != null && (!Number.isFinite(estimatedDuration) || estimatedDuration < 0)) {
        throw new Error("estimated_duration_minutes must be a non-negative number.");
      }

      await patchJson<PpmScheduleOut>(
        `${apiBase}/ppm/schedules/${encodeURIComponent(selectedScheduleId)}`,
        authHeaders,
        {
          title: patchForm.title.trim(),
          frequency_value: patchForm.frequency_value,
          frequency_unit: patchForm.frequency_unit,
          recurrence_rule: patchForm.recurrence_rule.trim() || null,
          next_due_date: datetimeLocalToIso(patchForm.next_due_date),
          planning_window_days: patchForm.planning_window_days,
          estimated_duration_minutes: estimatedDuration,
          checklist_template_ref: patchForm.checklist_template_ref.trim() || null,
          compliance_template_ref: patchForm.compliance_template_ref.trim() || null,
          required_competencies_json: patchForm.required_competencies_json.trim() || "[]",
          active: patchForm.active,
        },
      );

      setBanner("PPM schedule updated.");
      await loadSchedules();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadSchedules, patchForm, selectedScheduleId]);

  const runGeneration = useCallback(async () => {
    setRunBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      await postJson<{ created_job_ids: string[]; skipped_schedule_ids: string[] }>(
        `${apiBase}/ppm/run-generation`,
        authHeaders,
        {
          run_date: runForm.run_date.trim() ? datetimeLocalToIso(runForm.run_date) : null,
          planning_window_days: runForm.planning_window_days,
        },
      );
      setBanner("PPM job generation triggered.");
      await loadSchedules();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunBusy(false);
    }
  }, [apiBase, authHeaders, loadSchedules, runForm]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>PPM schedules</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          CRUD for planned preventative maintenance schedules, plus a “generate jobs” trigger.
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <label className="hub-sub" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            Contract filter
            <select
              value={filterContractId}
              onChange={(e) => setFilterContractId(e.target.value)}
              disabled={contractsBusy || busy}
            >
              <option value="">(All)</option>
              {contracts.map((c) => (
                <option value={c.id} key={c.id}>
                  {c.contract_code} · {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="hub-sub" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            Site filter
            <select value={filterSiteId} onChange={(e) => setFilterSiteId(e.target.value)} disabled={sitesBusy || busy}>
              <option value="">(All)</option>
              {sites.map((s) => (
                <option value={s.id} key={s.id}>
                  {s.name} · {s.address_line1.slice(0, 28)}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="secondary" onClick={() => void loadSchedules()} disabled={busy}>
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

      <nav className="hub-toc" aria-label="PPM sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#ppm-list">Schedules</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#ppm-create">Create</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#ppm-edit">Edit</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#ppm-generate">Generate jobs</a>
        </div>
      </nav>

      <div id="ppm-list" className="card hub-panel hub-anchor">
        <h3>Schedules</h3>
        {schedulesState.error ? <div className="hub-err">{schedulesState.error}</div> : null}
        {!schedulesState.error && !schedules.length ? <div className="muted">No PPM schedules loaded.</div> : null}
        {schedules.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {schedules.map((s) => (
              <li key={s.id} style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  className={s.id === selectedScheduleId ? "" : "secondary"}
                  onClick={() => setSelectedScheduleId(s.id)}
                  style={{ textAlign: "left", width: "100%" }}
                >
                  <div>
                    <strong>{s.title}</strong> · {s.frequency_value} {s.frequency_unit}
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    due {String(s.next_due_date).slice(0, 16)} · {s.active ? "Active" : "Inactive"}
                    {s.asset_id ? ` · asset ${s.asset_id.slice(0, 8)}…` : " · all assets"}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div id="ppm-create" className="card hub-panel hub-anchor">
        <h3>Create schedule</h3>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>Contract</label>
            <select value={createForm.contract_id} onChange={(e) => setCreateForm((f) => ({ ...f, contract_id: e.target.value }))} disabled={contractsBusy || busy}>
              <option value="">Select contract</option>
              {contracts.map((c) => (
                <option value={c.id} key={c.id}>
                  {c.contract_code} · {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>Site</label>
            <select value={createForm.site_id} onChange={(e) => setCreateForm((f) => ({ ...f, site_id: e.target.value }))} disabled={sitesBusy || busy}>
              <option value="">Select site</option>
              {sites.map((s) => (
                <option value={s.id} key={s.id}>
                  {s.name} · {s.address_line1.slice(0, 28)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>Asset (optional)</label>
            <select
              value={createForm.asset_id}
              onChange={(e) => setCreateForm((f) => ({ ...f, asset_id: e.target.value }))}
              disabled={assetsBusy || busy || !createForm.site_id.trim()}
            >
              <option value="">All assets</option>
              {assets.map((a) => (
                <option value={a.id} key={a.id}>
                  {a.asset_code} · {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Title</label>
            <input value={createForm.title} onChange={(e) => setCreateForm((f) => ({ ...f, title: e.target.value }))} />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Frequency value</label>
            <input type="number" value={createForm.frequency_value} onChange={(e) => setCreateForm((f) => ({ ...f, frequency_value: Number(e.target.value) }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Frequency unit</label>
            <select value={createForm.frequency_unit} onChange={(e) => setCreateForm((f) => ({ ...f, frequency_unit: e.target.value }))} disabled={busy}>
              <option value="day">day</option>
              <option value="week">week</option>
              <option value="month">month</option>
              <option value="year">year</option>
            </select>
          </div>
        </div>

        <div className="field">
          <label>recurrence_rule (optional)</label>
          <textarea value={createForm.recurrence_rule} onChange={(e) => setCreateForm((f) => ({ ...f, recurrence_rule: e.target.value }))} />
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>next_due_date</label>
            <input
              type="datetime-local"
              value={createForm.next_due_date}
              onChange={(e) => setCreateForm((f) => ({ ...f, next_due_date: e.target.value }))}
              disabled={busy}
            />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 240 }}>
            <label>planning_window_days</label>
            <input
              type="number"
              value={createForm.planning_window_days}
              onChange={(e) => setCreateForm((f) => ({ ...f, planning_window_days: Number(e.target.value) }))}
              disabled={busy}
            />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 240 }}>
            <label>estimated_duration_minutes (optional)</label>
            <input
              type="number"
              value={createForm.estimated_duration_minutes}
              onChange={(e) => setCreateForm((f) => ({ ...f, estimated_duration_minutes: e.target.value }))}
            />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 240 }}>
            <label>Active</label>
            <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={createForm.active} onChange={(e) => setCreateForm((f) => ({ ...f, active: e.target.checked }))} />
              <span className="hub-sub">Generate jobs from active schedules</span>
            </div>
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>checklist_template_ref (optional)</label>
            <input value={createForm.checklist_template_ref} onChange={(e) => setCreateForm((f) => ({ ...f, checklist_template_ref: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>compliance_template_ref (optional)</label>
            <input value={createForm.compliance_template_ref} onChange={(e) => setCreateForm((f) => ({ ...f, compliance_template_ref: e.target.value }))} />
          </div>
        </div>

        <div className="field">
          <label>required_competencies_json</label>
          <textarea value={createForm.required_competencies_json} onChange={(e) => setCreateForm((f) => ({ ...f, required_competencies_json: e.target.value }))} />
        </div>

        <button type="button" onClick={() => void createSchedule()} disabled={busy}>
          {busy ? "Creating…" : "Create schedule"}
        </button>
      </div>

      <div id="ppm-edit" className="card hub-panel hub-anchor">
        <h3>Edit selected schedule</h3>
        {!selectedSchedule ? <div className="muted">Select a schedule from the list.</div> : null}

        {selectedSchedule ? (
          <>
            <div className="hint" style={{ marginTop: 10 }}>
              <strong>{selectedSchedule.title}</strong> · contract {selectedSchedule.contract_id.slice(0, 8)}… · site{" "}
              {selectedSchedule.site_id.slice(0, 8)}… {selectedSchedule.asset_id ? ` · asset ${selectedSchedule.asset_id.slice(0, 8)}…` : " · all assets"}
            </div>

            <div className="divider" />

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>Title</label>
                <input value={patchForm.title} onChange={(e) => setPatchForm((f) => ({ ...f, title: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Active</label>
                <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
                  <input type="checkbox" checked={patchForm.active} onChange={(e) => setPatchForm((f) => ({ ...f, active: e.target.checked }))} />
                  <span className="hub-sub">Disable stops future job creation</span>
                </div>
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Frequency value</label>
                <input type="number" value={patchForm.frequency_value} onChange={(e) => setPatchForm((f) => ({ ...f, frequency_value: Number(e.target.value) }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Frequency unit</label>
                <select value={patchForm.frequency_unit} onChange={(e) => setPatchForm((f) => ({ ...f, frequency_unit: e.target.value }))} disabled={busy}>
                  <option value="day">day</option>
                  <option value="week">week</option>
                  <option value="month">month</option>
                  <option value="year">year</option>
                </select>
              </div>
            </div>

            <div className="field">
              <label>recurrence_rule (optional)</label>
              <textarea value={patchForm.recurrence_rule} onChange={(e) => setPatchForm((f) => ({ ...f, recurrence_rule: e.target.value }))} />
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>next_due_date</label>
                <input
                  type="datetime-local"
                  value={patchForm.next_due_date}
                  onChange={(e) => setPatchForm((f) => ({ ...f, next_due_date: e.target.value }))}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 240 }}>
                <label>planning_window_days</label>
                <input
                  type="number"
                  value={patchForm.planning_window_days}
                  onChange={(e) => setPatchForm((f) => ({ ...f, planning_window_days: Number(e.target.value) }))}
                />
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 240 }}>
                <label>estimated_duration_minutes (optional)</label>
                <input
                  type="number"
                  value={patchForm.estimated_duration_minutes}
                  onChange={(e) => setPatchForm((f) => ({ ...f, estimated_duration_minutes: e.target.value }))}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>checklist_template_ref (optional)</label>
                <input value={patchForm.checklist_template_ref} onChange={(e) => setPatchForm((f) => ({ ...f, checklist_template_ref: e.target.value }))} />
              </div>
            </div>

            <div className="field">
              <label>compliance_template_ref (optional)</label>
              <input value={patchForm.compliance_template_ref} onChange={(e) => setPatchForm((f) => ({ ...f, compliance_template_ref: e.target.value }))} />
            </div>

            <div className="field">
              <label>required_competencies_json</label>
              <textarea value={patchForm.required_competencies_json} onChange={(e) => setPatchForm((f) => ({ ...f, required_competencies_json: e.target.value }))} />
            </div>

            <button type="button" className="secondary" disabled={busy} onClick={() => void patchSchedule()}>
              {busy ? "Saving…" : "Save changes"}
            </button>
          </>
        ) : null}
      </div>

      <div id="ppm-generate" className="card hub-panel hub-anchor">
        <h3>Generate jobs</h3>
        <div className="hint" style={{ marginTop: 8 }}>
          Triggers job creation for due active PPM schedules within the planning window.
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>run_date</label>
            <input type="datetime-local" value={runForm.run_date} onChange={(e) => setRunForm((f) => ({ ...f, run_date: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 240 }}>
            <label>planning_window_days</label>
            <input
              type="number"
              value={runForm.planning_window_days}
              onChange={(e) => setRunForm((f) => ({ ...f, planning_window_days: Number(e.target.value) }))}
            />
          </div>
        </div>
        <button type="button" className="secondary" onClick={() => void runGeneration()} disabled={runBusy}>
          {runBusy ? "Generating…" : "Generate PPM jobs"}
        </button>
      </div>
    </div>
  );
}

