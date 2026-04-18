# Runbook

## Local Startup
1. Configure `.env` from `.env.example`.
2. Run `make up`.
3. Confirm API health endpoint.

## Incident Workflow (MVP)
1. Ingest documents linked to an asset.
2. Analyze incident for that asset.
3. If recommendation is high-risk, complete approver handshake.
4. Query audit events for traceability.
