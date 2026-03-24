import React, { useCallback, useEffect, useMemo, useState } from "react";

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type FetchState<T> = { data: T | null; error: string | null };

type StockItem = {
  id: string;
  sku: string;
  name: string;
  unit_cost: number;
  on_hand_quantity: number;
  reserved_quantity: number;
  reorder_point_quantity: number;
  unit_of_measure: string;
  created_at: string;
};

type StockLocation = {
  id: string;
  code: string;
  name: string;
  kind: string;
  engineer_user_id: string | null;
  created_at: string;
};

type StockReservation = {
  id: string;
  quote_id: string;
  job_id: string | null;
  sku: string;
  quantity: number;
  status: string;
  location_id: string | null;
  stock_item_id: string | null;
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
  // Some endpoints might return empty response; normalize.
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function InventoryHub({ apiBase, authHeaders }: Props) {
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);
  const [bannerErr, setBannerErr] = useState<string | null>(null);

  const [itemsBusy, setItemsBusy] = useState(false);
  const [items, setItems] = useState<StockItem[]>([]);
  const [itemsErr, setItemsErr] = useState<string | null>(null);

  const [locationsBusy, setLocationsBusy] = useState(false);
  const [locations, setLocations] = useState<StockLocation[]>([]);
  const [locationsErr, setLocationsErr] = useState<string | null>(null);

  const [lowStock, setLowStock] = useState<FetchState<Record<string, unknown>[]>>({ data: null, error: null });

  const [quoteId, setQuoteId] = useState("");
  const [jobId, setJobId] = useState("");
  const [reservationsBusy, setReservationsBusy] = useState(false);
  const [reservations, setReservations] = useState<StockReservation[]>([]);
  const [reservationsErr, setReservationsErr] = useState<string | null>(null);

  const [stockItemForm, setStockItemForm] = useState({
    sku: "",
    name: "",
    unit_cost: "0",
    on_hand_quantity: "0",
    reorder_point_quantity: "0",
    unit_of_measure: "ea",
  });

  const clearBanner = useCallback(() => setBanner(null), []);

  useEffect(() => {
    if (!banner) return;
    const t = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(t);
  }, [banner]);

  const loadItems = useCallback(async () => {
    setItemsBusy(true);
    setItemsErr(null);
    try {
      const rows = await fetchJson<StockItem[]>(`${apiBase}/inventory/items?limit=50&offset=0`, authHeaders);
      setItems(rows);
    } catch (e) {
      setItemsErr(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setItemsBusy(false);
    }
  }, [apiBase, authHeaders]);

  const loadLocations = useCallback(async () => {
    setLocationsBusy(true);
    setLocationsErr(null);
    try {
      const rows = await fetchJson<StockLocation[]>(`${apiBase}/inventory/locations`, authHeaders);
      setLocations(rows);
    } catch (e) {
      setLocationsErr(e instanceof Error ? e.message : String(e));
      setLocations([]);
    } finally {
      setLocationsBusy(false);
    }
  }, [apiBase, authHeaders]);

  const loadLowStock = useCallback(async () => {
    setLowStock({ data: null, error: null });
    try {
      const rows = await fetchJson<Record<string, unknown>[]>(`${apiBase}/inventory/dashboard/low-stock`, authHeaders);
      setLowStock({ data: rows, error: null });
    } catch (e) {
      setLowStock({ data: null, error: e instanceof Error ? e.message : String(e) });
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    // Best-effort initial loads.
    void loadItems();
    void loadLocations();
    void loadLowStock();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createStockItem = useCallback(async () => {
    setBusy(true);
    setBannerErr(null);
    try {
      const toNum = (v: string) => {
        const t = v.trim();
        const n = Number(t);
        if (!Number.isFinite(n)) return 0;
        return n;
      };
      const sku = stockItemForm.sku.trim();
      const name = stockItemForm.name.trim();
      if (!sku) throw new Error("SKU is required.");
      if (!name) throw new Error("Name is required.");

      await postJson<unknown>(`${apiBase}/inventory/items`, authHeaders, {
        sku,
        name,
        unit_cost: toNum(stockItemForm.unit_cost),
        on_hand_quantity: toNum(stockItemForm.on_hand_quantity),
        reorder_point_quantity: toNum(stockItemForm.reorder_point_quantity),
        unit_of_measure: stockItemForm.unit_of_measure.trim() || "ea",
      });
      setBanner("Stock item created.");
      setStockItemForm({
        sku: "",
        name: "",
        unit_cost: "0",
        on_hand_quantity: "0",
        reorder_point_quantity: "0",
        unit_of_measure: "ea",
      });
      await loadItems();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadItems, stockItemForm]);

  const loadReservations = useCallback(async () => {
    const q = quoteId.trim();
    if (!q) return;
    setReservationsBusy(true);
    setReservationsErr(null);
    try {
      const params = new URLSearchParams();
      params.set("quote_id", q);
      if (jobId.trim()) params.set("job_id", jobId.trim());
      const rows = await fetchJson<StockReservation[]>(`${apiBase}/inventory/reservations?${params.toString()}`, authHeaders);
      setReservations(rows);
    } catch (e) {
      setReservationsErr(e instanceof Error ? e.message : String(e));
      setReservations([]);
    } finally {
      setReservationsBusy(false);
    }
  }, [apiBase, authHeaders, jobId, quoteId]);

  const releaseReservation = useCallback(
    async (rid: string) => {
      setBusy(true);
      setBannerErr(null);
      try {
        await postJson<unknown>(`${apiBase}/inventory/reservations/${encodeURIComponent(rid)}/release`, authHeaders, {});
        setBanner("Reservation released.");
        await loadReservations();
      } catch (e) {
        setBannerErr(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [apiBase, authHeaders, loadReservations],
  );

  const suggestPurchaseRequests = useCallback(async () => {
    setBusy(true);
    setBannerErr(null);
    try {
      const out = await postJson<{ created_request_ids: string[] }>(`${apiBase}/inventory/purchase-requests/suggest-from-low-stock`, authHeaders, {});
      setBanner(out.created_request_ids.length ? `Created ${out.created_request_ids.length} purchase requests.` : "No low stock suggestions.");
      await loadLowStock();
    } catch (e) {
      setBannerErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders, loadLowStock]);

  const locationById = useMemo(() => {
    const m = new Map<string, StockLocation>();
    for (const l of locations) m.set(l.id, l);
    return m;
  }, [locations]);

  return (
    <div className="hub-grid">
      <div className="hub-intro">
        <h2>Inventory</h2>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Stock items, locations, low-stock dashboard, and reservations release (ledger-driven inventory movements).
        </p>
        <div className="row" style={{ marginTop: 10, flexWrap: "wrap", gap: 8 }}>
          <button type="button" className="secondary" onClick={() => void loadItems()} disabled={itemsBusy}>
            {itemsBusy ? "Loading…" : "Refresh items"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadLocations()} disabled={locationsBusy}>
            {locationsBusy ? "Loading…" : "Refresh locations"}
          </button>
          <button type="button" className="secondary" onClick={() => void loadLowStock()} disabled={busy}>
            {busy ? "Working…" : "Refresh low-stock"}
          </button>
          <button type="button" onClick={() => void suggestPurchaseRequests()} disabled={busy}>
            {busy ? "Suggesting…" : "Suggest purchase requests"}
          </button>
        </div>
        {banner ? (
          <div className="hub-sub" style={{ marginTop: 10, padding: "10px 16px", borderRadius: 8, border: "1px solid rgba(34,197,94,0.35)", background: "rgba(34,197,94,0.15)", color: "#86efac" }}>
            {banner}
            <button type="button" className="secondary" style={{ marginLeft: 12, padding: "2px 8px", fontSize: 12 }} onClick={clearBanner}>
              Dismiss
            </button>
          </div>
        ) : null}
        {bannerErr ? <div style={{ marginTop: 10, color: "#ffb4b4" }}>{bannerErr}</div> : null}
      </div>

      <nav className="hub-toc" aria-label="Inventory sections">
        <p className="hub-toc-title">Jump to section</p>
        <div className="hub-toc-links">
          <a href="#inv-items">Stock items</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#inv-locations">Locations</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#inv-low-stock">Low stock</a>
          <span className="hub-toc-sep" aria-hidden>
            ·
          </span>
          <a href="#inv-reservations">Reservations</a>
        </div>
      </nav>

      <div id="inv-items" className="card hub-panel hub-anchor">
        <h3>Stock items</h3>
        {itemsErr ? <div className="hub-err">{itemsErr}</div> : null}
        {itemsBusy ? <div className="muted" style={{ marginTop: 8 }}>Loading items…</div> : null}
        {!itemsBusy && items.length === 0 ? <div className="muted" style={{ marginTop: 8 }}>No items loaded.</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 12 }}>
          {items.slice(0, 25).map((it) => (
            <li key={it.id} style={{ marginBottom: 10 }}>
              <div>
                <strong>{it.sku}</strong> · {it.name}
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                on hand {it.on_hand_quantity} · reserved {it.reserved_quantity} · reorder at {it.reorder_point_quantity} ({it.unit_of_measure})
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                unit cost {it.unit_cost}
              </div>
            </li>
          ))}
        </ul>

        <div className="divider" />
        <h4 style={{ fontSize: 13, marginTop: 0 }}>Create stock item</h4>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>SKU</label>
            <input value={stockItemForm.sku} onChange={(e) => setStockItemForm((f) => ({ ...f, sku: e.target.value }))} placeholder="e.g. WIDGET-ABC" />
          </div>
          <div className="field" style={{ flex: 2, minWidth: 220 }}>
            <label>Name</label>
            <input value={stockItemForm.name} onChange={(e) => setStockItemForm((f) => ({ ...f, name: e.target.value }))} placeholder="Human-readable item name" />
          </div>
        </div>
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Unit cost</label>
            <input type="number" value={stockItemForm.unit_cost} onChange={(e) => setStockItemForm((f) => ({ ...f, unit_cost: e.target.value }))} step="any" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>On hand</label>
            <input type="number" value={stockItemForm.on_hand_quantity} onChange={(e) => setStockItemForm((f) => ({ ...f, on_hand_quantity: e.target.value }))} step="any" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 180 }}>
            <label>Reorder point</label>
            <input type="number" value={stockItemForm.reorder_point_quantity} onChange={(e) => setStockItemForm((f) => ({ ...f, reorder_point_quantity: e.target.value }))} step="any" />
          </div>
          <div className="field" style={{ flex: 0.7, minWidth: 140 }}>
            <label>UOM</label>
            <input value={stockItemForm.unit_of_measure} onChange={(e) => setStockItemForm((f) => ({ ...f, unit_of_measure: e.target.value }))} />
          </div>
        </div>
        <button type="button" style={{ marginTop: 8 }} onClick={() => void createStockItem()} disabled={busy || !stockItemForm.sku.trim() || !stockItemForm.name.trim()}>
          {busy ? "Creating…" : "Create"}
        </button>
      </div>

      <div id="inv-locations" className="card hub-panel hub-anchor">
        <h3>Locations</h3>
        {locationsErr ? <div className="hub-err">{locationsErr}</div> : null}
        {locationsBusy ? <div className="muted" style={{ marginTop: 8 }}>Loading locations…</div> : null}
        {!locationsBusy && locations.length === 0 ? <div className="muted" style={{ marginTop: 8 }}>No locations loaded.</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 12 }}>
          {locations.slice(0, 50).map((l) => (
            <li key={l.id} style={{ marginBottom: 10 }}>
              <div>
                <strong>{l.code}</strong> · {l.name}
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                kind {l.kind} {l.engineer_user_id ? `· van engineer ${l.engineer_user_id.slice(0, 8)}…` : ""}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div id="inv-low-stock" className="card hub-panel hub-anchor">
        <h3>Low stock dashboard</h3>
        {lowStock.error ? <div className="hub-err">{lowStock.error}</div> : null}
        {!lowStock.error && lowStock.data ? (
          <ul className="hub-list-compact" style={{ marginTop: 12 }}>
            {lowStock.data.slice(0, 25).map((row, i) => (
              <li key={String(row.id ?? i)} style={{ marginBottom: 10 }}>
                <div>
                  {String(row.sku ?? row.stock_item_id ?? row.id ?? "—")} · {String(row.name ?? row.stock_item_name ?? "—")}
                </div>
                <div className="hub-sub" style={{ marginTop: 2 }}>
                  {(() => {
                    const loc = row.location_id ? `Location ${String(row.location_id).slice(0, 8)}…` : "All locations";
                    const onHand = String(row.on_hand_quantity ?? row.on_hand ?? "—");
                    const reorderAt = String(row.reorder_point_quantity ?? row.reorder_point ?? "—");
                    return `${loc} · on hand ${onHand} · reorder at ${reorderAt}`;
                  })()}
                </div>
              </li>
            ))}
            {lowStock.data.length === 0 ? <li>No low stock rows in this snapshot.</li> : null}
          </ul>
        ) : null}
      </div>

      <div id="inv-reservations" className="card hub-panel hub-anchor">
        <h3>Reservations</h3>
        <p className="hub-sub" style={{ marginTop: 4 }}>
          Load reservations for a quote, then release one to return inventory to available stock.
        </p>
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <div className="field" style={{ flex: 2, minWidth: 220 }}>
            <label>quote_id (required)</label>
            <input value={quoteId} onChange={(e) => setQuoteId(e.target.value)} placeholder="Quote UUID" />
          </div>
          <div className="field" style={{ flex: 1, minWidth: 200 }}>
            <label>job_id (optional)</label>
            <input value={jobId} onChange={(e) => setJobId(e.target.value)} placeholder="Job UUID" />
          </div>
          <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
            <button type="button" className="secondary" onClick={() => void loadReservations()} disabled={reservationsBusy || !quoteId.trim()}>
              {reservationsBusy ? "Loading…" : "Load reservations"}
            </button>
          </div>
        </div>
        {reservationsErr ? <div className="hub-err" style={{ marginTop: 10 }}>{reservationsErr}</div> : null}
        {!reservationsBusy && reservations.length === 0 && quoteId.trim() ? <div className="muted" style={{ marginTop: 10 }}>No reservations found for this quote.</div> : null}
        <ul className="hub-list-compact" style={{ marginTop: 12 }}>
          {reservations.slice(0, 50).map((r) => (
            <li key={r.id} style={{ marginBottom: 10 }}>
              <div>
                <strong>{r.sku}</strong> · qty {r.quantity} · {r.status}
              </div>
              <div className="hub-sub" style={{ marginTop: 2 }}>
                {r.job_id ? `Job ${r.job_id.slice(0, 8)}…` : "No job"} ·{" "}
                {r.location_id ? `Location ${locationById.get(r.location_id)?.code ?? r.location_id.slice(0, 8) + "…"}`
                  : "No location"}
              </div>
              {r.id ? (
                <button
                  type="button"
                  className="secondary"
                  style={{ marginTop: 6 }}
                  disabled={busy}
                  onClick={() => void releaseReservation(r.id)}
                >
                  Release
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

