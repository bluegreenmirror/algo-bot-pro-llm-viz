#!/usr/bin/env bash
# Scheduler only: wake periodically and invoke run-daily.
# Weekday / trading-hours enforcement lives in ComplianceEngine (authoritative).
set -euo pipefail
MODE="${MODE:-mock}"
while true; do
  python -m src.app run-daily --mode "$MODE" --universe AAPL,MSFT \
    --limit 40 --fast 5 --slow 20 \
    --risk 0.005 --stop 0.03 --take 0.05 --max-pos 2
  sleep 300
done
