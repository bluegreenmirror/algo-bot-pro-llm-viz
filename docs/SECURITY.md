# Security Practices for Algo-Bot-Pro-LLM-Viz

## Overview
This document outlines key security practices to ensure the safe and responsible operation of the trading bot project. Following these guidelines helps protect sensitive information, prevent unintended live trades, and maintain the integrity and confidentiality of data.

## Secrets Management
- Store all sensitive credentials such as API keys and secrets in a `.env` file.
- Never commit `.env` files or any secrets to version control.
- Rotate API keys and secrets regularly to minimize risk in case of exposure.
- In production environments, use dedicated secret management solutions (e.g., AWS Secrets Manager, HashiCorp Vault) rather than plain `.env` files.

## Kill-Switch
- The environment variable `ENABLE_TRADING` acts as a kill-switch.
- Broker orders are allowed only when `ENABLE_TRADING=true`.
  Unset or any other value blocks paper/live broker submits (dry-run / audit only).
- Mock mode does not require the kill-switch; it never calls Alpaca.
- This prevents accidental live trading during development, testing, or unexpected conditions.

## Order Gates
- Each broker mode is bound to one endpoint: `paper` requires `https://paper-api.alpaca.markets`,
  `live` requires `https://api.alpaca.markets`. Any mismatch or non-HTTPS URL is refused.
- `run-daily` and `place-bracket` both apply `MAX_NOTIONAL` (policy). Paper/live also apply the
  symbol whitelist, weekdays, and trading hours (compliance).
- Hours and weekdays are evaluated in `MARKET_TZ` (default `America/New_York`), never the host zone.
- Entries are long-only until positions are persisted; sell and hold signals never submit orders.
- Only the mock LLM provider is accepted; real providers are rejected until v1.2 shadow mode.

## Dashboard
- The Streamlit dashboard has no authentication. Docker publishes it on `127.0.0.1` only.
- The mode selector offers only `mock` unless `DASHBOARD_ALLOW_BROKER=true`.
- Backtest files load only from `logs/*.jsonl`; uploads are parsed in memory.

## Dependencies
- All requirements are pinned with `==`. CI runs `pip-audit` and `bandit` (medium and above) on every PR.

## Network & API
- Always use HTTPS endpoints to communicate with trading APIs to ensure encrypted data transmission.
- Restrict API keys to only the necessary permissions and scopes.
- Use separate API keys and endpoints for paper trading and live trading environments.
- Respect and monitor API rate limits to avoid service disruptions.

## File & Data Hygiene
- The `.gitignore` file excludes `.env`, log files, and plot outputs to prevent sensitive or large files from being committed.
- Keep audit logs and sensitive data locally or in secured storage with restricted access.
- Regularly clean up old logs and data to minimize exposure.

## Access Control
- Limit repository and server access to trusted team members only.
- Apply the principle of least privilege when managing Alpaca API keys and other credentials.
- Regularly review and revoke access for users who no longer require it.

## Monitoring & Alerts
- Use the provided `healthcheck.sh` script to monitor the bot’s operational status.
- Integrate alerting mechanisms for stale logs, failed health checks, and suspicious order activity.
- Monitor trading activity closely to detect anomalies or unauthorized trades promptly.

## Disclaimer
This project is an experimental system and does not constitute financial advice. Users are responsible for their own trading decisions and should use the bot at their own risk.
