import React, { useCallback, useEffect, useState } from "react";

type HolidayCalendar = {
  id: string;
  name: string;
  region_code: string;
  timezone_name: string;
  active: boolean;
  notes: string | null;
  external_feed_url: string | null;
  external_feed_format: string;
  last_feed_import_at: string | null;
  last_feed_import_status: string | null;
  last_feed_import_detail: string | null;
  created_at: string;
};

type Quote = { id: string; status: string; grand_total: number };
type Lead = { id: string; name: string; status: string };
type Props = { apiBase: string; authHeaders: Record<string, string> };

export function LabourAiToolsHub({ apiBase, authHeaders }: Props) {
  const [calendars, setCalendars] = useState<HolidayCalendar[]>([]);
  const [selectedCalId, setSelectedCalId] = useState("");
  const [calBusy, setCalBusy] = useState(false);
  const [calErr, setCalErr] = useState("");

  const [createForm, setCreateForm] = useState({
    name: "",
    region_code: "GB",
    timezone_name: "Europe/London",
    external_feed_url: "",
    external_feed_format: "ics",
  });

  const [feedOverride, setFeedOverride] = useState("");
  const [editFeedUrl, setEditFeedUrl] = useState("");
  const [editFeedFormat, setEditFeedFormat] = useState("ics");
  const [applyRegion, setApplyRegion] = useState("");
  const [importMsg, setImportMsg] = useState("");

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);

  const [aiTask, setAiTask] = useState<
    "quote_summary" | "follow_up_notes" | "proposal_explanation" | "dispatch_prioritization_hint"
  >("follow_up_notes");
  const [aiQuoteId, setAiQuoteId] = useState("");
  const [aiLeadId, setAiLeadId] = useState("");
  const [aiJobIds, setAiJobIds] = useState("");
  const [aiExtra, setAiExtra] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiErr, setAiErr] = useState("");
  const [aiOut, setAiOut] = useState<{ suggested_text: string; model: string; disclaimer: string } | null>(null);

  const hdr = useCallback(() => ({ ...authHeaders, "Content-Type": "application/json" }), [authHeaders]);

  const refreshCalendars = useCallback(async () => {
    setCalErr("");
    setCalBusy(true);
    try {
      const res = await fetch(`${apiBase}/labour/calendars`, { headers: authHeaders });
      if (res.status === 403) {
        setCalErr("Permission denied (need can_manage_labour_rules).");
        setCalendars([]);
        return;
      }
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as HolidayCalendar[];
      setCalendars(data);
      setSelectedCalId((prev) => (prev && data.some((c) => c.id === prev) ? prev : data[0]?.id ?? ""));
    } catch (e) {
      setCalErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCalBusy(false);
    }
  }, [apiBase, authHeaders]);

  const refreshLists = useCallback(async () => {
    try {
      const [rq, rl] = await Promise.all([
        fetch(`${apiBase}/quotes?limit=80&offset=0`, { headers: authHeaders }),
        fetch(`${apiBase}/crm/leads?limit=80&offset=0`, { headers: authHeaders }),
      ]);
      if (rq.ok) setQuotes((await rq.json()) as Quote[]);
      if (rl.ok) setLeads((await rl.json()) as Lead[]);
    } catch {
      /* best-effort */
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    void refreshCalendars();
    void refreshLists();
  }, [refreshCalendars, refreshLists]);

  const selected = calendars.find((c) => c.id === selectedCalId) ?? null;

  useEffect(() => {
    if (selected) {
      setEditFeedUrl(selected.external_feed_url || "");
      setEditFeedFormat(selected.external_feed_format || "ics");
    } else {
      setEditFeedUrl("");
      setEditFeedFormat("ics");
    }
  }, [selected]);

  async function createCalendar() {
    setCalErr("");
    setImportMsg("");
    if (!createForm.name.trim()) {
      setCalErr("Calendar name required.");
      return;
    }
    setCalBusy(true);
    try {
      const body: Record<string, unknown> = {
        name: createForm.name.trim(),
        region_code: createForm.region_code.trim() || "GB",
        timezone_name: createForm.timezone_name.trim() || "Europe/London",
        active: true,
        external_feed_format: createForm.external_feed_format,
      };
      if (createForm.external_feed_url.trim()) body.external_feed_url = createForm.external_feed_url.trim();
      const res = await fetch(`${apiBase}/labour/calendars`, { method: "POST", headers: hdr(), body: JSON.stringify(body) });
      if (!res.ok) throw new Error(await res.text());
      const row = (await res.json()) as HolidayCalendar;
      setCreateForm((f) => ({ ...f, name: "", external_feed_url: "" }));
      await refreshCalendars();
      setSelectedCalId(row.id);
      setImportMsg("Calendar created.");
    } catch (e) {
      setCalErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCalBusy(false);
    }
  }

  async function savePersistedFeed() {
    if (!selectedCalId) return;
    setCalErr("");
    setImportMsg("");
    setCalBusy(true);
    try {
      const fmt = editFeedFormat === "json" ? "json" : "ics";
      const body = {
        external_feed_url: editFeedUrl.trim() || null,
        external_feed_format: fmt,
      };
      const res = await fetch(`${apiBase}/labour/calendars/${selectedCalId}`, {
        method: "PATCH",
        headers: hdr(),
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      await refreshCalendars();
      setImportMsg("Saved feed URL / format on calendar.");
    } catch (e) {
      setCalErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCalBusy(false);
    }
  }

  async function runImport(dryRun: boolean) {
    if (!selectedCalId) return;
    setCalErr("");
    setImportMsg("");
    setCalBusy(true);
    try {
      const body: Record<string, unknown> = { dry_run: dryRun };
      if (feedOverride.trim()) body.feed_url = feedOverride.trim();
      if (applyRegion.trim()) body.apply_region_code = applyRegion.trim();
      const res = await fetch(`${apiBase}/labour/calendars/${selectedCalId}/import-feed`, {
        method: "POST",
        headers: hdr(),
        body: JSON.stringify(body),
      });
      const text = await res.text();
      if (!res.ok) throw new Error(text);
      const j = JSON.parse(text) as { imported_days: number; status: string; detail?: string | null; dry_run: boolean };
      setImportMsg(
        `${dryRun ? "Dry run" : "Import"}: ${j.imported_days} day(s). ${j.detail ?? ""}`.trim(),
      );
      await refreshCalendars();
    } catch (e) {
      setCalErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCalBusy(false);
    }
  }

  async function runAiAssist() {
    setAiErr("");
    setAiOut(null);
    setAiBusy(true);
    try {
      const body: Record<string, unknown> = { task: aiTask, extra_context: aiExtra.trim() || null };
      if (aiTask === "quote_summary" || aiTask === "proposal_explanation") {
        body.quote_id = aiQuoteId.trim();
      } else if (aiTask === "follow_up_notes") {
        body.lead_id = aiLeadId.trim();
      } else {
        const ids = aiJobIds
          .split(/[\s,]+/)
          .map((s) => s.trim())
          .filter(Boolean)
          .slice(0, 20);
        body.job_ids = ids;
      }
      const res = await fetch(`${apiBase}/ai/drafting/assist`, { method: "POST", headers: hdr(), body: JSON.stringify(body) });
      const text = await res.text();
      if (res.status === 403) {
        setAiErr("Permission denied (need can_ai_assisted_drafting).");
        return;
      }
      if (!res.ok) {
        try {
          const er = JSON.parse(text) as { detail?: string };
          setAiErr(er.detail || text);
        } catch {
          setAiErr(text || `HTTP ${res.status}`);
        }
        return;
      }
      setAiOut(JSON.parse(text) as { suggested_text: string; model: string; disclaimer: string });
    } catch (e) {
      setAiErr(e instanceof Error ? e.message : String(e));
    } finally {
      setAiBusy(false);
    }
  }

  return (
    <div className="labour-ai-hub">
      <div className="hint" style={{ padding: "12px 18px 0" }}>
        <strong>Labour &amp; AI</strong> (§5.18–§5.19): holiday calendar <strong>external feed import</strong> (ICS/JSON) and
        permission-gated <strong>AI drafting</strong> helpers. Requires env + API access; errors below are expected if your
        login lacks <code>can_manage_labour_rules</code> / <code>can_ai_assisted_drafting</code> or Gemini is disabled.
      </div>

      <div className="grid" style={{ alignItems: "start" }}>
        <div className="card">
          <h3>Holiday calendars &amp; feed import</h3>
          <div className="row" style={{ justifyContent: "flex-start", gap: 8, marginBottom: 10 }}>
            <button type="button" className="secondary" onClick={() => void refreshCalendars()} disabled={calBusy}>
              Refresh calendars
            </button>
          </div>
          {calErr ? <div className="error" style={{ marginBottom: 10 }}>{calErr}</div> : null}
          {importMsg ? <div className="hint" style={{ marginBottom: 10 }}>{importMsg}</div> : null}

          <div className="field">
            <label>Select calendar</label>
            <select value={selectedCalId} onChange={(e) => setSelectedCalId(e.target.value)}>
              {calendars.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.region_code})
                </option>
              ))}
            </select>
          </div>

          {selected ? (
            <div className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
              Last import: {selected.last_feed_import_status || "—"} {selected.last_feed_import_at ? ` @ ${selected.last_feed_import_at}` : ""}
              {selected.last_feed_import_detail ? (
                <>
                  <br />
                  {selected.last_feed_import_detail}
                </>
              ) : null}
            </div>
          ) : null}

          <div className="field">
            <label>Persisted feed URL &amp; format</label>
            <input value={editFeedUrl} onChange={(e) => setEditFeedUrl(e.target.value)} placeholder="https://…" />
            <select
              style={{ marginTop: 8 }}
              value={editFeedFormat}
              onChange={(e) => setEditFeedFormat(e.target.value)}
            >
              <option value="ics">ics</option>
              <option value="json">json</option>
            </select>
            <div className="row" style={{ marginTop: 8 }}>
              <button type="button" className="secondary" disabled={calBusy || !selectedCalId} onClick={() => void savePersistedFeed()}>
                Save feed settings
              </button>
            </div>
          </div>

          <div className="field">
            <label>One-off feed URL for this import only (optional)</label>
            <input value={feedOverride} onChange={(e) => setFeedOverride(e.target.value)} placeholder="Leave empty to use saved URL" />
          </div>
          <div className="field">
            <label>Apply region code on import (optional)</label>
            <input value={applyRegion} onChange={(e) => setApplyRegion(e.target.value)} placeholder="e.g. GB-ENG" />
          </div>
          <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
            <button type="button" disabled={calBusy || !selectedCalId} onClick={() => void runImport(true)}>
              Dry-run import
            </button>
            <button type="button" disabled={calBusy || !selectedCalId} onClick={() => void runImport(false)}>
              Import &amp; upsert days
            </button>
          </div>

          <hr style={{ border: 0, borderTop: "1px solid rgba(255,255,255,0.1)", margin: "16px 0" }} />

          <h4 style={{ margin: "0 0 8px" }}>Create calendar</h4>
          <div className="field">
            <label>Name</label>
            <input value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} />
          </div>
          <div className="field">
            <label>Region code</label>
            <input
              value={createForm.region_code}
              onChange={(e) => setCreateForm({ ...createForm, region_code: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Timezone (IANA)</label>
            <input
              value={createForm.timezone_name}
              onChange={(e) => setCreateForm({ ...createForm, timezone_name: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Default feed format</label>
            <select
              value={createForm.external_feed_format}
              onChange={(e) => setCreateForm({ ...createForm, external_feed_format: e.target.value })}
            >
              <option value="ics">ics</option>
              <option value="json">json</option>
            </select>
          </div>
          <div className="field">
            <label>External feed URL (optional)</label>
            <input
              value={createForm.external_feed_url}
              onChange={(e) => setCreateForm({ ...createForm, external_feed_url: e.target.value })}
            />
          </div>
          <button type="button" onClick={() => void createCalendar()} disabled={calBusy}>
            Create calendar
          </button>
        </div>

        <div className="card">
          <h3>AI-assisted drafting</h3>
          <p className="muted" style={{ fontSize: 13 }}>
            Enable <code>PHI_DPS_AI_ASSISTED_DRAFTING_ENABLED=1</code>, <code>GEMINI_ENABLED=1</code>, and{" "}
            <code>GEMINI_API_KEY</code>. Output is draft-only.
          </p>

          <div className="field">
            <label>Task</label>
            <select value={aiTask} onChange={(e) => setAiTask(e.target.value as typeof aiTask)}>
              <option value="follow_up_notes">Follow-up notes (lead)</option>
              <option value="quote_summary">Quote summary (internal)</option>
              <option value="proposal_explanation">Proposal explanation (customer-facing tone)</option>
              <option value="dispatch_prioritization_hint">Dispatch prioritization hint</option>
            </select>
          </div>

          {(aiTask === "quote_summary" || aiTask === "proposal_explanation") && (
            <div className="field">
              <label>Quote</label>
              <select value={aiQuoteId} onChange={(e) => setAiQuoteId(e.target.value)}>
                <option value="">— select —</option>
                {quotes.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.id.slice(0, 8)}… {q.status} £{q.grand_total}
                  </option>
                ))}
              </select>
            </div>
          )}

          {aiTask === "follow_up_notes" && (
            <div className="field">
              <label>Lead</label>
              <select value={aiLeadId} onChange={(e) => setAiLeadId(e.target.value)}>
                <option value="">— select —</option>
                {leads.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} ({l.status})
                  </option>
                ))}
              </select>
            </div>
          )}

          {aiTask === "dispatch_prioritization_hint" && (
            <div className="field">
              <label>Job IDs (comma or space, max 20)</label>
              <input value={aiJobIds} onChange={(e) => setAiJobIds(e.target.value)} placeholder="uuid, uuid, …" />
            </div>
          )}

          <div className="field">
            <label>Extra context (optional)</label>
            <textarea value={aiExtra} onChange={(e) => setAiExtra(e.target.value)} />
          </div>

          <div className="row" style={{ gap: 8 }}>
            <button type="button" onClick={() => void runAiAssist()} disabled={aiBusy}>
              {aiBusy ? "Running…" : "Run assistant"}
            </button>
            <button type="button" className="secondary" onClick={() => void refreshLists()}>
              Refresh quotes / leads
            </button>
          </div>

          {aiErr ? <div className="error" style={{ marginTop: 12 }}>{aiErr}</div> : null}

          {aiOut ? (
            <div style={{ marginTop: 14 }}>
              <h4 style={{ margin: "0 0 6px", fontSize: 14 }}>Suggested text ({aiOut.model})</h4>
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  fontSize: 13,
                  background: "rgba(0,0,0,0.25)",
                  padding: 12,
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                {aiOut.suggested_text}
              </pre>
              <p className="hint" style={{ marginTop: 8 }}>
                {aiOut.disclaimer}
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
