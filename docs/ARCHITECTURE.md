# FORGE — Architecture

## System Diagram

```mermaid
flowchart TB
    %% ── Users ────────────────────────────────────────────────────────────
    subgraph USERS["USERS"]
        direction LR
        OP["Operator\n──────────\nSubmit incidents\nView results"]
        AP["Approver\n──────────\nAll operator access\n+ Approve / Reject"]
        AD["Admin\n──────────\nFull access"]
    end

    %% ── Frontend ─────────────────────────────────────────────────────────
    subgraph FE["FRONTEND — Next.js 15  •  port 3002"]
        direction TB
        LOGIN["/login\nRole selector\n3 demo tokens"]
        DASH["/ Dashboard\nServer component\nKPI bar · Asset health · Trend chart"]
        ANALYZE["/analyze\nClient component\nIncident form · AI output panel"]
        APPROVALS["/approvals\nClient component\nPending queue · Approve/Reject"]
        AUTHCTX["Auth Context\nlocalStorage  •  role + token\nredirects unauthenticated users"]
    end

    %% ── API ──────────────────────────────────────────────────────────────
    subgraph API["BACKEND — FastAPI  •  port 8000"]
        direction TB
        RBAC["RBAC Middleware\nBearer token → role\nrequire_roles() per endpoint"]

        subgraph ROUTERS["Routers"]
            direction LR
            R1["POST /incidents/analyze\n[operator, admin]"]
            R2["GET  /recommendations/\n[operator, approver, admin]"]
            R3["POST /recommendations/:id/approve\n[approver, admin]"]
            R4["GET  /analytics/*\n[operator+]"]
        end

        subgraph SERVICES["Services"]
            direction TB
            REC["RecommendationService\nFusion orchestrator\nmax(LLM, ML, keyword floor)"]
            LLM_SVC["LLM Service\nGroq client  •  JSON mode\nStructured prompt + compliance rules"]
            ML_SVC["ML Service\njoblib model loader\nclassify_risk()  score_anomaly()  predict_rul()"]
            DB_SVC["DB Service\nRead-only DuckDB\nqueries dbt mart tables"]
            APPROVAL["Approval Service\nState machine\ndraft → pending → approved/rejected"]
            AUDIT["Audit Service\nAppend-only event log\nactor + timestamp + reasoning"]
        end
    end

    %% ── AI / ML ──────────────────────────────────────────────────────────
    subgraph AIML["AI / ML LAYER"]
        direction LR
        GROQ["☁  Groq API\nLlama-3.3-70b-versatile\nExternal  •  JSON-mode\nreturns risk_score + actions"]

        subgraph MODELS["Local Models  (ml/models/)"]
            direction TB
            ISO["IsolationForest\nAnomaly Detector\nInput: z-scored sensor readings\nROC-AUC 0.975"]
            TFIDF["TF-IDF + LogisticRegression\nRisk Classifier\nInput: incident text\nAUC 1.000"]
            GBR["GradientBoosting\nRUL Predictor\nInput: 14 CMAPSS sensors\nMAE 13.3 cycles"]
        end
    end

    %% ── Data ─────────────────────────────────────────────────────────────
    subgraph DATA["DATA LAYER"]
        direction TB
        DUCKDB[("DuckDB\nimam_lite.duckdb\n────────────────\nassets  •  sensor_readings\nincidents  •  work_orders")]

        subgraph DBT["dbt Core Pipeline  (packages/dbt/)"]
            direction LR
            STG["Staging  (views)\nstg_sensor_readings\nstg_incidents\nclean + z-score"]
            FCT["Facts  (table)\nfct_anomalies\nrolling 2-hr window\ndrift_score"]
            MART["Marts  (tables)\nmart_asset_health\nmart_incident_kpis\nhealth_score  •  min_rul"]
        end
    end

    %% ── Data Sources ─────────────────────────────────────────────────────
    subgraph SOURCES["DATA SOURCES"]
        direction LR
        CMAPSS["NASA CMAPSS FD001\n────────────────\n100 turbofan engines\n20,631 run-to-failure cycles\n14 sensor channels\nReal degradation signals"]
        SYNTH["Synthetic\n────────────────\nIncident text templates\nWork orders\nRisk labels (low/med/high)"]
    end

    %% ── DevSecOps ────────────────────────────────────────────────────────
    subgraph DEVSEC["DEVSECOPS  (GitHub Actions CI)"]
        direction LR
        LINT["Lint\nruff  •  eslint"]
        TEST["Test\npytest  •  npm audit"]
        SAST["SAST / SCA\nbandit  •  Trivy\ndetect-secrets"]
    end

    %% ── Edges ────────────────────────────────────────────────────────────
    USERS -->|"HTTPS + Bearer token"| FE
    FE -->|"REST  •  Authorization header"| RBAC
    RBAC --> ROUTERS

    R1 --> REC
    R2 --> APPROVAL
    R3 --> APPROVAL
    R4 --> DB_SVC

    REC --> LLM_SVC
    REC --> ML_SVC
    REC --> DB_SVC
    REC --> APPROVAL
    APPROVAL --> AUDIT

    LLM_SVC -->|"HTTPS  •  API key"| GROQ
    ML_SVC --> ISO
    ML_SVC --> TFIDF
    ML_SVC --> GBR

    DB_SVC -->|"read-only"| DUCKDB
    DUCKDB --- STG --> FCT --> MART

    CMAPSS -->|"seed_cmapss.py\n5 engines → 5 assets"| DUCKDB
    CMAPSS -->|"all 100 engines\nfor ML training"| GBR
    CMAPSS -->|"all 100 engines\nfor ML training"| ISO
    SYNTH  -->|"seed.py"| DUCKDB
    SYNTH  -->|"incident text"| TFIDF

    DEVSEC -.->|"on push / PR"| API
    DEVSEC -.->|"on push / PR"| FE

    %% ── Styles ───────────────────────────────────────────────────────────
    classDef external  fill:#fef3c7,stroke:#b45309,color:#1c1917
    classDef data      fill:#f0fdf4,stroke:#166534,color:#14532d
    classDef ml        fill:#eff6ff,stroke:#1e40af,color:#1e3a8a
    classDef api       fill:#fafafa,stroke:#6b7280,color:#111827
    classDef fe        fill:#fff7ed,stroke:#b45309,color:#1c1917

    class GROQ external
    class DUCKDB,STG,FCT,MART,CMAPSS,SYNTH data
    class ISO,TFIDF,GBR ml
    class RBAC,ROUTERS,SERVICES api
    class LOGIN,DASH,ANALYZE,APPROVALS,AUTHCTX fe
```

---

## Risk Fusion — How the Score is Computed

Three signals compete. The maximum always wins — safety systems should be pessimistic:

```
Incident text ──► TF-IDF + LogReg ──────────────────────► P(high)  ─────┐
                                                                          │
Incident text ──► Groq LLM (JSON mode) ─────────────────► risk_score ───┼──► max() ──► final_score
                  llama-3.3-70b-versatile                                 │
                                                                          │
Keyword scan  ──► safety floor                                            │
                  "bypass"/"interlock" → 0.90                            │
                  "fire"/"rupture"/...  → 0.70 ──────────────────────────┘

final_score ≥ 0.70  →  state = pending_approval  (locked until approver signs off)
```

---

## Data Engineering Pipeline

```
NASA CMAPSS FD001          Synthetic generator
(20,631 rows, 100 engines) (incidents, work orders)
         │                          │
         ▼                          ▼
  data/cmapss/seed_cmapss.py   data/synthetic/seed.py
  • Maps 5 engines → 5 assets  • 180 incidents
  • Scales sensors to °C/bar   • 60 work orders
  • RUL column (real labels)   • rul = NULL
         │                          │
         └──────────┬───────────────┘
                    ▼
           DuckDB  imam_lite.duckdb
           ├── assets             (5 rows)
           ├── sensor_readings    (1,084 CMAPSS rows + rul column)
           ├── incidents          (180 rows)
           └── work_orders        (60 rows)
                    │
                    ▼ dbt run
           packages/dbt/models/
           ├── staging/
           │   ├── stg_sensor_readings   view  clean + z-scores + rul
           │   └── stg_incidents         view  risk ordinal, approval flag
           ├── facts/
           │   └── fct_anomalies         table rolling 2-hr stats, drift_score
           └── marts/
               ├── mart_asset_health     table health_score, min_rul per asset
               └── mart_incident_kpis    table daily KPI roll-up
                    │
                    ▼ python ml/train.py
           ml/models/
           ├── anomaly_detector.joblib   IsolationForest  ROC-AUC 0.975
           ├── risk_classifier.joblib    TF-IDF+LogReg    AUC 1.000
           ├── feature_meta.joblib       per-asset scaling params
           └── rul_predictor.joblib      GradientBoosting MAE 13.3 cycles
```

---

## RBAC Matrix

| Endpoint | Operator | Approver | Admin |
|---|:---:|:---:|:---:|
| `GET /analytics/*` | ✅ | ✅ | ✅ |
| `GET /assets/*` | ✅ | ✅ | ✅ |
| `POST /incidents/analyze` | ✅ | ✅ | ✅ |
| `GET /recommendations/` | ✅ | ✅ | ✅ |
| `POST /recommendations/:id/approve` | ❌ 403 | ✅ | ✅ |
| `GET /recommendations/:id/audit` | ❌ 403 | ✅ | ✅ |

Frontend mirrors these constraints — operators see the approval queue read-only; the Approve/Reject buttons are hidden at render time (not just disabled).

---

## Security Controls

| Layer | Control | Implementation |
|---|---|---|
| Transport | TLS 1.3 | Deployment edge |
| Authentication | Bearer token | HS256 JWT + demo tokens |
| Authorisation | Role per endpoint | `require_roles()` FastAPI dependency |
| Input validation | Schema enforcement | Pydantic v2 with field constraints |
| Audit | Append-only log | `AuditEvent` per recommendation |
| SAST | Static analysis | Bandit (Python), ESLint (JS) |
| SCA | Dependency scan | `npm audit`, Trivy container scan |
| Secrets | Pre-commit detection | `detect-private-key`, `detect-secrets` |

---

## ML Model Details

### IsolationForest — Anomaly Detector
- **Input:** per-asset z-scored `(temperature_c, vibration_mms, pressure_bar)`
- **Training data:** CMAPSS FD001 — 5 engines, 1,084 readings, 13.84% anomaly rate
- **Label:** `is_anomaly_true = (RUL < 30 cycles)` — real degradation window
- **ROC-AUC:** 0.975 (vs 0.789 on synthetic data)

### TF-IDF + LogisticRegression — Risk Classifier
- **Input:** raw incident description string
- **Features:** bigram TF-IDF, 2,000 features, sublinear_tf, class_weight=balanced
- **Output:** P(high-risk) — used as independent check on LLM score
- **ROC-AUC:** 1.000 on 80/20 stratified split

### GradientBoosting — RUL Predictor
- **Input:** 14 CMAPSS sensor channels (s2, s3, s4, s7, s8, s9, s11–s15, s17, s20, s21)
- **Training data:** all 100 FD001 engines, 20,631 cycles, RUL clipped at 125
- **Top features:** s11 (0.400), s4 (0.235), s9 (0.121)
- **MAE:** 13.3 cycles on held-out 20% test set
