"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { analyzeIncident } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Recommendation } from "@/lib/types";

const ASSETS = ["PUMP-101", "PUMP-102", "COMP-201", "HEX-301", "VALVE-401"];

function riskLabel(score: number) {
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

function RecommendationPanel({ rec }: { rec: Recommendation }) {
  const rl = riskLabel(rec.risk_score);
  return (
    <div>
      <div className={`rec-risk-banner ${rl}`}>
        <div>
          <div className={`rec-risk-score ${rl}`}>{(rec.risk_score * 100).toFixed(0)}</div>
          <div className="text-xs text-muted mt-1">RISK SCORE / 100</div>
        </div>
        <div>
          <div style={{ marginBottom: ".25rem" }}>
            <span className={`badge ${rec.state === "pending_approval" ? "pending" : rec.state}`}>
              {rec.state.replace("_", " ")}
            </span>
          </div>
          <div className="text-xs text-muted">
            ID: <span className="mono">{rec.recommendation_id.slice(0, 8)}…</span>
          </div>
          <div className="text-xs text-muted">
            Asset: <span className="mono">{rec.asset_id}</span>
          </div>
        </div>
      </div>

      {rec.compliance_violations.length > 0 && (
        <div className="mb-2">
          <div className="panel-title" style={{ marginBottom: ".5rem" }}>Compliance Violations</div>
          <ul className="violations">
            {rec.compliance_violations.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </div>
      )}

      <div className="panel-title">Ranked Actions</div>
      <div className="rec-actions">
        {rec.actions.map((action, i) => (
          <div key={i} className="rec-action">
            <div className="rec-action-title">
              <span className="text-muted" style={{ marginRight: ".5rem" }}>0{i + 1}.</span>
              {action.title}
            </div>
            <div className="rec-action-rationale">{action.rationale}</div>
            <div className="confidence-bar-wrap">
              <span className="text-xs text-muted" style={{ minWidth: "80px" }}>CONFIDENCE</span>
              <div className="confidence-bar-track">
                <div className="confidence-bar-fill" style={{ width: `${action.confidence * 100}%` }} />
              </div>
              <span className="confidence-val">{(action.confidence * 100).toFixed(0)}%</span>
            </div>
            {action.evidence_links[0] !== "abstain://no-evidence" && (
              <div className="text-xs text-muted mt-1">
                {action.evidence_links.map((l, j) => (
                  <span key={j} style={{ marginRight: ".5rem", color: "var(--link)" }}>{l}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  const { role, token, ready } = useAuth();
  const router = useRouter();

  const [assetId, setAssetId]     = useState(ASSETS[0]);
  const [summary, setSummary]     = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [result, setResult]       = useState<Recommendation | null>(null);

  useEffect(() => {
    if (ready && !token) router.replace("/login");
  }, [ready, token, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!summary.trim() || !token) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const rec = await analyzeIncident(assetId, summary, token);
      setResult(rec);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  if (!ready || !token) return null;

  return (
    <>
      <div className="mb-2">
        <div className="page-title">Incident Analysis</div>
        <div className="page-sub">
          Submit an incident report. The AI co-pilot retrieves asset context, scores risk, and proposes ranked actions.
        </div>
      </div>

      <div className="split-layout">
        {/* Left: form */}
        <div className="split-pane">
          <div className="panel-title">Incident Input</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="asset">Asset ID</label>
              <select
                id="asset"
                className="form-control"
                value={assetId}
                onChange={(e) => setAssetId(e.target.value)}
              >
                {ASSETS.map((a) => <option key={a}>{a}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="summary">Incident Summary</label>
              <textarea
                id="summary"
                className="form-control"
                rows={8}
                placeholder="Describe the observed symptoms, alarms, or anomalies…"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                style={{ minHeight: "180px" }}
              />
            </div>
            <div style={{ display: "flex", gap: ".75rem", flexWrap: "wrap" }}>
              <button className="btn btn-primary" type="submit" disabled={loading || !summary.trim()}>
                {loading ? "Analyzing…" : "Run Analysis"}
              </button>
              <button
                className="btn btn-ghost"
                type="button"
                onClick={() => { setSummary(""); setResult(null); setError(null); }}
              >
                Clear
              </button>
            </div>
          </form>

          {/* Quick scenario presets */}
          <div style={{ marginTop: "1.5rem" }}>
            <div className="section-label">Scenario Presets</div>
            {[
              { label: "High Vib + Temp", text: "Pump P-101 showing high vibration 8.2 mm/s and temperature spike to 95°C. Possible seal failure with minor gland leak observed." },
              { label: "Bypass Attempt", text: "Operator attempting to bypass safety interlock to restart compressor C-201 after trip. OEM manual not consulted." },
              { label: "Routine PM", text: "Scheduled preventive maintenance on heat exchanger E-301. Filter element due for replacement. No alarms present." },
            ].map(({ label, text }) => (
              <button
                key={label}
                className="btn btn-ghost"
                type="button"
                style={{ width: "100%", marginBottom: ".375rem", justifyContent: "flex-start", fontSize: ".75rem" }}
                onClick={() => { setSummary(text); setResult(null); setError(null); }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Right: output */}
        <div className="split-pane right">
          <div className="panel-title">AI Co-Pilot Output</div>
          {loading && <div className="loader">Running LLM analysis via Groq…</div>}
          {error && (
            <div style={{ padding: "1rem", background: "rgba(250,77,86,.08)", borderLeft: "4px solid var(--danger)", color: "var(--danger)", fontSize: ".8125rem" }}>
              {error}
            </div>
          )}
          {result && <RecommendationPanel rec={result} />}
          {!loading && !error && !result && (
            <div className="empty-state">
              Submit an incident report to see ranked recommendations, risk score, and compliance checks.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
