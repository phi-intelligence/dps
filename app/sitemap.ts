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
  "/services",
  "/services/commercial",
  "/services/domestic",
  "/services/mechanical",
  "/services/mechanical/commercial",
  "/services/mechanical/domestic",
  "/services/plumbing",
  "/services/plumbing/commercial",
  "/services/plumbing/domestic",
  "/services/plumbing/general-plumbing",
  "/services/plumbing/plumbing-repairs",
  "/services/electrical",
  "/services/electrical/commercial",
  "/services/electrical/domestic",
  "/services/gas",
  "/services/gas/commercial",
  "/services/gas/domestic",
  "/services/heating",
  "/services/heating/boiler-installation",
  "/services/heating/boiler-repair",
  "/services/heating/boiler-servicing",
  "/services/heating/central-heating",
  "/services/heating/power-flushing",
  "/services/heating/radiators",
  "/services/air-conditioning",
  "/services/air-conditioning/ac-installation",
  "/services/air-conditioning/ac-maintenance",
  "/services/air-conditioning/ac-repairs",
  "/services/air-conditioning/ac-servicing",
  "/services/air-conditioning/commercial-ac",
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
