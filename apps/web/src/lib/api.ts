import type { AssetHealth, DailyKPI, KPISummary, Recommendation } from "./types";

const API_URL      = process.env.NEXT_PUBLIC_API_URL             || "http://localhost:8000";
const SERVER_TOKEN = process.env.NEXT_PUBLIC_DEMO_OPERATOR_TOKEN || "imam-demo-operator";

async function apiFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization:  `Bearer ${token}`,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Server-component calls (use default operator token) ───────────────────

export async function getAssetHealth(): Promise<AssetHealth[]> {
  const data = await apiFetch<{ assets: AssetHealth[]; ml_models_active: boolean }>(
    "/analytics/asset-health",
    SERVER_TOKEN,
  );
  return data.assets;
}

export async function getKPIs(): Promise<{ summary: KPISummary; daily: DailyKPI[] }> {
  return apiFetch("/analytics/kpis", SERVER_TOKEN);
}

// ── Client-component calls (caller passes the token from useAuth) ─────────

export async function analyzeIncident(
  asset_id: string,
  incident_summary: string,
  token: string,
): Promise<Recommendation> {
  return apiFetch("/incidents/analyze", token, {
    method: "POST",
    body:   JSON.stringify({ asset_id, incident_summary }),
  });
}

export async function listRecommendations(token: string): Promise<Recommendation[]> {
  return apiFetch("/recommendations/", token);
}

export async function approveRecommendation(
  id: string,
  approved: boolean,
  reason: string,
  token: string,
): Promise<{ recommendation_id: string; state: string }> {
  return apiFetch(`/recommendations/${id}/approve`, token, {
    method: "POST",
    body:   JSON.stringify({ approved, reason }),
  });
}
