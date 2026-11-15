from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo
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

    def market_now(self, now: datetime | None = None) -> datetime:
        """
        Return `now` in the market timezone (MARKET_TZ).

        Aware datetimes are converted; naive datetimes are taken as already
        market-local. Hours and weekdays must never use the host clock zone,
        because containers usually run in UTC.
        """
        tz = ZoneInfo(self.settings.market_tz)
        if now is None:
            return datetime.now(tz)
        if now.tzinfo is None:
            return now
        return now.astimezone(tz)

    def check_symbol(self, symbol: str) -> ComplianceResult:
        if symbol not in self.settings.symbols:
            return ComplianceResult(False, f"symbol {symbol} not whitelisted")
        return ComplianceResult(True, "ok")

    def check_weekday(self, now: datetime | None = None) -> ComplianceResult:
        now = self.market_now(now)
        if now.weekday() >= 5:
            return ComplianceResult(False, "weekend; trading Mon-Fri only")
        return ComplianceResult(True, "ok")

    def check_hours(self, now: datetime | None = None) -> ComplianceResult:
        now = self.market_now(now)
        (h1, m1), (h2, m2) = _parse_window(self.settings.trading_hours)
        start = h1 * 60 + m1
        end = h2 * 60 + m2
        cur = now.hour * 60 + now.minute
        if cur < start or cur >= end:
            return ComplianceResult(
                False, f"outside trading hours {self.settings.trading_hours} {self.settings.market_tz}"
            )
        return ComplianceResult(True, "ok")

    def check_all(self, symbol: str, now: datetime | None = None) -> ComplianceResult:
        now = self.market_now(now)
        for check in (
            self.check_symbol(symbol),
            self.check_weekday(now=now),
            self.check_hours(now=now),
        ):
            if not check.ok:
                return check
        return ComplianceResult(True, "ok")
