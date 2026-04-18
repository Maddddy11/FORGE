.PHONY: up down api-test api-lint web-lint test

up:
docker compose up --build -d

down:
docker compose down

api-test:
docker compose run --rm api pytest -q

api-lint:
docker compose run --rm api ruff check app tests

web-lint:
docker compose run --rm web npm run lint

test: api-test
