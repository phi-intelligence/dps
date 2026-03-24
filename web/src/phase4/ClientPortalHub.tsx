import React, { useCallback, useEffect, useState } from "react";
type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type PortalDashboard = {
  profile?: string;
  summary?: Record<string, number>;
  alerts?: string[];
  contracts?: Array<{ id: string; name: string; contract_code: string; status: string; term_end_at?: string | null }>;
  open_jobs?: Array<{ id: string; status: string; address: string; scheduled_at?: string | null }>;
  upcoming_visits?: Array<{
    job_id: string;
    scheduled_at?: string | null;
    address: string;
    site_id?: string | null;
  }>;
  outstanding_invoices?: Array<{
    id: string;
    grand_total: number;
    currency: string;
    status: string;
    created_at: string;
  }>;
  recent_certificates?: Array<{ id: string; job_id: string; type: string; status: string; created_at: string }>;
};

type PortalProposal = {
  id: string;
  proposal_reference: string;
  currency: string;
  current_contract_value: number | null;
  proposed_contract_value: number | null;
  customer_release_status: string;
  customer_response_status: string | null;
  released_to_customer_at: string | null;
  customer_viewed_at: string | null;
  pdf_downloadable: boolean;
  is_past_validity?: boolean;
};

type PortalActivation = {
  id: string;
  confirmation_reference: string;
  status: string;
  effective_date: string;
  released_to_customer_at: string | null;
  customer_viewed_at: string | null;
  customer_acknowledged_at: string | null;
};

type PortalDocumentItem = {
  id: string;
  title: string;
  document_type: string;
  status: string;
  stored_document_id: string | null;
  related_job_id: string | null;
  issue_date?: string;
};

type PortalCommRow = {
  id: string;
  contract_id: string;
  source_entity_type: string;
  communication_type: string;
  channel: string;
  status: string;
  subject: string | null;
  created_at: string;
  sent_at: string | null;
  failed_at: string | null;
  cancelled_at: string | null;
  body_preview: string | null;
  recipient_masked: string | null;
  last_delivery_status: string | null;
  last_delivery_completed_at: string | null;
};

/** §5.10 — readable labels for portal users (avoid raw enum strings). */
function humanizePortalText(s: string): string {
  const t = s.trim();
  if (!t) return "—";
  return t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const PORTAL_NAV: { id: string; label: string }[] = [
  { id: "portal-documents", label: "Documents" },
  { id: "portal-comms", label: "Messages" },
  { id: "portal-contracts", label: "Contracts & proposals" },
  { id: "portal-certs", label: "Certificates" },
  { id: "portal-jobs", label: "Jobs & invoices" },
];

async function fetchJson<T>(url: string, auth: Record<string, string>, init?: RequestInit): Promise<T> {
  const h = new Headers(auth);
  if (init?.body && typeof init.body === "string" && !h.has("Content-Type")) {
    h.set("Content-Type", "application/json");
  }
  const res = await fetch(url, { ...init, headers: h });
  if (!res.ok) throw new Error((await res.text()).slice(0, 240) || res.statusText);
  return res.json() as Promise<T>;
}

function pillClass(status: string): string {
  const s = status.toLowerCase();
  if (
    s === "released" ||
    s === "viewed" ||
    s === "acknowledged" ||
    s === "accepted" ||
    s === "completed" ||
    s === "signed" ||
    s === "activated" ||
    s === "paid"
  ) {
    return "status-pill released";
  }
  if (
    s === "pending" ||
    s === "pending_generation" ||
    s === "generated" ||
    s === "in_progress" ||
    s === "sent_for_signature" ||
    s === "queued" ||
    s === "draft"
  ) {
    return "status-pill pending";
  }
  if (s === "rejected" || s === "failed" || s === "cancelled" || s === "expired" || s === "declined" || s === "bounced") {
    return "status-pill danger";
  }
  return "status-pill muted";
}

function commStatusPill(status: string): string {
  const s = status.toLowerCase();
  if (s === "sent" || s === "delivered") return "status-pill released";
  if (s === "failed" || s === "bounced" || s === "complained") return "status-pill danger";
  if (s === "cancelled") return "status-pill muted";
  if (s === "pending" || s === "queued" || s === "draft") return "status-pill pending";
  return "status-pill muted";
}

function PortalInvoiceBreakdown({ data }: { data: Record<string, unknown> }) {
  const inv = data.invoice as Record<string, unknown> | undefined;
  const ctx = data.service_context as Record<string, unknown> | undefined;
  const ret = data.retrieval as Record<string, unknown> | undefined;
  if (!inv) return <div className="muted">No invoice detail.</div>;
  const overdue = inv.overdue === true;
  return (
    <div className="item-body" style={{ marginTop: 10, fontSize: 13 }}>
      <div>
        <strong>Total:</strong> {String(inv.grand_total)} {String(inv.currency)} ·{" "}
        <span className={pillClass(String(inv.status))}>{humanizePortalText(String(inv.status))}</span>
        {overdue ? <span className="portal-alert" style={{ marginLeft: 8, padding: "2px 8px" }}>Overdue</span> : null}
      </div>
      <div className="item-sub" style={{ marginTop: 6 }}>
        Labour {String(inv.labour_total)} · Materials {String(inv.materials_total)}
      </div>
      <div className="item-sub">
        Job {String(inv.job_id).slice(0, 8)}… · Created {inv.created_at ? new Date(String(inv.created_at)).toLocaleString() : "—"}
        {inv.paid_at ? ` · Paid ${new Date(String(inv.paid_at)).toLocaleString()}` : ""}
      </div>
      {ctx ? (
        <div style={{ marginTop: 10 }}>
          <strong>Service context</strong>
          <div className="item-sub">{String(ctx.job_address ?? "—")}</div>
          <div className="item-sub">
            Job status: {String(ctx.job_status ?? "—")}
            {ctx.scheduled_at ? ` · Scheduled ${new Date(String(ctx.scheduled_at)).toLocaleString()}` : ""}
          </div>
          {(ctx.site_name || ctx.site_code) ? (
            <div className="item-sub">
              Site: {String(ctx.site_name ?? "")} {ctx.site_code ? `(${String(ctx.site_code)})` : ""}
            </div>
          ) : null}
        </div>
      ) : null}
      {ret?.receipt_note ? <div className="item-sub" style={{ marginTop: 8 }}>{String(ret.receipt_note)}</div> : null}
    </div>
  );
}

function PortalMapHint({ mapPayload }: { mapPayload: Record<string, unknown> | undefined }) {
  if (!mapPayload || Object.keys(mapPayload).length === 0) return null;
  const band = mapPayload.distance_band != null ? String(mapPayload.distance_band).replace(/_/g, " ") : null;
  const fresh = mapPayload.freshness != null ? String(mapPayload.freshness) : null;
  const pos = mapPayload.approximate_engineer_position as Record<string, unknown> | undefined;
  return (
    <div style={{ marginTop: 8 }}>
      <strong>Live location (approximate)</strong>
      <div className="item-sub">
        When the engineer is on the way, we show reduced-precision coordinates for privacy. Distance band:{" "}
        {band ?? "unknown"}
        {fresh ? ` · telemetry freshness: ${fresh}` : ""}
      </div>
      {pos?.latitude != null && pos?.longitude != null ? (
        <div className="item-sub">
          Map reference point ~{Number(pos.latitude).toFixed(2)}, {Number(pos.longitude).toFixed(2)} (not exact).
        </div>
      ) : null}
    </div>
  );
}

function PortalEtaSummary({ eta }: { eta: Record<string, unknown> | undefined }) {
  if (!eta || Object.keys(eta).length === 0) return null;
  const mins = eta.eta_minutes;
  const conf = eta.eta_confidence != null ? String(eta.eta_confidence) : null;
  const src = eta.eta_source != null ? String(eta.eta_source).replace(/_/g, " ") : null;
  const start = eta.eta_window_start ? new Date(String(eta.eta_window_start)).toLocaleString() : null;
  const end = eta.eta_window_end ? new Date(String(eta.eta_window_end)).toLocaleString() : null;
  const updated = eta.last_updated_at ? new Date(String(eta.last_updated_at)).toLocaleString() : null;
  return (
    <div style={{ marginTop: 8 }}>
      <strong>Arrival estimate</strong>
      <div className="item-sub">
        {typeof mins === "number" ? `About ${Math.round(mins)} minutes` : "Time not available"}
        {conf ? ` · confidence: ${conf}` : ""}
        {src ? ` · source: ${src}` : ""}
      </div>
      {start && end ? (
        <div className="item-sub">
          Window: {start} – {end}
        </div>
      ) : null}
      {updated ? <div className="item-sub">Last updated {updated}</div> : null}
    </div>
  );
}

export function ClientPortalHub({ apiBase, authHeaders }: Props) {
  const [dash, setDash] = useState<PortalDashboard | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [proposalsByContract, setProposalsByContract] = useState<Record<string, PortalProposal[]>>({});
  const [activationsByContract, setActivationsByContract] = useState<Record<string, PortalActivation[]>>({});
  const [contractLoading, setContractLoading] = useState<Record<string, boolean>>({});

  const [extraByProposal, setExtraByProposal] = useState<
    Record<string, { timeline?: unknown[]; acceptance?: Record<string, unknown>; loading?: boolean }>
  >({});
  const [timelineOpen, setTimelineOpen] = useState<Record<string, boolean>>({});

  const [respondType, setRespondType] = useState<Record<string, string>>({});
  const [respondNotes, setRespondNotes] = useState<Record<string, string>>({});
  const [acceptName, setAcceptName] = useState<Record<string, string>>({});
  const [ackContact, setAckContact] = useState<Record<string, string>>({});
  const [ackNotes, setAckNotes] = useState<Record<string, string>>({});
  const [portalDocs, setPortalDocs] = useState<PortalDocumentItem[]>([]);
  const [payBusy, setPayBusy] = useState<string | null>(null);
  const [jobLiveById, setJobLiveById] = useState<
    Record<string, { loading?: boolean; data?: Record<string, unknown>; err?: string }>
  >({});
  const [actTimelineOpen, setActTimelineOpen] = useState<Record<string, boolean>>({});
  const [actTimelineById, setActTimelineById] = useState<
    Record<string, { loading?: boolean; events?: Array<Record<string, unknown>>; err?: string }>
  >({});
  const [invDetailOpen, setInvDetailOpen] = useState<Record<string, boolean>>({});
  const [invDetailById, setInvDetailById] = useState<
    Record<string, { loading?: boolean; data?: Record<string, unknown>; err?: string }>
  >({});
  const [portalComms, setPortalComms] = useState<PortalCommRow[]>([]);
  const [commsExpandedId, setCommsExpandedId] = useState<string | null>(null);
  const [commsDetailById, setCommsDetailById] = useState<Record<string, PortalCommRow>>({});
  const [commsDetailBusy, setCommsDetailBusy] = useState<string | null>(null);

  const refreshDashboard = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const [d, rawDocs, rawComms] = await Promise.all([
        fetchJson<PortalDashboard>(`${apiBase}/portal/me/dashboard`, authHeaders),
        fetch(`${apiBase}/portal/me/documents`, { headers: authHeaders }).then(async (res) => {
          if (!res.ok) return [];
          return res.json() as Promise<PortalDocumentItem[]>;
        }),
        fetch(`${apiBase}/portal/me/communications?limit=40`, { headers: authHeaders }).then(async (res) => {
          if (!res.ok) return [];
          return res.json() as Promise<PortalCommRow[]>;
        }),
      ]);
      setDash(d);
      setPortalDocs(Array.isArray(rawDocs) ? rawDocs : []);
      setPortalComms(Array.isArray(rawComms) ? rawComms : []);
      setCommsDetailById({});
      setCommsExpandedId(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders]);

  const loadCommunicationDetail = useCallback(
    async (communicationId: string) => {
      setCommsExpandedId(communicationId);
      setCommsDetailBusy(communicationId);
      setErr(null);
      try {
        const row = await fetchJson<PortalCommRow>(
          `${apiBase}/portal/me/communications/${encodeURIComponent(communicationId)}`,
          authHeaders,
        );
        setCommsDetailById((m) => ({ ...m, [communicationId]: row }));
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
        setCommsExpandedId(null);
      } finally {
        setCommsDetailBusy(null);
      }
    },
    [apiBase, authHeaders],
  );

  useEffect(() => {
    void refreshDashboard();
  }, [refreshDashboard]);

  const loadContractBundles = useCallback(
    async (contractId: string) => {
      setContractLoading((c) => ({ ...c, [contractId]: true }));
      try {
        const [props, acts] = await Promise.all([
          fetchJson<PortalProposal[]>(
            `${apiBase}/portal/me/contracts/${encodeURIComponent(contractId)}/repricing-proposals`,
            authHeaders,
          ),
          fetchJson<PortalActivation[]>(
            `${apiBase}/portal/me/contracts/${encodeURIComponent(contractId)}/activation-confirmations`,
            authHeaders,
          ),
        ]);
        setProposalsByContract((p) => ({ ...p, [contractId]: props }));
        setActivationsByContract((a) => ({ ...a, [contractId]: acts }));
      } catch {
        setProposalsByContract((p) => ({ ...p, [contractId]: [] }));
        setActivationsByContract((a) => ({ ...a, [contractId]: [] }));
      } finally {
        setContractLoading((c) => ({ ...c, [contractId]: false }));
      }
    },
    [apiBase, authHeaders],
  );

  const loadJobLive = useCallback(
    async (jobId: string) => {
      setJobLiveById((m) => ({ ...m, [jobId]: { ...m[jobId], loading: true, err: undefined } }));
      try {
        const data = await fetchJson<Record<string, unknown>>(
          `${apiBase}/portal/me/jobs/${encodeURIComponent(jobId)}/tracking`,
          authHeaders,
        );
        setJobLiveById((m) => ({ ...m, [jobId]: { loading: false, data } }));
      } catch (e) {
        setJobLiveById((m) => ({
          ...m,
          [jobId]: { loading: false, err: e instanceof Error ? e.message : String(e) },
        }));
      }
    },
    [apiBase, authHeaders],
  );

  const loadActivationTimeline = useCallback(
    async (confirmationId: string) => {
      setActTimelineById((m) => ({ ...m, [confirmationId]: { ...m[confirmationId], loading: true, err: undefined } }));
      try {
        const events = await fetchJson<Array<Record<string, unknown>>>(
          `${apiBase}/portal/me/activation-confirmations/${encodeURIComponent(confirmationId)}/timeline`,
          authHeaders,
        );
        setActTimelineById((m) => ({ ...m, [confirmationId]: { loading: false, events } }));
      } catch (e) {
        setActTimelineById((m) => ({
          ...m,
          [confirmationId]: { loading: false, err: e instanceof Error ? e.message : String(e) },
        }));
      }
    },
    [apiBase, authHeaders],
  );

  const loadInvoiceDetail = useCallback(
    async (invoiceId: string) => {
      setInvDetailById((m) => ({ ...m, [invoiceId]: { ...m[invoiceId], loading: true, err: undefined } }));
      try {
        const data = await fetchJson<Record<string, unknown>>(
          `${apiBase}/portal/me/invoices/${encodeURIComponent(invoiceId)}`,
          authHeaders,
        );
        setInvDetailById((m) => ({ ...m, [invoiceId]: { loading: false, data } }));
      } catch (e) {
        setInvDetailById((m) => ({
          ...m,
          [invoiceId]: { loading: false, err: e instanceof Error ? e.message : String(e) },
        }));
      }
    },
    [apiBase, authHeaders],
  );

  const loadProposalExtras = useCallback(
    async (proposalId: string) => {
      setExtraByProposal((x) => ({ ...x, [proposalId]: { ...x[proposalId], loading: true } }));
      try {
        const [timeline, acceptance] = await Promise.all([
          fetchJson<unknown[]>(`${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/timeline`, authHeaders),
          fetchJson<Record<string, unknown>>(
            `${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/acceptance`,
            authHeaders,
          ),
        ]);
        setExtraByProposal((x) => ({ ...x, [proposalId]: { timeline, acceptance, loading: false } }));
      } catch {
        setExtraByProposal((x) => ({ ...x, [proposalId]: { loading: false } }));
      }
    },
    [apiBase, authHeaders],
  );

  const downloadProposalPdf = async (proposalId: string) => {
    const res = await fetch(`${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/download`, {
      headers: authHeaders,
    });
    if (!res.ok) {
      setErr(await res.text());
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `proposal-${proposalId.slice(0, 8)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const submitRespond = async (proposalId: string) => {
    const response_type = respondType[proposalId] || "accepted";
    const notes = respondNotes[proposalId]?.trim() || null;
    try {
      await fetchJson(`${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/respond`, authHeaders, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ response_type, notes }),
      });
      const cid = Object.keys(proposalsByContract).find((k) => proposalsByContract[k].some((p) => p.id === proposalId));
      if (cid) await loadContractBundles(cid);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const initiateAcceptance = async (proposalId: string) => {
    try {
      await fetchJson(`${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/acceptance/initiate`, authHeaders, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ acceptance_type: "portal_acceptance" }),
      });
      await loadProposalExtras(proposalId);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const completeAcceptance = async (proposalId: string) => {
    const signed_name = acceptName[proposalId]?.trim() || "Customer";
    try {
      await fetchJson(
        `${apiBase}/portal/me/repricing-proposals/${encodeURIComponent(proposalId)}/acceptance/complete`,
        authHeaders,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            signed_name,
            confirm_binding_acknowledgement: true,
            acceptance_notes: respondNotes[proposalId]?.trim() || null,
          }),
        },
      );
      const cid = Object.keys(proposalsByContract).find((k) => proposalsByContract[k].some((p) => p.id === proposalId));
      if (cid) await loadContractBundles(cid);
      await loadProposalExtras(proposalId);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const downloadActivationPdf = async (confirmationId: string) => {
    const res = await fetch(
      `${apiBase}/portal/me/activation-confirmations/${encodeURIComponent(confirmationId)}/download`,
      { headers: authHeaders },
    );
    if (!res.ok) {
      setErr(await res.text());
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activation-${confirmationId.slice(0, 8)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadPortalDocument = async (storedDocumentId: string) => {
    const res = await fetch(
      `${apiBase}/portal/me/documents/${encodeURIComponent(storedDocumentId)}/download`,
      { headers: authHeaders },
    );
    if (!res.ok) {
      setErr(await res.text());
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `document-${storedDocumentId.slice(0, 8)}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const payOutstandingInvoice = async (invoiceId: string) => {
    setPayBusy(invoiceId);
    setErr(null);
    try {
      await fetchJson(`${apiBase}/portal/me/invoices/${encodeURIComponent(invoiceId)}/pay`, authHeaders, {
        method: "POST",
      });
      await refreshDashboard();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setPayBusy(null);
    }
  };

  const acknowledgeActivation = async (confirmationId: string) => {
    const acknowledged_by_contact = ackContact[confirmationId]?.trim() || "Portal user";
    const notes = ackNotes[confirmationId]?.trim() || null;
    try {
      await fetchJson(
        `${apiBase}/portal/me/activation-confirmations/${encodeURIComponent(confirmationId)}/acknowledge`,
        authHeaders,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ acknowledged_by_contact, notes }),
        },
      );
      const cid = Object.keys(activationsByContract).find((k) =>
        activationsByContract[k].some((a) => a.id === confirmationId),
      );
      if (cid) await loadContractBundles(cid);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const summary = dash?.summary;

  return (
    <div className="portal-shell">
      <div className="portal-hero">
        <h2>Your service portal</h2>
        <p>
          Review pricing or renewal proposals, tell us your decision, complete <strong>formal acceptance</strong> or{" "}
          <strong>e-sign</strong> when we invite you, and acknowledge when your agreement is <strong>live</strong>. Open a
          contract below for step-by-step actions. Download PDFs and documents when we make them available. Message history
          shows what we have sent — your account manager is still your main day-to-day contact.
        </p>
        {dash?.alerts && dash.alerts.length > 0 ? (
          <div className="portal-alert-strip">
            {dash.alerts.map((a, i) => (
              <div key={i} className="portal-alert">
                {a}
              </div>
            ))}
          </div>
        ) : null}
        {summary ? (
          <div className="portal-stat-row">
            <div className="portal-stat">
              <div className="n">{summary.open_jobs_count ?? 0}</div>
              <div className="l">Open jobs</div>
            </div>
            <div className="portal-stat">
              <div className="n">{summary.outstanding_invoices_count ?? 0}</div>
              <div className="l">Outstanding invoices</div>
            </div>
            <div className="portal-stat">
              <div className="n">{summary.upcoming_visits_count ?? 0}</div>
              <div className="l">Upcoming visits</div>
            </div>
          </div>
        ) : null}
        <div className="row" style={{ marginTop: 16, justifyContent: "flex-start" }}>
          <button type="button" className="secondary" onClick={() => void refreshDashboard()} disabled={busy}>
            {busy ? "Refreshing…" : "Refresh overview"}
          </button>
        </div>
      </div>

      <nav className="portal-toc" aria-label="Page sections">
        <p className="portal-toc-title">Jump to</p>
        <div className="portal-toc-links">
          {PORTAL_NAV.map((item, i) => (
            <React.Fragment key={item.id}>
              {i > 0 ? (
                <span className="portal-toc-sep" aria-hidden>
                  ·
                </span>
              ) : null}
              <a href={`#${item.id}`}>{item.label}</a>
            </React.Fragment>
          ))}
        </div>
      </nav>

      {err ? <div className="error" style={{ marginBottom: 16 }}>{err}</div> : null}

      <div id="portal-documents" className="portal-section-title portal-anchor">
        Your documents
      </div>
      {portalDocs.length === 0 ? (
        <div className="muted" style={{ padding: "0 18px 12px" }}>
          No documents visible yet, or still loading.
        </div>
      ) : (
        <div className="card" style={{ margin: "0 18px 20px" }}>
          <div className="list">
            {portalDocs.slice(0, 40).map((doc) => (
              <div key={doc.id} className="item">
                <div className="item-title">{doc.title}</div>
                <div className="item-sub">
                  {humanizePortalText(doc.document_type)} · {humanizePortalText(doc.status)}
                  {doc.issue_date ? ` · issued ${new Date(doc.issue_date).toLocaleDateString()}` : ""}
                  {doc.related_job_id ? ` · job ${doc.related_job_id.slice(0, 8)}…` : ""}
                </div>
                {doc.stored_document_id ? (
                  <div className="portal-actions">
                    <button
                      type="button"
                      aria-label={`Download ${doc.title || "document"}`}
                      onClick={() => void downloadPortalDocument(doc.stored_document_id!)}
                    >
                      Download
                    </button>
                  </div>
                ) : (
                  <div className="item-sub">A downloadable file is not linked to this entry yet.</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div id="portal-comms" className="portal-section-title portal-anchor">
        Emails &amp; messages from us
      </div>
      <p className="muted" style={{ padding: "0 18px 8px", margin: 0 }}>
        Sent and attempted outbound notifications for contracts you can access (drafts and internal queue items are not
        shown). Open an item for a longer preview when available.
      </p>
      {portalComms.length === 0 ? (
        <div className="muted" style={{ padding: "0 18px 16px" }}>
          No message history yet, or not available for this account type.
        </div>
      ) : (
        <div className="card" style={{ margin: "0 18px 20px" }}>
          <div className="list">
            {portalComms.map((c) => {
              const open = commsExpandedId === c.id;
              const detail = commsDetailById[c.id];
              return (
                <div key={c.id} className="item">
                  <div className="item-title">{c.subject || c.communication_type}</div>
                  <div className="item-sub">
                    <span className={commStatusPill(c.status)} title={c.status}>
                      {humanizePortalText(c.status)}
                    </span>
                    <span style={{ marginLeft: 8 }}>
                      {humanizePortalText(c.channel)} · {humanizePortalText(c.communication_type)}
                    </span>
                  </div>
                  <div className="item-sub">
                    {c.sent_at
                      ? `Sent ${new Date(c.sent_at).toLocaleString()}`
                      : c.failed_at
                        ? `Failed ${new Date(c.failed_at).toLocaleString()}`
                        : c.cancelled_at
                          ? `Cancelled ${new Date(c.cancelled_at).toLocaleString()}`
                          : `Created ${new Date(c.created_at).toLocaleString()}`}
                    {c.recipient_masked ? ` · To ${c.recipient_masked}` : ""}
                  </div>
                  {c.last_delivery_status ? (
                    <div className="item-sub">
                      Delivery: {c.last_delivery_status}
                      {c.last_delivery_completed_at
                        ? ` · ${new Date(c.last_delivery_completed_at).toLocaleString()}`
                        : ""}
                    </div>
                  ) : null}
                  {!open && c.body_preview ? (
                    <div className="item-body" style={{ marginTop: 8 }}>
                      {c.body_preview}
                    </div>
                  ) : null}
                  <div className="portal-actions">
                    <button
                      type="button"
                      className="btn-link"
                      disabled={commsDetailBusy === c.id}
                      onClick={() => {
                        if (open) {
                          setCommsExpandedId(null);
                          return;
                        }
                        if (commsDetailById[c.id]) {
                          setCommsExpandedId(c.id);
                          return;
                        }
                        void loadCommunicationDetail(c.id);
                      }}
                    >
                      {commsDetailBusy === c.id ? "Loading…" : open ? "Collapse" : "Longer preview"}
                    </button>
                  </div>
                  {open && detail?.body_preview ? (
                    <div className="item-body" style={{ marginTop: 10, whiteSpace: "pre-wrap" }}>
                      {detail.body_preview}
                    </div>
                  ) : null}
                  {open && !detail && commsDetailBusy === c.id ? (
                    <div className="muted" style={{ marginTop: 8 }}>
                      Loading full preview…
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div id="portal-contracts" className="portal-section-title portal-anchor">
        Contracts &amp; agreements
      </div>
      {!dash?.contracts?.length ? (
        <div className="muted">No contracts linked to this portal profile yet.</div>
      ) : (
        dash.contracts.map((c) => (
          <details
            key={c.id}
            className="contract-acc"
            onToggle={(e) => {
              const el = e.currentTarget;
              if (el.open && !proposalsByContract[c.id] && !contractLoading[c.id]) void loadContractBundles(c.id);
            }}
          >
            <summary>
              <span>
                {c.name} · <span className="muted">{c.contract_code}</span>
              </span>
              <span className={pillClass(c.status)} title={c.status}>
                {humanizePortalText(c.status)}
              </span>
            </summary>
            <div className="acc-body">
              {contractLoading[c.id] ? <div className="muted">Loading proposals and confirmations…</div> : null}

              <h4 style={{ margin: "12px 0 8px", fontSize: 13 }}>Repricing & renewal proposals</h4>
              {(proposalsByContract[c.id] ?? []).length === 0 && !contractLoading[c.id] ? (
                <div className="muted">No active proposals visible for this contract.</div>
              ) : null}
              {(proposalsByContract[c.id] ?? []).map((p) => {
                const ex = extraByProposal[p.id];
                const acc = ex?.acceptance;
                const esignPhase = acc?.provider_esign_customer_phase as string | undefined;
                const esign = acc?.provider_esign as Record<string, unknown> | null | undefined;
                return (
                  <div key={p.id} className="proposal-card">
                    <h4>{p.proposal_reference}</h4>
                    <p className="item-sub" style={{ marginTop: 4, lineHeight: 1.45 }}>
                      We may ask you to review a new contract value or terms. Use <strong>Download PDF</strong> for the full
                      detail, then record your response or complete formal acceptance if required.
                    </p>
                    <div className="item-sub">
                      Proposed value: {p.proposed_contract_value != null ? `${p.proposed_contract_value} ${p.currency}` : "—"}
                      {p.is_past_validity ? " · Past customer validity — only acknowledgement may be available." : ""}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <span className={pillClass(p.customer_release_status)} title={p.customer_release_status}>
                        Release: {humanizePortalText(p.customer_release_status)}
                      </span>
                      {p.customer_response_status ? (
                        <span className={pillClass(p.customer_response_status)} style={{ marginLeft: 8 }} title={p.customer_response_status}>
                          Response: {humanizePortalText(p.customer_response_status)}
                        </span>
                      ) : null}
                    </div>
                    {p.released_to_customer_at ? (
                      <div className="item-sub" style={{ marginTop: 6 }}>
                        Shared with you {new Date(p.released_to_customer_at).toLocaleString()}
                        {p.customer_viewed_at ? ` · Opened ${new Date(p.customer_viewed_at).toLocaleString()}` : ""}
                      </div>
                    ) : null}
                    <div className="portal-actions">
                      {p.pdf_downloadable ? (
                        <button type="button" onClick={() => void downloadProposalPdf(p.id)} aria-label={`Download proposal PDF ${p.proposal_reference}`}>
                          Download proposal PDF
                        </button>
                      ) : (
                        <span className="muted" style={{ fontSize: 12, alignSelf: "center" }}>
                          PDF not available yet
                        </span>
                      )}
                      <button
                        type="button"
                        className="btn-link"
                        onClick={() => {
                          const next = !timelineOpen[p.id];
                          setTimelineOpen((t) => ({ ...t, [p.id]: next }));
                          if (next && !ex?.timeline) void loadProposalExtras(p.id);
                        }}
                      >
                        {timelineOpen[p.id] ? "Hide timeline" : "Show timeline"}
                      </button>
                    </div>
                    {ex?.loading && timelineOpen[p.id] ? <div className="muted">Loading timeline…</div> : null}
                    {ex?.timeline && timelineOpen[p.id] ? (
                      <div className="timeline-mini">
                        {ex.timeline.map((ev, i) => {
                          const o = ev as Record<string, unknown>;
                          const line =
                            (o.label as string) ||
                            (o.summary as string) ||
                            (o.event_type as string) ||
                            JSON.stringify(ev);
                          const at = (o.at as string) || (o.performed_at as string) || "";
                          return (
                            <div key={i}>
                              {at ? `${new Date(at).toLocaleString()} · ` : ""}
                              {line}
                            </div>
                          );
                        })}
                      </div>
                    ) : null}

                    <div className="portal-card-section">
                      <div className="portal-card-section-title">Your response</div>
                      <p className="item-sub" style={{ marginTop: 0 }}>
                        Tell us if you accept, reject, or need changes. This is separate from formal e-sign, if we require it.
                      </p>
                    <div className="form-stack">
                      <label>Record a response</label>
                      <select
                        value={respondType[p.id] ?? "accepted"}
                        onChange={(e) => setRespondType((r) => ({ ...r, [p.id]: e.target.value }))}
                      >
                        <option value="accepted">Accepted</option>
                        <option value="rejected">Rejected</option>
                        <option value="counter_requested">Counter requested</option>
                        <option value="needs_follow_up">Needs follow-up</option>
                        <option value="acknowledged">Acknowledged (e.g. after expiry)</option>
                      </select>
                      <textarea
                        placeholder="Optional notes to your account manager"
                        value={respondNotes[p.id] ?? ""}
                        onChange={(e) => setRespondNotes((r) => ({ ...r, [p.id]: e.target.value }))}
                      />
                      <button type="button" className="secondary" onClick={() => void submitRespond(p.id)}>
                        Submit response
                      </button>
                    </div>
                    </div>

                    <div className="portal-card-section">
                      <div className="portal-card-section-title">Formal acceptance &amp; e-sign</div>
                    <div className="form-stack">
                      <label>Formal in-product acceptance</label>
                      <div className="item-sub">
                        {acc?.completed_summary
                          ? `Completed (${humanizePortalText(String((acc.completed_summary as Record<string, unknown>).acceptance_type ?? ""))}).`
                          : "When we require it: start a session, then confirm with your name to record binding acknowledgement in the product."}
                      </div>
                      {esignPhase && esignPhase !== "none" ? (
                        <div className="item-sub">
                          <strong>E-sign:</strong> {humanizePortalText(esignPhase)}
                        </div>
                      ) : null}
                      {esign && typeof esign === "object" ? (
                        <div className="item-sub" style={{ marginTop: 6 }}>
                          Provider: {String(esign.provider_name ?? "—")} · envelope status:{" "}
                          {String(esign.provider_status ?? "—")}
                          {esign.provider_envelope_id ? ` · ref ${String(esign.provider_envelope_id).slice(0, 10)}…` : ""}
                          <br />
                          <span className="muted">
                            If e-sign is in progress, use the link from your email from the signing provider; the portal
                            shows status only for security.
                          </span>
                        </div>
                      ) : null}
                      <div className="portal-actions">
                        <button type="button" className="secondary" onClick={() => void initiateAcceptance(p.id)}>
                          Start acceptance session
                        </button>
                        <input
                          placeholder="Sign as (full name)"
                          value={acceptName[p.id] ?? ""}
                          onChange={(e) => setAcceptName((a) => ({ ...a, [p.id]: e.target.value }))}
                        />
                        <button type="button" onClick={() => void completeAcceptance(p.id)}>
                          Complete acceptance
                        </button>
                      </div>
                    </div>
                    </div>
                  </div>
                );
              })}

              <h4 style={{ margin: "20px 0 8px", fontSize: 13 }}>Activation confirmations</h4>
              {(activationsByContract[c.id] ?? []).length === 0 && !contractLoading[c.id] ? (
                <div className="muted">No activation confirmations visible.</div>
              ) : null}
              {(activationsByContract[c.id] ?? []).map((a) => (
                <div key={a.id} className="proposal-card">
                  <h4>{a.confirmation_reference}</h4>
                  <p className="item-sub" style={{ marginTop: 4, lineHeight: 1.45 }}>
                    Confirms when your updated agreement is <strong>live</strong>. Download the summary PDF, review the
                    timeline, then acknowledge so we know you have seen it.
                  </p>
                  <div className="item-sub">Effective date {new Date(a.effective_date).toLocaleDateString()}</div>
                  <div style={{ marginTop: 8 }}>
                    <span className={pillClass(a.status)} title={a.status}>
                      {humanizePortalText(a.status)}
                    </span>
                  </div>
                  {a.released_to_customer_at ? (
                    <div className="item-sub" style={{ marginTop: 6 }}>
                      Shared {new Date(a.released_to_customer_at).toLocaleString()}
                      {a.customer_viewed_at ? ` · You opened ${new Date(a.customer_viewed_at).toLocaleString()}` : ""}
                    </div>
                  ) : null}
                  <div className="portal-actions">
                    <button
                      type="button"
                      onClick={() => void downloadActivationPdf(a.id)}
                      aria-label={`Download activation PDF ${a.confirmation_reference}`}
                    >
                      Download confirmation PDF
                    </button>
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() => {
                        const next = !actTimelineOpen[a.id];
                        setActTimelineOpen((t) => ({ ...t, [a.id]: next }));
                        if (next && !actTimelineById[a.id]?.events && !actTimelineById[a.id]?.loading) {
                          void loadActivationTimeline(a.id);
                        }
                      }}
                    >
                      {actTimelineOpen[a.id] ? "Hide activation timeline" : "Show activation timeline"}
                    </button>
                  </div>
                  {actTimelineById[a.id]?.loading && actTimelineOpen[a.id] ? (
                    <div className="muted">Loading timeline…</div>
                  ) : null}
                  {actTimelineById[a.id]?.err && actTimelineOpen[a.id] ? (
                    <div className="error" style={{ marginTop: 8 }}>
                      {actTimelineById[a.id]?.err}
                    </div>
                  ) : null}
                  {actTimelineOpen[a.id] && actTimelineById[a.id]?.events ? (
                    <div className="timeline-mini" style={{ marginTop: 10 }}>
                      {actTimelineById[a.id]!.events!.map((ev, i) => (
                        <div key={i}>
                          {ev.at ? `${new Date(String(ev.at)).toLocaleString()} · ` : ""}
                          {String(ev.summary ?? ev.event_type ?? "—")}
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {!a.customer_acknowledged_at ? (
                    <div className="portal-card-section">
                      <div className="portal-card-section-title">Acknowledgement</div>
                    <div className="form-stack">
                      <label>Acknowledge go-live</label>
                      <input
                        placeholder="Your name or role"
                        value={ackContact[a.id] ?? ""}
                        onChange={(e) => setAckContact((x) => ({ ...x, [a.id]: e.target.value }))}
                      />
                      <textarea
                        placeholder="Optional note"
                        value={ackNotes[a.id] ?? ""}
                        onChange={(e) => setAckNotes((x) => ({ ...x, [a.id]: e.target.value }))}
                      />
                      <button type="button" className="secondary" onClick={() => void acknowledgeActivation(a.id)}>
                        Confirm acknowledgement
                      </button>
                    </div>
                    </div>
                  ) : (
                    <div className="item-sub" style={{ marginTop: 8 }}>
                      You acknowledged this on {new Date(a.customer_acknowledged_at).toLocaleString()}.
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        ))
      )}

      <div id="portal-certs" className="portal-section-title portal-anchor">
        Recent certificates
      </div>
      <p className="muted" style={{ padding: "0 18px 8px", margin: 0 }}>
        Compliance documents linked to work we have carried out (read-only snapshot in the portal).
      </p>
      {dash?.recent_certificates && dash.recent_certificates.length > 0 ? (
        <div className="card" style={{ margin: "0 18px 20px" }}>
          <div className="list">
            {dash.recent_certificates.map((c) => (
              <div key={c.id} className="item">
                <div className="item-title">
                  {humanizePortalText(c.type)} · {humanizePortalText(c.status)}
                </div>
                <div className="item-sub">
                  Job {c.job_id.slice(0, 8)}… · {new Date(c.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="muted" style={{ padding: "0 18px 20px" }}>
          No certificates in your portal snapshot yet.
        </div>
      )}

      <div id="portal-jobs" className="portal-section-title portal-anchor">
        Jobs &amp; invoices (summary)
      </div>
      <p className="muted" style={{ padding: "0 18px 12px", margin: 0 }}>
        Open jobs: load live visit status, ETA, and milestones. Invoices: expand for labour/material breakdown;{" "}
        <strong>Record payment</strong> is a demo action for sandbox — real payments go through your agreed process.
      </p>
      <div className="grid" style={{ padding: 0 }}>
        <div className="card">
          <h3>Open jobs</h3>
          <div className="list">
            {(dash?.open_jobs ?? []).slice(0, 12).map((j) => {
              const live = jobLiveById[j.id];
              const eta = live?.data?.eta as Record<string, unknown> | undefined;
              const mapPayload = live?.data?.map_payload as Record<string, unknown> | undefined;
              const timeline = (live?.data?.status_timeline as Array<Record<string, unknown>> | undefined) ?? [];
              const support = live?.data?.support_contact as Record<string, string> | undefined;
              return (
                <div key={j.id} className="item">
                  <div className="item-title">{j.status}</div>
                  <div className="item-sub">{j.address}</div>
                  {j.scheduled_at ? (
                    <div className="item-sub">Scheduled {new Date(j.scheduled_at).toLocaleString()}</div>
                  ) : null}
                  <div className="portal-actions">
                    <button type="button" className="secondary" onClick={() => void loadJobLive(j.id)} disabled={live?.loading}>
                      {live?.loading ? "Loading…" : live?.data ? "Refresh live status" : "Live status & milestones"}
                    </button>
                  </div>
                  {live?.err ? <div className="error" style={{ marginTop: 8 }}>{live.err}</div> : null}
                  {live?.data ? (
                    <div className="timeline-mini" style={{ marginTop: 10 }}>
                      <div>
                        <strong>Visit state:</strong> {String(live.data.customer_tracking_state ?? "—")}
                      </div>
                      {live.data.engineer_on_site ? <div>Engineer marked on site.</div> : null}
                      {live.data.engineer_on_the_way ? <div>Engineer on the way.</div> : null}
                      <PortalEtaSummary eta={eta} />
                      <PortalMapHint mapPayload={mapPayload} />
                      {timeline.length > 0 ? (
                        <>
                          <div style={{ marginTop: 8 }}>Milestones</div>
                          {timeline.slice(0, 8).map((ev, i) => (
                            <div key={i}>
                              {ev.at ? `${new Date(String(ev.at)).toLocaleString()} · ` : ""}
                              {String(ev.title ?? ev.milestone ?? "—")}
                            </div>
                          ))}
                        </>
                      ) : null}
                      {support?.email ? (
                        <div className="item-sub" style={{ marginTop: 8 }}>
                          Support: {support.email}
                          {support.phone ? ` · ${support.phone}` : ""}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
            {(dash?.open_jobs ?? []).length === 0 ? <div className="muted">None in overview.</div> : null}
            {(dash?.upcoming_visits ?? []).length > 0 ? (
              <>
                <div className="divider" style={{ margin: "16px 0" }} />
                <h4 style={{ margin: "0 0 10px", fontSize: 13 }}>Upcoming visits</h4>
                <div className="list">
                  {(dash?.upcoming_visits ?? []).slice(0, 12).map((v) => (
                    <div key={v.job_id} className="item">
                      <div className="item-title">
                        {v.scheduled_at ? new Date(v.scheduled_at).toLocaleString() : "Scheduled TBC"}
                      </div>
                      <div className="item-sub">{v.address}</div>
                      <div className="portal-actions">
                        <button type="button" className="secondary" onClick={() => void loadJobLive(v.job_id)}>
                          Live status
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : null}
          </div>
        </div>
        <div className="card">
          <h3>Outstanding invoices</h3>
          <div className="list">
            {(dash?.outstanding_invoices ?? []).map((inv) => {
              const open = invDetailOpen[inv.id];
              const det = invDetailById[inv.id];
              return (
                <div key={inv.id} className="item">
                  <div className="item-title">
                    {inv.grand_total} {inv.currency} · <span className={pillClass(inv.status)}>{humanizePortalText(inv.status)}</span>
                  </div>
                  <div className="item-sub">Issued {new Date(inv.created_at).toLocaleDateString()}</div>
                  <div className="portal-actions">
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() => {
                        const next = !open;
                        setInvDetailOpen((m) => ({ ...m, [inv.id]: next }));
                        if (next && !det?.data && !det?.loading) void loadInvoiceDetail(inv.id);
                      }}
                    >
                      {open ? "Hide breakdown" : "View breakdown"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void payOutstandingInvoice(inv.id)}
                      disabled={payBusy === inv.id}
                    >
                      {payBusy === inv.id ? "Recording…" : "Record payment (demo)"}
                    </button>
                  </div>
                  {det?.loading && open ? <div className="muted">Loading detail…</div> : null}
                  {det?.err && open ? <div className="error">{det.err}</div> : null}
                  {open && det?.data ? <PortalInvoiceBreakdown data={det.data} /> : null}
                </div>
              );
            })}
            {(dash?.outstanding_invoices ?? []).length === 0 ? <div className="muted">None.</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
