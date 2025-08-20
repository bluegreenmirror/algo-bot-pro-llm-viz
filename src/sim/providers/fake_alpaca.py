from __future__ import annotations
from typing import List
from types import SimpleNamespace

class FakeREST:
    def __init__(self, *, base_price: float = 100.0):
        self.base = base_price

    def get_bars(self, symbol: str, timeframe: str, limit: int = 5) -> List[object]:
        out = []
        for i in range(limit):
            out.append(SimpleNamespace(
                t=f"2025-01-0{i+1}T09:30:00Z",
                o=self.base + i,
                h=self.base + i + 1,
                low=self.base + i - 1,
                c=self.base + i + 0.5,
                v=1000 + i,
            ))
        return out
