from __future__ import annotations
from dataclasses import dataclass

@dataclass
class PortfolioLimits:
    max_total_exposure_pct: float = 0.5  # <=50% of equity

def can_open_positions(equity: float, per_trade_notional: float, desired_count: int, limits: PortfolioLimits) -> int:
    if equity <= 0: return 0
    max_sum = equity * limits.max_total_exposure_pct
    max_count = int(max_sum // max(1.0, per_trade_notional))
    return max(0, min(desired_count, max_count))
