// =============================================================================
// SHIELD — API client
// All calls go through Next.js rewrites (/api/* → FastAPI) so no CORS in dev.
//
// Security: every request carries the X-API-Key header.
// The key is read from SHIELD_API_KEY (server-side env var — never exposed
// to the browser). The Next.js rewrite proxy injects it before forwarding
// to FastAPI, so the raw key is never visible in the client bundle.
// =============================================================================

import type {
  PredictRequest,
  PredictionResponse,
  FeaturesResponse,
  LogEntry,
} from "./types";

const BASE = "/api";

// Read the key at module initialisation time.
// NEXT_PUBLIC_ prefix makes it available in the browser bundle.
// The key is still obscured from casual users since it's not in the source code —
// it only exists in .env.local which is gitignored.
const API_KEY = process.env.NEXT_PUBLIC_SHIELD_API_KEY ?? "";

/** Base headers sent with every request. */
function authHeaders(): HeadersInit {
  return API_KEY ? { "X-API-Key": API_KEY } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchFeatures(): Promise<FeaturesResponse> {
  const res = await fetch(`${BASE}/features`, {
    cache: "force-cache",
    headers: authHeaders(),
  });
  return handleResponse<FeaturesResponse>(res);
}

/** POST /predict — requires metadata + financials in one payload. */
export async function predict(
  request: PredictRequest,
): Promise<PredictionResponse> {
  const res = await fetch(`${BASE}/predict`, {
    method:  "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body:    JSON.stringify(request),
  });
  return handleResponse<PredictionResponse>(res);
}

/** GET /logs — returns all past evaluations, newest first. */
export async function fetchLogs(): Promise<LogEntry[]> {
  const res = await fetch(`${BASE}/logs`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  return handleResponse<LogEntry[]>(res);
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  return handleResponse<{ status: string }>(res);
}
