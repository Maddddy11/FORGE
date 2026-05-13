import { getAssetHealth, getKPIs } from "@/lib/api";
import type { AssetHealth, DailyKPI } from "@/lib/types";

function riskClass(score: number) {
  if (score >= 0.7) return "danger";
  if (score >= 0.4) return "warning";
  return "success";
}

function healthClass(score: number) {
  if (score >= 0.95) return "good";
  if (score >= 0.80) return "warning";
  return "danger";
}

function AssetCard({ asset }: { asset: AssetHealth }) {
  const hc = healthClass(asset.health_score);
  return (
    <div className="asset-card">
      <div className="asset-id">{asset.asset_id}</div>
      <div className="asset-name">{asset.name}</div>
      <div className="health-bar-wrap">
        <div className="health-bar-label">
          <span>HEALTH</span>
          <strong>{(asset.health_score * 100).toFixed(1)}%</strong>
        </div>
        <div className="health-bar-track">
          <div
            className={`health-bar-fill ${hc}`}
            style={{ width: `${asset.health_score * 100}%` }}
          />
        </div>
      </div>
      <div className="asset-meta">
        <div className="asset-meta-row">
          <span>TEMP</span>
          <span>{asset.avg_temp_c.toFixed(1)} °C</span>
        </div>
        <div className="asset-meta-row">
          <span>VIB</span>
          <span>{asset.avg_vib_mms.toFixed(2)} mm/s</span>
        </div>
        <div className="asset-meta-row">
          <span>PRESS</span>
          <span>{asset.avg_pressure_bar.toFixed(2)} bar</span>
        </div>
        <div className="asset-meta-row">
          <span>DRIFT FLAGS</span>
          <span style={{ color: asset.drift_flagged_count > 0 ? "var(--warning)" : "var(--success)" }}>
            {asset.drift_flagged_count}
          </span>
        </div>
        <div className="asset-meta-row">
          <span>LOCATION</span>
          <span>{asset.location}</span>
        </div>
      </div>
    </div>
  );
}

function IncidentChart({ daily }: { daily: DailyKPI[] }) {
  const max = Math.max(...daily.map((d) => d.incident_count), 1);
  const recent = daily.slice(-14);
  return (
    <div className="panel" style={{ marginBottom: "2rem" }}>
      <div className="panel-title">30-Day Incident Trend — Last 14 Days Shown</div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: "3px", height: "80px" }}>
        {recent.map((d) => (
          <div
            key={d.incident_date}
            title={`${d.incident_date}: ${d.incident_count} incidents (${d.high_risk_count} high)`}
            style={{ flex: 1, display: "flex", flexDirection: "column", gap: "1px", height: "100%" }}
          >
            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
              <div style={{ height: `${(d.high_risk_count / max) * 100}%`, background: "var(--danger)", minHeight: d.high_risk_count > 0 ? "2px" : "0" }} />
              <div style={{ height: `${(d.medium_risk_count / max) * 100}%`, background: "var(--warning)", minHeight: d.medium_risk_count > 0 ? "2px" : "0" }} />
              <div style={{ height: `${(d.low_risk_count / max) * 100}%`, background: "var(--border-strong)", minHeight: d.low_risk_count > 0 ? "2px" : "0" }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: "1.5rem", marginTop: ".75rem" }}>
        {[
          { color: "var(--danger)",   label: "High" },
          { color: "var(--warning)",  label: "Medium" },
          { color: "var(--border-strong)", label: "Low" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: ".375rem", fontSize: ".75rem", color: "var(--text-helper)" }}>
            <span style={{ width: 10, height: 10, background: color, display: "inline-block" }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

export default async function DashboardPage() {
  let assets: AssetHealth[] = [];
  let summary = { total_incidents: 0, total_high_risk: 0, high_risk_rate: 0, avg_mttd_high_risk_hrs: null as number | null };
  let daily: DailyKPI[] = [];

  try {
    [assets, { summary, daily }] = await Promise.all([getAssetHealth(), getKPIs()]);
  } catch {
    // API not running yet — show empty state
  }

  const mttd = summary.avg_mttd_high_risk_hrs?.toFixed(1) ?? "—";
  const rateClass = riskClass(summary.high_risk_rate);

  return (
    <>
      <div className="mb-2">
        <div className="page-title">Operations Dashboard</div>
        <div className="page-sub">Asset health, incident KPIs, and anomaly status — live from DuckDB + ML pipeline.</div>
      </div>

      {/* KPI bar */}
      <div className="kpi-bar">
        <div className="kpi-card">
          <div className="kpi-label">Total Incidents (30d)</div>
          <div className="kpi-value">{summary.total_incidents}</div>
          <div className="kpi-sub">all severity levels</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">High-Risk Count</div>
          <div className={`kpi-value ${summary.total_high_risk > 0 ? "danger" : "success"}`}>
            {summary.total_high_risk}
          </div>
          <div className="kpi-sub">require approver sign-off</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">High-Risk Rate</div>
          <div className={`kpi-value ${rateClass}`}>
            {(summary.high_risk_rate * 100).toFixed(1)}%
          </div>
          <div className="kpi-sub">target: &lt; 25%</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Avg MTTD (High Risk)</div>
          <div className="kpi-value">{mttd}<span style={{ fontSize: "1rem", color: "var(--text-helper)" }}> hr</span></div>
          <div className="kpi-sub">mean time to diagnose</div>
        </div>
      </div>

      {/* Asset health */}
      <div className="section-label">Asset Health — {assets.length} Assets Monitored</div>
      {assets.length > 0 ? (
        <div className="asset-grid mb-3">
          {assets.map((a) => <AssetCard key={a.asset_id} asset={a} />)}
        </div>
      ) : (
        <div className="empty-state mb-3">
          No asset data. Run <code>make pipeline</code> to seed the database.
        </div>
      )}

      {/* Incident chart */}
      {daily.length > 0 && (
        <>
          <div className="section-label">Incident Activity</div>
          <IncidentChart daily={daily} />
        </>
      )}
    </>
  );
}
