CMD?=--help

run:
	docker compose run --rm app python -m src.app $(CMD)

test:
	docker compose run --rm app python -m pytest -v --maxfail=1 --disable-warnings

validate:
	./scripts/validate.sh

.PHONY: run-scheduler
run-scheduler:
	docker compose run --rm app bash scripts/runner.sh

.PHONY: health
health:
	docker compose run --rm app bash scripts/healthcheck.sh

.PHONY: dash
dash:
	docker compose up dash