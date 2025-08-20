# src/viz/equity.py
from __future__ import annotations
import json
from typing import Iterable, Dict, List, Tuple
import matplotlib.pyplot as plt
from pathlib import Path

def load_trades_jsonl(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backtest log not found: {path}")
    trades: List[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            # Expect keys: ts, side, price, notional, symbol
            if {"ts","side","price","notional"}.issubset(rec.keys()):
                trades.append(rec)
        except Exception:
            continue
    return trades

def equity_curve_from_trades(trades: List[dict], initial_equity: float = 100_000.0) -> Tuple[List[float], List[int]]:
    """
    Pairs buy->sell trades per symbol to compute stepwise cumulative equity.
    Returns (equity_curve, indices) where indices are event indices.
    """
    # bucket by symbol
    by_sym: Dict[str, List[dict]] = {}
    for t in trades:
        by_sym.setdefault(t.get("symbol","GEN"), []).append(t)

    equity = initial_equity
    curve: List[float] = [equity]
    idx: List[int] = [0]
    event_i = 0

    for sym, events in by_sym.items():
        # simple streaming pair: buy then sell
        open_buy = None
        for ev in events:
            event_i += 1
            if ev["side"] == "buy" and open_buy is None:
                open_buy = ev
            elif ev["side"] == "sell" and open_buy is not None:
                buy = open_buy
                sell = ev
                shares = (buy["notional"] / buy["price"]) if buy["price"] else 0.0
                pnl = (sell["price"] - buy["price"]) * shares
                equity += pnl
                open_buy = None
                curve.append(equity)
                idx.append(event_i)
            else:
                # ignore unmatched sells or multiple buys; real engine would track positions
                curve.append(equity)
                idx.append(event_i)
    return (curve, idx)

def plot_equity_curve(curve: List[float], indices: List[int], title: str = "Equity Curve"):
    fig, ax = plt.subplots()
    ax.plot(indices, curve, label="Equity")
    ax.set_title(title)
    ax.set_xlabel("Trade event")
    ax.set_ylabel("Equity ($)")
    ax.legend()
    fig.tight_layout()
    return fig

def save_fig(fig, out_path: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)