.PHONY: up down api-test api-lint api-sast web-lint web-audit container-scan lint test scan

# ── Docker Compose lifecycle ─────────────────────────────────────────────────
up:
	docker compose up --build -d

down:
	docker compose down

# ── API ──────────────────────────────────────────────────────────────────────
api-test:
	PYTHONPATH=apps/api .venv/bin/pytest apps/api/tests -q

api-lint:
	.venv/bin/ruff check apps/api/app apps/api/tests

api-sast:
	.venv/bin/bandit -r apps/api/app -ll -q -c .bandit

# ── Web ──────────────────────────────────────────────────────────────────────
web-lint:
	cd apps/web && npm run lint

web-audit:
	cd apps/web && npm audit --audit-level=high

# ── Container security ───────────────────────────────────────────────────────
container-scan:
	docker build -t imam-lite-api:scan ./apps/api
	trivy image --severity HIGH,CRITICAL --ignore-unfixed imam-lite-api:scan

# ── Data & ML pipeline ───────────────────────────────────────────────────────
seed:
	.venv/bin/python data/synthetic/seed.py

dbt-run:
	cd packages/dbt && ../../.venv/bin/dbt run --profiles-dir .

dbt-test:
	cd packages/dbt && ../../.venv/bin/dbt test --profiles-dir .

ml-train:
	.venv/bin/python ml/train.py

pipeline: seed dbt-run ml-train

# ── Convenience aggregates ───────────────────────────────────────────────────
lint: api-lint web-lint
test: api-test
scan: api-sast web-audit container-scan
