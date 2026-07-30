import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Empty Turbopack config silences Turbopack‑related warnings.
  turbopack: {},
  experimental: {
    workerThreads: false,
    cpus: 1,
    memoryBasedWorkersCount: true,
  },
};

export default nextConfig;
