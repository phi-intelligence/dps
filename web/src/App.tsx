import React, { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";
import "./phase4/phase4.css";
import { getPhiDpsApiBase } from "./config";
import { CommercialHub } from "./phase4/CommercialHub";
import { ClientPortalHub } from "./phase4/ClientPortalHub";
import { FieldJobConsole } from "./phase4/FieldJobConsole";
import { OrgAccessHub } from "./phase4/OrgAccessHub";
import { LabourAiToolsHub } from "./phase4/LabourAiToolsHub";
import { LiveDispatchMap } from "./phase4/LiveDispatchMap";
import { SitesHub } from "./phase4/SitesHub";
import { AssetsHub } from "./phase4/AssetsHub";
import { InventoryHub } from "./phase4/InventoryHub";
import { SlaPoliciesHub } from "./phase4/SlaPoliciesHub";
import { PpmSchedulesHub } from "./phase4/PpmSchedulesHub";
import { ApprovalsHub } from "./phase4/ApprovalsHub";
import { VehiclesHub } from "./phase4/VehiclesHub";
import { CompetenceHub } from "./phase4/CompetenceHub";
import { AnalyticsHub } from "./phase4/AnalyticsHub";
import { OpsHub } from "./phase4/OpsHub";
import { SettingsHub } from "./phase4/SettingsHub";

type TokenResponse = { access_token: string; token_type: string };
type Lead = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  property_type: string | null;
  preferred_time_slots: string | null;
  issue_description: string | null;
  status: string;
  converted_customer_id?: string | null;
};
type Customer = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
};
type QuoteItemIn = { item_type: string; description: string; quantity: number; unit_price: number };
type Quote = {
  id: string;
  customer_id: string | null;
  status: string;
  currency: string;
  notes: string | null;
  labour_total: number;
  materials_total: number;
  grand_total: number;
};
type QuoteItemOut = { id: string; item_type: string; description: string; quantity: number; unit_price: number; line_total: number };
type QuoteDetail = Quote & { items?: QuoteItemOut[] };
type Job = {
  id: string;
  customer_id: string | null;
  quote_id: string | null;
  address: string;
  status: string;
  assigned_engineer_id?: string | null;
  eta_minutes?: number;
  delay_notice?: string | null;
  delay_notice_at?: string | null;
  sla_risk_state?: string | null;
  sla_target_completion_at?: string | null;
};

type Punch = {
  id: string;
  user_id: string;
  job_id: string;
  kind: string;
  occurred_at: string;
  latitude: number;
  longitude: number;
  valid: boolean;
  distance_m: number | null;
  offline_device_id: string | null;
  created_at: string;
};

type TimesheetSession = {
  job_id: string;
  clock_in_punch_id: string;
  clock_out_punch_id: string;
  clock_in_at: string;
  clock_out_at: string;
  duration_seconds: number;
};

type Timesheet = {
  user_id: string;
  date: string;
  total_seconds: number;
  sessions: TimesheetSession[];
};

type JobGeofence = {
  id: string;
  job_id: string;
  latitude: number;
  longitude: number;
  radius_m: number;
  created_at: string;
};

type Certificate = {
  id: string;
  job_id: string;
  certificate_type: string;
  status: string;
  engineer_user_id: string | null;
  signed_by_engineer: boolean;
  signed_by_client: boolean;
  created_at: string;
};

type Invoice = {
  id: string;
  job_id: string;
  currency: string;
  status: string;
  labour_total: number;
  materials_total: number;
  grand_total: number;
  paid_at: string | null;
  created_at: string;
  finance_reviewed_at?: string | null;
};

type RolloutWave = {
  id: string;
  name: string;
  target_role: string | null;
  rollout_percent: number;
  status: string;
  pause_reason: string | null;
  created_at: string;
};

type RolloutAlert = {
  id: string;
  severity: string;
  code: string;
  message: string;
  status: string;
  dedup_count: number;
  created_at: string;
};

type NotificationDelivery = {
  id: string;
  alert_id: string;
  channel: string;
  status: string;
  attempts: number;
  last_error: string | null;
  next_retry_at: string | null;
  dead_lettered_at: string | null;
  created_at: string;
};

type RolloutDigest = {
  total_alerts: number;
  open_alerts: number;
  acknowledged_alerts: number;
  critical_open_alerts: number;
  warnings_open_alerts: number;
  alerts_last_24h: number;
  open_by_code: Record<string, number>;
};

const TOKEN_KEY = "phi_dps_token";

function asAuthHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function SuccessBanner({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000);
    return () => clearTimeout(t);
  }, [onDismiss]);
  return (
    <div
      role="alert"
      className="success-banner"
      style={{
        background: "rgba(34, 197, 94, 0.15)",
        border: "1px solid rgba(34, 197, 94, 0.4)",
        color: "#86efac",
        padding: "10px 16px",
        borderRadius: 8,
        margin: "0 18px 12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <span>{message}</span>
      <button type="button" className="secondary" style={{ padding: "4px 10px", fontSize: 12 }} onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  );
}

function ConvertLeadForm({
  lead,
  onConvert,
  onCancel,
}: {
  lead: Lead;
  onConvert: (c: { name: string; email: string; phone: string; address: string }) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(lead.name);
  const [email, setEmail] = useState(lead.email || "");
  const [phone, setPhone] = useState(lead.phone || "");
  const [address, setAddress] = useState("");
  return (
    <div className="card" style={{ marginTop: 12 }}>
      <h4 style={{ marginTop: 0 }}>Convert to customer</h4>
      <div className="field">
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="field">
        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div className="field">
        <label>Phone</label>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} />
      </div>
      <div className="field">
        <label>Address (optional)</label>
        <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Service address" />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="button" onClick={() => onConvert({ name, email, phone, address })}>
          Convert
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function haversineM(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371000;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const dPhi = ((lat2 - lat1) * Math.PI) / 180;
  const dLambda = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dPhi / 2) * Math.sin(dPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) * Math.sin(dLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function isValidEmail(value: string): boolean {
  const v = value.trim();
  if (!v) return true;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem(TOKEN_KEY) || "");
  const [activeTab, setActiveTab] = useState<
    | "dashboard"
    | "leads"
    | "customers"
    | "quotes"
    | "jobs"
    | "time"
    | "compliance"
    | "invoices"
    | "approvals"
    | "vehicles"
    | "competence"
    | "analytics"
    | "ops"
    | "settings"
    | "commercial"
    | "access"
    | "portal"
    | "rollout"
    | "labour_ai"
    | "map"
    | "sites"
    | "assets"
    | "inventory"
    | "sla"
    | "ppm"
  >("dashboard");
  const [quoteFormPrefillCustomerId, setQuoteFormPrefillCustomerId] = useState<string>("");

  useEffect(() => {
    if (activeTab === "quotes" && quoteFormPrefillCustomerId) {
      setQuoteForm((prev) => ({ ...prev, customer_id: quoteFormPrefillCustomerId }));
      setQuoteFormPrefillCustomerId("");
    }
  }, [activeTab, quoteFormPrefillCustomerId]);
  const isAuthed = token.trim().length > 0;

  const [loginUsername, setLoginUsername] = useState("admin@example.com");
  const [loginPassword, setLoginPassword] = useState("admin");
  const [authError, setAuthError] = useState<string>("");

  const [appError, setAppError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadsBusy, setLeadsBusy] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customersBusy, setCustomersBusy] = useState(false);
  const [convertLeadId, setConvertLeadId] = useState<string | null>(null);
  const [expandedQuoteId, setExpandedQuoteId] = useState<string | null>(null);
  const [quoteDetail, setQuoteDetail] = useState<QuoteDetail | null>(null);
  const [assignBestBusy, setAssignBestBusy] = useState<string | null>(null);
  const [manualAssignBusy, setManualAssignBusy] = useState<string | null>(null);
  const [statusUpdateBusy, setStatusUpdateBusy] = useState<string | null>(null);
  const [commPrefCustomerId, setCommPrefCustomerId] = useState("");
  const [commPrefs, setCommPrefs] = useState<{ id: string; channel: string; enabled: boolean; contact_reference: string | null; preferred: boolean }[]>([]);
  const [commPrefsBusy, setCommPrefsBusy] = useState(false);
  const [commPrefForm, setCommPrefForm] = useState({ channel: "email", enabled: true, contact_reference: "", preferred: false });
  const [certDownloadBusy, setCertDownloadBusy] = useState<string | null>(null);
  const [leadForm, setLeadForm] = useState({
    name: "",
    email: "",
    phone: "",
    property_type: "House",
    preferred_time_slots: "",
    issue_description: "",
  });

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [quotesBusy, setQuotesBusy] = useState(false);
  const [quoteForm, setQuoteForm] = useState({
    customer_id: "",
    currency: "GBP",
    notes: "",
    labour_desc: "",
    labour_qty: 1,
    labour_unit_price: 0,
    materials_desc: "",
    materials_qty: 0,
    materials_unit_price: 0,
  });

  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsBusy, setJobsBusy] = useState(false);
  const [jobForm, setJobForm] = useState({
    quote_id: "",
    address: "",
    scheduled_at: "",
  });

  const [geofenceForm, setGeofenceForm] = useState({
    job_id: "",
    latitude: 51.5074,
    longitude: -0.1278,
    radius_m: 200,
  });

  const [timeForm, setTimeForm] = useState({
    job_id: "",
    latitude: 51.5074,
    longitude: -0.1278,
  });

  const [punches, setPunches] = useState<Punch[]>([]);
  const [timesheet, setTimesheet] = useState<Timesheet | null>(null);
  const [timesheetDate, setTimesheetDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [timeBusy, setTimeBusy] = useState(false);
  const [punchGeoBusy, setPunchGeoBusy] = useState(false);
  const [timeOfflineDeviceId, setTimeOfflineDeviceId] = useState("");
  const [engineerAvailability, setEngineerAvailability] = useState<{ engineer_id: string; availability_state: string; active_job_count: number }[]>([]);
  const [approvalForm, setApprovalForm] = useState({ user_id: "", date_str: new Date().toISOString().slice(0, 10) });
  const [approvalBusy, setApprovalBusy] = useState(false);
  const [payrollExportBusy, setPayrollExportBusy] = useState(false);
  const [payrollExport, setPayrollExport] = useState<{ date_str: string; lines: { user_id: string; total_seconds: number; amount: number }[] } | null>(null);

  const [loadedGeofence, setLoadedGeofence] = useState<JobGeofence | null>(null);
  const [geofenceBusy, setGeofenceBusy] = useState(false);

  const [certificateJobId, setCertificateJobId] = useState("");
  const [certificateType, setCertificateType] = useState("CP12");
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [certBusy, setCertBusy] = useState(false);

  const [invoiceJobId, setInvoiceJobId] = useState("");
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invoiceBusy, setInvoiceBusy] = useState(false);

  const [rolloutBusy, setRolloutBusy] = useState(false);
  const [rolloutWaves, setRolloutWaves] = useState<RolloutWave[]>([]);
  const [rolloutAlerts, setRolloutAlerts] = useState<RolloutAlert[]>([]);
  const [rolloutDeliveries, setRolloutDeliveries] = useState<NotificationDelivery[]>([]);
  const [rolloutDigest, setRolloutDigest] = useState<RolloutDigest | null>(null);
  const [rolloutWaveForm, setRolloutWaveForm] = useState({
    name: "",
    target_role: "Engineer",
    rollout_percent: 10,
  });
  const [browserOnline, setBrowserOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );
  const [currentUser, setCurrentUser] = useState<{ email: string; roles?: { name: string }[] } | null>(null);

  const authHeaders = useMemo(() => asAuthHeaders(token), [token]);
  const apiBase = useMemo(() => getPhiDpsApiBase(), []);

  const refreshEngineerAvailability = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/dispatch/engineers/availability`, { headers: authHeaders });
      if (res.status === 401 || res.status === 403) return;
      if (!res.ok) return;
      const data = (await res.json()) as { engineer_id: string; availability_state: string; active_job_count: number }[];
      setEngineerAvailability(data);
    } catch {
      setEngineerAvailability([]);
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    const up = () => setBrowserOnline(true);
    const down = () => setBrowserOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);

  useEffect(() => {
    if (activeTab === "time" || activeTab === "jobs") void refreshEngineerAvailability();
  }, [activeTab, isAuthed, refreshEngineerAvailability]);

  useEffect(() => {
    if (!isAuthed) {
      setCurrentUser(null);
      return;
    }
    void (async () => {
      try {
        const res = await fetch(`${apiBase}/auth/me`, { headers: authHeaders });
        if (res.ok) {
          const u = (await res.json()) as { email: string; roles?: { name: string }[] };
          setCurrentUser(u);
        }
      } catch {
        setCurrentUser(null);
      }
    })();
    void Promise.all([
      refreshLeads(),
      refreshQuotes(),
      refreshJobs(),
      refreshCustomers(),
      refreshTimesheet(),
    ]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthed]);

  function clearAuthOn401() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setAuthError("Session expired. Please log in again.");
  }

  async function refreshCustomers() {
    if (customersBusy) return;
    setCustomersBusy(true);
    try {
      const res = await fetch(`${apiBase}/crm/customers?limit=100&offset=0`, { headers: authHeaders });
      if (res.status === 401) {
        clearAuthOn401();
        return;
      }
      if (!res.ok) throw new Error(`Failed to load customers (${res.status})`);
      const data = (await res.json()) as Customer[];
      setCustomers(data);
    } finally {
      setCustomersBusy(false);
    }
  }

  async function refreshLeads() {
    if (leadsBusy) return;
    setLeadsBusy(true);
    try {
      const res = await fetch(`${apiBase}/crm/leads?limit=50&offset=0`, { headers: authHeaders });
      if (res.status === 401) {
        clearAuthOn401();
        return;
      }
      if (!res.ok) throw new Error(`Failed to load leads (${res.status})`);
      const data = (await res.json()) as Lead[];
      setLeads(data);
    } finally {
      setLeadsBusy(false);
    }
  }

  async function loadQuoteDetail(quoteId: string) {
    try {
      const res = await fetch(`${apiBase}/quotes/${encodeURIComponent(quoteId)}`, { headers: authHeaders });
      if (!res.ok) return;
      const data = (await res.json()) as QuoteDetail;
      setQuoteDetail(data);
      setExpandedQuoteId(quoteId);
    } catch {
      setQuoteDetail(null);
      setExpandedQuoteId(null);
    }
  }

  async function refreshQuotes() {
    if (quotesBusy) return;
    setQuotesBusy(true);
    try {
      const res = await fetch(`${apiBase}/quotes?limit=50&offset=0`, { headers: authHeaders });
      if (res.status === 401) {
        clearAuthOn401();
        return;
      }
      if (!res.ok) throw new Error(`Failed to load quotes (${res.status})`);
      const data = (await res.json()) as Quote[];
      setQuotes(data);
    } finally {
      setQuotesBusy(false);
    }
  }

  async function refreshJobs() {
    if (jobsBusy) return;
    setJobsBusy(true);
    try {
      const res = await fetch(`${apiBase}/jobs?limit=50&offset=0`, { headers: authHeaders });
      if (res.status === 401) {
        clearAuthOn401();
        return;
      }
      if (!res.ok) throw new Error(`Failed to load jobs (${res.status})`);
      const data = (await res.json()) as Job[];
      setJobs(data);
    } finally {
      setJobsBusy(false);
    }
  }

  async function convertLead(
    lead: Lead,
    customerIn: { name: string; email: string; phone: string; address: string },
  ) {
    setAppError(null);
    try {
      if (!customerIn.name.trim()) throw new Error("Customer name is required.");
      if (!isValidEmail(customerIn.email)) throw new Error("Customer email format is invalid.");
      const res = await fetch(`${apiBase}/crm/leads/${encodeURIComponent(lead.id)}/convert`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          name: customerIn.name,
          email: customerIn.email || null,
          phone: customerIn.phone || null,
          address: customerIn.address || null,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        setAppError(text || `Convert failed (${res.status})`);
        return;
      }
      setConvertLeadId(null);
      setSuccessMessage("Lead converted to customer.");
      await Promise.all([refreshLeads(), refreshCustomers()]);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function login() {
    setAuthError("");
    const body = new URLSearchParams();
    body.set("username", loginUsername);
    body.set("password", loginPassword);
    // FastAPI OAuth2 form expects x-www-form-urlencoded.
    const res = await fetch(`${apiBase}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    if (!res.ok) {
      const text = await res.text();
      setAuthError(text || `Login failed (${res.status})`);
      return;
    }
    const data = (await res.json()) as TokenResponse;
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
  }

  async function createLead() {
    setAppError(null);
    try {
    if (!leadForm.name.trim()) throw new Error("Lead name is required.");
    if (!isValidEmail(leadForm.email)) throw new Error("Lead email format is invalid.");
    if (leadForm.phone.trim() && leadForm.phone.trim().length < 6) throw new Error("Lead phone looks too short.");
    if (!leadForm.email.trim() && !leadForm.phone.trim()) {
      throw new Error("Provide at least an email or phone so we can contact the customer.");
    }
    const issue = leadForm.issue_description?.trim() ?? "";
    if (issue.length < 10) {
      throw new Error("Describe the issue in at least 10 characters (scope, asset, urgency).");
    }
    const res = await fetch(`${apiBase}/crm/leads`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({
        name: leadForm.name,
        email: leadForm.email || null,
        phone: leadForm.phone || null,
        property_type: leadForm.property_type || null,
        preferred_time_slots: leadForm.preferred_time_slots || null,
        issue_description: leadForm.issue_description || null,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    setLeadForm({
      name: "",
      email: "",
      phone: "",
      property_type: "House",
      preferred_time_slots: "",
      issue_description: "",
    });
    setSuccessMessage("Lead created.");
    await refreshLeads();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function createQuote() {
    setAppError(null);
    try {
    if (!quoteForm.customer_id.trim()) throw new Error("Select a customer for the quote.");
    if (quoteForm.labour_qty < 0 || quoteForm.materials_qty < 0) throw new Error("Quantities cannot be negative.");
    if (quoteForm.labour_unit_price < 0 || quoteForm.materials_unit_price < 0) {
      throw new Error("Unit prices cannot be negative.");
    }
    const items: QuoteItemIn[] = [];
    if (quoteForm.labour_desc.trim()) {
      items.push({
        item_type: "labour",
        description: quoteForm.labour_desc,
        quantity: quoteForm.labour_qty,
        unit_price: quoteForm.labour_unit_price,
      });
    }
    if (quoteForm.materials_desc.trim() && quoteForm.materials_qty > 0) {
      items.push({
        item_type: "materials",
        description: quoteForm.materials_desc,
        quantity: quoteForm.materials_qty,
        unit_price: quoteForm.materials_unit_price,
      });
    }
    if (items.length === 0) throw new Error("Add at least one quote item.");

    const res = await fetch(`${apiBase}/quotes`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: quoteForm.customer_id || null,
        currency: quoteForm.currency,
        notes: quoteForm.notes || null,
        items,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    setQuoteForm({
      customer_id: "",
      currency: "GBP",
      notes: "",
      labour_desc: "",
      labour_qty: 1,
      labour_unit_price: 0,
      materials_desc: "",
      materials_qty: 0,
      materials_unit_price: 0,
    });
    setSuccessMessage("Quote created.");
    await refreshQuotes();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function acceptQuote(quoteId: string) {
    setAppError(null);
    try {
      const res = await fetch(`${apiBase}/quotes/${encodeURIComponent(quoteId)}/accept`, {
        method: "POST",
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Quote accepted.");
      await refreshQuotes();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function createJob() {
    setAppError(null);
    try {
    if (!jobForm.quote_id) throw new Error("Select a quote.");
    const selectedQuote = quotes.find((q) => q.id === jobForm.quote_id);
    if (!selectedQuote) throw new Error("Selected quote not found — refresh quotes and try again.");
    if (String(selectedQuote.status).toLowerCase() !== "accepted") {
      throw new Error("Quote must be accepted before creating a job (accept the quote in Quotes first).");
    }
    if (!jobForm.address.trim()) throw new Error("Enter an address.");
    if (jobForm.address.trim().length < 5) throw new Error("Address is too short.");

    const scheduledAt = jobForm.scheduled_at.trim() ? jobForm.scheduled_at.trim() : null;

    const res = await fetch(`${apiBase}/jobs`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: null,
        quote_id: jobForm.quote_id,
        address: jobForm.address,
        scheduled_at: scheduledAt,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    setJobForm({ quote_id: jobForm.quote_id, address: "", scheduled_at: "" });
    setSuccessMessage("Job created.");
    await refreshJobs();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function setJobGeofence() {
    setAppError(null);
    try {
    if (!geofenceForm.job_id) throw new Error("Select a job.");
    if (geofenceForm.latitude < -90 || geofenceForm.latitude > 90) throw new Error("Latitude must be between -90 and 90.");
    if (geofenceForm.longitude < -180 || geofenceForm.longitude > 180) throw new Error("Longitude must be between -180 and 180.");
    if (geofenceForm.radius_m <= 0) throw new Error("Radius must be greater than 0.");
    const res = await fetch(`${apiBase}/tracking/geofences/${geofenceForm.job_id}`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: geofenceForm.latitude,
        longitude: geofenceForm.longitude,
        radius_m: geofenceForm.radius_m,
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    }
  }

  async function punchIn() {
    setTimeBusy(true);
    try {
      const oid = timeOfflineDeviceId.trim();
      const res = await fetch(`${apiBase}/time/punch/in`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: timeForm.job_id,
          latitude: timeForm.latitude,
          longitude: timeForm.longitude,
          ...(oid ? { offline_device_id: oid } : {}),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const p = (await res.json()) as Punch;
      setPunches((prev) => [p, ...prev].slice(0, 20));
      setSuccessMessage("Punched in.");
      await refreshTimesheet();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setTimeBusy(false);
    }
  }

  async function punchOut() {
    setTimeBusy(true);
    try {
      const oid = timeOfflineDeviceId.trim();
      const res = await fetch(`${apiBase}/time/punch/out`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: timeForm.job_id,
          latitude: timeForm.latitude,
          longitude: timeForm.longitude,
          ...(oid ? { offline_device_id: oid } : {}),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const p = (await res.json()) as Punch;
      setPunches((prev) => [p, ...prev].slice(0, 20));
      setSuccessMessage("Punched out.");
      await refreshTimesheet();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setTimeBusy(false);
    }
  }

  function fillPunchLocationFromDevice() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setAppError("Geolocation is not available in this browser.");
      return;
    }
    setPunchGeoBusy(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setTimeForm((f) => ({
          ...f,
          latitude: Math.round(pos.coords.latitude * 1e6) / 1e6,
          longitude: Math.round(pos.coords.longitude * 1e6) / 1e6,
        }));
        setPunchGeoBusy(false);
      },
      (err) => {
        setPunchGeoBusy(false);
        setAppError(err?.message ?? "Could not read location.");
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 120000 },
    );
  }

  async function refreshTimesheet() {
    // Best-effort: if user is not an Engineer, this will 403.
    try {
      const res = await fetch(`${apiBase}/time/timesheets?date=${encodeURIComponent(timesheetDate)}`, {
        headers: authHeaders,
      });
      if (res.status === 401) {
        clearAuthOn401();
        return;
      }
      if (!res.ok) return;
      const t = (await res.json()) as Timesheet;
      setTimesheet(t);
    } catch {
      // Ignore UI refresh errors.
    }
  }

  async function approveTimesheet() {
    if (!approvalForm.user_id || !approvalForm.date_str) return;
    setApprovalBusy(true);
    try {
      const res = await fetch(`${apiBase}/time/timesheets/approve`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: approvalForm.user_id, date_str: approvalForm.date_str }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Timesheet approved.");
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setApprovalBusy(false);
    }
  }

  async function exportPayroll() {
    if (!approvalForm.date_str) return;
    setPayrollExportBusy(true);
    setPayrollExport(null);
    try {
      const res = await fetch(`${apiBase}/time/payroll/export`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "", date_str: approvalForm.date_str }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as { date_str: string; lines: { user_id: string; total_seconds: number; amount: number }[] };
      setPayrollExport(data);
      setSuccessMessage("Payroll export loaded.");
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setPayrollExportBusy(false);
    }
  }

  async function loadJobGeofence() {
    if (!timeForm.job_id) {
      setLoadedGeofence(null);
      return;
    }
    setGeofenceBusy(true);
    try {
      const res = await fetch(`${apiBase}/tracking/geofences/${encodeURIComponent(timeForm.job_id)}`, {
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(await res.text());
      const g = (await res.json()) as JobGeofence;
      setLoadedGeofence(g);
    } finally {
      setGeofenceBusy(false);
    }
  }

  async function refreshCertificates(jobId: string) {
    setCertBusy(true);
    try {
      const url = jobId.trim()
        ? `${apiBase}/compliance/certificates?job_id=${encodeURIComponent(jobId)}&limit=50`
        : `${apiBase}/compliance/certificates?limit=50`;
      const res = await fetch(url, { headers: authHeaders });
      if (!res.ok) return;
      const data = (await res.json()) as Certificate[];
      setCertificates(data);
    } finally {
      setCertBusy(false);
    }
  }

  async function generateCertificate() {
    setCertBusy(true);
    try {
      const res = await fetch(`${apiBase}/compliance/certificates/generate`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: certificateJobId,
          certificate_type: certificateType,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Certificate generated.");
      await refreshCertificates(certificateJobId);
    } finally {
      setCertBusy(false);
    }
  }

  async function refreshInvoices(jobId: string) {
    setInvoiceBusy(true);
    try {
      const url = jobId.trim()
        ? `${apiBase}/invoicing/invoices?job_id=${encodeURIComponent(jobId)}&limit=50`
        : `${apiBase}/invoicing/invoices?limit=50`;
      const res = await fetch(url, { headers: authHeaders });
      if (!res.ok) return;
      const data = (await res.json()) as Invoice[];
      setInvoices(data);
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function generateInvoice() {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/generate`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: invoiceJobId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Invoice generated.");
      await refreshInvoices(invoiceJobId);
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function payInvoice(invoiceId: string) {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/${encodeURIComponent(invoiceId)}/pay`, {
        method: "POST",
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Invoice marked paid.");
      await refreshInvoices(invoiceJobId);
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function holdInvoice(invoiceId: string, note: string) {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/${encodeURIComponent(invoiceId)}/hold`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ note: note || "Held from UI" }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Invoice held.");
      await refreshInvoices(invoiceJobId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function loadCommPrefs(customerId: string) {
    if (!customerId) return;
    setCommPrefsBusy(true);
    try {
      const res = await fetch(`${apiBase}/customers/${encodeURIComponent(customerId)}/communication-preferences`, { headers: authHeaders });
      if (res.status === 401 || res.status === 403) return;
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as { id: string; channel: string; enabled: boolean; contact_reference: string | null; preferred: boolean }[];
      setCommPrefs(data);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
      setCommPrefs([]);
    } finally {
      setCommPrefsBusy(false);
    }
  }

  async function createCommPref(customerId: string) {
    setCommPrefsBusy(true);
    try {
      const res = await fetch(`${apiBase}/customers/${encodeURIComponent(customerId)}/communication-preferences`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({
          channel: commPrefForm.channel,
          enabled: commPrefForm.enabled,
          contact_reference: commPrefForm.contact_reference.trim() || null,
          preferred: commPrefForm.preferred,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Preference added.");
      setCommPrefForm({ channel: "email", enabled: true, contact_reference: "", preferred: false });
      await loadCommPrefs(customerId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setCommPrefsBusy(false);
    }
  }

  async function downloadCertificatePdf(certId: string) {
    setCertDownloadBusy(certId);
    try {
      const regRes = await fetch(`${apiBase}/compliance/certificates/${encodeURIComponent(certId)}/regenerate-pdf`, {
        method: "POST",
        headers: authHeaders,
      });
      if (!regRes.ok) throw new Error(await regRes.text());
      const doc = (await regRes.json()) as { id: string };
      const linkRes = await fetch(`${apiBase}/documents/${encodeURIComponent(doc.id)}/download-link`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!linkRes.ok) throw new Error(await linkRes.text());
      const link = (await linkRes.json()) as { download_url: string };
      window.open(`${apiBase}${link.download_url}`, "_blank");
      setSuccessMessage("Certificate PDF ready.");
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setCertDownloadBusy(null);
    }
  }

  async function patchCommPref(preferenceId: string, patch: { enabled?: boolean }) {
    setCommPrefsBusy(true);
    try {
      const res = await fetch(`${apiBase}/customers/communication-preferences/${encodeURIComponent(preferenceId)}`, {
        method: "PATCH",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Preference updated.");
      if (commPrefCustomerId) await loadCommPrefs(commPrefCustomerId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setCommPrefsBusy(false);
    }
  }

  async function manualAssignJob(jobId: string, engineerId: string) {
    setManualAssignBusy(jobId);
    try {
      const res = await fetch(`${apiBase}/jobs/${encodeURIComponent(jobId)}/assign`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ engineer_id: engineerId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Job assigned.");
      await refreshJobs();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setManualAssignBusy(null);
    }
  }

  async function updateJobStatus(jobId: string, status: string) {
    setStatusUpdateBusy(jobId);
    try {
      const res = await fetch(`${apiBase}/jobs/${encodeURIComponent(jobId)}/status`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage(`Job status set to ${status}.`);
      await refreshJobs();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setStatusUpdateBusy(null);
    }
  }

  async function assignBestEngineer(jobId: string) {
    setAssignBestBusy(jobId);
    try {
      const res = await fetch(`${apiBase}/dispatch/jobs/${encodeURIComponent(jobId)}/assign-best`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Assigned from UI" }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as { selected_engineer_id: string; explanation_reasons?: string[] };
      setSuccessMessage(
        `Assigned to engineer ${data.selected_engineer_id.slice(0, 8)}…${data.explanation_reasons?.length ? ` (${data.explanation_reasons.slice(0, 2).join(", ")})` : ""}`,
      );
      await refreshJobs();
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setAssignBestBusy(null);
    }
  }

  async function markInvoiceFinanceReview(invoiceId: string, note?: string) {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/${encodeURIComponent(invoiceId)}/finance-review`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ note: note ?? undefined }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Invoice marked for finance review.");
      await refreshInvoices(invoiceJobId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function clearInvoiceFinanceReview(invoiceId: string) {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/${encodeURIComponent(invoiceId)}/clear-finance-review`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Finance review cleared.");
      await refreshInvoices(invoiceJobId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function releaseInvoiceHold(invoiceId: string) {
    setInvoiceBusy(true);
    try {
      const res = await fetch(`${apiBase}/invoicing/invoices/${encodeURIComponent(invoiceId)}/release-hold`, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ note: "Release hold" }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccessMessage("Invoice released from hold.");
      await refreshInvoices(invoiceJobId);
    } catch (e) {
      setAppError(e instanceof Error ? e.message : String(e));
    } finally {
      setInvoiceBusy(false);
    }
  }

  async function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
  }

  async function refreshRolloutAll() {
    setRolloutBusy(true);
    try {
      const [wavesRes, alertsRes, deliveriesRes, digestRes] = await Promise.all([
        fetch(`${apiBase}/rollout/waves`, { headers: authHeaders }),
        fetch(`${apiBase}/rollout/alerts`, { headers: authHeaders }),
        fetch(`${apiBase}/rollout/notifications/deliveries`, { headers: authHeaders }),
        fetch(`${apiBase}/rollout/alerts/digest`, { headers: authHeaders }),
      ]);
      if (wavesRes.ok) setRolloutWaves((await wavesRes.json()) as RolloutWave[]);
      if (alertsRes.ok) setRolloutAlerts((await alertsRes.json()) as RolloutAlert[]);
      if (deliveriesRes.ok) setRolloutDeliveries((await deliveriesRes.json()) as NotificationDelivery[]);
      if (digestRes.ok) setRolloutDigest((await digestRes.json()) as RolloutDigest);
    } finally {
      setRolloutBusy(false);
    }
  }

  async function createRolloutWave() {
    const res = await fetch(`${apiBase}/rollout/waves`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify(rolloutWaveForm),
    });
    if (!res.ok) throw new Error(await res.text());
    setRolloutWaveForm({ ...rolloutWaveForm, name: "" });
    await refreshRolloutAll();
  }

  async function runRolloutCycle() {
    const res = await fetch(`${apiBase}/rollout/automation/run-cycle?force=true`, {
      method: "POST",
      headers: authHeaders,
    });
    if (!res.ok) throw new Error(await res.text());
    await refreshRolloutAll();
  }

  async function evaluateRolloutHealth() {
    const res = await fetch(`${apiBase}/rollout/health/evaluate`, {
      method: "POST",
      headers: authHeaders,
    });
    if (!res.ok) throw new Error(await res.text());
    await refreshRolloutAll();
  }

  async function processNotificationRetries() {
    const res = await fetch(`${apiBase}/rollout/notifications/retries/process`, {
      method: "POST",
      headers: authHeaders,
    });
    if (!res.ok) throw new Error(await res.text());
    await refreshRolloutAll();
  }

  async function acknowledgeAlert(alertId: string) {
    const res = await fetch(`${apiBase}/rollout/alerts/${encodeURIComponent(alertId)}/ack`, {
      method: "POST",
      headers: authHeaders,
    });
    if (!res.ok) throw new Error(await res.text());
    await refreshRolloutAll();
  }

  if (!isAuthed) {
    return (
      <div className="App">
        <div className="card">
          <h2>PHI-DPS Admin Login</h2>
          <div className="field">
            <label>Username (email)</label>
            <input value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
          </div>
          {authError ? <div className="error">{authError}</div> : null}
          <button onClick={() => void login()}>Login</button>
          <div className="hint">
            API base: <code>{getPhiDpsApiBase()}</code> — set <code>REACT_APP_PHI_DPS_API_BASE</code> at build time or{" "}
            <code>config.js</code> <code>apiBase</code> at deploy (see <code>PRODUCTION_CHECKLIST.md</code>).
          </div>
          <div className="hint">
            Dev default: <code>admin@example.com</code> / <code>admin</code>
          </div>
        </div>
      </div>
    );
  }

  const tabTitles: Record<string, string> = {
    dashboard: "Dashboard",
    leads: "Leads",
    customers: "Customers",
    quotes: "Quotes",
    jobs: "Jobs",
    time: "Time & punches",
    compliance: "Certificates",
    invoices: "Invoices",
    approvals: "Approvals",
    vehicles: "Vehicles",
    competence: "Competence",
    analytics: "Analytics",
    ops: "Ops",
    settings: "Settings",
    commercial: "Commercial",
    access: "Access",
    portal: "Portal",
    rollout: "Rollout Ops",
    labour_ai: "Labour & AI",
    map: "Live Map",
    sites: "Sites",
    assets: "Assets",
    inventory: "Inventory",
    sla: "SLA policies",
    ppm: "PPM schedules",
  };

  return (
    <div className="App">
      <div className="app-layout">
        <aside className="app-sidebar">
          <div className="app-sidebar-group">Overview</div>
          <button
            type="button"
            className={activeTab === "dashboard" ? "active" : ""}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>
          <div className="app-sidebar-group">CRM</div>
          <button
            type="button"
            className={activeTab === "leads" ? "active" : ""}
            onClick={() => setActiveTab("leads")}
          >
            Leads
          </button>
          <button
            type="button"
            className={activeTab === "customers" ? "active" : ""}
            onClick={() => setActiveTab("customers")}
          >
            Customers
          </button>
          <button
            type="button"
            className={activeTab === "quotes" ? "active" : ""}
            onClick={() => setActiveTab("quotes")}
          >
            Quotes
          </button>
          <button
            type="button"
            className={activeTab === "jobs" ? "active" : ""}
            onClick={() => setActiveTab("jobs")}
          >
            Jobs
          </button>
          <div className="app-sidebar-group">Field</div>
          <button
            type="button"
            className={activeTab === "map" ? "active" : ""}
            onClick={() => setActiveTab("map")}
          >
            Live Map
          </button>
          <button
            type="button"
            className={activeTab === "time" ? "active" : ""}
            onClick={() => setActiveTab("time")}
          >
            Time
          </button>
          <button
            type="button"
            className={activeTab === "compliance" ? "active" : ""}
            onClick={() => setActiveTab("compliance")}
          >
            Compliance
          </button>
          <div className="app-sidebar-group">Finance</div>
          <button
            type="button"
            className={activeTab === "invoices" ? "active" : ""}
            onClick={() => setActiveTab("invoices")}
          >
            Invoices
          </button>
          <button
            type="button"
            className={activeTab === "approvals" ? "active" : ""}
            onClick={() => setActiveTab("approvals")}
          >
            Approvals
          </button>
          <div className="app-sidebar-group">Ops</div>
          <button
            type="button"
            className={activeTab === "commercial" ? "active" : ""}
            onClick={() => setActiveTab("commercial")}
          >
            Commercial
          </button>
          <button
            type="button"
            className={activeTab === "rollout" ? "active" : ""}
            onClick={() => setActiveTab("rollout")}
          >
            Rollout
          </button>
          <button
            type="button"
            className={activeTab === "labour_ai" ? "active" : ""}
            onClick={() => setActiveTab("labour_ai")}
          >
            Labour & AI
          </button>
          <button
            type="button"
            className={activeTab === "sites" ? "active" : ""}
            onClick={() => setActiveTab("sites")}
          >
            Sites
          </button>
          <button
            type="button"
            className={activeTab === "assets" ? "active" : ""}
            onClick={() => setActiveTab("assets")}
          >
            Assets
          </button>
          <button
            type="button"
            className={activeTab === "inventory" ? "active" : ""}
            onClick={() => setActiveTab("inventory")}
          >
            Inventory
          </button>
          <button
            type="button"
            className={activeTab === "sla" ? "active" : ""}
            onClick={() => setActiveTab("sla")}
          >
            SLA policies
          </button>
          <button
            type="button"
            className={activeTab === "ppm" ? "active" : ""}
            onClick={() => setActiveTab("ppm")}
          >
            PPM schedules
          </button>
          <button
            type="button"
            className={activeTab === "vehicles" ? "active" : ""}
            onClick={() => setActiveTab("vehicles")}
          >
            Vehicles
          </button>
          <button
            type="button"
            className={activeTab === "competence" ? "active" : ""}
            onClick={() => setActiveTab("competence")}
          >
            Competence
          </button>
          <button
            type="button"
            className={activeTab === "analytics" ? "active" : ""}
            onClick={() => setActiveTab("analytics")}
          >
            Analytics
          </button>
          <button
            type="button"
            className={activeTab === "ops" ? "active" : ""}
            onClick={() => setActiveTab("ops")}
          >
            Ops
          </button>
          <div className="app-sidebar-group">Admin</div>
          <button
            type="button"
            className={activeTab === "settings" ? "active" : ""}
            onClick={() => setActiveTab("settings")}
          >
            Settings
          </button>
          <button
            type="button"
            className={activeTab === "access" ? "active" : ""}
            onClick={() => setActiveTab("access")}
          >
            Access
          </button>
          <button
            type="button"
            className={activeTab === "portal" ? "active" : ""}
            onClick={() => setActiveTab("portal")}
          >
            Portal
          </button>
          <div style={{ flex: 1 }} />
          <button type="button" className="secondary" onClick={() => void logout()} style={{ margin: "8px 8px 0" }}>
            Logout
          </button>
        </aside>
        <main className="app-main">
          <div className="topbar">
            <h1>{tabTitles[activeTab] ?? activeTab}</h1>
            {currentUser ? (
              <span className="topbar-user" style={{ fontSize: 13, color: "rgba(231,238,252,0.7)" }}>
                {currentUser.email}
                {currentUser.roles?.length ? ` · ${currentUser.roles.map((r) => r.name).join(", ")}` : ""}
              </span>
            ) : null}
          </div>

      {appError ? (
        <div className="error" style={{ margin: "0 18px 12px" }}>
          {appError}
          <button type="button" className="secondary" style={{ marginLeft: 8 }} onClick={() => setAppError(null)}>
            Dismiss
          </button>
        </div>
      ) : null}
      {successMessage ? (
        <SuccessBanner message={successMessage} onDismiss={() => setSuccessMessage(null)} />
      ) : null}

      {activeTab === "dashboard" ? (
        <div className="grid" style={{ padding: 18 }}>
          <div className="card">
            <h3>Overview</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: 12 }}>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("leads")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>{leads.length}</div>
                <div className="item-sub">Leads</div>
              </button>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("customers")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>{customers.length}</div>
                <div className="item-sub">Customers</div>
              </button>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("quotes")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>{quotes.length}</div>
                <div className="item-sub">Quotes</div>
              </button>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("jobs")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>{jobs.length}</div>
                <div className="item-sub">Jobs</div>
              </button>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("jobs")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>
                  {jobs.filter((j) => j.status && !["completed", "cancelled"].includes(j.status.toLowerCase())).length}
                </div>
                <div className="item-sub">In progress</div>
              </button>
              <button
                type="button"
                className="secondary"
                style={{ textAlign: "left", padding: 16 }}
                onClick={() => setActiveTab("map")}
              >
                <div className="item-title" style={{ fontSize: 24 }}>Map</div>
                <div className="item-sub">Dispatch</div>
              </button>
            </div>
            <div className="hint" style={{ marginTop: 16 }}>
              Click a card to go to that section.
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "leads" ? (
        <div className="grid">
          <div className="card">
            <h3>Create Lead</h3>
            <div className="field">
              <label>Name</label>
              <input value={leadForm.name} onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })} />
            </div>
            <div className="field">
              <label>Email</label>
              <input value={leadForm.email} onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })} />
            </div>
            <div className="field">
              <label>Phone</label>
              <input value={leadForm.phone} onChange={(e) => setLeadForm({ ...leadForm, phone: e.target.value })} />
            </div>
            <div className="field">
              <label>Property Type</label>
              <input
                value={leadForm.property_type}
                onChange={(e) => setLeadForm({ ...leadForm, property_type: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Preferred Time Slots</label>
              <input
                value={leadForm.preferred_time_slots}
                onChange={(e) => setLeadForm({ ...leadForm, preferred_time_slots: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Issue Description</label>
              <textarea
                value={leadForm.issue_description}
                onChange={(e) => setLeadForm({ ...leadForm, issue_description: e.target.value })}
              />
            </div>
            <button onClick={() => void createLead()}>Create Lead</button>
          </div>

          <div className="card">
            <div className="row">
              <h3>Leads</h3>
              <button className="secondary" onClick={() => void refreshLeads()}>
                Refresh
              </button>
            </div>
            {leadsBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {leads.map((l) => (
                <div key={l.id} className="item">
                  <div className="row" style={{ alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div className="item-title">{l.name}</div>
                      <div className="item-sub">
                        {l.email || "—"} • {l.phone || "—"} • <span className="badge">{l.status}</span>
                        {l.converted_customer_id ? " • Converted" : ""}
                      </div>
                      <div className="item-body">{l.issue_description || "No issue description"}</div>
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      {!l.converted_customer_id ? (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => setConvertLeadId(convertLeadId === l.id ? null : l.id)}
                        >
                          {convertLeadId === l.id ? "Cancel" : "Convert"}
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => {
                            setQuoteFormPrefillCustomerId(l.converted_customer_id!);
                            setActiveTab("quotes");
                          }}
                        >
                          Create quote
                        </button>
                      )}
                    </div>
                  </div>
                  {convertLeadId === l.id ? (
                    <ConvertLeadForm
                      lead={l}
                      onConvert={(cust) => convertLead(l, cust)}
                      onCancel={() => setConvertLeadId(null)}
                    />
                  ) : null}
                </div>
              ))}
              {leads.length === 0 ? <div className="muted">No leads yet.</div> : null}
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "quotes" ? (
        <div className="grid">
          <div className="card">
            <h3>Create Quote</h3>
            <div className="field">
              <label>Customer</label>
              <select
                value={quoteForm.customer_id}
                onChange={(e) => setQuoteForm({ ...quoteForm, customer_id: e.target.value })}
              >
                <option value="">— None —</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.email ? `(${c.email})` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Labour Description</label>
              <input
                value={quoteForm.labour_desc}
                onChange={(e) => setQuoteForm({ ...quoteForm, labour_desc: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Labour Qty</label>
              <input
                type="number"
                value={quoteForm.labour_qty}
                onChange={(e) => setQuoteForm({ ...quoteForm, labour_qty: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Labour Unit Price</label>
              <input
                type="number"
                value={quoteForm.labour_unit_price}
                onChange={(e) => setQuoteForm({ ...quoteForm, labour_unit_price: Number(e.target.value) })}
              />
            </div>

            <div className="divider" />

            <div className="field">
              <label>Materials Description</label>
              <input
                value={quoteForm.materials_desc}
                onChange={(e) => setQuoteForm({ ...quoteForm, materials_desc: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Materials Qty</label>
              <input
                type="number"
                value={quoteForm.materials_qty}
                onChange={(e) => setQuoteForm({ ...quoteForm, materials_qty: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Materials Unit Price</label>
              <input
                type="number"
                value={quoteForm.materials_unit_price}
                onChange={(e) => setQuoteForm({ ...quoteForm, materials_unit_price: Number(e.target.value) })}
              />
            </div>

            <div className="field">
              <label>Notes (optional)</label>
              <input value={quoteForm.notes} onChange={(e) => setQuoteForm({ ...quoteForm, notes: e.target.value })} />
            </div>

            <button onClick={() => void createQuote()}>Create Quote</button>
          </div>

          <div className="card">
            <div className="row">
              <h3>Quotes</h3>
              <button className="secondary" onClick={() => void refreshQuotes()}>
                Refresh
              </button>
            </div>
            {quotesBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {quotes.map((q) => (
                <div key={q.id} className="item">
                  <div className="row" style={{ alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div className="item-title">
                        {q.status} • {q.grand_total} {q.currency}
                        {customers.find((c) => c.id === q.customer_id)
                          ? ` • ${customers.find((c) => c.id === q.customer_id)!.name}`
                          : ""}
                      </div>
                      <div className="item-sub">
                        <span className="badge">{q.id.slice(0, 8)}...</span>
                      </div>
                      {q.notes ? <div className="item-body">{q.notes}</div> : null}
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() =>
                          expandedQuoteId === q.id
                            ? (setExpandedQuoteId(null), setQuoteDetail(null))
                            : void loadQuoteDetail(q.id)
                        }
                      >
                        {expandedQuoteId === q.id ? "Hide" : "View"}
                      </button>
                      {q.status === "draft" ? (
                        <button type="button" onClick={() => acceptQuote(q.id)}>
                          Accept
                        </button>
                      ) : null}
                    </div>
                  </div>
                  {expandedQuoteId === q.id && quoteDetail?.id === q.id ? (
                    <div className="card" style={{ marginTop: 12, padding: 12, background: "rgba(0,0,0,0.15)" }}>
                      <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>Quote details</h4>
                      <div className="item-sub" style={{ marginBottom: 8 }}>
                        Labour: {quoteDetail.labour_total} {quoteDetail.currency} · Materials: {quoteDetail.materials_total} · Total: {quoteDetail.grand_total}
                      </div>
                      {quoteDetail.items && quoteDetail.items.length > 0 ? (
                        <ul className="hub-list-compact" style={{ margin: "0 0 8px", paddingLeft: 20 }}>
                          {quoteDetail.items.map((it) => (
                            <li key={it.id}>
                              {it.item_type}: {it.description} × {it.quantity} @ {it.unit_price} = {it.line_total}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                      {quoteDetail.notes ? <div className="hint" style={{ marginTop: 4 }}>{quoteDetail.notes}</div> : null}
                      {quoteDetail.status === "draft" ? (
                        <button type="button" style={{ marginTop: 8 }} onClick={() => acceptQuote(q.id)}>
                          Accept this quote
                        </button>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
              {quotes.length === 0 ? <div className="muted">No quotes yet.</div> : null}
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "customers" ? (
        <div className="grid">
          <div className="card">
            <div className="row">
              <h3>Customers</h3>
              <button className="secondary" onClick={() => void refreshCustomers()}>
                Refresh
              </button>
            </div>
            {customersBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {customers.map((c) => (
                <div key={c.id} className="item">
                  <div className="item-title">{c.name}</div>
                  <div className="item-sub">
                    {c.email || "—"} • {c.phone || "—"}
                  </div>
                  {c.address ? <div className="item-body">{c.address}</div> : null}
                </div>
              ))}
              {customers.length === 0 ? <div className="muted">No customers yet. Convert leads to create customers.</div> : null}
            </div>
          </div>
          <div className="card">
            <h3>Communication preferences</h3>
            <p className="hint" style={{ marginBottom: 12 }}>
              Manage how and when to contact customers (email, SMS). Requires permission.
            </p>
            <div className="field">
              <label>Customer</label>
              <select
                value={commPrefCustomerId}
                onChange={(e) => {
                  setCommPrefCustomerId(e.target.value);
                  if (e.target.value) void loadCommPrefs(e.target.value);
                  else setCommPrefs([]);
                }}
              >
                <option value="">Select customer...</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.email ? `(${c.email})` : ""}
                  </option>
                ))}
              </select>
            </div>
            {commPrefCustomerId ? (
              <>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => void loadCommPrefs(commPrefCustomerId)}
                  disabled={commPrefsBusy}
                >
                  {commPrefsBusy ? "Loading…" : "Refresh"}
                </button>
                <div className="list" style={{ marginTop: 12 }}>
                  {commPrefs.map((p) => (
                    <div key={p.id} className="item">
                      <div className="item-title">
                        {p.channel} · {p.enabled ? "Enabled" : "Disabled"}
                        {p.preferred ? " · Preferred" : ""}
                      </div>
                      <div className="item-sub">{p.contact_reference || "Default"}</div>
                      <button
                        type="button"
                        className="secondary"
                        style={{ marginTop: 4, fontSize: 12 }}
                        onClick={() => void patchCommPref(p.id, { enabled: !p.enabled })}
                        disabled={commPrefsBusy}
                      >
                        {p.enabled ? "Disable" : "Enable"}
                      </button>
                    </div>
                  ))}
                  {commPrefs.length === 0 && !commPrefsBusy ? <div className="muted">No preferences. Add one below.</div> : null}
                </div>
                <div className="divider" />
                <h4 style={{ fontSize: 14, margin: "0 0 8px" }}>Add preference</h4>
                <div className="field">
                  <label>Channel</label>
                  <select
                    value={commPrefForm.channel}
                    onChange={(e) => setCommPrefForm({ ...commPrefForm, channel: e.target.value })}
                  >
                    <option value="email">Email</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>
                <div className="field">
                  <label>Contact (optional)</label>
                  <input
                    value={commPrefForm.contact_reference}
                    onChange={(e) => setCommPrefForm({ ...commPrefForm, contact_reference: e.target.value })}
                    placeholder="email@example.com or +44..."
                  />
                </div>
                <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    id="comm-pref-enabled"
                    checked={commPrefForm.enabled}
                    onChange={(e) => setCommPrefForm({ ...commPrefForm, enabled: e.target.checked })}
                  />
                  <label htmlFor="comm-pref-enabled">Enabled</label>
                </div>
                <div className="field" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    id="comm-pref-preferred"
                    checked={commPrefForm.preferred}
                    onChange={(e) => setCommPrefForm({ ...commPrefForm, preferred: e.target.checked })}
                  />
                  <label htmlFor="comm-pref-preferred">Preferred</label>
                </div>
                <button
                  type="button"
                  onClick={() => void createCommPref(commPrefCustomerId)}
                  disabled={commPrefsBusy}
                >
                  Add preference
                </button>
              </>
            ) : null}
            <div className="divider" />
            <button className="secondary" onClick={() => setActiveTab("leads")}>Go to Leads</button>
          </div>
        </div>
      ) : null}

      {activeTab === "jobs" ? (
        <div>
        <div className="grid">
          <div className="card">
            <h3>Create Job</h3>
            <div className="field">
              <label>Quote (accepted)</label>
              <select value={jobForm.quote_id} onChange={(e) => setJobForm({ ...jobForm, quote_id: e.target.value })}>
                <option value="">Select quote...</option>
                {quotes
                  .filter((q) => q.status === "accepted")
                  .map((q) => {
                    const cust = customers.find((c) => c.id === q.customer_id);
                    const label = cust ? `${cust.name} • ${q.grand_total} ${q.currency}` : `${q.grand_total} ${q.currency}`;
                    return (
                      <option key={q.id} value={q.id}>
                        {label}
                      </option>
                    );
                  })}
              </select>
              {quotes.filter((q) => q.status === "accepted").length === 0 && quotes.length > 0 ? (
                <div className="hint">Accept a quote on the Quotes tab first.</div>
              ) : null}
            </div>
            <div className="field">
              <label>Address</label>
              <textarea value={jobForm.address} onChange={(e) => setJobForm({ ...jobForm, address: e.target.value })} />
            </div>
            <div className="field">
              <label>Scheduled At (optional)</label>
              <input
                type="datetime-local"
                value={
                  jobForm.scheduled_at && jobForm.scheduled_at.includes("T")
                    ? jobForm.scheduled_at.slice(0, 16)
                    : ""
                }
                onChange={(e) =>
                  setJobForm({
                    ...jobForm,
                    scheduled_at: e.target.value ? new Date(e.target.value).toISOString() : "",
                  })
                }
              />
            </div>
            <button onClick={() => void createJob()}>Create Job</button>
          </div>

          <div className="card">
            <div className="row">
              <h3>Jobs</h3>
              <button className="secondary" onClick={() => void refreshJobs()}>
                Refresh
              </button>
            </div>
            {jobsBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {jobs.map((j) => {
                const terminal = ["completed", "closed", "cancelled"].includes((j.status || "").toLowerCase());
                const unassigned = !j.assigned_engineer_id && !terminal;
                return (
                  <div key={j.id} className="item">
                    <div className="row" style={{ alignItems: "flex-start" }}>
                      <div style={{ flex: 1 }}>
                        <div className="item-title">
                          {j.status} • {j.address}
                        </div>
                        <div className="item-sub">
                          Quote: {j.quote_id ? `${j.quote_id.slice(0, 8)}...` : "—"} •{" "}
                          SLA: {j.sla_risk_state ? j.sla_risk_state : "—"} •{" "}
                          {j.assigned_engineer_id ? `Assigned: ${j.assigned_engineer_id.slice(0, 8)}…` : "Unassigned"} •{" "}
                          <span className="badge">{j.id.slice(0, 8)}...</span>
                        </div>
                      </div>
                      {unassigned ? (
                        <>
                          <select
                            value=""
                            onChange={(e) => {
                              const engId = e.target.value;
                              if (engId) void manualAssignJob(j.id, engId);
                            }}
                            disabled={manualAssignBusy === j.id}
                            style={{ fontSize: 13, padding: "4px 8px" }}
                          >
                            <option value="">Assign to…</option>
                            {engineerAvailability.map((e) => (
                              <option key={e.engineer_id} value={e.engineer_id}>
                                {e.engineer_id.slice(0, 8)}… ({e.availability_state})
                              </option>
                            ))}
                          </select>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => void assignBestEngineer(j.id)}
                            disabled={assignBestBusy === j.id}
                          >
                            {assignBestBusy === j.id ? "Assigning…" : "Assign best"}
                          </button>
                        </>
                      ) : null}
                      <select
                        value=""
                        onChange={(e) => {
                          const st = e.target.value;
                          if (st) void updateJobStatus(j.id, st);
                        }}
                        disabled={statusUpdateBusy === j.id}
                        style={{ fontSize: 13, padding: "4px 8px" }}
                      >
                        <option value="">Set status…</option>
                        <option value="dispatched">dispatched</option>
                        <option value="en_route">en_route</option>
                        <option value="on_site">on_site</option>
                        <option value="in_progress">in_progress</option>
                        <option value="completed">completed</option>
                        <option value="cancelled">cancelled</option>
                      </select>
                    </div>
                  </div>
                );
              })}
              {jobs.length === 0 ? <div className="muted">No jobs yet.</div> : null}
            </div>

            <div className="divider" />

            <h3>Set Job Geofence</h3>
            <div className="field">
              <label>Job</label>
              <select
                value={geofenceForm.job_id}
                onChange={(e) => setGeofenceForm({ ...geofenceForm, job_id: e.target.value })}
              >
                <option value="">Select job...</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.address} ({j.status})
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Latitude</label>
              <input
                type="number"
                value={geofenceForm.latitude}
                onChange={(e) => setGeofenceForm({ ...geofenceForm, latitude: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Longitude</label>
              <input
                type="number"
                value={geofenceForm.longitude}
                onChange={(e) => setGeofenceForm({ ...geofenceForm, longitude: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Radius (meters)</label>
              <input
                type="number"
                value={geofenceForm.radius_m}
                onChange={(e) => setGeofenceForm({ ...geofenceForm, radius_m: Number(e.target.value) })}
              />
            </div>
            <button onClick={() => void setJobGeofence()}>Set Geofence</button>
          </div>
        </div>
        <FieldJobConsole apiBase={apiBase} authHeaders={authHeaders} jobs={jobs.map((j) => ({ id: j.id, address: j.address, status: j.status }))} />
        </div>
      ) : null}

      {activeTab === "time" ? (
        <div className="field-work-wrap">
          {!browserOnline ? (
            <div className="portal-alert" style={{ margin: "0 18px 12px" }}>
              You appear offline — punch requests may fail until connectivity returns; native apps should queue punches when
              supported.
            </div>
          ) : null}
          <p className="field-hint" style={{ margin: "0 18px 8px" }}>
            Field-friendly layout: large punch targets, clear geofence / validity feedback, optional device
            GPS for coordinates. Use the Jobs tab → Field job console for SLA, completion gates, and equipment readiness.
          </p>
          <div className="field-work-grid">
          <div className="card field-punch-card" id="field-time-punches">
            <h3>Engineer punches</h3>
            <div className="field">
              <label>Job</label>
              <select
                value={timeForm.job_id}
                onChange={(e) => setTimeForm({ ...timeForm, job_id: e.target.value })}
              >
                <option value="">Select job...</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.address} ({j.status})
                  </option>
                ))}
              </select>
            </div>
            <div className="row" style={{ marginTop: 8 }}>
              <button className="secondary" onClick={() => void loadJobGeofence()} disabled={geofenceBusy || !timeForm.job_id}>
                {geofenceBusy ? "Loading..." : "Load Geofence"}
              </button>
              {loadedGeofence ? (
                <div className="muted" style={{ marginLeft: 10 }}>
                  Radius: {Math.round(loadedGeofence.radius_m)}m
                </div>
              ) : null}
            </div>
            {loadedGeofence ? (
              <div className="hint" style={{ marginTop: 8 }}>
                Point is{" "}
                <b>{haversineM(timeForm.latitude, timeForm.longitude, loadedGeofence.latitude, loadedGeofence.longitude) <= loadedGeofence.radius_m ? "inside" : "outside"}</b>{" "}
                the geofence (distance{" "}
                <b>{Math.round(haversineM(timeForm.latitude, timeForm.longitude, loadedGeofence.latitude, loadedGeofence.longitude))}m</b>).
              </div>
            ) : null}
            <div className="field field-geo-row">
              <div style={{ flex: 1, minWidth: 120 }}>
                <label>Latitude</label>
                <input
                  type="number"
                  value={timeForm.latitude}
                  onChange={(e) => setTimeForm({ ...timeForm, latitude: Number(e.target.value) })}
                />
              </div>
              <div style={{ flex: 1, minWidth: 120 }}>
                <label>Longitude</label>
                <input
                  type="number"
                  value={timeForm.longitude}
                  onChange={(e) => setTimeForm({ ...timeForm, longitude: Number(e.target.value) })}
                />
              </div>
              <div className="field-geo-actions">
                <label className="field-geo-actions-label">&nbsp;</label>
                <button
                  type="button"
                  className="secondary"
                  disabled={punchGeoBusy || timeBusy}
                  onClick={() => fillPunchLocationFromDevice()}
                >
                  {punchGeoBusy ? "Locating…" : "Use device GPS"}
                </button>
              </div>
            </div>
            <div className="field">
              <label>Offline device ID (optional)</label>
              <input
                value={timeOfflineDeviceId}
                onChange={(e) => setTimeOfflineDeviceId(e.target.value)}
                placeholder="Stable id from queued / replay punch"
              />
            </div>
            <div className="field-hint" style={{ marginTop: 4 }}>
              <code>POST /time/punch/in</code> and <code>/out</code> accept <code>offline_device_id</code> for idempotent
              replay when a client retries the same punch after connectivity returns (this web UI does not queue offline).
            </div>

            <div className="field-punch-row">
              <button type="button" onClick={() => void punchIn()} disabled={timeBusy || !timeForm.job_id.trim()}>
                Punch in
              </button>
              <button type="button" onClick={() => void punchOut()} disabled={timeBusy || !timeForm.job_id.trim()}>
                Punch out
              </button>
            </div>

            <div className="field-hint">
              Dev defaults for engineer: <code>engineer@example.com</code> / <code>engineer</code>. Ensure job geofence is
              loaded when testing distance validation.
            </div>
          </div>

          <div className="card field-timesheet-card" id="field-time-timesheet">
            <div className="row">
              <h3>Timesheet</h3>
              <button type="button" className="secondary field-touch-btn" onClick={() => void refreshTimesheet()}>
                Refresh
              </button>
            </div>
            <div className="field">
              <label>Date (YYYY-MM-DD UTC)</label>
              <input
                value={timesheetDate}
                onChange={(e) => setTimesheetDate(e.target.value)}
              />
            </div>

            {timesheet ? (
              <div className="list">
                <div className="item">
                  <div className="item-title">Total: {Math.round(timesheet.total_seconds / 60)} minutes</div>
                  <div className="item-sub">Sessions: {timesheet.sessions.length}</div>
                </div>
                {timesheet.sessions.map((s) => (
                  <div key={s.clock_out_punch_id} className="item">
                    <div className="item-title">
                      Job {s.job_id.slice(0, 8)}... • {Math.round(s.duration_seconds / 60)} minutes
                    </div>
                    <div className="item-sub">
                      In: {new Date(s.clock_in_at).toLocaleString()} • Out: {new Date(s.clock_out_at).toLocaleString()}
                    </div>
                  </div>
                ))}
                {timesheet.sessions.length === 0 ? <div className="muted">No sessions yet.</div> : null}
              </div>
            ) : (
              <div className="muted">No timesheet loaded yet.</div>
            )}

            <div className="divider" />

            <h3>Supervisor: Approve timesheet</h3>
            <p className="hint" style={{ marginBottom: 12 }}>
              Admin/Dispatcher: approve an engineer&apos;s timesheet for a date, or export payroll for a date.
            </p>
            <div className="field">
              <label>Engineer</label>
              <select
                value={approvalForm.user_id}
                onChange={(e) => setApprovalForm({ ...approvalForm, user_id: e.target.value })}
              >
                <option value="">Select engineer...</option>
                {engineerAvailability.map((e) => (
                  <option key={e.engineer_id} value={e.engineer_id}>
                    {e.engineer_id.slice(0, 8)}… ({e.availability_state}, {e.active_job_count} jobs)
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Date (YYYY-MM-DD)</label>
              <input
                type="date"
                value={approvalForm.date_str}
                onChange={(e) => setApprovalForm({ ...approvalForm, date_str: e.target.value })}
              />
            </div>
            <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => void approveTimesheet()}
                disabled={approvalBusy || !approvalForm.user_id || !approvalForm.date_str}
              >
                {approvalBusy ? "Approving…" : "Approve timesheet"}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => void exportPayroll()}
                disabled={payrollExportBusy || !approvalForm.date_str}
              >
                {payrollExportBusy ? "Exporting…" : "Export payroll"}
              </button>
              <button type="button" className="secondary" onClick={() => void refreshEngineerAvailability()}>
                Refresh engineers
              </button>
            </div>
            {payrollExport ? (
              <div className="card" style={{ marginTop: 12, padding: 12, background: "rgba(0,0,0,0.15)" }}>
                <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>Payroll export for {payrollExport.date_str}</h4>
                <div className="list">
                  {payrollExport.lines.length === 0 ? (
                    <div className="muted">No records for this date.</div>
                  ) : (
                    payrollExport.lines.map((line) => (
                      <div key={line.user_id} className="item">
                        <div className="item-title">
                          {line.user_id.slice(0, 8)}… • {Math.round(line.total_seconds / 60)} min • {line.amount.toFixed(2)}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : null}

            <div className="divider" />

            <h3>Recent Punch Events</h3>
            {punches.length === 0 ? (
              <div className="muted">No punches recorded.</div>
            ) : (
              <div className="list">
                {punches.map((p) => (
                  <div key={p.id} className="item">
                    <div className="item-title">
                      <span style={{ marginRight: 8 }}>{p.kind.toUpperCase()}</span>
                      <span className={p.valid ? "status-pill released" : "status-pill danger"}>
                        {p.valid ? "Valid" : "Invalid"}
                      </span>
                    </div>
                    <div className="item-sub">
                      Job {p.job_id.slice(0, 8)}... • {new Date(p.occurred_at).toLocaleString()}
                      {p.offline_device_id ? ` · offline id: ${p.offline_device_id}` : ""}
                    </div>
                    {p.distance_m != null ? (
                      <div className="item-body">
                        Distance from geofence center: {Math.round(p.distance_m)}m
                        {!p.valid ? " — likely outside radius or other validation failed." : ""}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        </div>
      ) : null}

      {activeTab === "compliance" ? (
        <div className="grid">
          <div className="card">
            <h3>Generate Certificate</h3>
            <div className="field">
              <label>Job</label>
              <select
                value={certificateJobId}
                onChange={(e) => setCertificateJobId(e.target.value)}
              >
                <option value="">All jobs (list only)</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.address} ({j.status})
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>certificate_type</label>
              <input value={certificateType} onChange={(e) => setCertificateType(e.target.value)} />
            </div>
            <button
              onClick={() => void generateCertificate()}
              disabled={certBusy || !certificateJobId.trim()}
            >
              {certBusy ? "Working..." : "Generate"}
            </button>
          </div>

          <div className="card">
            <div className="row">
              <h3>Certificates</h3>
              <button
                className="secondary"
                onClick={() => void refreshCertificates(certificateJobId)}
                disabled={certBusy}
              >
                Refresh
              </button>
            </div>
            {certBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {certificates.map((c) => (
                <div key={c.id} className="item">
                  <div className="row" style={{ alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div className="item-title">
                        {c.certificate_type} • {c.status}
                      </div>
                      <div className="item-sub">
                        job: {c.job_id.slice(0, 8)}… • engineer: {c.engineer_user_id ? c.engineer_user_id.slice(0, 8) : "—"}
                      </div>
                      <div className="item-body">
                        signed_by_engineer={String(c.signed_by_engineer)} · signed_by_client={String(c.signed_by_client)}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => void downloadCertificatePdf(c.id)}
                      disabled={certDownloadBusy === c.id}
                    >
                      {certDownloadBusy === c.id ? "Preparing…" : "Download PDF"}
                    </button>
                  </div>
                </div>
              ))}
              {certificates.length === 0 ? <div className="muted">No certificates yet.</div> : null}
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "invoices" ? (
        <div className="grid">
          <div className="card">
            <h3>Generate Invoice</h3>
            <div className="field">
              <label>Job</label>
              <select
                value={invoiceJobId}
                onChange={(e) => setInvoiceJobId(e.target.value)}
              >
                <option value="">All jobs (list only)</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.address} ({j.status})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => void generateInvoice()}
              disabled={invoiceBusy || !invoiceJobId.trim()}
            >
              {invoiceBusy ? "Working..." : "Generate"}
            </button>
          </div>

          <div className="card">
            <div className="row">
              <h3>Invoices</h3>
            <button
              className="secondary"
              onClick={() => void refreshInvoices(invoiceJobId)}
              disabled={invoiceBusy}
            >
              Refresh
            </button>
            </div>
            {invoiceBusy ? <div className="muted">Loading...</div> : null}
            <div className="list">
              {invoices.map((inv) => (
                <div key={inv.id} className="item">
                  <div className="item-title">
                    {inv.status} • {inv.grand_total} {inv.currency}
                  </div>
                  <div className="item-sub">
                    job: {inv.job_id.slice(0, 8)}…
                    {inv.finance_reviewed_at ? " · Finance reviewed" : ""}
                  </div>
                  {inv.status !== "paid" ? (
                    <div className="row" style={{ justifyContent: "flex-start", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                      {inv.status !== "held" ? (
                        <button
                          onClick={() => {
                            const note = window.prompt("Hold reason:", "Held from UI");
                            if (note !== null) void holdInvoice(inv.id, note.trim() || "Held from UI");
                          }}
                          disabled={invoiceBusy}
                          className="secondary"
                        >
                          Hold
                        </button>
                      ) : (
                        <button onClick={() => void releaseInvoiceHold(inv.id)} disabled={invoiceBusy} className="secondary">
                          Release hold
                        </button>
                      )}
                      {!inv.finance_reviewed_at ? (
                        <button
                          onClick={() => void markInvoiceFinanceReview(inv.id)}
                          disabled={invoiceBusy}
                          className="secondary"
                        >
                          Mark finance review
                        </button>
                      ) : (
                        <button
                          onClick={() => void clearInvoiceFinanceReview(inv.id)}
                          disabled={invoiceBusy}
                          className="secondary"
                        >
                          Clear finance review
                        </button>
                      )}
                      <button onClick={() => void payInvoice(inv.id)} disabled={invoiceBusy}>
                        Mark Paid
                      </button>
                    </div>
                  ) : (
                    <div className="item-body" style={{ marginTop: 8 }}>
                      paid_at={inv.paid_at ? new Date(inv.paid_at).toLocaleString() : "—"}
                    </div>
                  )}
                </div>
              ))}
              {invoices.length === 0 ? <div className="muted">No invoices yet.</div> : null}
            </div>
          </div>
        </div>
      ) : null}

      {activeTab === "commercial" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Commercial</strong> (§5.9): one scrollable hub with a <strong>Jump to section</strong> map at the top.
            Covers follow-ups, repricing, amendments, activations, comms, suppressions, finance export, diagnostics, and
            documents. Deep org/group admin is on the <strong>Access</strong> tab; customer-facing flows on{" "}
            <strong>Portal</strong>.
          </div>
          <CommercialHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "access" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Access</strong> (§5.9): internal groups + portal groups, members, permission grants, and entity
            scopes. Use the in-page links below to jump between internal and customer sections. Requires the org-access admin
            permission grant.
          </div>
          <OrgAccessHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "portal" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Portal</strong> (§5.10): customer-facing view — use <code>client@example.com</code> / <code>client</code> to
            see proposals, formal acceptance, e-sign status, activation PDFs &amp; timelines, jobs/ETA, invoices, message
            history, and downloads. The page includes a <strong>Jump to</strong> map for long scroll. Staff logins usually see
            an empty or partial dashboard here.
          </div>
          <ClientPortalHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "labour_ai" ? (
        <LabourAiToolsHub apiBase={apiBase} authHeaders={authHeaders} />
      ) : null}

      {activeTab === "sites" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Sites</strong>: internal site CRUD plus linked assets and open job summaries (dispatch/contracts context).
          </div>
          <SitesHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "assets" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Assets</strong>: asset CRUD with maintenance schedules.
          </div>
          <AssetsHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "inventory" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Inventory</strong>: stock items, locations, low-stock dashboard, and reservations.
          </div>
          <InventoryHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}
      
      {activeTab === "approvals" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Approvals</strong>: approve or reject pending requests.
          </div>
          <ApprovalsHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}
 
      {activeTab === "sla" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>SLA policies</strong>: response, attendance, and resolution targets.
          </div>
          <SlaPoliciesHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}
 
      {activeTab === "ppm" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>PPM schedules</strong>: planned preventative maintenance schedules and job generation.
          </div>
          <PpmSchedulesHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}
 
      {activeTab === "vehicles" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Vehicles</strong>: inspection attention, inspections, and defect workflow.
          </div>
          <VehiclesHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "competence" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Competence</strong>: qualifications management for engineers.
          </div>
          <CompetenceHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "analytics" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Analytics</strong>: ETL snapshot dashboard, margin summary, and cost variance.
          </div>
          <AnalyticsHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "ops" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Ops</strong>: recommendations scan, action workflows, and suppressions.
          </div>
          <OpsHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "settings" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Settings</strong>: enterprise configuration domains with audit history.
          </div>
          <SettingsHub apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "map" ? (
        <div style={{ padding: 18 }}>
          <LiveDispatchMap apiBase={apiBase} authHeaders={authHeaders} />
        </div>
      ) : null}

      {activeTab === "rollout" ? (
        <div>
          <div className="hint" style={{ padding: "12px 18px 0" }}>
            <strong>Rollout Ops</strong> (§5.9): pilot waves, alerts, and notification delivery retries. For invalid webhook
            signatures and dead-letter deliveries, use <strong>Commercial</strong> → Operational diagnostics.
          </div>
          <div className="grid">
          <div className="card">
            <h3>Rollout Operations</h3>
            <div className="field">
              <label>Wave Name</label>
              <input
                value={rolloutWaveForm.name}
                onChange={(e) => setRolloutWaveForm({ ...rolloutWaveForm, name: e.target.value })}
                placeholder="e.g. wave-engineers-1"
              />
            </div>
            <div className="field">
              <label>Target Role</label>
              <select
                value={rolloutWaveForm.target_role}
                onChange={(e) => setRolloutWaveForm({ ...rolloutWaveForm, target_role: e.target.value })}
              >
                <option value="Engineer">Engineer</option>
                <option value="Dispatcher">Dispatcher</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
            <div className="field">
              <label>Rollout %</label>
              <input
                type="number"
                value={rolloutWaveForm.rollout_percent}
                onChange={(e) => setRolloutWaveForm({ ...rolloutWaveForm, rollout_percent: Number(e.target.value) })}
              />
            </div>
            <div className="row">
              <button onClick={() => void createRolloutWave()} disabled={rolloutBusy || !rolloutWaveForm.name.trim()}>
                Create Wave
              </button>
              <button className="secondary" onClick={() => void runRolloutCycle()} disabled={rolloutBusy}>
                Run Cycle
              </button>
              <button className="secondary" onClick={() => void evaluateRolloutHealth()} disabled={rolloutBusy}>
                Evaluate Health
              </button>
            </div>
            <div className="row" style={{ marginTop: 10 }}>
              <button className="secondary" onClick={() => void processNotificationRetries()} disabled={rolloutBusy}>
                Process Retries
              </button>
              <button className="secondary" onClick={() => void refreshRolloutAll()} disabled={rolloutBusy}>
                {rolloutBusy ? "Refreshing..." : "Refresh"}
              </button>
            </div>
            {rolloutDigest ? (
              <div className="hint" style={{ marginTop: 10 }}>
                Alerts total: <b>{rolloutDigest.total_alerts}</b> • Open: <b>{rolloutDigest.open_alerts}</b> • Critical
                open: <b>{rolloutDigest.critical_open_alerts}</b>
              </div>
            ) : null}
          </div>

          <div className="card">
            <h3>Waves</h3>
            <div className="list">
              {rolloutWaves.map((w) => (
                <div key={w.id} className="item">
                  <div className="item-title">
                    {w.name} • {w.status} • {w.rollout_percent}%
                  </div>
                  <div className="item-sub">
                    role: {w.target_role || "all"} • created: {new Date(w.created_at).toLocaleString()}
                  </div>
                  {w.pause_reason ? <div className="item-body">pause_reason={w.pause_reason}</div> : null}
                </div>
              ))}
              {rolloutWaves.length === 0 ? <div className="muted">No waves yet.</div> : null}
            </div>

            <div className="divider" />
            <h3>Alerts</h3>
            <div className="list">
              {rolloutAlerts.slice(0, 12).map((a) => (
                <div key={a.id} className="item">
                  <div className="item-title">
                    {a.code} • {a.severity} • {a.status}
                  </div>
                  <div className="item-sub">dedup_count={a.dedup_count}</div>
                  <div className="item-body">{a.message}</div>
                  {a.status === "open" ? (
                    <div className="row" style={{ justifyContent: "flex-start", marginTop: 8 }}>
                      <button onClick={() => void acknowledgeAlert(a.id)} disabled={rolloutBusy}>
                        Acknowledge
                      </button>
                    </div>
                  ) : null}
                </div>
              ))}
              {rolloutAlerts.length === 0 ? <div className="muted">No alerts.</div> : null}
            </div>

            <div className="divider" />
            <h3>Notification Deliveries</h3>
            <div className="list">
              {rolloutDeliveries.slice(0, 12).map((d) => (
                <div key={d.id} className="item">
                  <div className="item-title">
                    {d.channel} • {d.status} • attempts={d.attempts}
                  </div>
                  <div className="item-sub">alert: {d.alert_id.slice(0, 8)}...</div>
                  {d.last_error ? <div className="item-body">{d.last_error}</div> : null}
                </div>
              ))}
              {rolloutDeliveries.length === 0 ? <div className="muted">No delivery records.</div> : null}
            </div>
          </div>
        </div>
        </div>
      ) : null}

        </main>
      </div>
    </div>
  );
}
