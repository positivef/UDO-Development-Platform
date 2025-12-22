import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Production optimization: Standalone output for Docker
  output: 'standalone',

  // Disable telemetry
  typescript: {
    ignoreBuildErrors: false,
  },

  // Image optimization
  images: {
    unoptimized: process.env.NODE_ENV === 'development',
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
