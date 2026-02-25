"use client";

import { useEffect, useRef } from "react";
import { MapContainer, Marker, Popup, useMap, ZoomControl } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useTheme } from "@/lib/theme-provider";
import { SERVICE_AREAS } from "@/lib/constants";

/* ── Tile URLs ─────────────────────────────────────────── */
// Both modes use Voyager — dark mode inverts them via CSS filter
const TILES = {
  light: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  dark:  "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
};

/* ── Service area coordinates (London, Kent, Essex, Surrey) ─────────────────────────── */
const AREA_COORDS: Record<string, [number, number]> = {
  London: [51.5074, -0.1278],
  Kent:   [51.2704, 0.5227],   // Maidstone area
  Essex:  [51.7356, 0.4690],   // Chelmsford area
  Surrey: [51.2362, -0.5704], // Guildford area
};

/* ── Custom pulsing DivIcon ───────────────────────────── */
function createMarkerIcon(isMain = false, isDark = false) {
  const dot  = isMain ? 14 : 10;
  const ring = isMain ? 26 : 20;
  // White border in dark mode, dark border in light so pin pops on pale tiles
  const border = isDark
    ? "2px solid rgba(255,255,255,0.85)"
    : "2px solid rgba(255,255,255,1)";

  return L.divIcon({
    className: "",
    iconSize:    [ring, ring],
    iconAnchor:  [ring / 2, ring / 2],
    popupAnchor: [0, -(ring / 2 + 6)],
    html: `
      <div style="
        position:relative;
        width:${ring}px;height:${ring}px;
        display:flex;align-items:center;justify-content:center;
      ">
        <div style="
          position:absolute;
          width:${ring}px;height:${ring}px;
          border-radius:50%;
          background:rgba(212,175,55,0.22);
          animation:dps-ping ${isMain ? "1.6s" : "2.2s"} ease-out infinite;
        "></div>
        <div style="
          width:${dot}px;height:${dot}px;
          border-radius:50%;
          background:#d4af37;
          border:${border};
          box-shadow:0 0 ${isMain ? "12px" : "8px"} rgba(212,175,55,0.7);
          position:relative;z-index:1;
          flex-shrink:0;
        "></div>
      </div>
    `,
  });
}

/* ── Swap tiles + apply CSS filter when theme changes ─── */
function ThemeAwareTiles({ theme }: { theme: string }) {
  const map = useMap();
  const layerRef = useRef<L.TileLayer | null>(null);

  useEffect(() => {
    const isDark = theme === "dark";

    if (layerRef.current) map.removeLayer(layerRef.current);

    layerRef.current = L.tileLayer(isDark ? TILES.dark : TILES.light, {
      attribution: "© OpenStreetMap contributors © CARTO",
      maxZoom: 19,
    }).addTo(map);

    // Apply CSS filter to the tile pane to match brand palette
    const tilePaneEl = map.getPanes().tilePane as HTMLElement | undefined;
    if (tilePaneEl) {
      tilePaneEl.style.filter = isDark
        // Dark: invert + restore hues (180°) → proper dark map from Voyager tiles.
        // brightness(0.82) dims slightly; saturate(0.6) mutes cartographic colours
        // to match the brand's desaturated dark palette; contrast(0.88) softens edges.
        ? "invert(1) hue-rotate(180deg) brightness(0.82) saturate(0.6) contrast(0.88)"
        // Light: strip vivid cartographic greens/tans → clean neutral palette
        : "saturate(0.55) brightness(1.04) contrast(0.93)";
    }

    return () => {
      if (layerRef.current) map.removeLayer(layerRef.current);
    };
  }, [theme, map]);

  return null;
}

const mappedAreas = (SERVICE_AREAS as string[])
  .map((name) => ({ name, coords: AREA_COORDS[name] ?? null }))
  .filter((a): a is { name: string; coords: [number, number] } => a.coords !== null);

/* ── Map component ────────────────────────────────────── */
export default function ServiceAreasMap() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <MapContainer
      center={[51.45, 0]}
      zoom={8}
      scrollWheelZoom={false}
      className="w-full h-full dps-map"
      zoomControl={false}
      /* Background matches section bg so tile edges don't flash white */
      style={{ background: isDark ? "#0e0f11" : "#f1f0ee" }}
    >
      <ThemeAwareTiles theme={theme} />
      <ZoomControl position="bottomright" />

      {mappedAreas.map((area) => (
        <Marker
          key={area.name}
          position={area.coords}
          icon={createMarkerIcon(area.name === "London", isDark)}
        >
          <Popup className="dps-popup">
            <div className="dps-popup-inner">
              <p className="dps-popup-title">{area.name}</p>
              <p className="dps-popup-sub">Service area covered</p>
              <a href="/contact" className="dps-popup-link">
                Get a Quote →
              </a>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
