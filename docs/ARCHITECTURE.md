# IMAM Lite — Architecture

## Overview

IMAM Lite is a three-tier system: a data + ML pipeline feeding a FastAPI backend, served by a Next.js dashboard. Risk scoring fuses three independent signals so no single model can underestimate a safety-critical situation.

---

## ML Risk Fusion

The core design decision. Three signals compete; the maximum always wins:

```
                         ┌─────────────────────────────┐
Incident text ──────────►│ TF-IDF + LogisticRegression │──► P(high-risk) ─────┐
                         └─────────────────────────────┘                       │
                                                                                ├──► max() ──► risk_score
                         ┌─────────────────────────────┐                       │
Incident text ──────────►│ Groq LLM (JSON mode)        │──► risk_score ────────┤
                         │ llama-3.3-70b-versatile      │                       │
                         └─────────────────────────────┘                       │
                                                                                │
Keyword scan ───────────►  safety floor                  ──► 0.70 / 0.90 ──────┘
                           bypass→0.90, fire/rupture→0.70
```

**Why max() not average?** Industrial safety systems should be pessimistic. An LLM that underestimates a bypass-of-interlock scenario must be corrected by the keyword floor, not averaged away.

---

## Data Engineering Pipeline

```
data/synthetic/seed.py
        │
        ▼ writes
DuckDB (imam_lite.duckdb)
  ├── assets             (5 rows)
  ├── sensor_readings    (14,400 rows — 30 days × 5 assets × 15-min intervals)
  ├── incidents          (180 rows — synthetic labeled descriptions)
  └── work_orders        (60 rows)
        │
        ▼ dbt run
packages/dbt/models/
  ├── staging/
  │   ├── stg_sensor_readings   (view — clean + z-score features)
  │   └── stg_incidents         (view — risk ordinal, approval flag)
  ├── facts/
  │   └── fct_anomalies         (table — rolling window stats, drift score)
  └── marts/
      ├── mart_asset_health     (table — per-asset health score)
      └── mart_incident_kpis    (table — daily KPI roll-up)
```

The dbt mart tables are queried directly by the FastAPI analytics endpoints. If dbt hasn't run, `db_service.py` falls back to equivalent raw-table aggregations so the API stays operational.

---

## ML Models

### Anomaly Detector — IsolationForest

- **Input:** per-asset z-scored (temperature_c, vibration_mms, pressure_bar)
- **Training:** fit on normal readings only (contamination estimated from data: ~0.9%)
- **Output:** decision_function score → sigmoid-mapped to [0, 1] (higher = more anomalous)
- **ROC-AUC:** 0.789 on full held-out dataset
- **Artefacts:** `ml/models/anomaly_detector.joblib`, `ml/models/feature_meta.joblib`

### Risk Text Classifier — TF-IDF + LogisticRegression

- **Input:** raw incident description string
- **Features:** bigram TF-IDF, max 2,000 features, sublinear_tf, class_weight=balanced
- **Output:** probability of high-risk class (≥ 0.70 threshold)
- **ROC-AUC:** 1.000 on 80/20 stratified test split
- **Artefact:** `ml/models/risk_classifier.joblib`

Both models are loaded once at API startup in `ml_service.py`. The service degrades gracefully (returns `None`) if models haven't been trained yet.

---

## API Layer

```
FastAPI (apps/api)
├── Middleware
│   ├── CORS (localhost:3001)
│   └── JWT auth + RBAC (operator / approver / admin)
├── Routers
│   ├── /ingest          — document ingestion into in-memory store
│   ├── /assets          — asset context retrieval
│   ├── /incidents       — incident analysis (LLM + ML fusion)
│   ├── /recommendations — list, approve, audit trail
│   └── /analytics       — asset health + KPI endpoints (DuckDB)
└── Services
    ├── llm_service      — Groq client, JSON-mode prompt
    ├── ml_service       — loads joblib models, classify_risk(), score_anomaly()
    ├── db_service       — read-only DuckDB queries
    ├── recommendation_service — orchestrates fusion, writes audit
    ├── approval_service — state machine: draft → pending → approved/rejected
    └── audit_service    — append-only event log
```

---

## Frontend

```
Next.js 15 (apps/web) — IBM Carbon G100 dark theme
├── /              — Dashboard (server component)
│                    KPI bar · asset health grid · incident trend chart
├── /analyze       — Incident form + recommendation panel (client component)
│                    Preset scenarios · risk banner · action list · confidence bars
└── /approvals     — Approval queue (client component)
                     Pending table with approve/reject · resolved history
```

Data flow: server components fetch directly from FastAPI using server-side env vars (token stays off the browser). Client components call FastAPI directly via CORS.

---

## Security

| Control | Implementation |
|---|---|
| Authentication | HS256 JWT — required on all endpoints except `/health` |
| Authorisation | Role check per endpoint (`require_roles` dependency) |
| Input validation | Pydantic v2 models with field constraints |
| Audit trail | Append-only `AuditEvent` list per recommendation |
| SAST | Bandit in CI and pre-commit |
| SCA | `npm audit` (web), Trivy image scan (container) |
| Secret detection | detect-private-key + detect-secrets pre-commit hooks |
| Transport | TLS 1.3 enforced at deployment edge |

---

## Compliance Gate

Applied at inference time in `recommendation_service.py` and injected into the LLM system prompt:

| Rule | Trigger | Effect |
|---|---|---|
| OEM-INT-001 | "bypass" or "interlock" in text | Risk floor → 0.90, compliance violation added |
| ASME-PRESS-002 | "pressure" + "restart" | LLM instructed to cite rule |
| API-INSPECT-003 | "inspection" or "checklist" | LLM instructed to cite rule |

Recommendations with `risk_score ≥ 0.70` are set to `pending_approval` state and require an approver-role JWT to progress.
