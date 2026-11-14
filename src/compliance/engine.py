from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple
from src.config import Settings

@dataclass
class ComplianceResult:
    ok: bool
    reason: str = "ok"

def _parse_window(window: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    a, b = window.split("-")
    h1, m1 = map(int, a.split(":"))
    h2, m2 = map(int, b.split(":"))
    return (h1, m1), (h2, m2)

class ComplianceEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def check_symbol(self, symbol: str) -> ComplianceResult:
        if symbol not in self.settings.symbols:
            return ComplianceResult(False, f"symbol {symbol} not whitelisted")
        return ComplianceResult(True, "ok")

    def check_weekday(self, now: datetime | None = None) -> ComplianceResult:
        now = now or datetime.now()
        if now.weekday() >= 5:
            return ComplianceResult(False, "weekend; trading Mon-Fri only")
        return ComplianceResult(True, "ok")

    def check_hours(self, now: datetime | None = None) -> ComplianceResult:
        now = now or datetime.now()
        (h1, m1), (h2, m2) = _parse_window(self.settings.trading_hours)
        start = h1 * 60 + m1
        end = h2 * 60 + m2
        cur = now.hour * 60 + now.minute
        if cur < start or cur > end:
            return ComplianceResult(False, f"outside trading hours {self.settings.trading_hours}")
        return ComplianceResult(True, "ok")

    def check_all(self, symbol: str, now: datetime | None = None) -> ComplianceResult:
        now = now or datetime.now()
        for check in (
            self.check_symbol(symbol),
            self.check_weekday(now=now),
            self.check_hours(now=now),
        ):
            if not check.ok:
                return check
        return ComplianceResult(True, "ok")
