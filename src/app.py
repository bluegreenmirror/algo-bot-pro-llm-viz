from __future__ import annotations
import json
import click

@click.group()
def cli():
    """Algo Bot CLI (LLM & Viz)"""

@cli.command("fetch-bars")
@click.option("--symbol", required=True)
@click.option("--limit", default=5, type=int)
@click.option("--mock", is_flag=True)
def fetch_bars_cmd(symbol: str, limit: int, mock: bool):
    from src.data.providers.alpaca import fetch_bars
    if mock:
        from src.sim.providers.fake_alpaca import FakeREST
        rows = fetch_bars(symbol=symbol, limit=limit, client=FakeREST())
    else:
        rows = fetch_bars(symbol=symbol, limit=limit)
    click.echo(f"Fetched {len(rows)} bars for {symbol}")
    for r in rows:
        click.echo(f"{r.t} o={r.o} h={r.h} low={r.low} c={r.c} v={r.v}")

@cli.command("viz-sma")
@click.option("--symbol", required=True)
@click.option("--limit", default=60, type=int)
@click.option("--fast", default=5, type=int)
@click.option("--slow", default=20, type=int)
@click.option("--mock", is_flag=True)
@click.option("--out", default="viz_sma.png")
def viz_sma_cmd(symbol, limit, fast, slow, mock, out):
    from src.data.providers.alpaca import fetch_bars
    from src.strategy.sma import sma
    from src.viz.plot import plot_price_with_sma, save_fig
    if mock:
        from src.sim.providers.fake_alpaca import FakeREST
        bars = fetch_bars(symbol=symbol, limit=limit, client=FakeREST())
    else:
        bars = fetch_bars(symbol=symbol, limit=limit)
    closes = [b.c for b in bars]
    sf = sma(closes, fast); ss = sma(closes, slow)
    fig = plot_price_with_sma([b.t for b in bars], closes, sf, ss, title=f"{symbol} SMA {fast}/{slow}")
    save_fig(fig, out)
    click.echo(f"Saved {out}")

@cli.command("run-daily")
@click.option("--universe", required=True, help="Comma-separated symbols")
@click.option("--limit", default=40, type=int)
@click.option("--fast", default=5, type=int)
@click.option("--slow", default=20, type=int)
@click.option("--risk", "risk_per_trade", default=0.01, type=float)
@click.option("--stop", "stop_loss_pct", default=0.03, type=float)
@click.option("--take", "take_profit_pct", default=0.05, type=float)
@click.option("--max-pos", "max_positions", default=5, type=int)
@click.option("--mode", type=click.Choice(["mock", "paper", "live"]), default=None,
              help="Trading mode (default mock). paper/live use Alpaca brackets.")
@click.option("--mock", is_flag=True, help="Alias for --mode mock")
@click.option("--live", is_flag=True, help="Alias for --mode paper (legacy)")
def run_daily_cmd(universe: str, limit: int, fast: int, slow: int, risk_per_trade: float, stop_loss_pct: float, take_profit_pct: float, max_positions: int, mode: str | None, mock: bool, live: bool):
    from src.runtime import is_trading_enabled, require_alpaca_keys, require_endpoint_for_mode, resolve_mode
    try:
        resolved = resolve_mode(mode, mock=mock, live=live)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc

    if resolved in ("paper", "live"):
        try:
            require_alpaca_keys()
            require_endpoint_for_mode(resolved)
        except RuntimeError as exc:
            raise click.UsageError(str(exc)) from exc

    from src.data.providers.alpaca import fetch_bars
    if resolved == "mock":
        from src.sim.providers.fake_alpaca import FakeREST
        client = FakeREST()
    else:
        client = None
    syms = [s.strip() for s in universe.split(",") if s.strip()]
    bars_dict = {}
    for sym in syms:
        rows = fetch_bars(symbol=sym, limit=limit, client=client)
        closes = [r.c for r in rows]
        bars_dict[sym] = closes

    # Always brackets when submitting; never silent live market orders.
    if resolved == "mock":
        from src.sim.broker.fake_broker import submit_bracket_order as submit_fn
    else:
        from src.broker.alpaca_client import submit_bracket_order as submit_fn

    if resolved != "mock" and not is_trading_enabled():
        submit_fn = None
        click.echo(
            "Trading disabled (ENABLE_TRADING must be true for paper/live); dry run only.",
            err=True,
        )

    from src.execution.executor import run_daily
    try:
        result = run_daily(
            syms, bars_dict,
            fast=fast, slow=slow,
            risk_per_trade=risk_per_trade,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            max_positions=max_positions,
            submit_fn=submit_fn,
        )
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    result["mode"] = resolved
    click.echo(json.dumps(result))

@cli.command("viz-equity")
@click.option("--backtest-log", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--initial", default=100000.0, type=float, help="Starting equity")
@click.option("--out", default="equity.png", help="Output PNG path")
def viz_equity_cmd(backtest_log: str, initial: float, out: str):
    """Build and save an equity curve PNG from a backtest JSONL log."""
    from src.viz.equity import load_trades_jsonl, equity_curve_from_trades, plot_equity_curve, save_fig
    trades = load_trades_jsonl(backtest_log)
    curve, idx = equity_curve_from_trades(trades, initial_equity=initial)
    fig = plot_equity_curve(curve, idx, title=f"Equity from {backtest_log}")
    save_fig(fig, out)
    click.echo(f"Saved {out}")

@cli.command("place-bracket")
@click.option("--symbol", required=True, help="Symbol to trade")
@click.option("--qty", type=float, help="Quantity to buy/sell")
@click.option("--notional", type=float, help="Notional amount to trade (alternative to qty)")
@click.option("--side", required=True, type=click.Choice(["buy", "sell"]), help="Side of the trade")
@click.option("--ref-price", type=float, default=0.0, help="Reference price for TP/SL calculation (optional)")
@click.option("--take-profit-pct", "--tp", type=float, default=0.05, help="Take profit percentage (e.g. 0.05 for 5%)")
@click.option("--stop-loss-pct", "--sl", type=float, default=0.03, help="Stop loss percentage (e.g. 0.03 for 3%)")
@click.option("--mode", type=click.Choice(["mock", "paper", "live"]), default=None)
@click.option("--live", is_flag=True, help="Alias for --mode paper (legacy)")
def place_bracket_cmd(symbol, qty, notional, side, ref_price, take_profit_pct, stop_loss_pct, mode, live):
    from src.compliance.engine import ComplianceEngine
    from src.policy.engine import PolicyEngine
    from src.runtime import is_trading_enabled, require_alpaca_keys, require_endpoint_for_mode, resolve_mode
    try:
        resolved = resolve_mode(mode, live=live)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc

    if qty is None and notional is None:
        raise click.UsageError("Either --qty or --notional must be provided")
    if qty is not None and notional is not None:
        raise click.UsageError("Use either --qty or --notional, not both")

    order_notional = notional if notional is not None else (qty * ref_price if ref_price else None)
    if order_notional is None:
        raise click.UsageError("--ref-price is required with --qty so the order notional can be checked")
    pol = PolicyEngine().check_all(notional=order_notional)
    if not pol.ok:
        raise click.UsageError(f"Blocked by policy: {pol.reason}")

    if resolved == "mock":
        from src.sim.broker.fake_broker import submit_bracket_order
    else:
        if not is_trading_enabled():
            raise click.UsageError(
                "ENABLE_TRADING must be true to place paper/live bracket orders"
            )
        try:
            require_alpaca_keys()
            require_endpoint_for_mode(resolved)
        except RuntimeError as exc:
            raise click.UsageError(str(exc)) from exc
        comp = ComplianceEngine().check_all(symbol=symbol)
        if not comp.ok:
            raise click.UsageError(f"Blocked by compliance: {comp.reason}")
        from src.broker.alpaca_client import submit_bracket_order

    order = submit_bracket_order(
        symbol=symbol,
        qty=qty,
        notional=notional,
        side=side,
        ref_price=ref_price or None,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    click.echo(f"Placed bracket order: {order}")

@cli.command("backtest-sma")
@click.option("--symbol", required=True, help="Ticker symbol")
@click.option("--limit", default=100, type=int, help="Bars to load")
@click.option("--fast", default=5, type=int, help="SMA fast window")
@click.option("--slow", default=20, type=int, help="SMA slow window")
@click.option("--notional", default=1000.0, type=float, help="Notional per trade ($)")
@click.option("--mock", is_flag=True, help="Use mock data (FakeREST)")
@click.option("--out", default=None, help="Output JSONL path (default logs/backtest_<symbol>.jsonl)")
def backtest_sma_cmd(symbol: str, limit: int, fast: int, slow: int, notional: float, mock: bool, out: str | None):
    """
    Run a simple SMA crossover backtest and write trades to JSONL.
    Each line: {"ts": i, "side": "buy|sell", "price": float, "notional": float, "symbol": str}
    """
    import os, json
    from pathlib import Path
    from src.data.providers.alpaca import fetch_bars
    from src.strategy.sma import sma_signal

    # Fetch bars (mock or live)
    client = None
    if mock:
        try:
            from src.sim.providers.fake_alpaca import FakeREST
            client = FakeREST()
        except Exception:
            client = None
    rows = fetch_bars(symbol=symbol, limit=limit, client=client)
    closes = [r.c for r in rows]

    if len(closes) < max(fast, slow) + 1:
        click.echo("Not enough data for backtest.", err=True)
        return

    # Simple buy/sell pairing
    trades = []
    pos = 0  # 0 = flat, 1 = long
    for i in range(len(closes)):
        sub = closes[: i + 1]
        sig = sma_signal(sub, fast=fast, slow=slow)
        price = closes[i]
        if sig == "buy" and pos == 0:
            trades.append({"ts": i, "side": "buy", "price": price, "notional": float(notional), "symbol": symbol})
            pos = 1
        elif sig == "sell" and pos == 1:
            trades.append({"ts": i, "side": "sell", "price": price, "notional": float(notional), "symbol": symbol})
            pos = 0

    # Close any open long at last price
    if pos == 1 and closes:
        trades.append({"ts": len(closes) - 1, "side": "sell", "price": closes[-1], "notional": float(notional), "symbol": symbol})

    # Write JSONL
    out_path = out or f"logs/backtest_{symbol}.jsonl"
    Path(os.path.dirname(out_path) or ".").mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for t in trades:
            f.write(json.dumps(t) + "\n")

    click.echo(f"Saved backtest log: {out_path}")

if __name__ == "__main__":
    cli()
