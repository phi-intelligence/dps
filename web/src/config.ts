/**
 * API origin for browser → backend requests.
 *
 * Resolution order:
 * 1. `window.__PHI_DPS_CONFIG__.apiBase` from `/config.js` (deploy-time override, no rebuild).
 * 2. `REACT_APP_PHI_DPS_API_BASE` at **build** time (Create React App).
 * 3. Dev default `http://127.0.0.1:8000`.
 *
 * Must be an absolute URL (https://api.example.com) or same-origin path prefix (/api) if you terminate API behind the same host.
 */
declare global {
  interface Window {
    __PHI_DPS_CONFIG__?: { apiBase?: string };
  }
}

function stripTrailingSlash(s: string): string {
  return s.replace(/\/+$/, "");
}

function runtimeApiBase(): string | undefined {
  if (typeof window === "undefined") return undefined;
  const raw = window.__PHI_DPS_CONFIG__?.apiBase;
  if (raw == null || typeof raw !== "string") return undefined;
  const t = raw.trim();
  return t ? stripTrailingSlash(t) : undefined;
}

export function getPhiDpsApiBase(): string {
  const rt = runtimeApiBase();
  if (rt) return rt;
  const env = (process.env.REACT_APP_PHI_DPS_API_BASE || "").trim();
  if (env) return stripTrailingSlash(env);
  return "http://127.0.0.1:8000";
}
