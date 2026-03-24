import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type MeOut = {
  id: string;
  email: string;
  roles: { id: string; name: string }[];
};

type VehicleInspectionItemOut = {
  id: string;
  inspection_id: string;
  item_code: string;
  item_label: string;
  result: string;
  notes: string | null;
  photo_document_id: string | null;
  fail_criticality: string;
};

type VehicleInspectionOut = {
  id: string;
  vehicle_id: string;
  engineer_id: string;
  inspection_date: string; // date
  performed_at: string; // datetime
  odometer: number | null;
  latitude: number | null;
  longitude: number | null;
  overall_status: string;
  notes: string | null;
  created_at: string;
  items: VehicleInspectionItemOut[];
};

type VehicleDefectOut = {
  id: string;
  vehicle_id: string;
  inspection_id: string | null;
  defect_type: string;
  severity: string;
  title: string;
  description: string | null;
  status: string;
  reported_at: string;
  reported_by_user_id: string | null;
  resolved_at: string | null;
  resolved_by_user_id: string | null;
  resolution_notes: string | null;
};

type InspectionAttentionDashboardOut = {
  attention_count: number;
  items: { [k: string]: unknown }[];
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

function datetimeLocalToIso(v: string): string {
  return new Date(v).toISOString();
}

export function VehiclesHub({ apiBase, authHeaders }: Props) {
  const [me, setMe] = useState<MeOut | null>(null);

  const [busyAttention, setBusyAttention] = useState(false);
  const [attention, setAttention] = useState<InspectionAttentionDashboardOut | null>(null);
  const [attentionErr, setAttentionErr] = useState<string | null>(null);

  const [vehicleId, setVehicleId] = useState("");

  const [busyInspections, setBusyInspections] = useState(false);
  const [inspections, setInspections] = useState<VehicleInspectionOut[]>([]);
  const [latestInspection, setLatestInspection] = useState<VehicleInspectionOut | null>(null);
  const [inspectionsErr, setInspectionsErr] = useState<string | null>(null);

  const [busyDefects, setBusyDefects] = useState(false);
  const [defects, setDefects] = useState<VehicleDefectOut[]>([]);
  const [defectsErr, setDefectsErr] = useState<string | null>(null);
  const [defectStatus, setDefectStatus] = useState<string>(""); // query: status

  const [selectedDefectId, setSelectedDefectId] = useState<string>("");
  const selectedDefect = useMemo(
    () => (selectedDefectId ? defects.find((d) => d.id === selectedDefectId) ?? null : null),
    [defects, selectedDefectId],
  );

  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const isEngineer = Boolean(me?.roles?.some((r) => r.name === "Engineer"));

  const [inspectionForm, setInspectionForm] = useState({
    engineer_id: "",
    performed_at: "",
    inspection_date: "",
    odometer: "",
    latitude: "",
    longitude: "",
    overall_status: "",
    notes: "",
    items: [
      {
        item_code: "",
        item_label: "",
        result: "pass",
        notes: "",
        photo_document_id: "",
        fail_criticality: "minor",
      },
    ],
  });

  const [defectCreateForm, setDefectCreateForm] = useState({
    defect_type: "",
    severity: "minor",
    title: "",
    description: "",
    inspection_id: "",
  });

  const [resolveNotes, setResolveNotes] = useState("");

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  useEffect(() => {
    void (async () => {
      try {
        const rows = await fetchJson<MeOut>(`${apiBase}/auth/me`, authHeaders);
        setMe(rows);
      } catch {
        setMe(null);
      }
    })();
  }, [apiBase, authHeaders]);

  useEffect(() => {
    if (!isEngineer || !me?.id) return;
    setInspectionForm((f) => ({ ...f, engineer_id: me.id }));
  }, [isEngineer, me?.id]);

  const loadAttention = useCallback(async () => {
    setBusyAttention(true);
    setAttentionErr(null);
    try {
      const rows = await fetchJson<InspectionAttentionDashboardOut>(`${apiBase}/vehicles/dashboard/inspection-attention`, authHeaders);
      setAttention(rows);
    } catch (e) {
      setAttention(null);
      setAttentionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyAttention(false);
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    void loadAttention();
  }, [loadAttention]);

  const loadInspections = useCallback(async () => {
    const vid = vehicleId.trim();
    if (!vid) {
      setInspections([]);
      setLatestInspection(null);
      setInspectionsErr(null);
      return;
    }

    setBusyInspections(true);
    setInspectionsErr(null);
    try {
      const latest = await fetchJson<VehicleInspectionOut>(`${apiBase}/vehicles/${encodeURIComponent(vid)}/inspections/latest`, authHeaders);
      setLatestInspection(latest);
    } catch (e) {
      setLatestInspection(null);
    }

    try {
      const rows = await fetchJson<VehicleInspectionOut[]>(
        `${apiBase}/vehicles/${encodeURIComponent(vid)}/inspections?limit=20&offset=0`,
        authHeaders,
      );
      setInspections(rows);
    } catch (e) {
      setInspections([]);
      setInspectionsErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyInspections(false);
    }
  }, [apiBase, authHeaders, vehicleId]);

  useEffect(() => {
    void loadInspections();
  }, [loadInspections]);

  const loadDefects = useCallback(async () => {
    const vid = vehicleId.trim();
    if (!vid) {
      setDefects([]);
      setDefectsErr(null);
      return;
    }
    setBusyDefects(true);
    setDefectsErr(null);
    try {
      const q = new URLSearchParams();
      q.set("limit", "200");
      q.set("offset", "0");
      if (defectStatus.trim()) q.set("status", defectStatus.trim());
      const rows = await fetchJson<VehicleDefectOut[]>(
        `${apiBase}/vehicles/${encodeURIComponent(vid)}/defects?${q.toString()}`,
        authHeaders,
      );
      setDefects(rows);
      if (!selectedDefectId && rows[0]?.id) setSelectedDefectId(rows[0].id);
    } catch (e) {
      setDefects([]);
      setDefectsErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyDefects(false);
    }
  }, [apiBase, authHeaders, defectStatus, selectedDefectId, vehicleId]);

  useEffect(() => {
    void loadDefects();
  }, [loadDefects]);

  const loadVehicleAll = useCallback(async () => {
    await loadInspections();
    await loadDefects();
  }, [loadDefects, loadInspections]);

  const createInspection = useCallback(async () => {
    const vid = vehicleId.trim();
    if (!vid) {
      setBannerErr("Enter a vehicle id first.");
      return;
    }
    if (!inspectionForm.engineer_id.trim()) {
      setBannerErr("Engineer id is required.");
      return;
    }

    const items = inspectionForm.items.filter((it) => it.item_code.trim() || it.item_label.trim() || it.result.trim() || it.notes.trim());
    if (!items.length) {
      setBannerErr("Add at least one inspection item.");
      return;
    }
    for (const it of items) {
      if (!it.item_code.trim()) throw new Error("Each inspection item needs an item_code.");
      if (!it.item_label.trim()) throw new Error("Each inspection item needs an item_label.");
      if (!it.result.trim()) throw new Error("Each inspection item needs a result.");
      if (it.result.toLowerCase() === "fail" && !it.fail_criticality.trim()) throw new Error("fail_criticality is required when result=fail.");
    }

    setBusyInspections(true);
    setBannerErr(null);
    setBanner(null);
    try {
      const payloadItems = items.map((it) => ({
        item_code: it.item_code.trim(),
        item_label: it.item_label.trim(),
        result: it.result,
        notes: it.notes.trim() || null,
        photo_document_id: it.photo_document_id.trim() || null,
        fail_criticality: it.result.toLowerCase() === "fail" ? it.fail_criticality.trim() : "minor",
      }));

      await postJson<VehicleInspectionOut>(
        `${apiBase}/vehicles/${encodeURIComponent(vid)}/inspections`,
        authHeaders,
        {
          engineer_id: inspectionForm.engineer_id.trim(),
          performed_at: inspectionForm.performed_at.trim() ? datetimeLocalToIso(inspectionForm.performed_at.trim()) : null,
          inspection_date: inspectionForm.inspection_date.trim() ? inspectionForm.inspection_date.trim() : null,
          odometer: inspectionForm.odometer.trim() ? Number(inspectionForm.odometer.trim()) : null,
          latitude: inspectionForm.latitude.trim() ? Number(inspectionForm.latitude.trim()) : null,
          longitude: inspectionForm.longitude.trim() ? Number(inspectionForm.longitude.trim()) : null,
          overall_status: inspectionForm.overall_status.trim() ? inspectionForm.overall_status.trim() : null,
          notes: inspectionForm.notes.trim() || null,
          items: payloadItems,
        },
      );
      setBanner("Vehicle inspection created.");
      setInspectionForm((f) => ({
        ...f,
        performed_at: "",
        inspection_date: "",
        odometer: "",
        latitude: "",
        longitude: "",
        overall_status: "",
        notes: "",
        items: [
          {
            item_code: "",
            item_label: "",
            result: "pass",
            notes: "",
            photo_document_id: "",
            fail_criticality: "minor",
          },
        ],
      }));
      await loadVehicleAll();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyInspections(false);
    }
  }, [apiBase, authHeaders, inspectionForm, loadVehicleAll, vehicleId]);

  const createDefect = useCallback(async () => {
    const vid = vehicleId.trim();
    if (!vid) {
      setBannerErr("Enter a vehicle id first.");
      return;
    }
    if (!defectCreateForm.defect_type.trim()) {
      setBannerErr("defect_type is required.");
      return;
    }
    if (!defectCreateForm.title.trim()) {
      setBannerErr("title is required.");
      return;
    }

    setBusyDefects(true);
    setBannerErr(null);
    setBanner(null);
    try {
      await postJson<VehicleDefectOut>(
        `${apiBase}/vehicles/${encodeURIComponent(vid)}/defects`,
        authHeaders,
        {
          defect_type: defectCreateForm.defect_type.trim(),
          severity: defectCreateForm.severity,
          title: defectCreateForm.title.trim(),
          description: defectCreateForm.description.trim() || null,
          inspection_id: defectCreateForm.inspection_id.trim() || null,
        },
      );
      setBanner("Vehicle defect created.");
      setDefectCreateForm({ defect_type: "", severity: "minor", title: "", description: "", inspection_id: "" });
      await loadDefects();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyDefects(false);
    }
  }, [apiBase, authHeaders, defectCreateForm, loadDefects, vehicleId]);

  const [decisionBusy, setDecisionBusy] = useState(false);

  const resolveDefect = useCallback(async () => {
    if (!vehicleId.trim()) return;
    if (!selectedDefectId) return;

    setDecisionBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      await postJson<VehicleDefectOut>(
        `${apiBase}/vehicles/${encodeURIComponent(vehicleId.trim())}/defects/${encodeURIComponent(selectedDefectId)}/resolve`,
        authHeaders,
        {
          resolution_notes: resolveNotes.trim() || null,
        },
      );
      setBanner("Defect resolved.");
      setResolveNotes("");
      await loadDefects();
      await loadInspections();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDecisionBusy(false);
    }
  }, [apiBase, authHeaders, loadDefects, loadInspections, resolveNotes, selectedDefectId, vehicleId]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Vehicles</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Inspection attention dashboard, inspections (latest + recent), and defect workflow (create + resolve).
        </p>

        <div className="row" style={{ marginTop: 10, gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ minWidth: 320 }}>
            <label>Vehicle ID</label>
            <input value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} placeholder="Paste vehicle uuid/id" />
          </div>
          <div className="field" style={{ minWidth: 240 }}>
            <label>Defect status filter</label>
            <select value={defectStatus} onChange={(e) => setDefectStatus(e.target.value)} disabled={busyDefects || busyInspections}>
              <option value="">(any)</option>
              <option value="pending">pending</option>
              <option value="resolved">resolved</option>
            </select>
          </div>
          <button type="button" className="secondary" onClick={() => void loadVehicleAll()} disabled={busyDefects || busyInspections}>
            Refresh vehicle data
          </button>
        </div>

        {banner ? (
          <div
            style={{
              marginTop: 12,
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

      <nav className="hub-toc" aria-label="Vehicle sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#vehicles-attention">Attention</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#vehicles-inspections">Inspections</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#vehicles-defects">Defects</a>
        </div>
      </nav>

      <div id="vehicles-attention" className="card hub-panel hub-anchor">
        <h3>Inspection attention</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="hub-sub">Attention count: <strong>{attention?.attention_count ?? 0}</strong></div>
          <button type="button" className="secondary" onClick={() => void loadAttention()} disabled={busyAttention}>
            {busyAttention ? "Loading…" : "Refresh attention"}
          </button>
        </div>
        {attentionErr ? <div className="hub-err" style={{ marginTop: 10 }}>{attentionErr}</div> : null}
        {attention?.items?.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {attention.items.slice(0, 15).map((it, idx) => (
              <li key={String(idx)} style={{ marginBottom: 10 }}>
                <div>
                  <strong>{String(it.readiness_status ?? "—")}</strong> · vehicle {String(it.vehicle_id ?? "—")}
                </div>
                {Array.isArray(it.reasons) ? (
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    reasons: {it.reasons.slice(0, 3).map((r) => String(r)).join(", ")}
                    {it.reasons.length > 3 ? "…" : ""}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
        {!attention?.items?.length && !busyAttention ? <div className="muted" style={{ marginTop: 10 }}>No attention items.</div> : null}
      </div>

      <div id="vehicles-inspections" className="card hub-panel hub-anchor">
        <h3>Inspections</h3>
        {!vehicleId.trim() ? <div className="muted">Enter a vehicle id to view inspections.</div> : null}

        {inspectionsErr ? <div className="hub-err" style={{ marginTop: 10 }}>{inspectionsErr}</div> : null}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Latest inspection</h4>
        {busyInspections ? <div className="muted" style={{ marginTop: 10 }}>Loading…</div> : null}
        {!busyInspections && latestInspection ? (
          <div className="hint" style={{ marginTop: 10 }}>
            Status: <b>{latestInspection.overall_status}</b> · date {String(latestInspection.inspection_date)} · engineer{" "}
            {latestInspection.engineer_id}
            <div className="hub-sub" style={{ marginTop: 6 }}>
              items: {latestInspection.items.length} · notes: {latestInspection.notes ? latestInspection.notes : "—"}
            </div>
          </div>
        ) : null}
        {!busyInspections && !latestInspection ? <div className="muted" style={{ marginTop: 10 }}>No latest inspection found.</div> : null}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Recent inspections</h4>
        {inspections.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 10 }}>
            {inspections.map((ins) => (
              <li key={ins.id} style={{ marginBottom: 10 }}>
                <div>
                  <strong>{ins.overall_status}</strong> · {String(ins.inspection_date)} · engineer {ins.engineer_id.slice(0, 8)}…
                </div>
                {ins.notes ? <div className="hub-sub" style={{ marginTop: 2 }}>{ins.notes}</div> : null}
              </li>
            ))}
          </ul>
        ) : null}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Create inspection</h4>
        {!vehicleId.trim() ? <div className="muted" style={{ marginTop: 8 }}>Vehicle ID required.</div> : null}

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>engineer_id</label>
            <input
              value={inspectionForm.engineer_id}
              onChange={(e) => setInspectionForm((f) => ({ ...f, engineer_id: e.target.value }))}
              disabled={isEngineer}
              placeholder={isEngineer ? "From your profile" : "Engineer uuid/id"}
            />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>performed_at (optional)</label>
            <input type="datetime-local" value={inspectionForm.performed_at} onChange={(e) => setInspectionForm((f) => ({ ...f, performed_at: e.target.value }))} />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>inspection_date (optional)</label>
            <input type="date" value={inspectionForm.inspection_date} onChange={(e) => setInspectionForm((f) => ({ ...f, inspection_date: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>odometer (optional)</label>
            <input value={inspectionForm.odometer} onChange={(e) => setInspectionForm((f) => ({ ...f, odometer: e.target.value }))} placeholder="e.g. 12345.6" />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>latitude (optional)</label>
            <input value={inspectionForm.latitude} onChange={(e) => setInspectionForm((f) => ({ ...f, latitude: e.target.value }))} placeholder="—" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>longitude (optional)</label>
            <input value={inspectionForm.longitude} onChange={(e) => setInspectionForm((f) => ({ ...f, longitude: e.target.value }))} placeholder="—" />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>overall_status (optional)</label>
            <select value={inspectionForm.overall_status} onChange={(e) => setInspectionForm((f) => ({ ...f, overall_status: e.target.value }))} disabled={busyInspections}>
              <option value="">(derive from items)</option>
              <option value="passed">passed</option>
              <option value="failed_minor">failed_minor</option>
              <option value="failed_critical">failed_critical</option>
            </select>
          </div>
        </div>

        <div className="field" style={{ marginTop: 8 }}>
          <label>notes (optional)</label>
          <textarea value={inspectionForm.notes} onChange={(e) => setInspectionForm((f) => ({ ...f, notes: e.target.value }))} />
        </div>

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Inspection items</h4>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button
            type="button"
            className="secondary"
            onClick={() =>
              setInspectionForm((f) => ({
                ...f,
                items: [
                  ...f.items,
                  {
                    item_code: "",
                    item_label: "",
                    result: "pass",
                    notes: "",
                    photo_document_id: "",
                    fail_criticality: "minor",
                  },
                ],
              }))
            }
            disabled={busyInspections}
          >
            Add item
          </button>
          <div className="hub-sub">Provide item_code + item_label + result.</div>
        </div>

        {inspectionForm.items.map((it, idx) => (
          <div key={`${idx}`} className="card" style={{ marginTop: 10, padding: 12 }}>
            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>item_code</label>
                <input
                  value={it.item_code}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, item_code: e.target.value } : x)),
                    }))
                  }
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>item_label</label>
                <input
                  value={it.item_label}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, item_label: e.target.value } : x)),
                    }))
                  }
                />
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <div className="field" style={{ flex: 1, minWidth: 180 }}>
                <label>result</label>
                <select
                  value={it.result}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, result: e.target.value } : x)),
                    }))
                  }
                >
                  <option value="pass">pass</option>
                  <option value="fail">fail</option>
                  <option value="advisory">advisory</option>
                  <option value="n_a">n_a</option>
                </select>
              </div>

              <div className="field" style={{ flex: 1, minWidth: 200 }}>
                <label>fail_criticality</label>
                <select
                  value={it.fail_criticality}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, fail_criticality: e.target.value } : x)),
                    }))
                  }
                  disabled={String(it.result).toLowerCase() !== "fail"}
                >
                  <option value="minor">minor</option>
                  <option value="critical">critical</option>
                </select>
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>notes (optional)</label>
                <input
                  value={it.notes}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, notes: e.target.value } : x)),
                    }))
                  }
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>photo_document_id (optional)</label>
                <input
                  value={it.photo_document_id}
                  onChange={(e) =>
                    setInspectionForm((f) => ({
                      ...f,
                      items: f.items.map((x, i) => (i === idx ? { ...x, photo_document_id: e.target.value } : x)),
                    }))
                  }
                  placeholder="document uuid/id"
                />
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
              <button
                type="button"
                className="secondary"
                disabled={busyInspections || inspectionForm.items.length <= 1}
                onClick={() =>
                  setInspectionForm((f) => ({
                    ...f,
                    items: f.items.filter((_, i) => i !== idx),
                  }))
                }
              >
                Remove item
              </button>
            </div>
          </div>
        ))}

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 12 }}>
          <button type="button" disabled={busyInspections} onClick={() => void createInspection()}>
            {busyInspections ? "Saving…" : "Create inspection"}
          </button>
        </div>
      </div>

      <div id="vehicles-defects" className="card hub-panel hub-anchor">
        <h3>Defects</h3>
        {!vehicleId.trim() ? <div className="muted">Enter a vehicle id to manage defects.</div> : null}
        {defectsErr ? <div className="hub-err" style={{ marginTop: 10 }}>{defectsErr}</div> : null}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Defects list</h4>
        {busyDefects ? <div className="muted" style={{ marginTop: 10 }}>Loading…</div> : null}
        {!busyDefects && defects.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 10 }}>
            {defects.map((d) => (
              <li key={d.id} style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  className={d.id === selectedDefectId ? "" : "secondary"}
                  onClick={() => setSelectedDefectId(d.id)}
                  style={{ textAlign: "left", width: "100%" }}
                  disabled={decisionBusy}
                >
                  <div>
                    <strong>{d.severity}</strong> · {d.defect_type}
                  </div>
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    {d.status} · {d.title} · reported {String(d.reported_at).slice(0, 16)}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {!busyDefects && !defects.length ? <div className="muted" style={{ marginTop: 10 }}>No defects found.</div> : null}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Create defect</h4>
        {!vehicleId.trim() ? null : (
          <>
            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>defect_type</label>
                <input value={defectCreateForm.defect_type} onChange={(e) => setDefectCreateForm((f) => ({ ...f, defect_type: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 180 }}>
                <label>severity</label>
                <select value={defectCreateForm.severity} onChange={(e) => setDefectCreateForm((f) => ({ ...f, severity: e.target.value }))}>
                  <option value="critical">critical</option>
                  <option value="major">major</option>
                  <option value="minor">minor</option>
                </select>
              </div>
            </div>

            <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
              <div className="field" style={{ flex: 1, minWidth: 220 }}>
                <label>title</label>
                <input value={defectCreateForm.title} onChange={(e) => setDefectCreateForm((f) => ({ ...f, title: e.target.value }))} />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>inspection_id (optional)</label>
                <input value={defectCreateForm.inspection_id} onChange={(e) => setDefectCreateForm((f) => ({ ...f, inspection_id: e.target.value }))} placeholder="Paste inspection uuid/id" />
              </div>
            </div>

            <div className="field" style={{ marginTop: 8 }}>
              <label>description (optional)</label>
              <textarea value={defectCreateForm.description} onChange={(e) => setDefectCreateForm((f) => ({ ...f, description: e.target.value }))} />
            </div>

            <button type="button" disabled={busyDefects} onClick={() => void createDefect()} style={{ marginTop: 10 }}>
              {busyDefects ? "Creating…" : "Create defect"}
            </button>
          </>
        )}

        <div className="divider" />

        <h4 style={{ fontSize: 13, marginTop: 0 }}>Resolve defect</h4>
        {!selectedDefect ? <div className="muted" style={{ marginTop: 10 }}>Select a defect to resolve.</div> : null}
        {selectedDefect ? (
          <>
            <div className="hint" style={{ marginTop: 10 }}>
              <strong>{selectedDefect.title}</strong> · {selectedDefect.severity} · status {selectedDefect.status}
            </div>
            {selectedDefect.resolution_notes ? (
              <div className="hub-sub" style={{ marginTop: 8 }}>
                Existing resolution notes: {selectedDefect.resolution_notes}
              </div>
            ) : null}

            {selectedDefect.status !== "resolved" ? (
              <>
                <div className="field" style={{ marginTop: 10 }}>
                  <label>resolution_notes</label>
                  <textarea value={resolveNotes} onChange={(e) => setResolveNotes(e.target.value)} placeholder="Notes for resolution. Critical defects may require a longer explanation." />
                </div>
                <button type="button" className="secondary" disabled={decisionBusy} onClick={() => void resolveDefect()}>
                  {decisionBusy ? "Resolving…" : "Resolve defect"}
                </button>
              </>
            ) : (
              <div className="muted" style={{ marginTop: 10 }}>Already resolved.</div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}

