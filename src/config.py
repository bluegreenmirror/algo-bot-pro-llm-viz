from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List

@dataclass
class Settings:
    env: str
    alpaca_key_id: str | None
    alpaca_secret_key: str | None
    alpaca_base_url: str
    symbols: List[str]
    trading_hours: str
    market_tz: str
    max_notional: float
    state_dir: str
    llm_weight: float

    def __init__(self):
        self.env = os.getenv("ENV", "dev")
        self.alpaca_key_id = os.getenv("ALPACA_KEY_ID")
        self.alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.alpaca_base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        self.symbols = [s.strip() for s in os.getenv("SYMBOLS", "AAPL").split(",") if s.strip()]
        self.trading_hours = os.getenv("TRADING_HOURS", "09:30-16:00")
        self.market_tz = os.getenv("MARKET_TZ", "America/New_York")
        self.max_notional = float(os.getenv("MAX_NOTIONAL", "2000"))
        self.state_dir = os.getenv("STATE_DIR", "./state")
        self.llm_weight = float(os.getenv("LLM_WEIGHT", "0.0"))
