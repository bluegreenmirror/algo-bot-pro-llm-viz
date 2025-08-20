from __future__ import annotations
from typing import Optional, Literal, Any, Dict

try:
    from alpaca_trade_api.rest import REST  # type: ignore
except Exception:  # pragma: no cover
    REST = object  # type: ignore

from src.config import Settings

def _client(settings: Settings) -> REST:
    if not settings.alpaca_key_id or not settings.alpaca_secret_key:
        raise RuntimeError("Missing Alpaca credentials. Set ALPACA_KEY_ID/ALPACA_SECRET_KEY or use --mock.")
    return REST(settings.alpaca_key_id, settings.alpaca_secret_key, base_url=settings.alpaca_base_url)  # type: ignore

def submit_market_order(symbol: str, *, notional: float, side: Literal["buy","sell"], time_in_force: str = "day", client: Optional[REST] = None, settings: Optional[Settings] = None) -> Dict[str, Any]:
    settings = settings or Settings()
    c = client or _client(settings)
    order = c.submit_order(symbol=symbol, notional=notional, side=side, type="market", time_in_force=time_in_force)  # type: ignore
    return {"id": getattr(order, "id", "unknown"), "status": getattr(order, "status", "submitted"), "symbol": symbol, "side": side, "notional": float(notional)}


# Bracket order with take profit and stop loss
from typing import Optional, Literal, Any, Dict
def submit_bracket_order(
    symbol: str,
    *,
    side: Literal["buy", "sell"],
    qty: Optional[float] = None,
    notional: Optional[float] = None,
    ref_price: Optional[float] = None,
    take_profit_pct: float = 0.05,
    stop_loss_pct: float = 0.03,
    time_in_force: str = "day",
    client: Optional[REST] = None,
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    settings = settings or Settings()
    c = client or _client(settings)

    if qty is None and notional is None:
        raise ValueError("Either qty or notional must be provided.")

    # Get reference price if not provided
    _ref_price = ref_price
    if _ref_price is None:
        bars = c.get_bars(symbol, "1Min", limit=1)
        if hasattr(bars, "df"):  # v2 API
            df = bars.df
            if not df.empty:
                _ref_price = float(df["close"].iloc[-1])
        elif hasattr(bars, "__iter__"):
            bar_list = list(bars)
            if bar_list:
                _ref_price = float(getattr(bar_list[-1], "c", getattr(bar_list[-1], "close", None)))
        if _ref_price is None:
            raise RuntimeError("Failed to obtain reference price for bracket order.")

    # Calculate take profit and stop loss absolute prices
    if side == "buy":
        tp = _ref_price * (1 + take_profit_pct)
        sl = _ref_price * (1 - stop_loss_pct)
    else:  # sell
        tp = _ref_price * (1 - take_profit_pct)
        sl = _ref_price * (1 + stop_loss_pct)

    kwargs = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "time_in_force": time_in_force,
        "order_class": "bracket",
        "take_profit": {"limit_price": round(tp, 2)},
        "stop_loss": {"stop_price": round(sl, 2)},
    }
    if qty is not None:
        kwargs["qty"] = qty
    elif notional is not None:
        kwargs["notional"] = notional

    order = c.submit_order(**kwargs)  # type: ignore
    return {
        "id": getattr(order, "id", "unknown"),
        "status": getattr(order, "status", "submitted"),
        "symbol": symbol,
        "side": side,
        "notional": float(notional) if notional is not None else None,
        "qty": float(qty) if qty is not None else None,
        "tp": round(tp, 2),
        "sl": round(sl, 2),
    }
