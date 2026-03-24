import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type EngineerAvailabilityRowOut = {
  engineer_id: string;
  availability_state: string;
  active_job_count: number;
};

type QualificationOut = {
  id: string;
  engineer_user_id: string;
  competency: string;
  issued_at: string | null;
  expires_at: string | null;
  document_ref: string | null;
  status: string;
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

function datetimeLocalToIso(v: string): string {
  return new Date(v).toISOString();
}

export function CompetenceHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [engineersBusy, setEngineersBusy] = useState(false);
  const [engineersErr, setEngineersErr] = useState<string | null>(null);
  const [engineers, setEngineers] = useState<EngineerAvailabilityRowOut[]>([]);

  const [selectedEngineerId, setSelectedEngineerId] = useState("");

  const [qualsState, setQualsState] = useState<{ data: QualificationOut[]; err: string | null; busy: boolean }>({
    data: [],
    err: null,
    busy: false,
  });

  const [createForm, setCreateForm] = useState({
    competency: "",
    issued_at: "",
    expires_at: "",
    document_ref: "",
  });

  const qualificationSummary = useMemo(() => {
    const items = qualsState.data ?? [];
    const active = items.filter((q) => (q.status || "").toLowerCase() === "active").length;
    const total = items.length;
    return { active, total };
  }, [qualsState.data]);

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  const loadEngineers = useCallback(async () => {
    setEngineersBusy(true);
    setEngineersErr(null);
    setEngineers([]);
    try {
      const rows = await fetchJson<EngineerAvailabilityRowOut[]>(`${apiBase}/dispatch/engineers/availability`, authHeaders);
      setEngineers(rows);
      if (!selectedEngineerId && rows[0]?.engineer_id) setSelectedEngineerId(rows[0].engineer_id);
    } catch (e) {
      setEngineersErr(e instanceof Error ? e.message : String(e));
      setEngineers([]);
    } finally {
      setEngineersBusy(false);
    }
  }, [apiBase, authHeaders, selectedEngineerId]);

  const loadQualifications = useCallback(async () => {
    const eid = selectedEngineerId.trim();
    if (!eid) {
      setQualsState({ data: [], err: null, busy: false });
      return;
    }
    setQualsState((s) => ({ ...s, busy: true, err: null }));
    try {
      const rows = await fetchJson<QualificationOut[]>(
        `${apiBase}/competence/qualifications?engineer_user_id=${encodeURIComponent(eid)}`,
        authHeaders,
      );
      setQualsState({ data: rows, err: null, busy: false });
    } catch (e) {
      setQualsState({ data: [], err: e instanceof Error ? e.message : String(e), busy: false });
    }
  }, [apiBase, authHeaders, selectedEngineerId]);

  useEffect(() => {
    void loadEngineers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void loadQualifications();
  }, [loadQualifications]);

  const createQualification = useCallback(async () => {
    const eid = selectedEngineerId.trim();
    if (!eid) {
      setBannerErr("Select an engineer.");
      return;
    }
    if (!createForm.competency.trim()) {
      setBannerErr("competency is required.");
      return;
    }
    setBusy(true);
    setBannerErr(null);
    setBanner(null);
    try {
      await postJson<QualificationOut>(`${apiBase}/competence/qualifications`, authHeaders, {
        engineer_user_id: eid,
        competency: createForm.competency.trim(),
        issued_at: createForm.issued_at.trim() ? datetimeLocalToIso(createForm.issued_at.trim()) : null,
        expires_at: createForm.expires_at.trim() ? datetimeLocalToIso(createForm.expires_at.trim()) : null,
        document_ref: createForm.document_ref.trim() || null,
      });

      setBanner("Qualification added.");
      setCreateForm({ competency: "", issued_at: "", expires_at: "", document_ref: "" });
      await loadQualifications();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, createForm, loadQualifications, selectedEngineerId]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Competence</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Manage engineer qualifications (competency + optional issued/expires dates and document references).
        </p>

        <div className="row" style={{ marginTop: 10, gap: 8, flexWrap: "wrap" }}>
          <label className="hub-sub" style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 320 }}>
            Engineer
            <select
              value={selectedEngineerId}
              onChange={(e) => setSelectedEngineerId(e.target.value)}
              disabled={engineersBusy || busy}
            >
              {engineers.map((e) => (
                <option value={e.engineer_id} key={e.engineer_id}>
                  {e.engineer_id} · {e.availability_state}
                </option>
              ))}
              {!engineers.length ? <option value="">(no engineers loaded)</option> : null}
            </select>
          </label>

          <button type="button" className="secondary" onClick={() => void loadEngineers()} disabled={engineersBusy || busy}>
            {engineersBusy ? "Loading…" : "Refresh engineers"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadQualifications()} disabled={busy}>
            {qualsState.busy ? "Loading…" : "Refresh qualifications"}
          </button>
        </div>

        {engineersErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{engineersErr}</div> : null}

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

      <nav className="hub-toc" aria-label="Competence sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#competence-list">Qualifications</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#competence-add">Add</a>
        </div>
      </nav>

      <div id="competence-list" className="card hub-panel hub-anchor">
        <h3>Qualifications</h3>
        {qualsState.err ? <div className="hub-err">{qualsState.err}</div> : null}
        {qualsState.busy ? <div className="muted">Loading…</div> : null}
        {!qualsState.busy && !qualsState.err && !qualsState.data.length ? <div className="muted">No qualifications found.</div> : null}
        {!qualsState.busy && qualsState.data.length ? (
          <div className="hint" style={{ marginTop: 6 }}>
            Active: <b>{qualificationSummary.active}</b> / Total: <b>{qualificationSummary.total}</b>
          </div>
        ) : null}

        {qualsState.data.length ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {qualsState.data.map((q) => (
              <li key={q.id} style={{ marginBottom: 10 }}>
                <div>
                  <strong>{q.competency}</strong> · {q.status}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  issued {q.issued_at ? String(q.issued_at).slice(0, 16) : "—"} · expires {q.expires_at ? String(q.expires_at).slice(0, 16) : "—"}
                </div>
                {q.document_ref ? (
                  <div className="hub-sub" style={{ marginTop: 2 }}>
                    document: {q.document_ref}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div id="competence-add" className="card hub-panel hub-anchor">
        <h3>Add qualification</h3>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <div className="field" style={{ flex: 1, minWidth: 260 }}>
            <label>competency</label>
            <input value={createForm.competency} onChange={(e) => setCreateForm((f) => ({ ...f, competency: e.target.value }))} placeholder="e.g. Gas Safe · category …" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>document_ref (optional)</label>
            <input value={createForm.document_ref} onChange={(e) => setCreateForm((f) => ({ ...f, document_ref: e.target.value }))} placeholder="Stored document uuid/id" />
          </div>
        </div>

        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>issued_at (optional)</label>
            <input type="datetime-local" value={createForm.issued_at} onChange={(e) => setCreateForm((f) => ({ ...f, issued_at: e.target.value }))} />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 220 }}>
            <label>expires_at (optional)</label>
            <input type="datetime-local" value={createForm.expires_at} onChange={(e) => setCreateForm((f) => ({ ...f, expires_at: e.target.value }))} />
          </div>
        </div>

        <button type="button" style={{ marginTop: 12 }} onClick={() => void createQualification()} disabled={busy}>
          {busy ? "Saving…" : "Add qualification"}
        </button>
      </div>
    </div>
  );
}

