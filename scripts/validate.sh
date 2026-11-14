#!/usr/bin/env bash
set -euo pipefail

echo "== Build =="
docker compose build

echo
echo "== Tests =="
docker compose run --rm app python -m pytest -q

echo
echo "== Mock fetch =="
docker compose run --rm app python -m src.app fetch-bars --symbol AAPL --limit 3 --mock

echo
echo "== Daily (LLM shadow mode) =="
docker compose run --rm app python -m src.app run-daily --universe AAPL,MSFT --limit 40 --fast 5 --slow 20 --risk 0.01 --mode mock

echo
echo "== Viz =="
docker compose run --rm app python -m src.app viz-sma --symbol AAPL --limit 40 --fast 5 --slow 20 --mock --out /app/viz_sma.png
ls -l viz_sma.png || true

echo
echo "== OK =="
