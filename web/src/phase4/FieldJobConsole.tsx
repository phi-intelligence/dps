import React, { useCallback, useEffect, useState } from "react";

type JobOption = { id: string; address: string; status: string };
type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
  jobs?: JobOption[];
};

const FIELD_CONSOLE_NAV = [
  { id: "field-console-top", label: "Top" },
  { id: "field-job", label: "Job" },
  { id: "field-sla", label: "SLA" },
  { id: "field-eta", label: "ETA" },
  { id: "field-costing", label: "Costing" },
  { id: "field-equipment", label: "Equipment" },
  { id: "field-site-reqs", label: "Site reqs" },
  { id: "field-completion", label: "Completion" },
  { id: "field-vehicle", label: "Vehicle" },
] as const;

function readinessPillClass(status: string): string {
  const s = status.toLowerCase();
  if (s === "ready") return "field-readiness-pill ready";
  if (s === "warning") return "field-readiness-pill warn";
  return "field-readiness-pill blocked";
}

function formatEquipmentDictRow(d: Record<string, unknown>): string {
  const code = d.equipment_code != null ? String(d.equipment_code) : "";
  const typ = d.equipment_type != null ? String(d.equipment_type) : "";
  const cat = d.category != null ? String(d.category) : "";
  const reason = d.reason != null ? String(d.reason) : "";
  const qty = d.quantity_required != null ? `×${String(d.quantity_required)}` : "";
  const head = [code || typ || "item", typ && code ? typ : "", cat ? `(${cat})` : "", qty].filter(Boolean).join(" ");
  return reason ? `${head} — ${reason}` : head;
}

export function FieldJobConsole({ apiBase, authHeaders, jobs = [] }: Props) {
  const [jobId, setJobId] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<Record<string, unknown> | null>(null);
  const [sla, setSla] = useState<Record<string, unknown> | null>(null);
  const [equipment, setEquipment] = useState<Record<string, unknown> | null>(null);
  const [eqReqs, setEqReqs] = useState<unknown[] | null>(null);
  const [completion, setCompletion] = useState<Record<string, unknown> | null>(null);
  const [vehicleReadiness, setVehicleReadiness] = useState<Record<string, unknown> | null>(null);
  const [costing, setCosting] = useState<Record<string, unknown> | null>(null);
  const [eta, setEta] = useState<Record<string, unknown> | null>(null);
  const [timeline, setTimeline] = useState<{ job_id: string; events: Record<string, unknown>[] } | null>(null);
  const [onMyWayBusy, setOnMyWayBusy] = useState(false);
  const [notes, setNotes] = useState<string[]>([]);
  const [showCompletionRaw, setShowCompletionRaw] = useState(false);
  const [showSlaRaw, setShowSlaRaw] = useState(false);
  const [showEquipmentRaw, setShowEquipmentRaw] = useState(false);
  const [showVehicleRaw, setShowVehicleRaw] = useState(false);
  const [online, setOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );

  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);

  const load = useCallback(async () => {
    const id = jobId.trim();
    if (!id) return;
    setBusy(true);
    setNotes([]);
    setJob(null);
    setSla(null);
    setEquipment(null);
    setEqReqs(null);
    setCompletion(null);
    setVehicleReadiness(null);
    setCosting(null);
    setEta(null);
    setTimeline(null);
    const h = authHeaders;
    const tryJson = async (path: string): Promise<Record<string, unknown> | unknown[] | null> => {
      const res = await fetch(`${apiBase}${path}`, { headers: h });
      if (res.status === 403) {
        setNotes((n) => [...n, `${path}: forbidden for your role (try Dispatcher/Admin).`]);
        return null;
      }
      if (!res.ok) {
        const errText = await res.text();
        setNotes((n) => [...n, `${path}: ${errText.slice(0, 120)}`]);
        return null;
      }
      return res.json() as Promise<Record<string, unknown> | unknown[]>;
    };

    try {
      const j = await tryJson(`/jobs/${encodeURIComponent(id)}`);
      if (j && !Array.isArray(j)) setJob(j);

      const s = await tryJson(`/jobs/${encodeURIComponent(id)}/sla`);
      if (s && !Array.isArray(s)) setSla(s);

      const e = await tryJson(`/jobs/${encodeURIComponent(id)}/equipment-readiness`);
      if (e && !Array.isArray(e)) setEquipment(e);

      const r = await tryJson(`/jobs/${encodeURIComponent(id)}/equipment-requirements`);
      if (r && Array.isArray(r)) setEqReqs(r);

      const comp = await tryJson(`/jobs/${encodeURIComponent(id)}/completion-requirements`);
      if (comp && !Array.isArray(comp)) setCompletion(comp);

      const cost = await tryJson(`/jobs/${encodeURIComponent(id)}/costing`);
      if (cost && !Array.isArray(cost)) setCosting(cost);

      const etaRes = await tryJson(`/dispatch/jobs/${encodeURIComponent(id)}/eta`);
      if (etaRes && !Array.isArray(etaRes)) setEta(etaRes);

      const tlRes = await tryJson(`/dispatch/jobs/${encodeURIComponent(id)}/timeline`);
      if (tlRes && typeof tlRes === "object" && tlRes !== null && "events" in tlRes) setTimeline(tlRes as { job_id: string; events: Record<string, unknown>[] });

      const vid = vehicleId.trim();
      if (vid) {
        const v = await tryJson(`/equipment/vehicles/${encodeURIComponent(vid)}/readiness-summary`);
        if (v && !Array.isArray(v)) setVehicleReadiness(v);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Request failed";
      setNotes((n) => [...n, `Network or client error — ${msg}. Check connectivity and API base URL.`]);
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, jobId, vehicleId]);

  const onMyWay = useCallback(async () => {
    const id = jobId.trim();
    if (!id) return;
    setOnMyWayBusy(true);
    try {
      const res = await fetch(`${apiBase}/dispatch/jobs/${encodeURIComponent(id)}/customer-notify/on-my-way`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ source: "ui", set_en_route: true }),
      });
      if (!res.ok) throw new Error(await res.text());
      await load();
    } catch (err) {
      setNotes((n) => [...n, `On-my-way: ${err instanceof Error ? err.message : String(err)}`]);
    } finally {
      setOnMyWayBusy(false);
    }
  }, [apiBase, authHeaders, jobId, load]);

  return (
    <div className="field-work-wrap">
      <nav className="field-toc" aria-label="Field console sections">
        <span className="field-toc-label">Jump to:</span>
        <span className="field-toc-links">
          {FIELD_CONSOLE_NAV.map((item, i) => (
            <React.Fragment key={item.id}>
              {i > 0 ? <span className="field-toc-sep">·</span> : null}
              <a href={`#${item.id}`}>{item.label}</a>
            </React.Fragment>
          ))}
        </span>
      </nav>
      <div className="card field-punch-card" style={{ margin: "0 18px 18px" }} id="field-console-top">
        <h3>Field job console</h3>
        <p className="field-hint">
          Quick lookup for engineers and dispatchers: job record, SLA, completion requirements (forms / signatures /
          media / parts), equipment readiness, optional vehicle kit readiness, and site equipment requirements. This view
          is read-only.
        </p>
        {!online ? (
          <div className="portal-alert" style={{ marginBottom: 12 }}>
            You appear offline — data may be stale; punches and uploads should queue on the native app when supported. When
            replaying a queued punch via the API, send the same <code>offline_device_id</code> on{" "}
            <code>POST /time/punch/in|out</code> so the server can treat duplicates idempotently.
          </div>
        ) : null}
        <div className="field">
          <label>Job</label>
          {jobs.length > 0 ? (
            <select
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
            >
              <option value="">Select job...</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.address} ({j.status})
                </option>
              ))}
            </select>
          ) : (
            <input
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="Paste full job UUID"
            />
          )}
        </div>
        <div className="field">
          <label>Vehicle ID (optional)</label>
          <input
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            placeholder="Equipment vehicle UUID for kit readiness summary"
          />
        </div>
        <div className="field-punch-row">
          <button type="button" onClick={() => void load()} disabled={busy || !jobId.trim()}>
            {busy ? "Loading…" : "Load job context"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              const id = jobId.trim();
              if (!id || !navigator.clipboard) return;
              void navigator.clipboard.writeText(id).catch(() => undefined);
            }}
            disabled={!jobId.trim()}
          >
            Copy job ID
          </button>
        </div>
        {notes.length > 0 ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {notes.map((x, i) => (
              <li key={i} style={{ color: "#ffb4b4" }}>
                {x}
              </li>
            ))}
          </ul>
        ) : null}
        {job ? (
          <div style={{ marginTop: 16 }}>
            <div className="item-title">Status: {String(job.status)}</div>
            <div className="item-sub">{String(job.address ?? "")}</div>
            <div className="item-sub">
              SLA risk: {String(job.sla_risk_state ?? "—")} · ETA min: {job.eta_minutes != null ? String(job.eta_minutes) : "—"}
            </div>
            <div style={{ marginTop: 8 }}>
              <button
                type="button"
                className="secondary"
                onClick={() => void onMyWay()}
                disabled={onMyWayBusy || !jobId.trim()}
              >
                {onMyWayBusy ? "Sending…" : "Notify customer: On my way"}
              </button>
            </div>
          </div>
        ) : null}
        {sla ? (
          <div style={{ marginTop: 14 }} id="field-sla" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              SLA clock
            </h4>
            <ul className="hub-list-compact">
              <li>
                Summary: <strong>{String(sla.sla_status_summary ?? "—")}</strong> · warning:{" "}
                {String(sla.warning_state ?? "—")}
              </li>
              <li>
                Response: {sla.response_time_minutes != null ? `${Number(sla.response_time_minutes).toFixed(0)} min` : "—"}
                {sla.response_breached ? " · breached" : ""}
              </li>
              <li>
                Attendance: {sla.attendance_time_minutes != null ? `${Number(sla.attendance_time_minutes).toFixed(0)} min` : "—"}
                {sla.attendance_breached ? " · breached" : ""}
              </li>
              <li>
                Resolution:{" "}
                {sla.resolution_time_minutes != null ? `${Number(sla.resolution_time_minutes).toFixed(0)} min` : "—"}
                {sla.resolution_breached ? " · breached" : ""}
              </li>
              {sla.computed_at ? (
                <li className="item-sub">Computed {new Date(String(sla.computed_at)).toLocaleString()}</li>
              ) : null}
            </ul>
            <button type="button" className="secondary" onClick={() => setShowSlaRaw((x) => !x)}>
              {showSlaRaw ? "Hide SLA raw JSON" : "Show SLA raw JSON"}
            </button>
            {showSlaRaw ? (
              <pre className="item-body" style={{ fontSize: 11, maxHeight: 120, overflow: "auto", marginTop: 8 }}>
                {JSON.stringify(sla, null, 2)}
              </pre>
            ) : null}
          </div>
        ) : null}
        {eta ? (
          <div style={{ marginTop: 14 }} id="field-eta" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              ETA
            </h4>
            <ul className="hub-list-compact">
              <li>
                {eta.eta_minutes != null ? `${Number(eta.eta_minutes).toFixed(0)} min` : "—"} · source: {String(eta.eta_source ?? "—")} · confidence: {String(eta.eta_confidence ?? "—")}
              </li>
              {eta.eta_window_start != null || eta.eta_window_end != null ? (
                <li>Window: {eta.eta_window_start ? new Date(String(eta.eta_window_start)).toLocaleTimeString() : "—"} – {eta.eta_window_end ? new Date(String(eta.eta_window_end)).toLocaleTimeString() : "—"}</li>
              ) : null}
            </ul>
          </div>
        ) : null}
        {timeline && timeline.events.length > 0 ? (
          <div style={{ marginTop: 14 }} className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Timeline
            </h4>
            <ul className="hub-list-compact">
              {timeline.events.slice(0, 8).map((ev, i) => (
                <li key={i}>
                  {String(ev.summary ?? ev.event_type ?? "—")}
                  {ev.at ? ` · ${new Date(String(ev.at)).toLocaleString()}` : ""}
                </li>
              ))}
              {timeline.events.length > 8 ? <li className="item-sub">…and {timeline.events.length - 8} more</li> : null}
            </ul>
          </div>
        ) : null}
        {costing ? (
          <div style={{ marginTop: 14 }} id="field-costing" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Job costing
            </h4>
            <ul className="hub-list-compact">
              <li>Source: {String(costing.source ?? "—")} · {String(costing.currency ?? "")}</li>
              <li>
                Labour: {Number(costing.labour_hours ?? 0).toFixed(1)}h · cost: {Number(costing.labour_cost ?? 0).toFixed(2)}
                {costing.labour_overtime_cost != null ? ` · OT: ${Number(costing.labour_overtime_cost).toFixed(2)}` : ""}
              </li>
              <li>
                Materials: est {Number(costing.estimated_material_cost ?? 0).toFixed(2)} · actual {Number(costing.actual_material_cost ?? 0).toFixed(2)}
                {costing.material_cost_variance_vs_estimate != null ? ` · var: ${Number(costing.material_cost_variance_vs_estimate).toFixed(2)}` : ""}
              </li>
              <li>Status: {String(costing.labour_completeness_status ?? "—")}</li>
            </ul>
          </div>
        ) : null}
        {equipment ? (
          <div style={{ marginTop: 14 }} id="field-equipment" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Equipment readiness
            </h4>
            <div className="field-readiness-head">
              <span className={readinessPillClass(String(equipment.readiness_status ?? ""))}>
                {String(equipment.readiness_status ?? "—")}
              </span>
              {equipment.evaluated_for_engineer_id ? (
                <span className="item-sub" style={{ marginLeft: 8 }}>
                  Engineer context: {String(equipment.evaluated_for_engineer_id).slice(0, 8)}…
                </span>
              ) : (
                <span className="item-sub" style={{ marginLeft: 8 }}>No engineer context</span>
              )}
            </div>
            {Array.isArray(equipment.blocking_flags) && equipment.blocking_flags.length > 0 ? (
              <ul className="hub-list-compact" style={{ marginTop: 8 }}>
                {(equipment.blocking_flags as unknown[]).map((f, i) => (
                  <li key={`b-${i}`} style={{ color: "#ffb4b4" }}>
                    Block: {String(f)}
                  </li>
                ))}
              </ul>
            ) : null}
            {Array.isArray(equipment.warnings) && equipment.warnings.length > 0 ? (
              <ul className="hub-list-compact" style={{ marginTop: 6 }}>
                {(equipment.warnings as unknown[]).map((w, i) => (
                  <li key={`w-${i}`} style={{ color: "#ffe0a8" }}>
                    {String(w)}
                  </li>
                ))}
              </ul>
            ) : null}
            {(() => {
              const missing = (equipment.missing_required_equipment as Record<string, unknown>[]) ?? [];
              const expired = (equipment.expired_required_equipment as Record<string, unknown>[]) ?? [];
              const dueSoon = (equipment.due_soon_equipment as Record<string, unknown>[]) ?? [];
              const assigned = (equipment.assigned_matching_equipment as Record<string, unknown>[]) ?? [];
              return (
                <>
                  {missing.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4 }}>
                        Missing required ({missing.length})
                      </div>
                      <ul className="hub-list-compact">
                        {missing.slice(0, 10).map((row, i) => (
                          <li key={`m-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {expired.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4 }}>
                        Calibration / gap ({expired.length})
                      </div>
                      <ul className="hub-list-compact">
                        {expired.slice(0, 10).map((row, i) => (
                          <li key={`e-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {dueSoon.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4 }}>
                        Due soon ({dueSoon.length})
                      </div>
                      <ul className="hub-list-compact">
                        {dueSoon.slice(0, 10).map((row, i) => (
                          <li key={`d-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {assigned.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4 }}>
                        Satisfied requirements ({assigned.length})
                      </div>
                      <ul className="hub-list-compact">
                        {assigned.slice(0, 8).map((row, i) => (
                          <li key={`a-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </>
              );
            })()}
            <button type="button" className="secondary" style={{ marginTop: 10 }} onClick={() => setShowEquipmentRaw((x) => !x)}>
              {showEquipmentRaw ? "Hide equipment raw JSON" : "Show equipment raw JSON"}
            </button>
            {showEquipmentRaw ? (
              <pre className="item-body" style={{ fontSize: 11, maxHeight: 160, overflow: "auto", marginTop: 8 }}>
                {JSON.stringify(equipment, null, 2)}
              </pre>
            ) : null}
          </div>
        ) : null}
        {eqReqs && eqReqs.length > 0 ? (
          <div style={{ marginTop: 14 }} id="field-site-reqs" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Site equipment requirements ({eqReqs.length})
            </h4>
            <ul className="hub-list-compact">
              {eqReqs.slice(0, 12).map((row, i) => {
                const r = row as Record<string, unknown>;
                return (
                  <li key={i}>
                    {String(r.equipment_type ?? "equipment")} · qty {String(r.quantity ?? "—")} ·{" "}
                    {r.mandatory ? "mandatory" : "optional"}
                    {r.calibration_required ? " · calibration" : ""}
                    {r.notes ? ` · ${String(r.notes).slice(0, 48)}` : ""}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
        {completion ? (
          <div style={{ marginTop: 14 }} id="field-completion" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Job completion gate
            </h4>
            <div className="item-sub" style={{ marginBottom: 8 }}>
              Material policy: <strong>{String(completion.material_policy ?? "—")}</strong> — parts requirements apply
              when policy expects materials.
            </div>
            {(() => {
              const forms = (completion.form_requirements as Record<string, unknown>[]) ?? [];
              const sigs = (completion.signature_requirements as Record<string, unknown>[]) ?? [];
              const media = (completion.media_requirements as Record<string, unknown>[]) ?? [];
              const parts = (completion.parts_requirements as Record<string, unknown>[]) ?? [];
              const row = (label: string, done: boolean) => (
                <span style={{ color: done ? "#8fd68f" : "#ffb4b4" }}>{done ? "✓" : "○"} {label}</span>
              );
              return (
                <ul className="hub-list-compact" style={{ marginBottom: 8 }}>
                  {forms.map((f, i) => (
                    <li key={`f-${i}`}>
                      {row(`Form ${String(f.form_key)}`, f.satisfied_at != null)}
                      <span className="item-sub" style={{ marginLeft: 6 }}>
                        keys: {String(f.required_keys_json ?? "[]").slice(0, 60)}
                        {String(f.required_keys_json ?? "").length > 60 ? "…" : ""}
                      </span>
                    </li>
                  ))}
                  {sigs.map((s, i) => (
                    <li key={`s-${i}`}>{row("Customer / job signature", s.satisfied_at != null)}</li>
                  ))}
                  {media.map((m, i) => (
                    <li key={`m-${i}`}>
                      {row(`Photos (${String(m.required_photo_count)} required)`, m.satisfied_at != null)}
                    </li>
                  ))}
                  {parts.map((p, i) => (
                    <li key={`p-${i}`}>
                      {row(`Parts lines (${String(p.required_parts_items_count)} required)`, p.satisfied_at != null)}
                    </li>
                  ))}
                  {forms.length + sigs.length + media.length + parts.length === 0 ? (
                    <li className="item-sub">No explicit requirements — completion may proceed once other gates pass.</li>
                  ) : null}
                </ul>
              );
            })()}
            <button type="button" className="secondary" onClick={() => setShowCompletionRaw((x) => !x)}>
              {showCompletionRaw ? "Hide raw JSON" : "Show raw JSON"}
            </button>
            {showCompletionRaw ? (
              <pre className="item-body" style={{ fontSize: 11, maxHeight: 200, overflow: "auto", marginTop: 8 }}>
                {JSON.stringify(completion, null, 2)}
              </pre>
            ) : null}
          </div>
        ) : null}
        {vehicleReadiness ? (
          <div style={{ marginTop: 14 }} id="field-vehicle" className="field-anchor">
            <h4 className="field-section-title" style={{ fontSize: 13, margin: "0 0 6px" }}>
              Vehicle equipment readiness
            </h4>
            <div className="item-sub" style={{ marginBottom: 8 }}>
              Items on van / vehicle: <strong>{String(vehicleReadiness.equipment_count ?? "—")}</strong>
            </div>
            {(() => {
              const expired = (vehicleReadiness.expired_calibration as Record<string, unknown>[]) ?? [];
              const dueSoon = (vehicleReadiness.due_soon_calibration as Record<string, unknown>[]) ?? [];
              const unusable = (vehicleReadiness.unusable as Record<string, unknown>[]) ?? [];
              return (
                <>
                  {expired.length > 0 ? (
                    <div style={{ marginTop: 6 }}>
                      <div className="item-sub" style={{ marginBottom: 4, color: "#ffb4b4" }}>
                        Expired calibration ({expired.length})
                      </div>
                      <ul className="hub-list-compact">
                        {expired.slice(0, 12).map((row, i) => (
                          <li key={`ve-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {dueSoon.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4, color: "#ffe0a8" }}>
                        Calibration due soon ({dueSoon.length})
                      </div>
                      <ul className="hub-list-compact">
                        {dueSoon.slice(0, 12).map((row, i) => (
                          <li key={`vd-${i}`}>{formatEquipmentDictRow(row)}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {unusable.length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <div className="item-sub" style={{ marginBottom: 4 }}>
                        Unusable status ({unusable.length})
                      </div>
                      <ul className="hub-list-compact">
                        {unusable.slice(0, 12).map((row, i) => (
                          <li key={`vu-${i}`}>
                            {String(row.equipment_code ?? row.equipment_id ?? "item")} · status {String(row.status ?? "—")}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </>
              );
            })()}
            {Array.isArray(vehicleReadiness.warnings) && vehicleReadiness.warnings.length > 0 ? (
              <ul className="hub-list-compact" style={{ marginTop: 8 }}>
                {(vehicleReadiness.warnings as unknown[]).map((w, i) => (
                  <li key={`vw-${i}`} style={{ color: "#ffe0a8" }}>
                    {String(w)}
                  </li>
                ))}
              </ul>
            ) : null}
            {Number(vehicleReadiness.equipment_count ?? 0) === 0 &&
            (!Array.isArray(vehicleReadiness.warnings) || vehicleReadiness.warnings.length === 0) ? (
              <div className="item-sub">No equipment linked to this vehicle id.</div>
            ) : null}
            <button type="button" className="secondary" style={{ marginTop: 10 }} onClick={() => setShowVehicleRaw((x) => !x)}>
              {showVehicleRaw ? "Hide vehicle raw JSON" : "Show vehicle raw JSON"}
            </button>
            {showVehicleRaw ? (
              <pre className="item-body" style={{ fontSize: 11, maxHeight: 160, overflow: "auto", marginTop: 8 }}>
                {JSON.stringify(vehicleReadiness, null, 2)}
              </pre>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
