import type { MetadataRoute } from "next";

function getBaseUrl() {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "https://dps-heating.co.uk";
}

const PUBLIC_PATHS = [
  "/",
  "/about",
  "/contact",
  "/portfolio",
  "/service-areas",
  "/emergency",
  "/commercial-gas-engineer-london",
  "/commercial-heating-engineer-london",
  "/plant-room-maintenance-london",
  "/commercial-boiler-repair-london",
  "/emergency-heating-engineer-london",
  "/services",
  "/services/mechanical",
  "/services/plumbing",
  "/services/plumbing/general-plumbing",
  "/services/plumbing/plumbing-repairs",
  "/services/electrical",
  "/services/gas",
  "/tools",
] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = getBaseUrl();
  const now = new Date();

  return PUBLIC_PATHS.map((path) => ({
    url: `${baseUrl}${path}`,
    lastModified: now,
    changeFrequency: path === "/" ? "daily" : "weekly",
    priority: path === "/" ? 1 : path.startsWith("/services/") ? 0.8 : 0.7,
  }));
}
