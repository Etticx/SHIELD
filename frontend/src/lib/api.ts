// =============================================================================
// SHIELD — API client
// All calls go through Next.js rewrites (/api/* → FastAPI) so no CORS in dev.
// =============================================================================

import type {
  PredictRequest,
  PredictionResponse,
  FeaturesResponse,
  LogEntry,
} from "./types";

const BASE = "/api";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchFeatures(): Promise<FeaturesResponse> {
  const res = await fetch(`${BASE}/features`, { cache: "force-cache" });
  return handleResponse<FeaturesResponse>(res);
}

/** POST /predict — now requires metadata + financials in one payload. */
export async function predict(
  request: PredictRequest,
): Promise<PredictionResponse> {
  const res = await fetch(`${BASE}/predict`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(request),
  });
  return handleResponse<PredictionResponse>(res);
}

/** GET /logs — returns all past evaluations, newest first. */
export async function fetchLogs(): Promise<LogEntry[]> {
  const res = await fetch(`${BASE}/logs`, { cache: "no-store" });
  return handleResponse<LogEntry[]>(res);
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`, { cache: "no-store" });
  return handleResponse<{ status: string }>(res);
}
