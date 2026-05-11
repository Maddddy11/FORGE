export interface AssetHealth {
  asset_id: string;
  name: string;
  type: string;
  location: string;
  total_readings: number;
  drift_flagged_count: number;
  avg_temp_c: number;
  avg_vib_mms: number;
  avg_pressure_bar: number;
  health_score: number;
  last_reading_at: string;
}

export interface KPISummary {
  total_incidents: number;
  total_high_risk: number;
  high_risk_rate: number;
  avg_mttd_high_risk_hrs: number | null;
}

export interface DailyKPI {
  incident_date: string;
  incident_count: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  avg_risk_score: number;
  avg_mttd_high_risk_hrs: number | null;
  avg_resolution_hrs: number;
  approval_required_count: number;
}

export interface ActionOption {
  title: string;
  rationale: string;
  confidence: number;
  evidence_links: string[];
}

export interface Recommendation {
  recommendation_id: string;
  asset_id: string;
  risk_score: number;
  compliance_violations: string[];
  actions: ActionOption[];
  state: "draft" | "pending_approval" | "approved" | "rejected";
}
