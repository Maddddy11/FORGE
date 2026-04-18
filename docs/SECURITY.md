# Security Controls (MVP)

- JWT authentication with issuer/audience checks.
- RBAC authorization in route dependencies.
- Strict Pydantic input validation and bounded fields.
- Security header-compatible API behavior via standards-compliant auth errors.
- Environment-based secret injection only.
- Immutable-style audit trail via append-only event pattern.
- Production requirements: TLS 1.3, AES-256 storage encryption, key rotation, SIEM log shipping.
