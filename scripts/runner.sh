#!/usr/bin/env bash
set -euo pipefail
while true; do
  dow=$(date +%u)
  now=$(date +%H%M)
  # force base-10 to avoid octal interpretation on leading zeros
  now=$((10#$now))
  # Mon–Fri, 09:30–16:00 local time
  if [[ $dow -ge 1 && $dow -le 5 && $now -ge 930 && $now -le 1600 ]]; then
    python -m src.app run-daily --universe AAPL,MSFT \
      --limit 40 --fast 5 --slow 20 \
      --risk 0.005 --stop 0.03 --take 0.05 --max-pos 2
  fi
  sleep 300
done