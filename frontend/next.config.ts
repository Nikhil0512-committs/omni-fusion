import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  serverExternalPackages: ["onnxruntime-web"],
  webpack: (config, { isServer }) => {
    // Prevent onnxruntime-web WASM from being processed during server builds
    if (isServer) {
      config.externals = config.externals || [];
      config.externals.push("onnxruntime-web");
    }
    // Handle .wasm files
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
    };
    return config;
  },
};

export default nextConfig;
