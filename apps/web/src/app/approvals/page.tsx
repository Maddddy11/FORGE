"use client";

import { useEffect, useState } from "react";
import { listRecommendations, approveRecommendation } from "@/lib/api";
import type { Recommendation } from "@/lib/types";

function riskLabel(score: number) {
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

function RiskChip({ score }: { score: number }) {
  const rl = riskLabel(score);
  return <span className={`risk-chip ${rl}`}>{(score * 100).toFixed(0)}</span>;
}

function StateBadge({ state }: { state: string }) {
  const cls = state === "pending_approval" ? "pending" : state;
  return <span className={`badge ${cls}`}>{state.replace("_", " ")}</span>;
}

export default function ApprovalsPage() {
  const [recs, setRecs]       = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing]   = useState<string | null>(null);
  const [reason, setReason]   = useState<Record<string, string>>({});

  async function refresh() {
    try {
      const all = await listRecommendations();
      setRecs(all.sort((a, b) => b.risk_score - a.risk_score));
    } catch {
      setRecs([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function decide(id: string, approved: boolean) {
    setActing(id);
    try {
      await approveRecommendation(id, approved, reason[id] || "(no reason given)");
      await refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Request failed");
    } finally {
      setActing(null);
    }
  }

  const pending  = recs.filter((r) => r.state === "pending_approval");
  const resolved = recs.filter((r) => r.state !== "pending_approval");

  return (
    <>
      <div className="mb-2">
        <div className="page-title">Approval Queue</div>
        <div className="page-sub">
          High-risk recommendations (score ≥ 0.70) require approver sign-off before action.
          {pending.length > 0 && (
            <span style={{ marginLeft: ".75rem", color: "var(--warning)", fontWeight: 600 }}>
              {pending.length} PENDING
            </span>
          )}
        </div>
      </div>

      {loading && <div className="loader">Loading recommendations…</div>}

      {!loading && recs.length === 0 && (
        <div className="empty-state">
          No recommendations yet. Submit an incident on the Analyze page.
        </div>
      )}

      {pending.length > 0 && (
        <>
          <div className="section-label">Pending Approval</div>
          <table className="data-table mb-3">
            <thead>
              <tr>
                <th>ID</th>
                <th>Asset</th>
                <th>Risk Score</th>
                <th>Violations</th>
                <th>Top Action</th>
                <th>Reason</th>
                <th style={{ width: "180px" }}>Decision</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((r) => (
                <tr key={r.recommendation_id}>
                  <td><span className="mono" style={{ color: "var(--link)", fontSize: ".75rem" }}>{r.recommendation_id.slice(0, 8)}…</span></td>
                  <td><span className="mono">{r.asset_id}</span></td>
                  <td><RiskChip score={r.risk_score} /></td>
                  <td>
                    {r.compliance_violations.length > 0 ? (
                      <span style={{ color: "var(--danger)", fontSize: ".75rem" }}>
                        {r.compliance_violations.length} violation{r.compliance_violations.length > 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span className="text-muted text-xs">None</span>
                    )}
                  </td>
                  <td style={{ maxWidth: "260px" }}>
                    <div className="text-sm" style={{ color: "var(--text-primary)" }}>
                      {r.actions[0]?.title ?? "—"}
                    </div>
                    <div className="text-xs text-muted" style={{ marginTop: ".125rem" }}>
                      Confidence: {((r.actions[0]?.confidence ?? 0) * 100).toFixed(0)}%
                    </div>
                  </td>
                  <td>
                    <input
                      className="form-control"
                      style={{ fontSize: ".75rem", padding: ".375rem .5rem" }}
                      placeholder="Approver note…"
                      value={reason[r.recommendation_id] ?? ""}
                      onChange={(e) => setReason((prev) => ({ ...prev, [r.recommendation_id]: e.target.value }))}
                    />
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: ".375rem" }}>
                      <button
                        className="btn btn-success"
                        style={{ padding: ".375rem .75rem", fontSize: ".75rem" }}
                        disabled={acting === r.recommendation_id}
                        onClick={() => decide(r.recommendation_id, true)}
                      >
                        Approve
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ padding: ".375rem .75rem", fontSize: ".75rem" }}
                        disabled={acting === r.recommendation_id}
                        onClick={() => decide(r.recommendation_id, false)}
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {resolved.length > 0 && (
        <>
          <div className="section-label">Resolved</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Asset</th>
                <th>Risk Score</th>
                <th>State</th>
                <th>Top Action</th>
              </tr>
            </thead>
            <tbody>
              {resolved.map((r) => (
                <tr key={r.recommendation_id}>
                  <td><span className="mono" style={{ color: "var(--text-helper)", fontSize: ".75rem" }}>{r.recommendation_id.slice(0, 8)}…</span></td>
                  <td><span className="mono">{r.asset_id}</span></td>
                  <td><RiskChip score={r.risk_score} /></td>
                  <td><StateBadge state={r.state} /></td>
                  <td className="text-sm">{r.actions[0]?.title ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
