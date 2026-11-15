# v1 Revision Plan

Source of truth for this revision: this file, `OPERATIONALIZING.md`, and `SECURITY.md`.
Archived MVP: branch `archive/v0-mvp`, tag `v0.1.0-mvp`.

## Product contract (v1)

This repo is a local CLI + Streamlit trading bot with mock and paper Alpaca paths.
It is not an API server, user database, auth system, or pip-installable viz package.

## Checklist

### v1.0 Spec + safety

- [x] Demote or rewrite `ARCHITECTURE.md` and `USAGE.md` to match the bot above
- [x] Kill-switch: unset or `false` blocks broker orders; only explicit `true` allows them
- [x] Modes: `mock | paper | live` (no silent live market-order path)
- [x] Pass stop / take-profit through execution into bracket orders
- [x] Compliance owns trading hours and weekdays; runner only schedules
- [x] Deduplicate `.env.example`; mock runs without live keys

### v1.0.1 Security hardening (PR #3)

Audit of `main` after v1.0. Every item has a test that fails on the pre-fix code.

- [ ] Patch vulnerable pins (Pillow, Streamlit, pytest); `pip-audit` clean
- [ ] Bind `paper` / `live` to their Alpaca hosts (HTTPS only)
- [ ] `place-bracket` applies policy, compliance, and endpoint gates
- [ ] Long-only entries: hold / sell never submit (no accidental shorts)
- [ ] Compliance evaluates hours and weekdays in `MARKET_TZ`
- [ ] Reject non-mock LLM providers until v1.2
- [ ] Dashboard: loopback publish, mock-only by default, `logs/*.jsonl` paths only
- [ ] CI: pytest, `pip-audit`, `bandit -ll` on every PR

### v1.1 State + honest validation

Detailed spec in the next section.

- [ ] R1 Persist equity and open positions under `STATE_DIR`
- [ ] R2 Exposure, `--max-pos`, and exits use persisted state
- [ ] R3 Order sizing that can pass `MAX_NOTIONAL` with default settings
- [ ] R4 Non-monotonic mock bars and fixtures so SMA crosses occur
- [ ] R5 Backtest fees / slippage; one shared equity calculation
- [ ] R6 Dashboard shows persisted state and a non-empty equity curve
- [ ] R7 Market holiday calendar in compliance

### v1.2 Paper path

- [ ] Pin Alpaca client; paper validate path in `validate.sh`
- [ ] Reconcile persisted positions against broker positions on every paper/live run
- [ ] Health alerts: missed runs, high block ratio, order-rate spikes
- [ ] Optional LLM shadow (`LLM_WEIGHT=0`) after audit reasons are real

## v1.1 specification

Goal: the mock path produces trades a reviewer can check by hand, and every risk
limit reads from real portfolio state instead of a hard-coded 100,000 equity.

Prerequisite: v1.0.1 merged. v1.1 relies on its long-only rule, market-timezone
compliance, and CI gates.

### R1 Portfolio state store

- New module `src/state/store.py`; no I/O elsewhere touches the state file.
- File: `STATE_DIR/portfolio.json` with `version`, `equity`, `cash`,
  `positions` (symbol -> `qty`, `entry_price`, `opened_ts`, `order_id`), `updated_ts`.
- First run seeds from `INITIAL_EQUITY` (default 100000).
- Writes are atomic (temp file + `os.replace`) with mode `0600`.
- Unknown `version` or unparseable JSON fails closed: no orders, audit event
  `state_error`, non-zero exit. Never silently reset.
- Stores no secrets.

Acceptance tests (`tests/test_state_store.py`):

- `test_seed_from_initial_equity`
- `test_round_trip_preserves_positions`
- `test_write_is_atomic` (simulated crash mid-write leaves the previous file intact)
- `test_file_mode_0600`
- `test_corrupt_or_unknown_version_fails_closed`
- `test_state_path_stays_under_state_dir`

### R2 Executor uses state

- `run_daily` takes an injected store (the CLI builds the real one; tests pass
  a memory store), keeping domain logic free of file I/O.
- Equity and current exposure come from state. `can_open_positions` counts
  existing positions toward `--max-pos` and the 50% exposure cap.
- A buy signal for a symbol already held is `skipped` ("already long").
- A sell signal for a held symbol closes it (exit). With no position it stays
  `skipped`. Shorts remain out of scope.
- Mock fills update state. Paper/live do not mutate positions until broker
  reconciliation exists (v1.2); they audit `pending_reconcile` instead.

Acceptance tests (`tests/test_executor_state.py`):

- `test_equity_read_from_state`
- `test_max_positions_counts_existing`
- `test_exposure_cap_counts_existing`
- `test_buy_when_already_long_skipped`
- `test_sell_closes_held_position_and_updates_cash`
- `test_sell_without_position_never_submits`
- `test_paper_does_not_mutate_positions`
- `test_state_survives_two_cli_runs` (CLI, `tmp_path` `STATE_DIR`)

### R3 Sizing vs policy

- Problem today: risk sizing gives `equity * risk / stop`
  (100000 * 0.01 / 0.03 = 33,333), above the default `MAX_NOTIONAL=2000`.
  The default config can therefore never place an order.
- Rule: order notional = `min(risk sizing, MAX_NOTIONAL, available cash)`.
  `PolicyEngine` stays a hard gate and still rejects anything above `MAX_NOTIONAL`.
- The audit records `sized_notional` and `sizing_reason`.

Acceptance tests (`tests/test_sizing.py`):

- `test_notional_capped_at_max_notional`
- `test_notional_capped_at_cash`
- `test_policy_still_rejects_oversize`
- `test_default_settings_can_place_in_mock`

### R4 Mock data that crosses

- `FakeREST` produces a deterministic, seeded series (trend plus oscillation),
  never strictly monotonic. Prices stay positive and timestamps are valid ISO dates.
- Fixtures: `tests/fixtures/bars_cross.csv` with known buy and sell cross indices.

Acceptance tests (`tests/test_mock_data.py`):

- `test_fake_rest_deterministic_per_seed`
- `test_fake_rest_not_monotonic`
- `test_fixture_crosses_at_expected_indices`
- `test_timestamps_are_valid_iso_dates`

### R5 Backtest realism

- `backtest-sma` gains `--fee-bps` and `--slippage-bps` (defaults 1 and 5).
  Buys fill at `price * (1 + slip)`, sells at `price * (1 - slip)`, and fees
  apply on both sides.
- Each trade line records `gross_pnl`, `fees`, and `net_pnl`.
- One equity function in `src/viz/equity.py`. The dashboard calls it instead
  of keeping its own copy.

Acceptance tests (`tests/test_backtest.py`):

- `test_mock_backtest_produces_round_trips`
- `test_fees_and_slippage_reduce_pnl` (hand-computed expected value)
- `test_zero_cost_matches_gross`
- `test_dashboard_and_cli_equity_agree`

### R6 Dashboard

- Shows persisted equity, cash, and open positions (read-only).
- The equity curve is non-empty after `backtest-sma --mock`.
- No new controls that can submit orders.

Acceptance tests (`tests/test_dashboard_app.py`, Streamlit `AppTest`):

- `test_state_panel_shows_positions`
- `test_equity_curve_after_mock_backtest`
- Manual: recorded walkthrough of a tick, a backtest, and the equity curve.

### R7 Holidays

- Static NYSE full-closure list for the current and next year in
  `src/compliance/calendar.py`. Early closes are out of scope.
- `ComplianceEngine.check_all` blocks on listed dates with reason `market holiday`.

Acceptance tests (`tests/test_compliance.py`):

- `test_holiday_blocked` (for example 2026-11-26, Thanksgiving)
- `test_day_after_holiday_open`

### v1.1 exit criteria

- All acceptance tests above pass in CI, and `pip-audit` and `bandit -ll` are clean.
- `scripts/validate.sh` passes. Its mock run over the fixture produces at least
  one buy and one exit, and state persists across two runs.
- No new network-facing surface, no new secrets, no order path without the
  kill switch, endpoint binding, policy, and compliance gates.

### Security checklist for every v1.1 PR

- New file paths resolve under `STATE_DIR` or `logs/`; no user-controlled paths.
- Fail closed on bad state or config; never default to trading.
- No secrets in state, audit, or stdout.
- New dependencies pinned with `==` and pass `pip-audit`.

## Known low-severity items (tracked, not blocking)

- `bandit` low findings: broad `except: continue` in JSONL readers. These skip
  malformed lines on purpose.
- Equity curves start with a single seed point, so a "curve" can be one value
  (fixed by R5).
- `fetch-bars` / `viz-sma` without `--mock` need the Alpaca SDK, which is
  unpinned until v1.2.
- Health check only detects a stale audit log (v1.2 alerts).

## Out of scope for v1

- API server, database, auth
- Trained ML models / data ingestion platform
- `pip install algo-bot-pro-llm-viz` / `visualize_strategy`
- Short selling
