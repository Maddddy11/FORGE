# API Spec (MVP)

## Endpoints
- `POST /ingest/documents`
- `GET /assets/{asset_id}/context`
- `POST /incidents/analyze`
- `POST /recommendations/{id}/approve`
- `GET /recommendations/{id}/audit`
- `GET /health`

## Security
- Bearer JWT required for all endpoints except `/health`
- Roles:
  - operator: ingest, analyze, view context
  - approver: approve/review audit
  - admin: full access
