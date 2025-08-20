from __future__ import annotations
from types import SimpleNamespace

class FakeBroker:
    def __init__(self):
        self._i = 0
    def submit_order(self, symbol: str, *, notional: float, side: str, type: str, time_in_force: str):
        self._i += 1
        return SimpleNamespace(id=f"ord_{self._i}", status="accepted", symbol=symbol, side=side, notional=notional)

def submit_market_order(symbol: str, *, notional: float, side: str, time_in_force: str = "day"):
    return FakeBroker().submit_order(symbol, notional=notional, side=side, type="market", time_in_force=time_in_force)

def submit_bracket_order(
    symbol: str,
    *,
    notional: float = 0.0,
    qty: float = 0.0,
    side: str = "buy",
    take_profit_pct: float = 0.05,
    stop_loss_pct: float = 0.03,
    ref_price: float | None = None,   # <— accept it (unused)
):
    return SimpleNamespace(
        id="ord_mock_bracket",
        status="accepted",
        symbol=symbol,
        side=side,
        notional=notional,
        qty=qty,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        ref_price=ref_price,           # optional to echo back
    )