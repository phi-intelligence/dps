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
  location_address: string;
  next_maintenance_eta_at: string | null;
  created_at: string;
};

type SiteJobsSummary = {
  site_id: string;
  open_count: number;
  jobs: {
    id: string;
    status: string;
    work_type: string;
    contract_id: string | null;
    created_at: string;
  }[];
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

export function SitesHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customersBusy, setCustomersBusy] = useState(false);
  const [customerFilterId, setCustomerFilterId] = useState("");

  const [sites, setSites] = useState<Site[]>([]);
  const [sitesBusy, setSitesBusy] = useState(false);

  const [selectedSiteId, setSelectedSiteId] = useState<string>("");
  const selectedSite = useMemo(() => sites.find((s) => s.id === selectedSiteId) ?? null, [sites, selectedSiteId]);

  const [sitePatch, setSitePatch] = useState({
    site_code: "",
    name: "",
    address_line1: "",
    address_line2: "",
    city: "",
    postcode: "",
    country: "",
    latitude: "",
    longitude: "",
    service_region: "",
    access_notes: "",
    billing_notes: "",
    site_contacts_json: "[]",
    active: true,
  });

  const [siteAssetsBusy, setSiteAssetsBusy] = useState(false);
  const [siteAssets, setSiteAssets] = useState<Asset[]>([]);
  const [siteJobsBusy, setSiteJobsBusy] = useState(false);
  const [siteJobs, setSiteJobs] = useState<SiteJobsSummary | null>(null);

  const [createForm, setCreateForm] = useState({
    customer_id: "",
    site_code: "",
    name: "",
    address_line1: "",
    address_line2: "",
    city: "",
    postcode: "",
    country: "",
    latitude: "",
    longitude: "",
    service_region: "",
    access_notes: "",
    billing_notes: "",
    site_contacts_json: "[]",
    active: true,
  });

  const loadCustomers = useCallback(async () => {
    setCustomersBusy(true);
    setErr(null);
    try {
      const rows = await fetchJson<Customer[]>(`${apiBase}/crm/customers?limit=100&offset=0`, authHeaders);
      setCustomers(rows);
      if (!customerFilterId && rows[0]?.id) setCustomerFilterId(rows[0].id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setCustomers([]);
    } finally {
      setCustomersBusy(false);
    }
  }, [apiBase, authHeaders, customerFilterId]);

  const loadSites = useCallback(async () => {
    setSitesBusy(true);
    setErr(null);
    try {
      const q = customerFilterId.trim() ? `?customer_id=${encodeURIComponent(customerFilterId.trim())}` : "";
      const rows = await fetchJson<Site[]>(`${apiBase}/sites${q}`, authHeaders);
      setSites(rows);
      if (!selectedSiteId && rows[0]?.id) setSelectedSiteId(rows[0].id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setSites([]);
    } finally {
      setSitesBusy(false);
    }
  }, [apiBase, authHeaders, customerFilterId, selectedSiteId]);

  const loadSiteAssets = useCallback(async (siteId: string) => {
    setSiteAssetsBusy(true);
    setErr(null);
    try {
      const rows = await fetchJson<Asset[]>(`${apiBase}/sites/${encodeURIComponent(siteId)}/assets`, authHeaders);
      setSiteAssets(rows);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setSiteAssets([]);
    } finally {
      setSiteAssetsBusy(false);
    }
  }, [apiBase, authHeaders]);

  const loadSiteJobs = useCallback(async (siteId: string) => {
    setSiteJobsBusy(true);
    setErr(null);
    try {
      const row = await fetchJson<SiteJobsSummary>(`${apiBase}/sites/${encodeURIComponent(siteId)}/jobs`, authHeaders);
      setSiteJobs(row);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setSiteJobs(null);
    } finally {
      setSiteJobsBusy(false);
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    void loadCustomers();
    // Intentionally only on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!customerFilterId) return;
    void loadSites();
  }, [customerFilterId, loadSites]);

  useEffect(() => {
    if (!selectedSiteId) return;
    if (!selectedSite) return;
    setSitePatch({
      site_code: selectedSite.site_code ?? "",
      name: selectedSite.name ?? "",
      address_line1: selectedSite.address_line1 ?? "",
      address_line2: selectedSite.address_line2 ?? "",
      city: selectedSite.city ?? "",
      postcode: selectedSite.postcode ?? "",
      country: selectedSite.country ?? "",
      latitude: selectedSite.latitude != null ? String(selectedSite.latitude) : "",
      longitude: selectedSite.longitude != null ? String(selectedSite.longitude) : "",
      service_region: selectedSite.service_region ?? "",
      access_notes: selectedSite.access_notes ?? "",
      billing_notes: selectedSite.billing_notes ?? "",
      site_contacts_json: selectedSite.site_contacts_json ?? "[]",
      active: selectedSite.active ?? true,
    });
    void loadSiteAssets(selectedSiteId);
    void loadSiteJobs(selectedSiteId);
  }, [selectedSiteId, selectedSite, loadSiteAssets, loadSiteJobs]);

  const refreshAll = useCallback(async () => {
    setBusy(true);
    try {
      await loadSites();
      if (selectedSiteId) {
        void loadSiteAssets(selectedSiteId);
        void loadSiteJobs(selectedSiteId);
      }
    } finally {
      setBusy(false);
    }
  }, [loadSites, loadSiteAssets, loadSiteJobs, selectedSiteId]);

  useEffect(() => {
    if (!successBanner) return;
    const t = window.setTimeout(() => setSuccessBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [successBanner]);

  const createSite = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      if (!createForm.customer_id.trim()) throw new Error("Select a customer.");
      if (!createForm.site_code.trim()) throw new Error("Site code is required.");
      if (!createForm.name.trim()) throw new Error("Site name is required.");
      if (!createForm.address_line1.trim()) throw new Error("Address line 1 is required.");

      const toNum = (v: string) => {
        const t = v.trim();
        if (!t) return null;
        const n = Number(t);
        return Number.isFinite(n) ? n : null;
      };

      await postJson<Site>(`${apiBase}/sites`, authHeaders, {
        customer_id: createForm.customer_id.trim(),
        site_code: createForm.site_code.trim(),
        name: createForm.name.trim(),
        address_line1: createForm.address_line1.trim(),
        address_line2: createForm.address_line2.trim() || null,
        city: createForm.city.trim() || null,
        postcode: createForm.postcode.trim() || null,
        country: createForm.country.trim() || null,
        latitude: toNum(createForm.latitude),
        longitude: toNum(createForm.longitude),
        service_region: createForm.service_region.trim() || null,
        access_notes: createForm.access_notes.trim() || null,
        billing_notes: createForm.billing_notes.trim() || null,
        site_contacts_json: createForm.site_contacts_json.trim() || "[]",
        active: createForm.active,
      });
      setSuccessBanner("Site created.");
      setCreateForm({
        customer_id: createForm.customer_id,
        site_code: "",
        name: "",
        address_line1: "",
        address_line2: "",
        city: "",
        postcode: "",
        country: "",
        latitude: "",
        longitude: "",
        service_region: "",
        access_notes: "",
        billing_notes: "",
        site_contacts_json: "[]",
        active: true,
      });
      await loadSites();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, createForm, loadSites]);

  const patchSite = useCallback(async () => {
    if (!selectedSiteId) return;
    setBusy(true);
    setErr(null);
    try {
      const toNumOrNull = (v: string) => {
        const t = v.trim();
        if (!t) return null;
        const n = Number(t);
        return Number.isFinite(n) ? n : null;
      };
      await patchJson<Site>(`${apiBase}/sites/${encodeURIComponent(selectedSiteId)}`, authHeaders, {
        site_code: sitePatch.site_code.trim() || null,
        name: sitePatch.name.trim() || null,
        address_line1: sitePatch.address_line1.trim() || null,
        address_line2: sitePatch.address_line2.trim() || null,
        city: sitePatch.city.trim() || null,
        postcode: sitePatch.postcode.trim() || null,
        country: sitePatch.country.trim() || null,
        latitude: toNumOrNull(sitePatch.latitude),
        longitude: toNumOrNull(sitePatch.longitude),
        service_region: sitePatch.service_region.trim() || null,
        access_notes: sitePatch.access_notes.trim() || null,
        billing_notes: sitePatch.billing_notes.trim() || null,
        site_contacts_json: sitePatch.site_contacts_json.trim() || "[]",
        active: sitePatch.active,
      });
      setSuccessBanner("Site updated.");
      await loadSites();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadSites, selectedSiteId, sitePatch]);

  const hasLatLon = selectedSite?.latitude != null && selectedSite?.longitude != null;

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Sites</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Create and manage customer sites. This panel also shows site-linked assets and open job summaries.
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <button type="button" className="secondary" onClick={() => void refreshAll()} disabled={busy || sitesBusy}>
            {busy ? "Refreshing…" : "Refresh"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadCustomers()} disabled={customersBusy}>
            {customersBusy ? "Loading customers…" : "Load customers"}
          </button>
        </div>
        {successBanner ? (
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
            {successBanner}
          </div>
        ) : null}
        {err ? (
          <div style={{ marginTop: 10, color: "#ffb4b4" }}>
            {err}
          </div>
        ) : null}
      </div>

      <nav className="hub-toc" aria-label="Sites sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#sites-list">Sites list</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#sites-create">Create</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#sites-details">Selected site</a>
        </div>
      </nav>

      <div id="sites-list" className="card hub-panel hub-anchor">
        <h3>Sites</h3>
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
          <button type="button" className="secondary" onClick={() => void loadSites()} disabled={sitesBusy}>
            {sitesBusy ? "Loading…" : "Load sites"}
          </button>
        </div>
        {sitesBusy ? <div className="muted" style={{ marginTop: 8 }}>Loading sites…</div> : null}
        {!sitesBusy && sites.length === 0 ? <div className="muted" style={{ marginTop: 8 }}>No sites loaded.</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 12 }}>
          {sites.map((s) => (
            <li key={s.id} style={{ marginBottom: 10 }}>
              <button
                type="button"
                className={s.id === selectedSiteId ? "" : "secondary"}
                onClick={() => setSelectedSiteId(s.id)}
                style={{ textAlign: "left", width: "100%" }}
              >
                <div>
                  <strong>{s.site_code}</strong> · {s.name}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  {s.active ? "Active" : "Inactive"} · {s.address_line1.slice(0, 60)}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div id="sites-create" className="card hub-panel hub-anchor">
        <h3>Create site</h3>
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
          <label>Site code</label>
          <input value={createForm.site_code} onChange={(e) => setCreateForm((f) => ({ ...f, site_code: e.target.value }))} placeholder="e.g. OPS_NORTH_01" />
        </div>
        <div className="field">
          <label>Site name</label>
          <input value={createForm.name} onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))} placeholder="Human-friendly site name" />
        </div>
        <div className="field">
          <label>Address line 1</label>
          <input value={createForm.address_line1} onChange={(e) => setCreateForm((f) => ({ ...f, address_line1: e.target.value }))} placeholder="Street address" />
        </div>
        <div className="field">
          <label>Address line 2 (optional)</label>
          <input value={createForm.address_line2} onChange={(e) => setCreateForm((f) => ({ ...f, address_line2: e.target.value }))} />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>City</label>
            <input value={createForm.city} onChange={(e) => setCreateForm((f) => ({ ...f, city: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 160 }}>
            <label>Postcode</label>
            <input value={createForm.postcode} onChange={(e) => setCreateForm((f) => ({ ...f, postcode: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 160 }}>
            <label>Country</label>
            <input value={createForm.country} onChange={(e) => setCreateForm((f) => ({ ...f, country: e.target.value }))} />
          </div>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>Latitude (optional)</label>
            <input type="number" value={createForm.latitude} onChange={(e) => setCreateForm((f) => ({ ...f, latitude: e.target.value }))} step="any" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>Longitude (optional)</label>
            <input type="number" value={createForm.longitude} onChange={(e) => setCreateForm((f) => ({ ...f, longitude: e.target.value }))} step="any" />
          </div>
        </div>
        <div className="field">
          <label>Service region (optional)</label>
          <input value={createForm.service_region} onChange={(e) => setCreateForm((f) => ({ ...f, service_region: e.target.value }))} />
        </div>
        <div className="field">
          <label>Access notes (optional)</label>
          <textarea value={createForm.access_notes} onChange={(e) => setCreateForm((f) => ({ ...f, access_notes: e.target.value }))} />
        </div>
        <div className="field">
          <label>Billing notes (optional)</label>
          <textarea value={createForm.billing_notes} onChange={(e) => setCreateForm((f) => ({ ...f, billing_notes: e.target.value }))} />
        </div>
        <div className="field">
          <label>Site contacts JSON (required by API, default [])</label>
          <textarea value={createForm.site_contacts_json} onChange={(e) => setCreateForm((f) => ({ ...f, site_contacts_json: e.target.value }))} />
        </div>
        <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={createForm.active} onChange={(e) => setCreateForm((f) => ({ ...f, active: e.target.checked }))} />
          <label>Active</label>
        </div>
        <button type="button" onClick={() => void createSite()} disabled={busy || !createForm.customer_id.trim()}>
          {busy ? "Creating…" : "Create site"}
        </button>
      </div>

      <div id="sites-details" className="card hub-panel hub-anchor">
        <h3>Selected site</h3>
        {!selectedSite ? <div className="muted">Pick a site from the list.</div> : null}
        {selectedSite ? (
          <>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              {hasLatLon ? (
                <a
                  className="secondary"
                  href={`https://www.openstreetmap.org/?mlat=${selectedSite.latitude}&mlon=${selectedSite.longitude}#map=13/${selectedSite.latitude}/${selectedSite.longitude}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open coordinates in map
                </a>
              ) : (
                <span className="muted">No coordinates on this site.</span>
              )}
              <button type="button" className="secondary" onClick={() => void patchSite()} disabled={busy}>
                {busy ? "Saving…" : "Save updates"}
              </button>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 12 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Site code</label>
                <input value={sitePatch.site_code} onChange={(e) => setSitePatch((p) => ({ ...p, site_code: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 2, minWidth: 260 }}>
                <label>Site name</label>
                <input value={sitePatch.name} onChange={(e) => setSitePatch((p) => ({ ...p, name: e.target.value }))} />
              </div>
            </div>

            <div className="field">
              <label>Address line 1</label>
              <input value={sitePatch.address_line1} onChange={(e) => setSitePatch((p) => ({ ...p, address_line1: e.target.value }))} />
            </div>
            <div className="field">
              <label>Address line 2 (optional)</label>
              <input value={sitePatch.address_line2} onChange={(e) => setSitePatch((p) => ({ ...p, address_line2: e.target.value }))} />
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>City</label>
                <input value={sitePatch.city} onChange={(e) => setSitePatch((p) => ({ ...p, city: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 160 }}>
                <label>Postcode</label>
                <input value={sitePatch.postcode} onChange={(e) => setSitePatch((p) => ({ ...p, postcode: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 160 }}>
                <label>Country</label>
                <input value={sitePatch.country} onChange={(e) => setSitePatch((p) => ({ ...p, country: e.target.value }))} />
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>Latitude (optional)</label>
                <input type="number" value={sitePatch.latitude} onChange={(e) => setSitePatch((p) => ({ ...p, latitude: e.target.value }))} step="any" />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>Longitude (optional)</label>
                <input type="number" value={sitePatch.longitude} onChange={(e) => setSitePatch((p) => ({ ...p, longitude: e.target.value }))} step="any" />
              </div>
            </div>

            <div className="field">
              <label>Service region (optional)</label>
              <input value={sitePatch.service_region} onChange={(e) => setSitePatch((p) => ({ ...p, service_region: e.target.value }))} />
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Access notes</label>
                <textarea value={sitePatch.access_notes} onChange={(e) => setSitePatch((p) => ({ ...p, access_notes: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>Billing notes</label>
                <textarea value={sitePatch.billing_notes} onChange={(e) => setSitePatch((p) => ({ ...p, billing_notes: e.target.value }))} />
              </div>
            </div>

            <div className="field">
              <label>Site contacts JSON</label>
              <textarea value={sitePatch.site_contacts_json} onChange={(e) => setSitePatch((p) => ({ ...p, site_contacts_json: e.target.value }))} />
            </div>

            <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input type="checkbox" checked={sitePatch.active} onChange={(e) => setSitePatch((p) => ({ ...p, active: e.target.checked }))} />
              <label>Active</label>
            </div>

            <div className="divider" />
            <h4 style={{ fontSize: 13, marginTop: 0 }}>Site assets</h4>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 6 }}>
              <button type="button" className="secondary" onClick={() => void loadSiteAssets(selectedSiteId)} disabled={siteAssetsBusy}>
                {siteAssetsBusy ? "Loading…" : "Refresh assets"}
              </button>
            </div>
            {siteAssetsBusy ? <div className="muted" style={{ marginTop: 6 }}>Loading assets…</div> : null}
            {siteAssets.length === 0 && !siteAssetsBusy ? <div className="muted" style={{ marginTop: 6 }}>No assets found.</div> : null}
            <ul className="hub-list-compact" style={{ marginTop: 10 }}>
              {siteAssets.slice(0, 25).map((a) => (
                <li key={a.id} style={{ marginBottom: 10 }}>
                  <div>
                    <strong>{a.asset_code}</strong> · {a.asset_type}
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    {a.name || "—"} · {a.status} · criticality {a.criticality}
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    {a.location_address || "—"}
                  </div>
                </li>
              ))}
            </ul>

            <div className="divider" />
            <h4 style={{ fontSize: 13, marginTop: 0 }}>Site jobs</h4>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 6 }}>
              <button type="button" className="secondary" onClick={() => void loadSiteJobs(selectedSiteId)} disabled={siteJobsBusy}>
                {siteJobsBusy ? "Loading…" : "Refresh jobs"}
              </button>
            </div>
            {siteJobsBusy ? <div className="muted" style={{ marginTop: 6 }}>Loading jobs…</div> : null}
            {!siteJobsBusy && siteJobs ? (
              <>
                <div className="hub-sub" style={{ marginTop: 6 }}>
                  Open jobs: {siteJobs.open_count}
                </div>
                <ul className="hub-list-compact" style={{ marginTop: 10 }}>
                  {siteJobs.jobs.slice(0, 25).map((j) => (
                    <li key={j.id} style={{ marginBottom: 10 }}>
                      <div>
                        <strong>{j.status}</strong> · {j.work_type}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        {j.contract_id ? `Contract ${String(j.contract_id).slice(0, 8)}…` : "No contract"} · created {j.created_at ? String(j.created_at).slice(0, 16) : "—"}
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

