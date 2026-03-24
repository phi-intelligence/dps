import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type Domain = "feature_flags" | "dispatch" | "security" | "notifications";

type DomainCatalogRow = {
  domain: Domain;
  label: string;
  description: string;
};

type DomainOut = {
  domain: Domain;
  defaults: Record<string, unknown>;
  overrides: Record<string, unknown>;
  effective: Record<string, unknown>;
  updated_at: string | null;
  updated_by_user_id: string | null;
};

type RuntimeSettingsEffectiveSnapshotOut = {
  feature_flags: DomainOut;
  dispatch: DomainOut;
  security: DomainOut;
  notifications: DomainOut;
};

type AuditRow = {
  id: string;
  setting_key: string;
  old_value_json: string;
  new_value_json: string;
  reason: string | null;
  changed_by_user_id: string | null;
  changed_at: string;
};

async function fetchJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
  return res.json() as Promise<T>;
}

async function putJson<T>(url: string, headers: Record<string, string>, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "PUT",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
  return res.json() as Promise<T>;
}

function parseNumber(v: unknown, fallback: number): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function isEmailLike(v: string): boolean {
  return /\S+@\S+\.\S+/.test(v.trim());
}

function toComparable(v: unknown): string {
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

export function SettingsHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);
  const [cacheBusy, setCacheBusy] = useState(false);

  const [catalog, setCatalog] = useState<DomainCatalogRow[]>([]);
  const [catalogErr, setCatalogErr] = useState<string | null>(null);

  const [activeDomain, setActiveDomain] = useState<Domain>("feature_flags");
  const [domainOut, setDomainOut] = useState<DomainOut | null>(null);
  const [domainErr, setDomainErr] = useState<string | null>(null);

  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [auditErr, setAuditErr] = useState<string | null>(null);

  const [effectiveSnapshot, setEffectiveSnapshot] = useState<RuntimeSettingsEffectiveSnapshotOut | null>(null);
  const [effectiveSnapshotErr, setEffectiveSnapshotErr] = useState<string | null>(null);

  const [reason, setReason] = useState("");

  const [featureFlagsForm, setFeatureFlagsForm] = useState({
    ai_assisted_drafting_enabled: false,
    dispatch_recommend_stale: false,
    strict_parts_reconciliation: false,
  });

  const [dispatchForm, setDispatchForm] = useState({
    telemetry_fresh_seconds: 60,
    telemetry_aging_seconds: 300,
    avg_vehicle_speed_mps: 13.89,
  });

  const [securityForm, setSecurityForm] = useState({
    access_token_expire_minutes: 60,
  });

  const [notificationsForm, setNotificationsForm] = useState({
    communication_enabled: false,
    communication_email_provider: "none",
    communication_sms_provider: "none",
    communication_template_locale: "en",
    communication_template_catalog_version: "1",
    portal_support_email: "",
    portal_support_phone: "",
  });

  const fieldErrors = useMemo<Record<string, string>>(() => {
    const errs: Record<string, string> = {};
    if (activeDomain === "dispatch") {
      if (dispatchForm.telemetry_fresh_seconds < 10 || dispatchForm.telemetry_fresh_seconds > 3600) {
        errs.telemetry_fresh_seconds = "Must be between 10 and 3600 seconds.";
      }
      if (dispatchForm.telemetry_aging_seconds < 30 || dispatchForm.telemetry_aging_seconds > 86400) {
        errs.telemetry_aging_seconds = "Must be between 30 and 86400 seconds.";
      }
      if (dispatchForm.telemetry_aging_seconds <= dispatchForm.telemetry_fresh_seconds) {
        errs.telemetry_aging_seconds = "Aging threshold must be greater than fresh threshold.";
      }
      if (dispatchForm.avg_vehicle_speed_mps < 1 || dispatchForm.avg_vehicle_speed_mps > 60) {
        errs.avg_vehicle_speed_mps = "Must be between 1 and 60 m/s.";
      }
    }
    if (activeDomain === "security") {
      if (securityForm.access_token_expire_minutes < 1 || securityForm.access_token_expire_minutes > 10080) {
        errs.access_token_expire_minutes = "Must be between 1 and 10080 minutes.";
      }
    }
    if (activeDomain === "notifications") {
      const locale = notificationsForm.communication_template_locale.trim();
      if (!locale) errs.communication_template_locale = "Template locale is required.";
      const version = notificationsForm.communication_template_catalog_version.trim();
      if (!version) errs.communication_template_catalog_version = "Template catalog version is required.";
      const email = notificationsForm.portal_support_email.trim();
      if (!email) errs.portal_support_email = "Portal support email is required.";
      else if (!isEmailLike(email)) errs.portal_support_email = "Enter a valid email address.";
      const provider = notificationsForm.communication_email_provider.trim().toLowerCase();
      if (!["none", "smtp", "sendgrid"].includes(provider)) {
        errs.communication_email_provider = "Allowed values: none, smtp, sendgrid.";
      }
      const smsProvider = notificationsForm.communication_sms_provider.trim().toLowerCase();
      if (!["none", "twilio"].includes(smsProvider)) {
        errs.communication_sms_provider = "Allowed values: none, twilio.";
      }
    }
    return errs;
  }, [activeDomain, dispatchForm, notificationsForm, securityForm]);

  const hasFieldErrors = Object.keys(fieldErrors).length > 0;

  useEffect(() => {
    if (!banner && !bannerErr) return;
    const t = window.setTimeout(() => {
      setBanner(null);
      setBannerErr(null);
    }, 4000);
    return () => window.clearTimeout(t);
  }, [banner, bannerErr]);

  const loadCatalog = useCallback(async () => {
    setCatalogErr(null);
    try {
      const rows = await fetchJson<DomainCatalogRow[]>(`${apiBase}/admin/settings/domains`, authHeaders);
      setCatalog(rows);
    } catch (e) {
      setCatalogErr(e instanceof Error ? e.message : String(e));
      setCatalog([]);
    }
  }, [apiBase, authHeaders]);

  const loadDomain = useCallback(async () => {
    setDomainErr(null);
    try {
      const out = await fetchJson<DomainOut>(`${apiBase}/admin/settings/${encodeURIComponent(activeDomain)}`, authHeaders);
      setDomainOut(out);
      if (out.domain === "feature_flags") {
        setFeatureFlagsForm({
          ai_assisted_drafting_enabled: Boolean(out.effective.ai_assisted_drafting_enabled),
          dispatch_recommend_stale: Boolean(out.effective.dispatch_recommend_stale),
          strict_parts_reconciliation: Boolean(out.effective.strict_parts_reconciliation),
        });
      } else if (out.domain === "dispatch") {
        setDispatchForm({
          telemetry_fresh_seconds: parseNumber(out.effective.telemetry_fresh_seconds, 60),
          telemetry_aging_seconds: parseNumber(out.effective.telemetry_aging_seconds, 300),
          avg_vehicle_speed_mps: parseNumber(out.effective.avg_vehicle_speed_mps, 13.89),
        });
      } else if (out.domain === "security") {
        setSecurityForm({
          access_token_expire_minutes: parseNumber(out.effective.access_token_expire_minutes, 60),
        });
      } else if (out.domain === "notifications") {
        setNotificationsForm({
          communication_enabled: Boolean(out.effective.communication_enabled),
          communication_email_provider: String(out.effective.communication_email_provider ?? "none"),
          communication_sms_provider: String(out.effective.communication_sms_provider ?? "none"),
          communication_template_locale: String(out.effective.communication_template_locale ?? "en"),
          communication_template_catalog_version: String(out.effective.communication_template_catalog_version ?? "1"),
          portal_support_email: String(out.effective.portal_support_email ?? ""),
          portal_support_phone: String(out.effective.portal_support_phone ?? ""),
        });
      }
    } catch (e) {
      setDomainErr(e instanceof Error ? e.message : String(e));
      setDomainOut(null);
    }
  }, [activeDomain, apiBase, authHeaders]);

  const loadHistory = useCallback(async () => {
    setAuditErr(null);
    try {
      const rows = await fetchJson<AuditRow[]>(
        `${apiBase}/admin/settings/${encodeURIComponent(activeDomain)}/history?limit=30`,
        authHeaders,
      );
      setAudit(rows);
    } catch (e) {
      setAuditErr(e instanceof Error ? e.message : String(e));
      setAudit([]);
    }
  }, [activeDomain, apiBase, authHeaders]);

  const loadEffectiveSnapshot = useCallback(async () => {
    setEffectiveSnapshotErr(null);
    try {
      const rows = await fetchJson<RuntimeSettingsEffectiveSnapshotOut>(`${apiBase}/admin/settings/effective`, authHeaders);
      setEffectiveSnapshot(rows);
    } catch (e) {
      setEffectiveSnapshot(null);
      setEffectiveSnapshotErr(e instanceof Error ? e.message : String(e));
    }
  }, [apiBase, authHeaders]);

  const refreshRuntimeCacheNow = useCallback(async () => {
    setCacheBusy(true);
    setEffectiveSnapshotErr(null);
    try {
      const res = await fetch(`${apiBase}/admin/settings/effective-cache/refresh`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t.slice(0, 220) || res.statusText);
      }
      await loadEffectiveSnapshot();
    } catch (e) {
      setEffectiveSnapshotErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCacheBusy(false);
    }
  }, [apiBase, authHeaders, loadEffectiveSnapshot]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  useEffect(() => {
    void loadDomain();
    void loadHistory();
    void loadEffectiveSnapshot();
  }, [loadDomain, loadHistory]);

  const save = useCallback(async () => {
    if (hasFieldErrors) {
      setBannerErr("Please fix validation errors before saving.");
      return;
    }
    setBusy(true);
    setBanner(null);
    setBannerErr(null);
    try {
      const values =
        activeDomain === "feature_flags"
          ? {
              ai_assisted_drafting_enabled: featureFlagsForm.ai_assisted_drafting_enabled,
              dispatch_recommend_stale: featureFlagsForm.dispatch_recommend_stale,
              strict_parts_reconciliation: featureFlagsForm.strict_parts_reconciliation,
            }
          : activeDomain === "dispatch"
            ? {
                telemetry_fresh_seconds: dispatchForm.telemetry_fresh_seconds,
                telemetry_aging_seconds: dispatchForm.telemetry_aging_seconds,
                avg_vehicle_speed_mps: dispatchForm.avg_vehicle_speed_mps,
              }
            : activeDomain === "security"
              ? {
                  access_token_expire_minutes: securityForm.access_token_expire_minutes,
                }
              : {
                  communication_enabled: notificationsForm.communication_enabled,
                  communication_email_provider: notificationsForm.communication_email_provider,
                  communication_sms_provider: notificationsForm.communication_sms_provider,
                  communication_template_locale: notificationsForm.communication_template_locale,
                  communication_template_catalog_version: notificationsForm.communication_template_catalog_version,
                  portal_support_email: notificationsForm.portal_support_email,
                  portal_support_phone: notificationsForm.portal_support_phone,
                };
      await putJson<DomainOut>(`${apiBase}/admin/settings/${encodeURIComponent(activeDomain)}`, authHeaders, {
        values,
        reason: reason.trim() || null,
      });
      setBanner("Settings saved.");
      await loadDomain();
      await loadHistory();
      await loadEffectiveSnapshot();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [
    activeDomain,
    apiBase,
    authHeaders,
    dispatchForm,
    featureFlagsForm,
    loadDomain,
    loadHistory,
    notificationsForm,
    reason,
    securityForm,
    hasFieldErrors,
  ]);

  const effectiveJson = useMemo(() => {
    if (!domainOut) return "";
    return JSON.stringify(domainOut.effective, null, 2);
  }, [domainOut]);

  const diffRows = useMemo(() => {
    if (!domainOut) return [] as Array<{ key: string; defaults: unknown; overrides: unknown; effective: unknown; changed: boolean }>;
    const keys = new Set<string>([
      ...Object.keys(domainOut.defaults || {}),
      ...Object.keys(domainOut.overrides || {}),
      ...Object.keys(domainOut.effective || {}),
    ]);
    return Array.from(keys)
      .sort()
      .map((k) => {
        const defaults = domainOut.defaults?.[k];
        const overrides = domainOut.overrides?.[k];
        const effective = domainOut.effective?.[k];
        return {
          key: k,
          defaults,
          overrides,
          effective,
          changed: toComparable(defaults) !== toComparable(effective),
        };
      });
  }, [domainOut]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Enterprise Settings</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Typed settings domains with audit history. Phase 4 domains: feature flags, dispatch, security, and notifications.
        </p>
        <div className="row" style={{ marginTop: 10, gap: 8, flexWrap: "wrap" }}>
          <select value={activeDomain} onChange={(e) => setActiveDomain(e.target.value as Domain)} disabled={busy}>
            {catalog.map((d) => (
              <option key={d.domain} value={d.domain}>
                {d.label}
              </option>
            ))}
          </select>
          <button type="button" className="secondary" onClick={() => void loadDomain()} disabled={busy}>
            Refresh domain
          </button>
          <button type="button" className="secondary" onClick={() => void loadHistory()} disabled={busy}>
            Refresh history
          </button>
        </div>
        {catalogErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{catalogErr}</div> : null}
        {banner ? <div style={{ marginTop: 10, color: "#86efac" }}>{banner}</div> : null}
        {bannerErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{bannerErr}</div> : null}
      </div>

      <div className="card hub-panel">
        <h3>Domain configuration</h3>
        {domainErr ? <div className="hub-err">{domainErr}</div> : null}
        {hasFieldErrors ? (
          <div className="hub-err" style={{ marginTop: 8 }}>
            This form has {Object.keys(fieldErrors).length} validation issue(s). Resolve them before saving.
          </div>
        ) : null}
        {activeDomain === "feature_flags" ? (
          <div style={{ marginTop: 10 }}>
            <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={featureFlagsForm.ai_assisted_drafting_enabled}
                onChange={(e) => setFeatureFlagsForm((f) => ({ ...f, ai_assisted_drafting_enabled: e.target.checked }))}
              />
              AI assisted drafting enabled
            </label>
            <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
              <input
                type="checkbox"
                checked={featureFlagsForm.dispatch_recommend_stale}
                onChange={(e) => setFeatureFlagsForm((f) => ({ ...f, dispatch_recommend_stale: e.target.checked }))}
              />
              Dispatch recommendations include stale telemetry
            </label>
            <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
              <input
                type="checkbox"
                checked={featureFlagsForm.strict_parts_reconciliation}
                onChange={(e) => setFeatureFlagsForm((f) => ({ ...f, strict_parts_reconciliation: e.target.checked }))}
              />
              Strict parts reconciliation
            </label>
          </div>
        ) : activeDomain === "dispatch" ? (
          <div style={{ marginTop: 10 }}>
            <div className="field">
              <label>Telemetry fresh seconds</label>
              <input
                type="number"
                value={dispatchForm.telemetry_fresh_seconds}
                onChange={(e) => setDispatchForm((f) => ({ ...f, telemetry_fresh_seconds: Number(e.target.value) }))}
              />
              {fieldErrors.telemetry_fresh_seconds ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.telemetry_fresh_seconds}</div>
              ) : null}
            </div>
            <div className="field">
              <label>Telemetry aging seconds</label>
              <input
                type="number"
                value={dispatchForm.telemetry_aging_seconds}
                onChange={(e) => setDispatchForm((f) => ({ ...f, telemetry_aging_seconds: Number(e.target.value) }))}
              />
              {fieldErrors.telemetry_aging_seconds ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.telemetry_aging_seconds}</div>
              ) : null}
            </div>
            <div className="field">
              <label>Average vehicle speed (m/s)</label>
              <input
                type="number"
                step="0.01"
                value={dispatchForm.avg_vehicle_speed_mps}
                onChange={(e) => setDispatchForm((f) => ({ ...f, avg_vehicle_speed_mps: Number(e.target.value) }))}
              />
              {fieldErrors.avg_vehicle_speed_mps ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.avg_vehicle_speed_mps}</div>
              ) : null}
            </div>
          </div>
        ) : activeDomain === "security" ? (
          <div style={{ marginTop: 10 }}>
            <div className="field">
              <label>Access token expiry (minutes)</label>
              <input
                type="number"
                value={securityForm.access_token_expire_minutes}
                onChange={(e) => setSecurityForm((f) => ({ ...f, access_token_expire_minutes: Number(e.target.value) }))}
              />
              {fieldErrors.access_token_expire_minutes ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.access_token_expire_minutes}</div>
              ) : null}
            </div>
            <div className="hint" style={{ marginTop: 8 }}>
              Affects new tokens immediately after refresh (existing tokens keep their original `exp`).
            </div>
          </div>
        ) : (
          <div style={{ marginTop: 10 }}>
            <label className="hub-sub" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={notificationsForm.communication_enabled}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, communication_enabled: e.target.checked }))}
              />
              Outbound communications enabled
            </label>

            <div className="hint" style={{ marginTop: 8 }}>
              Runtime services use a cached effective view. Click "Refresh runtime cache now" to apply changes immediately.
            </div>

            <div className="field" style={{ marginTop: 10 }}>
              <label>Email provider</label>
              <select
                value={notificationsForm.communication_email_provider}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, communication_email_provider: e.target.value }))}
                disabled={!notificationsForm.communication_enabled}
              >
                <option value="none">(none)</option>
                <option value="smtp">smtp</option>
                <option value="sendgrid">sendgrid</option>
              </select>
              {fieldErrors.communication_email_provider ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.communication_email_provider}</div>
              ) : null}
            </div>

            <div className="field">
              <label>SMS provider</label>
              <select
                value={notificationsForm.communication_sms_provider}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, communication_sms_provider: e.target.value }))}
                disabled={!notificationsForm.communication_enabled}
              >
                <option value="none">(none)</option>
                <option value="twilio">twilio</option>
              </select>
              {fieldErrors.communication_sms_provider ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.communication_sms_provider}</div>
              ) : null}
            </div>

            <div className="field">
              <label>Template locale</label>
              <input
                value={notificationsForm.communication_template_locale}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, communication_template_locale: e.target.value }))}
              />
              {fieldErrors.communication_template_locale ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.communication_template_locale}</div>
              ) : null}
            </div>

            <div className="field">
              <label>Template catalog version</label>
              <input
                value={notificationsForm.communication_template_catalog_version}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, communication_template_catalog_version: e.target.value }))}
              />
              {fieldErrors.communication_template_catalog_version ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.communication_template_catalog_version}</div>
              ) : null}
            </div>

            <div className="field">
              <label>Portal support email</label>
              <input
                value={notificationsForm.portal_support_email}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, portal_support_email: e.target.value }))}
              />
              {fieldErrors.portal_support_email ? (
                <div className="hub-err" style={{ marginTop: 6 }}>{fieldErrors.portal_support_email}</div>
              ) : null}
            </div>

            <div className="field">
              <label>Portal support phone</label>
              <input
                value={notificationsForm.portal_support_phone}
                onChange={(e) => setNotificationsForm((f) => ({ ...f, portal_support_phone: e.target.value }))}
              />
            </div>
          </div>
        )}

        <div className="field" style={{ marginTop: 10 }}>
          <label>Change reason (optional but recommended)</label>
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button type="button" onClick={() => void save()} disabled={busy || hasFieldErrors}>
            {busy ? "Saving…" : "Save settings"}
          </button>
          <button type="button" className="secondary" disabled={busy} onClick={() => void loadDomain()}>
            Reload editor from server
          </button>
        </div>
      </div>

      <div className="card hub-panel">
        <h3>Defaults vs overrides vs effective</h3>
        <div className="hint" style={{ marginTop: 0 }}>
          Changed fields are highlighted where effective differs from defaults.
        </div>
        <div style={{ marginTop: 10, maxHeight: 320, overflow: "auto", border: "1px solid #2a2a2a", borderRadius: 8 }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #2a2a2a" }}>Field</th>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #2a2a2a" }}>Default</th>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #2a2a2a" }}>Override</th>
                <th style={{ textAlign: "left", padding: 8, borderBottom: "1px solid #2a2a2a" }}>Effective</th>
              </tr>
            </thead>
            <tbody>
              {diffRows.map((r) => (
                <tr key={r.key} style={{ background: r.changed ? "rgba(251, 191, 36, 0.08)" : "transparent" }}>
                  <td style={{ padding: 8, borderBottom: "1px solid #1f1f1f" }}>{r.key}</td>
                  <td style={{ padding: 8, borderBottom: "1px solid #1f1f1f" }}>{String(r.defaults ?? "—")}</td>
                  <td style={{ padding: 8, borderBottom: "1px solid #1f1f1f" }}>{String(r.overrides ?? "—")}</td>
                  <td style={{ padding: 8, borderBottom: "1px solid #1f1f1f" }}>
                    {String(r.effective ?? "—")} {r.changed ? <span className="hint">(changed)</span> : null}
                  </td>
                </tr>
              ))}
              {!diffRows.length ? (
                <tr>
                  <td colSpan={4} style={{ padding: 8 }}>No domain values loaded.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        <textarea value={effectiveJson} readOnly rows={6} style={{ width: "100%", marginTop: 10 }} />
        {domainOut?.updated_at ? (
          <div className="hint" style={{ marginTop: 8 }}>
            Last updated: {String(domainOut.updated_at).slice(0, 19)} by {domainOut.updated_by_user_id ?? "—"}
          </div>
        ) : null}
      </div>

      <div className="card hub-panel">
        <h3>Effective runtime snapshot (all domains)</h3>
        {effectiveSnapshotErr ? <div className="hub-err" style={{ marginTop: 8 }}>{effectiveSnapshotErr}</div> : null}
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button type="button" className="secondary" onClick={() => void refreshRuntimeCacheNow()} disabled={cacheBusy}>
            {cacheBusy ? "Refreshing…" : "Refresh runtime cache now"}
          </button>
        </div>
        {effectiveSnapshot ? (
          <div style={{ marginTop: 10 }}>
            <div className="hint" style={{ marginTop: 0 }}>
              Updated by: feature_flags <code>{effectiveSnapshot.feature_flags.updated_by_user_id ?? "—"}</code> · dispatch{" "}
              <code>{effectiveSnapshot.dispatch.updated_by_user_id ?? "—"}</code> · security{" "}
              <code>{effectiveSnapshot.security.updated_by_user_id ?? "—"}</code> · notifications{" "}
              <code>{effectiveSnapshot.notifications.updated_by_user_id ?? "—"}</code>
            </div>
            <div className="row" style={{ gap: 12, flexWrap: "wrap", marginTop: 10 }}>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>feature_flags effective</label>
                <textarea
                  value={JSON.stringify(effectiveSnapshot.feature_flags.effective, null, 2)}
                  readOnly
                  rows={8}
                  style={{ width: "100%" }}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>dispatch effective</label>
                <textarea
                  value={JSON.stringify(effectiveSnapshot.dispatch.effective, null, 2)}
                  readOnly
                  rows={8}
                  style={{ width: "100%" }}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>security effective</label>
                <textarea
                  value={JSON.stringify(effectiveSnapshot.security.effective, null, 2)}
                  readOnly
                  rows={8}
                  style={{ width: "100%" }}
                />
              </div>
              <div className="field" style={{ flex: 1, minWidth: 260 }}>
                <label>notifications effective</label>
                <textarea
                  value={JSON.stringify(effectiveSnapshot.notifications.effective, null, 2)}
                  readOnly
                  rows={8}
                  style={{ width: "100%" }}
                />
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="card hub-panel">
        <h3>Change history</h3>
        {auditErr ? <div className="hub-err">{auditErr}</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 10, maxHeight: 280, overflow: "auto" }}>
          {audit.map((a) => (
            <li key={a.id} style={{ marginBottom: 10 }}>
              <div>
                <strong>{String(a.changed_at).slice(0, 19)}</strong> · by {a.changed_by_user_id ?? "—"}
              </div>
              {a.reason ? <div className="hub-sub">{a.reason}</div> : null}
            </li>
          ))}
          {!audit.length ? <li className="muted">No change history yet.</li> : null}
        </ul>
      </div>
    </div>
  );
}

