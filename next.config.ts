import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Smaller production image + correct tracing for Docker (see Dockerfile)
  output: "standalone",
  turbopack: {
    root: __dirname,
  },
  experimental: {
    turbopackFileSystemCacheForDev: true,
  },
  async redirects() {
    return [
      { source: "/services/commercial", destination: "/services", permanent: true },
      { source: "/services/domestic", destination: "/services", permanent: true },
      { source: "/services/mechanical/commercial", destination: "/services/mechanical", permanent: true },
      { source: "/services/mechanical/domestic", destination: "/services/mechanical", permanent: true },
      { source: "/services/plumbing/commercial", destination: "/services/plumbing", permanent: true },
      { source: "/services/plumbing/domestic", destination: "/services/plumbing", permanent: true },
      { source: "/services/electrical/commercial", destination: "/services/electrical", permanent: true },
      { source: "/services/electrical/domestic", destination: "/services/electrical", permanent: true },
      { source: "/services/gas/commercial", destination: "/services/gas", permanent: true },
      { source: "/services/gas/domestic", destination: "/services/gas", permanent: true },

      { source: "/services/air-conditioning", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/commercial-ac", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/ac-installation", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/ac-servicing", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/ac-repairs", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/ac-maintenance", destination: "/services/mechanical", permanent: true },
      { source: "/services/air-conditioning/:path*", destination: "/services/mechanical", permanent: true },

      { source: "/services/heating", destination: "/services/gas", permanent: true },
      { source: "/services/heating/boiler-installation", destination: "/services/gas", permanent: true },
      { source: "/services/heating/boiler-servicing", destination: "/services/gas", permanent: true },
      { source: "/services/heating/boiler-repair", destination: "/services/gas", permanent: true },
      { source: "/services/heating/central-heating", destination: "/services/mechanical", permanent: true },
      { source: "/services/heating/radiators", destination: "/services/mechanical", permanent: true },
      { source: "/services/heating/power-flushing", destination: "/services/mechanical", permanent: true },
      { source: "/services/heating/:path*", destination: "/services/gas", permanent: true },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "source.unsplash.com",
      },
    ],
  },
};

export default nextConfig;
