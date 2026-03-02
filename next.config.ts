import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  experimental: {
    turbopackFileSystemCacheForDev: true,
  },
  async redirects() {
    return [
      { source: "/services/air-conditioning", destination: "/services", permanent: true },
      { source: "/services/air-conditioning/:path*", destination: "/services", permanent: true },
      { source: "/services/heating", destination: "/services/domestic", permanent: true },
      { source: "/services/plumbing", destination: "/services", permanent: true },
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
