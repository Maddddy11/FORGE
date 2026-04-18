# IMAM Lite Architecture (MVP)

## Core Components
- Next.js Dashboard (UI)
- FastAPI API Gateway
- Auth/RBAC middleware
- Orchestrator (LangGraph-ready state flow)
- Ingestion, Retrieval/Reasoning, Compliance, Ethical Handshake agent modules

## Data Layer
- PostgreSQL (assets, incidents, approvals, audit)
- Qdrant (embeddings + metadata)
- Redis (cache/session)
- Object storage (raw docs and parsed artifacts)

## Observability
- OpenTelemetry-ready service boundaries
- Prometheus/Grafana targets via containerized deployment extension

## Security
- JWT auth + role enforcement
- Strict request schema validation
- Append-only audit event model
- TLS and encryption-at-rest requirements enforced at deployment/infrastructure layer
