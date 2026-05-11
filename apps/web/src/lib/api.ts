import type { AssetHealth, DailyKPI, KPISummary, Recommendation } from "./types";

const API_URL    = process.env.API_URL    || "http://localhost:8000";
const OP_TOKEN   = process.env.DEMO_OPERATOR_TOKEN  || "";
const AP_TOKEN   = process.env.DEMO_APPROVER_TOKEN  || "";

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

export async function getAssetHealth(): Promise<AssetHealth[]> {
  const data = await apiFetch<{ assets: AssetHealth[]; ml_models_active: boolean }>(
    "/analytics/asset-health",
    OP_TOKEN,
  );
  return data.assets;
}

export async function getKPIs(): Promise<{ summary: KPISummary; daily: DailyKPI[] }> {
  return apiFetch("/analytics/kpis", OP_TOKEN);
}

export async function analyzeIncident(
  asset_id: string,
  incident_summary: string,
): Promise<Recommendation> {
  return apiFetch("/incidents/analyze", OP_TOKEN, {
    method: "POST",
    body:   JSON.stringify({ asset_id, incident_summary }),
  });
}

export async function listRecommendations(): Promise<Recommendation[]> {
  return apiFetch("/recommendations/", OP_TOKEN);
}

export async function approveRecommendation(
  id: string,
  approved: boolean,
  reason: string,
): Promise<{ recommendation_id: string; state: string }> {
  return apiFetch(`/recommendations/${id}/approve`, AP_TOKEN, {
    method: "POST",
    body:   JSON.stringify({ approved, reason }),
  });
}
