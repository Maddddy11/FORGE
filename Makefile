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

cmapss-fetch:
	.venv/bin/python data/cmapss/fetch.py

cmapss-seed:
	.venv/bin/python data/cmapss/seed_cmapss.py

dbt-run:
	cd packages/dbt && ../../.venv/bin/dbt run --profiles-dir .

dbt-test:
	cd packages/dbt && ../../.venv/bin/dbt test --profiles-dir .

ml-train:
	.venv/bin/python ml/train.py

# Synthetic-only pipeline (no network required)
pipeline: seed dbt-run ml-train

# CMAPSS pipeline: fetch real data, seed DB, run dbt, train all models
cmapss-pipeline: cmapss-fetch seed cmapss-seed dbt-run ml-train

# ── Convenience aggregates ───────────────────────────────────────────────────
lint: api-lint web-lint
test: api-test
scan: api-sast web-audit container-scan
