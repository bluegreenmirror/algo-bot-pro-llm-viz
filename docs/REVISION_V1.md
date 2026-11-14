# v1 Revision Plan

Source of truth for this revision: this file, `OPERATIONALIZING.md`, and `SECURITY.md`.
Archived MVP: branch `archive/v0-mvp`, tag `v0.1.0-mvp`.

## Product contract (v1)

This repo is a local CLI + Streamlit trading bot with mock and paper Alpaca paths.
It is not an API server, user database, auth system, or pip-installable viz package.

## Checklist

### v1.0 Spec + safety

- [ ] Demote or rewrite `ARCHITECTURE.md` and `USAGE.md` to match the bot above
- [ ] Kill-switch: unset or `false` blocks broker orders; only explicit `true` allows them
- [ ] Modes: `mock | paper | live` (no silent live market-order path)
- [ ] Pass stop / take-profit through execution into bracket orders
- [ ] Compliance owns trading hours and weekdays; runner only schedules
- [ ] Deduplicate `.env.example`; mock runs without live keys

### v1.1 State + honest validation

- [ ] Persist equity and open positions under `STATE_DIR`
- [ ] Exposure and `--max-pos` use persisted state
- [ ] Non-monotonic mock bars or fixtures so SMA crosses occur
- [ ] Backtest fees / slippage; dashboard equity curve has real trades

### v1.2 Paper path

- [ ] Pin Alpaca client; paper validate path in `validate.sh`
- [ ] Health alerts: missed runs, high block ratio, order-rate spikes
- [ ] Optional LLM shadow (`LLM_WEIGHT=0`) after audit reasons are real

## Out of scope for v1

- API server, database, auth
- Trained ML models / data ingestion platform
- `pip install algo-bot-pro-llm-viz` / `visualize_strategy`
