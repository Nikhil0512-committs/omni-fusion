import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Empty Turbopack config silences Turbopack‑related warnings.
  // Most apps work fine without any custom Turbopack settings.
  turbopack: {},
};

export default nextConfig;
