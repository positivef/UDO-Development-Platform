/**
 * API Configuration - Single Source of Truth
 *
 * All components should import API_URL and WS_URL from this file
 * to ensure consistent backend URL usage across the frontend.
 */

// Backend URL - read from environment or use default
// Backend runs on port 8000 by default
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8006";

// WebSocket URL - derived from API_URL
export const WS_URL = (() => {
  try {
    const url = new URL(API_URL);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return url.origin;
  } catch {
    return "ws://localhost:8006";
  }
})();

// API endpoints helper
export const endpoints = {
  health: `${API_URL}/health`,
  status: `${API_URL}/api/status`,
  metrics: `${API_URL}/api/metrics`,
  uncertainty: {
    status: `${API_URL}/api/uncertainty/status`,
    confidence: `${API_URL}/api/uncertainty/confidence`,
    ack: (id: string) => `${API_URL}/api/uncertainty/ack/${id}`,
  },
  governance: {
    tierStatus: `${API_URL}/api/governance/tier/status`,
    tierUpgrade: `${API_URL}/api/governance/tier/upgrade`,
  },
  projects: {
    list: `${API_URL}/api/projects`,
    current: `${API_URL}/api/projects/current`,
  },
  tasks: `${API_URL}/api/tasks/`,
  websocket: `${WS_URL}/ws`,
} as const;

// Debug logging (only in development)
if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
  console.log("[API Config] Backend URL:", API_URL);
  console.log("[API Config] WebSocket URL:", WS_URL);
}
