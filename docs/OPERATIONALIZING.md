# Operationalizing the Algo Trading Bot

This document describes how to take the MVP algo trading bot into production-like usage with safety, reliability, and monitoring.

---

## 0. Golden Settings for a Small Account

Example `.env` (mock → live later):

```ini
ENV=prod
SYMBOLS=AAPL,MSFT,SPY
MAX_NOTIONAL=200
LLM_WEIGHT=0.0
```

CLI typical run:

```
--risk 0.005   # 0.5% equity per trade
--stop 0.03    # -3% stop
--take 0.05    # +5% TP
--max-pos 2    # 2 concurrent positions
```

Validate in **mock** mode for at least a week before live.

---

## 1. Scheduling

### Option A — cron
```cron
*/5 9-16 * * 1-5 cd /path/to/repo && \\
  docker compose run --rm app \\
  python -m src.app run-daily --universe AAPL,MSFT \\
  --limit 40 --fast 5 --slow 20 --risk 0.005 --stop 0.03 --take 0.05 --max-pos 2 \\
  >> logs/cron.log 2>&1
```

### Option B — runner loop
`scripts/runner.sh` only schedules (every 5 minutes). Weekday and trading-hours
rules are enforced in `ComplianceEngine`.

```bash
MODE=mock  # or paper / live
bash scripts/runner.sh
```

Run with:
```bash
docker compose run --rm app bash scripts/runner.sh
```

---

## 2. Secrets & Environments

- `.env` file for keys, not checked into git.
- Example for live:

```ini
ALPACA_KEY_ID=...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

For production: use a secrets manager.

---

## 3. Monitoring & Alerting

- Health: alert on non-zero exit codes.
- Logs: tail audit or ship to ELK/CloudWatch.
- Alerts:
  - Missed >= 3 scheduled runs
  - High block ratio (>80%)
  - Excessive placed orders per minute

---

## 4. Broker Protection

- Use `place-bracket` for paper/live entries (`ENABLE_TRADING=true` required):

```bash
make run CMD='place-bracket --symbol AAPL --side buy --notional 5 --tp 0.05 --sl 0.03 --ref-price 150 --mode paper'
```

- `run-daily --mode paper|live` always submits brackets (stop/take from CLI flags).

---

## 5. Canary → Rollout

- Start with $1-$5 notionals for several days.
- Increase size gradually once fills and slippage are stable.
- Keep `MAX_NOTIONAL` conservative.

---

## 6. Rules to Enforce

- Universe whitelist: via `.env` and ComplianceEngine
- Trading hours: ComplianceEngine
- Stops/TP: OCO bracket orders
- Exposure cap: `risk/portfolio.py` (<= 50% equity)
- Max positions: `--max-pos`

---

## 7. Change Management & Safety

- Always dry run in mock/paper before live.
- Tag releases, allow rollback.
- Add a kill-switch flag (`ENABLE_TRADING=false`).
- For LLM scoring: start with weight=0.0 (shadow), review audit logs, then gradually increase.

---

## 8. Backtesting → Paper → Live Hygiene

- Backtest with fees/slippage assumptions.
- Paper trade 1–2 weeks.
- Enable live canary only after validation.

---

## 9. Dashboards

- CLI: `viz-sma` and `viz-equity` PNGs.
- Streamlit: `make dash` (decisions, SMA plots, equity curve). See `REVISION_V1.md` for remaining dashboard gaps (empty mock equity, CLI shell-out).

---

## 10. Go Live Checklist

1. `make test` passes
2. `./scripts/validate.sh` passes
3. Paper run for a week on schedule
4. Enable kill-switch flag
5. Live tiny notional via bracket orders
6. Monitor logs for status and rationale
7. Daily review and parameter adjustment

---

