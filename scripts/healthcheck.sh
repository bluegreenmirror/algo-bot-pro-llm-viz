#!/usr/bin/env bash
set -euo pipefail
FILE="logs/audit.jsonl"
THRESHOLD=${1:-900} # seconds; default 15 minutes

if [[ ! -f "$FILE" ]]; then
  echo "NO_AUDIT_FILE"
  exit 1
fi

LAST_TS=$(tail -n 1 "$FILE" | awk -F'"ts":' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
NOW=$(date +%s)

if [[ -z "$LAST_TS" ]]; then
  echo "NO_TS_IN_AUDIT"
  exit 1
fi

AGE=$(( NOW - ${LAST_TS%.*} ))
if (( AGE > THRESHOLD )); then
  echo "STALE:${AGE}s"
  exit 2
else
  echo "OK:${AGE}s"
  exit 0
fi