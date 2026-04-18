# IMAM Lite — Institutional Memory & Asset Management Co-Pilot

IMAM Lite is an MVP-ready, security-minded scaffold for an agentic maintenance co-pilot that ingests industrial documents, retrieves asset context, generates explainable recommendations, applies compliance/risk checks, and enforces human approval for high-risk actions.

## MVP Scope
- FastAPI backend with endpoint contract for ingestion, context retrieval, incident analysis, approval, and audit.
- Next.js dashboard starter for incident/recommendation workflows.
- Policy-driven compliance and risk gating.
- Audit trail-first design for traceable decisions.

## Quickstart
1. Copy `.env.example` to `.env`.
2. Run `make up`.
3. API health: `http://localhost:8000/health`.
4. API docs: `http://localhost:8000/docs`.

## Security Posture (MVP)
- JWT-based auth and role checks (Operator/Approver/Admin).
- Input validation through Pydantic models.
- Immutable-style audit events (append-only event log service pattern).
- Encrypted transport expectation (TLS 1.3 at deployment edge).
- Secrets via environment variables only.

## Repository Layout
See `docs/ARCHITECTURE.md` and `docs/API_SPEC.md`.
