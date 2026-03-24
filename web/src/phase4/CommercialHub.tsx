import React, { useCallback, useEffect, useState } from "react";
type FetchState<T> = { data: T | null; error: string | null };

async function fetchJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(res.status === 403 ? "Not permitted for your role." : t.slice(0, 200) || res.statusText);
  }
  return res.json() as Promise<T>;
}

function rowsToCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const keys = Object.keys(rows[0]);
  const esc = (v: unknown) => {
    const s = v == null ? "" : String(v);
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const lines = [keys.join(",")];
  for (const r of rows) {
    lines.push(keys.map((k) => esc(r[k])).join(","));
  }
  return lines.join("\n");
}

function versionTypeShortLabel(t: string): string {
  const m: Record<string, string> = {
    initial: "Initial window",
    amendment_activation: "Amendment activation",
    manual_update: "Manual update",
  };
  return m[t] ?? t.replace(/_/g, " ");
}

function formatDiffValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") {
    try {
      return JSON.stringify(v);
    } catch {
      return String(v);
    }
  }
  return String(v);
}

function followUpReasonLabel(code: string): string {
  const m: Record<string, string> = {
    released_not_viewed_stale: "Released — not viewed (past days threshold)",
    viewed_no_response_stale: "Viewed — no response (past days threshold)",
    provider_esign_incomplete_stale: "E-sign in flight — not completed (stale)",
    expired_no_response: "Expired / past customer deadline — no response",
    activation_released_not_viewed_stale: "Activation confirmation released — not viewed",
    activation_viewed_not_acknowledged_stale: "Activation viewed — not acknowledged",
    rejected: "Customer rejected",
    counter_requested: "Customer counter-offer",
    needs_follow_up: "Marked needs follow-up",
  };
  return m[code] ?? code.replace(/_/g, " ");
}

async function copyText(text: string): Promise<void> {
  if (!text || !navigator.clipboard) return;
  await navigator.clipboard.writeText(text);
}

/** §5.9 — anchor targets for the jump nav (same order as panels top-to-bottom). */
const COMMERCIAL_HUB_NAV: { id: string; label: string }[] = [
  { id: "hub-needs-action", label: "Needs action" },
  { id: "hub-auto-followup", label: "Automated follow-up" },
  { id: "hub-proposal-queue", label: "Proposal queue" },
  { id: "hub-comm-pipeline", label: "Comm pipeline" },
  { id: "hub-activation-lifecycle", label: "Activation lifecycle" },
  { id: "hub-acceptance-policy", label: "Acceptance policy" },
  { id: "hub-contract-history", label: "Contract history" },
  { id: "hub-comms-hygiene", label: "Comms hygiene" },
  { id: "hub-recurring-jobs", label: "Recurring jobs" },
  { id: "hub-system-jobs-admin", label: "System jobs admin" },
  { id: "hub-automation-runs", label: "Automation runs" },
  { id: "hub-ops-diagnostics", label: "Operational diagnostics" },
  { id: "hub-blockers", label: "Blockers" },
  { id: "hub-integration", label: "Integration" },
  { id: "hub-finance", label: "Finance" },
  { id: "hub-access-tab", label: "Access tab" },
  { id: "hub-repricing", label: "Repricing pipeline" },
  { id: "hub-pending-activations", label: "Pending activations" },
  { id: "hub-amendments", label: "Amendments" },
  { id: "hub-comms-delivery", label: "Comms delivery" },
  { id: "hub-comms-failures", label: "Comms failures" },
  { id: "hub-documents", label: "Documents" },
];

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

export function CommercialHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [needsAction, setNeedsAction] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [lifecycle, setLifecycle] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [versionHistory, setVersionHistory] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [readableOpenKey, setReadableOpenKey] = useState<string | null>(null);
  const [readableCache, setReadableCache] = useState<Record<string, Record<string, unknown>>>({});
  const [readableErr, setReadableErr] = useState<Record<string, string>>({});
  const [readableLoading, setReadableLoading] = useState<Record<string, boolean>>({});
  const [commsHygiene, setCommsHygiene] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [jobsDue, setJobsDue] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [jobFailures, setJobFailures] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [opsDiagnostics, setOpsDiagnostics] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [blockers, setBlockers] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [integration, setIntegration] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [financeQ, setFinanceQ] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [financeRecon, setFinanceRecon] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [financeExportBusy, setFinanceExportBusy] = useState(false);
  const [financeExportErr, setFinanceExportErr] = useState<string | null>(null);
  const [repricingProps, setRepricingProps] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [pendingActivations, setPendingActivations] = useState<FetchState<Record<string, unknown>>>({
    data: null,
    error: null,
  });
  const [amendmentsDash, setAmendmentsDash] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [commsDelivery, setCommsDelivery] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [commsFailures, setCommsFailures] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [policyBlockers, setPolicyBlockers] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [proposalFollowUp, setProposalFollowUp] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [commFollowUpHints, setCommFollowUpHints] = useState<FetchState<Record<string, unknown>>>({
    data: null,
    error: null,
  });
  const [documentsList, setDocumentsList] = useState<FetchState<unknown[]>>({ data: null, error: null });
  const [documentsJobFilter, setDocumentsJobFilter] = useState("");
  const [docDownloadBusyId, setDocDownloadBusyId] = useState<string | null>(null);
  const [docDownloadErr, setDocDownloadErr] = useState<string | null>(null);
  const [systemJobs, setSystemJobs] = useState<FetchState<Record<string, unknown>[]>>({ data: null, error: null });
  const [systemJobRuns, setSystemJobRuns] = useState<FetchState<Record<string, unknown>[]>>({ data: null, error: null });
  const [systemJobsBusy, setSystemJobsBusy] = useState(false);
  const [automationSummary, setAutomationSummary] = useState<FetchState<Record<string, unknown>>>({ data: null, error: null });
  const [automationRuns, setAutomationRuns] = useState<FetchState<Record<string, unknown>[]>>({ data: null, error: null });
  const [automationBusy, setAutomationBusy] = useState(false);
  const [automationRecId, setAutomationRecId] = useState("");
  const [automationProposalId, setAutomationProposalId] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    setReadableOpenKey(null);
    const h = authHeaders;

    const run = async <T,>(
      path: string,
      setter: React.Dispatch<React.SetStateAction<FetchState<T>>>,
    ) => {
      try {
        const data = await fetchJson<T>(`${apiBase}${path}`, h);
        setter({ data, error: null });
      } catch (e) {
        setter({ data: null, error: e instanceof Error ? e.message : String(e) });
      }
    };

    const docQs =
      documentsJobFilter.trim() === ""
        ? "limit=30"
        : `limit=30&related_job_id=${encodeURIComponent(documentsJobFilter.trim())}`;

    await Promise.all([
      run("/contracts/dashboard/commercial-follow-up-needs-action", setNeedsAction),
      run("/contracts/dashboard/activation-customer-lifecycle", setLifecycle),
      run("/contracts/dashboard/version-history-summary?limit=18", setVersionHistory),
      run("/contracts/dashboard/customer-communications-hygiene?limit=40", setCommsHygiene),
      run("/system/dashboard/jobs-due", setJobsDue),
      run("/system/dashboard/job-failures?limit=15", setJobFailures),
      run("/system/dashboard/operations-diagnostics?limit_each=12", setOpsDiagnostics),
      run("/system/dashboard/operations-blockers-overview", setBlockers),
      run("/system/integration-status", setIntegration),
      run("/invoicing/dashboard/finance-queue?limit_queue=100", setFinanceQ),
      run("/invoicing/dashboard/reconciliation-summary", setFinanceRecon),
      run("/contracts/dashboard/repricing-proposals?limit=35", setRepricingProps),
      run("/contracts/dashboard/pending-activations", setPendingActivations),
      run("/contracts/dashboard/amendments?limit=30", setAmendmentsDash),
      run("/contracts/dashboard/customer-communications-delivery", setCommsDelivery),
      run("/contracts/dashboard/customer-communications-failures", setCommsFailures),
      run("/contracts/dashboard/acceptance-policy-blockers?limit_proposals=80", setPolicyBlockers),
      run("/contracts/dashboard/customer-proposal-follow-up?limit=25", setProposalFollowUp),
      run("/contracts/dashboard/customer-communications-follow-up", setCommFollowUpHints),
      run(`/documents?${docQs}`, setDocumentsList),
      run("/system/jobs", setSystemJobs),
      run("/system/job-runs?limit=30", setSystemJobRuns),
      run("/automation/dashboard/summary", setAutomationSummary),
      run("/automation/runs?limit=30", setAutomationRuns),
    ]);
    setBusy(false);
  }, [apiBase, authHeaders, documentsJobFilter]);

  const refreshSystemJobs = useCallback(async () => {
    setSystemJobsBusy(true);
    try {
      const [jobs, runs] = await Promise.all([
        fetchJson<Record<string, unknown>[]>(`${apiBase}/system/jobs`, authHeaders),
        fetchJson<Record<string, unknown>[]>(`${apiBase}/system/job-runs?limit=30`, authHeaders),
      ]);
      setSystemJobs({ data: jobs, error: null });
      setSystemJobRuns({ data: runs, error: null });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setSystemJobs((prev) => ({ data: prev.data, error: msg }));
      setSystemJobRuns((prev) => ({ data: prev.data, error: msg }));
    } finally {
      setSystemJobsBusy(false);
    }
  }, [apiBase, authHeaders]);

  const toggleSystemJobEnabled = useCallback(
    async (jobId: string, enabled: boolean) => {
      setSystemJobsBusy(true);
      try {
        const res = await fetch(`${apiBase}/system/jobs/${encodeURIComponent(jobId)}`, {
          method: "PATCH",
          headers: { ...authHeaders, "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        });
        if (!res.ok) throw new Error((await res.text()).slice(0, 220) || res.statusText);
        await refreshSystemJobs();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setSystemJobs((prev) => ({ data: prev.data, error: msg }));
      } finally {
        setSystemJobsBusy(false);
      }
    },
    [apiBase, authHeaders, refreshSystemJobs],
  );

  const runSystemJobNow = useCallback(
    async (jobId: string, dryRun: boolean) => {
      setSystemJobsBusy(true);
      try {
        const res = await fetch(`${apiBase}/system/jobs/${encodeURIComponent(jobId)}/run`, {
          method: "POST",
          headers: { ...authHeaders, "Content-Type": "application/json" },
          body: JSON.stringify({ dry_run: dryRun }),
        });
        if (!res.ok) throw new Error((await res.text()).slice(0, 220) || res.statusText);
        await refreshSystemJobs();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setSystemJobs((prev) => ({ data: prev.data, error: msg }));
      } finally {
        setSystemJobsBusy(false);
      }
    },
    [apiBase, authHeaders, refreshSystemJobs],
  );

  const retrySystemRun = useCallback(
    async (runId: string) => {
      setSystemJobsBusy(true);
      try {
        const res = await fetch(`${apiBase}/system/job-runs/${encodeURIComponent(runId)}/retry`, {
          method: "POST",
          headers: authHeaders,
        });
        if (!res.ok) throw new Error((await res.text()).slice(0, 220) || res.statusText);
        await refreshSystemJobs();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setSystemJobRuns((prev) => ({ data: prev.data, error: msg }));
      } finally {
        setSystemJobsBusy(false);
      }
    },
    [apiBase, authHeaders, refreshSystemJobs],
  );

  const refreshAutomation = useCallback(async () => {
    setAutomationBusy(true);
    try {
      const [summary, runs] = await Promise.all([
        fetchJson<Record<string, unknown>>(`${apiBase}/automation/dashboard/summary`, authHeaders),
        fetchJson<Record<string, unknown>[]>(`${apiBase}/automation/runs?limit=30`, authHeaders),
      ]);
      setAutomationSummary({ data: summary, error: null });
      setAutomationRuns({ data: runs, error: null });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setAutomationSummary((prev) => ({ data: prev.data, error: msg }));
      setAutomationRuns((prev) => ({ data: prev.data, error: msg }));
    } finally {
      setAutomationBusy(false);
    }
  }, [apiBase, authHeaders]);

  const runForRecommendation = useCallback(async () => {
    const id = automationRecId.trim();
    if (!id) return;
    setAutomationBusy(true);
    try {
      const res = await fetch(`${apiBase}/automation/run-for-recommendation/${encodeURIComponent(id)}`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error((await res.text()).slice(0, 220) || res.statusText);
      setAutomationRecId("");
      await refreshAutomation();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setAutomationRuns((prev) => ({ data: prev.data, error: msg }));
    } finally {
      setAutomationBusy(false);
    }
  }, [apiBase, authHeaders, automationRecId, refreshAutomation]);

  const runForProposal = useCallback(async () => {
    const id = automationProposalId.trim();
    if (!id) return;
    setAutomationBusy(true);
    try {
      const res = await fetch(`${apiBase}/automation/run-for-proposal/${encodeURIComponent(id)}`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error((await res.text()).slice(0, 220) || res.statusText);
      setAutomationProposalId("");
      await refreshAutomation();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setAutomationRuns((prev) => ({ data: prev.data, error: msg }));
    } finally {
      setAutomationBusy(false);
    }
  }, [apiBase, authHeaders, automationProposalId, refreshAutomation]);

  const loadReadableDetail = useCallback(
    async (contractId: string, versionId: string) => {
      const key = `${contractId}:${versionId}`;
      setReadableErr((e) => {
        const n = { ...e };
        delete n[key];
        return n;
      });
      setReadableLoading((m) => ({ ...m, [key]: true }));
      try {
        const data = await fetchJson<Record<string, unknown>>(
          `${apiBase}/contracts/${encodeURIComponent(contractId)}/versions/${encodeURIComponent(versionId)}/readable-change`,
          authHeaders,
        );
        setReadableCache((m) => ({ ...m, [key]: data }));
      } catch (err) {
        setReadableErr((e) => ({
          ...e,
          [key]: err instanceof Error ? err.message : String(err),
        }));
      } finally {
        setReadableLoading((m) => ({ ...m, [key]: false }));
      }
    },
    [apiBase, authHeaders],
  );

  const downloadInvoiceExportCsv = useCallback(async () => {
    setFinanceExportErr(null);
    setFinanceExportBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/export-rows?limit=500`, { headers: authHeaders });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t.slice(0, 220) || res.statusText);
      }
      const rows = (await res.json()) as Record<string, unknown>[];
      const csv = rowsToCsv(rows);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `phi-dps-invoices-export-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setFinanceExportErr(e instanceof Error ? e.message : String(e));
    } finally {
      setFinanceExportBusy(false);
    }
  }, [apiBase, authHeaders]);

  const downloadStoredDocument = useCallback(
    async (documentId: string, filename: string) => {
      setDocDownloadErr(null);
      setDocDownloadBusyId(documentId);
      try {
        const res = await fetch(`${apiBase}/documents/${encodeURIComponent(documentId)}/download`, {
          headers: authHeaders,
        });
        if (!res.ok) {
          const t = await res.text();
          throw new Error(t.slice(0, 200) || res.statusText);
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename || "document";
        a.click();
        URL.revokeObjectURL(url);
      } catch (e) {
        setDocDownloadErr(e instanceof Error ? e.message : String(e));
      } finally {
        setDocDownloadBusyId(null);
      }
    },
    [apiBase, authHeaders],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const na = needsAction.data as Record<string, unknown> | null;
  const naProposals = (na?.proposals as unknown[] | undefined)?.length ?? 0;
  const naAct = (na?.activation_confirmations as unknown[] | undefined)?.length ?? 0;
  const naDrafts = (na?.draft_customer_comms as unknown[] | undefined)?.length ?? 0;
  const naProposalRows = (na?.proposals as Record<string, unknown>[] | undefined) ?? [];
  const naActivationRows = (na?.activation_confirmations as Record<string, unknown>[] | undefined) ?? [];
  const naDraftRows = (na?.draft_customer_comms as Record<string, unknown>[] | undefined) ?? [];
  const naThresholds = na?.thresholds as Record<string, number> | undefined;
  const naGeneratedAt = na?.generated_at ? String(na.generated_at) : null;

  const pf = proposalFollowUp.data as { rows?: Record<string, unknown>[]; count?: number } | null;
  const pfRows = pf?.rows ?? [];

  const pb = policyBlockers.data as Record<string, unknown> | null;
  const pbAmend = (pb?.amendment_creation_blocked as Record<string, unknown>[] | undefined) ?? [];
  const pbAct = (pb?.activation_blocked as Record<string, unknown>[] | undefined) ?? [];
  const pbCounts = pb?.counts as Record<string, number> | undefined;
  const pbMatrix = (pb?.policy_matrix as Record<string, unknown>[] | undefined) ?? [];
  const pbExplainer = pb?.active_mode_explainer as Record<string, unknown> | undefined;
  const pbReqAmend = (pb?.requirements_for_amendment as string[] | undefined) ?? [];
  const pbReqAct = (pb?.requirements_for_activation as string[] | undefined) ?? [];
  const pbEvidenceLegend = pb?.evidence_types_explainer != null ? String(pb.evidence_types_explainer) : "";
  const pbEnvVar = pb?.config_env_var != null ? String(pb.config_env_var) : "PHI_DPS_ACCEPTANCE_POLICY_MODE";

  const cfh = commFollowUpHints.data as Record<string, unknown> | null;
  const cfhProp = (cfh?.repricing_proposal_reminder_candidates as unknown[] | undefined) ?? [];
  const cfhActView = (cfh?.activation_confirmation_view_reminder_candidates as unknown[] | undefined) ?? [];
  const cfhActAck = (cfh?.activation_confirmation_ack_candidates as unknown[] | undefined) ?? [];

  const lc = lifecycle.data as Record<string, unknown> | null;
  const fu = lc?.follow_up_counts as Record<string, number> | undefined;

  const fin = financeQ.data as Record<string, unknown> | null;
  const finCounts = fin?.status_counts as Record<string, number> | undefined;
  const finHeld = (fin?.held_invoices as Record<string, unknown>[] | undefined) ?? [];
  const finAwaitReview = (fin?.unpaid_awaiting_finance_review as Record<string, unknown>[] | undefined) ?? [];
  const finReviewed = (fin?.unpaid_finance_reviewed_ready_to_collect as Record<string, unknown>[] | undefined) ?? [];
  const finExportCols = (fin?.export_column_definitions as Record<string, unknown>[] | undefined) ?? [];
  const finCredit = fin?.credit_notes_and_adjustments as Record<string, unknown> | undefined;

  const recon = financeRecon.data as Record<string, unknown> | null;
  const reconCounts = recon?.counts as Record<string, number> | undefined;
  const reconBuckets = recon?.open_invoice_age_buckets as Record<string, number> | undefined;
  const reconOutstanding = recon?.outstanding_grand_total_open;
  const reconNote = recon?.currencies_note != null ? String(recon.currencies_note) : "";

  const vh = versionHistory.data as Record<string, unknown> | null;
  const vhRecent = (vh?.recent_versions as Record<string, unknown>[] | undefined) ?? [];
  const vhByType = vh?.recent_versions_by_type_counts as Record<string, number> | undefined;

  const od = opsDiagnostics.data as Record<string, unknown> | null;
  const odJobFails = (od?.recurring_job_failures as Record<string, unknown>[] | undefined) ?? [];
  const odActFails = (od?.contract_activation_failures as Record<string, unknown>[] | undefined) ?? [];
  const odDelFails = (od?.customer_communication_delivery_failures as Record<string, unknown>[] | undefined) ?? [];
  const odProvFails = (od?.communication_provider_webhook_failures as Record<string, unknown>[] | undefined) ?? [];
  const odRolloutDels = (od?.rollout_notification_delivery_failures as Record<string, unknown>[] | undefined) ?? [];
  const odRollSigs = (od?.rollout_webhook_invalid_signatures as Record<string, unknown>[] | undefined) ?? [];
  const odCounts = od?.counts as Record<string, number> | undefined;

  const integ = integration.data as Record<string, unknown> | null;
  const comm = integ?.communication as Record<string, unknown> | undefined;
  const esign = integ?.esign as Record<string, unknown> | undefined;

  const activeSuppressions =
    (commsHygiene.data?.active_suppressions as Array<Record<string, unknown>> | undefined) ?? [];
  const pendingSuppressions =
    (commsHygiene.data?.suppressions_pending_review as Array<Record<string, unknown>> | undefined) ?? [];

  const dueJobs = (jobsDue.data as { due?: Array<Record<string, unknown>> } | null)?.due ?? [];
  const failList = (jobFailures.data as { failed_runs?: Array<Record<string, unknown>> } | null)?.failed_runs ?? [];
  const systemJobRows = systemJobs.data ?? [];
  const systemRunRows = systemJobRuns.data ?? [];
  const automationRunRows = automationRuns.data ?? [];
  const automationCounts = (automationSummary.data?.counts as Record<string, number> | undefined) ?? {};

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Commercial & operations hub</h2>
        <p>
          Contract, repricing, amendment, communications, and document signals in one place (Phase 4 admin UX, §5.9).
          Follow-up automation (§5.1), acceptance policy (§5.2), activation lifecycle (§5.3), finance (§5.4), contract history
          &amp; readable diffs (§5.5), deployment/diagnostics context (§5.6–§5.7), and pipeline hints load in the panels
          below. Use <strong>Jump to section</strong> to skip scrolling. Internal and customer portal access groups live on
          the <strong>Access</strong> tab. Holiday feed import and AI drafting live on the <strong>Labour &amp; AI</strong> tab.
          Panels you are not permitted to see show a short error instead of breaking the page.
        </p>
        <div className="row" style={{ marginTop: 12, justifyContent: "flex-start" }}>
          <button type="button" onClick={() => void load()} disabled={busy}>
            {busy ? "Loading…" : "Refresh all panels"}
          </button>
        </div>
      </div>

      <nav className="hub-toc" aria-label="Commercial hub sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          {COMMERCIAL_HUB_NAV.map((item, i) => (
            <React.Fragment key={item.id}>
              {i > 0 ? (
                <span className="hub-toc-sep" aria-hidden>
                  ·
                </span>
              ) : null}
              <a href={`#${item.id}`}>{item.label}</a>
            </React.Fragment>
          ))}
        </div>
      </nav>

      <div id="hub-needs-action" className="card hub-panel hub-anchor">
        <h3>Needs action (commercial follow-up)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Stalled customer workflows from the same rules as recurring scans (staleness thresholds below). Use IDs in contract
          tooling or CRM; refresh pulls a new snapshot.
        </p>
        {needsAction.error ? <div className="hub-err">{needsAction.error}</div> : null}
        {!needsAction.error && na ? (
          <>
            <div className="hub-metric">{naProposals + naAct + naDrafts}</div>
            <div className="hub-sub">
              Proposals: {naProposals} · Activation confirmations: {naAct} · Draft comms: {naDrafts}
            </div>
            {naGeneratedAt ? (
              <div className="hub-sub" style={{ marginTop: 6 }}>
                Snapshot: {new Date(naGeneratedAt).toLocaleString()}
              </div>
            ) : null}
            {naThresholds && Object.keys(naThresholds).length > 0 ? (
              <details style={{ marginTop: 10 }}>
                <summary className="hub-sub" style={{ cursor: "pointer" }}>
                  Staleness thresholds (days)
                </summary>
                <ul className="hub-list-compact" style={{ marginTop: 6 }}>
                  {Object.entries(naThresholds).map(([k, v]) => (
                    <li key={k}>
                      {k.replace(/_/g, " ")}: <strong>{v}</strong>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Stalled repricing proposals (up to 15)</h4>
            {naProposalRows.length === 0 ? (
              <div className="hub-sub">None in this snapshot.</div>
            ) : (
              <ul className="hub-list-compact">
                {naProposalRows.slice(0, 15).map((row, i) => {
                  const pid = String(row.proposal_id ?? "");
                  const reason = String(row.reason_code ?? "—");
                  const days = row.stale_days != null ? String(row.stale_days) : "—";
                  const arid = row.acceptance_record_id != null ? String(row.acceptance_record_id) : "";
                  return (
                    <li key={pid || `p-${i}-${reason}`} style={{ marginBottom: 10 }}>
                      <div>
                        <strong>{followUpReasonLabel(reason)}</strong>
                        {days !== "—" ? ` · ~${days}d stale` : ""}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        ref {String(row.proposal_reference ?? "—")} · contract{" "}
                        <code style={{ fontSize: 11 }}>{String(row.contract_id ?? "").slice(0, 8)}…</code>
                      </div>
                      <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                        {pid ? (
                          <button type="button" className="secondary" onClick={() => void copyText(pid)}>
                            Copy proposal id
                          </button>
                        ) : null}
                        {arid ? (
                          <button type="button" className="secondary" onClick={() => void copyText(arid)}>
                            Copy e-sign record id
                          </button>
                        ) : null}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Stalled activation confirmations (up to 15)</h4>
            {naActivationRows.length === 0 ? (
              <div className="hub-sub">None in this snapshot.</div>
            ) : (
              <ul className="hub-list-compact">
                {naActivationRows.slice(0, 15).map((row, i) => {
                  const cid = String(row.confirmation_id ?? "");
                  const reason = String(row.reason_code ?? "—");
                  const days = row.stale_days != null ? String(row.stale_days) : "—";
                  return (
                    <li key={cid || `a-${i}-${reason}`} style={{ marginBottom: 10 }}>
                      <div>
                        <strong>{followUpReasonLabel(reason)}</strong>
                        {days !== "—" ? ` · ~${days}d stale` : ""}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        ref {String(row.confirmation_reference ?? "—")} · contract{" "}
                        <code style={{ fontSize: 11 }}>{String(row.contract_id ?? "").slice(0, 8)}…</code>
                      </div>
                      {cid ? (
                        <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(cid)}>
                          Copy confirmation id
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Open draft customer comms (up to 15)</h4>
            {naDraftRows.length === 0 ? (
              <div className="hub-sub">None in this snapshot.</div>
            ) : (
              <ul className="hub-list-compact">
                {naDraftRows.slice(0, 15).map((row, i) => {
                  const commId = String(row.communication_id ?? "");
                  return (
                    <li key={commId || `d-${i}`} style={{ marginBottom: 10 }}>
                      <div>
                        <strong>{String(row.communication_type ?? "—")}</strong> · status {String(row.status ?? "—")}
                        {row.stale_days != null ? ` · ~${String(row.stale_days)}d since created` : ""}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        contract <code style={{ fontSize: 11 }}>{String(row.contract_id ?? "").slice(0, 8)}…</code>
                        {row.source_entity_type ? ` · source ${String(row.source_entity_type)}` : ""}
                      </div>
                      {commId ? (
                        <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(commId)}>
                          Copy communication id
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </>
        ) : null}
      </div>

      <div id="hub-auto-followup" className="card hub-panel hub-anchor">
        <h3>Automated follow-up (recurring jobs)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          §5.1 backend: system recurring jobs create <strong>draft</strong> customer communications (deduped) and internal
          tasks only — no silent sends. Recipient suppressions skip new reminder drafts when the CRM primary email matches
          an active block.
        </p>
        <ul className="hub-list-compact">
          <li>
            <code>proposal_follow_up_scan</code> — stale released-not-viewed &amp; e-sign-in-flight reminders; viewed-no-response
            &amp; expired internal tasks.
          </li>
          <li>
            <code>activation_confirmation_follow_up_scan</code> — stale activation confirmation view + acknowledgement
            drafts.
          </li>
        </ul>
        <div className="hub-sub" style={{ marginTop: 8 }}>
          Job payloads use the same day thresholds as the needs-action panel (see <code>released_no_view_days</code>,{" "}
          <code>released_not_viewed_days</code>, etc.).
        </div>
      </div>

      <div id="hub-proposal-queue" className="card hub-panel hub-anchor">
        <h3>Proposal follow-up queue</h3>
        {proposalFollowUp.error ? <div className="hub-err">{proposalFollowUp.error}</div> : null}
        {!proposalFollowUp.error && pf ? (
          <>
            <div className="hub-metric">{Number(pf.count ?? pfRows.length)}</div>
            <div className="hub-sub">Rejected / counter / needs_follow_up / expired / viewed-no-response (sample).</div>
            <ul className="hub-list-compact">
              {pfRows.slice(0, 12).map((row, i) => {
                const pid = String(row.proposal_id ?? "");
                return (
                  <li key={pid || `pf-${i}`} style={{ marginBottom: 8 }}>
                    <div>
                      <strong>{String(row.reason ?? "—")}</strong> · {String(row.priority ?? "—")} ·{" "}
                      {String(row.proposal_reference ?? "—")}
                    </div>
                    {pid ? (
                      <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(pid)}>
                        Copy proposal id
                      </button>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </>
        ) : null}
      </div>

      <div id="hub-comm-pipeline" className="card hub-panel hub-anchor">
        <h3>Communication pipeline hints</h3>
        {commFollowUpHints.error ? <div className="hub-err">{commFollowUpHints.error}</div> : null}
        {!commFollowUpHints.error && cfh ? (
          <ul className="hub-list-compact">
            <li>Repricing reminder candidates (7d heuristic): {cfhProp.length}</li>
            <li>Activation &quot;not viewed&quot; reminder candidates: {cfhActView.length}</li>
            <li>Activation viewed, awaiting acknowledgement: {cfhActAck.length}</li>
          </ul>
        ) : null}
      </div>

      <div id="hub-activation-lifecycle" className="card hub-panel hub-anchor">
        <h3>Activation customer lifecycle</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          §5.3: set <code style={{ fontSize: 11 }}>PHI_DPS_AUTO_CREATE_ACTIVATION_CONFIRMATION_ON_ACTIVATE=1</code> to auto-create
          an activation confirmation in pending generation after a successful amendment activation. Stale confirmation follow-ups
          are drafted by <code style={{ fontSize: 11 }}>activation_confirmation_follow_up_scan</code> (see above).
        </p>
        {lifecycle.error ? <div className="hub-err">{lifecycle.error}</div> : null}
        {!lifecycle.error && fu ? (
          <ul className="hub-list-compact">
            <li>Released, not viewed: {fu.released_not_viewed ?? 0}</li>
            <li>Viewed, not acknowledged: {fu.viewed_not_acknowledged ?? 0}</li>
            <li>Withdrawn: {fu.withdrawn_confirmations ?? 0}</li>
            <li>Activated without open confirmation: {fu.activated_without_open_confirmation ?? 0}</li>
          </ul>
        ) : null}
      </div>

      <div id="hub-acceptance-policy" className="card hub-panel hub-anchor">
        <h3>Acceptance policy &amp; readiness (§5.2)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          One view for active mode, what it means for <strong>amendment</strong> vs <strong>activation</strong>, requirement
          checklists, the full review matrix, and live blockers. Tune policy with env{" "}
          <code style={{ fontSize: 11 }}>{pbEnvVar}</code> (see <code style={{ fontSize: 11 }}>.env.example</code>).
        </p>
        {policyBlockers.error ? <div className="hub-err">{policyBlockers.error}</div> : null}
        {!policyBlockers.error && pb ? (
          <>
            <div className="hub-sub" style={{ marginTop: 8 }}>
              <strong>Active mode:</strong> {String(pb.acceptance_policy_mode ?? "—")}
              {pbExplainer?.label ? ` — ${String(pbExplainer.label)}` : ""}
            </div>
            {pbExplainer?.customer_evidence ? (
              <p className="hub-sub" style={{ marginTop: 6 }}>
                {String(pbExplainer.customer_evidence)}
              </p>
            ) : null}
            {pbExplainer?.notes ? (
              <p className="hub-sub" style={{ marginTop: 4 }}>
                {String(pbExplainer.notes)}
              </p>
            ) : null}

            <h4 style={{ fontSize: 13, marginTop: 12 }}>Checklist — create amendment</h4>
            <ul className="hub-list-compact">
              {pbReqAmend.length > 0 ? (
                pbReqAmend.map((line, i) => <li key={i}>{line}</li>)
              ) : (
                <li>No extra policy requirements in this mode.</li>
              )}
            </ul>
            <h4 style={{ fontSize: 13, marginTop: 10 }}>Checklist — run activation</h4>
            <ul className="hub-list-compact">
              {pbReqAct.length > 0 ? (
                pbReqAct.map((line, i) => <li key={i}>{line}</li>)
              ) : (
                <li>No extra policy requirements in this mode.</li>
              )}
            </ul>
            {pbEvidenceLegend ? (
              <p className="hub-sub" style={{ marginTop: 10, fontSize: 12 }}>
                <strong>Evidence types:</strong> {pbEvidenceLegend}
              </p>
            ) : null}

            <details style={{ marginTop: 12 }}>
              <summary className="hub-sub" style={{ cursor: "pointer" }}>
                Full policy review matrix (all modes)
              </summary>
              <ul className="hub-list-compact" style={{ marginTop: 8 }}>
                {pbMatrix.map((row) => (
                  <li key={String(row.mode)} style={{ marginBottom: 12 }}>
                    <strong>{String(row.label ?? row.mode)}</strong> <code style={{ fontSize: 10 }}>{String(row.mode)}</code>
                    <div className="hub-sub" style={{ marginTop: 4 }}>
                      Customer evidence: {String(row.customer_evidence ?? "—")}
                    </div>
                    {Array.isArray(row.blocks_amendment_on) && (row.blocks_amendment_on as unknown[]).length > 0 ? (
                      <div className="hub-sub" style={{ marginTop: 4 }}>
                        Blocks amendment: {(row.blocks_amendment_on as string[]).join(" · ")}
                      </div>
                    ) : (
                      <div className="hub-sub" style={{ marginTop: 4 }}>
                        Blocks amendment: (none)
                      </div>
                    )}
                    {Array.isArray(row.blocks_activation_on) && (row.blocks_activation_on as unknown[]).length > 0 ? (
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        Blocks activation: {(row.blocks_activation_on as string[]).join(" · ")}
                      </div>
                    ) : (
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        Blocks activation: (none)
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </details>

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Live blockers</h4>
            <ul className="hub-list-compact">
              <li>Amendment creation blocked: {pbCounts?.amendment_creation_blocked ?? pbAmend.length}</li>
              <li>Activation blocked: {pbCounts?.activation_blocked ?? pbAct.length}</li>
            </ul>
            {pbAmend.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Amendment (sample)</div>
                <ul className="hub-list-compact">
                  {pbAmend.slice(0, 8).map((row, i) => {
                    const pid = String(row.proposal_id ?? "");
                    return (
                      <li key={pid || `ab-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {(row.reason_messages as string[] | undefined)?.join(" ") ||
                            String((row.reasons as unknown[] | undefined)?.[0] ?? "—")}
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          {String(row.proposal_reference ?? "—")}
                        </div>
                        {pid ? (
                          <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(pid)}>
                            Copy proposal id
                          </button>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {pbAct.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Activation (sample)</div>
                <ul className="hub-list-compact">
                  {pbAct.slice(0, 8).map((row, i) => {
                    const aid = String(row.amendment_id ?? "");
                    const spid = row.source_proposal_id != null ? String(row.source_proposal_id) : "";
                    return (
                      <li key={aid || `act-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {(row.reason_messages as string[] | undefined)?.join(" ") ||
                            String((row.reasons as unknown[] | undefined)?.[0] ?? "—")}
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          {String(row.amendment_reference ?? "—")}
                        </div>
                        <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                          {aid ? (
                            <button type="button" className="secondary" onClick={() => void copyText(aid)}>
                              Copy amendment id
                            </button>
                          ) : null}
                          {spid ? (
                            <button type="button" className="secondary" onClick={() => void copyText(spid)}>
                              Copy source proposal id
                            </button>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <div id="hub-contract-history" className="card hub-panel hub-anchor">
        <h3>Contract history &amp; readable diffs (§5.5)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Recent version rows from the dashboard summary; expand a row for categorized field-level before/after (no raw JSON
          required for a quick explanation). Copy IDs for contract tooling.
        </p>
        {versionHistory.error ? <div className="hub-err">{versionHistory.error}</div> : null}
        {!versionHistory.error && vh ? (
          <>
            {vhByType && Object.keys(vhByType).length > 0 ? (
              <ul className="hub-list-compact" style={{ marginBottom: 10 }}>
                {Object.entries(vhByType).map(([k, n]) => (
                  <li key={k}>
                    {versionTypeShortLabel(k)}: <strong>{n}</strong> in this window
                  </li>
                ))}
              </ul>
            ) : null}
            {vhRecent.length === 0 ? (
              <div className="hub-sub">No contract versions in this snapshot.</div>
            ) : (
              <ul className="hub-list-compact">
                {vhRecent.map((r) => {
                  const cid = String(r.contract_id ?? "");
                  const vid = String(r.version_id ?? "");
                  const key = `${cid}:${vid}`;
                  const open = readableOpenKey === key;
                  const detail = readableCache[key];
                  const loading = readableLoading[key];
                  const err = readableErr[key];
                  const fullSum = r.human_readable_summary as string | null | undefined;
                  const summaryLine =
                    fullSum && fullSum.length > 140 ? `${fullSum.slice(0, 140)}…` : fullSum || "";
                  const code = r.contract_code != null ? String(r.contract_code) : "";
                  return (
                    <li key={vid || key} style={{ marginBottom: 12 }}>
                      <div>
                        <strong>{code || cid.slice(0, 10)}</strong>
                        {r.is_active ? (
                          <span className="hub-sub" style={{ marginLeft: 8 }}>
                            · active window
                          </span>
                        ) : null}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        v{String(r.version_number ?? "—")} · {versionTypeShortLabel(String(r.version_type ?? ""))}
                        {r.created_at ? ` · ${String(r.created_at).slice(0, 16)}` : ""}
                      </div>
                      {summaryLine ? <div className="hub-sub" style={{ marginTop: 4 }}>{summaryLine}</div> : null}
                      <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 6 }}>
                        {cid ? (
                          <button type="button" className="secondary" onClick={() => void copyText(cid)}>
                            Copy contract id
                          </button>
                        ) : null}
                        {vid ? (
                          <button type="button" className="secondary" onClick={() => void copyText(vid)}>
                            Copy version id
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => {
                            if (open) {
                              setReadableOpenKey(null);
                            } else {
                              setReadableOpenKey(key);
                              void loadReadableDetail(cid, vid);
                            }
                          }}
                        >
                          {open ? "Hide field-level diff" : "Show field-level diff"}
                        </button>
                      </div>
                      {open ? (
                        <div style={{ marginTop: 10, paddingLeft: 8, borderLeft: "2px solid var(--border, #ccc)" }}>
                          {loading ? <div className="hub-sub">Loading readable change…</div> : null}
                          {err ? <div className="hub-err">{err}</div> : null}
                          {!loading && !err && detail ? (
                            <>
                              <div className="hub-sub" style={{ marginBottom: 6 }}>
                                {String(detail.version_type_explanation ?? "")}
                              </div>
                              {detail.headline ? (
                                <div style={{ marginBottom: 8, fontSize: 13 }}>{String(detail.headline)}</div>
                              ) : null}
                              {Array.isArray(detail.by_category) && (detail.by_category as unknown[]).length > 0 ? (
                                <div style={{ marginBottom: 8 }}>
                                  <div className="hub-sub" style={{ marginBottom: 4 }}>
                                    Changes by category
                                  </div>
                                  <ul className="hub-list-compact">
                                    {(detail.by_category as Record<string, unknown>[]).map((bc, i) => (
                                      <li key={i}>
                                        <strong>{String(bc.category_display ?? bc.category ?? "—")}</strong>
                                        {Array.isArray(bc.fields) && bc.fields.length > 0
                                          ? `: ${(bc.fields as string[]).join(", ")}`
                                          : null}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              ) : null}
                              {Array.isArray(detail.changes) && (detail.changes as unknown[]).length > 0 ? (
                                <table className="hub-table" style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                                  <thead>
                                    <tr>
                                      <th style={{ textAlign: "left", padding: "4px 6px" }}>Field</th>
                                      <th style={{ textAlign: "left", padding: "4px 6px" }}>Category</th>
                                      <th style={{ textAlign: "left", padding: "4px 6px" }}>Before</th>
                                      <th style={{ textAlign: "left", padding: "4px 6px" }}>After</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {(detail.changes as Record<string, unknown>[]).map((ch, i) => (
                                      <tr key={i}>
                                        <td style={{ padding: "4px 6px", verticalAlign: "top" }}>
                                          {String(ch.field_label ?? ch.field ?? "—")}
                                        </td>
                                        <td style={{ padding: "4px 6px", verticalAlign: "top" }}>
                                          {String(ch.category_display ?? ch.category ?? "—")}
                                        </td>
                                        <td style={{ padding: "4px 6px", verticalAlign: "top", wordBreak: "break-word" }}>
                                          {formatDiffValue(ch.before)}
                                        </td>
                                        <td style={{ padding: "4px 6px", verticalAlign: "top", wordBreak: "break-word" }}>
                                          {formatDiffValue(ch.after)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <div className="hub-sub">No structured field changes on this version (e.g. baseline row).</div>
                              )}
                              {detail.manual_update_reason != null && String(detail.manual_update_reason).trim() !== "" ? (
                                <div className="hub-sub" style={{ marginTop: 8 }}>
                                  Manual reason: {String(detail.manual_update_reason)}
                                </div>
                              ) : null}
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </>
        ) : null}
      </div>

      <div id="hub-comms-hygiene" className="card hub-panel hub-anchor">
        <h3>Communications hygiene</h3>
        {commsHygiene.error ? <div className="hub-err">{commsHygiene.error}</div> : null}
        {!commsHygiene.error && commsHygiene.data ? (
          <>
            <ul className="hub-list-compact">
              <li>
                Bad / failed deliveries (sample):{" "}
                {(commsHygiene.data.recent_failed_or_bad_deliveries as unknown[] | undefined)?.length ?? 0}
              </li>
              <li>Active suppressions: {activeSuppressions.length}</li>
              <li>
                Pending manual review:{" "}
                {(commsHygiene.data.suppressions_pending_review as unknown[] | undefined)?.length ?? 0}
              </li>
              <li>Recent provider events: {(commsHygiene.data.recent_provider_events as unknown[] | undefined)?.length ?? 0}</li>
            </ul>
            {activeSuppressions.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Active suppressions (sample)</div>
                <ul className="hub-list-compact">
                  {activeSuppressions.slice(0, 10).map((s, i) => (
                    <li key={i}>
                      <span>
                        {String(s.recipient_email_normalized ?? "—")} · customer {String(s.customer_id ?? "").slice(0, 8)}… ·{" "}
                        {String(s.kind ?? "—")}
                        {s.requires_manual_review ? " · review" : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {pendingSuppressions.length > 0 ? (
              <div style={{ marginTop: 12 }}>
                <div className="hub-sub">Pending manual review (needs action)</div>
                <ul className="hub-list-compact">
                  {pendingSuppressions.slice(0, 10).map((s, i) => (
                    <li key={`p-${i}`}>
                      <span>
                        {String(s.recipient_email_normalized ?? "—")} · customer {String(s.customer_id ?? "").slice(0, 8)}… ·{" "}
                        {String(s.kind ?? "—")}
                        {s.last_seen_at ? ` · seen ${String(s.last_seen_at).slice(0, 16)}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <div id="hub-recurring-jobs" className="card hub-panel hub-anchor">
        <h3>Recurring jobs</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Production: run due jobs on a schedule with a <strong>single runner</strong> per environment — see{" "}
          <strong>DEPLOYMENT.md</strong> (§5.8) for cron and <code>run_due_recurring_jobs.py</code>.
        </p>
        {jobsDue.error ? <div className="hub-err">{jobsDue.error}</div> : null}
        {jobFailures.error ? <div className="hub-err">{jobFailures.error}</div> : null}
        {!jobsDue.error && jobsDue.data ? (
          <>
            <div className="hub-metric">{dueJobs.length}</div>
            <div className="hub-sub">Jobs due now (cron should process these).</div>
            <ul className="hub-list-compact">
              {dueJobs.slice(0, 8).map((j, i) => (
                <li key={i}>
                  {String(j.name ?? j.job_key)} · next {j.next_run_at ? String(j.next_run_at).slice(0, 16) : "—"}
                </li>
              ))}
            </ul>
          </>
        ) : null}
        {!jobFailures.error && jobFailures.data ? (
          <>
            <div className="hub-sub" style={{ marginTop: 10 }}>
              Failed runs (latest {failList.length}).
            </div>
            <ul className="hub-list-compact">
              {failList.slice(0, 6).map((r, i) => (
                <li key={i}>
                  {String(r.job_key)} · {String(r.error ?? "").slice(0, 80)}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>

      <div id="hub-system-jobs-admin" className="card hub-panel hub-anchor">
        <h3>System jobs & runs</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Lightweight control surface for recurring jobs: enable/disable, run now (dry/live), and retry failed runs.
        </p>
        <div className="row" style={{ marginTop: 8, flexWrap: "wrap", gap: 8 }}>
          <button type="button" className="secondary" onClick={() => void refreshSystemJobs()} disabled={systemJobsBusy}>
            {systemJobsBusy ? "Refreshing…" : "Refresh jobs and runs"}
          </button>
        </div>
        {systemJobs.error ? <div className="hub-err" style={{ marginTop: 8 }}>{systemJobs.error}</div> : null}
        {systemJobRuns.error ? <div className="hub-err" style={{ marginTop: 8 }}>{systemJobRuns.error}</div> : null}
        <h4 style={{ fontSize: 13, marginTop: 12 }}>Jobs ({systemJobRows.length})</h4>
        <ul className="hub-list-compact">
          {systemJobRows.slice(0, 12).map((j, i) => {
            const jid = String(j.id ?? "");
            const enabled = Boolean(j.enabled);
            return (
              <li key={jid || `sj-${i}`} style={{ marginBottom: 10 }}>
                <div>
                  <strong>{String(j.name ?? j.job_key ?? "—")}</strong> · enabled {String(enabled)}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  {String(j.job_key ?? "—")} · next {j.next_run_at ? String(j.next_run_at).slice(0, 16) : "—"}
                </div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                  <button type="button" className="secondary" disabled={!jid || systemJobsBusy || enabled} onClick={() => void toggleSystemJobEnabled(jid, true)}>
                    Enable
                  </button>
                  <button type="button" className="secondary" disabled={!jid || systemJobsBusy || !enabled} onClick={() => void toggleSystemJobEnabled(jid, false)}>
                    Disable
                  </button>
                  <button type="button" className="secondary" disabled={!jid || systemJobsBusy} onClick={() => void runSystemJobNow(jid, true)}>
                    Run dry
                  </button>
                  <button type="button" className="secondary" disabled={!jid || systemJobsBusy} onClick={() => void runSystemJobNow(jid, false)}>
                    Run live
                  </button>
                </div>
              </li>
            );
          })}
          {systemJobRows.length === 0 ? <li>No system jobs loaded.</li> : null}
        </ul>
        <h4 style={{ fontSize: 13, marginTop: 12 }}>Recent runs ({systemRunRows.length})</h4>
        <ul className="hub-list-compact">
          {systemRunRows.slice(0, 12).map((r, i) => {
            const rid = String(r.id ?? "");
            const status = String(r.status ?? "—");
            return (
              <li key={rid || `sr-${i}`} style={{ marginBottom: 8 }}>
                <div>
                  {String(r.job_key ?? "—")} · {status} · {r.dry_run ? "dry" : "live"}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  {r.started_at ? String(r.started_at).slice(0, 16) : "—"} · {String(r.result_summary ?? "").slice(0, 90)}
                </div>
                {status === "failed" ? (
                  <button
                    type="button"
                    className="secondary"
                    style={{ marginTop: 4 }}
                    disabled={!rid || systemJobsBusy}
                    onClick={() => void retrySystemRun(rid)}
                  >
                    Retry run
                  </button>
                ) : null}
              </li>
            );
          })}
          {systemRunRows.length === 0 ? <li>No runs loaded.</li> : null}
        </ul>
      </div>

      <div id="hub-automation-runs" className="card hub-panel hub-anchor">
        <h3>Automation runs</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Run low-risk automation by recommendation/proposal and monitor recent outcomes.
        </p>
        <div className="row" style={{ marginTop: 8, flexWrap: "wrap", gap: 8 }}>
          <button type="button" className="secondary" onClick={() => void refreshAutomation()} disabled={automationBusy}>
            {automationBusy ? "Refreshing…" : "Refresh automation"}
          </button>
        </div>
        {automationSummary.error ? <div className="hub-err" style={{ marginTop: 8 }}>{automationSummary.error}</div> : null}
        {automationRuns.error ? <div className="hub-err" style={{ marginTop: 8 }}>{automationRuns.error}</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 10 }}>
          <li>Total runs (window): {Number(automationCounts.total_runs ?? 0)}</li>
          <li>Succeeded: {Number(automationCounts.succeeded ?? 0)}</li>
          <li>Failed: {Number(automationCounts.failed ?? 0)}</li>
          <li>Skipped: {Number(automationCounts.skipped ?? 0)}</li>
        </ul>
        <h4 style={{ fontSize: 13, marginTop: 12 }}>Run for recommendation</h4>
        <input
          style={{ width: "100%", maxWidth: 460, marginTop: 4 }}
          value={automationRecId}
          onChange={(e) => setAutomationRecId(e.target.value)}
          placeholder="Recommendation UUID"
        />
        <button type="button" style={{ marginTop: 6 }} disabled={automationBusy || !automationRecId.trim()} onClick={() => void runForRecommendation()}>
          Trigger recommendation automation
        </button>
        <h4 style={{ fontSize: 13, marginTop: 12 }}>Run for proposal</h4>
        <input
          style={{ width: "100%", maxWidth: 460, marginTop: 4 }}
          value={automationProposalId}
          onChange={(e) => setAutomationProposalId(e.target.value)}
          placeholder="Proposal UUID"
        />
        <button type="button" style={{ marginTop: 6 }} disabled={automationBusy || !automationProposalId.trim()} onClick={() => void runForProposal()}>
          Trigger proposal automation
        </button>
        <h4 style={{ fontSize: 13, marginTop: 12 }}>Recent runs ({automationRunRows.length})</h4>
        <ul className="hub-list-compact">
          {automationRunRows.slice(0, 15).map((r, i) => (
            <li key={String(r.id ?? `ar-${i}`)} style={{ marginBottom: 8 }}>
              <div>
                {String(r.automation_type ?? "—")} · {String(r.status ?? "—")} · {String(r.trigger_entity_type ?? "—")}
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                {String(r.trigger_entity_id ?? "").slice(0, 12)}… · {r.created_at ? String(r.created_at).slice(0, 16) : "—"}
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                {String(r.result_summary ?? "").slice(0, 120)}
              </div>
            </li>
          ))}
          {automationRunRows.length === 0 ? <li>No automation runs loaded.</li> : null}
        </ul>
      </div>

      <div id="hub-ops-diagnostics" className="card hub-panel hub-anchor">
        <h3>Operational diagnostics (§5.7)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Same payload as <code>GET /system/dashboard/operations-diagnostics</code> — jobs, activations, outbound comms
          deliveries, inbound comms webhook processing failures, rollout notification dead-letters, and invalid rollout
          webhook signatures. Enable <code>PHI_DPS_LOG_JSON_ACCESS=1</code> for structured HTTP logs (see DEPLOYMENT.md).
        </p>
        {opsDiagnostics.error ? <div className="hub-err">{opsDiagnostics.error}</div> : null}
        {!opsDiagnostics.error && od ? (
          <>
            <ul className="hub-list-compact">
              <li>
                Recurring job failures (sample): <strong>{odCounts?.recurring_job_failures_shown ?? odJobFails.length}</strong>
              </li>
              <li>
                Activation failures (sample): <strong>{odCounts?.activation_failures_shown ?? odActFails.length}</strong>
              </li>
              <li>
                Comms delivery failures (sample):{" "}
                <strong>{odCounts?.communication_delivery_failures_shown ?? odDelFails.length}</strong>
              </li>
              <li>
                Comms provider webhook failures:{" "}
                <strong>{odCounts?.communication_provider_webhook_failures_shown ?? odProvFails.length}</strong>
              </li>
              <li>
                Rollout notification failures / dead-letter:{" "}
                <strong>{odCounts?.rollout_notification_delivery_failures_shown ?? odRolloutDels.length}</strong>
              </li>
              <li>
                Invalid rollout webhook signatures:{" "}
                <strong>{odCounts?.rollout_webhook_invalid_signatures_shown ?? odRollSigs.length}</strong>
              </li>
            </ul>
            {odJobFails.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Recurring job failures</div>
                <ul className="hub-list-compact">
                  {odJobFails.slice(0, 6).map((r, i) => {
                    const rid = String(r.id ?? "");
                    return (
                      <li key={rid || `jf-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {String(r.job_key ?? "—")} · {String(r.error_message ?? "").slice(0, 120) || "—"}
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          {r.started_at ? String(r.started_at).slice(0, 16) : ""}
                        </div>
                        {rid ? (
                          <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(rid)}>
                            Copy run id
                          </button>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odActFails.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Contract activation failures</div>
                <ul className="hub-list-compact">
                  {odActFails.slice(0, 6).map((r, i) => {
                    const rid = String(r.id ?? "");
                    const cid = r.contract_id != null ? String(r.contract_id) : "";
                    return (
                      <li key={rid || `af-${i}`} style={{ marginBottom: 8 }}>
                        <div>{String(r.result_summary ?? "—").slice(0, 140)}</div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          contract {cid.slice(0, 8)}… · {String(r.run_type ?? "—")}
                        </div>
                        <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                          {rid ? (
                            <button type="button" className="secondary" onClick={() => void copyText(rid)}>
                              Copy run id
                            </button>
                          ) : null}
                          {cid ? (
                            <button type="button" className="secondary" onClick={() => void copyText(cid)}>
                              Copy contract id
                            </button>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odDelFails.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Customer communication delivery failures</div>
                <ul className="hub-list-compact">
                  {odDelFails.slice(0, 6).map((r, i) => {
                    const did = String(r.id ?? "");
                    const commId = r.communication_id != null ? String(r.communication_id) : "";
                    return (
                      <li key={did || `df-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {String(r.channel ?? "—")} · {String(r.provider_name ?? "—")} ·{" "}
                          {String(r.error_message ?? r.error_code ?? "—").slice(0, 120)}
                        </div>
                        <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                          {did ? (
                            <button type="button" className="secondary" onClick={() => void copyText(did)}>
                              Copy delivery id
                            </button>
                          ) : null}
                          {commId ? (
                            <button type="button" className="secondary" onClick={() => void copyText(commId)}>
                              Copy communication id
                            </button>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odProvFails.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Communication provider webhook processing failures</div>
                <ul className="hub-list-compact">
                  {odProvFails.slice(0, 6).map((r, i) => {
                    const eid = String(r.id ?? "");
                    return (
                      <li key={eid || `pf-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {String(r.provider_name ?? "—")} · {String(r.event_type ?? "—")} ·{" "}
                          {String(r.error_message ?? "—").slice(0, 120)}
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          {r.received_at ? String(r.received_at).slice(0, 16) : ""}
                        </div>
                        {eid ? (
                          <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(eid)}>
                            Copy provider event id
                          </button>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odRolloutDels.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Rollout notification deliveries (failed / dead-letter)</div>
                <ul className="hub-list-compact">
                  {odRolloutDels.slice(0, 6).map((r, i) => {
                    const did = String(r.id ?? "");
                    const aid = r.alert_id != null ? String(r.alert_id) : "";
                    return (
                      <li key={did || `rd-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {String(r.channel ?? "—")} · {String(r.status ?? "—")} · attempts {String(r.attempts ?? "—")}
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>{String(r.last_error ?? "").slice(0, 120)}</div>
                        <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                          {did ? (
                            <button type="button" className="secondary" onClick={() => void copyText(did)}>
                              Copy delivery id
                            </button>
                          ) : null}
                          {aid ? (
                            <button type="button" className="secondary" onClick={() => void copyText(aid)}>
                              Copy alert id
                            </button>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odRollSigs.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <div className="hub-sub">Rollout webhooks — invalid HMAC signature</div>
                <ul className="hub-list-compact">
                  {odRollSigs.slice(0, 6).map((r, i) => {
                    const eid = String(r.id ?? "");
                    return (
                      <li key={eid || `rs-${i}`} style={{ marginBottom: 8 }}>
                        <div>
                          {String(r.channel ?? "—")} · external {String(r.external_event_id ?? "—").slice(0, 24)}…
                        </div>
                        <div className="hub-sub" style={{ marginTop: 2 }}>
                          {r.created_at ? String(r.created_at).slice(0, 16) : ""} · processed: {String(r.processed ?? "—")}
                        </div>
                        {eid ? (
                          <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(eid)}>
                            Copy webhook event id
                          </button>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null}
            {odJobFails.length === 0 &&
            odActFails.length === 0 &&
            odDelFails.length === 0 &&
            odProvFails.length === 0 &&
            odRolloutDels.length === 0 &&
            odRollSigs.length === 0 ? (
              <div className="hub-sub" style={{ marginTop: 8 }}>
                No failure rows in this snapshot (good).
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <div id="hub-blockers" className="card hub-panel hub-anchor">
        <h3>Cross-domain blockers (counts)</h3>
        {blockers.error ? <div className="hub-err">{blockers.error}</div> : null}
        {!blockers.error && blockers.data ? (
          <pre className="item-body" style={{ fontSize: 11, maxHeight: 140, overflow: "auto" }}>
            {JSON.stringify(blockers.data, null, 2)}
          </pre>
        ) : null}
      </div>

      <div id="hub-integration" className="card hub-panel hub-anchor">
        <h3>Integration status</h3>
        {integration.error ? <div className="hub-err">{integration.error}</div> : null}
        {!integration.error && integ ? (
          <ul className="hub-list-compact">
            <li>Database: {integ.database_reachable ? "reachable" : "unreachable"}</li>
            <li>
              Email: {String(comm?.enabled)} / provider {String(comm?.email_provider)} (from configured:{" "}
              {String(comm?.from_email_configured)})
            </li>
            <li>
              E-sign: {String(esign?.enabled)} / {String(esign?.provider)} (ready: {String(esign?.integration_ready)})
            </li>
          </ul>
        ) : null}
      </div>

      <div id="hub-finance" className="card hub-panel hub-anchor">
        <h3>Finance operations (§5.4)</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Invoice states: <strong>unpaid</strong> → optional <strong>finance review</strong> → collections; <strong>held</strong>{" "}
          blocks collection until released; <strong>paid</strong> closes AR. Export uses the same column contract as{" "}
          <code style={{ fontSize: 11 }}>GET /invoicing/invoices/export-rows</code>.
        </p>
        {financeQ.error ? <div className="hub-err">{financeQ.error}</div> : null}
        {financeRecon.error ? <div className="hub-err">{financeRecon.error}</div> : null}
        {financeExportErr ? <div className="hub-err">{financeExportErr}</div> : null}
        {!financeQ.error && finCounts ? (
          <>
            <div className="hub-metric" style={{ fontSize: 22 }}>
              {(finCounts.unpaid ?? 0) + (finCounts.held ?? 0)}
            </div>
            <div className="hub-sub">Open invoices (unpaid + held)</div>
            <ul className="hub-list-compact" style={{ marginTop: 8 }}>
              <li>Unpaid: {finCounts.unpaid ?? 0}</li>
              <li>Held: {finCounts.held ?? 0}</li>
              <li>Paid: {finCounts.paid ?? 0}</li>
            </ul>
          </>
        ) : null}
        {!financeRecon.error && recon ? (
          <div style={{ marginTop: 12 }}>
            <h4 style={{ fontSize: 13, margin: "0 0 6px" }}>Reconciliation summary</h4>
            <ul className="hub-list-compact">
              <li>Paid (last 30 days): {reconCounts?.paid_last_30_days ?? 0}</li>
              <li>
                Outstanding (unpaid + held, grand total):{" "}
                <strong>{reconOutstanding != null ? String(reconOutstanding) : "—"}</strong>
              </li>
              <li>Open age 0–7d: {reconBuckets?.["0_7_days"] ?? 0}</li>
              <li>Open age 8–30d: {reconBuckets?.["8_30_days"] ?? 0}</li>
              <li>Open age 31+d: {reconBuckets?.["31_plus_days"] ?? 0}</li>
            </ul>
            {reconNote ? <p className="hub-sub" style={{ marginTop: 6, fontSize: 12 }}>{reconNote}</p> : null}
          </div>
        ) : null}
        {!financeQ.error && fin ? (
          <>
            <div className="row" style={{ marginTop: 12, flexWrap: "wrap", gap: 8 }}>
              <button type="button" onClick={() => void downloadInvoiceExportCsv()} disabled={financeExportBusy}>
                {financeExportBusy ? "Preparing CSV…" : "Download invoice export CSV (500 rows)"}
              </button>
            </div>
            {finCredit?.message || finCredit?.status ? (
              <p className="hub-sub" style={{ marginTop: 10 }}>
                <strong>Credit notes / adjustments</strong>
                {finCredit?.status ? (
                  <>
                    {" "}
                    <span className="badge">{String(finCredit.status)}</span>
                  </>
                ) : null}
                {finCredit?.in_app_supported === false ? (
                  <>
                    {" "}
                    <span className="badge">not in PHI-DPS</span>
                  </>
                ) : null}
                : {String(finCredit.message ?? "")}
              </p>
            ) : null}
            <details style={{ marginTop: 10 }}>
              <summary className="hub-sub" style={{ cursor: "pointer" }}>
                Export column reference
              </summary>
              <ul className="hub-list-compact" style={{ marginTop: 6 }}>
                {finExportCols.map((c) => (
                  <li key={String(c.key)}>
                    <code style={{ fontSize: 11 }}>{String(c.key)}</code> — {String(c.description ?? "")}
                  </li>
                ))}
              </ul>
            </details>

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Held invoices (sample)</h4>
            {finHeld.length === 0 ? (
              <div className="hub-sub">None.</div>
            ) : (
              <ul className="hub-list-compact">
                {finHeld.slice(0, 8).map((row, i) => {
                  const iid = String(row.invoice_id ?? "");
                  return (
                    <li key={iid || `h-${i}`} style={{ marginBottom: 8 }}>
                      <div>
                        {String(row.currency ?? "")} {String(row.grand_total ?? "—")} · {String(row.status ?? "")}
                        {row.has_costing_warnings ? " · costing flag" : ""}
                      </div>
                      <div className="hub-sub" style={{ marginTop: 2 }}>
                        job <code style={{ fontSize: 11 }}>{String(row.job_id ?? "").slice(0, 8)}…</code>
                      </div>
                      {iid ? (
                        <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(iid)}>
                          Copy invoice id
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}

            <h4 style={{ fontSize: 13, marginTop: 12 }}>Unpaid — awaiting finance review</h4>
            {finAwaitReview.length === 0 ? (
              <div className="hub-sub">None in queue.</div>
            ) : (
              <ul className="hub-list-compact">
                {finAwaitReview.slice(0, 10).map((row, i) => {
                  const iid = String(row.invoice_id ?? "");
                  return (
                    <li key={iid || `a-${i}`} style={{ marginBottom: 8 }}>
                      <div>
                        {String(row.currency ?? "")} {String(row.grand_total ?? "—")}
                        {row.has_costing_warnings ? " · costing flag" : ""}
                      </div>
                      {iid ? (
                        <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(iid)}>
                          Copy invoice id
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}

            <h4 style={{ fontSize: 13, marginTop: 12 }}>Unpaid — finance reviewed (ready to collect)</h4>
            {finReviewed.length === 0 ? (
              <div className="hub-sub">None in sample.</div>
            ) : (
              <ul className="hub-list-compact">
                {finReviewed.slice(0, 8).map((row, i) => {
                  const iid = String(row.invoice_id ?? "");
                  return (
                    <li key={iid || `r-${i}`} style={{ marginBottom: 8 }}>
                      <div>
                        {String(row.currency ?? "")} {String(row.grand_total ?? "—")} · reviewed{" "}
                        {row.finance_reviewed_at ? String(row.finance_reviewed_at).slice(0, 10) : "—"}
                      </div>
                      {iid ? (
                        <button type="button" className="secondary" style={{ marginTop: 4 }} onClick={() => void copyText(iid)}>
                          Copy invoice id
                        </button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </>
        ) : null}
      </div>

      <div id="hub-access-tab" className="card hub-panel hub-anchor">
        <h3>Org & portal access</h3>
        <p className="hub-sub" style={{ marginTop: 0 }}>
          Manage internal access groups (members + entity scopes), customer portal groups, portal members, and portal entity
          scopes on the dedicated <strong>Access</strong> tab.
        </p>
      </div>

      <div id="hub-repricing" className="card hub-panel hub-anchor">
        <h3>Repricing proposals (pipeline)</h3>
        {repricingProps.error ? <div className="hub-err">{repricingProps.error}</div> : null}
        {!repricingProps.error && repricingProps.data ? (
          <>
            <div className="hub-metric">{Number(repricingProps.data.total_listed ?? 0)}</div>
            <div className="hub-sub">Latest rows (max 35 loaded).</div>
            <ul className="hub-list-compact">
              {((repricingProps.data.rows as Record<string, unknown>[]) ?? []).slice(0, 10).map((r, i) => (
                <li key={i}>
                  {String(r.proposal_reference)} · {String(r.proposal_status)} · contract {String(r.contract_id ?? "").slice(0, 8)}…
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>

      <div id="hub-pending-activations" className="card hub-panel hub-anchor">
        <h3>Pending activations</h3>
        {pendingActivations.error ? <div className="hub-err">{pendingActivations.error}</div> : null}
        {!pendingActivations.error && pendingActivations.data ? (
          <>
            <div className="hub-metric">{Number((pendingActivations.data as { count?: number }).count ?? 0)}</div>
            <ul className="hub-list-compact">
              {(
                (pendingActivations.data as { pending_activations?: Record<string, unknown>[] }).pending_activations ?? []
              )
                .slice(0, 10)
                .map((r, i) => (
                  <li key={i}>
                    {String(r.amendment_reference)} · {String(r.status)} · eff. {String(r.effective_date ?? "").slice(0, 10)}
                  </li>
                ))}
            </ul>
          </>
        ) : null}
      </div>

      <div id="hub-amendments" className="card hub-panel hub-anchor">
        <h3>Amendments (recent)</h3>
        {amendmentsDash.error ? <div className="hub-err">{amendmentsDash.error}</div> : null}
        {!amendmentsDash.error && amendmentsDash.data ? (
          <ul className="hub-list-compact">
            {(
              (amendmentsDash.data as { amendments?: Record<string, unknown>[] }).amendments ?? []
            )
              .slice(0, 12)
              .map((r, i) => (
                <li key={i}>
                  {String(r.amendment_reference)} · {String(r.status)} · {String(r.contract_id ?? "").slice(0, 8)}…
                </li>
              ))}
          </ul>
        ) : null}
      </div>

      <div id="hub-comms-delivery" className="card hub-panel hub-anchor">
        <h3>Customer communications — delivery</h3>
        {commsDelivery.error ? <div className="hub-err">{commsDelivery.error}</div> : null}
        {!commsDelivery.error && commsDelivery.data ? (
          <ul className="hub-list-compact">
            <li>Ready to send: {Number((commsDelivery.data as { communications_ready_to_send?: number }).communications_ready_to_send ?? 0)}</li>
            <li>Failed comms: {Number((commsDelivery.data as { communications_failed?: number }).communications_failed ?? 0)}</li>
            <li>Sent (24h): {Number((commsDelivery.data as { communications_sent_last_24h?: number }).communications_sent_last_24h ?? 0)}</li>
            <li>Pending approval (ready): {Number((commsDelivery.data as { pending_approval_ready_to_send?: number }).pending_approval_ready_to_send ?? 0)}</li>
            <li>Delivery attempts: {Number((commsDelivery.data as { total_delivery_attempts?: number }).total_delivery_attempts ?? 0)}</li>
          </ul>
        ) : null}
      </div>

      <div id="hub-comms-failures" className="card hub-panel hub-anchor">
        <h3>Customer communications — failures & safety</h3>
        {commsFailures.error ? <div className="hub-err">{commsFailures.error}</div> : null}
        {!commsFailures.error && commsFailures.data ? (
          <pre className="item-body" style={{ fontSize: 11, maxHeight: 160, overflow: "auto" }}>
            {JSON.stringify(commsFailures.data, null, 2)}
          </pre>
        ) : null}
      </div>

      <div id="hub-documents" className="card hub-panel hub-anchor">
        <h3>Stored documents (recent)</h3>
        <p className="hub-sub" style={{ marginTop: 0 }}>
          Optional filter by related job; use &quot;Refresh all panels&quot; to reload the list.
        </p>
        <label className="hub-sub">Related job ID</label>
        <input
          style={{ width: "100%", maxWidth: 420, marginTop: 4, marginBottom: 8, display: "block" }}
          value={documentsJobFilter}
          onChange={(e) => setDocumentsJobFilter(e.target.value)}
          placeholder="Leave empty for latest across jobs"
        />
        {docDownloadErr ? <div className="hub-err">{docDownloadErr}</div> : null}
        {documentsList.error ? <div className="hub-err">{documentsList.error}</div> : null}
        {!documentsList.error && documentsList.data ? (
          <ul className="hub-list-compact">
            {(documentsList.data as Record<string, unknown>[]).slice(0, 12).map((d, i) => {
              const did = String(d.id ?? "");
              const fn = String(d.filename ?? "document");
              return (
                <li key={i}>
                  <span>
                    {String(d.document_type)} · {fn.slice(0, 40)}
                    {d.downloadable ? (
                      <>
                        {" "}
                        <button
                          type="button"
                          className="secondary"
                          disabled={docDownloadBusyId === did}
                          onClick={() => void downloadStoredDocument(did, fn)}
                        >
                          {docDownloadBusyId === did ? "…" : "Download"}
                        </button>
                      </>
                    ) : null}
                  </span>
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
