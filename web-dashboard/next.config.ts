import type { NextConfig } from "next";

// Backend URL - single source of truth
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

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
    NEXT_PUBLIC_API_URL: BACKEND_URL,
  },

  // Rewrites: Proxy API requests to backend
  // This allows frontend to use relative URLs like /api/health
  // and Next.js will automatically forward them to the backend
  async rewrites() {
    return [
      // Proxy all /api/* requests to backend
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
      // Proxy health endpoint
      {
        source: "/health",
        destination: `${BACKEND_URL}/health`,
      },
      // Proxy WebSocket connections
      {
        source: "/ws",
        destination: `${BACKEND_URL}/ws`,
      },
      {
        source: "/ws/:path*",
        destination: `${BACKEND_URL}/ws/:path*`,
      },
    ];
  },
};

export default nextConfig;

