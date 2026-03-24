import React, { useCallback, useEffect, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

async function fetchJson<T>(url: string, headers: Record<string, string>): Promise<T> {
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(res.status === 403 ? "Not permitted (org access admin required)." : t.slice(0, 220) || res.statusText);
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

async function deleteReq(url: string, headers: Record<string, string>): Promise<void> {
  const res = await fetch(url, { method: "DELETE", headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t.slice(0, 220) || res.statusText);
  }
}

/** Mirrors backend `authorization_policy.PERMISSION_LABELS` for group grant pickers. */
const GROUP_PERMISSION_CATALOG: { key: string; label: string }[] = [
  { key: "can_hold_invoice", label: "Hold invoices" },
  { key: "can_release_invoice", label: "Release held invoices" },
  { key: "can_mark_finance_review", label: "Mark invoices for finance review" },
  { key: "can_create_purchase_order", label: "Create purchase orders / drafts" },
  { key: "can_approve_purchase_order", label: "Approve purchase orders" },
  { key: "can_trigger_customer_notification", label: "Trigger customer notifications" },
  { key: "can_decide_contract_review", label: "Decide contract / repricing review" },
  { key: "can_approve_repricing", label: "Approve repricing internally" },
  { key: "can_override_vehicle_block", label: "Override vehicle block gates" },
  { key: "can_override_equipment_block", label: "Override equipment block gates" },
  { key: "can_manage_labour_rules", label: "Manage labour rules / holiday calendars" },
  { key: "can_admin_permission_grants", label: "Administer per-user permission grants" },
  { key: "can_admin_org_access", label: "Manage org access groups and scopes" },
  { key: "can_run_ops_automation", label: "Run low-risk ops automation APIs" },
  { key: "can_view_contract_customer_communication", label: "View contract customer communications" },
  { key: "can_create_contract_customer_communication", label: "Create contract customer communications" },
  { key: "can_approve_contract_customer_communication_send", label: "Approve comms before send" },
  { key: "can_send_contract_customer_communication", label: "Send contract customer communications" },
  {
    key: "can_break_glass_communication_suppression",
    label: "Break-glass: send contract comms despite recipient suppression (audited)",
  },
  { key: "can_manage_customer_communication_preference", label: "Manage customer comm preferences" },
].sort((a, b) => a.label.localeCompare(b.label));

export function OrgAccessHub({ apiBase, authHeaders }: Props) {
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [intGroups, setIntGroups] = useState<Record<string, unknown>[] | null>(null);
  const [intBusy, setIntBusy] = useState(false);
  const [intSelGroupId, setIntSelGroupId] = useState("");
  const [intMembers, setIntMembers] = useState<Record<string, unknown>[] | null>(null);
  const [intScopes, setIntScopes] = useState<Record<string, unknown>[] | null>(null);
  const [newIntName, setNewIntName] = useState("");
  const [newIntCode, setNewIntCode] = useState("");
  const [newIntGtype, setNewIntGtype] = useState("operations");
  const [newIntParentId, setNewIntParentId] = useState("");
  const [newIntInheritParent, setNewIntInheritParent] = useState(true);
  const [addIntUserId, setAddIntUserId] = useState("");
  const [intScopeEntityType, setIntScopeEntityType] = useState("contract");
  const [intScopeEntityId, setIntScopeEntityId] = useState("");
  const [intScopeAccess, setIntScopeAccess] = useState<"view" | "manage" | "full_access">("view");
  const [intPatchName, setIntPatchName] = useState("");
  const [intPatchParentId, setIntPatchParentId] = useState("");
  const [intPatchInheritParent, setIntPatchInheritParent] = useState(true);
  const [intPatchActive, setIntPatchActive] = useState(true);
  const [intPermissions, setIntPermissions] = useState<Record<string, unknown>[] | null>(null);
  const [intScopeAccessDraft, setIntScopeAccessDraft] = useState<Record<string, "view" | "manage" | "full_access">>({});
  const [newGrantPermissionKey, setNewGrantPermissionKey] = useState(GROUP_PERMISSION_CATALOG[0]?.key ?? "can_hold_invoice");
  const [newGrantEffect, setNewGrantEffect] = useState<"allow" | "deny">("allow");
  const [permissionCatalog, setPermissionCatalog] = useState<
    { permission_key: string; label: string; default_roles: string[] }[] | null
  >(null);
  const [permissionCatalogBusy, setPermissionCatalogBusy] = useState(false);
  const [aiStatus, setAiStatus] = useState<{
    enabled: boolean;
    provider_name: string;
    model: string;
    base_url_configured: boolean;
    api_key_configured: boolean;
    ai_assisted_drafting_feature_flag: boolean;
    ai_assisted_drafting_ready: boolean;
  } | null>(null);
  const [aiStatusBusy, setAiStatusBusy] = useState(false);
  const [grantUserId, setGrantUserId] = useState("");
  const [grantUserBusy, setGrantUserBusy] = useState(false);
  const [grantUserDetail, setGrantUserDetail] = useState<{
    user_id: string;
    email: string;
    role_names: string[];
    role_permissions: string[];
    effective_permissions: string[];
    grants: {
      id: string;
      permission_key: string;
      effect: "allow" | "deny";
      active: boolean;
      notes: string | null;
      expires_at: string | null;
    }[];
  } | null>(null);
  const [newUserGrantPermission, setNewUserGrantPermission] = useState(GROUP_PERMISSION_CATALOG[0]?.key ?? "can_hold_invoice");
  const [newUserGrantEffect, setNewUserGrantEffect] = useState<"allow" | "deny">("allow");
  const [newUserGrantNotes, setNewUserGrantNotes] = useState("");

  const [crmCustomers, setCrmCustomers] = useState<Record<string, unknown>[] | null>(null);
  const [custId, setCustId] = useState("");
  const [portalGroups, setPortalGroups] = useState<Record<string, unknown>[] | null>(null);
  const [portalSelGroupId, setPortalSelGroupId] = useState("");
  const [portalMembers, setPortalMembers] = useState<Record<string, unknown>[] | null>(null);
  const [portalScopes, setPortalScopes] = useState<Record<string, unknown>[] | null>(null);
  const [newPortalName, setNewPortalName] = useState("");
  const [newPortalGtype, setNewPortalGtype] = useState("operations");
  const [newMemberContactScope, setNewMemberContactScope] = useState<"full" | "billing" | "operations">("full");
  const [addPortalEmail, setAddPortalEmail] = useState("");
  const [custScopeEntityType, setCustScopeEntityType] = useState<"contract" | "site" | "proposal" | "activation_confirmation">(
    "contract",
  );
  const [custScopeEntityId, setCustScopeEntityId] = useState("");
  const [custScopeAccess, setCustScopeAccess] = useState<"view" | "manage" | "full_access">("view");
  const [portalPatchName, setPortalPatchName] = useState("");
  const [portalPatchGtype, setPortalPatchGtype] = useState("operations");
  const [portalPatchActive, setPortalPatchActive] = useState(true);
  const [portalScopeAccessDraft, setPortalScopeAccessDraft] = useState<Record<string, "view" | "manage" | "full_access">>(
    {},
  );

  const flash = (msg: string, err?: string) => {
    setBanner(msg);
    setBannerErr(err ?? null);
    if (!err) window.setTimeout(() => setBanner(null), 5000);
  };

  const loadInternalGroups = useCallback(async () => {
    setIntBusy(true);
    setBannerErr(null);
    try {
      const rows = await fetchJson<Record<string, unknown>[]>(`${apiBase}/admin/access-groups`, authHeaders);
      setIntGroups(rows);
      setIntSelGroupId((prev) => {
        if (prev) return prev;
        if (rows.length > 0) return String(rows[0].id ?? "");
        return "";
      });
    } catch (e) {
      setIntGroups(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setIntBusy(false);
    }
  }, [apiBase, authHeaders]);

  const loadInternalGroupChildren = useCallback(
    async (gid: string) => {
      if (!gid) {
        setIntMembers(null);
        setIntScopes(null);
        setIntPermissions(null);
        return;
      }
      try {
        const [mem, scp, perm] = await Promise.all([
          fetchJson<Record<string, unknown>[]>(
            `${apiBase}/admin/access-groups/${encodeURIComponent(gid)}/members`,
            authHeaders,
          ),
          fetchJson<Record<string, unknown>[]>(
            `${apiBase}/admin/access-groups/${encodeURIComponent(gid)}/scopes`,
            authHeaders,
          ),
          fetchJson<Record<string, unknown>[]>(
            `${apiBase}/admin/access-groups/${encodeURIComponent(gid)}/permissions`,
            authHeaders,
          ),
        ]);
        setIntMembers(mem);
        setIntScopes(scp);
        setIntPermissions(perm);
      } catch (e) {
        setIntMembers(null);
        setIntScopes(null);
        setIntPermissions(null);
        setBannerErr(e instanceof Error ? e.message : String(e));
      }
    },
    [apiBase, authHeaders],
  );

  useEffect(() => {
    void loadInternalGroups();
  }, [loadInternalGroups]);

  useEffect(() => {
    void loadInternalGroupChildren(intSelGroupId);
  }, [intSelGroupId, loadInternalGroupChildren]);

  useEffect(() => {
    const g = intGroups?.find((x) => String(x.id) === intSelGroupId);
    if (g) {
      setIntPatchName(String(g.name ?? ""));
      setIntPatchActive(g.active !== false);
      setIntPatchParentId(g.parent_group_id ? String(g.parent_group_id) : "");
      setIntPatchInheritParent(g.inherit_parent_grants !== false);
    } else {
      setIntPatchName("");
      setIntPatchActive(true);
      setIntPatchParentId("");
      setIntPatchInheritParent(true);
    }
  }, [intSelGroupId, intGroups]);

  useEffect(() => {
    const d: Record<string, "view" | "manage" | "full_access"> = {};
    for (const s of intScopes ?? []) {
      const id = String(s.id);
      const ac = String(s.access_scope);
      if (ac === "view" || ac === "manage" || ac === "full_access") d[id] = ac;
      else d[id] = "view";
    }
    setIntScopeAccessDraft(d);
  }, [intScopes]);

  useEffect(() => {
    const g = portalGroups?.find((x) => String(x.id) === portalSelGroupId);
    if (g) {
      setPortalPatchName(String(g.name ?? ""));
      setPortalPatchGtype(String(g.group_type ?? "operations"));
      setPortalPatchActive(g.active !== false);
    } else {
      setPortalPatchName("");
      setPortalPatchGtype("operations");
      setPortalPatchActive(true);
    }
  }, [portalSelGroupId, portalGroups]);

  useEffect(() => {
    const d: Record<string, "view" | "manage" | "full_access"> = {};
    for (const s of portalScopes ?? []) {
      const id = String(s.id);
      const ac = String(s.access_scope);
      if (ac === "view" || ac === "manage" || ac === "full_access") d[id] = ac;
      else d[id] = "view";
    }
    setPortalScopeAccessDraft(d);
  }, [portalScopes]);

  const createInternalGroup = async () => {
    setBannerErr(null);
    try {
      await postJson(`${apiBase}/admin/access-groups`, authHeaders, {
        name: newIntName.trim(),
        code: newIntCode.trim(),
        group_type: newIntGtype,
        description: null,
        parent_group_id: newIntParentId.trim() || null,
        inherit_parent_grants: newIntInheritParent,
      });
      setNewIntName("");
      setNewIntCode("");
      setNewIntParentId("");
      flash("Internal access group created.");
      await loadInternalGroups();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const addInternalMember = async () => {
    if (!intSelGroupId || !addIntUserId.trim()) return;
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/access-groups/${encodeURIComponent(intSelGroupId)}/members`,
        authHeaders,
        { user_id: addIntUserId.trim(), notes: null },
      );
      setAddIntUserId("");
      flash("Internal member added.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const addInternalScope = async () => {
    if (!intSelGroupId || !intScopeEntityId.trim()) return;
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/access-groups/${encodeURIComponent(intSelGroupId)}/scopes`,
        authHeaders,
        {
          entity_type: intScopeEntityType.trim(),
          entity_id: intScopeEntityId.trim(),
          access_scope: intScopeAccess,
          notes: null,
        },
      );
      setIntScopeEntityId("");
      flash("Internal group scope added.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const loadCrmCustomers = async () => {
    try {
      const rows = await fetchJson<Record<string, unknown>[]>(`${apiBase}/crm/customers?limit=100`, authHeaders);
      setCrmCustomers(rows);
    } catch (e) {
      setCrmCustomers(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const loadPortalGroups = async (preferSelectId?: string) => {
    const id = custId.trim();
    if (!id) return;
    setBannerErr(null);
    try {
      const rows = await fetchJson<Record<string, unknown>[]>(
        `${apiBase}/admin/customers/${encodeURIComponent(id)}/access-groups`,
        authHeaders,
      );
      setPortalGroups(rows);
      const keep =
        preferSelectId && rows.some((r) => String(r.id) === preferSelectId) ? preferSelectId : "";
      setPortalSelGroupId(keep || (rows[0]?.id ? String(rows[0].id) : ""));
      if (!keep) {
        setPortalMembers(null);
        setPortalScopes(null);
      }
    } catch (e) {
      setPortalGroups(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const loadPortalGroupChildren = useCallback(
    async (gid: string) => {
      if (!gid) {
        setPortalMembers(null);
        setPortalScopes(null);
        return;
      }
      try {
        const [mem, scp] = await Promise.all([
          fetchJson<Record<string, unknown>[]>(
            `${apiBase}/admin/customer-access-groups/${encodeURIComponent(gid)}/members`,
            authHeaders,
          ),
          fetchJson<Record<string, unknown>[]>(
            `${apiBase}/admin/customer-access-groups/${encodeURIComponent(gid)}/scopes`,
            authHeaders,
          ),
        ]);
        setPortalMembers(mem);
        setPortalScopes(scp);
      } catch (e) {
        setPortalMembers(null);
        setPortalScopes(null);
        setBannerErr(e instanceof Error ? e.message : String(e));
      }
    },
    [apiBase, authHeaders],
  );

  useEffect(() => {
    void loadPortalGroupChildren(portalSelGroupId);
  }, [portalSelGroupId, loadPortalGroupChildren]);

  const createPortalGroup = async () => {
    const id = custId.trim();
    if (!id || !newPortalName.trim()) return;
    setBannerErr(null);
    try {
      await postJson(`${apiBase}/admin/customers/${encodeURIComponent(id)}/access-groups`, authHeaders, {
        name: newPortalName.trim(),
        group_type: newPortalGtype,
        notes: null,
      });
      setNewPortalName("");
      flash("Customer portal group created.");
      await loadPortalGroups();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const addPortalMember = async () => {
    if (!portalSelGroupId || !addPortalEmail.trim()) return;
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/customer-access-groups/${encodeURIComponent(portalSelGroupId)}/members`,
        authHeaders,
        {
          portal_login_email: addPortalEmail.trim().toLowerCase(),
          member_contact_scope: newMemberContactScope,
          notes: null,
        },
      );
      setAddPortalEmail("");
      flash("Portal member added.");
      await loadPortalGroupChildren(portalSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const addCustomerScope = async () => {
    if (!portalSelGroupId || !custScopeEntityId.trim()) return;
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/customer-access-groups/${encodeURIComponent(portalSelGroupId)}/scopes`,
        authHeaders,
        {
          entity_type: custScopeEntityType,
          entity_id: custScopeEntityId.trim(),
          access_scope: custScopeAccess,
          notes: null,
        },
      );
      setCustScopeEntityId("");
      flash("Customer portal scope added.");
      await loadPortalGroupChildren(portalSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchInternalGroup = async () => {
    if (!intSelGroupId) return;
    setBannerErr(null);
    try {
      const body: {
        name?: string;
        active: boolean;
        parent_group_id: string | null;
        inherit_parent_grants: boolean;
      } = {
        active: intPatchActive,
        parent_group_id: intPatchParentId.trim() || null,
        inherit_parent_grants: intPatchInheritParent,
      };
      if (intPatchName.trim()) body.name = intPatchName.trim();
      await patchJson(`${apiBase}/admin/access-groups/${encodeURIComponent(intSelGroupId)}`, authHeaders, body);
      flash("Internal group updated.");
      await loadInternalGroups();
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchInternalMembership = async (
    membershipId: string,
    patch: { active?: boolean; left_at_clear?: boolean },
  ) => {
    setBannerErr(null);
    try {
      await patchJson(
        `${apiBase}/admin/access-group-memberships/${encodeURIComponent(membershipId)}`,
        authHeaders,
        patch,
      );
      flash("Membership updated.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const addInternalPermissionGrant = async () => {
    if (!intSelGroupId || !newGrantPermissionKey) return;
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/access-groups/${encodeURIComponent(intSelGroupId)}/permissions`,
        authHeaders,
        { permission_key: newGrantPermissionKey, effect: newGrantEffect, notes: null },
      );
      flash("Group permission grant added.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const loadPermissionCatalog = async () => {
    setPermissionCatalogBusy(true);
    setBannerErr(null);
    try {
      const rows = await fetchJson<{ permission_key: string; label: string; default_roles: string[] }[]>(
        `${apiBase}/admin/permissions/catalog`,
        authHeaders,
      );
      setPermissionCatalog(rows);
      if (rows.length > 0) {
        setNewUserGrantPermission((prev) =>
          rows.some((r) => r.permission_key === prev) ? prev : rows[0].permission_key,
        );
      }
    } catch (e) {
      setPermissionCatalog(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setPermissionCatalogBusy(false);
    }
  };

  const loadAiStatus = async () => {
    setAiStatusBusy(true);
    setBannerErr(null);
    try {
      const row = await fetchJson<{
        enabled: boolean;
        provider_name: string;
        model: string;
        base_url_configured: boolean;
        api_key_configured: boolean;
        ai_assisted_drafting_feature_flag: boolean;
        ai_assisted_drafting_ready: boolean;
      }>(`${apiBase}/admin/ai/status`, authHeaders);
      setAiStatus(row);
    } catch (e) {
      setAiStatus(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setAiStatusBusy(false);
    }
  };

  const loadUserPermissionDetail = async () => {
    const uid = grantUserId.trim();
    if (!uid) return;
    setGrantUserBusy(true);
    setBannerErr(null);
    try {
      const row = await fetchJson<{
        user_id: string;
        email: string;
        role_names: string[];
        role_permissions: string[];
        effective_permissions: string[];
        grants: {
          id: string;
          permission_key: string;
          effect: "allow" | "deny";
          active: boolean;
          notes: string | null;
          expires_at: string | null;
        }[];
      }>(`${apiBase}/admin/permissions/users/${encodeURIComponent(uid)}`, authHeaders);
      setGrantUserDetail(row);
    } catch (e) {
      setGrantUserDetail(null);
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setGrantUserBusy(false);
    }
  };

  const createUserGrant = async () => {
    const uid = grantUserId.trim();
    if (!uid || !newUserGrantPermission) return;
    setGrantUserBusy(true);
    setBannerErr(null);
    try {
      await postJson(
        `${apiBase}/admin/permissions/users/${encodeURIComponent(uid)}/grants`,
        authHeaders,
        {
          permission_key: newUserGrantPermission,
          effect: newUserGrantEffect,
          notes: newUserGrantNotes.trim() || null,
        },
      );
      setNewUserGrantNotes("");
      flash("User grant added.");
      await loadUserPermissionDetail();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setGrantUserBusy(false);
    }
  };

  const patchUserGrant = async (grantId: string, patch: { active?: boolean; effect?: "allow" | "deny" }) => {
    setGrantUserBusy(true);
    setBannerErr(null);
    try {
      await patchJson(`${apiBase}/admin/permissions/grants/${encodeURIComponent(grantId)}`, authHeaders, patch);
      flash("User grant updated.");
      await loadUserPermissionDetail();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setGrantUserBusy(false);
    }
  };

  const deleteUserGrant = async (grantId: string) => {
    setGrantUserBusy(true);
    setBannerErr(null);
    try {
      await deleteReq(`${apiBase}/admin/permissions/grants/${encodeURIComponent(grantId)}`, authHeaders);
      flash("User grant removed.");
      await loadUserPermissionDetail();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setGrantUserBusy(false);
    }
  };

  const patchInternalGrant = async (grantId: string, patch: { active?: boolean; effect?: "allow" | "deny" }) => {
    setBannerErr(null);
    try {
      await patchJson(`${apiBase}/admin/access-group-permissions/${encodeURIComponent(grantId)}`, authHeaders, patch);
      flash("Grant updated.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const deleteInternalGrant = async (grantId: string) => {
    setBannerErr(null);
    try {
      await deleteReq(`${apiBase}/admin/access-group-permissions/${encodeURIComponent(grantId)}`, authHeaders);
      flash("Grant removed.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchInternalScopeRow = async (scopeId: string, patch: { access_scope?: "view" | "manage" | "full_access"; active?: boolean }) => {
    setBannerErr(null);
    try {
      await patchJson(`${apiBase}/admin/access-group-scopes/${encodeURIComponent(scopeId)}`, authHeaders, patch);
      flash("Scope updated.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const deleteInternalScope = async (scopeId: string) => {
    setBannerErr(null);
    try {
      await deleteReq(`${apiBase}/admin/access-group-scopes/${encodeURIComponent(scopeId)}`, authHeaders);
      flash("Scope removed.");
      await loadInternalGroupChildren(intSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchPortalGroup = async () => {
    if (!portalSelGroupId) return;
    setBannerErr(null);
    try {
      const body: { name?: string; group_type?: string; active: boolean } = { active: portalPatchActive };
      if (portalPatchName.trim()) body.name = portalPatchName.trim();
      if (portalPatchGtype.trim()) body.group_type = portalPatchGtype.trim();
      await patchJson(
        `${apiBase}/admin/customer-access-groups/${encodeURIComponent(portalSelGroupId)}`,
        authHeaders,
        body,
      );
      flash("Portal group updated.");
      const gid = portalSelGroupId;
      await loadPortalGroups(gid);
      await loadPortalGroupChildren(gid);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchPortalMemberFields = async (
    membershipId: string,
    patch: { active?: boolean; member_contact_scope?: "full" | "billing" | "operations" },
  ) => {
    setBannerErr(null);
    try {
      await patchJson(
        `${apiBase}/admin/customer-access-group-memberships/${encodeURIComponent(membershipId)}`,
        authHeaders,
        patch,
      );
      flash("Portal membership updated.");
      await loadPortalGroupChildren(portalSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const patchPortalScopeRow = async (
    scopeId: string,
    patch: { access_scope?: "view" | "manage" | "full_access"; active?: boolean },
  ) => {
    setBannerErr(null);
    try {
      await patchJson(
        `${apiBase}/admin/customer-access-group-scopes/${encodeURIComponent(scopeId)}`,
        authHeaders,
        patch,
      );
      flash("Portal scope updated.");
      await loadPortalGroupChildren(portalSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  const deletePortalScope = async (scopeId: string) => {
    setBannerErr(null);
    try {
      await deleteReq(`${apiBase}/admin/customer-access-group-scopes/${encodeURIComponent(scopeId)}`, authHeaders);
      flash("Portal scope removed.");
      await loadPortalGroupChildren(portalSelGroupId);
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Org & portal access</h2>
        <p>
          Dedicated workspace for org-access admins: internal access groups (members, permission grants, entity scopes) and
          customer portal groups (members + contract/site/proposal scopes). Internal groups support{" "}
          <strong>nested parents</strong>: members inherit permission grants and entity scopes from active ancestors when{" "}
          <em>inherit parent grants</em> is enabled. Portal groups support{" "}
          <strong>group types</strong> (e.g. operations vs billing) and per-member <strong>contact scopes</strong> for
          downstream comms targeting; visibility is still enforced by entity scopes. Link multi-entity customers via{" "}
          <code style={{ fontSize: 11 }}>PATCH /crm/customers/{"{id}"}</code> with <code style={{ fontSize: 11 }}>parent_customer_id</code>.
          Requires <code style={{ fontSize: 11 }}>CAN_ADMIN_ORG_ACCESS</code> grants.
        </p>
        {banner ? <div className="hub-sub" style={{ marginTop: 10, color: "#9dffb4" }}>{banner}</div> : null}
        {bannerErr ? <div className="hub-err" style={{ marginTop: 10 }}>{bannerErr}</div> : null}
      </div>

      <nav className="hub-toc" aria-label="Access hub sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#access-internal">Internal groups</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#access-permissions">Permission catalog</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#access-user-grants">Per-user grants</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#access-portal">Portal groups</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#access-ai-status">AI status</a>
        </div>
      </nav>

      <div id="access-internal" className="card hub-panel hub-anchor">
        <h3>Internal access groups</h3>
        <div className="row" style={{ gap: 8, marginTop: 8 }}>
          <button type="button" className="secondary" onClick={() => void loadInternalGroups()} disabled={intBusy}>
            {intBusy ? "Loading…" : "Refresh groups"}
          </button>
        </div>
        {intGroups && intGroups.length > 0 ? (
          <div style={{ marginTop: 10 }}>
            <label className="hub-sub">Active group</label>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 4, display: "block" }}
              value={intSelGroupId}
              onChange={(e) => setIntSelGroupId(e.target.value)}
            >
              {intGroups.map((g) => {
                const pid = g.parent_group_id ? String(g.parent_group_id).slice(0, 8) : "";
                return (
                  <option key={String(g.id)} value={String(g.id)}>
                    {String(g.name)} ({String(g.code)})
                    {pid ? ` · parent ${pid}…` : ""}
                  </option>
                );
              })}
            </select>
            <h4 style={{ fontSize: 13, marginTop: 14 }}>Update selected group</h4>
            <input
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={intPatchName}
              onChange={(e) => setIntPatchName(e.target.value)}
              placeholder="Display name"
            />
            <label className="hub-sub" style={{ display: "block", marginTop: 8 }}>
              Parent group (optional — for inheritance)
            </label>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={intPatchParentId}
              onChange={(e) => setIntPatchParentId(e.target.value)}
            >
              <option value="">— no parent —</option>
              {intGroups
                .filter((g) => String(g.id) !== intSelGroupId)
                .map((g) => (
                  <option key={String(g.id)} value={String(g.id)}>
                    {String(g.name)} ({String(g.code)})
                  </option>
                ))}
            </select>
            <label style={{ display: "block", marginTop: 8 }} className="hub-sub">
              <input
                type="checkbox"
                checked={intPatchInheritParent}
                onChange={(e) => setIntPatchInheritParent(e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Inherit parent grants &amp; scopes
            </label>
            <label style={{ display: "block", marginTop: 8 }} className="hub-sub">
              <input
                type="checkbox"
                checked={intPatchActive}
                onChange={(e) => setIntPatchActive(e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Group active
            </label>
            <button type="button" style={{ marginTop: 8 }} onClick={() => void patchInternalGroup()} disabled={!intSelGroupId}>
              Save group changes
            </button>
          </div>
        ) : (
          <div className="hub-sub" style={{ marginTop: 8 }}>No groups loaded or none exist.</div>
        )}

        <h4 style={{ fontSize: 13, marginTop: 16 }}>Create internal group</h4>
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
          value={newIntName}
          onChange={(e) => setNewIntName(e.target.value)}
          placeholder="Display name"
        />
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
          value={newIntCode}
          onChange={(e) => setNewIntCode(e.target.value)}
          placeholder="Unique code (e.g. OPS_NORTH)"
        />
        <select style={{ width: "100%", maxWidth: 480, marginTop: 6 }} value={newIntGtype} onChange={(e) => setNewIntGtype(e.target.value)}>
          <option value="operations">operations</option>
          <option value="commercial">commercial</option>
          <option value="finance">finance</option>
          <option value="field">field</option>
        </select>
        <label className="hub-sub" style={{ display: "block", marginTop: 8 }}>
          Parent group (optional)
        </label>
        <select
          style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
          value={newIntParentId}
          onChange={(e) => setNewIntParentId(e.target.value)}
        >
          <option value="">— no parent —</option>
          {(intGroups ?? []).map((g) => (
            <option key={String(g.id)} value={String(g.id)}>
              {String(g.name)} ({String(g.code)})
            </option>
          ))}
        </select>
        <label style={{ display: "block", marginTop: 8 }} className="hub-sub">
          <input
            type="checkbox"
            checked={newIntInheritParent}
            onChange={(e) => setNewIntInheritParent(e.target.checked)}
            style={{ marginRight: 8 }}
          />
          Inherit parent grants &amp; scopes
        </label>
        <button type="button" style={{ marginTop: 8 }} onClick={() => void createInternalGroup()} disabled={!newIntName.trim() || !newIntCode.trim()}>
          Create internal group
        </button>

        <h4 style={{ fontSize: 13, marginTop: 16 }}>Members ({intMembers?.length ?? 0})</h4>
        <ul className="hub-list-compact">
          {(intMembers ?? []).map((m) => {
            const mid = String(m.id ?? "");
            const uid = String(m.user_id ?? "");
            const active = Boolean(m.active);
            return (
              <li key={mid || uid} style={{ marginBottom: 8 }}>
                <div>
                  user <code style={{ fontSize: 11 }}>{uid || "—"}</code> · active {String(active)}
                </div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!mid || !active}
                    onClick={() => void patchInternalMembership(mid, { active: false })}
                  >
                    Deactivate
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!mid || active}
                    onClick={() => void patchInternalMembership(mid, { active: true })}
                  >
                    Activate
                  </button>
                  <button type="button" className="secondary" disabled={!mid} onClick={() => void patchInternalMembership(mid, { left_at_clear: true })}>
                    Clear left_at
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
          value={addIntUserId}
          onChange={(e) => setAddIntUserId(e.target.value)}
          placeholder="User UUID to add"
        />
        <button type="button" style={{ marginTop: 6 }} onClick={() => void addInternalMember()} disabled={!intSelGroupId || !addIntUserId.trim()}>
          Add internal member
        </button>

        <h4 style={{ fontSize: 13, marginTop: 16 }}>Group permission grants ({intPermissions?.length ?? 0})</h4>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Extra allow/deny keys applied to everyone in this group (in addition to role defaults).
        </p>
        <ul className="hub-list-compact">
          {(intPermissions ?? []).map((g) => {
            const gid = String(g.id ?? "");
            const pk = String(g.permission_key ?? "");
            const eff = String(g.effect ?? "");
            const gactive = g.active !== false;
            return (
              <li key={gid || pk} style={{ marginBottom: 8 }}>
                <div>
                  <code style={{ fontSize: 11 }}>{pk}</code> · {eff} · active {String(gactive)}
                </div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!gid || !gactive}
                    onClick={() => void patchInternalGrant(gid, { active: false })}
                  >
                    Deactivate grant
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!gid || gactive}
                    onClick={() => void patchInternalGrant(gid, { active: true })}
                  >
                    Activate grant
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!gid || eff === "allow"}
                    onClick={() => void patchInternalGrant(gid, { effect: "allow" })}
                  >
                    Set allow
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!gid || eff === "deny"}
                    onClick={() => void patchInternalGrant(gid, { effect: "deny" })}
                  >
                    Set deny
                  </button>
                  <button type="button" className="secondary" disabled={!gid} onClick={() => void deleteInternalGrant(gid)}>
                    Remove
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <select
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
          value={newGrantPermissionKey}
          onChange={(e) => setNewGrantPermissionKey(e.target.value)}
        >
          {GROUP_PERMISSION_CATALOG.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label} ({p.key})
            </option>
          ))}
        </select>
        <select style={{ width: "100%", maxWidth: 480, marginTop: 6 }} value={newGrantEffect} onChange={(e) => setNewGrantEffect(e.target.value as "allow" | "deny")}>
          <option value="allow">allow</option>
          <option value="deny">deny</option>
        </select>
        <button type="button" style={{ marginTop: 6 }} onClick={() => void addInternalPermissionGrant()} disabled={!intSelGroupId}>
          Add grant to selected group
        </button>

        <h4 style={{ fontSize: 13, marginTop: 16 }}>Entity scopes ({intScopes?.length ?? 0})</h4>
        <ul className="hub-list-compact">
          {(intScopes ?? []).map((s) => {
            const sid = String(s.id ?? "");
            const draft = intScopeAccessDraft[sid] ?? "view";
            const scActive = s.active !== false;
            return (
              <li key={sid} style={{ marginBottom: 10 }}>
                <div>
                  {String(s.entity_type)} <code style={{ fontSize: 11 }}>{String(s.entity_id ?? "")}</code> · active {String(scActive)}
                </div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4, alignItems: "center" }}>
                  <select
                    style={{ maxWidth: 200 }}
                    value={draft}
                    onChange={(e) =>
                      setIntScopeAccessDraft((d) => ({
                        ...d,
                        [sid]: e.target.value as "view" | "manage" | "full_access",
                      }))
                    }
                  >
                    <option value="view">view</option>
                    <option value="manage">manage</option>
                    <option value="full_access">full_access</option>
                  </select>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!sid}
                    onClick={() => void patchInternalScopeRow(sid, { access_scope: draft })}
                  >
                    Apply access level
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!sid || !scActive}
                    onClick={() => void patchInternalScopeRow(sid, { active: false })}
                  >
                    Deactivate scope
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={!sid || scActive}
                    onClick={() => void patchInternalScopeRow(sid, { active: true })}
                  >
                    Activate scope
                  </button>
                  <button type="button" className="secondary" disabled={!sid} onClick={() => void deleteInternalScope(sid)}>
                    Remove
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <select
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
          value={intScopeEntityType}
          onChange={(e) => setIntScopeEntityType(e.target.value)}
        >
          <option value="contract">contract</option>
          <option value="site">site</option>
          <option value="job">job</option>
          <option value="customer">customer</option>
        </select>
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
          value={intScopeEntityId}
          onChange={(e) => setIntScopeEntityId(e.target.value)}
          placeholder="Entity UUID"
        />
        <select style={{ width: "100%", maxWidth: 480, marginTop: 6 }} value={intScopeAccess} onChange={(e) => setIntScopeAccess(e.target.value as "view" | "manage" | "full_access")}>
          <option value="view">view</option>
          <option value="manage">manage</option>
          <option value="full_access">full_access</option>
        </select>
        <button type="button" style={{ marginTop: 6 }} onClick={() => void addInternalScope()} disabled={!intSelGroupId || !intScopeEntityId.trim()}>
          Add scope
        </button>
      </div>

      <div id="access-permissions" className="card hub-panel hub-anchor">
        <h3>Permission catalog</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Live catalog from <code style={{ fontSize: 11 }}>GET /admin/permissions/catalog</code> with default role baselines.
        </p>
        <button type="button" className="secondary" onClick={() => void loadPermissionCatalog()} disabled={permissionCatalogBusy}>
          {permissionCatalogBusy ? "Loading…" : "Load permission catalog"}
        </button>
        {permissionCatalog ? (
          <ul className="hub-list-compact" style={{ marginTop: 10 }}>
            {permissionCatalog.map((p) => (
              <li key={p.permission_key} style={{ marginBottom: 8 }}>
                <div>
                  <code style={{ fontSize: 11 }}>{p.permission_key}</code> — {p.label}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  Default roles: {p.default_roles.length ? p.default_roles.join(", ") : "none"}
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div id="access-user-grants" className="card hub-panel hub-anchor">
        <h3>Per-user grants</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Inspect effective permissions and manage user-level allow/deny overrides.
        </p>
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
          value={grantUserId}
          onChange={(e) => setGrantUserId(e.target.value)}
          placeholder="User UUID"
        />
        <button
          type="button"
          style={{ marginTop: 6 }}
          onClick={() => void loadUserPermissionDetail()}
          disabled={!grantUserId.trim() || grantUserBusy}
        >
          {grantUserBusy ? "Loading…" : "Load user permissions"}
        </button>
        {grantUserDetail ? (
          <>
            <div className="hub-sub" style={{ marginTop: 10 }}>
              {grantUserDetail.email} · roles: {grantUserDetail.role_names.join(", ") || "none"}
            </div>
            <div className="hub-sub" style={{ marginTop: 4 }}>
              Effective permissions: {grantUserDetail.effective_permissions.length}
            </div>
            <details style={{ marginTop: 8 }}>
              <summary className="hub-sub" style={{ cursor: "pointer" }}>
                Show effective permission keys
              </summary>
              <ul className="hub-list-compact" style={{ marginTop: 6 }}>
                {grantUserDetail.effective_permissions.map((p) => (
                  <li key={p}>
                    <code style={{ fontSize: 11 }}>{p}</code>
                  </li>
                ))}
              </ul>
            </details>
            <h4 style={{ fontSize: 13, marginTop: 14 }}>User grants ({grantUserDetail.grants.length})</h4>
            <ul className="hub-list-compact">
              {grantUserDetail.grants.map((g) => (
                <li key={g.id} style={{ marginBottom: 8 }}>
                  <div>
                    <code style={{ fontSize: 11 }}>{g.permission_key}</code> · {g.effect} · active {String(g.active)}
                  </div>
                  {g.notes ? <div className="hub-sub">{g.notes}</div> : null}
                  <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                    <button
                      type="button"
                      className="secondary"
                      disabled={grantUserBusy || g.effect === "allow"}
                      onClick={() => void patchUserGrant(g.id, { effect: "allow" })}
                    >
                      Set allow
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={grantUserBusy || g.effect === "deny"}
                      onClick={() => void patchUserGrant(g.id, { effect: "deny" })}
                    >
                      Set deny
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={grantUserBusy || !g.active}
                      onClick={() => void patchUserGrant(g.id, { active: false })}
                    >
                      Deactivate
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={grantUserBusy || g.active}
                      onClick={() => void patchUserGrant(g.id, { active: true })}
                    >
                      Activate
                    </button>
                    <button type="button" className="secondary" disabled={grantUserBusy} onClick={() => void deleteUserGrant(g.id)}>
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <h4 style={{ fontSize: 13, marginTop: 14 }}>Add user grant</h4>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={newUserGrantPermission}
              onChange={(e) => setNewUserGrantPermission(e.target.value)}
            >
              {(permissionCatalog ??
                GROUP_PERMISSION_CATALOG.map((x) => ({ permission_key: x.key, label: x.label, default_roles: [] }))).map((p) => (
                <option key={p.permission_key} value={p.permission_key}>
                  {p.label} ({p.permission_key})
                </option>
              ))}
            </select>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={newUserGrantEffect}
              onChange={(e) => setNewUserGrantEffect(e.target.value as "allow" | "deny")}
            >
              <option value="allow">allow</option>
              <option value="deny">deny</option>
            </select>
            <input
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={newUserGrantNotes}
              onChange={(e) => setNewUserGrantNotes(e.target.value)}
              placeholder="Notes (optional)"
            />
            <button
              type="button"
              style={{ marginTop: 6 }}
              onClick={() => void createUserGrant()}
              disabled={grantUserBusy || !grantUserId.trim()}
            >
              Add user grant
            </button>
          </>
        ) : null}
      </div>

      <div id="access-portal" className="card hub-panel hub-anchor">
        <h3>Customer portal access groups</h3>
        <button type="button" className="secondary" style={{ marginTop: 8 }} onClick={() => void loadCrmCustomers()}>
          Load CRM customers
        </button>
        {crmCustomers && crmCustomers.length > 0 ? (
          <select
            style={{ width: "100%", maxWidth: 480, marginTop: 8, display: "block" }}
            value={custId}
            onChange={(e) => setCustId(e.target.value)}
          >
            <option value="">— pick customer —</option>
            {crmCustomers.map((c) => {
              const pid = c.parent_customer_id ? String(c.parent_customer_id).slice(0, 8) : "";
              const label = String(c.name ?? c.email ?? c.id).slice(0, 36);
              return (
                <option key={String(c.id)} value={String(c.id)}>
                  {label}
                  {pid ? ` · parent ${pid}…` : ""}
                </option>
              );
            })}
          </select>
        ) : null}
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 8 }}
          value={custId}
          onChange={(e) => setCustId(e.target.value)}
          placeholder="Customer UUID"
        />
        <button type="button" style={{ marginTop: 6 }} onClick={() => void loadPortalGroups()} disabled={!custId.trim()}>
          Load portal groups
        </button>

        <h4 style={{ fontSize: 13, marginTop: 14 }}>Create portal group</h4>
        <input
          style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
          value={newPortalName}
          onChange={(e) => setNewPortalName(e.target.value)}
          placeholder="Group name"
        />
        <select style={{ width: "100%", maxWidth: 480, marginTop: 6 }} value={newPortalGtype} onChange={(e) => setNewPortalGtype(e.target.value)}>
          <option value="operations">operations (site / job visibility)</option>
          <option value="billing">billing (invoices / finance)</option>
          <option value="site_team">site_team (per-site portal cohorts)</option>
          <option value="read_only">read_only</option>
          <option value="general">general</option>
        </select>
        <p className="hub-sub" style={{ marginTop: 6, maxWidth: 520 }}>
          Use <strong>site</strong> entity scopes below to limit a site_team group to specific locations; combine with member
          contact scope for billing vs operations contacts.
        </p>
        <button type="button" style={{ marginTop: 6 }} onClick={() => void createPortalGroup()} disabled={!custId.trim() || !newPortalName.trim()}>
          Create portal group
        </button>

        {portalGroups && portalGroups.length > 0 ? (
          <>
            <h4 style={{ fontSize: 13, marginTop: 14 }}>Active portal group</h4>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={portalSelGroupId}
              onChange={(e) => setPortalSelGroupId(e.target.value)}
            >
              {portalGroups.map((g) => (
                <option key={String(g.id)} value={String(g.id)}>
                  {String(g.name ?? g.id)}
                </option>
              ))}
            </select>

            <h4 style={{ fontSize: 13, marginTop: 12 }}>Update portal group</h4>
            <input
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={portalPatchName}
              onChange={(e) => setPortalPatchName(e.target.value)}
              placeholder="Display name"
            />
            <label className="hub-sub" style={{ display: "block", marginTop: 8 }}>
              Group type
            </label>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={portalPatchGtype}
              onChange={(e) => setPortalPatchGtype(e.target.value)}
            >
              <option value="operations">operations</option>
              <option value="billing">billing</option>
              <option value="site_team">site_team</option>
              <option value="read_only">read_only</option>
              <option value="general">general</option>
            </select>
            <label style={{ display: "block", marginTop: 8 }} className="hub-sub">
              <input
                type="checkbox"
                checked={portalPatchActive}
                onChange={(e) => setPortalPatchActive(e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Portal group active
            </label>
            <button type="button" style={{ marginTop: 8 }} onClick={() => void patchPortalGroup()} disabled={!portalSelGroupId}>
              Save portal group
            </button>

            <h4 style={{ fontSize: 13, marginTop: 12 }}>Portal members ({portalMembers?.length ?? 0})</h4>
            <ul className="hub-list-compact">
              {(portalMembers ?? []).map((m) => {
                const mid = String(m.id ?? "");
                const em = String(m.portal_login_email ?? "");
                const active = Boolean(m.active);
                const sc = String(m.member_contact_scope ?? "full");
                return (
                  <li key={mid || em} style={{ marginBottom: 8 }}>
                    <div>
                      {em} · active {String(active)} · contact scope <strong>{sc}</strong>
                    </div>
                    <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4, alignItems: "center" }}>
                      <select
                        style={{ maxWidth: 200 }}
                        value={sc === "billing" || sc === "operations" || sc === "full" ? sc : "full"}
                        onChange={(e) =>
                          void patchPortalMemberFields(mid, {
                            member_contact_scope: e.target.value as "full" | "billing" | "operations",
                          })
                        }
                      >
                        <option value="full">full</option>
                        <option value="billing">billing</option>
                        <option value="operations">operations</option>
                      </select>
                      <button
                        type="button"
                        className="secondary"
                        disabled={!mid || !active}
                        onClick={() => void patchPortalMemberFields(mid, { active: false })}
                      >
                        Deactivate
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={!mid || active}
                        onClick={() => void patchPortalMemberFields(mid, { active: true })}
                      >
                        Activate
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
            <input
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={addPortalEmail}
              onChange={(e) => setAddPortalEmail(e.target.value)}
              placeholder="portal_login_email"
            />
            <label className="hub-sub" style={{ display: "block", marginTop: 6 }}>
              New member contact scope
            </label>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 4 }}
              value={newMemberContactScope}
              onChange={(e) => setNewMemberContactScope(e.target.value as "full" | "billing" | "operations")}
            >
              <option value="full">full (all scoped entities)</option>
              <option value="billing">billing</option>
              <option value="operations">operations</option>
            </select>
            <button type="button" style={{ marginTop: 6 }} onClick={() => void addPortalMember()} disabled={!portalSelGroupId || !addPortalEmail.trim()}>
              Add portal member
            </button>

            <h4 style={{ fontSize: 13, marginTop: 14 }}>Portal scopes ({portalScopes?.length ?? 0})</h4>
            <ul className="hub-list-compact">
              {(portalScopes ?? []).map((s) => {
                const sid = String(s.id ?? "");
                const draft = portalScopeAccessDraft[sid] ?? "view";
                const scActive = s.active !== false;
                return (
                  <li key={sid} style={{ marginBottom: 10 }}>
                    <div>
                      {String(s.entity_type)} <code style={{ fontSize: 11 }}>{String(s.entity_id ?? "")}</code> · active{" "}
                      {String(scActive)}
                    </div>
                    <div className="row" style={{ flexWrap: "wrap", gap: 6, marginTop: 4, alignItems: "center" }}>
                      <select
                        style={{ maxWidth: 200 }}
                        value={draft}
                        onChange={(e) =>
                          setPortalScopeAccessDraft((d) => ({
                            ...d,
                            [sid]: e.target.value as "view" | "manage" | "full_access",
                          }))
                        }
                      >
                        <option value="view">view</option>
                        <option value="manage">manage</option>
                        <option value="full_access">full_access</option>
                      </select>
                      <button
                        type="button"
                        className="secondary"
                        disabled={!sid}
                        onClick={() => void patchPortalScopeRow(sid, { access_scope: draft })}
                      >
                        Apply access level
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={!sid || !scActive}
                        onClick={() => void patchPortalScopeRow(sid, { active: false })}
                      >
                        Deactivate
                      </button>
                      <button
                        type="button"
                        className="secondary"
                        disabled={!sid || scActive}
                        onClick={() => void patchPortalScopeRow(sid, { active: true })}
                      >
                        Activate
                      </button>
                      <button type="button" className="secondary" disabled={!sid} onClick={() => void deletePortalScope(sid)}>
                        Remove
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
            <select
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={custScopeEntityType}
              onChange={(e) => setCustScopeEntityType(e.target.value as typeof custScopeEntityType)}
            >
              <option value="contract">contract</option>
              <option value="site">site</option>
              <option value="proposal">proposal</option>
              <option value="activation_confirmation">activation_confirmation</option>
            </select>
            <input
              style={{ width: "100%", maxWidth: 480, marginTop: 6 }}
              value={custScopeEntityId}
              onChange={(e) => setCustScopeEntityId(e.target.value)}
              placeholder="Entity UUID"
            />
            <select style={{ width: "100%", maxWidth: 480, marginTop: 6 }} value={custScopeAccess} onChange={(e) => setCustScopeAccess(e.target.value as typeof custScopeAccess)}>
              <option value="view">view</option>
              <option value="manage">manage</option>
              <option value="full_access">full_access</option>
            </select>
            <button type="button" style={{ marginTop: 6 }} onClick={() => void addCustomerScope()} disabled={!portalSelGroupId || !custScopeEntityId.trim()}>
              Add portal scope
            </button>
          </>
        ) : portalGroups && portalGroups.length === 0 ? (
          <div className="hub-sub" style={{ marginTop: 10 }}>No portal groups for this customer.</div>
        ) : null}
      </div>

      <div id="access-ai-status" className="card hub-panel hub-anchor">
        <h3>AI provider status</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Safe config visibility from <code style={{ fontSize: 11 }}>GET /admin/ai/status</code> (no secrets exposed).
        </p>
        <button type="button" className="secondary" onClick={() => void loadAiStatus()} disabled={aiStatusBusy}>
          {aiStatusBusy ? "Loading…" : "Load AI status"}
        </button>
        {aiStatus ? (
          <ul className="hub-list-compact" style={{ marginTop: 10 }}>
            <li>Enabled: {String(aiStatus.enabled)}</li>
            <li>Provider: {aiStatus.provider_name || "—"}</li>
            <li>Model: {aiStatus.model || "—"}</li>
            <li>Base URL configured: {String(aiStatus.base_url_configured)}</li>
            <li>API key configured: {String(aiStatus.api_key_configured)}</li>
            <li>AI drafting feature flag: {String(aiStatus.ai_assisted_drafting_feature_flag)}</li>
            <li>AI drafting ready: {String(aiStatus.ai_assisted_drafting_ready)}</li>
          </ul>
        ) : null}
      </div>
    </div>
  );
}
