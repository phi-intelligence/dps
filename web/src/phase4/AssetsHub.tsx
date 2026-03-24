import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type Customer = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
};

type Site = {
  id: string;
  customer_id: string;
  site_code: string;
  name: string;
  address_line1: string;
  address_line2: string | null;
  city: string | null;
  postcode: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  service_region: string | null;
  access_notes: string | null;
  billing_notes: string | null;
  site_contacts_json: string;
  active: boolean;
  created_at: string;
};

type Asset = {
  id: string;
  customer_id: string;
  site_id: string | null;
  contract_id: string | null;
  asset_code: string;
  asset_type: string;
  name: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  status: string;
  criticality: string;
  service_interval_value: number | null;
  service_interval_unit: string | null;
  last_service_date: string | null;
  next_service_date: string | null;
  notes: string | null;
  compliance_tags_json: string;
  required_competencies_json: string;
  location_address: string;
  next_maintenance_eta_at: string | null;
  created_at: string;
};

type MaintenanceSchedule = {
  id: string;
  asset_id: string;
  schedule_type: string;
  next_due_at: string;
  interval_days: number;
  notes: string | null;
  created_at: string;
};

type RunDueMaintenanceOut = {
  created_job_ids: string[];
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

export function AssetsHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customersBusy, setCustomersBusy] = useState(false);

  const [customerFilterId, setCustomerFilterId] = useState("");
  const [siteFilterId, setSiteFilterId] = useState("");

  const [sitesForCustomer, setSitesForCustomer] = useState<Site[]>([]);
  const [sitesBusy, setSitesBusy] = useState(false);

  const [assetsBusy, setAssetsBusy] = useState(false);
  const [assets, setAssets] = useState<Asset[]>([]);

  const [selectedAssetId, setSelectedAssetId] = useState("");
  const selectedAsset = useMemo(() => assets.find((a) => a.id === selectedAssetId) ?? null, [assets, selectedAssetId]);

  const [schedulesBusy, setSchedulesBusy] = useState(false);
  const [schedules, setSchedules] = useState<MaintenanceSchedule[]>([]);

  const dueSchedulesForSelectedAsset = useMemo(() => schedules.filter((s) => s.asset_id === selectedAssetId), [schedules, selectedAssetId]);

  const [createForm, setCreateForm] = useState({
    customer_id: "",
    site_id: "",
    contract_id: "",
    asset_code: "",
    asset_type: "equipment",
    name: "",
    manufacturer: "",
    model: "",
    serial_number: "",
    status: "in_service",
    criticality: "standard",
    service_interval_value: "",
    service_interval_unit: "months",
    location_address: "",
    next_maintenance_eta_at: "",
    notes: "",
    compliance_tags_json: "[]",
    required_competencies_json: "[]",
  });

  const [patchForm, setPatchForm] = useState({
    name: "",
    asset_code: "",
    status: "in_service",
    criticality: "standard",
    site_id: "",
    location_address: "",
    notes: "",
    compliance_tags_json: "[]",
    required_competencies_json: "[]",
  });

  const [newScheduleForm, setNewScheduleForm] = useState({
    next_due_at: new Date().toISOString().slice(0, 16),
    interval_days: 90,
    notes: "",
  });

  const loadCustomers = useCallback(async () => {
    setCustomersBusy(true);
    setErr(null);
    try {
      const rows = await fetchJson<Customer[]>(`${apiBase}/crm/customers?limit=100&offset=0`, authHeaders);
      setCustomers(rows);
      if (!customerFilterId && rows[0]?.id) setCustomerFilterId(String(rows[0].id));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setCustomers([]);
    } finally {
      setCustomersBusy(false);
    }
  }, [apiBase, authHeaders, customerFilterId]);

  const loadSitesForCustomer = useCallback(
    async (customerId: string) => {
      if (!customerId) {
        setSitesForCustomer([]);
        return;
      }
      setSitesBusy(true);
      setErr(null);
      try {
        const rows = await fetchJson<Site[]>(`${apiBase}/sites?customer_id=${encodeURIComponent(customerId)}`, authHeaders);
        setSitesForCustomer(rows);
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
        setSitesForCustomer([]);
      } finally {
        setSitesBusy(false);
      }
    },
    [apiBase, authHeaders],
  );

  const loadAssets = useCallback(async () => {
    setAssetsBusy(true);
    setErr(null);
    try {
      const q = new URLSearchParams();
      q.set("limit", "50");
      if (customerFilterId.trim()) q.set("customer_id", customerFilterId.trim());
      if (siteFilterId.trim()) q.set("site_id", siteFilterId.trim());
      const rows = await fetchJson<Asset[]>(`${apiBase}/assets?${q.toString()}`, authHeaders);
      setAssets(rows);
      if (!selectedAssetId && rows[0]?.id) setSelectedAssetId(rows[0].id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setAssets([]);
    } finally {
      setAssetsBusy(false);
    }
  }, [apiBase, authHeaders, customerFilterId, siteFilterId, selectedAssetId]);

  const refreshSchedules = useCallback(async () => {
    setSchedulesBusy(true);
    setErr(null);
    try {
      const rows = await fetchJson<MaintenanceSchedule[]>(`${apiBase}/assets/schedules`, authHeaders);
      setSchedules(rows);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setSchedules([]);
    } finally {
      setSchedulesBusy(false);
    }
  }, [apiBase, authHeaders]);

  const refreshAll = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      if (customerFilterId.trim()) {
        await loadSitesForCustomer(customerFilterId.trim());
      }
      await loadAssets();
      await refreshSchedules();
    } finally {
      setBusy(false);
    }
  }, [customerFilterId, loadAssets, loadSitesForCustomer, refreshSchedules]);

  useEffect(() => {
    void loadCustomers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!customerFilterId.trim()) return;
    void loadSitesForCustomer(customerFilterId.trim());
  }, [customerFilterId, loadSitesForCustomer]);

  useEffect(() => {
    void loadAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerFilterId, siteFilterId]);

  useEffect(() => {
    if (!successBanner) return;
    const t = window.setTimeout(() => setSuccessBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [successBanner]);

  useEffect(() => {
    if (!selectedAsset) return;
    setPatchForm({
      name: selectedAsset.name ?? "",
      asset_code: selectedAsset.asset_code ?? "",
      status: selectedAsset.status ?? "in_service",
      criticality: selectedAsset.criticality ?? "standard",
      site_id: selectedAsset.site_id ?? "",
      location_address: selectedAsset.location_address ?? "",
      notes: selectedAsset.notes ?? "",
      compliance_tags_json: selectedAsset.compliance_tags_json ?? "[]",
      required_competencies_json: selectedAsset.required_competencies_json ?? "[]",
    });
    void refreshSchedules();
  }, [selectedAssetId]); // eslint-disable-line react-hooks/exhaustive-deps

  const createAsset = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      if (!createForm.customer_id.trim()) throw new Error("Select a customer.");
      if (!createForm.asset_type.trim()) throw new Error("asset_type is required.");
      if (!createForm.name.trim()) throw new Error("Asset name is required.");
      if (!createForm.location_address.trim()) throw new Error("location_address is required.");

      const toIntOrNull = (v: string) => {
        const t = v.trim();
        if (!t) return null;
        const n = Number(t);
        return Number.isFinite(n) ? n : null;
      };

      await postJson<Asset>(`${apiBase}/assets`, authHeaders, {
        customer_id: createForm.customer_id.trim(),
        site_id: createForm.site_id.trim() || null,
        contract_id: createForm.contract_id.trim() || null,
        asset_code: createForm.asset_code.trim() || null,
        asset_type: createForm.asset_type.trim(),
        name: createForm.name.trim(),
        manufacturer: createForm.manufacturer.trim() || null,
        model: createForm.model.trim() || null,
        serial_number: createForm.serial_number.trim() || null,
        status: createForm.status,
        criticality: createForm.criticality,
        service_interval_value: toIntOrNull(createForm.service_interval_value),
        service_interval_unit: createForm.service_interval_value.trim() ? createForm.service_interval_unit : null,
        notes: createForm.notes.trim() || null,
        compliance_tags_json: createForm.compliance_tags_json.trim() || "[]",
        required_competencies_json: createForm.required_competencies_json.trim() || "[]",
        location_address: createForm.location_address.trim(),
        next_maintenance_eta_at: createForm.next_maintenance_eta_at.trim() ? new Date(createForm.next_maintenance_eta_at.trim()).toISOString() : null,
      });

      setSuccessBanner("Asset created.");
      setCreateForm((f) => ({ ...f, asset_code: "", name: "", manufacturer: "", model: "", serial_number: "", location_address: "", notes: "" }));
      await loadAssets();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, createForm, loadAssets]);

  const patchSelectedAsset = useCallback(async () => {
    if (!selectedAssetId) return;
    setBusy(true);
    setErr(null);
    try {
      if (!patchForm.name.trim()) throw new Error("Asset name is required.");
      if (!patchForm.location_address.trim()) throw new Error("location_address is required.");

      await patchJson<Asset>(`${apiBase}/assets/${encodeURIComponent(selectedAssetId)}`, authHeaders, {
        name: patchForm.name.trim(),
        asset_code: patchForm.asset_code.trim() || null,
        status: patchForm.status,
        criticality: patchForm.criticality,
        site_id: patchForm.site_id.trim() || null,
        location_address: patchForm.location_address.trim(),
        notes: patchForm.notes.trim() || null,
        compliance_tags_json: patchForm.compliance_tags_json.trim() || "[]",
        required_competencies_json: patchForm.required_competencies_json.trim() || "[]",
      });

      setSuccessBanner("Asset updated.");
      await loadAssets();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadAssets, patchForm, selectedAssetId]);

  const createMaintenanceSchedule = useCallback(async () => {
    if (!selectedAssetId) return;
    setBusy(true);
    setErr(null);
    try {
      const toIso = (s: string) => {
        const t = s.trim();
        if (!t) return null;
        const d = new Date(t);
        return d.toISOString();
      };
      const nextDueIso = toIso(newScheduleForm.next_due_at);
      if (!nextDueIso) throw new Error("next_due_at is required.");
      if (!(newScheduleForm.interval_days > 0)) throw new Error("interval_days must be > 0.");

      await postJson<unknown>(`${apiBase}/assets/${encodeURIComponent(selectedAssetId)}/schedules`, authHeaders, {
        asset_id: selectedAssetId,
        schedule_type: "date",
        next_due_at: nextDueIso,
        interval_days: Number(newScheduleForm.interval_days),
        notes: newScheduleForm.notes.trim() || null,
      });
      setSuccessBanner("Maintenance schedule created.");
      await refreshSchedules();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, newScheduleForm, refreshSchedules, selectedAssetId]);

  const runDueMaintenance = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const out = await postJson<RunDueMaintenanceOut>(`${apiBase}/assets/maintenance/run-due`, authHeaders, {});
      setSuccessBanner(out.created_job_ids.length ? `Maintenance triggered: ${out.created_job_ids.length} jobs.` : "No maintenance due.");
      await loadAssets();
      await refreshSchedules();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadAssets, refreshSchedules]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Assets</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Create and maintain asset records, with optional maintenance schedules and a run-due button.
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <button type="button" className="secondary" onClick={() => void refreshAll()} disabled={busy}>
            {busy ? "Refreshing…" : "Refresh"}
          </button>
          <button type="button" className="secondary" onClick={() => void refreshSchedules()} disabled={schedulesBusy}>
            {schedulesBusy ? "Loading schedules…" : "Refresh schedules"}
          </button>
          <button type="button" onClick={() => void runDueMaintenance()} disabled={busy}>
            {busy ? "Working…" : "Run due maintenance"}
          </button>
        </div>
        {successBanner ? (
          <div style={{ marginTop: 10, padding: "10px 16px", borderRadius: 8, border: "1px solid rgba(34,197,94,0.35)", background: "rgba(34,197,94,0.15)", color: "#86efac" }}>
            {successBanner}
          </div>
        ) : null}
        {err ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{err}</div> : null}
      </div>

      <nav className="hub-toc" aria-label="Assets sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#assets-list">Assets list</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#assets-create">Create</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#assets-details">Selected asset</a>
        </div>
      </nav>

      <div id="assets-list" className="card hub-panel hub-anchor">
        <h3>Assets</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <select
            style={{ width: "100%", maxWidth: 420 }}
            value={customerFilterId}
            onChange={(e) => setCustomerFilterId(e.target.value)}
            disabled={customersBusy || !customers.length}
          >
            <option value="">Filter: all customers</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.email ? `(${c.email})` : ""}
              </option>
            ))}
          </select>
          <select
            style={{ width: "100%", maxWidth: 420 }}
            value={siteFilterId}
            onChange={(e) => setSiteFilterId(e.target.value)}
            disabled={sitesBusy || !sitesForCustomer.length}
          >
            <option value="">Filter: all sites</option>
            {sitesForCustomer.map((s) => (
              <option key={s.id} value={s.id}>
                {s.site_code} · {s.name}
              </option>
            ))}
          </select>
        </div>
        {assetsBusy ? <div className="muted" style={{ marginTop: 8 }}>Loading assets…</div> : null}
        {!assetsBusy && assets.length === 0 ? <div className="muted" style={{ marginTop: 8 }}>No assets loaded.</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 12 }}>
          {assets.map((a) => (
            <li key={a.id} style={{ marginBottom: 10 }}>
              <button
                type="button"
                className={a.id === selectedAssetId ? "" : "secondary"}
                onClick={() => setSelectedAssetId(a.id)}
                style={{ textAlign: "left", width: "100%" }}
              >
                <div>
                  <strong>{a.asset_code}</strong> · {a.name}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  {a.status} · {a.criticality} · {a.asset_type} {a.site_id ? `· site ${String(a.site_id).slice(0, 8)}…` : ""}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div id="assets-create" className="card hub-panel hub-anchor">
        <h3>Create asset</h3>
        <div className="field">
          <label>Customer</label>
          <select
            value={createForm.customer_id}
            onChange={(e) => setCreateForm((f) => ({ ...f, customer_id: e.target.value }))}
            style={{ width: "100%", maxWidth: 480 }}
          >
            <option value="">Select customer…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.email ? `(${c.email})` : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Site (optional)</label>
          <select
            value={createForm.site_id}
            onChange={(e) => setCreateForm((f) => ({ ...f, site_id: e.target.value }))}
            style={{ width: "100%", maxWidth: 480 }}
            disabled={!createForm.customer_id || sitesForCustomer.length === 0}
          >
            <option value="">— none —</option>
            {sitesForCustomer.map((s) => (
              <option key={s.id} value={s.id}>
                {s.site_code} · {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>asset_type</label>
            <input value={createForm.asset_type} onChange={(e) => setCreateForm((f) => ({ ...f, asset_type: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Asset code (optional)</label>
            <input value={createForm.asset_code} onChange={(e) => setCreateForm((f) => ({ ...f, asset_code: e.target.value }))} placeholder="optional" />
          </div>
        </div>
        <div className="field">
          <label>Name</label>
          <input value={createForm.name} onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))} placeholder="e.g. Boiler Unit 1" />
        </div>
        <div className="field">
          <label>location_address</label>
          <input value={createForm.location_address} onChange={(e) => setCreateForm((f) => ({ ...f, location_address: e.target.value }))} placeholder="service address / location" />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Status</label>
            <input value={createForm.status} onChange={(e) => setCreateForm((f) => ({ ...f, status: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Criticality</label>
            <input value={createForm.criticality} onChange={(e) => setCreateForm((f) => ({ ...f, criticality: e.target.value }))} />
          </div>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Manufacturer</label>
            <input value={createForm.manufacturer} onChange={(e) => setCreateForm((f) => ({ ...f, manufacturer: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Model</label>
            <input value={createForm.model} onChange={(e) => setCreateForm((f) => ({ ...f, model: e.target.value }))} />
          </div>
        </div>
        <div className="field">
          <label>Serial number</label>
          <input value={createForm.serial_number} onChange={(e) => setCreateForm((f) => ({ ...f, serial_number: e.target.value }))} />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Service interval value (optional)</label>
            <input type="number" value={createForm.service_interval_value} onChange={(e) => setCreateForm((f) => ({ ...f, service_interval_value: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>Service interval unit</label>
            <input value={createForm.service_interval_unit} onChange={(e) => setCreateForm((f) => ({ ...f, service_interval_unit: e.target.value }))} />
          </div>
        </div>
        <div className="field">
          <label>Notes (optional)</label>
          <textarea value={createForm.notes} onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))} />
        </div>
        <button type="button" onClick={() => void createAsset()} disabled={busy || !createForm.customer_id.trim()}>
          {busy ? "Working…" : "Create asset"}
        </button>
      </div>

      <div id="assets-details" className="card hub-panel hub-anchor">
        <h3>Selected asset</h3>
        {!selectedAsset ? <div className="muted">Select an asset from the list.</div> : null}
        {selectedAsset ? (
          <>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Asset code</label>
                <input value={patchForm.asset_code} onChange={(e) => setPatchForm((p) => ({ ...p, asset_code: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 2, minWidth: 260 }}>
                <label>Name</label>
                <input value={patchForm.name} onChange={(e) => setPatchForm((p) => ({ ...p, name: e.target.value }))} />
              </div>
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Status</label>
                <input value={patchForm.status} onChange={(e) => setPatchForm((p) => ({ ...p, status: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Criticality</label>
                <input value={patchForm.criticality} onChange={(e) => setPatchForm((p) => ({ ...p, criticality: e.target.value }))} />
              </div>
            </div>
            <div className="field">
              <label>Site (optional)</label>
              <select
                value={patchForm.site_id}
                onChange={(e) => setPatchForm((p) => ({ ...p, site_id: e.target.value }))}
                style={{ width: "100%", maxWidth: 480 }}
              >
                <option value="">— none —</option>
                {sitesForCustomer.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.site_code} · {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>location_address</label>
              <input value={patchForm.location_address} onChange={(e) => setPatchForm((p) => ({ ...p, location_address: e.target.value }))} />
            </div>
            <div className="field">
              <label>Notes</label>
              <textarea value={patchForm.notes} onChange={(e) => setPatchForm((p) => ({ ...p, notes: e.target.value }))} />
            </div>
            <button type="button" className="secondary" disabled={busy} onClick={() => void patchSelectedAsset()}>
              {busy ? "Saving…" : "Save asset"}
            </button>

            <div className="divider" />
            <h4 style={{ fontSize: 13, marginTop: 0 }}>Maintenance schedules</h4>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <button type="button" className="secondary" onClick={() => void refreshSchedules()} disabled={schedulesBusy}>
                {schedulesBusy ? "Loading…" : "Refresh schedules"}
              </button>
            </div>
            {dueSchedulesForSelectedAsset.length === 0 && !schedulesBusy ? (
              <div className="muted" style={{ marginTop: 8 }}>No schedules for this asset.</div>
            ) : null}
            <ul className="hub-list-compact" style={{ marginTop: 10 }}>
              {dueSchedulesForSelectedAsset.slice(0, 10).map((s) => (
                <li key={s.id} style={{ marginBottom: 10 }}>
                  <div>
                    <strong>{s.schedule_type}</strong> · due {s.next_due_at ? String(s.next_due_at).slice(0, 16) : "—"} · every{" "}
                    {s.interval_days}d
                  </div>
                  {s.notes ? <div className="hub-sub" style={{ marginTop: 2 }}>{s.notes}</div> : null}
                </li>
              ))}
            </ul>

            <div className="divider" />
            <h4 style={{ fontSize: 13, marginTop: 0 }}>Add schedule</h4>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>next_due_at</label>
                <input type="datetime-local" value={newScheduleForm.next_due_at} onChange={(e) => setNewScheduleForm((f) => ({ ...f, next_due_at: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 160 }}>
                <label>interval_days</label>
                <input type="number" value={newScheduleForm.interval_days} onChange={(e) => setNewScheduleForm((f) => ({ ...f, interval_days: Number(e.target.value) }))} />
              </div>
            </div>
            <div className="field">
              <label>Notes (optional)</label>
              <input value={newScheduleForm.notes} onChange={(e) => setNewScheduleForm((f) => ({ ...f, notes: e.target.value }))} />
            </div>
            <button type="button" disabled={busy} onClick={() => void createMaintenanceSchedule()}>
              {busy ? "Creating…" : "Create schedule"}
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}

