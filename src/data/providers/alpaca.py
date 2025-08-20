from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional

try:
    from alpaca_trade_api.rest import REST, TimeFrame  # type: ignore
except Exception:  # pragma: no cover
    REST = object  # type: ignore
    class TimeFrame:  # type: ignore
        Day = "1Day"

from src.config import Settings

@dataclass(frozen=True)
class Bar:
    t: Any
    o: float
    h: float
    low: float
    c: float
    v: float

    @classmethod
    def from_obj(cls, obj: Any) -> "Bar":
        d = None
        if isinstance(obj, dict):
            d = obj
        elif hasattr(obj, "_raw") and isinstance(getattr(obj, "_raw"), dict):
            d = getattr(obj, "_raw")
        if d is not None:
            return cls(
                t=d.get("t") or d.get("timestamp") or d.get("time"),
                o=float(d.get("o", d.get("open", 0.0))),
                h=float(d.get("h", d.get("high", 0.0))),
                low=float(d.get("low", d.get("l", d.get("low_price", 0.0)))),
                c=float(d.get("c", d.get("close", 0.0))),
                v=float(d.get("v", d.get("volume", 0.0))),
            )
        return cls(
            t=getattr(obj, "t", getattr(obj, "timestamp", getattr(obj, "time", None))),
            o=float(getattr(obj, "o", getattr(obj, "open", 0.0))),
            h=float(getattr(obj, "h", getattr(obj, "high", 0.0))),
            low=float(getattr(obj, "low", getattr(obj, "l", getattr(obj, "low_price", 0.0)))),
            c=float(getattr(obj, "c", getattr(obj, "close", 0.0))),
            v=float(getattr(obj, "v", getattr(obj, "volume", 0.0))),
        )

def _client(settings: Settings) -> REST:
    if not settings.alpaca_key_id or not settings.alpaca_secret_key:
        raise RuntimeError("Missing Alpaca credentials. Set ALPACA_KEY_ID/ALPACA_SECRET_KEY or use --mock.")
    return REST(settings.alpaca_key_id, settings.alpaca_secret_key, base_url=settings.alpaca_base_url)  # type: ignore

def fetch_bars(symbol: str, limit: int = 5, timeframe: Any = None, *, client: Optional[REST]=None, settings: Optional[Settings]=None) -> List[Bar]:
    settings = settings or Settings()
    tf = timeframe or getattr(TimeFrame, "Day", "1Day")
    c = client or _client(settings)
    rows = c.get_bars(symbol, tf, limit=limit)  # type: ignore
    return [Bar.from_obj(r) for r in rows]
