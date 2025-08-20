

# Algo Trading Bot Pro — LLM + Visualization

An experimental algorithmic trading bot that integrates traditional technical strategies (e.g., SMA crossovers) with optional LLM-based scoring and rich visualization tools.

## Features

- **Trading strategies**
  - SMA crossover strategy (mock/live data)
  - Bracket (OCO) orders for live trading via Alpaca
  - Policy/compliance rules (universe, trading hours, exposure caps)
- **Safety**
  - Kill-switch via `ENABLE_TRADING`
  - Risk-based position sizing
- **Visualization**
  - CLI plots (SMA chart, equity curve)
  - Streamlit dashboard with Run Tick button, audit table, SMA chart, and equity curve
- **Backtesting**
  - Generate JSONL trade logs
  - Plot equity curves in CLI or dashboard
- **Ops tooling**
  - Dockerized environment
  - Healthcheck and runner scripts
  - Comprehensive test suite

## Quick Start

```bash
git init
git add .
git commit -m "Initial commit of trading bot"
cp .env.example .env
docker compose build
make test
```

Run a mock trading cycle:
```bash
make run CMD='run-daily --universe AAPL,MSFT --limit 40 --fast 5 --slow 20 --risk 0.01 --mock'
```

Launch the dashboard:
```bash
make dash
# open http://localhost:8501
```

## Documentation

See [USAGE.md](USAGE.md) for full details on configuration, running in mock/live modes, backtesting, and operationalizing the bot.

## Safety Notes

- **Not financial advice**: this project is for educational and experimental purposes.
- Always paper trade first before using real capital.
- Keep `.env` and API keys out of source control.

## License

MIT License