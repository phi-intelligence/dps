import React, { useCallback, useEffect, useMemo, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

type LiveMapEngineer = {
  engineer_id: string;
  latitude: number | null;
  longitude: number | null;
  operational_source: string | null;
  freshness_status: string | null;
  availability_state: string;
  stale: boolean;
};

type LiveMapVehicle = {
  vehicle_id: string;
  latitude: number;
  longitude: number;
  assigned_engineer_id: string | null;
  freshness_status: string;
  readiness_status?: string | null;
};

type LiveMapJob = {
  job_id: string;
  status: string;
  assigned_engineer_id: string | null;
  site_latitude: number | null;
  site_longitude: number | null;
};

type LiveMapData = {
  engineers: LiveMapEngineer[];
  vehicles: LiveMapVehicle[];
  jobs: LiveMapJob[];
};

type Props = {
  apiBase: string;
  authHeaders: Record<string, string>;
};

type LivePoint = {
  id: string;
  kind: "engineer" | "vehicle" | "job";
  latitude: number;
  longitude: number;
  title: string;
  subtitle: string;
  engineerId?: string;
};

const londonCenter: [number, number] = [51.5074, -0.1278];

const defaultMarkerIcon = L.icon({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function MapCenterController({
  center,
}: {
  center: [number, number] | null;
}) {
  const map = useMap();
  useEffect(() => {
    if (!center) return;
    map.setView(center, Math.max(map.getZoom(), 13), { animate: true });
  }, [center, map]);
  return null;
}

function mapLink(lat: number, lng: number): string {
  return `https://www.openstreetmap.org/?mlat=${encodeURIComponent(String(lat))}&mlon=${encodeURIComponent(String(lng))}#map=13/${encodeURIComponent(String(lat))}/${encodeURIComponent(String(lng))}`;
}

export function LiveDispatchMap({ apiBase, authHeaders }: Props) {
  const [data, setData] = useState<LiveMapData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEngineerId, setSelectedEngineerId] = useState("");
  const [autoFollowEngineer, setAutoFollowEngineer] = useState(true);
  const [requestedCenter, setRequestedCenter] = useState<[number, number] | null>(null);
  const [geoBusy, setGeoBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/dispatch/live-map`, { headers: authHeaders });
      if (res.status === 401) return;
      if (!res.ok) {
        setError(`Failed to load map (${res.status})`);
        return;
      }
      const json = (await res.json()) as LiveMapData;
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [apiBase, authHeaders]);

  useEffect(() => {
    void load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  const points = useMemo<LivePoint[]>(() => {
    if (!data) return [];
    const out: LivePoint[] = [];
    for (const e of data.engineers) {
      if (e.latitude == null || e.longitude == null) continue;
      out.push({
        id: `eng-${e.engineer_id}`,
        kind: "engineer",
        latitude: e.latitude,
        longitude: e.longitude,
        title: `Engineer ${e.engineer_id.slice(0, 8)}…`,
        subtitle: `${e.availability_state}${e.stale ? " · stale" : ""} · ${e.freshness_status ?? "unknown freshness"}`,
        engineerId: e.engineer_id,
      });
    }
    for (const v of data.vehicles) {
      out.push({
        id: `veh-${v.vehicle_id}`,
        kind: "vehicle",
        latitude: v.latitude,
        longitude: v.longitude,
        title: `Vehicle ${v.vehicle_id.slice(0, 8)}…`,
        subtitle: `${v.freshness_status}${v.readiness_status ? ` · ${v.readiness_status}` : ""}`,
      });
    }
    for (const j of data.jobs) {
      if (j.site_latitude == null || j.site_longitude == null) continue;
      out.push({
        id: `job-${j.job_id}`,
        kind: "job",
        latitude: j.site_latitude,
        longitude: j.site_longitude,
        title: `Job ${j.job_id.slice(0, 8)}…`,
        subtitle: `${j.status}${j.assigned_engineer_id ? ` · ${j.assigned_engineer_id.slice(0, 8)}…` : ""}`,
      });
    }
    return out;
  }, [data]);

  useEffect(() => {
    if (!selectedEngineerId || !autoFollowEngineer) return;
    const selectedPoint = points.find((p) => p.kind === "engineer" && p.engineerId === selectedEngineerId);
    if (!selectedPoint) return;
    setRequestedCenter([selectedPoint.latitude, selectedPoint.longitude]);
  }, [autoFollowEngineer, points, selectedEngineerId]);

  const useBrowserLocation = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setError("Browser geolocation is not available.");
      return;
    }
    setGeoBusy(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setRequestedCenter([pos.coords.latitude, pos.coords.longitude]);
        setGeoBusy(false);
      },
      (geoErr) => {
        setError(`Location error: ${geoErr.message}`);
        setGeoBusy(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 10000 },
    );
  }, []);

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div className="row">
        <h3>Live dispatch map</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="secondary" onClick={useBrowserLocation} disabled={geoBusy}>
            {geoBusy ? "Locating…" : "Use my location"}
          </button>
          <button type="button" className="secondary" onClick={() => void load()} disabled={busy}>
            {busy ? "Loading…" : "Refresh"}
          </button>
        </div>
      </div>
      <p className="hint" style={{ marginBottom: 12 }}>
        Live dispatch map with in-page markers. Auto-refreshes every 10s.
      </p>
      {error ? <div className="error">{error}</div> : null}
      {!data && !busy ? (
        <div className="muted">No map data yet. Ensure engineers have telemetry and jobs have site coordinates.</div>
      ) : (
        <div style={{ border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: 10 }}>
          <div className="row" style={{ justifyContent: "flex-start", gap: 10, marginBottom: 8 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              Follow engineer:
              <select value={selectedEngineerId} onChange={(e) => setSelectedEngineerId(e.target.value)}>
                <option value="">None</option>
                {(data?.engineers ?? []).map((e) => (
                  <option key={e.engineer_id} value={e.engineer_id}>
                    {e.engineer_id.slice(0, 8)}… ({e.availability_state})
                  </option>
                ))}
              </select>
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={autoFollowEngineer}
                onChange={(e) => setAutoFollowEngineer(e.target.checked)}
              />
              Auto-follow
            </label>
          </div>
          <div className="row" style={{ justifyContent: "flex-start", gap: 8, marginBottom: 8 }}>
            <span className="badge" style={{ background: "rgba(59,130,246,.2)" }}>
              Engineers: {data?.engineers.length ?? 0}
            </span>
            <span className="badge" style={{ background: "rgba(34,197,94,.2)" }}>
              Vehicles: {data?.vehicles.length ?? 0}
            </span>
            <span className="badge" style={{ background: "rgba(245,158,11,.2)" }}>
              Jobs: {data?.jobs.length ?? 0}
            </span>
          </div>
          <div style={{ height: 360, borderRadius: 10, overflow: "hidden", marginBottom: 10 }}>
            <MapContainer center={requestedCenter ?? londonCenter} zoom={12} style={{ height: "100%", width: "100%" }}>
              <MapCenterController center={requestedCenter} />
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {points.map((p) => (
                <Marker key={p.id} position={[p.latitude, p.longitude]} icon={defaultMarkerIcon}>
                  <Popup>
                    <strong>{p.title}</strong>
                    <br />
                    {p.subtitle}
                    <br />
                    {p.latitude.toFixed(5)}, {p.longitude.toFixed(5)}
                    <br />
                    <a href={mapLink(p.latitude, p.longitude)} target="_blank" rel="noreferrer">
                      Open in OSM
                    </a>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
          <div className="list" style={{ maxHeight: 220, overflow: "auto" }}>
            {points.map((p) => (
              <button
                key={p.id}
                type="button"
                className="item"
                style={{ width: "100%", textAlign: "left", background: "transparent", cursor: "pointer" }}
                onClick={() => setRequestedCenter([p.latitude, p.longitude])}
              >
                <div className="item-title">{p.title}</div>
                <div className="item-sub">{p.subtitle}</div>
                <div className="item-sub">
                  {p.latitude.toFixed(5)}, {p.longitude.toFixed(5)}
                </div>
              </button>
            ))}
            {points.length === 0 ? <div className="muted">No live coordinates available.</div> : null}
          </div>
        </div>
      )}
    </div>
  );
}
